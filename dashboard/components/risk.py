"""
Risk Center page — capacity risk analysis with sortable table,
risk distribution chart, and download functionality.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title
from dashboard.components.charts import apply_dark_theme, QUALITATIVE, RISK_COLORS


def _risk_level(util: float, threshold: float) -> str:
    if util > 1.00:   return "Critical"
    if util > threshold: return "High"
    if util > 0.60:   return "Moderate"
    return "Low"


def _risk_icon(level: str) -> str:
    return {"Critical": "🔴", "High": "🟠", "Moderate": "🔵", "Low": "🟢"}.get(level, "⚪")


def render_risk(fdf: pd.DataFrame, risk_threshold: float):
    """Render the Risk Center page."""
    page_title("Risk Center", "Capacity risk identification and analysis")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    risk_df = fdf.copy()
    risk_df["utilization"] = risk_df["predicted_demand"] / risk_df["capacity_allocated"]
    risk_df["risk_level"]  = risk_df["utilization"].apply(lambda u: _risk_level(u, risk_threshold))
    risk_df["headroom"]    = risk_df["capacity_allocated"] - risk_df["predicted_demand"]

    total_critical = int((risk_df["risk_level"] == "Critical").sum())
    total_high     = int((risk_df["risk_level"] == "High").sum())
    total_moderate = int((risk_df["risk_level"] == "Moderate").sum())
    total_low      = int((risk_df["risk_level"] == "Low").sum())
    total_high_risk = total_critical + total_high

    avg_util_hr = risk_df[risk_df["risk_level"].isin(["High", "Critical"])]["utilization"].mean()

    # ── KPI Row ─────────────────────────────────────────────────────
    row = [
        {"label": "Critical Records",  "value": f"{total_critical:,}",  "icon": "🔴",
         "delta_type": "negative" if total_critical > 0 else "positive",
         "accent_color": "#EF4444"},
        {"label": "High Risk Records", "value": f"{total_high:,}",      "icon": "🟠",
         "delta_type": "negative" if total_high > 0 else "positive",
         "accent_color": "#F59E0B"},
        {"label": "Moderate Risk",     "value": f"{total_moderate:,}",  "icon": "🔵",
         "accent_color": "#60A5FA"},
        {"label": "Low Risk",          "value": f"{total_low:,}",       "icon": "🟢",
         "accent_color": "#22C55E"},
        {"label": "Total High-Risk",   "value": f"{total_high_risk:,}", "icon": "⚠️",
         "accent_color": "#EF4444"},
        {"label": "Avg Util (High+)",  "value": f"{avg_util_hr:.1%}" if pd.notna(avg_util_hr) else "N/A",
         "icon": "📊", "accent_color": "#F59E0B"},
    ]
    render_kpi_row(row, columns=6)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("Risk Distribution", "📊")
        dist_df = risk_df["risk_level"].value_counts().reset_index()
        dist_df.columns = ["Risk Level", "Count"]
        ordered = ["Critical", "High", "Moderate", "Low"]
        dist_df["Risk Level"] = pd.Categorical(dist_df["Risk Level"], categories=ordered, ordered=True)
        dist_df = dist_df.sort_values("Risk Level")
        colors_seq = [RISK_COLORS.get(r, "#94A3B8") for r in dist_df["Risk Level"]]
        fig_dist = px.bar(dist_df, x="Risk Level", y="Count",
                          color="Risk Level",
                          color_discrete_map=RISK_COLORS)
        fig_dist = apply_dark_theme(fig_dist, height=320)
        fig_dist.update_layout(showlegend=False, xaxis_title="Risk Level", yaxis_title="Record Count")
        fig_dist.update_traces(marker_line_width=0)
        st.plotly_chart(fig_dist, width='stretch')

    with col_right:
        section_header("Risk by Region", "🌍")
        reg_risk = risk_df.groupby(["region", "risk_level"]).size().reset_index(name="count")
        fig_reg = px.bar(reg_risk, x="region", y="count", color="risk_level",
                         color_discrete_map=RISK_COLORS, barmode="stack")
        fig_reg = apply_dark_theme(fig_reg, height=320)
        fig_reg.update_layout(xaxis_title="Region", yaxis_title="Records",
                              legend_title="Risk Level")
        fig_reg.update_traces(marker_line_width=0)
        st.plotly_chart(fig_reg, width='stretch')

    # ── Filters for table ──────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    section_header("High-Risk Records", "🚨")

    tcol1, tcol2, tcol3 = st.columns([2, 2, 1])
    with tcol1:
        search_term = st.text_input("🔍 Search region or service", key="risk_search", placeholder="e.g. eastus, Compute")
    with tcol2:
        risk_filter = st.multiselect(
            "Filter by risk level", ["Critical", "High", "Moderate", "Low"],
            default=["Critical", "High"], key="risk_level_filter"
        )
    with tcol3:
        sort_col = st.selectbox("Sort by", ["utilization", "predicted_demand", "headroom"],
                                key="risk_sort")

    # Build display table
    display = risk_df[["date", "region", "service_type", "predicted_demand",
                        "capacity_allocated", "utilization", "headroom", "risk_level"]].copy()
    display = display[display["risk_level"].isin(risk_filter)] if risk_filter else display

    if search_term:
        mask = (
            display["region"].str.contains(search_term, case=False, na=False) |
            display["service_type"].str.contains(search_term, case=False, na=False)
        )
        display = display[mask]

    display = display.sort_values(sort_col, ascending=(sort_col == "headroom"))
    display["Risk"] = display["risk_level"].apply(lambda r: f"{_risk_icon(r)} {r}")
    display["Utilization %"] = display["utilization"].map("{:.1%}".format)
    display["Headroom"]      = display["headroom"].map("{:,.0f}".format)
    display["Forecast"]      = display["predicted_demand"].map("{:,.0f}".format)
    display["Capacity"]      = display["capacity_allocated"].map("{:,.0f}".format)
    display["Date"]          = pd.to_datetime(display["date"]).dt.strftime("%Y-%m-%d")

    st.markdown(f"<div style='font-size:12px;color:#94A3B8;margin-bottom:8px;'>{len(display):,} records matching filters</div>", unsafe_allow_html=True)

    st.dataframe(
        display[["Date", "region", "service_type", "Forecast", "Capacity",
                 "Utilization %", "Headroom", "Risk"]]
        .rename(columns={"region": "Region", "service_type": "Service"})
        .head(500),
        width='stretch',
        hide_index=True,
    )

    # ── Download ───────────────────────────────────────────────────
    csv_data = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Risk Report (CSV)",
        data=csv_data,
        file_name="risk_report.csv",
        mime="text/csv",
    )
