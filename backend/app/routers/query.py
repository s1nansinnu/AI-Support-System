"""POST /api/query — natural language question → SQL → synthesised answer."""
from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse
from app.services.gemini import answer_question

router = APIRouter(prefix="/api", tags=["Analytics"])


@router.post("/query", response_model=QueryResponse)
def run_query(payload: QueryRequest) -> QueryResponse:
    """
    Accepts a natural language question, translates it to SQLite SQL via
    Google Gemini, executes it, and synthesises a concise answer.

    If GEMINI_API_KEY is not set the response will have status='error'
    and explain that the key is missing.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = answer_question(
        question=payload.question,
        api_key=payload.api_key,
    )
    return QueryResponse(**result)
