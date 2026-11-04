"""Plotly map construction for saved track coordinates."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from timbrelio.ui.theme import COLORS


def build_coordinate_map(coordinates: pd.DataFrame) -> go.Figure:
    """Build the neutral A1 map without deriving or changing coordinates."""

    figure = px.scatter(
        coordinates,
        x="x",
        y="y",
        custom_data=["track_id"],
        render_mode="webgl",
    )
    figure.update_traces(
        marker={
            "color": COLORS["mocha_cream"],
            "size": 9,
            "opacity": 0.82,
            "line": {"color": COLORS["deep_burgundy"], "width": 0.6},
        },
        hovertemplate="<b>Track %{customdata[0]}</b><extra></extra>",
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
        showlegend=False,
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

