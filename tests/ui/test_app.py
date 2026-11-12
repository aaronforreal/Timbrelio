from streamlit.testing.v1 import AppTest


def test_app_starts_with_bundled_coordinates(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)

    app = AppTest.from_file("app.py", default_timeout=15).run()

    assert not app.exception
    assert app.radio[0].label == "Colour points by"
    assert app.radio[0].value == "Genre"
    assert app.selectbox[0].label == "Representation"
    assert app.selectbox[0].value == "Conventional"
    assert [widget.label for widget in app.multiselect] == ["Genres", "Clusters"]
    assert len(app.get("plotly_chart")) == 1


def test_app_switches_map_colour_mode(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15).run()

    app.radio[0].set_value("Cluster").run()

    assert not app.exception
    assert app.radio[0].value == "Cluster"
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


def test_app_filters_genres_and_resets_to_complete_view(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15).run()

    app.multiselect[0].set_value(["Jazz"]).run()

    assert not app.exception
    assert app.multiselect[0].value == ["Jazz"]
    assert any("5 of 20 tracks" in block.value for block in app.markdown)
    assert len(app.get("plotly_chart")) == 1

    app.button[0].click().run()

    assert not app.exception
    assert set(app.multiselect[0].value) == {
        "Electronic",
        "Folk",
        "Jazz",
        "Rock",
        "Unassigned",
    }
    assert len(app.get("plotly_chart")) == 1


def test_app_handles_zero_filter_results(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15).run()

    app.multiselect[0].set_value([]).run()

    assert not app.exception
    assert len(app.get("plotly_chart")) == 0
    assert any("No tracks match" in message.value for message in app.info)


def test_app_switches_saved_representations(monkeypatch, tmp_path):
    artifact = tmp_path / "representations.csv"
    artifact.write_text(
        "track_id,x,y,title,genre,cluster,representation\n"
        "TRK-1,0,1,First,Jazz,0,Conventional\n"
        "TRK-1,4,5,First,Jazz,2,OpenL3\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(artifact))
    app = AppTest.from_file("app.py", default_timeout=15).run()

    app.selectbox[0].set_value("OpenL3").run()

    assert not app.exception
    assert app.selectbox[0].value == "OpenL3"
    assert len(app.get("plotly_chart")) == 1

    app.button[0].click().run()

    assert not app.exception
    assert app.selectbox[0].value == "Conventional"

