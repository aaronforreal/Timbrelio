"""Streamlit entry point for the Timbrelio browser."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from timbrelio.ui.data import CoordinateDataError, read_coordinates
from timbrelio.ui.map import build_coordinate_map
from timbrelio.ui.neighbours import (
    RESULT_LIMIT,
    NeighbourDataError,
    NeighbourResult,
    neighbours_for_seed,
    read_neighbours,
)
from timbrelio.ui.theme import APP_CSS
from timbrelio.ui.track import (
    AudioSource,
    TrackDetails,
    resolve_audio_source,
    selected_track_id_from_event,
    track_details_for_id,
)

DEFAULT_COORDINATES_PATH = Path("data/sample_coordinates.csv")
DEFAULT_AUDIO_ROOT = Path("data/audio")
DEFAULT_NEIGHBOURS_PATH = Path("data/sample_neighbours.csv")
SELECTED_TRACK_KEY = "selected_track_id"
HIGHLIGHTED_NEIGHBOUR_KEY = "highlighted_neighbour_id"


@st.cache_data(show_spinner=False)
def load_coordinates(path: str, modified_at: int | None):
    """Load an immutable coordinate artifact once per path and file change."""

    del modified_at
    return read_coordinates(Path(path))


@st.cache_data(show_spinner=False)
def load_neighbours(path: str, modified_at: int | None):
    """Load immutable, precomputed neighbour results once per file change."""

    del modified_at
    return read_neighbours(Path(path))


def configured_coordinates_path() -> Path:
    """Return the configured artifact path or the bundled sample."""

    return Path(os.environ.get("TIMBRELIO_COORDINATES_PATH", DEFAULT_COORDINATES_PATH))


def configured_audio_root() -> Path:
    """Return the root under which manifest audio references are allowed."""

    return Path(os.environ.get("TIMBRELIO_AUDIO_ROOT", DEFAULT_AUDIO_ROOT))


def configured_neighbours_path() -> Path:
    """Return the configured saved-neighbour artifact or bundled sample."""

    return Path(os.environ.get("TIMBRELIO_NEIGHBOURS_PATH", DEFAULT_NEIGHBOURS_PATH))


def render_track_details(details: TrackDetails, audio_source: AudioSource) -> None:
    """Render selected-track metadata and a recoverable playback state."""

    with st.container(border=True):
        st.caption("SELECTED TRACK")
        st.subheader(details.title)
        metadata_columns = st.columns(3)
        metadata_columns[0].markdown(f"**Artist**  \n{details.artist}")
        metadata_columns[1].markdown(f"**Genre**  \n{details.genre}")
        metadata_columns[2].markdown(f"**Cluster**  \n{details.cluster}")
        st.caption(
            f"Track ID: {details.track_id} · Representation: {details.representation}"
        )
        if audio_source.available:
            st.audio(audio_source.path, format=audio_source.mime_type)
        else:
            st.button(
                "Audio unavailable",
                disabled=True,
                key=f"audio-unavailable-{details.track_id}",
            )
            st.caption(audio_source.message)


def render_neighbours(results: list[NeighbourResult]) -> None:
    """Render ranked saved results without replacing the selected seed track."""

    st.markdown("### Five nearest tracks")
    st.caption(
        "Saved results from the original standardized feature space — not distances "
        "on the two-dimensional map."
    )
    if not results:
        st.info("No saved neighbours are available for this track and representation.")
        return

    if len(results) < RESULT_LIMIT:
        st.warning(
            f"Only {len(results)} of {RESULT_LIMIT} saved neighbours are available."
        )

    for result in results:
        with st.container(border=True):
            identity, action = st.columns([4, 1])
            with identity:
                st.caption(f"RANK {result.rank} · {result.track_id}")
                st.markdown(f"**{result.title}**")
                st.caption(
                    f"{result.artist} · {result.genre} · Cluster {result.cluster} · "
                    f"{result.metric_name.title()} {result.metric_value:.3f}"
                )
            with action:
                if st.button(
                    "Locate on map",
                    key=f"locate-neighbour-{result.track_id}",
                    disabled=not result.on_map,
                    help=(
                        "Highlight this neighbour without changing the selected track."
                        if result.on_map
                        else "This neighbour is not present on the current map."
                    ),
                ):
                    st.session_state[HIGHLIGHTED_NEIGHBOUR_KEY] = result.track_id
                    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Timbrelio · Explore the soundscape",
        page_icon="◉",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

    coordinates_path = configured_coordinates_path()
    neighbours_path = configured_neighbours_path()

    with st.sidebar:
        st.markdown('<p class="brand-wordmark">timbrelio.</p>', unsafe_allow_html=True)
        st.markdown(
            "Browse a music collection by its projected audio characteristics. "
            "Select a point to inspect its metadata and play available local audio."
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
    selected_track_id = st.session_state.get(SELECTED_TRACK_KEY)
    selection_event = st.plotly_chart(
        build_coordinate_map(
            coordinates,
            color_by=color_label.lower(),
            selected_track_id=selected_track_id,
            highlighted_track_id=st.session_state.get(HIGHLIGHTED_NEIGHBOUR_KEY),
        ),
        use_container_width=True,
        theme=None,
        key="coordinate-map",
        on_select="rerun",
        selection_mode="points",
        config={
            "displaylogo": False,
            "responsive": True,
            "scrollZoom": True,
        },
    )
    event_track_id = selected_track_id_from_event(selection_event)
    if event_track_id is not None and event_track_id != selected_track_id:
        st.session_state[SELECTED_TRACK_KEY] = event_track_id
        st.session_state.pop(HIGHLIGHTED_NEIGHBOUR_KEY, None)
        st.rerun()
    st.caption(
        "Drag to pan, scroll to zoom, and use the Plotly home control to reset the map. "
        "Hover for metadata or select a point to inspect and play the track."
    )

    if selected_track_id is None:
        st.info("Select a point on the map to inspect its track details and audio.")
        return

    details = track_details_for_id(coordinates, selected_track_id)
    if details is None:
        st.session_state[SELECTED_TRACK_KEY] = None
        st.warning("The selected track is no longer available in this map.")
        return

    audio_source = resolve_audio_source(
        details.audio_path,
        configured_audio_root(),
        declared_status=details.audio_status,
    )
    render_track_details(details, audio_source)

    try:
        neighbours_modified_at = (
            neighbours_path.stat().st_mtime_ns if neighbours_path.exists() else None
        )
        neighbours = load_neighbours(
            str(neighbours_path),
            neighbours_modified_at,
        )
    except (NeighbourDataError, FileNotFoundError, OSError) as error:
        st.warning("Saved neighbours could not be loaded.", icon="⚠️")
        st.caption(str(error))
        return

    render_neighbours(
        neighbours_for_seed(
            neighbours,
            coordinates,
            seed_track_id=details.track_id,
            representation=details.representation,
        )
    )


if __name__ == "__main__":
    main()

