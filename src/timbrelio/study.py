"""Evaluate one representation using fixed configurations and original-space retrieval."""
import argparse
import hashlib
import json
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from timbrelio.evaluate import Config, load_features, run_experiment


def retrieval(metadata, raw, representation):
    values = StandardScaler().fit_transform(raw)
    if len(values) < 6:
        raise ValueError("Precision@5 requires at least six tracks")
    norms = np.linalg.norm(values, axis=1)
    if np.any(norms == 0):
        raise ValueError("Cosine distance is undefined for a zero standardized track")
    unit = values / norms[:, None]
    ids = metadata.track_id.to_numpy(dtype=str)
    genres = metadata.get("genre", pd.Series("", index=metadata.index)).fillna("").astype(str).str.strip().to_numpy()
    rows, scores = [], []
    # Break exact distance ties by track ID, independent of CSV row order.
    stable_order = np.argsort(ids, kind="stable")
    for i, track in enumerate(ids):
        distances = np.clip(1 - unit @ unit[i], 0, 2)
        distances[i] = np.inf
        nearest = stable_order[np.argsort(distances[stable_order], kind="stable")[:5]]
        for rank, j in enumerate(nearest, 1):
            rows.append((track, representation, ids[j], rank, distances[j]))
        if genres[i] and all(genres[nearest]):
            scores.append((track, float(np.mean(genres[nearest] == genres[i]))))
    neighbours = pd.DataFrame(rows, columns=["seed_track_id", "representation", "neighbour_track_id", "rank", "distance"])
    return neighbours, pd.DataFrame(scores, columns=["track_id", "precision_at_5"])


def study(features, destination, representation, seed):
    metadata, raw, _ = load_features(features)
    if len(raw) <= 30:
        raise ValueError("The fixed sensitivity grid requires at least 31 tracks")
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    base = Config(seed=seed)
    configs = {"baseline": base, "umap-n30": replace(base, umap_neighbors=30),
               "umap-dist05": replace(base, umap_min_dist=0.5),
               "hdb-size30": replace(base, min_cluster_size=30),
               "hdb-samples10": replace(base, min_samples=10)}
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        output = Path(tmp) / "study"
        output.mkdir()
        neighbours, scores = retrieval(metadata, raw, representation)
        neighbours.to_csv(output / "neighbours.csv", index=False)
        scores.to_csv(output / "retrieval_by_seed.csv", index=False)
        candidates = scores.sort_values(["precision_at_5", "track_id"])
        if len(candidates):
            candidates = candidates.iloc[[0, -1]].drop_duplicates("track_id")
        neighbours[neighbours.seed_track_id.isin(candidates.track_id)].merge(
            candidates, left_on="seed_track_id", right_on="track_id"
        ).drop(columns="track_id").to_csv(output / "listening_candidates.csv", index=False)
        tables = {"projection_metrics": [], "cluster_metrics": []}
        for name, config in configs.items():
            report = run_experiment(features, output / name, config)
            for group, rows in tables.items():
                for method, metrics in report[group].items():
                    rows.append({"run": name, "method": method, **metrics})
        for group, rows in tables.items():
            pd.DataFrame(rows).to_csv(output / f"{group}.csv", index=False)
        summary = {"representation": representation, "seed": seed, "track_count": len(raw),
                   "features_sha256": hashlib.sha256(features.read_bytes()).hexdigest(),
                   "eligible_seeds": len(scores),
                   "precision_at_5": float(scores.precision_at_5.mean()) if len(scores) else None,
                   "configurations": {name: asdict(config) for name, config in configs.items()}}
        (output / "study.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        output.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("features", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--representation", choices=["Conventional", "OpenL3"], required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    study(args.features, args.output, args.representation, args.seed)


if __name__ == "__main__":
    main()
