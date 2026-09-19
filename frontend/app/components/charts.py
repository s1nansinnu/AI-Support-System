"""
Reusable chart components.

Each function checks whether the data is suitable before rendering
so callers never need to guard against empty DataFrames.
"""
import pandas as pd
import streamlit as st


def bar_chart_from_df(df: pd.DataFrame, max_rows: int = 30) -> None:
    """
    Attempt to render a bar chart from a DataFrame.

    Selects the first string column as the label axis and the first
    numeric column as the value axis.  Does nothing if unsuitable.
    """
    if df.empty or len(df) > max_rows:
        return

    str_cols = df.select_dtypes(include=["object"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not str_cols or not num_cols:
        return

    with st.expander("📈 Chart View", expanded=False):
        chart_df = df.set_index(str_cols[0])[[num_cols[0]]]
        st.bar_chart(chart_df)
