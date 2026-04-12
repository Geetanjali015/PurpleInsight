"""
chart_renderer.py
─────────────────
Renders charts + data table side-by-side, exactly matching the screenshots:
  - Left: Plotly chart (horizontal bar / dual-line / annotated line)
  - Right: data table with "N rows · Xms" header + highlighted anomaly cells

Chart types by query type:
  breakdown  → horizontal bar (NatWest purple gradient)
  comparison → dual-line with annotation callout
  change     → single line with drop-window annotation + red markers
  summary    → dual-axis line (active customers + churn %)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Brand colours ─────────────────────────────────────────────
PURPLE_DARK   = "#4a0b65"
PURPLE_MID    = "#804b99"
PURPLE_LIGHT  = "#a682b1"
PURPLE_PALE   = "#d1bbe3"
GREEN_LINE    = "#3a9a3e"
AMBER         = "#f4a100"
RED_DOT       = "#c0392b"
GREY_BG       = "#faf4fd"


def _base_fig() -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=30, b=10),
        height=240,
        font=dict(family="sans-serif", size=11, color="#444"),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.12,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", zeroline=False, showline=False)
    return fig


def _render_breakdown_chart(chart_data: dict) -> None:
    """Horizontal bar chart — breakdown query type."""
    rows = chart_data.get("data", [])
    x_col = chart_data.get("x_col", "")
    y_col = chart_data.get("y_col", "")
    title = chart_data.get("title", "")

    if not rows:
        return

    df = pd.DataFrame(rows)
    labels  = df[x_col].tolist()
    values  = df[y_col].tolist()
    max_val = max(values) if values else 1

    # Colour gradient: darkest = highest
    colours = []
    for v in values:
        ratio = v / max_val
        if ratio > 0.8:
            colours.append(PURPLE_DARK)
        elif ratio > 0.6:
            colours.append(PURPLE_MID)
        elif ratio > 0.4:
            colours.append(PURPLE_LIGHT)
        else:
            colours.append(PURPLE_PALE)

    # Build text labels like "Mortgage £48.7M"
    text_labels = [
        f"{lbl} {val:,.1f}M" if isinstance(val, float) else f"{lbl} {val}"
        for lbl, val in zip(labels, values)
    ]

    fig = _base_fig()
    fig.add_trace(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colours,
        text=text_labels,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=11),
        hovertemplate="%{y}: %{x}<extra></extra>",
        showlegend=False,
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=11, color="#888"), x=0),
        yaxis=dict(autorange="reversed", showticklabels=False),
        xaxis=dict(showticklabels=False, showgrid=False),
        height=220,
        margin=dict(l=8, r=8, t=30, b=8),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_comparison_chart(chart_data: dict) -> None:
    """Dual-line chart with annotation — comparison query type."""
    rows   = chart_data.get("data", [])
    title  = chart_data.get("title", "")
    x_col  = chart_data.get("x_col", "month")
    y1_col = chart_data.get("y1_col", "north")
    y2_col = chart_data.get("y2_col", "south")
    annotation = chart_data.get("annotation", {})

    if not rows:
        return

    df = pd.DataFrame(rows)
    fig = _base_fig()

    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y1_col],
        mode="lines+markers",
        name="North",
        line=dict(color=PURPLE_DARK, width=2.5),
        marker=dict(size=7, color=PURPLE_DARK),
    ))
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y2_col],
        mode="lines+markers",
        name="South",
        line=dict(color=PURPLE_LIGHT, width=2, dash="dot"),
        marker=dict(size=7, color=PURPLE_LIGHT),
    ))

    # Drop annotation callout
    if annotation:
        fig.add_annotation(
            x=annotation.get("x", ""),
            y=annotation.get("y", 0),
            text=annotation.get("text", ""),
            showarrow=True,
            arrowhead=2,
            arrowcolor=AMBER,
            bgcolor=AMBER,
            font=dict(color="white", size=9),
            bordercolor=AMBER,
            ax=40, ay=-30,
        )
        # Red dots on the drop period
        for drop_x, drop_y in zip(
            annotation.get("drop_xs", []),
            annotation.get("drop_ys", [])
        ):
            fig.add_trace(go.Scatter(
                x=[drop_x], y=[drop_y],
                mode="markers",
                marker=dict(color=RED_DOT, size=9, symbol="circle"),
                showlegend=False,
                hoverinfo="skip",
            ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=11, color="#888"), x=0),
        height=240,
        margin=dict(l=8, r=8, t=40, b=8),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_change_chart(chart_data: dict) -> None:
    """Single line with drop window annotation — change analysis."""
    rows       = chart_data.get("data", [])
    title      = chart_data.get("title", "")
    x_col      = chart_data.get("x_col", "month")
    y_col      = chart_data.get("y_col", "revenue")
    annotation = chart_data.get("annotation", {})

    if not rows:
        return

    df = pd.DataFrame(rows)
    fig = _base_fig()

    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode="lines+markers",
        name="Revenue",
        line=dict(color=PURPLE_DARK, width=2.5),
        marker=dict(size=7, color=PURPLE_DARK),
        showlegend=False,
    ))

    # Drop-window shaded region + label
    if annotation:
        fig.add_vrect(
            x0=annotation.get("x0", ""),
            x1=annotation.get("x1", ""),
            fillcolor=RED_DOT,
            opacity=0.08,
            layer="below",
            line_width=0,
        )
        fig.add_annotation(
            x=annotation.get("label_x", ""),
            y=annotation.get("label_y", 0),
            text=annotation.get("text", ""),
            showarrow=False,
            bgcolor=RED_DOT,
            font=dict(color="white", size=9),
            bordercolor=RED_DOT,
        )
        # Red markers on drop months
        for drop_x, drop_y in zip(
            annotation.get("drop_xs", []),
            annotation.get("drop_ys", [])
        ):
            fig.add_trace(go.Scatter(
                x=[drop_x], y=[drop_y],
                mode="markers",
                marker=dict(color=RED_DOT, size=9),
                showlegend=False,
                hoverinfo="skip",
            ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=11, color="#888"), x=0),
        height=240,
        margin=dict(l=8, r=8, t=30, b=8),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_summary_chart(chart_data: dict) -> None:
    """Dual-line: active customers + churn % — summary query type."""
    rows   = chart_data.get("data", [])
    title  = chart_data.get("title", "")
    x_col  = chart_data.get("x_col", "month")
    y1_col = chart_data.get("y1_col", "active")
    y2_col = chart_data.get("y2_col", "churn_pct")
    anomaly_xs = chart_data.get("anomaly_xs", [])

    if not rows:
        return

    df = pd.DataFrame(rows)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y1_col],
        name="Active",
        mode="lines+markers",
        line=dict(color=PURPLE_DARK, width=2.5),
        marker=dict(size=7),
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y2_col],
        name="Churn %",
        mode="lines+markers",
        line=dict(color=GREEN_LINE, width=2, dash="dot"),
        marker=dict(size=7),
    ), secondary_y=True)

    # Red anomaly dots on churn spikes
    for ax in anomaly_xs:
        row = df[df[x_col] == ax]
        if not row.empty:
            fig.add_trace(go.Scatter(
                x=[ax], y=[row[y2_col].values[0]],
                mode="markers",
                marker=dict(color=RED_DOT, size=10),
                showlegend=False,
                hoverinfo="skip",
            ), secondary_y=True)

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=240,
        margin=dict(l=8, r=8, t=40, b=8),
        font=dict(family="sans-serif", size=11),
        title=dict(text=title, font=dict(size=11, color="#888"), x=0),
        legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="left", x=0, font=dict(size=10)),
        showlegend=True,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", showline=False, secondary_y=False)
    fig.update_yaxes(showgrid=False, showline=False, secondary_y=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_data_table(table_data: dict) -> None:
    """
    Right-side data table with:
    - "N rows · Xms" header
    - column headers
    - anomaly cells highlighted orange/bold
    """
    rows        = table_data.get("rows", [])
    columns     = table_data.get("columns", [])
    n_rows      = table_data.get("n_rows", len(rows))
    query_ms    = table_data.get("query_ms", 0)
    anomaly_col = table_data.get("anomaly_col", "")
    anomaly_val = table_data.get("anomaly_val", None)

    if not rows or not columns:
        return

    # Header: "N rows · Xms"
    st.markdown(
        f"<p style='font-size:11px; color:#888; margin:0 0 6px;'>"
        f"{n_rows} rows · {query_ms}ms</p>",
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(rows, columns=columns)

    # Apply highlighting to anomaly cells
    def highlight_anomaly(val):
        if anomaly_val and str(val) == str(anomaly_val):
            return "color:#e67e00; font-weight:700;"
        return ""

    def style_row(row):
        styles = [""] * len(row)
        if anomaly_col and anomaly_col in row.index:
            cell_val = str(row[anomaly_col])
            if anomaly_val and cell_val == str(anomaly_val):
                idx = list(row.index).index(anomaly_col)
                styles[idx] = "color:#e67e00; font-weight:700;"
        return styles

    styled = df.style.apply(style_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=min(32 + len(rows) * 35, 260),
    )


def render_chart(chart_data: dict) -> None:
    """
    Main entry point. Renders chart (left) + table (right) in two columns.
    chart_data must have a 'query_type' key to select the correct renderer.
    """
    if not chart_data:
        return

    query_type = chart_data.get("query_type", "breakdown")
    table_data = chart_data.get("table", {})

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        if query_type == "breakdown":
            _render_breakdown_chart(chart_data)
        elif query_type == "comparison":
            _render_comparison_chart(chart_data)
        elif query_type == "change":
            _render_change_chart(chart_data)
        elif query_type == "summary":
            _render_summary_chart(chart_data)

    with col_table:
        _render_data_table(table_data)