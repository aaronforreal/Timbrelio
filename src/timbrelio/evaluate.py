"""Reproducible projection and clustering experiments on track feature CSVs."""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import trustworthiness
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class Config:
    seed: int = 42
    neighbors: int = 5
    umap_neighbors: int = 15
    umap_min_dist: float = 0.1
    clusters: int = 8
    min_cluster_size: int = 15
    min_samples: int = 5


def load_features(path: Path):
    """Read track_id, optional genre/title, and numeric feature columns."""
    df = pd.read_csv(path, dtype={"track_id": "string"})
    if "track_id" not in df or df.track_id.isna().any() or (df.track_id.str.strip() == "").any():
        raise ValueError("CSV needs non-empty track_id values")
    if df.track_id.duplicated().any():
        raise ValueError("track_id values must be unique")
    metadata = [c for c in ("track_id", "title", "genre") if c in df]
    feature_names = [c for c in df.columns if c not in metadata]
    if len(feature_names) < 2:
        raise ValueError("At least two numeric feature columns are required")
    try:
        values = df[feature_names].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("All columns other than track_id, title and genre must be numeric features") from exc
    if not np.isfinite(values).all():
        raise ValueError("Feature values must be finite; fix missing or invalid values first")
    return df[metadata].copy(), values, feature_names


def neighbor_indices(values, k, metric):
    # Query against the fitted training set with X=None excludes each point itself,
    # even when multiple tracks have exactly equal vectors.
    return NearestNeighbors(n_neighbors=k, metric=metric, algorithm="brute").fit(values).kneighbors(return_distance=False)


def neighbor_overlap(original, projection, k):
    a = neighbor_indices(original, k, "cosine")
    b = neighbor_indices(projection, k, "euclidean")
    return float(np.mean([len(set(x) & set(y)) / k for x, y in zip(a, b)]))


def cluster_metrics(values, labels, genres=None):
    labels = np.asarray(labels)
    mask = labels != -1
    assigned = labels[mask]
    unique = np.unique(assigned)
    result = {"n_clusters": int(len(unique)), "noise_rate": float(np.mean(~mask)),
              "silhouette": None, "adjusted_rand_index": None, "ari_n_labeled": 0}
    # Noise is excluded from silhouette; labels and feature rows stay aligned.
    if len(unique) >= 2 and len(unique) < len(assigned):
        result["silhouette"] = float(silhouette_score(values[mask], assigned, metric="euclidean"))
    # ARI includes noise as a predicted label and excludes only unknown reference genres.
    if genres is not None:
        known = pd.notna(genres) & (pd.Series(genres).astype("string").str.strip().fillna("") != "").to_numpy()
        if known.sum() >= 2:
            result["adjusted_rand_index"] = float(adjusted_rand_score(np.asarray(genres)[known], labels[known]))
            result["ari_n_labeled"] = int(known.sum())
    return result


def run_experiment(input_path: Path, output_dir: Path, config: Config):
    # Imported lazily so that an actionable error is given if the optional tools are missing.
    try:
        import umap
        import hdbscan
    except ImportError as exc:
        raise RuntimeError('Install analysis dependencies with: python -m pip install -e ".[analysis]"') from exc
    metadata, raw, names = load_features(input_path)
    n = len(raw)
    if n < 4 or not 1 <= config.neighbors < n / 2:
        raise ValueError("Need at least 4 tracks and 1 <= neighbors < number of tracks / 2")
    if not 2 <= config.umap_neighbors < n:
        raise ValueError("UMAP neighbors must be at least 2 and less than track count")
    if not 2 <= config.clusters < n or not 2 <= config.min_cluster_size <= n or config.min_samples < 1:
        raise ValueError("Invalid clustering parameters for the number of tracks")
    if not 0 <= config.umap_min_dist <= 1:
        raise ValueError("UMAP min_dist must be between 0 and 1")
    values = StandardScaler().fit_transform(raw)
    projections = {}
    for name, model in {
        "pca": PCA(n_components=2, svd_solver="full"),
        "umap": umap.UMAP(n_components=2, n_neighbors=config.umap_neighbors,
                          min_dist=config.umap_min_dist, metric="cosine", random_state=config.seed, n_jobs=1),
    }.items():
        start = time.perf_counter()
        coordinates = model.fit_transform(values)
        elapsed = time.perf_counter() - start
        projections[name] = (coordinates, {
            "runtime_seconds": elapsed,
            "trustworthiness": float(trustworthiness(values, coordinates, n_neighbors=config.neighbors, metric="cosine")),
            "neighbor_overlap": neighbor_overlap(values, coordinates, config.neighbors),
        })
    clusters = {}
    for name, model in {
        "kmeans": KMeans(n_clusters=config.clusters, random_state=config.seed, n_init=10),
        "hdbscan": hdbscan.HDBSCAN(min_cluster_size=config.min_cluster_size, min_samples=config.min_samples,
                                   metric="euclidean", core_dist_n_jobs=1),
    }.items():
        start = time.perf_counter()
        labels = model.fit_predict(values)
        elapsed = time.perf_counter() - start
        metrics = cluster_metrics(values, labels, metadata["genre"].to_numpy() if "genre" in metadata else None)
        metrics["runtime_seconds"] = elapsed
        clusters[name] = (labels, metrics)
    output_dir.mkdir(parents=True, exist_ok=True)
    for projection_name, (coordinates, _) in projections.items():
        for cluster_name, (labels, _) in clusters.items():
            result = metadata.copy()
            result["x"], result["y"], result["cluster"] = coordinates[:, 0], coordinates[:, 1], labels
            result.to_csv(output_dir / f"{projection_name}_{cluster_name}.csv", index=False)
    report = {"input": str(input_path), "track_count": n, "feature_columns": names,
              "config": asdict(config),
              "versions": {p: version(p) for p in ("numpy", "pandas", "scikit-learn", "umap-learn", "hdbscan")},
              "projection_metrics": {name: metrics for name, (_, metrics) in projections.items()},
              "cluster_metrics": {name: metrics for name, (_, metrics) in clusters.items()}}
    (output_dir / "metrics.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("features", type=Path, help="CSV with track_id and numeric feature columns")
    parser.add_argument("output", type=Path, help="Output directory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--neighbors", type=int, default=5)
    parser.add_argument("--umap-neighbors", type=int, default=15)
    parser.add_argument("--umap-min-dist", type=float, default=0.1)
    parser.add_argument("--clusters", type=int, default=8)
    parser.add_argument("--min-cluster-size", type=int, default=15)
    parser.add_argument("--min-samples", type=int, default=5)
    args = parser.parse_args()
    config = Config(args.seed, args.neighbors, args.umap_neighbors, args.umap_min_dist,
                    args.clusters, args.min_cluster_size, args.min_samples)
    try:
        report = run_experiment(args.features, args.output, config)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
