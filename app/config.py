import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_secret(key: str, default: str = "") -> str:
    """
    Safely retrieves secrets from Streamlit Cloud Secrets (if running in Streamlit Cloud)
    or falls back to environment variables.
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONTRACTS_DIR = DATA_DIR / "contracts"
INVOICES_DIR = DATA_DIR / "invoices"
POLICIES_DIR = DATA_DIR / "policies"
CHROMA_PERSIST_DIR = Path(get_secret("CHROMA_PERSIST_DIR", str(DATA_DIR / "chromadb")))
DB_PATH = Path(get_secret("DB_PATH", str(DATA_DIR / "reconciliation.db")))

# Ensure directories exist
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
INVOICES_DIR.mkdir(parents=True, exist_ok=True)
POLICIES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# LLM & Embedding Settings
LLM_PROVIDER = get_secret("LLM_PROVIDER", "groq").lower()
LLM_API_KEY = get_secret("LLM_API_KEY", "")
LLM_MODEL = get_secret("LLM_MODEL", "openai/gpt-oss-120b")

EMBEDDING_PROVIDER = get_secret("EMBEDDING_PROVIDER", "demo").lower()
EMBEDDING_API_KEY = get_secret("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = get_secret("EMBEDDING_MODEL", "text-embedding-3-small")

# Business Logic Defaults
DEFAULT_TOLERANCE_PERCENT = float(get_secret("DEFAULT_TOLERANCE_PERCENT", "1.0"))
DEFAULT_TOLERANCE_ABSOLUTE = float(get_secret("DEFAULT_TOLERANCE_ABSOLUTE", "50.0"))
DATE_TOLERANCE_DAYS = int(get_secret("DATE_TOLERANCE_DAYS", "3"))

# Operational / ROI Assumptions
MANUAL_MINUTES_PER_INVOICE = 15.0  # Industry standard time to manually check contract & invoice
FINANCE_HOURLY_COST = 45.0  # Blended finance specialist rate ($/hr)
