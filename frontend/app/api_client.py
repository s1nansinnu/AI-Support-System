"""
API client — the single point of contact between the frontend and the backend.

All pages and components call functions from this module.
No page should ever import `requests` directly.
"""
from typing import Any, Dict, Optional

import requests
import streamlit as st

from app.config import API_BASE_URL, REQUEST_TIMEOUT_SECONDS


# ── Generic helpers ───────────────────────────────────────────────────────────

def _get(endpoint: str) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"_error": f"Cannot reach backend at {API_BASE_URL}. Start the server first."}
    except Exception as exc:
        return {"_error": str(exc)}


def _post_json(endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "answer": f"Cannot reach backend at {API_BASE_URL}."}
    except Exception as exc:
        return {"status": "error", "answer": str(exc)}


def _post_file(endpoint: str, file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.post(
            f"{API_BASE_URL}{endpoint}",
            files={"file": (filename, file_bytes, "text/csv")},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"_error": f"Cannot reach backend at {API_BASE_URL}."}
    except Exception as exc:
        return {"_error": str(exc)}


# ── Public API calls ──────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_health() -> Optional[Dict[str, Any]]:
    """
    Fetch /health — cached for 30 seconds.
    Prevents repeated calls on every Streamlit rerender.
    """
    return _get("/health")


def run_query(question: str) -> Dict[str, Any]:
    """POST /api/query — never cached; always calls live."""
    return _post_json("/api/query", {"question": question}) or {}


@st.cache_data(ttl=60)
def get_anomalies() -> Dict[str, Any]:
    """
    GET /api/anomalies — cached for 60 seconds.
    Anomaly detection is expensive; no need to rerun on every tab switch.
    """
    return _get("/api/anomalies") or {}


def upload_csv(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """POST /api/ingest — never cached; always live."""
    return _post_file("/api/ingest", file_bytes, filename) or {}
