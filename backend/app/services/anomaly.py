"""
Anomaly detection service.

Detects two categories of anomalies:
  1. Rule-based operational breaches (SLA violations).
  2. Statistical outliers via IQR on resolution and response times.
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from app.database.connection import get_connection


# ── Internal helpers ──────────────────────────────────────────────────────────

def _safe_float(value: Any) -> Optional[float]:
    """Convert a pandas value to float; return None for NaN/NaT."""
    try:
        return None if pd.isna(value) else float(value)
    except Exception:
        return None


def _make_record(
    row: pd.Series,
    anomaly_type: str,
    severity: str,
    details: str,
) -> Dict[str, Any]:
    return {
        "ticket_id":     row["ticket_id"],
        "category":      row["category"],
        "priority":      row["priority"],
        "status":        row["status"],
        "agent_id":      row["agent_id"],
        "created_at":    row["created_at"],
        "resp_time_hrs": _safe_float(row["resp_time_hrs"]),
        "resol_time_hrs":_safe_float(row["resol_time_hrs"]),
        "anomaly_type":  anomaly_type,
        "severity":      severity,
        "details":       details,
    }


# ── Detection logic ───────────────────────────────────────────────────────────

def _detect_sla_breaches(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Flag unresolved High / Critical tickets past SLA thresholds.
      • Critical > 12 h  → CRITICAL severity
      • High / Critical > 24 h → CRITICAL / HIGH severity
    Uses the latest created_at timestamp as the reference "now" so the
    function is deterministic on historical datasets.
    """
    records: List[Dict[str, Any]] = []
    ref_time = df["created_at_dt"].max()
    df = df.copy()
    df["age_hours"] = (ref_time - df["created_at_dt"]).dt.total_seconds() / 3600.0

    unresolved = df[df["status"] != "Resolved"]

    # Critical > 12 h (and ≤ 24 h to avoid double-counting with next rule)
    mask_12h = (
        unresolved["priority"].eq("Critical") &
        unresolved["age_hours"].gt(12.0) &
        unresolved["age_hours"].le(24.0)
    )
    for _, row in unresolved[mask_12h].iterrows():
        records.append(_make_record(
            row,
            anomaly_type="SLA Breach (Critical >12 h)",
            severity="CRITICAL",
            details=(
                f"Critical ticket unresolved for {row['age_hours']:.1f} h "
                f"(SLA limit: 12 h)."
            ),
        ))

    # High or Critical > 24 h
    mask_24h = (
        unresolved["priority"].isin(["High", "Critical"]) &
        unresolved["age_hours"].gt(24.0)
    )
    for _, row in unresolved[mask_24h].iterrows():
        sev = "CRITICAL" if row["priority"] == "Critical" else "HIGH"
        records.append(_make_record(
            row,
            anomaly_type="SLA Breach (High/Critical >24 h)",
            severity=sev,
            details=(
                f"{row['priority']} ticket unresolved for {row['age_hours']:.1f} h "
                f"(SLA limit: 24 h)."
            ),
        ))

    return records


def _detect_resolution_outliers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    IQR-based detection of abnormally long resolution times,
    computed per category so each group has its own threshold.
    """
    records: List[Dict[str, Any]] = []
    resolved = df[df["status"] == "Resolved"].dropna(subset=["resol_time_hrs"])

    for category, group in resolved.groupby("category"):
        q1 = group["resol_time_hrs"].quantile(0.25)
        q3 = group["resol_time_hrs"].quantile(0.75)
        threshold = q3 + 1.5 * (q3 - q1)

        outliers = group[group["resol_time_hrs"] > threshold]
        for _, row in outliers.iterrows():
            records.append(_make_record(
                row,
                anomaly_type="Abnormal Resolution Time",
                severity="HIGH",
                details=(
                    f"Resolution time {row['resol_time_hrs']:.1f} h exceeds the "
                    f"'{category}' category threshold of {threshold:.1f} h."
                ),
            ))

    return records


def _detect_response_outliers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """IQR-based detection of abnormally long first-response times (all tickets)."""
    records: List[Dict[str, Any]] = []
    q1 = df["resp_time_hrs"].quantile(0.25)
    q3 = df["resp_time_hrs"].quantile(0.75)
    threshold = q3 + 1.5 * (q3 - q1)

    outliers = df[df["resp_time_hrs"] > threshold]
    for _, row in outliers.iterrows():
        records.append(_make_record(
            row,
            anomaly_type="Abnormal Response Lag",
            severity="MEDIUM",
            details=(
                f"First response time {row['resp_time_hrs']:.1f} h exceeds the "
                f"statistical threshold of {threshold:.1f} h."
            ),
        ))

    return records


# ── Public API ────────────────────────────────────────────────────────────────

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}


def detect_anomalies() -> Dict[str, Any]:
    """
    Run all anomaly detectors and return a consolidated report.

    Returns dict with keys:
      total_tickets, anomaly_count, by_severity, by_type, anomalies, summary
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM support_tickets", conn)
    finally:
        conn.close()

    if df.empty:
        return {
            "total_tickets": 0,
            "anomaly_count": 0,
            "by_severity":   {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0},
            "by_type":       {},
            "anomalies":     [],
            "summary":       "No tickets in the database.",
        }

    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")

    # Collect all anomalies from each detector
    raw_records: List[Dict[str, Any]] = []
    raw_records.extend(_detect_sla_breaches(df))
    raw_records.extend(_detect_resolution_outliers(df))
    raw_records.extend(_detect_response_outliers(df))

    # Deduplicate by (ticket_id, anomaly_type)
    seen: set = set()
    unique: List[Dict[str, Any]] = []
    for rec in raw_records:
        key = (rec["ticket_id"], rec["anomaly_type"])
        if key not in seen:
            seen.add(key)
            unique.append(rec)

    # Sort: CRITICAL → HIGH → MEDIUM
    unique.sort(key=lambda r: _SEVERITY_ORDER.get(r["severity"], 9))

    by_severity = {
        "CRITICAL": sum(1 for r in unique if r["severity"] == "CRITICAL"),
        "HIGH":     sum(1 for r in unique if r["severity"] == "HIGH"),
        "MEDIUM":   sum(1 for r in unique if r["severity"] == "MEDIUM"),
    }
    by_type: Dict[str, int] = {}
    for rec in unique:
        by_type[rec["anomaly_type"]] = by_type.get(rec["anomaly_type"], 0) + 1

    summary = (
        f"Detected {len(unique)} anomalies across {len(df)} tickets — "
        f"{by_severity['CRITICAL']} Critical SLA breaches, "
        f"{by_severity['HIGH']} High resolution outliers, "
        f"{by_severity['MEDIUM']} Medium response lags."
    )

    return {
        "total_tickets": len(df),
        "anomaly_count": len(unique),
        "by_severity":   by_severity,
        "by_type":       by_type,
        "anomalies":     unique,
        "summary":       summary,
    }
