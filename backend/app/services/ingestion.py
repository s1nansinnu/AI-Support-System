"""
Ingestion service.

Responsibilities:
  - Validate and parse the support_tickets CSV.
  - Normalize column names and data types.
  - Load data into SQLite, replacing any previous data.
"""
import os
from typing import Dict, Any

import pandas as pd

from app.config import CSV_PATH
from app.database.connection import get_connection, init_db

# Canonical column names (CSV may use alternate names)
_COLUMN_MAP = {
    "response_time_hrs":   "resp_time_hrs",
    "resolution_time_hrs": "resol_time_hrs",
    "customer_rating":     "cust_rating",
}

_REQUIRED_COLUMNS = [
    "ticket_id", "created_at", "category", "priority", "status",
    "resp_time_hrs", "resol_time_hrs", "agent_id", "cust_rating",
    "issue_summary",
]


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Rename alternate column headers and cast to correct types."""
    df = df.rename(columns={k: v for k, v in _COLUMN_MAP.items() if k in df.columns})

    missing = [c for c in _REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df["ticket_id"]      = df["ticket_id"].astype(str).str.strip()
    df["created_at"]     = (
        pd.to_datetime(df["created_at"])
          .dt.strftime("%Y-%m-%d %H:%M")
    )
    df["category"]       = df["category"].astype(str).str.strip()
    df["priority"]       = df["priority"].astype(str).str.strip()
    df["status"]         = df["status"].astype(str).str.strip()
    df["resp_time_hrs"]  = pd.to_numeric(df["resp_time_hrs"],  errors="coerce").fillna(0.0)
    df["resol_time_hrs"] = pd.to_numeric(df["resol_time_hrs"], errors="coerce")
    df["agent_id"]       = df["agent_id"].astype(str).str.strip()
    df["cust_rating"]    = pd.to_numeric(df["cust_rating"],    errors="coerce")
    df["issue_summary"]  = df["issue_summary"].fillna("").astype(str).str.strip()

    return df


def ingest_csv(csv_path: str = CSV_PATH) -> Dict[str, Any]:
    """
    Parse *csv_path*, validate, and load into SQLite.
    Returns a summary dict on success; raises on failure.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    init_db()

    df = pd.read_csv(csv_path)
    df = _normalize(df)

    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM support_tickets")
            df.to_sql("support_tickets", conn, if_exists="append", index=False)
    finally:
        conn.close()

    return {
        "rows_ingested":       len(df),
        "status_breakdown":    df["status"].value_counts().to_dict(),
        "category_breakdown":  df["category"].value_counts().to_dict(),
        "earliest_ticket":     str(df["created_at"].min()),
        "latest_ticket":       str(df["created_at"].max()),
    }
