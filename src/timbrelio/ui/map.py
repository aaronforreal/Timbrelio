"""Plotly map construction for saved track coordinates."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from timbrelio.ui.data import NOISE_LABEL, UNASSIGNED_LABEL
from timbrelio.ui.theme import COLORS

SUPPORTED_COLOR_FIELDS = ("genre", "cluster")


def category_color_map(labels: Iterable[object]) -> dict[str, str]:
    """Return stable colours based on label values rather than row order."""

    normalized_labels = sorted({str(label) for label in labels})
    colors: dict[str, str] = {}
    for label in normalized_labels:
        if label == UNASSIGNED_LABEL:
            colors[label] = COLORS["mocha_cream"]
        elif label == NOISE_LABEL:
            colors[label] = COLORS["muted_ink"]
        else:
            digest = hashlib.sha256(label.encode("utf-8")).digest()
            hue = int.from_bytes(digest[:4], "big") % 360
            colors[label] = f"hsl({hue}, 42%, 38%)"
    return colors


def build_coordinate_map(
    coordinates: pd.DataFrame,
    color_by: str | None = None,
    selected_track_id: str | None = None,
    highlighted_track_id: str | None = None,
) -> go.Figure:
    """Build an interactive coordinate map with safe, track-aligned hover data."""

    if color_by not in (*SUPPORTED_COLOR_FIELDS, None):
        supported = ", ".join(SUPPORTED_COLOR_FIELDS)
        raise ValueError(f"color_by must be one of: {supported}")

    scatter_options: dict[str, object] = {}
    if color_by is not None:
        labels = coordinates[color_by].astype(str)
        scatter_options.update(
            color=color_by,
            color_discrete_map=category_color_map(labels),
            category_orders={color_by: sorted(labels.unique())},
        )

    figure = px.scatter(
        coordinates,
        x="x",
        y="y",
        custom_data=["track_id", "title", "genre", "cluster"],
        render_mode="webgl",
        **scatter_options,
    )
    figure.update_traces(
        marker={
            "size": 9,
            "opacity": 0.82,
            "line": {"color": COLORS["deep_burgundy"], "width": 0.6},
        },
        hovertemplate=(
            "<b>%{customdata[1]}</b><br>"
            "Track %{customdata[0]}<br>"
            "Genre: %{customdata[2]}<br>"
            "Cluster: %{customdata[3]}"
            "<extra></extra>"
        ),
        selected={
            "marker": {
                "size": 13,
                "opacity": 1,
            }
        },
        unselected={"marker": {"opacity": 0.35}},
    )
    if color_by is None:
        figure.update_traces(marker={"color": COLORS["mocha_cream"]})

    if selected_track_id is not None:
        for trace in figure.data:
            trace.selectedpoints = [
                index
                for index, custom_data in enumerate(trace.customdata)
                if str(custom_data[0]) == selected_track_id
            ]

    if highlighted_track_id is not None:
        highlighted = coordinates.loc[
            coordinates["track_id"].astype(str).eq(highlighted_track_id)
        ]
        if not highlighted.empty:
            point = highlighted.iloc[0]
            figure.add_trace(
                go.Scattergl(
                    x=[point["x"]],
                    y=[point["y"]],
                    mode="markers",
                    name="Located neighbour",
                    text=[highlighted_track_id],
                    customdata=[[""]],
                    hovertemplate="Located neighbour · %{text}<extra></extra>",
                    marker={
                        "color": COLORS["porcelain"],
                        "line": {"color": COLORS["deep_burgundy"], "width": 3},
                        "size": 18,
                        "symbol": "diamond-open",
                    },
                    showlegend=False,
                )
            )

    figure.update_layout(
        height=610,
        margin={"l": 24, "r": 24, "t": 24, "b": 24},
        paper_bgcolor=COLORS["cosmic_latte"],
        plot_bgcolor=COLORS["porcelain"],
        font={
            "family": "Inter, ui-sans-serif, system-ui, sans-serif",
            "color": COLORS["ink"],
        },
        hoverlabel={
            "bgcolor": COLORS["porcelain"],
            "bordercolor": COLORS["deep_burgundy"],
            "font": {"color": COLORS["ink"]},
        },
        dragmode="pan",
        clickmode="event+select",
        showlegend=color_by is not None,
        legend={
            "title": {"text": color_by.title() if color_by else ""},
            "bgcolor": "rgba(255, 249, 239, 0.92)",
            "bordercolor": "rgba(45, 35, 33, 0.16)",
            "borderwidth": 1,
        },
        uirevision=f"coordinate-map-{color_by or 'neutral'}",
    )
    figure.update_xaxes(
        title=None,
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        fixedrange=False,
    )
    figure.update_yaxes(
        title=None,
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        fixedrange=False,
        scaleanchor="x",
        scaleratio=1,
    )
    return figure

