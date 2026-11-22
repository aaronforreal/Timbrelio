"""Loading and presentation models for precomputed nearest neighbours."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from timbrelio.ui.track import UNAVAILABLE_VALUE

REQUIRED_COLUMNS = (
    "seed_track_id",
    "representation",
    "neighbour_track_id",
    "rank",
)
METRIC_COLUMNS = ("distance", "similarity")
RESULT_LIMIT = 5


class NeighbourDataError(ValueError):
    """Raised when a saved neighbour artifact violates the browser contract."""


@dataclass(frozen=True)
class NeighbourResult:
    """One ranked, display-ready neighbour from the original feature space."""

    rank: int
    track_id: str
    title: str
    artist: str
    genre: str
    cluster: str
    metric_name: str
    metric_value: float
    on_map: bool


def read_neighbours(path: Path) -> pd.DataFrame:
    """Read and validate a precomputed neighbour CSV without calculating results."""

    if not path.exists():
        raise FileNotFoundError(f"Neighbour artifact not found: {path}")
    if not path.is_file():
        raise NeighbourDataError(f"Neighbour artifact is not a file: {path}")
    if path.suffix.casefold() != ".csv":
        raise NeighbourDataError("Neighbour artifacts must use CSV format.")

    try:
        neighbours = pd.read_csv(path)
    except pd.errors.EmptyDataError as error:
        raise NeighbourDataError(
            "Neighbour artifact has no header. Expected seed and neighbour IDs."
        ) from error
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        raise NeighbourDataError(
            f"Neighbour artifact is not a readable CSV: {error}"
        ) from error

    missing = [column for column in REQUIRED_COLUMNS if column not in neighbours]
    if missing:
        raise NeighbourDataError(
            "Neighbour artifact is missing required columns: " + ", ".join(missing)
        )

    available_metrics = [column for column in METRIC_COLUMNS if column in neighbours]
    if len(available_metrics) != 1:
        raise NeighbourDataError(
            "Neighbour artifact must contain exactly one metric column: "
            "distance or similarity."
        )

    neighbours = neighbours.copy()
    for column in ("seed_track_id", "representation", "neighbour_track_id"):
        values = neighbours[column].astype("string").str.strip()
        if (values.isna() | values.eq("")).any():
            raise NeighbourDataError(f"Column {column} must not contain blank values.")
        neighbours[column] = values

    numeric_ranks = pd.to_numeric(neighbours["rank"], errors="coerce")
    valid_ranks = (
        numeric_ranks.notna()
        & np.isfinite(numeric_ranks)
        & numeric_ranks.mod(1).eq(0)
        & numeric_ranks.between(1, RESULT_LIMIT)
    )
    if not valid_ranks.all():
        raise NeighbourDataError("Ranks must be whole numbers from 1 through 5.")
    neighbours["rank"] = numeric_ranks.astype(int)

    metric = available_metrics[0]
    metric_values = pd.to_numeric(neighbours[metric], errors="coerce")
    if (metric_values.isna() | ~np.isfinite(metric_values)).any():
        raise NeighbourDataError(f"Column {metric} must contain only finite numbers.")
    neighbours[metric] = metric_values.astype(float)
    return neighbours


def neighbours_for_seed(
    neighbours: pd.DataFrame,
    coordinates: pd.DataFrame,
    *,
    seed_track_id: str,
    representation: str,
) -> list[NeighbourResult]:
    """Return up to five saved results, excluding the seed and duplicate IDs."""

    matches = neighbours.loc[
        neighbours["seed_track_id"].astype(str).eq(seed_track_id)
        & neighbours["representation"]
        .astype(str)
        .str.casefold()
        .eq(representation.casefold())
    ].sort_values("rank", kind="stable")

    metric_name = next(column for column in METRIC_COLUMNS if column in neighbours)
    coordinates_by_id = coordinates.assign(
        _track_id=coordinates["track_id"].astype(str)
    ).set_index("_track_id", drop=False)
    seen: set[str] = set()
    results: list[NeighbourResult] = []

    for row in matches.itertuples(index=False):
        neighbour_id = str(row.neighbour_track_id)
        if neighbour_id == seed_track_id or neighbour_id in seen:
            continue
        seen.add(neighbour_id)

        on_map = neighbour_id in coordinates_by_id.index
        metadata = coordinates_by_id.loc[neighbour_id] if on_map else None
        results.append(
            NeighbourResult(
                rank=int(row.rank),
                track_id=neighbour_id,
                title=_display_value(metadata, "title"),
                artist=_display_value(metadata, "artist"),
                genre=_display_value(metadata, "genre"),
                cluster=_display_value(metadata, "cluster"),
                metric_name=metric_name,
                metric_value=float(getattr(row, metric_name)),
                on_map=on_map,
            )
        )
        if len(results) == RESULT_LIMIT:
            break

    return results


def _display_value(metadata: pd.Series | None, field: str) -> str:
    if metadata is None or field not in metadata:
        return UNAVAILABLE_VALUE
    value = metadata[field]
    if value is None or pd.isna(value):
        return UNAVAILABLE_VALUE
    text = str(value).strip()
    return text or UNAVAILABLE_VALUE
