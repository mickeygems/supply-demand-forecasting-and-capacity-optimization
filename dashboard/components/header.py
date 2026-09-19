"""
Application header component — renders the branded top banner
and live system status bar.
"""
import streamlit as st
import pandas as pd


def render_header(df: pd.DataFrame):
    """Render the CCI header with status bar derived from actual data."""
    last_updated = "N/A"
    if df is not None and "date" in df.columns:
        try:
            last_updated = pd.to_datetime(df["date"]).max().strftime("%b %d, %Y")
        except Exception:
            pass

    st.markdown(f"""
<div class="cci-header">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;">
    <div>
      <div class="cci-header-title">☁️ CLOUD CAPACITY INTELLIGENCE</div>
      <div class="cci-header-subtitle">AI-Powered Demand Forecasting &amp; Capacity Planning</div>
    </div>
    <div style="text-align:right;">
      <span class="badge badge-success" style="font-size:12px;">XGBoost</span>
    </div>
  </div>
  <div class="cci-status-bar">
    <div class="cci-status-dot">
      <span class="dot"></span>
      SYSTEM HEALTHY
    </div>
    <span class="cci-status-chip">Model: <span>XGBoost</span></span>
    <span class="cci-status-chip">Forecast Engine: <span>Online</span></span>
    <span class="cci-status-chip">Last Updated: <span>{last_updated}</span></span>
  </div>
</div>""", unsafe_allow_html=True)
