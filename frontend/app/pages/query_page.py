"""
💬 Natural Language Query Page.

Renders the interactive query playground where users can type
or click a sample question and see:
  - The Gemini-generated SQL.
  - The raw result table.
  - The synthesised natural language answer.
"""
import pandas as pd
import streamlit as st

from app.api_client import run_query
from app.config import SAMPLE_QUERIES
from app.components.charts import bar_chart_from_df


def render() -> None:
    st.header("💬 Natural Language Query")
    st.markdown(
        "Ask any business question about the support tickets in plain English. "
        "**Google Gemini** converts it to SQL, runs it, and explains the results."
    )

    # ── Sample query buttons ─────────────────────────────────────────────────
    st.markdown("##### 💡 Quick-start queries:")
    cols = st.columns(2)
    preset = None
    for i, q in enumerate(SAMPLE_QUERIES):
        if cols[i % 2].button(q, key=f"sample_{i}", width="stretch"):
            preset = q

    # ── Query form (Enter key OR button both trigger submission) ─────────────
    with st.form(key="query_form", border=False):
        question = st.text_input(
            "Your question:",
            value=preset or "",
            placeholder="e.g. Which agent has the highest average customer rating?",
        )
        submitted = st.form_submit_button(
            "Run Query 🚀",
            type="primary",
            width="content",
        )

    if not submitted or not question.strip():
        return

    # ── Call backend ─────────────────────────────────────────────────────────
    with st.spinner("Translating and querying…"):
        result = run_query(question.strip())

    # ── Display results ──────────────────────────────────────────────────────
    if result.get("status") == "success":
        st.success("Query completed successfully.")

        st.markdown("### 🤖 Gemini Answer")
        st.info(result.get("answer", "—"))

        with st.expander("🔍 Generated SQL Query", expanded=True):
            st.code(result.get("sql_query", ""), language="sql")

        records = result.get("results", [])
        st.markdown(f"### 📋 Result Records ({len(records)} rows)")

        if records:
            df = pd.DataFrame(records)
            st.dataframe(df, width="stretch")
            bar_chart_from_df(df)
        else:
            st.info("The query returned no rows.")

    else:
        st.error(result.get("answer") or "An unexpected error occurred.")
