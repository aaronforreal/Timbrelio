"""Correctness at collection scale; deliberately no wall-clock assertions."""

import json
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from benchmark_browser import write_fixture


def plotted_ids(app):
    figure = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert all(trace["type"] == "scattergl" for trace in figure["data"])
    return {row[0] for trace in figure["data"] for row in trace["customdata"]}


def test_full_collection_filter_selection_projection_and_comparison(tmp_path, monkeypatch):
    coords, neighbours = write_fixture(tmp_path)
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(coords))
    monkeypatch.setenv("TIMBRELIO_NEIGHBOURS_PATH", str(neighbours))
    monkeypatch.setenv("TIMBRELIO_OPENL3_NEIGHBOURS_PATH", str(neighbours))
    app = AppTest.from_file("app.py", default_timeout=20).run()
    assert not app.exception
    assert len(plotted_ids(app)) == 8000
    app.session_state["coordinate-map"] = {
        "selection": {"points": [{"customdata": ["SYN-00000"]}]},
    }
    app.run()
    assert app.session_state["selected_track_id"] == "SYN-00000"
    app.multiselect(key="map_genres").set_value(["Genre 0"]).run()
    assert plotted_ids(app) == {f"SYN-{i:05d}" for i in range(0, 8000, 8)}
    app.radio(key="map_projection").set_value("PCA").run()
    app.selectbox(key="map_representation").set_value("OpenL3").run()
    assert not app.exception
    assert app.session_state["selected_track_id"] == "SYN-00000"
    app.radio(key="neighbour-view").set_value("Compare Conventional / OpenL3").run()
    assert not app.exception
    assert sum(c.value.startswith("RANK ") for c in app.caption) == 10
    app.multiselect(key="map_genres").set_value([]).run()
    assert app.session_state["selected_track_id"] is None
    assert not app.get("plotly_chart")
    assert not app.subheader
    next(b for b in app.button if b.label == "Reset filters").click().run()
    assert not app.exception
    assert len(plotted_ids(app)) == 8000
