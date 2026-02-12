"""
Configuration management for the Address Geocoding System.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Google AI (Gemini) Configuration
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")

# Google Sheets Configuration
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "address_registry")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")

# Quality Thresholds
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))

# Cache Settings
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TYPE = os.getenv("CACHE_TYPE", "sqlite")  # sqlite or memory

# Check for writable directory for cache
default_db = ".cache.db"
try:
    # Try to create/open the file to check writability
    with open(default_db, "a"):
        pass
    CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", default_db)
except (PermissionError, OSError):
    # Fallback to /tmp if root is not writable (common on cloud platforms)
    CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "/tmp/geocoding_cache.db")

CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "10000"))

# Rate Limiting
MAX_API_CALLS_PER_DAY = int(os.getenv("MAX_API_CALLS_PER_DAY", "1000"))
WARNING_THRESHOLD = int(os.getenv("WARNING_THRESHOLD", "800"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "geocoding.log")

# Data Files
GOLDEN_MAPPINGS_FILE = PROJECT_ROOT / "data" / "golden_mappings.json"

# Validation
def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not GOOGLE_MAPS_API_KEY:
        errors.append("GOOGLE_MAPS_API_KEY is not set in .env file")
    
    if not GOOGLE_SHEETS_ID:
        errors.append("GOOGLE_SHEETS_ID is not set in .env file")
    
    if not Path(SERVICE_ACCOUNT_FILE).exists():
        errors.append(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    
    if errors:
        return False, errors
    
    return True, []

def get_config_summary():
    """Get a summary of current configuration (for debugging)."""
    return {
        "google_maps_configured": bool(GOOGLE_MAPS_API_KEY),
        "google_sheets_configured": bool(GOOGLE_SHEETS_ID),
        "service_account_exists": Path(SERVICE_ACCOUNT_FILE).exists(),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "cache_enabled": ENABLE_CACHE,
        "cache_type": CACHE_TYPE,
        "max_api_calls_per_day": MAX_API_CALLS_PER_DAY,
    }
