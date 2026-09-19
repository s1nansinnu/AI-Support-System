"""
🚨 Anomaly Detection Page.

Displays SLA breaches and statistical outliers detected in the
ticket dataset, with severity-based filtering and charts.
"""
import pandas as pd
import streamlit as st

from app.api_client import get_anomalies


_SEVERITY_COLORS = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
}

_DISPLAY_COLUMNS = [
    "ticket_id", "severity", "anomaly_type", "category",
    "priority", "status", "agent_id",
    "resp_time_hrs", "resol_time_hrs", "details",
]


def render() -> None:
    st.header("🚨 Anomaly Detection Monitor")
    st.markdown(
        "Identifies **SLA breaches** (unresolved High/Critical tickets past "
        "their time thresholds) and **statistical outliers** (IQR-based) for "
        "resolution and first-response times."
    )

    with st.spinner("Scanning tickets for anomalies…"):
        data = get_anomalies()

    # ── Error guard ──────────────────────────────────────────────────────────
    if "_error" in data:
        st.error(f"Could not load anomaly data: {data['_error']}")
        return

    if data.get("anomaly_count", 0) == 0:
        st.success("✅ No anomalies detected. Dataset may be empty or all tickets are within SLA.")
        return

    # ── Summary metrics ──────────────────────────────────────────────────────
    by_sev = data.get("by_severity", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Anomalies",    data["anomaly_count"])
    c2.metric("🔴 Critical",        by_sev.get("CRITICAL", 0))
    c3.metric("🟠 High",            by_sev.get("HIGH", 0))
    c4.metric("🟡 Medium",          by_sev.get("MEDIUM", 0))

    st.info(f"📌 {data.get('summary', '')}")
    st.divider()

    # ── Filters ──────────────────────────────────────────────────────────────
    all_types = list(data.get("by_type", {}).keys())

    f1, f2 = st.columns(2)
    with f1:
        sel_severity = st.multiselect(
            "Filter by Severity",
            options=["CRITICAL", "HIGH", "MEDIUM"],
            default=["CRITICAL", "HIGH", "MEDIUM"],
        )
    with f2:
        sel_types = st.multiselect(
            "Filter by Anomaly Type",
            options=all_types,
            default=all_types,
        )

    # ── Table ────────────────────────────────────────────────────────────────
    df = pd.DataFrame(data.get("anomalies", []))
    if df.empty:
        st.info("No anomalies match the current filters.")
        return

    filtered = df[
        df["severity"].isin(sel_severity) &
        df["anomaly_type"].isin(sel_types)
    ]

    display_cols = [c for c in _DISPLAY_COLUMNS if c in filtered.columns]
    st.markdown(f"### Flagged Tickets ({len(filtered)})")
    st.dataframe(filtered[display_cols], use_container_width=True)

    # ── Charts ───────────────────────────────────────────────────────────────
    st.markdown("### Distribution by Category")
    cat_counts = filtered["category"].value_counts()
    st.bar_chart(cat_counts)

    st.markdown("### Distribution by Anomaly Type")
    type_counts = filtered["anomaly_type"].value_counts()
    st.bar_chart(type_counts)
