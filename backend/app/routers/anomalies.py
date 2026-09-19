"""GET /api/anomalies — SLA breaches and statistical outlier detection."""
from fastapi import APIRouter

from app.models.schemas import AnomalyResponse
from app.services.anomaly import detect_anomalies

router = APIRouter(prefix="/api", tags=["Anomalies"])


@router.get("/anomalies", response_model=AnomalyResponse)
def get_anomalies() -> AnomalyResponse:
    """
    Scans all tickets and returns:
    - SLA breaches (unresolved High/Critical tickets past time thresholds).
    - Resolution time outliers (IQR, per category).
    - First-response time outliers (IQR, across all tickets).
    """
    result = detect_anomalies()
    return AnomalyResponse(**result)
