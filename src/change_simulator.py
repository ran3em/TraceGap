"""Historical impact simulations for proposed business-rule changes."""

from __future__ import annotations

import pandas as pd


def simulate_finance_threshold(requests: pd.DataFrame, current: float, proposed: float) -> dict:
    current_mask = requests.amount > current
    proposed_mask = requests.amount > proposed
    added_mask = proposed_mask & ~current_mask
    removed_mask = current_mask & ~proposed_mask
    affected = requests[added_mask | removed_mask]
    direction = "additional" if proposed < current else "fewer"
    workload = int(added_mask.sum() - removed_mask.sum())
    dept = (
        affected.groupby("department_name", as_index=False)
        .agg(affected_requests=("request_id", "size"), affected_value=("amount", "sum"))
        .sort_values("affected_requests", ascending=False)
    )
    category = (
        affected.groupby("purchase_type", as_index=False)
        .agg(affected_requests=("request_id", "size"), affected_value=("amount", "sum"))
        .sort_values("affected_requests", ascending=False)
    )
    return {
        "rule": "Finance approval threshold",
        "current": current,
        "proposed": proposed,
        "direction": direction,
        "net_workload_change": workload,
        "additional_reviews": int(added_mask.sum()),
        "reviews_removed": int(removed_mask.sum()),
        "affected_pct": float((added_mask | removed_mask).mean() * 100),
        "estimated_hours": round(abs(workload) * 0.22, 1),
        "departments": dept,
        "categories": category,
    }


def simulate_director_threshold(requests: pd.DataFrame, current: float, proposed: float) -> dict:
    result = simulate_finance_threshold(requests, current, proposed)
    result["rule"] = "Director approval threshold"
    result["estimated_hours"] = round(abs(result["net_workload_change"]) * 0.3, 1)
    return result


def simulate_security_scope(requests: pd.DataFrame, include_ai: bool = True, include_equipment: bool = False) -> dict:
    current_mask = requests.purchase_type.eq("Software")
    proposed_mask = current_mask.copy()
    if include_ai:
        proposed_mask |= requests.purchase_type.eq("AI Services")
    if include_equipment:
        proposed_mask |= requests.purchase_type.eq("Equipment")
    added = proposed_mask & ~current_mask
    affected = requests[added]
    return {
        "rule": "Security review scope",
        "current": "Software only",
        "proposed": " + ".join(["Software", *( ["AI Services"] if include_ai else []), *( ["Equipment"] if include_equipment else [])]),
        "direction": "additional",
        "net_workload_change": int(added.sum()),
        "additional_reviews": int(added.sum()),
        "reviews_removed": 0,
        "affected_pct": float(added.mean() * 100),
        "estimated_hours": round(int(added.sum()) * 0.45, 1),
        "departments": affected.groupby("department_name", as_index=False).agg(affected_requests=("request_id", "size"), affected_value=("amount", "sum")).sort_values("affected_requests", ascending=False),
        "categories": affected.groupby("purchase_type", as_index=False).agg(affected_requests=("request_id", "size"), affected_value=("amount", "sum")).sort_values("affected_requests", ascending=False),
    }

