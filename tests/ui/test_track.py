import wave

import pandas as pd

from timbrelio.ui.track import (
    DEFAULT_REPRESENTATION,
    UNAVAILABLE_VALUE,
    resolve_audio_source,
    selected_track_id_from_event,
    track_details_for_id,
)


def write_wav(path):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8_000)
        audio.writeframes(b"\x00\x00" * 80)


def test_selected_track_id_comes_from_custom_data_not_point_index():
    event = {
        "selection": {
            "points": [
                {
                    "point_index": 0,
                    "customdata": ["TRK-42", "Title", "Jazz", "2"],
                }
            ]
        }
    }

    assert selected_track_id_from_event(event) == "TRK-42"
    assert selected_track_id_from_event({"selection": {"points": []}}) is None
    assert selected_track_id_from_event(None) is None


def test_track_details_lookup_uses_stable_id_and_fallback_metadata():
    coordinates = pd.DataFrame(
        {
            "track_id": ["TRK-9", "TRK-2"],
            "title": ["Ninth", "Second"],
            "genre": ["Rock", "Jazz"],
            "cluster": ["1", "0"],
            "artist": ["Artist Nine", None],
        },
        index=[40, 3],
    )

    details = track_details_for_id(coordinates, "TRK-2")

    assert details is not None
    assert details.track_id == "TRK-2"
    assert details.title == "Second"
    assert details.artist == UNAVAILABLE_VALUE
    assert details.representation == DEFAULT_REPRESENTATION
    assert track_details_for_id(coordinates, "TRK-missing") is None


def test_valid_relative_wav_is_available_for_playback(tmp_path):
    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    clip = audio_root / "clip.wav"
    write_wav(clip)

    source = resolve_audio_source("clip.wav", audio_root)

    assert source.available
    assert source.path == clip.resolve()
    assert source.mime_type == "audio/wav"


def test_audio_outside_configured_root_is_rejected_without_path_leak(tmp_path):
    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    outside = tmp_path / "private.wav"
    write_wav(outside)

    relative_source = resolve_audio_source("../private.wav", audio_root)
    absolute_source = resolve_audio_source(str(outside), audio_root)

    assert not relative_source.available
    assert not absolute_source.available
    assert str(outside) not in relative_source.message
    assert str(outside) not in absolute_source.message
    assert "not permitted" in relative_source.message


def test_missing_corrupt_and_declared_unavailable_audio_are_recoverable(tmp_path):
    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    (audio_root / "corrupt.wav").write_bytes(b"not a wave")

    missing = resolve_audio_source("missing.wav", audio_root)
    corrupt = resolve_audio_source("corrupt.wav", audio_root)
    declared = resolve_audio_source(
        "clip.wav", audio_root, declared_status="unavailable"
    )

    assert not missing.available
    assert not corrupt.available
    assert not declared.available
    assert "could not be played" in corrupt.message
    assert "marked as unavailable" in declared.message
