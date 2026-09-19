"""
Sidebar component.

Renders the persistent left panel containing:
  - Backend connectivity status.
  - Ticket count metric.
  - Useful API links.

The Gemini API key is configured in backend/.env.
The dataset is pre-loaded at server startup — no upload needed.
"""
import streamlit as st

from app.api_client import get_health


def render() -> None:
    """Render the sidebar."""
    st.sidebar.title("🎫 Ticket AI System")

    # ── Backend health ────────────────────────────────────────────────────────
    health = get_health()
    if health and "_error" not in health and health.get("status") == "healthy":
        total   = health.get("database", {}).get("total_tickets", 0)
        gemini  = health.get("gemini_api", {})
        st.sidebar.success("● Backend Online")
        st.sidebar.metric("Tickets in DB", total)

        if gemini.get("configured"):
            st.sidebar.success(f"🤖 Gemini Ready\n`{gemini.get('model')}`")
        else:
            st.sidebar.warning(
                "⚠️ Gemini API key missing.\n"
                "Set `GEMINI_API_KEY` in `backend/.env` and restart the server."
            )
    else:
        err = (health or {}).get("_error", "Unknown error")
        st.sidebar.error("● Backend Offline")
        st.sidebar.caption(f"Run `python run.py` to start.\n\n_{err}_")

    st.sidebar.divider()

    # ── Quick links ───────────────────────────────────────────────────────────
    st.sidebar.markdown(
        "**API Links**\n"
        "- [Swagger Docs](http://127.0.0.1:8000/docs)\n"
        "- [Health Check](http://127.0.0.1:8000/health)\n"
        "- [Anomaly API](http://127.0.0.1:8000/api/anomalies)\n"
    )
