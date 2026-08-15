"""SQLite build and validation helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .config import DB_PATH, PROCESSED_DIR, RAW_DIR, SCHEMA_PATH


def build_database(db_path: Path = DB_PATH) -> Path:
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        sources = {
            "departments": RAW_DIR / "departments.csv",
            "employees": RAW_DIR / "employees.csv",
            "vendors": RAW_DIR / "vendors.csv",
            "business_rules": RAW_DIR / "business_rules.csv",
            "purchase_requests": RAW_DIR / "purchase_requests.csv",
            "workflow_events": RAW_DIR / "event_log.csv",
            "rule_violations": PROCESSED_DIR / "rule_violations.csv",
            "process_instances": PROCESSED_DIR / "process_instances.csv",
            "threshold_patterns": PROCESSED_DIR / "threshold_patterns.csv",
        }
        for table, source in sources.items():
            frame = pd.read_csv(source)
            frame.to_sql(table, connection, if_exists="append", index=False)
        connection.execute("PRAGMA optimize")
        connection.commit()
    return db_path


def validate_database(db_path: Path = DB_PATH) -> dict[str, int]:
    expected_tables = [
        "departments", "employees", "vendors", "business_rules", "purchase_requests",
        "workflow_events", "rule_violations", "process_instances", "threshold_patterns",
    ]
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"Foreign-key violations found: {violations[:5]}")
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in expected_tables}
    return counts

