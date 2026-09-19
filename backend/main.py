"""
FastAPI application entry point.

Registers all routers and sets up the lifespan handler
that initialises the database and auto-ingests the default dataset.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CSV_PATH
from app.database.connection import init_db
from app.services.ingestion import ingest_csv
from app.routers import health, query, anomalies, ingest


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB and auto-ingest CSV if available."""
    init_db()
    if os.path.exists(CSV_PATH):
        try:
            result = ingest_csv(CSV_PATH)
            print(f"[startup] Ingested {result['rows_ingested']} tickets from {CSV_PATH}")
        except Exception as exc:
            print(f"[startup] CSV ingestion skipped: {exc}")
    yield  # application is running
    # (teardown goes here if needed)


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Support Ticket Analytics API",
    description=(
        "End-to-end AI system for customer support ticket analysis. "
        "Powered by Google Gemini for Text-to-SQL and anomaly summarisation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(query.router)
app.include_router(anomalies.router)
app.include_router(ingest.router)
