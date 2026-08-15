"""Indicator-based detection of potential approval-threshold avoidance."""

from __future__ import annotations

import pandas as pd

from .config import FINANCE_THRESHOLD


DISCLAIMER = "Pattern requires human review and does not establish intentional wrongdoing."


def detect_threshold_patterns(
    requests: pd.DataFrame,
    threshold: float = FINANCE_THRESHOLD,
    lower_ratio: float = 0.88,
    window_days: int = 21,
    minimum_count: int = 3,
) -> pd.DataFrame:
    """Flag near-threshold clusters for the same employee and vendor.

    Each request must fall below, but close to, the threshold; the rolling
    cluster's combined value must exceed it. Results are review indicators only.
    """

    candidates = requests[
        (requests.amount >= threshold * lower_ratio) & (requests.amount < threshold)
    ].copy()
    candidates["request_date"] = pd.to_datetime(candidates.request_date)
    records: list[dict] = []
    seen: set[tuple[str, ...]] = set()
    for (employee_id, vendor_id), group in candidates.groupby(["employee_id", "vendor_id"]):
        group = group.sort_values("request_date")
        for _, start in group.iterrows():
            end_date = start.request_date + pd.Timedelta(days=window_days)
            window = group[(group.request_date >= start.request_date) & (group.request_date <= end_date)]
            if len(window) < minimum_count or window.amount.sum() <= threshold:
                continue
            ids = tuple(sorted(window.request_id.tolist()))
            if ids in seen:
                continue
            seen.add(ids)
            records.append({
                "pattern_id": f"PAT-{len(records) + 1:04d}",
                "employee_id": employee_id,
                "department_name": window.department_name.iloc[0],
                "vendor_id": vendor_id,
                "vendor_name": window.vendor_name.iloc[0],
                "request_ids": ", ".join(ids),
                "transaction_count": int(len(window)),
                "first_date": window.request_date.min().date().isoformat(),
                "last_date": window.request_date.max().date().isoformat(),
                "combined_value": round(float(window.amount.sum()), 2),
                "threshold": float(threshold),
                "reason_flagged": f"{len(window)} purchases between {lower_ratio:.0%} and 100% of the Finance threshold within {window_days} days",
                "review_status": "Unreviewed indicator",
            })
    return pd.DataFrame(records)

