"""Reproduce the synthetic 8,000-track browser benchmark (separate from pytest)."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import tempfile
from time import perf_counter
from unittest.mock import patch

import numpy as np
import pandas as pd
import plotly
import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def write_fixture(directory: Path, tracks: int = 8000) -> tuple[Path, Path]:
    """Save 8,000 stable IDs in each of four maps, with five results per seed."""
    rng = np.random.default_rng(497)
    ids = np.array([f"SYN-{index:05d}" for index in range(tracks)])
    frames = []
    neighbours = []
    for representation in ("Conventional", "OpenL3"):
        for projection in ("PCA", "UMAP"):
            frames.append(pd.DataFrame({
                "track_id": ids, "representation": representation,
                "projection": projection, "x": rng.normal(size=tracks),
                "y": rng.normal(size=tracks), "title": [f"Sample {i}" for i in range(tracks)],
                "artist": "Synthetic fixture", "genre": [f"Genre {i % 8}" for i in range(tracks)],
                "cluster": np.arange(tracks) % 12,
            }))
        for rank in range(1, 6):
            neighbours.append(pd.DataFrame({
                "seed_track_id": ids, "representation": representation,
                "neighbour_track_id": np.roll(ids, -rank), "rank": rank,
                "distance": rank / 10,
            }))
    directory.mkdir(parents=True, exist_ok=True)
    coordinates_path, neighbours_path = directory / "coordinates.csv", directory / "neighbours.csv"
    pd.concat(frames, ignore_index=True).to_csv(coordinates_path, index=False)
    pd.concat(neighbours, ignore_index=True).to_csv(neighbours_path, index=False)
    return coordinates_path, neighbours_path


def run_benchmark(repeats: int) -> dict:
    samples: dict[str, list[float]] = {}
    reads: Counter = Counter()
    original_read = pd.read_csv

    def counted_read(path, *args, **kwargs):
        reads[Path(path).name] += 1
        return original_read(path, *args, **kwargs)

    with tempfile.TemporaryDirectory(prefix="timbrelio-a9-") as directory:
        coords, neighbours = write_fixture(Path(directory))
        environment = {
            "TIMBRELIO_COORDINATES_PATH": str(coords),
            "TIMBRELIO_NEIGHBOURS_PATH": str(neighbours),
            "TIMBRELIO_OPENL3_NEIGHBOURS_PATH": str(neighbours),
        }
        with patch.dict(os.environ, environment), patch.object(pd, "read_csv", counted_read):
            st.cache_data.clear()
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)

            def measure(name, action):
                start = perf_counter()
                action()
                elapsed = perf_counter() - start
                assert not app.exception, app.exception
                samples.setdefault(name, []).append(elapsed)

            measure("cold_load", app.run)
            # Prime caches and comparison dependencies before measuring warm actions.
            app.session_state["selected_track_id"] = "SYN-00000"
            app.run()
            app.radio(key="neighbour-view").set_value("Compare Conventional / OpenL3").run()
            app.radio(key="neighbour-view").set_value("Single representation").run()
            reads_before = reads.copy()
            for index in range(repeats):
                measure("filter", lambda: app.multiselect(key="map_genres").set_value(["Genre 0", "Genre 1"]).run())
                measure("filter_reset", lambda: next(b for b in app.button if b.label == "Reset filters").click().run())

                def select():
                    seed = f"SYN-{(index + 1) % 8000:05d}"
                    app.session_state["coordinate-map"] = {"selection": {"points": [{"customdata": [seed]}]}}
                    app.run()
                    assert app.session_state["selected_track_id"] == seed
                measure("selection", select)
                projection = "PCA" if index % 2 == 0 else "UMAP"
                measure("projection", lambda: app.radio(key="map_projection").set_value(projection).run())
                representation = "OpenL3" if index % 2 == 0 else "Conventional"
                measure("representation", lambda: app.selectbox(key="map_representation").set_value(representation).run())
                measure("comparison", lambda: app.radio(key="neighbour-view").set_value("Compare Conventional / OpenL3").run())
                app.radio(key="neighbour-view").set_value("Single representation").run()
            warm_reads = dict(reads - reads_before)

    return {
        "environment": {"python": platform.python_version(), "os": platform.platform(),
                        "cpu": platform.processor(), "logical_cpus": os.cpu_count(),
                        "pandas": pd.__version__, "numpy": np.__version__,
                        "streamlit": st.__version__, "plotly": plotly.__version__},
        "fixture": {"seed": 497, "tracks_per_map": 8000, "coordinate_rows": 32000,
                    "neighbour_rows": 80000, "audio": "unavailable (synthetic)"},
        "scope": "AppTest server reruns including chart serialization; excludes network and browser paint",
        "warm_csv_reads": warm_reads,
        "seconds": {name: {"median": statistics.median(values), "max": max(values), "runs": values}
                    for name, values in samples.items()},
        "warm_filter_selection_under_2s": all(
            value < 2 for name in ("filter", "filter_reset", "selection") for value in samples[name]
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-fixture", type=Path)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    os.chdir(ROOT)
    if args.write_fixture:
        write_fixture(args.write_fixture)
    result = run_benchmark(args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: round(value["median"], 4) for name, value in result["seconds"].items()}))
    print(f"Warm CSV reads: {result['warm_csv_reads']}")
    if not result["warm_filter_selection_under_2s"]:
        raise SystemExit("Cached filter/selection threshold exceeded")


if __name__ == "__main__":
    main()
