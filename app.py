"""Streamlit entry point for the Timbrelio browser."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from timbrelio.ui.data import CoordinateDataError, read_coordinates
from timbrelio.ui.map import build_coordinate_map
from timbrelio.ui.theme import APP_CSS

DEFAULT_COORDINATES_PATH = Path("data/sample_coordinates.csv")


@st.cache_data(show_spinner=False)
def load_coordinates(path: str, modified_at: int | None):
    """Load an immutable coordinate artifact once per path and file change."""

    del modified_at
    return read_coordinates(Path(path))


def configured_coordinates_path() -> Path:
    """Return the configured artifact path or the bundled sample."""

    return Path(os.environ.get("TIMBRELIO_COORDINATES_PATH", DEFAULT_COORDINATES_PATH))


def main() -> None:
    st.set_page_config(
        page_title="Timbrelio · Explore the soundscape",
        page_icon="◉",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

    coordinates_path = configured_coordinates_path()

    with st.sidebar:
        st.markdown('<p class="brand-wordmark">timbrelio.</p>', unsafe_allow_html=True)
        st.markdown(
            "Browse a music collection by its projected audio characteristics. "
            "Filters, playback, and neighbour comparison arrive in later deliverables."
        )
        st.divider()
        st.caption("ACTIVE ARTIFACT")
        if coordinates_path == DEFAULT_COORDINATES_PATH:
            st.info("Bundled sample coordinates", icon="ℹ️")
        else:
            st.success("Configured coordinate artifact", icon="✅")

    st.markdown(
        """
        <header class="hero">
          <p class="eyebrow">CONTENT-BASED MUSIC EXPLORATION</p>
          <h1>Explore the soundscape</h1>
          <p class="hero-copy">
            Navigate Timbrelio's saved two-dimensional track map and reveal
            how genres and clusters are distributed across the soundscape.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    try:
        modified_at = (
            coordinates_path.stat().st_mtime_ns if coordinates_path.exists() else None
        )
        coordinates = load_coordinates(str(coordinates_path), modified_at)
    except (CoordinateDataError, FileNotFoundError, OSError) as error:
        st.error("The coordinate map could not be loaded.", icon="⚠️")
        st.markdown(
            "Provide a readable CSV through `TIMBRELIO_COORDINATES_PATH` with "
            "the columns `track_id`, `x`, and `y`."
        )
        st.caption(str(error))
        st.stop()

    if coordinates.empty:
        st.info(
            "This coordinate artifact is valid but contains no tracks yet. "
            "Add projected rows to begin exploring.",
            icon="ℹ️",
        )
        return

    color_label = st.radio(
        "Colour points by",
        options=("Genre", "Cluster"),
        horizontal=True,
        help="The legend and point colours update without changing track coordinates.",
    )

    st.markdown(
        f'<div class="map-meta"><span>TRACK MAP · {color_label.upper()}</span>'
        f"<strong>{len(coordinates):,} tracks</strong></div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        build_coordinate_map(coordinates, color_by=color_label.lower()),
        use_container_width=True,
        theme=None,
        config={
            "displaylogo": False,
            "responsive": True,
            "scrollZoom": True,
        },
    )
    st.caption(
        "Drag to pan, scroll to zoom, and use the Plotly home control to reset the map. "
        "Hover over a point for its track, title, genre, and cluster."
    )


if __name__ == "__main__":
    main()

