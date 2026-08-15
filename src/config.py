"""Shared configuration for the TraceGap synthetic case study."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_PATH = PROJECT_ROOT / "data" / "tracegap.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"

SEED = 20250317
ANALYSIS_YEAR = 2025
SYSTEM_UPDATE_DATE = "2025-07-01"
FINANCE_THRESHOLD = 10_000.0
DIRECTOR_THRESHOLD = 25_000.0
COMPETITIVE_BID_THRESHOLD = 20_000.0
LEGAL_THRESHOLD = 50_000.0
TRAVEL_THRESHOLD_BEFORE = 7_500.0
TRAVEL_THRESHOLD_AFTER = 5_000.0

SEVERITY_WEIGHT = {"Low": 4, "Medium": 8, "High": 14, "Critical": 22}

