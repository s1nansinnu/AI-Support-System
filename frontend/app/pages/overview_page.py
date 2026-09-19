"""
📊 Dataset Overview Page.

Displays high-level ticket statistics and a sample preview.
"""
import streamlit as st

from app.api_client import get_health


def render() -> None:
    st.header("📊 Dataset Overview")
    st.markdown("High-level snapshot of the ingested support ticket data.")

    data = get_health()

    if not data or "_error" in data:
        st.warning(
            "⚠️ Cannot reach the backend API. "
            "Please start the server with `python run.py`."
        )
        return

    db = data.get("database", {})
    total = db.get("total_tickets", 0)

    if total == 0:
        st.info("No tickets ingested yet. Upload `support_tickets.csv` via the sidebar.")
        return

    # ── Top metrics ──────────────────────────────────────────────────────────
    status_counts = db.get("status_counts", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets",     total)
    c2.metric("Open",              status_counts.get("Open", 0))
    c3.metric("Resolved",          status_counts.get("Resolved", 0))
    c4.metric("Escalated",         status_counts.get("Escalated", 0))

    st.divider()

    # ── Status bar chart ─────────────────────────────────────────────────────
    if status_counts:
        st.markdown("### Tickets by Status")
        st.bar_chart(status_counts)

    # ── Gemini status ────────────────────────────────────────────────────────
    gemini = data.get("gemini_api", {})
    st.divider()
    st.markdown("### Gemini API Status")
    if gemini.get("configured"):
        st.success(f"✅ Gemini is configured — model: `{gemini.get('model')}`")
    else:
        st.warning(
            "⚠️ Gemini API key is not set. "
            "Enter it in the sidebar to enable AI-powered queries."
        )
