"""
Cost Optimization page — financial analytics using existing cost_usd
and availability columns from the dataset.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title
from dashboard.components.charts import apply_dark_theme, QUALITATIVE


def render_cost(fdf: pd.DataFrame):
    """Render the Cost Optimization page."""
    page_title("Cost Optimization", "Financial analytics and cost efficiency insights")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    has_cost  = "cost_usd" in fdf.columns
    has_avail = "availability" in fdf.columns

    total_cost    = fdf["cost_usd"].sum() if has_cost else 0
    avg_cost      = fdf["cost_usd"].mean() if has_cost else 0
    total_demand  = fdf["demand_units"].sum() if "demand_units" in fdf.columns else 1
    avg_cost_unit = total_cost / total_demand if total_demand > 0 else 0

    # Capacity waste cost: cost of over-allocated capacity
    fdf2 = fdf.copy()
    fdf2["cap_waste"] = fdf2["capacity_allocated"] - fdf2["predicted_demand"]
    total_waste  = fdf2["cap_waste"].sum()
    waste_pct    = (total_waste / fdf2["capacity_allocated"].sum() * 100) if fdf2["capacity_allocated"].sum() > 0 else 0

    avg_avail      = fdf["availability"].mean() if has_avail else 0
    lowest_svc     = "N/A"
    lowest_svc_val = 0
    if has_avail:
        avail_svc = fdf.groupby("service_type")["availability"].mean()
        lowest_svc     = avail_svc.idxmin()
        lowest_svc_val = avail_svc.min()

    # ── KPI Row ─────────────────────────────────────────────────────
    row = [
        {"label": "Total Cost (USD)",     "value": f"${total_cost:,.2f}",
         "icon": "💲", "accent_color": "#F59E0B"},
        {"label": "Avg Cost / Unit",      "value": f"${avg_cost_unit:.3f}",
         "icon": "📊", "accent_color": "#3B82F6"},
        {"label": "Total Capacity Waste", "value": f"{total_waste:,.0f}",
         "delta": f"{waste_pct:.1f}% of capacity",
         "delta_type": "negative" if waste_pct > 20 else "neutral",
         "icon": "♻️", "accent_color": "#EF4444"},
        {"label": "Avg Availability",     "value": f"{avg_avail:.2f}%",
         "icon": "🟢", "accent_color": "#22C55E"},
        {"label": "Lowest Availability",  "value": str(lowest_svc),
         "delta": f"{lowest_svc_val:.2f}%" if lowest_svc != "N/A" else "",
         "delta_type": "negative",
         "icon": "⚠️", "accent_color": "#EF4444"},
        {"label": "Avg Daily Cost",       "value": f"${fdf.groupby('date')['cost_usd'].sum().mean():.2f}" if has_cost else "N/A",
         "icon": "📅", "accent_color": "#A78BFA"},
    ]
    render_kpi_row(row, columns=6)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Row 1 Charts ────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("Cost by Region", "🌍")
        if has_cost and "region" in fdf.columns:
            reg_cost = fdf.groupby("region")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
            fig_reg = px.bar(reg_cost, x="region", y="cost_usd",
                             color_discrete_sequence=[QUALITATIVE[0]])
            fig_reg = apply_dark_theme(fig_reg, height=320)
            fig_reg.update_layout(xaxis_title="Region", yaxis_title="Total Cost (USD)", showlegend=False)
            fig_reg.update_traces(marker_line_width=0, text=reg_cost["cost_usd"].map("${:,.0f}".format),
                                  textposition="outside", textfont_color="#94A3B8", textfont_size=10)
            st.plotly_chart(fig_reg, width='stretch')

    with col_right:
        section_header("Cost by Service Type", "⚙️")
        if has_cost and "service_type" in fdf.columns:
            svc_cost = fdf.groupby("service_type")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
            fig_svc = px.bar(svc_cost, x="service_type", y="cost_usd",
                             color="service_type", color_discrete_sequence=QUALITATIVE)
            fig_svc = apply_dark_theme(fig_svc, height=320)
            fig_svc.update_layout(xaxis_title="Service", yaxis_title="Total Cost (USD)", showlegend=False)
            fig_svc.update_traces(marker_line_width=0)
            st.plotly_chart(fig_svc, width='stretch')

    # ── Row 2 Charts ────────────────────────────────────────────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        section_header("Cost vs Capacity Provisioned", "📈")
        if has_cost and "capacity_allocated" in fdf.columns:
            sample = fdf.sample(min(2000, len(fdf)), random_state=42)
            fig_scatter = px.scatter(
                sample, x="capacity_allocated", y="cost_usd",
                color="service_type" if "service_type" in sample.columns else None,
                color_discrete_sequence=QUALITATIVE,
                opacity=0.6,
            )
            fig_scatter = apply_dark_theme(fig_scatter, height=320)
            fig_scatter.update_layout(xaxis_title="Capacity Allocated", yaxis_title="Cost (USD)")
            st.plotly_chart(fig_scatter, width='stretch')

    with col_right2:
        section_header("Availability Over Time", "📡")
        if has_avail and "date" in fdf.columns:
            avail_trend = fdf.groupby("date")["availability"].mean().reset_index().sort_values("date")
            fig_avail = go.Figure()
            fig_avail.add_trace(go.Scatter(
                x=avail_trend["date"], y=avail_trend["availability"],
                mode="lines",
                line=dict(color="#22C55E", width=2),
                fill="tozeroy",
                fillcolor="rgba(34,197,94,0.05)",
                hovertemplate="<b>%{x|%b %d, %Y}</b><br>Availability: %{y:.3f}%<extra></extra>",
            ))
            fig_avail = apply_dark_theme(fig_avail, height=320)
            fig_avail.update_layout(
                yaxis_title="Avg Availability (%)",
                yaxis=dict(range=[
                    max(98.0, avail_trend["availability"].min() - 0.2),
                    min(100.5, avail_trend["availability"].max() + 0.1),
                ]),
                showlegend=False,
            )
            st.plotly_chart(fig_avail, width='stretch')

    # ── Monthly Cost Trend ──────────────────────────────────────────
    if has_cost and "date" in fdf.columns:
        section_header("Monthly Cost Trend", "📅")
        monthly = fdf.copy()
        monthly["month"] = pd.to_datetime(monthly["date"]).dt.to_period("M").astype(str)
        monthly_cost = monthly.groupby(["month", "service_type"])["cost_usd"].sum().reset_index()
        monthly_cost = monthly_cost.sort_values("month")
        fig_trend = px.bar(monthly_cost, x="month", y="cost_usd", color="service_type",
                           color_discrete_sequence=QUALITATIVE)
        fig_trend = apply_dark_theme(fig_trend, height=300)
        fig_trend.update_layout(xaxis_title="Month", yaxis_title="Total Cost (USD)",
                                legend_title="Service", bargap=0.15)
        fig_trend.update_traces(marker_line_width=0)
        st.plotly_chart(fig_trend, width='stretch')
