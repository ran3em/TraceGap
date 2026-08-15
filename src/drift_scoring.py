"""Explainable 0-100 Process Drift Score."""

from __future__ import annotations

import json

import pandas as pd

from .config import SEVERITY_WEIGHT


FORMULA = (
    "severity-weighted rule violations (max 65) + ordering anomalies (12 each, max 20) "
    "+ rework loops (5 each, max 10) + exceptions (3 each, max 6) + rare-path signal (4); capped at 100"
)


def score_processes(processes: pd.DataFrame, violations: pd.DataFrame) -> pd.DataFrame:
    """Score each process and retain a plain-language contribution breakdown."""

    violation_groups = {key: frame for key, frame in violations.groupby("request_id", sort=False)} if not violations.empty else {}
    records = []
    for row in processes.itertuples(index=False):
        request_violations = violation_groups.get(row.request_id, violations.iloc[0:0])
        violation_points = min(65, sum(SEVERITY_WEIGHT.get(sev, 0) for sev in request_violations.severity.tolist()))
        ordering_points = min(20, 12 * len(json.loads(row.sequence_issues)))
        rework_points = min(10, 5 * int(row.rework_count))
        exception_points = min(6, 3 * int(row.exception_count))
        rare_points = 4 if bool(row.rare_path) else 0
        score = min(100, violation_points + ordering_points + rework_points + exception_points + rare_points)
        records.append({
            "request_id": row.request_id,
            "drift_score": int(score),
            "violation_points": int(violation_points),
            "ordering_points": int(ordering_points),
            "rework_points": int(rework_points),
            "exception_points": int(exception_points),
            "rare_path_points": int(rare_points),
            "violation_count": int(len(request_violations)),
            "critical_violation_count": int((request_violations.severity == "Critical").sum()) if not request_violations.empty else 0,
            "high_violation_count": int((request_violations.severity == "High").sum()) if not request_violations.empty else 0,
            "aligned": bool(len(request_violations) == 0 and not json.loads(row.sequence_issues)),
        })
    return pd.DataFrame(records)


def aggregate_scores(scored_requests: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Create roll-up scores while preserving volume and alignment context."""

    return (
        scored_requests.groupby(group_column, as_index=False)
        .agg(
            average_drift_score=("drift_score", "mean"),
            median_drift_score=("drift_score", "median"),
            request_count=("request_id", "size"),
            alignment_rate=("aligned", "mean"),
            violation_count=("violation_count", "sum"),
        )
        .sort_values("average_drift_score", ascending=False)
    )

