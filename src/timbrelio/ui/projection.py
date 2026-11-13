"""Saved projection discovery, selection, and state reconciliation."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from timbrelio.ui.data import DEFAULT_REPRESENTATION

SUPPORTED_PROJECTIONS = ("PCA", "UMAP")


def active_representation(coordinates: pd.DataFrame) -> str:
    """Choose a deterministic representation until A3 exposes its filter."""

    representations = sorted(
        {str(value) for value in coordinates["representation"]}, key=str.casefold
    )
    if not representations:
        raise ValueError("At least one representation is required.")
    if DEFAULT_REPRESENTATION in representations:
        return DEFAULT_REPRESENTATION
    return representations[0]


def available_projections(
    coordinates: pd.DataFrame, *, representation: str
) -> list[str]:
    """Return supported saved projections in a stable comparison order."""

    saved = {
        str(value)
        for value in coordinates.loc[
            coordinates["representation"].eq(representation), "projection"
        ]
    }
    return [projection for projection in SUPPORTED_PROJECTIONS if projection in saved]


def default_projection(projections: Iterable[str]) -> str:
    """Prefer UMAP for browsing, falling back to the first saved projection."""

    options = list(projections)
    if not options:
        raise ValueError("At least one supported projection is required.")
    return "UMAP" if "UMAP" in options else options[0]


def coordinates_for_projection(
    coordinates: pd.DataFrame, *, representation: str, projection: str
) -> pd.DataFrame:
    """Select one saved coordinate set without fitting a projection at runtime."""

    if projection not in SUPPORTED_PROJECTIONS:
        supported = ", ".join(SUPPORTED_PROJECTIONS)
        raise ValueError(f"projection must be one of: {supported}")
    matches = coordinates["representation"].eq(representation) & coordinates[
        "projection"
    ].eq(projection)
    return coordinates.loc[matches].copy()


def reconcile_selected_track(
    selected_track_id: str | None, projected_track_ids: Iterable[object]
) -> tuple[str | None, bool]:
    """Retain a stable selection only when it exists in the target projection."""

    if selected_track_id is None:
        return None, False
    visible_ids = {str(track_id) for track_id in projected_track_ids}
    if selected_track_id in visible_ids:
        return selected_track_id, False
    return None, True
