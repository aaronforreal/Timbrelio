"""Bounded, read-only caches keyed by each saved artifact's file version."""

from pathlib import Path

import pandas as pd
import streamlit as st

from timbrelio.ui.data import read_coordinates
from timbrelio.ui.neighbours import index_neighbours, read_neighbours


def artifact_version(path: Path) -> tuple[str, int, int, int]:
    """Resolve aliases and detect edits, replacements, and file-size changes.

    Stat on every access, including cache hits. Missing files therefore never
    return a previously cached table. Artifact producers must publish a changed
    timestamp or size; byte changes preserving all metadata are not detected.
    """

    resolved = path.resolve(strict=True)
    info = resolved.stat()
    return str(resolved), info.st_mtime_ns, info.st_ctime_ns, info.st_size


@st.cache_data(show_spinner=False, max_entries=8)
def _coordinates(version: tuple[str, int, int, int]) -> pd.DataFrame:
    return read_coordinates(Path(version[0]))


@st.cache_data(show_spinner=False, max_entries=8)
def _neighbours(version: tuple[str, int, int, int]) -> pd.DataFrame:
    return index_neighbours(read_neighbours(Path(version[0])))


def load_coordinates(path: Path) -> pd.DataFrame:
    """Return an isolated copy of validated coordinates for this file version."""

    return _coordinates(artifact_version(path))


def load_neighbours(path: Path) -> pd.DataFrame:
    """Return indexed, validated original-space results for this file version."""

    return _neighbours(artifact_version(path))
