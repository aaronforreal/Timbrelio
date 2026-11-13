import pandas as pd
import plotly.graph_objects as go

from timbrelio.ui.data import NOISE_LABEL, UNASSIGNED_LABEL
from timbrelio.ui.map import build_coordinate_map, category_color_map
from timbrelio.ui.theme import COLORS


def coordinate_frame():
    return pd.DataFrame(
        {
            "track_id": ["TRK-1", "TRK-2", "TRK-3"],
            "x": [-1.0, 0.5, 2.0],
            "y": [0.0, 1.5, -0.5],
            "title": ["First Light", "Night Drive", "Open Window"],
            "genre": ["Jazz", "Rock", UNASSIGNED_LABEL],
            "cluster": ["0", "1", NOISE_LABEL],
        }
    )


def test_build_coordinate_map_preserves_rows_and_track_ids():
    coordinates = coordinate_frame()

    figure = build_coordinate_map(coordinates)

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 1
    assert list(figure.data[0].x) == [-1.0, 0.5, 2.0]
    assert list(figure.data[0].y) == [0.0, 1.5, -0.5]
    assert [item[0] for item in figure.data[0].customdata] == [
        "TRK-1",
        "TRK-2",
        "TRK-3",
    ]
    assert figure.data[0].marker.color == COLORS["mocha_cream"]


def test_category_color_map_is_stable_across_label_order():
    forward = category_color_map(["Rock", "Jazz", "Folk"])
    reverse = category_color_map(["Folk", "Jazz", "Rock"])

    assert forward == reverse
    assert forward["Jazz"] == category_color_map(["Jazz"])["Jazz"]
    assert len(set(forward.values())) == len(forward)


def test_category_color_map_distinguishes_noise_and_unassigned():
    colors = category_color_map([NOISE_LABEL, UNASSIGNED_LABEL])

    assert colors[NOISE_LABEL] == COLORS["muted_ink"]
    assert colors[UNASSIGNED_LABEL] == COLORS["mocha_cream"]
    assert colors[NOISE_LABEL] != colors[UNASSIGNED_LABEL]


def test_coloured_map_has_labelled_legend_and_track_aligned_hover_data():
    figure = build_coordinate_map(coordinate_frame(), color_by="genre")

    assert figure.layout.showlegend is True
    assert figure.layout.legend.title.text == "Genre"
    assert {trace.name for trace in figure.data} == {"Jazz", "Rock", UNASSIGNED_LABEL}

    hover_rows = {
        row[0]: tuple(row[1:])
        for trace in figure.data
        for row in trace.customdata
    }
    assert hover_rows == {
        "TRK-1": ("First Light", "Jazz", "0"),
        "TRK-2": ("Night Drive", "Rock", "1"),
        "TRK-3": ("Open Window", UNASSIGNED_LABEL, NOISE_LABEL),
    }
    assert "Genre: %{customdata[2]}" in figure.data[0].hovertemplate


def test_coloured_map_uses_non_colour_selected_marker_cue():
    figure = build_coordinate_map(coordinate_frame(), color_by="cluster")

    for trace in figure.data:
        assert trace.selected.marker.size == 13
        assert trace.selected.marker.opacity == 1
        assert trace.unselected.marker.opacity == 0.35


def test_map_viewport_revision_changes_only_with_coordinate_source():
    pca = build_coordinate_map(
        coordinate_frame(), color_by="genre", viewport_key="Conventional-PCA"
    )
    recolored_pca = build_coordinate_map(
        coordinate_frame(), color_by="cluster", viewport_key="Conventional-PCA"
    )
    umap = build_coordinate_map(
        coordinate_frame(), color_by="genre", viewport_key="Conventional-UMAP"
    )

    assert pca.layout.uirevision == recolored_pca.layout.uirevision
    assert pca.layout.uirevision != umap.layout.uirevision

