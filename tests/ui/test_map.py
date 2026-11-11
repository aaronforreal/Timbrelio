import pandas as pd
import plotly.graph_objects as go

from timbrelio.ui.map import build_coordinate_map
from timbrelio.ui.theme import COLORS


def test_build_coordinate_map_preserves_rows_and_track_ids():
    coordinates = pd.DataFrame(
        {
            "track_id": ["TRK-1", "TRK-2", "TRK-3"],
            "x": [-1.0, 0.5, 2.0],
            "y": [0.0, 1.5, -0.5],
        }
    )

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

