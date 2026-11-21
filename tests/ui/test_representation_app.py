import wave

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in (
        "TIMBRELIO_COORDINATES_PATH", "TIMBRELIO_NEIGHBOURS_PATH",
        "TIMBRELIO_OPENL3_NEIGHBOURS_PATH", "TIMBRELIO_AUDIO_ROOT",
    ):
        monkeypatch.delenv(name, raising=False)


def comparison_app(seed="TRK-0001"):
    app = AppTest.from_file("app.py", default_timeout=15)
    app.session_state["selected_track_id"] = seed
    app.run()
    assert app.radio(key="neighbour-view").value == "Single representation"
    app.radio(key="neighbour-view").set_value("Compare Conventional / OpenL3").run()
    assert not app.exception
    return app


def test_both_lists_same_seed_and_shared_rows_have_unique_widget_keys():
    app = comparison_app()
    assert [s.value for s in app.subheader][-2:] == ["Conventional", "OpenL3"]
    assert sum(c.value == "Seed: TRK-0001" for c in app.caption) == 2
    assert sum(c.value.startswith("RANK ") for c in app.caption) == 10
    assert sum(m.value == "Shared by both representations" for m in app.markdown) == 6
    assert sum("Only in " in m.value for m in app.markdown) == 4
    keys = [b.key for b in app.button]
    assert len(keys) == len(set(keys))
    app.button(key="representations-OpenL3-locate-TRK-0009").click().run()
    assert not app.exception
    assert app.session_state["selected_track_id"] == "TRK-0001"
    assert app.session_state["highlighted_neighbour_id"] == "TRK-0009"
    app.radio[0].set_value("Cluster").run()
    assert not app.exception
    assert sum(c.value.startswith("RANK ") for c in app.caption) == 10
    app.radio(key="neighbour-view").set_value("Single representation").run()
    assert not app.exception
    assert sum(c.value.startswith("RANK ") for c in app.caption) == 5


@pytest.mark.parametrize("bad_side", ["Conventional", "OpenL3"])
@pytest.mark.parametrize("bad_kind", ["missing", "corrupt", "empty", "other-seed"])
def test_one_side_unavailable_keeps_other_side(monkeypatch, tmp_path, bad_side, bad_kind):
    path = tmp_path / "bad.csv"
    if bad_kind == "corrupt":
        path.write_text("wrong,header\nx,y\n")
    elif bad_kind in ("empty", "other-seed"):
        path.write_text(
            "seed_track_id,representation,neighbour_track_id,rank,distance\n"
            + (f"OTHER,{bad_side},TRK-0006,1,0.1\n" if bad_kind == "other-seed" else "")
        )
    # Set both paths explicitly so custom conventional input does not imply
    # that OpenL3 should be read from the same combined artifact.
    monkeypatch.setenv("TIMBRELIO_NEIGHBOURS_PATH", "data/sample_neighbours.csv")
    monkeypatch.setenv("TIMBRELIO_OPENL3_NEIGHBOURS_PATH", "data/sample_openl3_neighbours.csv")
    monkeypatch.setenv(
        "TIMBRELIO_NEIGHBOURS_PATH" if bad_side == "Conventional"
        else "TIMBRELIO_OPENL3_NEIGHBOURS_PATH", str(path),
    )
    app = comparison_app()
    assert sum(c.value.startswith("RANK ") for c in app.caption) == 5
    assert any("Overlap is incomplete" in i.value for i in app.info)
    assert not any("Only in " in m.value for m in app.markdown)
    assert str(path) not in str(app)


