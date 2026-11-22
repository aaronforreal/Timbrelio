from pathlib import Path

import pandas as pd
import pytest

from timbrelio.ui.neighbours import (
    NeighbourDataError,
    neighbours_for_seed,
    read_neighbours,
)
from timbrelio.ui.track import UNAVAILABLE_VALUE


def write_neighbours(path: Path, rows: str, metric: str = "distance") -> None:
    path.write_text(
        "seed_track_id,representation,neighbour_track_id,rank," + metric + "\n" + rows,
        encoding="utf-8",
    )


def coordinate_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "track_id": ["SEED", "N-1", "N-2", "N-3", "N-4", "N-5"],
            "title": ["Seed", "One", "Two", "Three", "Four", "Five"],
            "artist": ["Artist"] * 6,
            "genre": ["Jazz"] * 6,
            "cluster": ["0"] * 6,
        }
    )


def test_read_neighbours_accepts_saved_distance_results(tmp_path):
    artifact = tmp_path / "neighbours.csv"
    write_neighbours(artifact, "SEED,Conventional,N-1,1,0.125\n")

    neighbours = read_neighbours(artifact)

    assert "distance" in neighbours
    assert neighbours.loc[0, "rank"] == 1
    assert neighbours.loc[0, "distance"] == pytest.approx(0.125)


def test_similarity_metric_is_preserved_for_display(tmp_path):
    artifact = tmp_path / "neighbours.csv"
    write_neighbours(
        artifact,
        "SEED,Conventional,N-1,1,0.875\n",
        metric="similarity",
    )

    results = neighbours_for_seed(
        read_neighbours(artifact),
        coordinate_frame(),
        seed_track_id="SEED",
        representation="Conventional",
    )

    assert results[0].metric_name == "similarity"
    assert results[0].metric_value == pytest.approx(0.875)


@pytest.mark.parametrize(
    ("header", "message"),
    [
        (
            "seed_track_id,representation,rank,distance\nSEED,Conventional,1,0.1\n",
            "neighbour_track_id",
        ),
        (
            "seed_track_id,representation,neighbour_track_id,rank\n"
            "SEED,Conventional,N-1,1\n",
            "exactly one metric",
        ),
        (
            "seed_track_id,representation,neighbour_track_id,rank,distance\n"
            "SEED,Conventional,N-1,6,0.1\n",
            "Ranks must",
        ),
    ],
)
def test_read_neighbours_rejects_invalid_contract(tmp_path, header, message):
    artifact = tmp_path / "invalid.csv"
    artifact.write_text(header, encoding="utf-8")

    with pytest.raises(NeighbourDataError, match=message):
        read_neighbours(artifact)


def test_results_preserve_rank_and_exclude_seed_and_duplicate_ids(tmp_path):
    artifact = tmp_path / "neighbours.csv"
    write_neighbours(
        artifact,
        "SEED,Conventional,SEED,1,0.0\n"
        "SEED,Conventional,N-1,2,0.1\n"
        "SEED,Conventional,N-1,3,0.2\n"
        "SEED,Conventional,N-2,4,0.3\n"
        "SEED,OpenL3,N-3,1,0.05\n",
    )

    results = neighbours_for_seed(
        read_neighbours(artifact),
        coordinate_frame(),
        seed_track_id="SEED",
        representation="conventional",
    )

    assert [(result.rank, result.track_id) for result in results] == [
        (2, "N-1"),
        (4, "N-2"),
    ]


def test_results_return_five_in_saved_order_with_joined_metadata(tmp_path):
    artifact = tmp_path / "neighbours.csv"
    write_neighbours(
        artifact,
        "SEED,Conventional,N-3,3,0.3\n"
        "SEED,Conventional,N-1,1,0.1\n"
        "SEED,Conventional,N-5,5,0.5\n"
        "SEED,Conventional,N-2,2,0.2\n"
        "SEED,Conventional,N-4,4,0.4\n",
    )

    results = neighbours_for_seed(
        read_neighbours(artifact),
        coordinate_frame(),
        seed_track_id="SEED",
        representation="Conventional",
    )

    assert [result.track_id for result in results] == [
        "N-1",
        "N-2",
        "N-3",
        "N-4",
        "N-5",
    ]
    assert results[0].title == "One"
    assert results[0].metric_name == "distance"
    assert results[0].on_map


def test_result_missing_from_map_keeps_rank_with_unavailable_metadata(tmp_path):
    artifact = tmp_path / "neighbours.csv"
    write_neighbours(artifact, "SEED,Conventional,NOT-ON-MAP,1,0.1\n")

    results = neighbours_for_seed(
        read_neighbours(artifact),
        coordinate_frame(),
        seed_track_id="SEED",
        representation="Conventional",
    )

    assert len(results) == 1
    assert results[0].track_id == "NOT-ON-MAP"
    assert results[0].title == UNAVAILABLE_VALUE
    assert not results[0].on_map
