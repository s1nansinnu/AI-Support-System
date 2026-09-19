"""GET /health — system status, DB stats, Gemini readiness."""
from fastapi import APIRouter

from app.config import GEMINI_MODEL, GEMINI_API_KEY
from app.database.connection import get_stats
from app.models.schemas import HealthResponse, DBHealth, GeminiHealth

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Returns:
    - Database status and ticket counts.
    - Whether a Gemini API key is configured.
    """
    stats = get_stats()
    gemini_ready = bool(GEMINI_API_KEY)

    return HealthResponse(
        status="healthy",
        service="AI Support Ticket Analytics API",
        database=DBHealth(
            status="connected",
            total_tickets=stats.get("total_tickets", 0),
            status_counts=stats.get("status_counts", {}),
        ),
        gemini_api=GeminiHealth(
            configured=gemini_ready,
            model=GEMINI_MODEL,
            status="ready" if gemini_ready else "missing_api_key",
        ),
    )
