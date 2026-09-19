"""
Model Intelligence page — XGBoost performance metrics, drift monitoring,
and feature importance.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
from datetime import datetime

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title
from dashboard.components.charts import apply_dark_theme, QUALITATIVE


def render_model_intelligence(fdf: pd.DataFrame, metrics: dict):
    """Render the Model Intelligence page."""
    page_title("Model Intelligence", "XGBoost model performance, data drift, and explainability")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    # ── Model Artifact Info ─────────────────────────────────────────
    model_path = "models/xgb_model.pkl"
    features_path = "models/feature_names.pkl"
    model_date = "Unknown"
    num_features = "Unknown"
    
    if os.path.exists(model_path):
        mtime = os.path.getmtime(model_path)
        model_date = datetime.fromtimestamp(mtime).strftime("%b %d, %Y %H:%M")
    
    if os.path.exists(features_path):
        try:
            features = joblib.load(features_path)
            num_features = len(features)
        except Exception:
            pass

    st.markdown(f"""
<div style="background:var(--card-bg);border:1px solid var(--border);
     border-radius:12px;padding:16px 20px;margin-bottom:20px;display:flex;gap:32px;flex-wrap:wrap;">
  <div>
    <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Model Engine</div>
    <div style="font-size:16px;font-weight:600;color:var(--text-primary);display:flex;align-items:center;gap:6px;">
      <span class="badge badge-success">XGBoostRegressor</span>
    </div>
  </div>
  <div>
    <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Training Date</div>
    <div style="font-size:15px;color:var(--text-primary);">{model_date}</div>
  </div>
  <div>
    <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Feature Count</div>
    <div style="font-size:15px;color:var(--text-primary);">{num_features} extracted features</div>
  </div>
  <div>
    <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Monitoring Status</div>
    <div style="font-size:15px;color:var(--success);display:flex;align-items:center;gap:4px;">🟢 Active</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── KPIs & Anomalies ────────────────────────────────────────────
    valid_df = fdf.dropna(subset=["demand_units", "predicted_demand"])
    
    if len(valid_df) > 0:
        fdf2 = fdf.copy()
        fdf2["residuals"] = fdf2["demand_units"] - fdf2["predicted_demand"]
        std_resid = fdf2["residuals"].std()
        mean_resid = fdf2["residuals"].mean()
        fdf2["is_outlier"] = np.abs(fdf2["residuals"] - mean_resid) > (2 * std_resid)
        outlier_count = fdf2["is_outlier"].sum()
        
        # Drift calculations
        drift_df = valid_df.groupby("date").agg({"demand_units":"sum", "predicted_demand":"sum"}).reset_index()
        drift_df = drift_df.sort_values("date")
        drift_df["error"] = np.abs(drift_df["demand_units"] - drift_df["predicted_demand"])
        drift_df["rolling_mae"] = drift_df["error"].rolling(window=7, min_periods=1).mean()
        
        current_mae = drift_df["rolling_mae"].iloc[-1]
        start_mae = drift_df["rolling_mae"].iloc[0]
        drift_trend = current_mae - start_mae
    else:
        outlier_count = 0
        current_mae = 0
        drift_trend = 0
        fdf2 = fdf.copy()
        fdf2["residuals"] = 0
        fdf2["is_outlier"] = False
        drift_df = pd.DataFrame()

    rmse = metrics.get("rmse", 0)
    mae = metrics.get("mae", 0)
    mape = metrics.get("mape", 0)
    dir_acc = metrics.get("dir_acc", 0)

    row = [
        {"label": "Current Rolling MAE (7d)", "value": f"{current_mae:,.1f}",
         "delta": f"{drift_trend:+,.1f} Drift", "delta_type": "negative" if drift_trend > 0 else "positive",
         "icon": "🌊", "accent_color": "#F59E0B" if drift_trend > 0 else "#22C55E"},
        {"label": "Anomalies (>2 StdDev)", "value": f"{outlier_count:,}",
         "icon": "⚡", "accent_color": "#EF4444" if outlier_count > 0 else "#22C55E"},
        {"label": "RMSE", "value": f"{rmse:,.1f}", "icon": "🎯", "accent_color": "#A78BFA"},
        {"label": "MAPE", "value": f"{mape:.2f}%", "icon": "📉", "accent_color": "#2DD4BF"},
        {"label": "Directional Accuracy", "value": f"{dir_acc:.1f}%", "icon": "🧭", "accent_color": "#3B82F6"},
    ]
    render_kpi_row(row, columns=5)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Charts Row 1 ────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("Model Drift: 7-Day Rolling MAE", "📈")
        if len(drift_df) > 0:
            fig_drift = go.Figure()
            fig_drift.add_trace(go.Scatter(
                x=drift_df["date"], y=drift_df["rolling_mae"],
                mode="lines",
                line=dict(color="#F59E0B", width=2),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.1)",
                name="Rolling MAE",
                hovertemplate="<b>%{x|%b %d, %Y}</b><br>MAE: %{y:,.1f}<extra></extra>"
            ))
            fig_drift = apply_dark_theme(fig_drift, height=320)
            fig_drift.update_layout(yaxis_title="Mean Absolute Error (MAE)", showlegend=False)
            st.plotly_chart(fig_drift, width='stretch')

    with col_right:
        section_header("Prediction Anomalies", "🔴")
        if len(valid_df) > 0:
            fig_anom = px.scatter(
                fdf2, x="date", y="residuals", color="is_outlier",
                color_discrete_map={True: "#EF4444", False: "#3B82F6"},
                opacity=0.7
            )
            fig_anom = apply_dark_theme(fig_anom, height=320)
            fig_anom.update_layout(yaxis_title="Residual (Actual - Forecast)", xaxis_title="Date", legend_title="Anomaly")
            st.plotly_chart(fig_anom, width='stretch')

    # ── Feature Importance ──────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_header("Feature Importance (Explainability)", "🧠")
    
    try:
        model = joblib.load(model_path)
        features = joblib.load(features_path)
        
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
            imp_df = imp_df.sort_values("Importance", ascending=False).head(15)
            
            fig_imp = px.bar(
                imp_df, x="Importance", y="Feature", orientation="h",
                color="Importance", color_continuous_scale="Blues"
            )
            fig_imp = apply_dark_theme(fig_imp, height=400)
            fig_imp.update_layout(
                yaxis={'categoryorder':'total ascending'},
                xaxis_title="Relative Importance Score",
                yaxis_title="",
                coloraxis_showscale=False
            )
            fig_imp.update_traces(marker_line_width=0)
            st.plotly_chart(fig_imp, width='stretch')
        else:
            st.info("Feature importance not available for this model type.")
            
    except Exception as e:
        st.info(f"Could not load feature importance: {e}")
