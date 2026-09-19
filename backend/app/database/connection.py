"""SQLite connection management and schema initialisation."""
import sqlite3
import re
from typing import Any, Dict, List, Tuple

from app.config import DB_PATH

# ── DDL ──────────────────────────────────────────────────────────────────────
_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id       TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    category        TEXT NOT NULL,
    priority        TEXT NOT NULL,
    status          TEXT NOT NULL,
    resp_time_hrs   REAL NOT NULL DEFAULT 0,
    resol_time_hrs  REAL,
    agent_id        TEXT NOT NULL,
    cust_rating     INTEGER,
    issue_summary   TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_status   ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_category ON support_tickets(category);
CREATE INDEX IF NOT EXISTS idx_agent    ON support_tickets(agent_id);
CREATE INDEX IF NOT EXISTS idx_created  ON support_tickets(created_at);
"""

# ── SQL safety: only SELECT / WITH allowed ───────────────────────────────────
_FORBIDDEN_PATTERNS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b",
    r"\bALTER\b", r"\bCREATE\b", r"\bATTACH\b", r"\bDETACH\b",
    r"\bPRAGMA\b", r"\bEXEC\b",  r"\bVACUUM\b",
    r";\s*\S+",   # multiple statements
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and indexes if they do not exist."""
    conn = get_connection()
    try:
        with conn:
            conn.executescript(_SCHEMA_DDL)
    finally:
        conn.close()


def is_safe_sql(sql: str) -> Tuple[bool, str]:
    """Return (True, 'Safe') or (False, reason) for a SQL string."""
    cleaned = sql.strip().rstrip(";")
    upper = cleaned.upper()

    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "Only SELECT or WITH queries are permitted."

    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, f"Prohibited keyword detected: {pattern}"

    return True, "Safe"


def run_query(sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Execute a validated read-only SQL query.
    Returns (list-of-row-dicts, column-names).
    Raises ValueError if the query fails the safety gate.
    """
    ok, reason = is_safe_sql(sql)
    if not ok:
        raise ValueError(f"SQL safety check failed: {reason}")

    conn = get_connection()
    try:
        cursor = conn.execute(sql)
        columns = [col[0] for col in (cursor.description or [])]
        rows    = [dict(row) for row in cursor.fetchall()]
        return rows, columns
    finally:
        conn.close()


def get_stats() -> Dict[str, Any]:
    """Return quick summary counts from the database."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM support_tickets").fetchone()[0]
        status_rows   = conn.execute(
            "SELECT status, COUNT(*) FROM support_tickets GROUP BY status"
        ).fetchall()
        category_rows = conn.execute(
            "SELECT category, COUNT(*) FROM support_tickets GROUP BY category"
        ).fetchall()
        return {
            "total_tickets":  total,
            "status_counts":  dict(status_rows),
            "category_counts": dict(category_rows),
        }
    except Exception as exc:
        return {"total_tickets": 0, "error": str(exc)}
    finally:
        conn.close()
