"""
Overview page — executive command center with KPIs, insights,
executive summary, and two-column analytics area.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from dashboard.components.kpi_cards import (
    render_kpi_row, insight_panel, exec_summary, section_header, page_title
)
from dashboard.components.charts import (
    apply_dark_theme, donut_chart, QUALITATIVE, COLORS
)


def render_overview(fdf: pd.DataFrame, metrics: dict, risk_threshold: float):
    """Render the Overview executive command center page."""
    page_title("Overview", "Executive command center — capacity health at a glance")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    # ── KPI Row 1 ──────────────────────────────────────────────────
    total_forecast = fdf["predicted_demand"].sum()
    total_actual   = fdf["demand_units"].sum() if "demand_units" in fdf.columns else 0
    rmse   = metrics.get("rmse", 0)
    mae    = metrics.get("mae", 0)
    dir_acc = metrics.get("dir_acc", 0)
    mape   = metrics.get("mape", 0)

    # Forecast growth (H2 vs H1 of filtered data)
    forecast_growth = 0.0
    try:
        half = len(fdf) // 2
        h1 = fdf.iloc[:half]["predicted_demand"].sum()
        h2 = fdf.iloc[half:]["predicted_demand"].sum()
        if h1 > 0:
            forecast_growth = (h2 - h1) / h1 * 100
    except Exception:
        pass

    peak_date = "N/A"
    if not fdf["predicted_demand"].isna().all():
        idx = fdf["predicted_demand"].idxmax()
        if pd.notna(idx):
            peak_date = fdf.loc[idx, "date"].strftime("%b %d, %Y")

    growth_delta_type = "positive" if forecast_growth >= 0 else "negative"
    growth_sign = "▲" if forecast_growth >= 0 else "▼"

    row1 = [
        {"label": "Total Forecast Demand", "value": f"{total_forecast:,.0f}",
         "icon": "📈", "accent_color": "#3B82F6"},
        {"label": "Peak Forecast Date", "value": peak_date,
         "icon": "📅", "accent_color": "#0078D4"},
        {"label": "Forecast Growth", "value": f"{forecast_growth:+.1f}%",
         "delta": f"{growth_sign} H2 vs H1",
         "delta_type": growth_delta_type,
         "icon": "📊", "accent_color": "#22C55E" if forecast_growth >= 0 else "#EF4444"},
        {"label": "Model RMSE", "value": f"{rmse:,.1f}",
         "icon": "🎯", "accent_color": "#A78BFA"},
        {"label": "MAE", "value": f"{mae:,.1f}",
         "icon": "📐", "accent_color": "#2DD4BF"},
        {"label": "Directional Accuracy", "value": f"{dir_acc:.1f}%",
         "icon": "🧭", "accent_color": "#F59E0B"},
    ]
    render_kpi_row(row1, columns=6)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── KPI Row 2 ──────────────────────────────────────────────────
    avg_cost = fdf["cost_usd"].mean() if "cost_usd" in fdf.columns else 0
    avg_avail = fdf["availability"].mean() if "availability" in fdf.columns else 0

    fdf_copy = fdf.copy()
    fdf_copy["utilization"] = fdf_copy["predicted_demand"] / fdf_copy["capacity_allocated"]
    high_risk_count = int((fdf_copy["utilization"] > risk_threshold).sum())

    avg_gdp = fdf["gdp_growth"].mean() if "gdp_growth" in fdf.columns else 0
    avg_mdi = fdf["market_demand_index"].mean() if "market_demand_index" in fdf.columns else 0
    pricing_events = int(fdf["pricing_event"].sum()) if "pricing_event" in fdf.columns else 0

    row2 = [
        {"label": "Avg Cost (USD)", "value": f"${avg_cost:,.2f}",
         "icon": "💲", "accent_color": "#F59E0B"},
        {"label": "Avg Availability", "value": f"{avg_avail:.2f}%",
         "icon": "🟢", "accent_color": "#22C55E"},
        {"label": "High-Risk Records", "value": f"{high_risk_count:,}",
         "delta": f">{risk_threshold:.0%} util threshold",
         "delta_type": "negative" if high_risk_count > 0 else "positive",
         "icon": "🚨", "accent_color": "#EF4444"},
        {"label": "Avg GDP Growth", "value": f"{avg_gdp:.2f}%",
         "icon": "🌐", "accent_color": "#60A5FA"},
        {"label": "Market Demand Index", "value": f"{avg_mdi:.1f}",
         "icon": "📉", "accent_color": "#2DD4BF"},
        {"label": "Pricing Events", "value": f"{pricing_events:,}",
         "icon": "🏷️", "accent_color": "#A78BFA"},
    ]
    render_kpi_row(row2, columns=6)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Key Insight Panel ──────────────────────────────────────────
    insight_text = _generate_insight(fdf_copy, high_risk_count, risk_threshold)
    insight_panel(insight_text)

    # ── Alert ──────────────────────────────────────────────────────
    if high_risk_count > 0:
        st.markdown(
            f'<div class="alert-warning">⚠️ <strong>{high_risk_count:,} records</strong> currently '
            f'exceed the {risk_threshold:.0%} capacity utilization risk threshold.</div>',
            unsafe_allow_html=True,
        )

    # ── Charts ─────────────────────────────────────────────────────
    section_header("Analytics Snapshot", "📊")
    col_left, col_right = st.columns(2)

    with col_left:
        _render_service_donut(fdf)

    with col_right:
        _render_capacity_waste_trend(fdf)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Executive Summary ──────────────────────────────────────────
    bullets = _generate_exec_summary(fdf_copy, risk_threshold, forecast_growth)
    exec_summary(bullets)


def _generate_insight(fdf: pd.DataFrame, high_risk_count: int, risk_threshold: float) -> str:
    """Dynamically generate key insight text from actual data."""
    parts = []

    # Highest utilization region
    if "region" in fdf.columns:
        reg_util = fdf.groupby("region")["utilization"].mean().sort_values(ascending=False)
        if len(reg_util) > 0:
            top_reg = reg_util.index[0]
            top_val = reg_util.iloc[0]
            parts.append(
                f"<strong>{top_reg}</strong> currently has the highest average utilization "
                f"at <strong>{top_val:.1%}</strong>."
            )

    # Service with most headroom
    if "service_type" in fdf.columns:
        fdf2 = fdf.copy()
        fdf2["headroom"] = fdf2["capacity_allocated"] - fdf2["predicted_demand"]
        svc_headroom = fdf2.groupby("service_type")["headroom"].mean().sort_values(ascending=False)
        if len(svc_headroom) > 0:
            best_svc = svc_headroom.index[0]
            parts.append(
                f"<strong>{best_svc}</strong> has the strongest average capacity headroom."
            )

    # High-risk count
    if high_risk_count > 0:
        parts.append(
            f"<strong>{high_risk_count:,} records</strong> currently exceed the configured "
            f"{risk_threshold:.0%} utilization risk threshold."
        )
    else:
        parts.append("All capacity utilization metrics are within acceptable thresholds.")

    return " &nbsp;·&nbsp; ".join(parts)


def _generate_exec_summary(fdf: pd.DataFrame, risk_threshold: float,
                            forecast_growth: float) -> list[str]:
    """Generate executive summary bullets from actual data."""
    bullets = []

    # Utilization status
    avg_util = fdf["utilization"].mean() if "utilization" in fdf.columns else 0
    util_label = "Critical" if avg_util > 0.9 else ("High" if avg_util > 0.75 else ("Moderate" if avg_util > 0.5 else "Low"))
    bullets.append(f"Current average capacity utilization: <strong>{avg_util:.1%}</strong> — {util_label}")

    # Forecast trend
    trend = "increasing" if forecast_growth > 0 else ("declining" if forecast_growth < 0 else "stable")
    bullets.append(f"Forecast demand is <strong>{trend}</strong> ({forecast_growth:+.1f}% H2 vs H1)")

    # Highest risk region
    if "region" in fdf.columns:
        high_risk_mask = fdf["utilization"] > risk_threshold
        if high_risk_mask.any():
            risk_by_region = fdf[high_risk_mask].groupby("region").size().sort_values(ascending=False)
            top_risk_region = risk_by_region.index[0]
            bullets.append(
                f"Highest-risk region: <strong>{top_risk_region}</strong> "
                f"({risk_by_region.iloc[0]:,} records exceed threshold)"
            )
        else:
            bullets.append("No regions currently exceed the capacity risk threshold.")

    # Service cost
    if "cost_usd" in fdf.columns and "service_type" in fdf.columns:
        top_cost_svc = fdf.groupby("service_type")["cost_usd"].sum().idxmax()
        bullets.append(f"Highest cost service type: <strong>{top_cost_svc}</strong>")

    # Availability
    if "availability" in fdf.columns:
        min_avail_svc = fdf.groupby("service_type")["availability"].mean().idxmin()
        min_avail_val = fdf.groupby("service_type")["availability"].mean().min()
        bullets.append(
            f"Service requiring monitoring: <strong>{min_avail_svc}</strong> "
            f"(avg availability {min_avail_val:.2f}%)"
        )

    return bullets


def _render_service_donut(fdf: pd.DataFrame):
    """Donut chart: forecast distribution by service type."""
    if "service_type" not in fdf.columns:
        return
    svc_df = fdf.groupby("service_type")["predicted_demand"].sum().reset_index()
    fig = donut_chart(svc_df, "service_type", "predicted_demand",
                      title="Forecast Distribution by Service", height=360)
    st.plotly_chart(fig, width='stretch')


def _render_capacity_waste_trend(fdf: pd.DataFrame):
    """Line chart: monthly capacity waste trend."""
    if "date" not in fdf.columns:
        return

    monthly = fdf.copy()
    monthly["month"] = pd.to_datetime(monthly["date"]).dt.to_period("M").astype(str)
    monthly["capacity_waste"] = monthly["capacity_allocated"] - monthly["predicted_demand"]
    monthly_agg = monthly.groupby("month")["capacity_waste"].sum().reset_index()
    monthly_agg = monthly_agg.sort_values("month")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_agg["month"],
        y=monthly_agg["capacity_waste"],
        mode="lines+markers",
        name="Capacity Waste",
        line=dict(color="#F59E0B", width=2),
        fill="tozeroy",
        fillcolor="rgba(245,158,11,0.07)",
        hovertemplate="<b>%{x}</b><br>Waste: %{y:,.0f}<extra></extra>",
    ))
    fig = apply_dark_theme(fig, title="Monthly Capacity Waste Trend", height=360)
    fig.update_layout(yaxis_title="Capacity Waste (Units)", showlegend=False)
    st.plotly_chart(fig, width='stretch')