def test_combined_artifact_ranks_metrics_partial_lists_and_seed_isolation(monkeypatch, tmp_path):
    saved = tmp_path / "combined.csv"
    saved.write_text(
        "seed_track_id,representation,neighbour_track_id,rank,similarity\n"
        "TRK-0001,Conventional,TRK-0006,3,0.8\n"
        "TRK-0001,Conventional,TRK-0001,1,1\n"
        "TRK-0001,Conventional,TRK-0006,4,0.7\n"
        "TRK-0001,OpenL3,TRK-0009,5,0.6\n"
        "TRK-0002,OpenL3,TRK-0008,1,0.9\n"
    )
    monkeypatch.setenv("TIMBRELIO_NEIGHBOURS_PATH", str(saved))
    app = comparison_app()
    assert [c.value for c in app.caption if c.value.startswith("RANK ")] == [
        "RANK 3 · TRK-0006", "RANK 5 · TRK-0009",
    ]
    assert any(c.value == "Similarity 0.600" for c in app.caption)
    assert sum("Only 1 of 5" in w.value for w in app.warning) == 2
    app.session_state["selected_track_id"] = "TRK-0002"
    app.run()
    assert not app.exception
    assert sum(c.value == "Seed: TRK-0002" for c in app.caption) == 2
    assert [c.value for c in app.caption if c.value.startswith("RANK ")] == [
        "RANK 1 · TRK-0008",
    ]


def test_custom_coordinates_do_not_use_synthetic_neighbours(monkeypatch, tmp_path):
    path = tmp_path / "coords.csv"
    path.write_text("track_id,x,y\nTRK-0001,0,0\n")
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(path))
    app = comparison_app()
    assert sum(c.value.startswith("RANK ") for c in app.caption) == 0
    assert len(app.warning) == 2


def test_both_sides_audio_matches_ids_and_missing_clips_keep_rank(monkeypatch, tmp_path):
    with wave.open(str(tmp_path / "clip.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 80)
    with wave.open(str(tmp_path / "first.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x01\x00" * 80)
    coords = tmp_path / "coords.csv"
    coords.write_text(
        "track_id,x,y,title,audio_path\n"
        "SEED,0,0,Seed,clip.wav\nA,1,1,First,first.wav\nB,2,2,Second,missing.wav\n"
    )
    saved = tmp_path / "saved.csv"
    saved.write_text(
        "seed_track_id,representation,neighbour_track_id,rank,distance\n"
        "SEED,Conventional,A,1,0.1\nSEED,Conventional,B,2,0.2\n"
        "SEED,OpenL3,B,1,0.3\nSEED,OpenL3,A,2,0.4\n"
    )
    monkeypatch.setenv("TIMBRELIO_COORDINATES_PATH", str(coords))
    monkeypatch.setenv("TIMBRELIO_NEIGHBOURS_PATH", str(saved))
    monkeypatch.setenv("TIMBRELIO_AUDIO_ROOT", str(tmp_path))
    app = comparison_app("SEED")
    assert len(app.get("audio")) == 3  # one seed plus A on both sides
    players = app.get("audio")
    assert players[0].proto.url != players[1].proto.url
    assert players[1].proto.url == players[2].proto.url
    unavailable = [b.key for b in app.button if b.label == "Audio unavailable"]
    assert unavailable == [
        "Conventional-comparison-playback-rank-2-B-unavailable",
        "OpenL3-comparison-playback-rank-1-B-unavailable",
    ]


def test_off_map_neighbour_keeps_rank_without_locate_or_audio(monkeypatch, tmp_path):
    saved = tmp_path / "saved.csv"
    saved.write_text(
        "seed_track_id,representation,neighbour_track_id,rank,distance\n"
        "TRK-0001,OpenL3,OFF-MAP,4,0.1\n"
    )
    monkeypatch.setenv("TIMBRELIO_OPENL3_NEIGHBOURS_PATH", str(saved))
    app = comparison_app()
    assert any(c.value == "RANK 4 · OFF-MAP" for c in app.caption)
    assert app.button(key="representations-OpenL3-locate-OFF-MAP").disabled
    assert app.button(key="OpenL3-comparison-playback-rank-4-OFF-MAP-unavailable").disabled
