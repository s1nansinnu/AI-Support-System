"""POST /api/ingest — upload and reload a CSV dataset."""
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config import CSV_PATH
from app.models.schemas import IngestResponse
from app.services.ingestion import ingest_csv

router = APIRouter(prefix="/api", tags=["Data Ingestion"])


@router.post("/ingest", response_model=IngestResponse)
async def upload_and_ingest(file: UploadFile = File(...)) -> IngestResponse:
    """
    Accepts a CSV upload, saves it to the data directory,
    and ingests it into SQLite (replacing any existing data).
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    dest = Path(CSV_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)

    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        stats = ingest_csv(str(dest))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Ingestion failed: {exc}")

    return IngestResponse(
        message="Dataset uploaded and ingested successfully.",
        **stats,
    )
