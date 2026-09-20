"""
What-If Analysis page — presentation-layer scenario simulation.
No model retraining. Uses existing capacity_allocated and predicted_demand
columns to compute scenario outcomes via a capacity adjustment slider.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title
from dashboard.components.charts import apply_dark_theme, QUALITATIVE


def render_whatif(fdf: pd.DataFrame, risk_threshold: float):
    """Render the What-If Analysis page."""
    page_title("What-If Analysis", "Capacity scenario simulation — presentation-layer only, no model retrain")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    # ── Controls ────────────────────────────────────────────────────
    st.markdown("""
<div style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.15);
     border-radius:12px;padding:16px 20px;margin-bottom:16px;">
  <div style="font-size:12px;font-weight:600;letter-spacing:0.08em;color:#94A3B8;
       text-transform:uppercase;margin-bottom:8px;">⚙️ Scenario Configuration</div>
  <div style="font-size:13px;color:#F8FAFC;">
    Adjust the capacity provisioning level relative to current allocations.
    The forecast demand from the XGBoost model remains fixed — only capacity changes.
  </div>
</div>""", unsafe_allow_html=True)

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    with col_ctrl1:
        capacity_adj = st.slider(
            "Capacity Adjustment",
            min_value=-20,
            max_value=50,
            value=0,
            step=5,
            format="%d%%",
            help="Adjust provisioned capacity relative to current. Forecast demand stays fixed.",
            key="whatif_slider",
        )
    with col_ctrl2:
        region_scope = st.selectbox(
            "Apply to",
            ["All Regions"] + sorted(fdf["region"].unique().tolist()),
            key="whatif_region",
        )
    with col_ctrl3:
        service_scope = st.selectbox(
            "Service",
            ["All Services"] + sorted(fdf["service_type"].unique().tolist()),
            key="whatif_service",
        )

    # ── Scenario Computation ────────────────────────────────────────
    adj_factor = 1 + capacity_adj / 100.0
    scen_df = fdf.copy()

    # Scope the capacity adjustment
    mask = pd.Series([True] * len(scen_df), index=scen_df.index)
    if region_scope != "All Regions":
        mask &= scen_df["region"] == region_scope
    if service_scope != "All Services":
        mask &= scen_df["service_type"] == service_scope

    scen_df["scenario_capacity"] = scen_df["capacity_allocated"]
    scen_df.loc[mask, "scenario_capacity"] = scen_df.loc[mask, "capacity_allocated"] * adj_factor

    scen_df["current_utilization"]  = scen_df["predicted_demand"] / scen_df["capacity_allocated"]
    scen_df["scenario_utilization"] = scen_df["predicted_demand"] / scen_df["scenario_capacity"]
    scen_df["capacity_gap"]         = scen_df["scenario_capacity"] - scen_df["predicted_demand"]

    # Risk levels
    def _risk(u):
        if u > 1.00:          return "Critical"
        if u > risk_threshold: return "High"
        if u > 0.60:           return "Moderate"
        return "Low"

    scen_df["current_risk"]  = scen_df["current_utilization"].apply(_risk)
    scen_df["scenario_risk"] = scen_df["scenario_utilization"].apply(_risk)

    # Cost impact (estimate using cost_usd proportional change)
    cost_impact = 0.0
    if "cost_usd" in scen_df.columns:
        # Approximate: cost scales proportionally with capacity for over-allocated regions
        current_total_cap  = scen_df.loc[mask, "capacity_allocated"].sum()
        scenario_total_cap = scen_df.loc[mask, "scenario_capacity"].sum()
        current_cost  = scen_df.loc[mask, "cost_usd"].sum()
        if current_total_cap > 0:
            cost_impact = current_cost * (scenario_total_cap / current_total_cap) - current_cost

    # ── Scenario KPIs ───────────────────────────────────────────────
    current_util_mean  = scen_df["current_utilization"].mean()
    scenario_util_mean = scen_df["scenario_utilization"].mean()
    util_change        = scenario_util_mean - current_util_mean

    current_cap_total  = scen_df["capacity_allocated"].sum()
    scenario_cap_total = scen_df["scenario_capacity"].sum()
    gap_total          = scen_df["capacity_gap"].sum()

    current_hr_count  = int((scen_df["current_risk"].isin(["High", "Critical"])).sum())
    scenario_hr_count = int((scen_df["scenario_risk"].isin(["High", "Critical"])).sum())

    adj_sign = "+" if capacity_adj >= 0 else ""
    delta_sign = "▲" if util_change > 0 else "▼"
    delta_type = "negative" if util_change > 0 else "positive"

    row = [
        {"label": "Current Avg Utilization",  "value": f"{current_util_mean:.1%}",
         "icon": "📊", "accent_color": "#94A3B8"},
        {"label": "Scenario Avg Utilization", "value": f"{scenario_util_mean:.1%}",
         "delta": f"{delta_sign} {abs(util_change):.1%} change",
         "delta_type": delta_type,
         "icon": "🔮", "accent_color": "#3B82F6"},
        {"label": "Current Capacity",         "value": f"{current_cap_total:,.0f}",
         "icon": "🏗️", "accent_color": "#94A3B8"},
        {"label": f"Scenario Capacity ({adj_sign}{capacity_adj}%)",
         "value": f"{scenario_cap_total:,.0f}",
         "delta": f"{adj_sign}{(scenario_cap_total - current_cap_total):,.0f} units",
         "delta_type": "positive" if capacity_adj >= 0 else "negative",
         "icon": "⚙️", "accent_color": "#22C55E" if capacity_adj >= 0 else "#EF4444"},
        {"label": "Capacity Gap",             "value": f"{gap_total:,.0f}",
         "icon": "↔️", "accent_color": "#F59E0B"},
        {"label": "Est. Cost Impact",         "value": f"${cost_impact:+,.2f}",
         "delta_type": "negative" if cost_impact > 0 else "positive",
         "icon": "💲", "accent_color": "#A78BFA"},
    ]
    render_kpi_row(row, columns=6)

    # Risk change indicator
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    risk_delta = scenario_hr_count - current_hr_count
    risk_color = "#EF4444" if risk_delta > 0 else "#22C55E"
    risk_arrow = "▲" if risk_delta > 0 else ("▼" if risk_delta < 0 else "→")
    st.markdown(f"""
