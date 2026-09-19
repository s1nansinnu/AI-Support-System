"""
Gemini LLM service.

Pipeline:
  User question
    → generate_sql()   (Gemini: NL → SQLite SELECT)
    → SQL safety gate  (connection.is_safe_sql)
    → run_query()      (SQLite execution)
    → synthesize()     (Gemini: rows → natural language answer)
"""
import re
from typing import Any, Dict, Optional

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.database.connection import is_safe_sql, run_query
from app.database.queries import TABLE_SCHEMA_CONTEXT

# ── Gemini client initialisation ─────────────────────────────────────────────

class GeminiClient:
    """
    Thin wrapper around the google-genai (or google-generativeai) SDK.
    Raises ValueError immediately if the API key is absent.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._key   = (api_key or GEMINI_API_KEY).strip()
        self._model = GEMINI_MODEL
        self._client = None
        self._sdk   = None

        if self._key:
            self._init_sdk()

    # ── initialisation ────────────────────────────────────────────────────────
    def _init_sdk(self) -> None:
        try:
            from google import genai
            self._client = genai.Client(api_key=self._key)
            self._sdk    = "genai"
        except Exception:
            try:
                import google.generativeai as legacy
                legacy.configure(api_key=self._key)
                self._client = legacy.GenerativeModel(self._model)
                self._sdk    = "legacy"
            except Exception as exc:
                self._client = None

    # ── public helpers ────────────────────────────────────────────────────────
    @property
    def available(self) -> bool:
        return bool(self._key and self._client)

    def generate(self, prompt: str) -> str:
        if not self._key:
            raise ValueError(
                "Gemini API key is not available. "
                "Please set GEMINI_API_KEY in backend/.env or enter it in the UI."
            )
        if not self._client:
            self._init_sdk()
            if not self._client:
                raise ValueError(
                    "Failed to initialise Gemini client. "
                    "Verify your GEMINI_API_KEY is correct."
                )

        if self._sdk == "genai":
            resp = self._client.models.generate_content(
                model=self._model, contents=prompt
            )
        else:
            resp = self._client.generate_content(prompt)

        return resp.text.strip()


# ── SQL helpers ───────────────────────────────────────────────────────────────

def _strip_code_fences(text: str) -> str:
    """Remove ```sql ... ``` or ``` ... ``` wrappers from generated SQL."""
    match = re.search(r"```(?:sql)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip().rstrip(";").strip("`")


# ── Public service function ───────────────────────────────────────────────────

def answer_question(question: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Full NL-to-SQL-to-answer pipeline.

    Returns a dict with keys:
      question, sql_query, columns, results, row_count, answer, status
    """
    client = GeminiClient(api_key=api_key)

    # ── Guard: no API key ─────────────────────────────────────────────────────
    if not client.available:
        return {
            "question":  question,
            "sql_query": None,
            "columns":   [],
            "results":   [],
            "row_count": 0,
            "answer": (
                "Gemini API key is not available. "
                "Please provide a GEMINI_API_KEY to enable AI query answering."
            ),
            "status": "error",
        }

    # ── Stage 1: Generate SQL ─────────────────────────────────────────────────
    sql_prompt = f"""You are an expert SQLite query writer for a Customer Support Analytics system.

{TABLE_SCHEMA_CONTEXT}

RULES:
- Return ONLY the raw SQL query — no markdown, no explanation.
- Use only SELECT or WITH statements.
- Column names must match exactly: ticket_id, created_at, category, priority, status,
  resp_time_hrs, resol_time_hrs, agent_id, cust_rating, issue_summary.
- Always add a meaningful alias to aggregated columns.
- Add LIMIT 500 unless the user explicitly asks for all records.

User Question: {question}
SQLite Query:"""

    try:
        raw_sql  = client.generate(sql_prompt)
        sql_query = _strip_code_fences(raw_sql)
    except Exception as exc:
        return {
            "question": question, "sql_query": None,
            "columns": [], "results": [], "row_count": 0,
            "answer": f"SQL generation failed: {exc}", "status": "error",
        }

    # ── Stage 2: Validate & Execute SQL ──────────────────────────────────────
    ok, reason = is_safe_sql(sql_query)
    if not ok:
        return {
            "question": question, "sql_query": sql_query,
            "columns": [], "results": [], "row_count": 0,
            "answer": f"Generated SQL failed safety check: {reason}", "status": "error",
        }

    try:
        results, columns = run_query(sql_query)
    except Exception as exc:
        return {
            "question": question, "sql_query": sql_query,
            "columns": [], "results": [], "row_count": 0,
            "answer": f"SQL execution error: {exc}", "status": "error",
        }

    # ── Stage 3: Synthesise natural-language answer ──────────────────────────
    synth_prompt = f"""You are a concise Customer Support Analytics assistant.

User Question: {question}
SQL Executed: {sql_query}
Result Row Count: {len(results)}
Sample Results (up to 25 rows): {results[:25]}

Write a direct, professional 1–3 sentence answer using the exact numbers from the results.
If the result is empty, clearly state that no records matched.
"""
    try:
        answer = client.generate(synth_prompt)
    except Exception as exc:
        answer = f"Found {len(results)} record(s). (Synthesis error: {exc})"

    return {
        "question":  question,
        "sql_query": sql_query,
        "columns":   columns,
        "results":   results,
        "row_count": len(results),
        "answer":    answer,
        "status":    "success",
    }
