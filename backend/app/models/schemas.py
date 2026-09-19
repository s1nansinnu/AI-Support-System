"""Pydantic schemas for all API request and response contracts."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── /api/query ───────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    api_key: Optional[str] = None   # Optional override from UI


class QueryResponse(BaseModel):
    question: str
    sql_query: Optional[str] = None
    columns: List[str] = []
    results: List[Dict[str, Any]] = []
    row_count: int = 0
    answer: str
    status: str                     # "success" | "error"


# ── /api/anomalies ───────────────────────────────────────
class AnomalyRecord(BaseModel):
    ticket_id: str
    category: str
    priority: str
    status: str
    agent_id: str
    created_at: str
    resp_time_hrs: Optional[float] = None
    resol_time_hrs: Optional[float] = None
    anomaly_type: str
    severity: str                   # "CRITICAL" | "HIGH" | "MEDIUM"
    details: str


class AnomalyResponse(BaseModel):
    total_tickets: int
    anomaly_count: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    anomalies: List[AnomalyRecord]
    summary: str


# ── /api/ingest ──────────────────────────────────────────
class IngestResponse(BaseModel):
    message: str
    rows_ingested: int
    status_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    earliest_ticket: str
    latest_ticket: str


# ── /health ──────────────────────────────────────────────
class DBHealth(BaseModel):
    status: str
    total_tickets: int
    status_counts: Dict[str, int]


class GeminiHealth(BaseModel):
    configured: bool
    model: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    database: DBHealth
    gemini_api: GeminiHealth
