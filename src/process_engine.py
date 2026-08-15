"""Workflow reconstruction and conformance utilities."""

from __future__ import annotations

import json

import pandas as pd

from .rule_engine import expected_steps


DISPLAY_NAMES = {
    "Request Submitted": "Submitted",
    "Request Resubmitted": "Resubmitted",
    "Manager Approval": "Manager",
    "Director Approval": "Director",
    "Procurement Review": "Procurement",
    "Finance Approval": "Finance",
    "Security Review": "Security",
    "Legal Review": "Legal",
    "Vendor Validation": "Vendor Validation",
    "Competitive Bid Confirmed": "Bid Confirmed",
    "Purchase Order Created": "PO Created",
    "Payment Authorized": "Payment",
    "Returned for Revision": "Returned",
    "Exception Approved": "Exception",
    "Rejected": "Rejected",
}


def _path(activities: list[str]) -> str:
    return " → ".join(DISPLAY_NAMES.get(a, a) for a in activities)


def sequence_issues(activities: list[str]) -> list[str]:
    """Detect explainable ordering anomalies in an observed path."""

    issues: list[str] = []
    index = {name: i for i, name in enumerate(activities)}
    if "Payment Authorized" in index and "Purchase Order Created" in index:
        if index["Payment Authorized"] < index["Purchase Order Created"]:
            issues.append("Payment before purchase order")
    if "Finance Approval" in index and "Manager Approval" in index:
        if index["Finance Approval"] < index["Manager Approval"]:
            issues.append("Finance before manager approval")
    if "Purchase Order Created" in index:
        for control in ("Finance Approval", "Director Approval", "Procurement Review"):
            if control in index and index[control] > index["Purchase Order Created"]:
                issues.append(f"{control} after purchase order")
    return issues


def reconstruct_processes(requests: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Collapse event-level data into one auditable process instance per request."""

    event_groups = {key: frame.sort_values("event_timestamp") for key, frame in events.groupby("request_id", sort=False)}
    records = []
    for _, row in requests.iterrows():
        request_events = event_groups.get(row.request_id, events.iloc[0:0])
        activities = request_events.activity.tolist()
        expected = expected_steps(row)
        actual_set = set(activities)
        missing = [step for step in expected if step not in actual_set]
        extras = [step for step in dict.fromkeys(activities) if step not in set(expected)]
        issues = sequence_issues(activities)
        started = pd.to_datetime(request_events.event_timestamp).min() if not request_events.empty else pd.NaT
        ended = pd.to_datetime(request_events.event_timestamp).max() if not request_events.empty else pd.NaT
        cycle_hours = (ended - started).total_seconds() / 3600 if pd.notna(started) and pd.notna(ended) else 0
        records.append({
            "request_id": row.request_id,
            "expected_path": _path(expected),
            "observed_path": _path(activities),
            "expected_steps": json.dumps(expected),
            "actual_steps": json.dumps(activities),
            "missing_steps": json.dumps(missing),
            "extra_steps": json.dumps(extras),
            "sequence_issues": json.dumps(issues),
            "step_count": len(activities),
            "expected_step_count": len(expected),
            "rework_count": activities.count("Returned for Revision"),
            "exception_count": activities.count("Exception Approved"),
            "cycle_time_hours": round(cycle_hours, 2),
            "has_unusual_sequence": bool(issues),
        })
    result = pd.DataFrame(records)
    counts = result.observed_path.value_counts()
    result["variant_frequency"] = result.observed_path.map(counts).astype(int)
    result["rare_path"] = result.variant_frequency <= max(3, int(len(result) * 0.001))
    return result


def path_variants(processes: pd.DataFrame, requests: pd.DataFrame) -> pd.DataFrame:
    """Summarize path variants and their operational characteristics."""

    enriched = processes.merge(requests[["request_id", "amount", "department_name", "purchase_type"]], on="request_id")
    summary = (
        enriched.groupby("observed_path", as_index=False)
        .agg(
            request_count=("request_id", "size"),
            total_value=("amount", "sum"),
            average_cycle_hours=("cycle_time_hours", "mean"),
            departments=("department_name", "nunique"),
            categories=("purchase_type", "nunique"),
        )
        .sort_values("request_count", ascending=False)
    )
    summary["share_pct"] = summary.request_count / summary.request_count.sum() * 100
    return summary

