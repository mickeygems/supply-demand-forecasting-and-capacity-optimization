"""
Regional Analysis page — heatmap, stacked bars, and risk summary table.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import mean_squared_error

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title
from dashboard.components.charts import apply_dark_theme, heatmap_chart, QUALITATIVE


def render_regional(fdf: pd.DataFrame, risk_threshold: float):
    """Render the Regional Analysis page."""
    page_title("Regional Analysis", "Capacity utilization and demand breakdown across regions")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    fdf2 = fdf.copy()
    fdf2["utilization"] = fdf2["predicted_demand"] / fdf2["capacity_allocated"]
    fdf2["headroom"]    = fdf2["capacity_allocated"] - fdf2["predicted_demand"]

    # ── Regional Aggregation ────────────────────────────────────────
    reg_df = fdf2.groupby("region").agg(
        predicted_demand=("predicted_demand", "sum"),
        demand_units=("demand_units", "sum"),
        capacity_allocated=("capacity_allocated", "sum"),
        headroom=("headroom", "sum"),
        utilization=("utilization", "mean"),
    ).reset_index()

    # ── Regional RMSE ───────────────────────────────────────────────
    valid_df = fdf2.dropna(subset=["demand_units", "predicted_demand"])
    reg_rmse = {}
    reg_growth = {}
    for r in reg_df["region"]:
        r_df = valid_df[valid_df["region"] == r]
        if len(r_df) > 0:
            reg_rmse[r] = np.sqrt(mean_squared_error(r_df["demand_units"], r_df["predicted_demand"]))
        else:
            reg_rmse[r] = 0
        sub = fdf2[fdf2["region"] == r]
        half = len(sub) // 2
        h1 = sub.iloc[:half]["predicted_demand"].sum()
        h2 = sub.iloc[half:]["predicted_demand"].sum()
        reg_growth[r] = ((h2 - h1) / h1 * 100) if h1 > 0 else 0

    highest_growth_reg = max(reg_growth, key=reg_growth.get) if reg_growth else "N/A"
    highest_growth_val = reg_growth.get(highest_growth_reg, 0)
    lowest_util_row    = reg_df.loc[reg_df["utilization"].idxmin()] if len(reg_df) > 0 else None
    avg_rmse           = np.mean(list(reg_rmse.values())) if reg_rmse else 0

    # ── KPI Row ─────────────────────────────────────────────────────
    row = [
        {"label": "Highest Growth Region",   "value": str(highest_growth_reg).title(),
         "delta": f"▲ {highest_growth_val:+.1f}%", "delta_type": "positive",
         "icon": "🚀", "accent_color": "#22C55E"},
        {"label": "Lowest Utilization Region","value": str(lowest_util_row["region"]).title() if lowest_util_row is not None else "N/A",
         "delta": f"{lowest_util_row['utilization']:.1%}" if lowest_util_row is not None else "N/A",
         "delta_type": "positive",
         "icon": "✅", "accent_color": "#3B82F6"},
        {"label": "Avg Regional RMSE",        "value": f"{avg_rmse:,.1f}",
         "icon": "🎯", "accent_color": "#A78BFA"},
        {"label": "Total Regions",            "value": str(len(reg_df)),
         "icon": "🌍", "accent_color": "#2DD4BF"},
    ]
    render_kpi_row(row, columns=4)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Charts Row ──────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("Forecast by Region & Service", "📊")
        grp = fdf2.groupby(["region", "service_type"])["predicted_demand"].sum().reset_index()
        fig_bar = px.bar(grp, x="region", y="predicted_demand", color="service_type",
                         color_discrete_sequence=QUALITATIVE, text_auto=".2s")
        fig_bar = apply_dark_theme(fig_bar, height=380)
        fig_bar.update_layout(yaxis_title="Predicted Demand", xaxis_title="Region",
                              legend_title="Service", bargap=0.2)
        fig_bar.update_traces(marker_line_width=0)
        st.plotly_chart(fig_bar, width='stretch')

    with col_right:
        section_header("Max Utilization Heatmap", "🔥")
        heat_df = fdf2.groupby(["region", "service_type"])["utilization"].max().reset_index()
        try:
            pivot = heat_df.pivot(index="service_type", columns="region", values="utilization")
            fig_heat = heatmap_chart(pivot, height=380, fmt=".1%")
            fig_heat.update_layout(
                coloraxis_colorbar=dict(
                    title="Utilization",
                    tickformat=".0%",
                    len=0.7,
                )
            )
            st.plotly_chart(fig_heat, width='stretch')
        except Exception:
            st.info("Not enough data to build heatmap.")

    # ── Risk Summary Table ─────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_header("Regional Risk Summary", "🚨")

    reg_df["rmse"]   = reg_df["region"].map(reg_rmse)
    reg_df["growth"] = reg_df["region"].map(reg_growth)

    def _risk_badge(util):
        if util > 0.90:   return "🔴 Critical"
        if util > risk_threshold: return "🟠 High"
        if util > 0.60:   return "🔵 Moderate"
        return "🟢 Low"

    display_df = reg_df.copy()
    display_df["Risk"] = display_df["utilization"].apply(_risk_badge)
    display_df["Utilization"] = display_df["utilization"].map("{:.1%}".format)
    display_df["Headroom"]    = display_df["headroom"].map("{:,.0f}".format)
    display_df["Forecast"]    = display_df["predicted_demand"].map("{:,.0f}".format)
    display_df["Capacity"]    = display_df["capacity_allocated"].map("{:,.0f}".format)
    display_df["RMSE"]        = display_df["rmse"].map("{:.1f}".format)
    display_df["Growth %"]    = display_df["growth"].map("{:+.1f}%".format)

    st.dataframe(
        display_df[["region", "Forecast", "Capacity", "Utilization", "Headroom", "Growth %", "RMSE", "Risk"]]
        .rename(columns={"region": "Region"}),
        width='stretch',
        hide_index=True,
    )
