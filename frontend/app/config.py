"""Frontend configuration — API URL and UI constants."""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# Backend base URL
API_BASE_URL: str = os.getenv("API_URL", "http://127.0.0.1:8000")

# UI constants
APP_TITLE   = "AI Support Ticket Analytics"
APP_ICON    = "🎫"
REQUEST_TIMEOUT_SECONDS = 30

SAMPLE_QUERIES = [
    "How many tickets are currently open?",
    "Which agent resolved the most tickets?",
    "Show all Critical tickets not resolved within 12 hours.",
    "What is the average customer rating for Technical tickets?",
    "Which category has the longest average resolution time?",
    "List all Escalated Billing tickets.",
]
