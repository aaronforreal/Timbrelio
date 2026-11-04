from streamlit.testing.v1 import AppTest


def test_app_starts_with_bundled_coordinates(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)

    app = AppTest.from_file("app.py", default_timeout=15).run()

    assert not app.exception
    assert len(app.get("plotly_chart")) == 1


def test_app_reports_invalid_artifact(monkeypatch, tmp_path):
    invalid_artifact = tmp_path / "invalid.csv"
    invalid_artifact.write_text("track_id,x\nTRK-1,1\n", encoding="utf-8")
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(invalid_artifact))

    app = AppTest.from_file("app.py", default_timeout=15).run()

    assert not app.exception
    assert app.error[0].value == "The coordinate map could not be loaded."


def test_app_explains_empty_artifact(monkeypatch, tmp_path):
    empty_artifact = tmp_path / "empty.csv"
    empty_artifact.write_text("track_id,x,y\n", encoding="utf-8")
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(empty_artifact))

    app = AppTest.from_file("app.py", default_timeout=15).run()

    assert not app.exception
    assert "contains no tracks yet" in app.info[-1].value
    assert len(app.get("plotly_chart")) == 0

