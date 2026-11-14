# Meet's objective 1: projection and clustering

This experiment takes a track-feature CSV and creates PCA and UMAP maps, k-means and HDBSCAN clusters, and quantitative evaluation. It is designed to work with either conventional features or learned embeddings; run it separately for each representation. These methods operate on standardized original features, not on the 2-D map. The program does not extract audio features.

## Install and run

From the repository root, with Python 3.11 or 3.12:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[analysis,dev]"
python -m timbrelio.evaluate path/to/features.csv results/conventional
```

Input: one row per track, a unique `track_id`, at least two numeric feature columns, and optional `genre` and `title` columns. IDs are read as strings to preserve leading zeroes. Missing or infinite feature values and duplicate IDs are rejected so alignment errors do not silently affect the results. Remove other metadata columns (such as file paths) before running. Use the same exact rows when comparing representations, so that differences are meaningful. The upstream pipeline is still being developed, so its eventual file format may need an adapter.

Output: `pca_kmeans.csv`, `pca_hdbscan.csv`, `umap_kmeans.csv`, `umap_hdbscan.csv`, and `metrics.json`. Each map CSV contains `track_id,x,y,cluster` and any supplied title/genre, and can be loaded by the existing app using `TIMBRELIO_COORDINATES_PATH`. Cluster -1 means HDBSCAN noise. Keep results in separate directories per run: existing outputs with the same names are overwritten.

```bash
# Example with changed parameters
python -m timbrelio.evaluate features.csv results/experiment2 --seed 42 --clusters 8 --neighbors 5 --umap-neighbors 15 --umap-min-dist 0.1 --min-cluster-size 15 --min-samples 5
```

The default k-means value of eight reflects the FMA Small genre count; it is a starting choice, not a claim that eight natural clusters exist. Defaults require more than 15 tracks. UMAP is seeded and uses one thread for repeatability; exact results and timing can still vary with platform and library versions. Timings measure fitting only, and UMAP's first run can include JIT compilation. Metrics and package versions are saved with the configuration.

## Metrics and interpretation

- **Trustworthiness:** how well each map avoids introducing false neighbours; higher is better. Original-space distances are cosine, map distances Euclidean. The configured neighbour count must be less than half the sample size.
- **Neighbour overlap:** average fraction of the original cosine-space k nearest neighbours retained among the Euclidean map's k nearest neighbours; higher is better. Both exclude the track itself.
- **Silhouette:** separation of clusters in standardized feature space using Euclidean distance; higher is better. HDBSCAN noise is excluded. It is `null` if fewer than two clusters or too few assigned points make it undefined.
- **Adjusted Rand index (ARI):** agreement between the cluster assignments and the supplied genre labels, adjusted for chance. Missing genres are excluded and HDBSCAN noise is treated as a cluster label. It is `null` when fewer than two labelled rows are available. Genre is an imperfect proxy for perceived similarity.
- **Noise rate:** fraction of all tracks labelled -1. K-means has no noise by design.

The different distance choices are intentional: cosine is the project's retrieval-space measure, whereas k-means and HDBSCAN use Euclidean distance on standardized features. Scores do not establish listening quality on their own. For FMA-scale datasets, trustworthiness and silhouette may be computationally intensive and memory-hungry. Store raw audio and generated results outside Git.

## Check the implementation

```bash
pytest tests/test_evaluate.py
```

Real FMA comparisons require the feature CSVs and genre labels from the dataset pipeline. No FMA experiment or quantitative finding is claimed by the code alone.

To exercise the complete workflow without FMA, generate a **synthetic** example and run it:

```bash
python examples/make_synthetic_features.py
python -m timbrelio.evaluate synthetic_features.csv results/synthetic --clusters 4
```

Its results test the workflow only; they are not findings about music.
