"""
Sidebar component — navigation, data source selector, and filters.
Returns the current page selection and filter values.
"""
import streamlit as st
import pandas as pd
from pipeline.batch_predict import run_batch_prediction

DATA_PATH = "data/forecast_output.csv"
NEW_DATA_PATH = "data/new_data.csv"

PAGES = [
    ("🏠", "Overview"),
    ("📈", "Demand Forecast"),
    ("🌍", "Regional Analysis"),
    ("🚨", "Risk Center"),
    ("💰", "Cost Optimization"),
    ("🔮", "What-If Analysis"),
    ("🧠", "Model Intelligence"),
    ("📊", "Data Explorer"),
]


def render_sidebar(df: pd.DataFrame) -> dict:
    """
    Render the full sidebar and return a dict with:
      page, regions, services, years, risk_threshold, uploaded_df
    """
    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────
        st.markdown("""
<div class="sidebar-brand">
  <div class="sidebar-brand-name">☁️ CLOUD CAPACITY<br>INTELLIGENCE</div>
  <div class="sidebar-brand-sub">Enterprise Forecasting Platform</div>
</div>""", unsafe_allow_html=True)

        # ── Navigation ─────────────────────────────────────────────
        st.markdown('<div class="sidebar-nav-label">NAVIGATION</div>', unsafe_allow_html=True)
        page_labels = [f"{icon} {name}" for icon, name in PAGES]
        selected_label = st.radio(
            label="nav",
            options=page_labels,
            label_visibility="collapsed",
            key="nav_page",
        )
        selected_page = selected_label.split(" ", 1)[1] if " " in selected_label else selected_label

        st.markdown("---")

        # ── Data Source ────────────────────────────────────────────
        st.markdown('<div class="sidebar-nav-label">DATA SOURCE</div>', unsafe_allow_html=True)
        data_source = st.radio(
            "Source",
            ["📊 Demo Data", "📁 Upload CSV / XLSX"],
            label_visibility="collapsed",
            key="data_source",
        )

        uploaded_df = None
        if "Upload" in data_source:
            uploaded_file = st.file_uploader(
                "Upload file",
                type=["csv", "xlsx"],
                label_visibility="collapsed",
            )
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".xlsx"):
                        uploaded_df = pd.read_excel(uploaded_file)
                    else:
                        uploaded_df = pd.read_csv(uploaded_file)
                    if "date" in uploaded_df.columns:
                        uploaded_df["date"] = pd.to_datetime(uploaded_df["date"])
                    st.success(f"Loaded {len(uploaded_df):,} rows")
                except Exception as e:
                    st.error(f"Failed to load file: {e}")

        st.markdown("---")

        # ── Batch Prediction ───────────────────────────────────────
        if st.button("🔄 Run Batch Prediction", width='stretch'):
            with st.spinner("Running XGBoost batch prediction…"):
                try:
                    run_batch_prediction(input_path=NEW_DATA_PATH, output_path=DATA_PATH)
                    st.success("Prediction complete! Refresh to see updated data.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Prediction failed: {e}")

        st.markdown("---")

        # ── Filters (populated from data) ─────────────────────────
        source_df = uploaded_df if uploaded_df is not None else df
        filters = _render_filters(source_df)
        filters["page"] = selected_page
        filters["uploaded_df"] = uploaded_df

    return filters


def _render_filters(df: pd.DataFrame) -> dict:
    """Render filter widgets and return selected values."""
    st.markdown('<div class="sidebar-nav-label">FILTERS</div>', unsafe_allow_html=True)

    if df is None:
        return {"regions": [], "services": [], "years": [], "risk_threshold": 0.8}

    # Regions
    all_regions = sorted(df["region"].dropna().unique().tolist()) if "region" in df.columns else []
    sel_regions = st.multiselect(
        "Regions",
        options=all_regions,
        default=all_regions,
        key="filter_regions",
    )

    # Services
    all_services = sorted(df["service_type"].dropna().unique().tolist()) if "service_type" in df.columns else []
    sel_services = st.multiselect(
        "Service Type",
        options=all_services,
        default=all_services,
        key="filter_services",
    )

    # Years
    all_years = []
    if "date" in df.columns:
        try:
            all_years = sorted(pd.to_datetime(df["date"]).dt.year.dropna().unique().tolist())
        except Exception:
            pass
    sel_years = st.multiselect(
        "Year",
        options=all_years,
        default=all_years,
        key="filter_years",
    )

    # Risk threshold
    risk_threshold = st.slider(
        "Capacity Risk Threshold",
        min_value=0.50,
        max_value=1.00,
        value=0.80,
        step=0.05,
        format="%.0f%%",
        help="Records where predicted demand / capacity exceeds this threshold are flagged as high-risk.",
        key="filter_risk_threshold",
    )

    return {
        "regions": sel_regions,
        "services": sel_services,
        "years": sel_years,
        "risk_threshold": risk_threshold,
    }
