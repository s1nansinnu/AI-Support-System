import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ── Gemini ──────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL: str   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# ── Paths ────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
DB_PATH: str   = os.getenv("DB_PATH",  str(BASE_DIR / "tickets.db"))

def resolve_csv_path() -> str:
    """Return the first CSV found among standard candidate locations."""
    env_path = os.getenv("CSV_PATH", "")
    if env_path and Path(env_path).exists():
        return env_path

    candidates = [
        BASE_DIR / "data" / "support_tickets.csv",
        BASE_DIR / "support_tickets.csv",
    ]
    for path in candidates:
        if path.exists():
            return str(path)

    # Fallback: first CSV found in data/ or project root
    data_dir = BASE_DIR / "data"
    if data_dir.exists():
        for f in data_dir.glob("*.csv"):
            return str(f)
    for f in BASE_DIR.glob("*.csv"):
        return str(f)

    return str(BASE_DIR / "data" / "support_tickets.csv")

CSV_PATH: str = resolve_csv_path()

# ── Server ───────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", 8000))
