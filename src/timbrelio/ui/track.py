"""Stable track selection, detail lookup, and safe local audio handling."""

from __future__ import annotations

import wave
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

UNAVAILABLE_VALUE = "Unavailable"
DEFAULT_REPRESENTATION = "Conventional"
UNAVAILABLE_AUDIO_STATUSES = {
    "corrupt",
    "error",
    "failed",
    "invalid",
    "missing",
    "unavailable",
}
AUDIO_MIME_TYPES = {
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
}


@dataclass(frozen=True)
class TrackDetails:
    """User-facing metadata for one stable track ID."""

    track_id: str
    title: str
    artist: str
    genre: str
    cluster: str
    representation: str
    audio_path: str | None
    audio_status: str | None


@dataclass(frozen=True)
class AudioSource:
    """Validated playback source with a path-free user-facing status."""

    path: Path | None
    mime_type: str | None
    message: str

    @property
    def available(self) -> bool:
        return self.path is not None and self.mime_type is not None


def selected_track_id_from_event(event: Mapping[str, Any] | None) -> str | None:
    """Extract the stable track ID embedded in a Plotly point selection."""

    if not event:
        return None
    selection = event.get("selection")
    if not isinstance(selection, Mapping):
        return None
    points = selection.get("points")
    if not isinstance(points, Sequence) or not points:
        return None
    point = points[0]
    if not isinstance(point, Mapping):
        return None
    custom_data = point.get("customdata")
    if not isinstance(custom_data, Sequence) or isinstance(custom_data, (str, bytes)):
        return None
    if not custom_data:
        return None
    track_id = str(custom_data[0]).strip()
    return track_id or None


def track_details_for_id(
    coordinates: pd.DataFrame, track_id: str
) -> TrackDetails | None:
    """Look up detail fields by stable track ID rather than row position."""

    matches = coordinates.loc[coordinates["track_id"].astype(str).eq(track_id)]
    if matches.empty:
        return None
    row = matches.iloc[0]
    return TrackDetails(
        track_id=track_id,
        title=_display_value(row.get("title")),
        artist=_display_value(row.get("artist")),
        genre=_display_value(row.get("genre")),
        cluster=_display_value(row.get("cluster")),
        representation=_display_value(
            row.get("representation"), fallback=DEFAULT_REPRESENTATION
        ),
        audio_path=_optional_value(row.get("audio_path")),
        audio_status=_optional_value(row.get("audio_status")),
    )


def resolve_audio_source(
    audio_reference: str | None,
    audio_root: Path,
    *,
    declared_status: str | None = None,
) -> AudioSource:
    """Validate an audio reference without exposing its local path to the UI."""

    if declared_status and declared_status.casefold() in UNAVAILABLE_AUDIO_STATUSES:
        return _unavailable("This track is marked as unavailable.")
    if not audio_reference:
        return _unavailable("No local audio is available for this track.")

    try:
        root = audio_root.resolve(strict=False)
        reference = Path(audio_reference)
        candidate = (
            reference.resolve(strict=False)
            if reference.is_absolute()
            else (root / reference).resolve(strict=False)
        )
        candidate.relative_to(root)
    except (OSError, ValueError):
        return _unavailable(
            "Audio is unavailable because its configured location is not permitted."
        )

    mime_type = AUDIO_MIME_TYPES.get(candidate.suffix.casefold())
    if mime_type is None:
        return _unavailable("The configured audio format is not supported.")
    try:
        if not candidate.is_file() or candidate.stat().st_size == 0:
            return _unavailable("No local audio is available for this track.")
        if not _has_valid_audio_header(candidate):
            return _unavailable("The local audio file could not be played.")
    except OSError:
        return _unavailable("The local audio file could not be read.")

    return AudioSource(path=candidate, mime_type=mime_type, message="Audio ready.")


def _display_value(value: object, *, fallback: str = UNAVAILABLE_VALUE) -> str:
    optional = _optional_value(value)
    return optional if optional is not None else fallback


def _optional_value(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _has_valid_audio_header(path: Path) -> bool:
    suffix = path.suffix.casefold()
    if suffix == ".wav":
        try:
            with wave.open(str(path), "rb") as audio:
                return (
                    audio.getnchannels() > 0
                    and audio.getframerate() > 0
                    and audio.getnframes() > 0
                )
        except (EOFError, wave.Error):
            return False

    with path.open("rb") as audio_file:
        header = audio_file.read(16)
    if suffix == ".flac":
        return header.startswith(b"fLaC")
    if suffix == ".m4a":
        return len(header) >= 8 and header[4:8] == b"ftyp"
    if suffix == ".mp3":
        return header.startswith(b"ID3") or (
            len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0
        )
    if suffix == ".ogg":
        return header.startswith(b"OggS")
    return False


def _unavailable(message: str) -> AudioSource:
    return AudioSource(path=None, mime_type=None, message=message)
