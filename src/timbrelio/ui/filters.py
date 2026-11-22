"""Track-aligned filtering for the interactive coordinate map."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from timbrelio.ui.data import DEFAULT_REPRESENTATION


def sorted_options(values: Iterable[object]) -> list[str]:
    """Return stable, unique display options."""

    return sorted({str(value) for value in values}, key=str.casefold)


def default_representation(representations: Iterable[object]) -> str:
    """Prefer the conventional representation, or the first available option."""

    options = sorted_options(representations)
    if not options:
        raise ValueError("At least one representation is required.")
    if DEFAULT_REPRESENTATION in options:
        return DEFAULT_REPRESENTATION
    return options[0]


def filter_coordinates(
    coordinates: pd.DataFrame,
    *,
    representation: str,
    genres: Iterable[str],
    clusters: Iterable[str],
) -> pd.DataFrame:
    """Return rows matching all filters without changing track identity."""

    matches = (
        coordinates["representation"].eq(representation)
        & coordinates["genre"].isin(set(genres))
        & coordinates["cluster"].isin(set(clusters))
    )
    return coordinates.loc[matches].copy()


def reconcile_selected_track(
    selected_track_id: str | None, visible_track_ids: Iterable[object]
) -> tuple[str | None, bool]:
    """Clear selection when its stable track ID is no longer visible."""

    if selected_track_id is None:
        return None, False
    if selected_track_id in {str(track_id) for track_id in visible_track_ids}:
        return selected_track_id, False
    return None, True
