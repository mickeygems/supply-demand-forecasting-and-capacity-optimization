"""
Shared Plotly chart styling utilities.
Applies the enterprise dark theme consistently across all charts.
"""
import plotly.graph_objects as go
import plotly.express as px

# ── Palette ────────────────────────────────────────────────────────────────────
COLORS = {
    "blue_primary": "#3B82F6",
    "blue_azure":   "#0078D4",
    "blue_light":   "#60A5FA",
    "success":      "#22C55E",
    "warning":      "#F59E0B",
    "danger":       "#EF4444",
    "moderate":     "#60A5FA",
    "purple":       "#A78BFA",
    "teal":         "#2DD4BF",
    "rose":         "#FB7185",
    "amber":        "#FBBF24",
    "text":         "#F8FAFC",
    "text_muted":   "#94A3B8",
    "card":         "#0F1F35",
    "bg":           "#07111F",
    "border":       "rgba(255,255,255,0.08)",
}

# Ordered qualitative palette for multi-series charts
QUALITATIVE = [
    "#3B82F6", "#22C55E", "#F59E0B", "#A78BFA",
    "#2DD4BF", "#FB7185", "#FBBF24", "#60A5FA",
    "#34D399", "#F97316",
]

RISK_COLORS = {
    "Low":      "#22C55E",
    "Moderate": "#60A5FA",
    "High":     "#F59E0B",
    "Critical": "#EF4444",
}


def apply_dark_theme(fig: go.Figure, title: str = None, height: int = 380) -> go.Figure:
    """Apply the enterprise dark theme to any Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(15,31,53,0.0)",
        paper_bgcolor="rgba(15,31,53,0.0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=COLORS["text_muted"]),
        title=dict(
            text=f"<b>{title}</b>" if title else None,
            font=dict(size=14, color=COLORS["text"], family="Inter, system-ui, sans-serif"),
            x=0.0,
            xanchor="left",
            pad=dict(l=4),
        ) if title else None,
        legend=dict(
            bgcolor="rgba(15,31,53,0.6)",
            bordercolor=COLORS["border"],
            borderwidth=1,
            font=dict(size=11, color=COLORS["text_muted"]),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            linecolor="rgba(255,255,255,0.08)",
            tickfont=dict(size=11, color=COLORS["text_muted"]),
            title_font=dict(size=12, color=COLORS["text_muted"]),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            linecolor="rgba(255,255,255,0.08)",
            tickfont=dict(size=11, color=COLORS["text_muted"]),
            title_font=dict(size=12, color=COLORS["text_muted"]),
            zeroline=False,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(11,23,40,0.95)",
            bordercolor=COLORS["border"],
            font=dict(size=12, color=COLORS["text"], family="Inter, system-ui, sans-serif"),
        ),
        margin=dict(l=16, r=16, t=48 if title else 16, b=16),
        height=height,
    )
    return fig


def line_chart(df, x, y_cols, names=None, colors=None, title=None, height=380, y_label="Value"):
    """Polished multi-line chart."""
    fig = go.Figure()
    palette = colors or QUALITATIVE
    for i, col in enumerate(y_cols):
        display_name = (names[i] if names and i < len(names) else col)
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            name=display_name,
            mode="lines",
            line=dict(color=palette[i % len(palette)], width=2),
            fill="tozeroy" if len(y_cols) == 1 else None,
            fillcolor=f"rgba({_hex_to_rgb(palette[i % len(palette)])},0.05)" if len(y_cols) == 1 else None,
        ))
    fig = apply_dark_theme(fig, title=title, height=height)
    fig.update_layout(yaxis_title=y_label)
    return fig


def bar_chart(df, x, y, color=None, title=None, height=380, color_seq=None, orientation="v"):
    """Polished bar chart."""
    palette = color_seq or QUALITATIVE
    if color:
        fig = px.bar(df, x=x, y=y, color=color,
                     color_discrete_sequence=palette,
                     orientation=orientation)
    else:
        fig = px.bar(df, x=x, y=y,
                     color_discrete_sequence=palette,
                     orientation=orientation)
    fig = apply_dark_theme(fig, title=title, height=height)
    fig.update_traces(marker_line_width=0)
    return fig


def donut_chart(df, names_col, values_col, title=None, height=350):
    """Polished donut chart."""
    fig = px.pie(df, names=names_col, values=values_col, hole=0.55,
                 color_discrete_sequence=QUALITATIVE)
    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
        marker=dict(line=dict(color="rgba(7,17,31,0.8)", width=2)),
    )
    fig = apply_dark_theme(fig, title=title, height=height)
    fig.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.05))
    return fig


def heatmap_chart(pivot_df, title=None, height=380, fmt=".1f"):
    """Polished heatmap."""
    fig = px.imshow(
        pivot_df,
        text_auto=fmt,
        aspect="auto",
        color_continuous_scale=[
            [0.0, "#22C55E"], [0.5, "#F59E0B"], [0.75, "#EF4444"], [1.0, "#7F1D1D"]
        ],
        zmin=0, zmax=1,
    )
    fig.update_traces(
        hovertemplate="Service: %{y}<br>Region: %{x}<br>Utilization: %{z:.1%}<extra></extra>"
    )
    fig = apply_dark_theme(fig, title=title, height=height)
    fig.update_layout(coloraxis_showscale=True)
    return fig


def scatter_chart(df, x, y, color=None, title=None, height=380, color_map=None):
    """Polished scatter chart."""
    if color and color_map:
        fig = px.scatter(df, x=x, y=y, color=color, color_discrete_map=color_map)
    elif color:
        fig = px.scatter(df, x=x, y=y, color=color, color_discrete_sequence=QUALITATIVE)
    else:
        fig = px.scatter(df, x=x, y=y, color_discrete_sequence=QUALITATIVE)
    fig = apply_dark_theme(fig, title=title, height=height)
    return fig


def _hex_to_rgb(hex_str: str) -> str:
    """Convert #RRGGBB to 'R,G,B' string."""
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "59,130,246"
