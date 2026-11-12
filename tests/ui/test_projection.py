import pandas as pd
import pytest

from timbrelio.ui.projection import (
    active_representation,
    available_projections,
    coordinates_for_projection,
    default_projection,
    reconcile_selected_track,
)


def projection_frame():
    return pd.DataFrame(
        {
            "track_id": ["TRK-1", "TRK-2", "TRK-1", "TRK-3", "OPEN-1"],
            "representation": [
                "Conventional",
                "Conventional",
                "Conventional",
                "Conventional",
                "OpenL3",
            ],
            "projection": ["PCA", "PCA", "UMAP", "UMAP", "PCA"],
            "x": [1.0, 2.0, 10.0, 30.0, 100.0],
            "y": [3.0, 4.0, 20.0, 40.0, 200.0],
        }
    )


def test_projection_options_are_scoped_to_active_representation():
    coordinates = projection_frame()

    representation = active_representation(coordinates)

    assert representation == "Conventional"
    assert available_projections(
        coordinates, representation=representation
    ) == ["PCA", "UMAP"]
    assert available_projections(
        coordinates, representation="OpenL3"
    ) == ["PCA"]


def test_projection_selection_uses_only_saved_target_coordinates():
    selected = coordinates_for_projection(
        projection_frame(), representation="Conventional", projection="UMAP"
    )

    assert selected["track_id"].tolist() == ["TRK-1", "TRK-3"]
    assert selected["x"].tolist() == [10.0, 30.0]
    assert selected["y"].tolist() == [20.0, 40.0]


def test_projection_selection_rejects_unsupported_method():
    with pytest.raises(ValueError, match="projection must be one of: PCA, UMAP"):
        coordinates_for_projection(
            projection_frame(),
            representation="Conventional",
            projection="t-SNE",
        )


def test_default_projection_prefers_umap_and_falls_back_to_saved_option():
    assert default_projection(["PCA", "UMAP"]) == "UMAP"
    assert default_projection(["PCA"]) == "PCA"


def test_selection_is_preserved_only_when_track_exists_in_target_projection():
    retained = reconcile_selected_track("TRK-1", ["TRK-1", "TRK-3"])
    cleared = reconcile_selected_track("TRK-2", ["TRK-1", "TRK-3"])

    assert retained == ("TRK-1", False)
    assert cleared == (None, True)