<div style="background:rgba(15,31,53,0.9);border:1px solid rgba(255,255,255,0.08);
     border-radius:10px;padding:14px 18px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
  <span style="font-size:12px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;">Risk Status Change</span>
  <span style="font-size:14px;color:#F8FAFC;">High/Critical records:
    <b>{current_hr_count:,}</b> current
    &nbsp;→&nbsp;
    <b style="color:{risk_color};">{scenario_hr_count:,}</b> scenario
    &nbsp;<span style="color:{risk_color};">{risk_arrow} {abs(risk_delta):,}</span>
  </span>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("Utilization: Current vs Scenario by Region", "📊")
        if "region" in scen_df.columns:
            reg_comp = scen_df.groupby("region").agg(
                current_util=("current_utilization", "mean"),
                scenario_util=("scenario_utilization", "mean"),
            ).reset_index()
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=reg_comp["region"], y=reg_comp["current_util"],
                name="Current", marker_color="#94A3B8",
            ))
            fig_comp.add_trace(go.Bar(
                x=reg_comp["region"], y=reg_comp["scenario_util"],
                name="Scenario", marker_color="#3B82F6",
            ))
            fig_comp.add_hline(y=risk_threshold, line_dash="dot",
                               line_color="#EF4444", annotation_text=f"Risk Threshold ({risk_threshold:.0%})")
            fig_comp = apply_dark_theme(fig_comp, height=340)
            fig_comp.update_layout(barmode="group", yaxis_title="Avg Utilization",
                                   yaxis_tickformat=".0%")
            st.plotly_chart(fig_comp, width='stretch')

    with col_right:
        section_header("Monthly Capacity Gap (Scenario)", "📅")
        if "date" in scen_df.columns:
            scen_df["month"] = pd.to_datetime(scen_df["date"]).dt.to_period("M").astype(str)
            monthly_gap = scen_df.groupby("month")["capacity_gap"].sum().reset_index().sort_values("month")
            colors_gap = ["#22C55E" if v >= 0 else "#EF4444" for v in monthly_gap["capacity_gap"]]
            fig_gap = go.Figure(go.Bar(
                x=monthly_gap["month"],
                y=monthly_gap["capacity_gap"],
                marker_color=colors_gap,
                hovertemplate="<b>%{x}</b><br>Gap: %{y:,.0f}<extra></extra>",
            ))
            fig_gap = apply_dark_theme(fig_gap, height=340)
            fig_gap.update_layout(yaxis_title="Capacity Gap (Units)", showlegend=False)
            fig_gap.update_traces(marker_line_width=0)
            st.plotly_chart(fig_gap, width='stretch')
