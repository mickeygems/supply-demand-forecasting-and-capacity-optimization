"""
Demand Forecast page — polished actual vs forecast visualization.
All metrics and charts use existing data columns only.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title
from dashboard.components.charts import apply_dark_theme, QUALITATIVE, COLORS


def render_forecast(fdf: pd.DataFrame, metrics: dict):
    """Render the Demand Forecast page."""
    page_title("Demand Forecast", "XGBoost model — actual vs predicted demand over time")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    rmse     = metrics.get("rmse", 0)
    mae      = metrics.get("mae", 0)
    mape     = metrics.get("mape", 0)
    dir_acc  = metrics.get("dir_acc", 0)

    total_forecast = fdf["predicted_demand"].sum()
    total_actual   = fdf["demand_units"].sum() if "demand_units" in fdf.columns else 0

    valid_df = fdf.dropna(subset=["demand_units", "predicted_demand"])
    avg_res = (valid_df["demand_units"] - valid_df["predicted_demand"]).mean() if len(valid_df) > 0 else 0
    max_res = (valid_df["demand_units"] - valid_df["predicted_demand"]).abs().max() if len(valid_df) > 0 else 0

    peak_f_date = "N/A"
    if not fdf["predicted_demand"].isna().all():
        idx = fdf["predicted_demand"].idxmax()
        if pd.notna(idx):
            peak_f_date = fdf.loc[idx, "date"].strftime("%b %d, %Y")

    peak_a_date = "N/A"
    if "demand_units" in fdf.columns and not fdf["demand_units"].isna().all():
        idx2 = fdf["demand_units"].idxmax()
        if pd.notna(idx2):
            peak_a_date = fdf.loc[idx2, "date"].strftime("%b %d, %Y")

    # ── KPI Row ────────────────────────────────────────────────────
    row = [
        {"label": "Total Forecast Demand", "value": f"{total_forecast:,.0f}", "icon": "📈", "accent_color": "#3B82F6"},
        {"label": "Total Actual Demand",   "value": f"{total_actual:,.0f}",   "icon": "📊", "accent_color": "#22C55E"},
        {"label": "RMSE",  "value": f"{rmse:,.1f}",  "icon": "🎯", "accent_color": "#A78BFA"},
        {"label": "MAE",   "value": f"{mae:,.1f}",   "icon": "📐", "accent_color": "#2DD4BF"},
        {"label": "MAPE",  "value": f"{mape:.2f}%",  "icon": "📉", "accent_color": "#F59E0B"},
        {"label": "Directional Accuracy", "value": f"{dir_acc:.1f}%", "icon": "🧭", "accent_color": "#60A5FA"},
    ]
    render_kpi_row(row, columns=6)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    row2 = [
        {"label": "Peak Forecast Date", "value": peak_f_date, "icon": "📅", "accent_color": "#3B82F6"},
        {"label": "Peak Actual Date",   "value": peak_a_date, "icon": "📅", "accent_color": "#0078D4"},
        {"label": "Avg Residual",       "value": f"{avg_res:+.2f}", "icon": "⚖️",
         "delta_type": "positive" if abs(avg_res) < rmse * 0.1 else "negative",
         "accent_color": "#22C55E"},
        {"label": "Max Abs Residual",   "value": f"{max_res:,.2f}", "icon": "⚡", "accent_color": "#EF4444"},
    ]
    render_kpi_row(row2, columns=4)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Main Chart: Actual vs Forecast ─────────────────────────────
    section_header("Actual vs Forecast Time Series", "📈")
    agg_df = fdf.groupby("date")[["demand_units", "predicted_demand"]].sum().reset_index()
    agg_df = agg_df.sort_values("date")

    fig_main = go.Figure()
    fig_main.add_trace(go.Scatter(
        x=agg_df["date"], y=agg_df["demand_units"],
        name="Actual Demand",
        mode="lines",
        line=dict(color="#94A3B8", width=1.5, dash="dot"),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Actual: %{y:,.0f}<extra></extra>",
    ))
    fig_main.add_trace(go.Scatter(
        x=agg_df["date"], y=agg_df["predicted_demand"],
        name="Forecast (XGBoost)",
        mode="lines",
        line=dict(color="#3B82F6", width=2),
        fill="tonexty",
        fillcolor="rgba(59,130,246,0.06)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Forecast: %{y:,.0f}<extra></extra>",
    ))
    fig_main = apply_dark_theme(fig_main, height=400)
    fig_main.update_layout(
        yaxis_title="Demand Units",
        xaxis_title="Date",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05, x=0),
    )
    st.plotly_chart(fig_main, width='stretch')

    # ── Second Row ──────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("Residuals Distribution", "📦")
        fdf2 = fdf.copy()
        fdf2["residuals"] = fdf2["demand_units"] - fdf2["predicted_demand"]
        fig_hist = px.histogram(
            fdf2.dropna(subset=["residuals"]),
            x="residuals", nbins=50, color="service_type",
            color_discrete_sequence=QUALITATIVE,
            opacity=0.85,
        )
        fig_hist = apply_dark_theme(fig_hist, title=None, height=320)
        fig_hist.update_layout(
            xaxis_title="Residual (Actual − Forecast)",
            yaxis_title="Count",
            bargap=0.02,
        )
        st.plotly_chart(fig_hist, width='stretch')

    with col_right:
        section_header("Forecast Growth by Region & Service", "🌍")
        if "region" in fdf.columns and "service_type" in fdf.columns:
            half = len(fdf) // 2
            growth_rows = []
            for reg in fdf["region"].unique():
                for svc in fdf["service_type"].unique():
                    sub = fdf[(fdf["region"] == reg) & (fdf["service_type"] == svc)]
                    if len(sub) < 2:
                        continue
                    h1 = sub.iloc[:len(sub)//2]["predicted_demand"].sum()
                    h2 = sub.iloc[len(sub)//2:]["predicted_demand"].sum()
                    growth = ((h2 - h1) / h1 * 100) if h1 > 0 else 0
                    growth_rows.append({"Region": reg, "Service": svc, "Growth %": round(growth, 1)})

            if growth_rows:
                g_df = pd.DataFrame(growth_rows)
                fig_growth = px.bar(
                    g_df, x="Region", y="Growth %", color="Service",
                    color_discrete_sequence=QUALITATIVE,
                    barmode="group",
                )
                fig_growth = apply_dark_theme(fig_growth, title=None, height=320)
                fig_growth.update_layout(yaxis_title="Growth % (H2 vs H1)", bargap=0.15)
                st.plotly_chart(fig_growth, width='stretch')
