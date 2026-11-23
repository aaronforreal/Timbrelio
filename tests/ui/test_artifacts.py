"""Cache correctness checks; performance measurements live in scripts/."""

import os

import pandas as pd
import pytest

from timbrelio.ui.artifacts import load_coordinates, load_neighbours
from timbrelio.ui.neighbours import neighbours_for_seed


@pytest.mark.parametrize("kind", ["coordinates", "neighbours"])
def test_cached_artifacts_invalidate_and_return_isolated_copies(tmp_path, monkeypatch, kind):
    path = tmp_path / "saved.csv"
    if kind == "coordinates":
        header = "track_id,x,y,title\n"
        row = "SEED,0,0,First\n"
        field, first, second = "title", "First", "Changed title"
        load = load_coordinates
    else:
        header = "seed_track_id,representation,neighbour_track_id,rank,distance\n"
        row = "SEED,Conventional,N-1,1,0.1\n"
        field, first, second = "neighbour_track_id", "N-1", "N-200"
        load = load_neighbours
    path.write_text(header + row, encoding="utf-8")
    reads = []
    original = pd.read_csv

    def counted(*args, **kwargs):
        reads.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", counted)
    result = load(path)
    result[field] = "caller mutation"
    assert load(path)[field].iloc[0] == first
    assert len(reads) == 1
    # Size change must invalidate even if a producer preserves mtime.
    saved_mtime = path.stat().st_mtime_ns
    path.write_text(header + row.replace(first, second), encoding="utf-8")
    os.utime(path, ns=(saved_mtime, saved_mtime))
    assert load(path)[field].iloc[0] == second
    assert len(reads) == 2
    # Normal same-size edit must also invalidate.
    third = second.replace(second[0], "Z", 1)
    path.write_text(header + row.replace(first, third), encoding="utf-8")
    os.utime(path, ns=(saved_mtime + 1_000_000_000, saved_mtime + 1_000_000_000))
    assert load(path)[field].iloc[0] == third
    assert len(reads) == 3
    path.unlink()
    with pytest.raises(FileNotFoundError):
        load(path)


def test_indexed_neighbours_keep_partial_lists_casefolding_and_missing_seeds(tmp_path):
    path = tmp_path / "saved.csv"
    path.write_text(
        "seed_track_id,representation,neighbour_track_id,rank,distance\n"
        "SEED,Conventional,N-1,4,0.4\n", encoding="utf-8",
    )
    saved = load_neighbours(path)
    coordinates = pd.DataFrame({"track_id": ["N-1"], "title": ["First"]})
    results = neighbours_for_seed(saved, coordinates, seed_track_id="SEED", representation="CONVENTIONAL")
    assert [(r.track_id, r.rank, r.title) for r in results] == [("N-1", 4, "First")]
    assert neighbours_for_seed(saved, coordinates, seed_track_id="MISSING", representation="Conventional") == []
