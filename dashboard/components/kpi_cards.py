"""
KPI card renderer — generates styled HTML metric cards.
"""
import streamlit as st


def kpi_card(label: str, value: str, delta: str = None,
             delta_type: str = "neutral", icon: str = None,
             accent_color: str = "#3B82F6") -> str:
    """
    Return the HTML string for a single KPI card.
    delta_type: 'positive' | 'negative' | 'neutral'
    """
    icon_html = f'<span style="font-size:14px;margin-right:4px;">{icon}</span>' if icon else ""
    delta_html = ""
    if delta:
        delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>'

    return f"""
<div class="kpi-card" style="--card-accent:{accent_color};">
  <div class="kpi-label">{icon_html}{label}</div>
  <div class="kpi-value">{value}</div>
  {delta_html}
</div>"""


def render_kpi_row(cards: list[dict], columns: int = 6):
    """
    Render a row of KPI cards.
    Each dict: {label, value, delta?, delta_type?, icon?, accent_color?}
    """
    cols = st.columns(columns)
    for i, card in enumerate(cards):
        html = kpi_card(
            label=card.get("label", ""),
            value=card.get("value", "—"),
            delta=card.get("delta"),
            delta_type=card.get("delta_type", "neutral"),
            icon=card.get("icon"),
            accent_color=card.get("accent_color", "#3B82F6"),
        )
        with cols[i % columns]:
            st.markdown(html, unsafe_allow_html=True)


def risk_badge(level: str) -> str:
    """Return HTML badge string for risk level."""
    mapping = {
        "Low":      ("badge-success",  "🟢 LOW"),
        "Moderate": ("badge-moderate", "🔵 MODERATE"),
        "High":     ("badge-warning",  "🟠 HIGH"),
        "Critical": ("badge-danger",   "🔴 CRITICAL"),
    }
    cls, label = mapping.get(level, ("badge-neutral", level))
    return f'<span class="badge {cls}">{label}</span>'


def insight_panel(text: str):
    """Render the Key Insight panel."""
    st.markdown(f"""
<div class="insight-panel">
  <div class="insight-panel-label">⚡ KEY INSIGHT</div>
  <p class="insight-panel-text">{text}</p>
</div>""", unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    """Render a styled section separator + title."""
    st.markdown(
        f'<div class="section-header">{icon}&nbsp;{title}</div>',
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str = ""):
    """Render a page title + subtitle."""
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def exec_summary(bullets: list[str]):
    """Render the Executive Summary block."""
    items = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(f"""
<div class="exec-summary">
  <div class="exec-summary-title">📋 Executive Summary</div>
  <ul>{items}</ul>
</div>""", unsafe_allow_html=True)
