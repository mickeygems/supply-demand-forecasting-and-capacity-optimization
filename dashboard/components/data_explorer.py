"""
Data Explorer page — searchable, filterable raw data view with downloads.
"""
import streamlit as st
import pandas as pd

from dashboard.components.kpi_cards import render_kpi_row, section_header, page_title


def render_data_explorer(fdf: pd.DataFrame):
    """Render the Data Explorer page."""
    page_title("Data Explorer", "Explore, filter, and download raw capacity records")

    if fdf is None or len(fdf) == 0:
        st.warning("No data available for the selected filters.")
        return

    # ── KPIs ────────────────────────────────────────────────────────
    total_rows = len(fdf)
    avg_demand = fdf["demand_units"].mean() if "demand_units" in fdf.columns else 0
    avg_util   = (fdf["predicted_demand"] / fdf["capacity_allocated"]).mean() if "predicted_demand" in fdf.columns and "capacity_allocated" in fdf.columns else 0
    avg_cost   = fdf["cost_usd"].mean() if "cost_usd" in fdf.columns else 0

    row = [
        {"label": "Rows Displayed",   "value": f"{total_rows:,}",    "icon": "📑", "accent_color": "#3B82F6"},
        {"label": "Avg Actual Demand","value": f"{avg_demand:,.1f}", "icon": "📊", "accent_color": "#22C55E"},
        {"label": "Avg Utilization",  "value": f"{avg_util:.1%}",    "icon": "⚙️", "accent_color": "#F59E0B"},
        {"label": "Avg Daily Cost",   "value": f"${avg_cost:,.2f}",  "icon": "💲", "accent_color": "#A78BFA"},
    ]
    render_kpi_row(row, columns=4)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Explorer Controls ───────────────────────────────────────────
    section_header("Records", "🗃️")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search records", placeholder="Type region, service type, etc.", key="dx_search")
    with col2:
        cols_to_show = st.multiselect(
            "Columns", options=fdf.columns.tolist(), default=fdf.columns.tolist()[:8], key="dx_cols"
        )
        
    display_df = fdf.copy()
    
    if search:
        # Simple text search across string columns
        str_cols = display_df.select_dtypes(include=['object', 'string']).columns
        if len(str_cols) > 0:
            mask = pd.Series(False, index=display_df.index)
            for c in str_cols:
                mask |= display_df[c].astype(str).str.contains(search, case=False, na=False)
            display_df = display_df[mask]

    # Format numeric columns for display
    styled_df = display_df[cols_to_show].copy()
    if "date" in styled_df.columns:
        styled_df["date"] = pd.to_datetime(styled_df["date"]).dt.strftime("%Y-%m-%d")
    
    for col in styled_df.select_dtypes(include=['float64']).columns:
        if "cost" in col.lower():
            styled_df[col] = styled_df[col].map("${:,.2f}".format)
        elif "utilization" in col.lower() or "availability" in col.lower() or "rate" in col.lower() or "growth" in col.lower():
            styled_df[col] = styled_df[col].map("{:.2f}".format)
        else:
            styled_df[col] = styled_df[col].map("{:,.1f}".format)

    st.markdown(f"<div style='font-size:12px;color:#94A3B8;margin-bottom:8px;'>Showing {len(styled_df):,} records</div>", unsafe_allow_html=True)
    st.dataframe(styled_df, width='stretch', hide_index=True)

    # ── Download ────────────────────────────────────────────────────
    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        data=csv_data,
        file_name="capacity_data_export.csv",
        mime="text/csv",
    )
