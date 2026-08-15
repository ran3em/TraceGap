"""Transparent business-rule evaluation for Purchase-to-Pay transactions.

The engine translates policy statements into reusable predicates. It does not
learn from outcomes: every expectation and violation is explainable by a named
rule and evidence from the transaction or event log.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

import pandas as pd

from .config import (
    COMPETITIVE_BID_THRESHOLD,
    DIRECTOR_THRESHOLD,
    FINANCE_THRESHOLD,
    LEGAL_THRESHOLD,
    SYSTEM_UPDATE_DATE,
    TRAVEL_THRESHOLD_AFTER,
    TRAVEL_THRESHOLD_BEFORE,
)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    description: str
    condition: str
    required_step: str
    severity: str
    policy_owner: str
    applies: Callable[[pd.Series], bool]


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _travel_finance_applies(row: pd.Series) -> bool:
    threshold = (
        TRAVEL_THRESHOLD_AFTER
        if pd.Timestamp(row.request_date) >= pd.Timestamp(SYSTEM_UPDATE_DATE)
        else TRAVEL_THRESHOLD_BEFORE
    )
    return row.purchase_type == "Travel" and float(row.amount) > threshold


def rule_catalog() -> list[Rule]:
    """Return the governed rule catalog used by generation and evaluation."""

    return [
        Rule("RULE-001", "Manager approval", "Purchases of $1,000 or more require manager approval.", "amount >= 1000", "Manager Approval", "Low", "Finance Operations", lambda r: float(r.amount) >= 1_000),
        Rule("RULE-002", "Finance approval", "Purchases above $10,000 require Finance approval.", "amount > 10000", "Finance Approval", "High", "CFO", lambda r: float(r.amount) > FINANCE_THRESHOLD),
        Rule("RULE-003", "Director approval", "Purchases above $25,000 require Director approval.", "amount > 25000", "Director Approval", "High", "CFO", lambda r: float(r.amount) > DIRECTOR_THRESHOLD),
        Rule("RULE-004", "Software security review", "Software and AI service purchases require Security review.", "purchase_type IN ('Software','AI Services')", "Security Review", "Critical", "Information Security", lambda r: r.purchase_type in {"Software", "AI Services"}),
        Rule("RULE-005", "High-value contract review", "Contracts above $50,000 require Legal review.", "contract_required AND amount > 50000", "Legal Review", "Critical", "Legal", lambda r: _truthy(r.contract_required) and float(r.amount) > LEGAL_THRESHOLD),
        Rule("RULE-006", "Unapproved vendor review", "Unapproved vendors require Procurement review.", "approved_vendor = false", "Procurement Review", "High", "VP Procurement", lambda r: not _truthy(r.approved_vendor)),
        Rule("RULE-007", "Competitive bid evidence", "Purchases above $20,000 require competitive bids or an approved exception.", "amount > 20000", "Competitive Bid Confirmed", "High", "VP Procurement", lambda r: float(r.amount) > COMPETITIVE_BID_THRESHOLD),
        Rule("RULE-008", "Approval authorization", "Approvers may not authorize purchases above their approval limit.", "approval amount <= performer approval_limit", "AUTHORIZED_APPROVER", "Critical", "Internal Audit", lambda r: float(r.amount) >= 1_000),
        Rule("RULE-009", "Segregation of duties", "The requester may not approve their own purchase.", "approver != requester", "NO_SELF_APPROVAL", "Critical", "Internal Audit", lambda r: float(r.amount) >= 1_000),
        Rule("RULE-010", "Vendor validation", "Unapproved or high-risk vendors require Vendor Validation.", "approved_vendor = false OR vendor_risk = 'High'", "Vendor Validation", "High", "Vendor Management", lambda r: (not _truthy(r.approved_vendor)) or r.vendor_risk == "High"),
        Rule("RULE-011", "Documented exception", "Every approved exception requires supporting documentation.", "exception used", "DOCUMENTED_EXCEPTION", "High", "Internal Audit", lambda r: int(r.get("exception_count", 0)) > 0),
        Rule("RULE-012", "PO before payment", "A purchase order must be created before payment is authorized.", "PO timestamp < payment timestamp", "PO_BEFORE_PAYMENT", "Critical", "Finance Operations", lambda r: str(r.final_status) == "Paid"),
        Rule("RULE-013", "International vendor legal review", "High-risk international vendors require Legal review.", "country != 'United States' AND vendor_risk = 'High'", "Legal Review", "High", "Legal", lambda r: r.country != "United States" and r.vendor_risk == "High"),
        Rule("RULE-014", "High-risk security review", "All high-risk technology vendors require Security review.", "vendor_risk = 'High' AND technology purchase", "Security Review", "Critical", "Information Security", lambda r: r.vendor_risk == "High" and r.purchase_type in {"Software", "AI Services", "Equipment"}),
        Rule("RULE-015", "Contractor procurement review", "Contractor engagements require Procurement review.", "purchase_type = 'Contractor'", "Procurement Review", "High", "VP Procurement", lambda r: r.purchase_type == "Contractor"),
        Rule("RULE-016", "Travel finance threshold", "Travel requires Finance approval above $7,500 before July and $5,000 after the system update.", "travel threshold by effective date", "Finance Approval", "Medium", "Finance Operations", _travel_finance_applies),
        Rule("RULE-017", "Urgent purchase rationale", "Urgent purchases require a documented exception rationale.", "urgency = 'Urgent'", "DOCUMENTED_URGENCY", "Medium", "Finance Operations", lambda r: r.urgency == "Urgent"),
        Rule("RULE-018", "Equipment dual control", "Equipment purchases above $30,000 require both Finance and Procurement review.", "purchase_type = 'Equipment' AND amount > 30000", "DUAL_CONTROL", "High", "Finance Operations", lambda r: r.purchase_type == "Equipment" and float(r.amount) > 30_000),
    ]


def expected_steps(row: pd.Series) -> list[str]:
    """Build the expected happy path for one enriched purchase request."""

    steps = ["Request Submitted"]
    required = {rule.required_step for rule in rule_catalog() if rule.applies(row)}
    canonical = [
        "Manager Approval",
        "Director Approval",
        "Vendor Validation",
        "Security Review",
        "Legal Review",
        "Procurement Review",
        "Competitive Bid Confirmed",
        "Finance Approval",
    ]
    steps.extend(step for step in canonical if step in required and step not in {
        "AUTHORIZED_APPROVER", "NO_SELF_APPROVAL", "DOCUMENTED_EXCEPTION",
        "PO_BEFORE_PAYMENT", "DOCUMENTED_URGENCY", "DUAL_CONTROL",
    })
    if str(row.final_status) == "Paid":
        steps.extend(["Purchase Order Created", "Payment Authorized"])
    elif str(row.final_status) == "Rejected":
        steps.append("Rejected")
    return steps


def _violation(
    row: pd.Series,
    rule: Rule,
    violation_type: str,
    evidence: str,
) -> dict:
    return {
        "request_id": row.request_id,
        "rule_id": rule.rule_id,
        "rule_name": rule.name,
        "required_step": rule.required_step,
        "severity": rule.severity,
        "violation_type": violation_type,
        "evidence": evidence,
        "amount_at_risk": round(float(row.amount), 2),
    }


def evaluate_request(row: pd.Series, events: pd.DataFrame, employees: pd.DataFrame) -> list[dict]:
    """Evaluate one transaction against all applicable rules."""

    actual_steps = events.sort_values("event_timestamp").activity.tolist()
    actual_set = set(actual_steps)
    employee_limits = employees.set_index("employee_id")["approval_limit"].to_dict()
    violations: list[dict] = []

    for rule in rule_catalog():
        if not rule.applies(row):
            continue

        if rule.required_step in {
            "Manager Approval", "Finance Approval", "Director Approval",
            "Security Review", "Legal Review", "Procurement Review",
            "Vendor Validation", "Competitive Bid Confirmed",
        }:
            exception_covers_bid = rule.rule_id == "RULE-007" and "Exception Approved" in actual_set
            if rule.required_step not in actual_set and not exception_covers_bid:
                violations.append(_violation(row, rule, "Missing required step", f"{rule.required_step} was required but not observed"))

        elif rule.rule_id == "RULE-008":
            approval_events = events[events.activity.isin(["Manager Approval", "Director Approval"])]
            for event in approval_events.itertuples():
                limit = float(employee_limits.get(event.performed_by, 0))
                if float(row.amount) > limit:
                    violations.append(_violation(row, rule, "Authorization limit exceeded", f"{event.performed_by} approved ${row.amount:,.0f} with a ${limit:,.0f} limit"))
                    break

        elif rule.rule_id == "RULE-009":
            approval_events = events[events.activity.str.contains("Approval", na=False)]
            if row.employee_id in set(approval_events.performed_by):
                violations.append(_violation(row, rule, "Self-approval", "Requester appears as an approver"))

        elif rule.rule_id == "RULE-011":
            if "Exception Approved" in actual_set and not _truthy(row.exception_documented):
                violations.append(_violation(row, rule, "Undocumented exception", "Exception approval exists without supporting documentation"))

        elif rule.rule_id == "RULE-012":
            po = events.loc[events.activity == "Purchase Order Created", "event_timestamp"]
            payment = events.loc[events.activity == "Payment Authorized", "event_timestamp"]
            if payment.empty or po.empty or pd.Timestamp(payment.min()) < pd.Timestamp(po.min()):
                violations.append(_violation(row, rule, "Incorrect sequence", "Payment was authorized before a purchase order was created"))

        elif rule.rule_id == "RULE-017" and not _truthy(row.urgency_documented):
            violations.append(_violation(row, rule, "Undocumented urgency", "Urgent routing was used without rationale"))

        elif rule.rule_id == "RULE-018":
            if not {"Finance Approval", "Procurement Review"}.issubset(actual_set):
                violations.append(_violation(row, rule, "Dual control incomplete", "Both Finance and Procurement review were required"))

    return violations


def evaluate_all(requests: pd.DataFrame, events: pd.DataFrame, employees: pd.DataFrame) -> pd.DataFrame:
    """Evaluate all requests and return one row per violation."""

    grouped = {key: frame for key, frame in events.groupby("request_id", sort=False)}
    records: list[dict] = []
    for _, row in requests.iterrows():
        records.extend(evaluate_request(row, grouped.get(row.request_id, events.iloc[0:0]), employees))
    columns = ["violation_id", "request_id", "rule_id", "rule_name", "required_step", "severity", "violation_type", "evidence", "amount_at_risk"]
    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(columns=columns)
    result.insert(0, "violation_id", [f"VIO-{i:06d}" for i in range(1, len(result) + 1)])
    return result[columns]


def catalog_frame() -> pd.DataFrame:
    """Serialize rule metadata without Python predicates."""

    rows = []
    for rule in rule_catalog():
        rows.append({
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "rule_description": rule.description,
            "condition": rule.condition,
            "required_step": rule.required_step,
            "severity": rule.severity,
            "effective_date": date(2025, 1, 1).isoformat(),
            "policy_owner": rule.policy_owner,
        })
    return pd.DataFrame(rows)


def applicable_rule_ids(row: pd.Series) -> list[str]:
    return [rule.rule_id for rule in rule_catalog() if rule.applies(row)]


def applicable_steps(row: pd.Series) -> Iterable[str]:
    return (rule.required_step for rule in rule_catalog() if rule.applies(row))
