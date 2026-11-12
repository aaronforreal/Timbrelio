"""Streamlit entry point for the Timbrelio browser."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from timbrelio.ui.data import CoordinateDataError, read_coordinates
from timbrelio.ui.filters import (
    default_representation,
    filter_coordinates,
    reconcile_selected_track,
    sorted_options,
)
from timbrelio.ui.map import build_coordinate_map
from timbrelio.ui.theme import APP_CSS

DEFAULT_COORDINATES_PATH = Path("data/sample_coordinates.csv")
REPRESENTATION_FILTER_KEY = "map_representation"
GENRE_FILTER_KEY = "map_genres"
CLUSTER_FILTER_KEY = "map_clusters"


@st.cache_data(show_spinner=False)
def load_coordinates(path: str, modified_at: int | None):
    """Load an immutable coordinate artifact once per path and file change."""

    del modified_at
    return read_coordinates(Path(path))


def configured_coordinates_path() -> Path:
    """Return the configured artifact path or the bundled sample."""

    return Path(os.environ.get("TIMBRELIO_COORDINATES_PATH", DEFAULT_COORDINATES_PATH))


def reset_map_filters(
    representation: str, genres: list[str], clusters: list[str]
) -> None:
    """Restore the complete default map view."""

    st.session_state[REPRESENTATION_FILTER_KEY] = representation
    st.session_state[GENRE_FILTER_KEY] = genres
    st.session_state[CLUSTER_FILTER_KEY] = clusters


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

    representations = sorted_options(coordinates["representation"])
    genres = sorted_options(coordinates["genre"])
    clusters = sorted_options(coordinates["cluster"])
    default_representation_name = default_representation(representations)

    if st.session_state.get(REPRESENTATION_FILTER_KEY) not in representations:
        st.session_state[REPRESENTATION_FILTER_KEY] = default_representation_name
    if GENRE_FILTER_KEY not in st.session_state:
        st.session_state[GENRE_FILTER_KEY] = genres
    else:
        st.session_state[GENRE_FILTER_KEY] = [
            genre for genre in st.session_state[GENRE_FILTER_KEY] if genre in genres
        ]
    if CLUSTER_FILTER_KEY not in st.session_state:
        st.session_state[CLUSTER_FILTER_KEY] = clusters
    else:
        st.session_state[CLUSTER_FILTER_KEY] = [
            cluster
            for cluster in st.session_state[CLUSTER_FILTER_KEY]
            if cluster in clusters
        ]

    with st.container(border=True):
        st.markdown("#### Refine the map")
        filter_columns = st.columns((1, 2, 2))
        with filter_columns[0]:
            st.selectbox(
                "Representation",
                options=representations,
                key=REPRESENTATION_FILTER_KEY,
                help="Choose which saved feature representation to explore.",
            )
        with filter_columns[1]:
            st.multiselect(
                "Genres",
                options=genres,
                key=GENRE_FILTER_KEY,
                help="Select one or more genres. Missing labels appear as Unassigned.",
            )
        with filter_columns[2]:
            st.multiselect(
                "Clusters",
                options=clusters,
                key=CLUSTER_FILTER_KEY,
                help="Select one or more clusters, including Noise or Unassigned.",
            )
        st.button(
            "Reset filters",
            on_click=reset_map_filters,
            args=(default_representation_name, genres, clusters),
        )

    active_representation = st.session_state[REPRESENTATION_FILTER_KEY]
    filtered_coordinates = filter_coordinates(
        coordinates,
        representation=active_representation,
        genres=st.session_state[GENRE_FILTER_KEY],
        clusters=st.session_state[CLUSTER_FILTER_KEY],
    )
    representation_total = int(
        coordinates["representation"].eq(active_representation).sum()
    )

    selected_track_id, selection_cleared = reconcile_selected_track(
        st.session_state.get("selected_track_id"),
        filtered_coordinates["track_id"],
    )
    st.session_state["selected_track_id"] = selected_track_id
    if selection_cleared:
        st.info("The selected track was cleared because it is outside the active filters.")

    color_label = st.radio(
        "Colour points by",
        options=("Genre", "Cluster"),
        horizontal=True,
        help="The legend and point colours update without changing track coordinates.",
    )

    st.markdown(
        f'<div class="map-meta"><span>{active_representation.upper()} · '
        f'{color_label.upper()}</span><strong>{len(filtered_coordinates):,} of '
        f"{representation_total:,} tracks</strong></div>",
        unsafe_allow_html=True,
    )

    if filtered_coordinates.empty:
        st.info(
            "No tracks match this filter combination. Adjust the filters or reset "
            "them to restore the complete map.",
            icon="ℹ️",
        )
        return

    st.plotly_chart(
        build_coordinate_map(filtered_coordinates, color_by=color_label.lower()),
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

