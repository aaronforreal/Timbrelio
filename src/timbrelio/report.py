"""Generate ISMIR-ready results tables from two aligned study runs."""
import argparse
import json
from pathlib import Path

import pandas as pd


def load_run(folder, expected):
    summary = json.loads((folder / "study.json").read_text())
    if summary["representation"] != expected:
        raise ValueError(f"Expected a {expected} study in {folder}")
    scores = pd.read_csv(folder / "retrieval_by_seed.csv", dtype={"track_id": str}).set_index("track_id")
    baseline = pd.read_csv(folder / "baseline/pca_kmeans.csv", dtype={"track_id": str})
    if baseline.track_id.isna().any() or baseline.track_id.duplicated().any():
        raise ValueError("Baseline track IDs must be present and unique")
    labels = baseline.set_index("track_id").reindex(columns=["genre"]).fillna("").sort_index()
    if not scores.index.is_unique or not scores.index.isin(labels.index).all():
        raise ValueError("Retrieval scores must identify unique tracks in the baseline")
    return summary, labels, scores.precision_at_5


def format_metric(value):
    return f"{value:.3f}" if pd.notna(value) else "--"


def result_tables(conventional, openl3):
    folders = {"Conventional": conventional, "OpenL3": openl3}
    runs = [load_run(folder, name) for name, folder in folders.items()]
    (left, labels, scores), (right, other_labels, other_scores) = runs
    if left["configurations"] != right["configurations"] or not labels.equals(other_labels):
        raise ValueError("Paired reporting requires matching configurations, track IDs and genres")
    common = scores.index.intersection(other_scores.index)
    tables = []
    def table(caption, headers, rows):
        tables.extend([r"\begin{table*}[t]", r"\centering",
                       r"\begin{tabular}{" + "l" * len(headers) + "}",
                       " & ".join(headers) + r" \\ \hline"])
        tables.extend(" & ".join(row) + r" \\" for row in rows)
        tables.extend([r"\end{tabular}", r"\caption{" + caption + "}", r"\end{table*}"])
    table("Genre agreement on the same eligible seeds in both representations.",
          ["Representation", "Tracks", "Eligible seeds", "Precision@5"],
          [[name, str(len(labels)), str(len(common)), format_metric(series.loc[common].mean())]
           for name, series in zip(folders, (scores, other_scores))])
    for group, columns, headings in [
        ("projection", ["trustworthiness", "neighbor_overlap", "runtime_seconds"],
         ["Trustworthiness", "Overlap", "Fit time (s)"]),
        ("cluster", ["silhouette", "adjusted_rand_index", "noise_rate", "runtime_seconds"],
         ["Silhouette", "ARI", "Noise rate", "Fit time (s)"]),
    ]:
        rows = []
        for name, folder in folders.items():
            frame = pd.read_csv(folder / f"{group}_metrics.csv")
            for _, row in frame[frame.run == "baseline"].iterrows():
                method = row["method"]
                if method not in ("pca", "umap", "kmeans", "hdbscan"):
                    raise ValueError("Unknown baseline method")
                rows.append([name, method.upper(), *[format_metric(row[c]) for c in columns]])
        table(f"Baseline {group} results. Dashes indicate undefined metrics.",
              ["Representation", "Method", *headings], rows)
    return "\n".join(tables) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("conventional", "openl3", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    content = result_tables(args.conventional, args.openl3)
    with args.output.open("x") as output:
        output.write(content)


if __name__ == "__main__":
    main()
