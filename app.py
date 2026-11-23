"""Streamlit entry point for the Timbrelio browser."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from timbrelio.ui.artifacts import load_coordinates, load_neighbours
from timbrelio.ui.data import CoordinateDataError
from timbrelio.ui.filters import (
    default_representation,
    filter_coordinates,
    reconcile_selected_track,
    sorted_options,
)
from timbrelio.ui.map import build_coordinate_map
from timbrelio.ui.neighbours import (
    RESULT_LIMIT,
    NeighbourDataError,
    NeighbourResult,
    neighbours_for_seed,
)
from timbrelio.ui.playback import PlaybackRow, comparison_playback_rows
from timbrelio.ui.representation import compare_neighbours
from timbrelio.ui.projection import (
    available_projections,
    coordinates_for_projection,
    default_projection,
)
from timbrelio.ui.theme import APP_CSS
from timbrelio.ui.track import (
    TrackDetails,
    selected_track_id_from_event,
    track_details_for_id,
)

DEFAULT_COORDINATES_PATH = Path("data/sample_coordinates.csv")
DEFAULT_AUDIO_ROOT = Path("data/audio")
DEFAULT_NEIGHBOURS_PATH = Path("data/sample_neighbours.csv")
DEFAULT_OPENL3_NEIGHBOURS_PATH = Path("data/sample_openl3_neighbours.csv")
SELECTED_TRACK_KEY = "selected_track_id"
HIGHLIGHTED_NEIGHBOUR_KEY = "highlighted_neighbour_id"


REPRESENTATION_FILTER_KEY = "map_representation"
GENRE_FILTER_KEY = "map_genres"
CLUSTER_FILTER_KEY = "map_clusters"
PROJECTION_KEY = "map_projection"


def configured_coordinates_path() -> Path:
    """Return the configured artifact path or the bundled sample."""

    return Path(os.environ.get("TIMBRELIO_COORDINATES_PATH", DEFAULT_COORDINATES_PATH))


def configured_audio_root() -> Path:
    """Return the root under which manifest audio references are allowed."""

    return Path(os.environ.get("TIMBRELIO_AUDIO_ROOT", DEFAULT_AUDIO_ROOT))


def configured_neighbours_path() -> Path:
    """Return the configured saved-neighbour artifact or bundled sample."""

    return Path(os.environ.get("TIMBRELIO_NEIGHBOURS_PATH", DEFAULT_NEIGHBOURS_PATH))


def configured_comparison_paths() -> dict[str, Path | None]:
    """Use explicit artifacts for custom data; never substitute sample results."""

    conventional = os.environ.get("TIMBRELIO_NEIGHBOURS_PATH")
    openl3 = os.environ.get("TIMBRELIO_OPENL3_NEIGHBOURS_PATH")
    sample_coordinates = configured_coordinates_path() == DEFAULT_COORDINATES_PATH
    return {
        "Conventional": Path(conventional) if conventional else (
            DEFAULT_NEIGHBOURS_PATH if sample_coordinates else None
        ),
        "OpenL3": Path(openl3 or conventional) if openl3 or conventional else (
            DEFAULT_OPENL3_NEIGHBOURS_PATH if sample_coordinates else None
        ),
    }


def render_track_details(details: TrackDetails) -> None:
    """Render selected-track metadata above the comparison workflow."""

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


def render_audio_control(row: PlaybackRow, *, namespace: str = "") -> None:
    """Render one available player or a rank-preserving disabled state."""

    if row.audio_source.available:
        st.audio(row.audio_source.path, format=row.audio_source.mime_type)
        return
    st.button(
        "Audio unavailable",
        disabled=True,
        key=f"{namespace}{row.component_key}-unavailable",
    )
    st.caption(row.audio_source.message)


def render_comparison_playback(
    seed: TrackDetails,
    results: list[NeighbourResult],
    coordinates: pd.DataFrame,
) -> None:
    """Render the seed and ranked neighbours in one listening workflow."""

    st.markdown("### Listen and compare")
    st.caption(
        "Play the selected seed first, then compare neighbours saved from the "
        "original standardized feature space in rank order."
    )
    rows = comparison_playback_rows(
        seed,
        results,
        coordinates,
        configured_audio_root(),
    )

    seed_row = rows[0]
    with st.container(border=True):
        st.caption(f"SEED · {seed_row.track_id}")
        st.markdown(f"**{seed_row.title}**")
        st.caption(
            f"{seed_row.artist} · {seed_row.genre} · Cluster {seed_row.cluster}"
        )
        render_audio_control(seed_row)

    if not results:
        st.info("No saved neighbours are available for this track and representation.")
        return

    if len(results) < RESULT_LIMIT:
        st.warning(
            f"Only {len(results)} of {RESULT_LIMIT} saved neighbours are available."
        )

    for result, row in zip(results, rows[1:], strict=True):
        with st.container(border=True):
            identity, action = st.columns([4, 1])
            with identity:
                st.caption(f"{row.label.upper()} · {row.track_id}")
                st.markdown(f"**{row.title}**")
                st.caption(
                    f"{row.artist} · {row.genre} · Cluster {row.cluster} · "
                    f"{result.metric_name.title()} {result.metric_value:.3f}"
                )
                render_audio_control(row)
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


def render_representation_comparison(
    seed: TrackDetails, coordinates: pd.DataFrame
) -> None:
    """Load each representation independently and compare the same seed ID."""

    st.markdown("### Compare representations")
    st.caption(
        "Both lists use the same seed and saved original standardized feature space "
        "results. Map distances are not used. Overlap describes these lists; "
        "it does not establish which representation sounds more similar."
    )
    st.caption(
        "Metric values are shown as saved, to three decimal places. "
        "Their scales may differ between representations."
    )
    if (
        configured_coordinates_path() == DEFAULT_COORDINATES_PATH
        and "TIMBRELIO_NEIGHBOURS_PATH" not in os.environ
        and "TIMBRELIO_OPENL3_NEIGHBOURS_PATH" not in os.environ
    ):
        st.info("Synthetic sample neighbour lists; these are not FMA retrieval results.")
    paths = configured_comparison_paths()
    results: dict[str, list[NeighbourResult]] = {}
    failures: set[str] = set()
    for representation, path in paths.items():
        try:
            if path is None:
                raise NeighbourDataError("No neighbour artifact configured.")
            saved = load_neighbours(path)
            results[representation] = neighbours_for_seed(
                saved, coordinates,
                seed_track_id=seed.track_id, representation=representation,
            )
        except (NeighbourDataError, FileNotFoundError, OSError):
            results[representation] = []
            failures.add(representation)

    overlap = compare_neighbours(results["Conventional"], results["OpenL3"])
    if all(results.values()):
        st.write(f"Shared neighbours: {len(overlap.shared)}")
    else:
        st.info("Overlap is incomplete because one or both saved lists are unavailable.")

    seed_row = comparison_playback_rows(seed, [], coordinates, configured_audio_root())[0]
    st.caption(f"SEED · {seed.track_id}")
    render_audio_control(seed_row, namespace="representations-seed-")

    # Streamlit stacks columns on narrow screens using the shared theme.
    for column, representation in zip(st.columns(2), paths, strict=True):
        with column:
            st.subheader(representation)
            st.caption(f"Seed: {seed.track_id}")
            if paths[representation] in (
                DEFAULT_NEIGHBOURS_PATH, DEFAULT_OPENL3_NEIGHBOURS_PATH
            ):
                st.caption("Synthetic sample neighbour list")
            if representation in failures:
                st.warning(
                    f"{representation} saved neighbours could not be loaded. "
                    "Check the configured CSV artifact."
                )
                continue
            side = results[representation]
            if not side:
                st.info(f"No saved {representation} neighbours for this seed.")
                continue
            if len(side) < RESULT_LIMIT:
                st.warning(f"Only {len(side)} of {RESULT_LIMIT} saved neighbours are available.")
            rows = comparison_playback_rows(seed, side, coordinates, configured_audio_root())
            for result, row in zip(side, rows[1:], strict=True):
                with st.container(border=True):
                    st.caption(f"RANK {result.rank} · {result.track_id}")
                    st.markdown(f"**{row.title}**")
                    st.caption(f"{row.artist} · {row.genre}")
                    st.caption(f"{result.metric_name.title()} {result.metric_value:.3f}")
                    if result.track_id in overlap.shared:
                        st.write("Shared by both representations")
                    elif all(results.values()):
                        st.write(f"Only in {representation} results")
                    else:
                        st.write("Overlap unknown: other list unavailable")
                    render_audio_control(row, namespace=f"{representation}-")
                    if st.button(
                        "Locate on map",
                        key=f"representations-{representation}-locate-{result.track_id}",
                        disabled=not result.on_map,
                        help="Highlight this track while keeping the same selected seed.",
                    ):
                        st.session_state[HIGHLIGHTED_NEIGHBOUR_KEY] = result.track_id
                        st.rerun()


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
        coordinates = load_coordinates(coordinates_path)
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
    projections = available_projections(coordinates, representation=active_representation)
    if not projections and coordinates["projection"].eq("Unspecified").all():
        projections = ["Unspecified"]
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
            f"{active_representation}."
        )

    projected_coordinates = (coordinates.loc[coordinates["representation"].eq(active_representation)].copy()
        if active_projection == "Unspecified" else coordinates_for_projection(
            coordinates, representation=active_representation, projection=active_projection))

    filtered_coordinates = filter_coordinates(
        projected_coordinates,
        representation=active_representation,
        genres=st.session_state[GENRE_FILTER_KEY],
        clusters=st.session_state[CLUSTER_FILTER_KEY],
    )
    representation_total = int(
        len(projected_coordinates)
    )

    selected_track_id, selection_cleared = reconcile_selected_track(
        st.session_state.get("selected_track_id"),
        filtered_coordinates["track_id"],
    )
    st.session_state["selected_track_id"] = selected_track_id
    if selection_cleared:
        st.info("The selected track was cleared because it is outside the active filters.")


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

    selected_track_id = st.session_state.get(SELECTED_TRACK_KEY)
    selection_event = st.plotly_chart(
        build_coordinate_map(
            filtered_coordinates,
            color_by=color_label.lower(),
            selected_track_id=selected_track_id,
            highlighted_track_id=st.session_state.get(HIGHLIGHTED_NEIGHBOUR_KEY),
            viewport_key=f"{active_representation}-{active_projection}",
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
    if (
        event_track_id is not None
        and event_track_id != selected_track_id
        and filtered_coordinates["track_id"].eq(event_track_id).any()
    ):
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

    details = track_details_for_id(filtered_coordinates, selected_track_id)
    if details is None:
        st.session_state[SELECTED_TRACK_KEY] = None
        st.warning("The selected track is no longer available in this map.")
        return

    render_track_details(details)

    mode = st.radio(
        "Neighbour view", ("Single representation", "Compare Conventional / OpenL3"),
        key="neighbour-view",
    )
    if mode == "Compare Conventional / OpenL3":
        render_representation_comparison(details, filtered_coordinates)
        return

    try:
        neighbours = load_neighbours(neighbours_path)
    except (NeighbourDataError, FileNotFoundError, OSError) as error:
        st.warning("Saved neighbours could not be loaded.", icon="⚠️")
        st.caption(str(error))
        render_comparison_playback(details, [], filtered_coordinates)
        return

    render_comparison_playback(
        details,
        neighbours_for_seed(
            neighbours,
            filtered_coordinates,
            seed_track_id=details.track_id,
            representation=details.representation,
        ),
        filtered_coordinates,
    )
    st.caption(
        "Projection changes only the saved map coordinates. Neighbours are retrieved "
        "from the original feature space, not from 2-D map distance."
    )


if __name__ == "__main__":
    main()

