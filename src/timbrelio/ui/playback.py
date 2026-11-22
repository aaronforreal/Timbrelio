"""Ordered playback models for comparing a seed track with its neighbours."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from timbrelio.ui.neighbours import NeighbourResult
from timbrelio.ui.track import (
    AudioSource,
    TrackDetails,
    resolve_audio_source,
    track_details_for_id,
)


@dataclass(frozen=True)
class PlaybackRow:
    """One stable row in the seed-then-neighbour listening order."""

    label: str
    rank: int | None
    track_id: str
    title: str
    artist: str
    genre: str
    cluster: str
    audio_source: AudioSource

    @property
    def component_key(self) -> str:
        """Return a stable widget identity independent of dataframe row positions."""

        role = "seed" if self.rank is None else f"rank-{self.rank}"
        return f"comparison-playback-{role}-{self.track_id}"


def comparison_playback_rows(
    seed: TrackDetails,
    neighbours: list[NeighbourResult],
    coordinates: pd.DataFrame,
    audio_root: Path,
) -> list[PlaybackRow]:
    """Build seed-first rows while preserving every saved neighbour rank."""

    rows = [_row_from_details("Seed", None, seed, audio_root)]
    for result in neighbours:
        details = track_details_for_id(coordinates, result.track_id)
        if details is None:
            rows.append(
                PlaybackRow(
                    label=f"Rank {result.rank}",
                    rank=result.rank,
                    track_id=result.track_id,
                    title=result.title,
                    artist=result.artist,
                    genre=result.genre,
                    cluster=result.cluster,
                    audio_source=resolve_audio_source(None, audio_root),
                )
            )
            continue
        rows.append(
            _row_from_details(f"Rank {result.rank}", result.rank, details, audio_root)
        )
    return rows


def _row_from_details(
    label: str,
    rank: int | None,
    details: TrackDetails,
    audio_root: Path,
) -> PlaybackRow:
    return PlaybackRow(
        label=label,
        rank=rank,
        track_id=details.track_id,
        title=details.title,
        artist=details.artist,
        genre=details.genre,
        cluster=details.cluster,
        audio_source=resolve_audio_source(
            details.audio_path,
            audio_root,
            declared_status=details.audio_status,
        ),
    )
