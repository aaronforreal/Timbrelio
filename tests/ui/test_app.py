import json
import wave

from streamlit.testing.v1 import AppTest


def write_wav(path):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8_000)
        audio.writeframes(b"\x00\x00" * 80)


def test_app_starts_with_bundled_coordinates(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)

    app = AppTest.from_file("app.py", default_timeout=15).run()

    assert not app.exception
    assert app.radio[0].label == "Colour points by"
    assert app.radio[0].value == "Genre"
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


def test_selected_track_details_survive_colour_change(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)
    monkeypatch.delenv("TIMBRELIO_AUDIO_ROOT", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15)
    app.session_state["selected_track_id"] = "TRK-0001"
    app.run()

    assert not app.exception
    assert app.subheader[0].value == "Velvet Morning"
    assert app.button[0].label == "Audio unavailable"
    assert app.button[0].disabled

    app.radio[0].set_value("Cluster").run()

    assert not app.exception
    assert app.session_state["selected_track_id"] == "TRK-0001"
    assert app.subheader[0].value == "Velvet Morning"
    figure = json.loads(app.get("plotly_chart")[0].proto.spec)
    selected_ids = [
        trace["customdata"][index][0]
        for trace in figure["data"]
        for index in trace.get("selectedpoints", [])
    ]
    assert selected_ids == ["TRK-0001"]


def test_plot_selection_uses_embedded_track_id(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15)
    app.session_state["coordinate-map"] = {
        "selection": {
            "points": [
                {
                    "point_index": 0,
                    "customdata": ["TRK-0001", "Velvet Morning", "Jazz", "0"],
                }
            ],
            "point_indices": [0],
            "box": [],
            "lasso": [],
        }
    }
    app.run()

    assert not app.exception
    assert app.session_state["selected_track_id"] == "TRK-0001"
    assert app.subheader[0].value == "Velvet Morning"


def test_selected_track_with_valid_audio_renders_player(monkeypatch, tmp_path):
    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    write_wav(audio_root / "clip.wav")
    artifact = tmp_path / "coordinates.csv"
    artifact.write_text(
        "track_id,x,y,title,artist,genre,cluster,representation,audio_path\n"
        "TRK-1,0,1,First Light,Example Artist,Jazz,0,Conventional,clip.wav\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(artifact))
    monkeypatch.setenv("TIMBRELIO_AUDIO_ROOT", str(audio_root))
    app = AppTest.from_file("app.py", default_timeout=15)
    app.session_state["selected_track_id"] = "TRK-1"
    app.run()

    assert not app.exception
    assert app.subheader[0].value == "First Light"
    assert len(app.get("audio")) == 1
    assert any("Example Artist" in block.value for block in app.markdown)
    assert any("Jazz" in block.value for block in app.markdown)
    assert any("Cluster" in block.value for block in app.markdown)
    assert any(
        "Track ID: TRK-1 · Representation: Conventional" in caption.value
        for caption in app.caption
    )


def test_unsafe_audio_path_is_not_rendered(monkeypatch, tmp_path):
    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    private_clip = tmp_path / "private.wav"
    write_wav(private_clip)
    artifact = tmp_path / "coordinates.csv"
    artifact.write_text(
        "track_id,x,y,title,genre,cluster,audio_path\n"
        f"TRK-1,0,1,First Light,Jazz,0,{private_clip}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(artifact))
    monkeypatch.setenv("TIMBRELIO_AUDIO_ROOT", str(audio_root))
    app = AppTest.from_file("app.py", default_timeout=15)
    app.session_state["selected_track_id"] = "TRK-1"
    app.run()

    assert not app.exception
    assert app.button[0].label == "Audio unavailable"
    assert str(private_clip) not in str(app)


def test_stale_selected_track_is_cleared_without_crashing(monkeypatch):
    monkeypatch.delenv("TIMBRELIO_COORDINATES_PATH", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15)
    app.session_state["selected_track_id"] = "TRK-missing"
    app.run()

    assert not app.exception
    assert app.session_state["selected_track_id"] is None
    assert (
        app.warning[0].value
        == "The selected track is no longer available in this map."
    )

