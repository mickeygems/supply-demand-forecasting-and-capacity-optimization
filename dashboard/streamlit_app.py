import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Add root directory to sys path so relative imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import new components
from dashboard.components.header import render_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.overview import render_overview
from dashboard.components.forecast import render_forecast
from dashboard.components.regional import render_regional
from dashboard.components.risk import render_risk
from dashboard.components.cost import render_cost
from dashboard.components.whatif import render_whatif
from dashboard.components.model_intelligence import render_model_intelligence
from dashboard.components.data_explorer import render_data_explorer

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="Cloud Capacity Intelligence",
    layout="wide",
    page_icon="☁️"
)

# Load Master CSS Theme
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "styles", "theme.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

DATA_PATH = "data/forecast_output.csv"

# -------------------------------------------------------------
# Data Loading (Preserving verbatim logic)
# -------------------------------------------------------------
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    df = pd.read_csv(DATA_PATH)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

if df is None:
    st.markdown('<div class="page-title">☁️ Cloud Capacity Intelligence</div>', unsafe_allow_html=True)
    st.info("No forecast data found. Please place `new_data.csv` in `data/` and click 'Run Batch Prediction' in the sidebar.")
    st.stop()

# Ensure required columns (Preserving verbatim fallback logic)
req_cols = ["date", "region", "service_type", "demand_units", "predicted_demand", "capacity_allocated"]
for c in req_cols:
    if c not in df.columns:
        if c == 'predicted_demand':
            df['predicted_demand'] = df['demand_units'] # Fallback
        elif c == 'capacity_allocated':
            df['capacity_allocated'] = df['demand_units'] * 1.2

# -------------------------------------------------------------
# Sidebar & Filters
# -------------------------------------------------------------
sidebar_state = render_sidebar(df)

sel_page = sidebar_state["page"]
sel_regions = sidebar_state["regions"]
sel_services = sidebar_state["services"]
sel_years = sidebar_state["years"]
risk_threshold = sidebar_state["risk_threshold"]
uploaded_df = sidebar_state["uploaded_df"]

# Determine source data
source_df = uploaded_df if uploaded_df is not None else df

# Apply filters (Preserving verbatim filter logic behavior)
filtered_df = source_df.copy()
if sel_regions:
    filtered_df = filtered_df[filtered_df["region"].isin(sel_regions)]
if sel_services:
    filtered_df = filtered_df[filtered_df["service_type"].isin(sel_services)]
if sel_years and "date" in filtered_df.columns:
    filtered_df = filtered_df[pd.to_datetime(filtered_df["date"]).dt.year.isin(sel_years)]

# -------------------------------------------------------------
# Shared Metrics Calculation
# -------------------------------------------------------------
def directional_accuracy(actual, pred):
    if len(actual) < 2: return 0.0
    act_diff = np.sign(np.diff(actual))
    pred_diff = np.sign(np.diff(pred))
    return np.mean(act_diff == pred_diff) * 100

valid_metrics_df = filtered_df.dropna(subset=["demand_units", "predicted_demand"])
if len(valid_metrics_df) > 0:
    rmse = np.sqrt(mean_squared_error(valid_metrics_df["demand_units"], valid_metrics_df["predicted_demand"]))
    mae = mean_absolute_error(valid_metrics_df["demand_units"], valid_metrics_df["predicted_demand"])
    dir_acc = directional_accuracy(valid_metrics_df["demand_units"].values, valid_metrics_df["predicted_demand"].values)
    nonzero_actuals = np.where(valid_metrics_df["demand_units"] == 0, 1e-9, valid_metrics_df["demand_units"])
    mape = np.mean(np.abs((valid_metrics_df["demand_units"] - valid_metrics_df["predicted_demand"]) / nonzero_actuals)) * 100
else:
    rmse, mae, dir_acc, mape = 0.0, 0.0, 0.0, 0.0

metrics = {
    "rmse": rmse,
    "mae": mae,
    "dir_acc": dir_acc,
    "mape": mape
}

# -------------------------------------------------------------
# Header
# -------------------------------------------------------------
render_header(filtered_df)

# -------------------------------------------------------------
# Page Routing
# -------------------------------------------------------------
if sel_page == "Overview":
    render_overview(filtered_df, metrics, risk_threshold)
elif sel_page == "Demand Forecast":
    render_forecast(filtered_df, metrics)
elif sel_page == "Regional Analysis":
    render_regional(filtered_df, risk_threshold)
elif sel_page == "Risk Center":
    render_risk(filtered_df, risk_threshold)
elif sel_page == "Cost Optimization":
    render_cost(filtered_df)
elif sel_page == "What-If Analysis":
    render_whatif(filtered_df, risk_threshold)
elif sel_page == "Model Intelligence":
    render_model_intelligence(filtered_df, metrics)
elif sel_page == "Data Explorer":
    render_data_explorer(filtered_df)
