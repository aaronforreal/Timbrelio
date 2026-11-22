import pandas as pd

from timbrelio.ui.filters import (
    default_representation,
    filter_coordinates,
    reconcile_selected_track,
    sorted_options,
)


def coordinate_frame():
    return pd.DataFrame(
        {
            "track_id": ["TRK-1", "TRK-2", "TRK-3", "TRK-1"],
            "representation": [
                "Conventional",
                "Conventional",
                "Conventional",
                "OpenL3",
            ],
            "genre": ["Jazz", "Rock", "Unassigned", "Jazz"],
            "cluster": ["0", "1", "Unassigned", "4"],
            "x": [0.0, 1.0, 2.0, 3.0],
            "y": [3.0, 2.0, 1.0, 0.0],
        }
    )


def test_filter_coordinates_combines_representation_genre_and_cluster():
    result = filter_coordinates(
        coordinate_frame(),
        representation="Conventional",
        genres=["Jazz", "Rock"],
        clusters=["1"],
    )

    assert result["track_id"].tolist() == ["TRK-2"]
    assert result.index.tolist() == [1]


def test_filter_coordinates_includes_explicit_missing_labels():
    result = filter_coordinates(
        coordinate_frame(),
        representation="Conventional",
        genres=["Unassigned"],
        clusters=["Unassigned"],
    )

    assert result["track_id"].tolist() == ["TRK-3"]


def test_empty_filter_selection_returns_no_rows():
    result = filter_coordinates(
        coordinate_frame(),
        representation="Conventional",
        genres=[],
        clusters=["0", "1", "Unassigned"],
    )

    assert result.empty


def test_filter_options_and_default_are_stable():
    assert sorted_options(["Rock", "Jazz", "Rock"]) == ["Jazz", "Rock"]
    assert default_representation(["OpenL3", "Conventional"]) == "Conventional"
    assert default_representation(["Learned B", "Learned A"]) == "Learned A"


def test_selection_is_preserved_only_while_track_is_visible():
    assert reconcile_selected_track("TRK-2", ["TRK-1", "TRK-2"]) == (
        "TRK-2",
        False,
    )
    assert reconcile_selected_track("TRK-2", ["TRK-1"]) == (None, True)
    assert reconcile_selected_track(None, ["TRK-1"]) == (None, False)
