import wave

import pandas as pd

from timbrelio.ui.neighbours import NeighbourResult
from timbrelio.ui.playback import comparison_playback_rows
from timbrelio.ui.track import TrackDetails


def write_wav(path):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8_000)
        audio.writeframes(b"\x00\x00" * 80)


def test_comparison_rows_are_seed_first_and_preserve_saved_ranks(tmp_path):
    coordinates = pd.DataFrame(
        {
            "track_id": ["SEED", "N-1", "N-2"],
            "title": ["Seed", "One", "Two"],
            "artist": ["Artist S", "Artist 1", "Artist 2"],
            "genre": ["Jazz", "Rock", "Pop"],
            "cluster": ["0", "1", "2"],
            "audio_path": [None, None, None],
        }
    )
    seed = TrackDetails(
        "SEED", "Seed", "Artist S", "Jazz", "0", "Conventional", None, None
    )
    neighbours = [
        NeighbourResult(
            1, "N-1", "One", "Artist 1", "Rock", "1", "distance", 0.1, True
        ),
        NeighbourResult(
            2, "N-2", "Two", "Artist 2", "Pop", "2", "distance", 0.2, True
        ),
    ]

    rows = comparison_playback_rows(seed, neighbours, coordinates, tmp_path)

    assert [(row.label, row.rank, row.track_id) for row in rows] == [
        ("Seed", None, "SEED"),
        ("Rank 1", 1, "N-1"),
        ("Rank 2", 2, "N-2"),
    ]
    assert len({row.component_key for row in rows}) == 3
    assert rows[1].component_key == "comparison-playback-rank-1-N-1"


def test_comparison_rows_keep_mixed_audio_states_without_shifting_ranks(tmp_path):
    audio_root = tmp_path / "audio"
    audio_root.mkdir()
    write_wav(audio_root / "seed.wav")
    write_wav(audio_root / "two.wav")
    coordinates = pd.DataFrame(
        {
            "track_id": ["SEED", "N-1", "N-2"],
            "title": ["Seed", "One", "Two"],
            "artist": ["Artist S", "Artist 1", "Artist 2"],
            "genre": ["Jazz", "Rock", "Pop"],
            "cluster": ["0", "1", "2"],
            "representation": ["Conventional"] * 3,
            "audio_path": ["seed.wav", "missing.wav", "two.wav"],
        }
    )
    seed = TrackDetails(
        "SEED",
        "Seed",
        "Artist S",
        "Jazz",
        "0",
        "Conventional",
        "seed.wav",
        None,
    )
    neighbours = [
        NeighbourResult(
            1, "N-1", "One", "Artist 1", "Rock", "1", "distance", 0.1, True
        ),
        NeighbourResult(
            2, "N-2", "Two", "Artist 2", "Pop", "2", "distance", 0.2, True
        ),
    ]

    rows = comparison_playback_rows(seed, neighbours, coordinates, audio_root)

    assert [row.rank for row in rows] == [None, 1, 2]
    assert [row.audio_source.available for row in rows] == [True, False, True]


def test_neighbour_missing_from_map_remains_visible_and_unavailable(tmp_path):
    coordinates = pd.DataFrame(
        {
            "track_id": ["SEED"],
            "title": ["Seed"],
            "artist": ["Artist S"],
            "genre": ["Jazz"],
            "cluster": ["0"],
        }
    )
    seed = TrackDetails(
        "SEED", "Seed", "Artist S", "Jazz", "0", "Conventional", None, None
    )
    neighbours = [
        NeighbourResult(
            3,
            "OFF-MAP",
            "Off Map",
            "Artist O",
            "Folk",
            "9",
            "distance",
            0.3,
            False,
        )
    ]

    rows = comparison_playback_rows(seed, neighbours, coordinates, tmp_path)

    assert [(row.rank, row.track_id, row.title) for row in rows] == [
        (None, "SEED", "Seed"),
        (3, "OFF-MAP", "Off Map"),
    ]
    assert not rows[1].audio_source.available
