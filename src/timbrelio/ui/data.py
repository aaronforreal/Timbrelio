"""Coordinate artifact loading and validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("track_id", "x", "y")
UNAVAILABLE_TITLE = "Unavailable"
UNASSIGNED_LABEL = "Unassigned"
NOISE_LABEL = "Noise"


class CoordinateDataError(ValueError):
    """Raised when a coordinate artifact violates the browser contract."""


def read_coordinates(path: Path) -> pd.DataFrame:
    """Read and validate saved two-dimensional track coordinates from CSV."""

    if not path.exists():
        raise FileNotFoundError(f"Coordinate artifact not found: {path}")
    if not path.is_file():
        raise CoordinateDataError(f"Coordinate artifact is not a file: {path}")
    if path.suffix.lower() != ".csv":
        raise CoordinateDataError("Coordinate artifacts must use CSV format for this starter.")

    try:
        coordinates = pd.read_csv(path)
    except pd.errors.EmptyDataError as error:
        raise CoordinateDataError(
            "Coordinate artifact has no header. Expected track_id, x, and y."
        ) from error
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        raise CoordinateDataError(f"Coordinate artifact is not a readable CSV: {error}") from error

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in coordinates.columns
    ]
    if missing_columns:
        raise CoordinateDataError(
            "Coordinate artifact is missing required columns: "
            + ", ".join(missing_columns)
        )

    coordinates = coordinates.copy()
    coordinates["track_id"] = coordinates["track_id"].astype("string").str.strip()

    missing_ids = coordinates["track_id"].isna() | coordinates["track_id"].eq("")
    if missing_ids.any():
        raise CoordinateDataError("Every coordinate row must have a non-empty track_id.")
    if coordinates["track_id"].duplicated().any():
        duplicate_ids = coordinates.loc[
            coordinates["track_id"].duplicated(keep=False), "track_id"
        ].unique()
        preview = ", ".join(str(track_id) for track_id in duplicate_ids[:3])
        raise CoordinateDataError(f"track_id values must be unique. Duplicates: {preview}")

    for axis in ("x", "y"):
        numeric_values = pd.to_numeric(coordinates[axis], errors="coerce")
        invalid_values = numeric_values.isna() | ~np.isfinite(numeric_values)
        if invalid_values.any():
            raise CoordinateDataError(f"Column {axis} must contain only finite numbers.")
        coordinates[axis] = numeric_values.astype(float)

    coordinates["title"] = _normalized_text_column(
        coordinates, "title", fallback=UNAVAILABLE_TITLE
    )
    coordinates["genre"] = _normalized_text_column(
        coordinates, "genre", fallback=UNASSIGNED_LABEL
    )
    coordinates["cluster"] = _normalized_cluster_column(coordinates)

    return coordinates


def _normalized_text_column(
    coordinates: pd.DataFrame, column: str, *, fallback: str
) -> pd.Series:
    """Return trimmed display text with missing values made explicit."""

    if column not in coordinates:
        return pd.Series(fallback, index=coordinates.index, dtype="string")

    values = coordinates[column].astype("string").str.strip()
    return values.mask(values.isna() | values.eq(""), fallback)


def _normalized_cluster_column(coordinates: pd.DataFrame) -> pd.Series:
    """Normalize cluster labels while preserving HDBSCAN's noise category."""

    values = _normalized_text_column(
        coordinates, "cluster", fallback=UNASSIGNED_LABEL
    )
    numeric_values = pd.to_numeric(values, errors="coerce")
    is_integer = (
        np.isfinite(numeric_values) & numeric_values.mod(1).eq(0)
    ).fillna(False)
    integer_values = (
        numeric_values.where(is_integer).round().astype("Int64").astype("string")
    )
    values = values.mask(is_integer, integer_values)
    return values.mask(numeric_values.eq(-1).fillna(False), NOISE_LABEL)

