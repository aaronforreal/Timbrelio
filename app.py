"""Streamlit entry point for the Timbrelio browser."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from timbrelio.ui.data import CoordinateDataError, read_coordinates
from timbrelio.ui.map import build_coordinate_map
from timbrelio.ui.projection import (
    active_representation,
    available_projections,
    coordinates_for_projection,
    default_projection,
    reconcile_selected_track,
)
from timbrelio.ui.theme import APP_CSS

DEFAULT_COORDINATES_PATH = Path("data/sample_coordinates.csv")
PROJECTION_KEY = "map_projection"
SELECTED_TRACK_KEY = "selected_track_id"


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

    representation = active_representation(coordinates)
    projections = available_projections(coordinates, representation=representation)
    if not projections:
        st.warning(
            "This artifact has no supported PCA or UMAP coordinates. Add a "
            "`projection` column with saved `PCA` or `UMAP` rows.",
            icon="⚠️",
        )
        return

    if st.session_state.get(PROJECTION_KEY) not in projections:
        st.session_state[PROJECTION_KEY] = default_projection(projections)

    active_projection = st.radio(
        "Projection",
        options=projections,
        key=PROJECTION_KEY,
        horizontal=True,
        disabled=len(projections) == 1,
        help="Switch between saved coordinates; Timbrelio never fits PCA or UMAP here.",
    )
    if len(projections) == 1:
        st.caption(
            f"Only {active_projection} coordinates are available for "
            f"{representation}."
        )

    projected_coordinates = coordinates_for_projection(
        coordinates,
        representation=representation,
        projection=active_projection,
    )
    selected_track_id, selection_cleared = reconcile_selected_track(
        st.session_state.get(SELECTED_TRACK_KEY),
        projected_coordinates["track_id"],
    )
    st.session_state[SELECTED_TRACK_KEY] = selected_track_id
    if selection_cleared:
        st.info(
            "The selected track was cleared because it is unavailable in "
            f"the {active_projection} projection."
        )

    color_label = st.radio(
        "Colour points by",
        options=("Genre", "Cluster"),
        horizontal=True,
        help="The legend and point colours update without changing track coordinates.",
    )

    st.markdown(
        f'<div class="map-meta"><span>{representation.upper()} · '
        f'{active_projection} · {color_label.upper()}</span>'
        f"<strong>{len(projected_coordinates):,} tracks</strong></div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        build_coordinate_map(
            projected_coordinates,
            color_by=color_label.lower(),
            viewport_key=f"{representation}-{active_projection}",
        ),
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
    st.caption(
        "Projection changes only the saved map coordinates. Neighbours are retrieved "
        "from the original feature space, not from 2-D map distance."
    )


if __name__ == "__main__":
    main()

