"""
Streamlit frontend entry point.

Assembles the sidebar and three main tabs:
  1. 💬 Natural Language Query
  2. 🚨 Anomaly Detection
  3. 📊 Dataset Overview
"""
import streamlit as st

from app.config import APP_TITLE, APP_ICON
from app.components.sidebar import render as render_sidebar
from app.pages.query_page   import render as render_query
from app.pages.anomaly_page import render as render_anomalies
from app.pages.overview_page import render as render_overview


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Render sidebar (no return value needed)
    render_sidebar()

    # Main tab layout
    tab_query, tab_anomalies, tab_overview = st.tabs([
        "💬 Natural Language Query",
        "🚨 Anomaly Detection",
        "📊 Dataset Overview",
    ])

    with tab_query:
        render_query()

    with tab_anomalies:
        render_anomalies()

    with tab_overview:
        render_overview()


if __name__ == "__main__":
    main()
