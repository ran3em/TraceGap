"""End-to-end TraceGap data and analytics pipeline."""

from __future__ import annotations

import argparse

import pandas as pd

from .config import PROCESSED_DIR, RAW_DIR
from .database import build_database, validate_database
from .drift_scoring import score_processes
from .generate_data import generate
from .metrics import calculate_rule_summary, calculate_summary, generate_findings, write_metrics
from .process_engine import path_variants, reconstruct_processes
from .rule_engine import evaluate_all
from .threshold_detection import detect_threshold_patterns


def enrich(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    requests = raw["purchase_requests"].copy()
    requests["request_date"] = pd.to_datetime(requests.request_date)
    departments = raw["departments"]
    vendors = raw["vendors"].rename(columns={"risk_level": "vendor_risk"})
    employees = raw["employees"][["employee_id", "employee_name", "location"]].rename(columns={"location": "employee_location"})
    return (
        requests
        .merge(departments, on="department_id", how="left")
        .merge(vendors, on="vendor_id", how="left")
        .merge(employees, on="employee_id", how="left")
    )


def run(request_count: int = 8_500) -> dict:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = generate(request_count=request_count)
    requests = enrich(raw)
    events = raw["event_log"].copy()
    events["event_timestamp"] = pd.to_datetime(events.event_timestamp)
    employees = raw["employees"]

    processes = reconstruct_processes(requests, events)
    violations = evaluate_all(requests, events, employees)
    scores = score_processes(processes, violations)
    processes = processes.merge(scores, on="request_id", validate="one_to_one")
    variants = path_variants(processes, requests)
    patterns = detect_threshold_patterns(requests)
    rule_summary = calculate_rule_summary(requests, violations)
    summary = calculate_summary(requests, processes, violations)
    findings = generate_findings(requests, processes, violations, patterns)

    outputs = {
        "requests_enriched": requests,
        "process_instances": processes,
        "rule_violations": violations,
        "path_variants": variants,
        "threshold_patterns": patterns,
        "rule_summary": rule_summary,
    }
    for name, frame in outputs.items():
        frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    write_metrics(PROCESSED_DIR / "metrics.json", summary, findings)
    build_database()
    counts = validate_database()
    return {"summary": summary, "findings": findings, "table_counts": counts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full TraceGap pipeline")
    parser.add_argument("--requests", type=int, default=8_500)
    args = parser.parse_args()
    result = run(args.requests)
    print("TraceGap pipeline completed")
    for key, value in result["summary"].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
