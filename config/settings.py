import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'spendlens.db'}")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

DB_PATH = BASE_DIR / "spendlens.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

DEDUP_CONFIDENCE_AUTO = 0.90
DEDUP_CONFIDENCE_REVIEW = 0.60
DEDUP_DATE_TOLERANCE_DAYS = 1
DEDUP_FUZZY_THRESHOLD = 75
DEDUP_COMERCIO_AUTO_THRESHOLD = 90  # similitud de comercio para fusión automática

SPLIT_RATIO_MIN = 0.20
SPLIT_RATIO_MAX = 0.80
SPLIT_LOOKBACK_DAYS = 7

GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_TOKEN_PATH = BASE_DIR / "token.json"
GMAIL_CREDENTIALS_PATH = BASE_DIR / "credentials.json"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BANK_SENDERS = [
    "alertasynotificaciones@bancolombia.com.co",
    "notificaciones@nequi.com.co",
    "notificaciones@nequi.com",
]
