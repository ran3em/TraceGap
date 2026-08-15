"""Portfolio metrics and evidence-backed finding generation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .rule_engine import rule_catalog


def calculate_rule_summary(requests: pd.DataFrame, violations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule in rule_catalog():
        applicable = requests[requests.apply(rule.applies, axis=1)]
        rule_violations = violations[violations.rule_id == rule.rule_id]
        violated_requests = rule_violations.request_id.nunique()
        applicable_count = len(applicable)
        rows.append({
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "rule_description": rule.description,
            "required_step": rule.required_step,
            "severity": rule.severity,
            "policy_owner": rule.policy_owner,
            "applicable_transactions": applicable_count,
            "violations": violated_requests,
            "compliance_pct": round((1 - violated_requests / applicable_count) * 100, 2) if applicable_count else 100.0,
            "affected_value": round(float(rule_violations.amount_at_risk.sum()), 2),
        })
    return pd.DataFrame(rows)


def calculate_summary(requests: pd.DataFrame, processes: pd.DataFrame, violations: pd.DataFrame) -> dict:
    total = len(processes)
    critical_requests = violations.loc[violations.severity == "Critical", "request_id"].nunique()
    high_requests = violations.loc[violations.severity == "High", "request_id"].nunique()
    return {
        "purchase_requests": total,
        "workflow_events": int(processes.step_count.sum()),
        "process_alignment_rate": round(float(processes.aligned.mean() * 100), 2),
        "critical_rule_compliance": round(float((1 - critical_requests / total) * 100), 2),
        "high_severity_violation_rate": round(float(high_requests / total * 100), 2),
        "exception_rate": round(float((processes.exception_count > 0).mean() * 100), 2),
        "rework_rate": round(float((processes.rework_count > 0).mean() * 100), 2),
        "average_process_drift_score": round(float(processes.drift_score.mean()), 2),
        "median_approval_cycle_time_hours": round(float(processes.cycle_time_hours.median()), 2),
        "process_step_completion_rate": round(float((processes.step_count / processes.expected_step_count.clip(lower=1)).clip(upper=1).mean() * 100), 2),
        "total_violations": int(len(violations)),
        "critical_violations": int((violations.severity == "Critical").sum()),
        "high_violations": int((violations.severity == "High").sum()),
    }


def _rate(ids: pd.Series, universe: pd.DataFrame) -> float:
    denominator = len(universe)
    return float(ids.nunique() / denominator * 100) if denominator else 0.0


def generate_findings(
    requests: pd.DataFrame,
    processes: pd.DataFrame,
    violations: pd.DataFrame,
    patterns: pd.DataFrame,
) -> list[dict]:
    """Calculate narrative findings from the generated data—not preset text."""

    joined = requests.merge(processes[["request_id", "drift_score", "aligned", "exception_count", "rework_count"]], on="request_id")
    security = violations[violations.rule_id.isin(["RULE-004", "RULE-014"])]
    eng_requests = requests[requests.department_name == "Engineering"]
    eng_security = security[security.request_id.isin(eng_requests.request_id)].request_id.nunique()
    total_security = security.request_id.nunique()
    eng_volume_share = len(eng_requests) / len(requests) * 100
    eng_violation_share = eng_security / total_security * 100 if total_security else 0

    vendor_rule = violations[violations.rule_id == "RULE-010"]
    before = requests[requests.system_period == "Before update"]
    after = requests[requests.system_period == "After update"]
    before_vendor_applicable = before[(~before.approved_vendor) | (before.vendor_risk == "High")]
    after_vendor_applicable = after[(~after.approved_vendor) | (after.vendor_risk == "High")]
    before_vendor_rate = _rate(vendor_rule[vendor_rule.request_id.isin(before_vendor_applicable.request_id)].request_id, before_vendor_applicable)
    after_vendor_rate = _rate(vendor_rule[vendor_rule.request_id.isin(after_vendor_applicable.request_id)].request_id, after_vendor_applicable)

    procurement = violations[violations.rule_id.isin(["RULE-006", "RULE-015", "RULE-018"])]
    before_urgent = before[before.urgency == "Urgent"]
    after_urgent = after[after.urgency == "Urgent"]
    before_urgent_rate = _rate(procurement[procurement.request_id.isin(before_urgent.request_id)].request_id, before_urgent)
    after_urgent_rate = _rate(procurement[procurement.request_id.isin(after_urgent.request_id)].request_id, after_urgent)

    post_travel = after[(after.purchase_type == "Travel") & after.amount.between(5_000, 7_500, inclusive="right")]
    finance = violations[violations.rule_id.isin(["RULE-002", "RULE-016"])]
    austin = post_travel[post_travel.employee_location == "Austin"]
    non_austin = post_travel[post_travel.employee_location != "Austin"]
    austin_rate = _rate(finance[finance.request_id.isin(austin.request_id)].request_id, austin)
    other_rate = _rate(finance[finance.request_id.isin(non_austin.request_id)].request_id, non_austin)

    marketing = joined[joined.department_name == "Marketing"]
    marketing_exception = (marketing.exception_count > 0).mean() * 100 if len(marketing) else 0
    overall_exception = (joined.exception_count > 0).mean() * 100

    self_approval = violations[violations.rule_id == "RULE-009"]
    revenue_ids = requests[requests.business_unit == "Revenue"].request_id
    revenue_self = self_approval[self_approval.request_id.isin(revenue_ids)].request_id.nunique()
    self_total = self_approval.request_id.nunique()

    findings = [
        {
            "finding_id": "FND-01",
            "title": "Engineering carries disproportionate Security-review drift",
            "evidence": f"Engineering represents {eng_volume_share:.1f}% of purchase volume but {eng_violation_share:.1f}% of Security-review violations ({eng_security:,} of {total_security:,}).",
            "root_cause_hypothesis": "Technology purchases use team-specific intake paths that do not consistently invoke the central Security gate.",
            "recommendation": "Move Security eligibility evaluation to submission time and block PO creation when a required review is absent.",
            "requirement": "FR-06",
            "kpi": "Security-review compliance by department and category",
        },
        {
            "finding_id": "FND-02",
            "title": "The July update improved Vendor Validation",
            "evidence": f"Applicable Vendor Validation violations fell from {before_vendor_rate:.1f}% before the update to {after_vendor_rate:.1f}% after it, a decrease of {before_vendor_rate-after_vendor_rate:.1f} points.",
            "root_cause_hypothesis": "NovaProcure's enforced vendor gate reduced a control gap that had been optional in the legacy workflow.",
            "recommendation": "Retain the vendor gate and accelerate retirement of remaining legacy routing.",
            "requirement": "FR-11",
            "kpi": "Vendor Validation violation rate by source system",
        },
        {
            "finding_id": "FND-03",
            "title": "Urgent routing introduced a Procurement side effect",
            "evidence": f"Procurement-related violation incidence among urgent requests changed from {before_urgent_rate:.1f}% before the update to {after_urgent_rate:.1f}% after it.",
            "root_cause_hypothesis": "The new fast-track branch prioritizes cycle time but does not always rejoin the mandatory Procurement gate.",
            "recommendation": "Add a non-bypassable Procurement eligibility check to urgent routing and regression-test the branch.",
            "requirement": "FR-12",
            "kpi": "Urgent-request Procurement compliance",
        },
        {
            "finding_id": "FND-04",
            "title": "Austin shows a legacy travel-threshold adoption gap",
            "evidence": f"After July, travel requests between $5,000 and $7,500 had a {austin_rate:.1f}% Finance-rule violation rate in Austin versus {other_rate:.1f}% elsewhere.",
            "root_cause_hypothesis": "A material share of Austin traffic remains on ProcureFlow Classic, which still applies the former $7,500 threshold.",
            "recommendation": "Migrate Austin routing and add an effective-date configuration check to deployment validation.",
            "requirement": "FR-13",
            "kpi": "Post-change compliance by office and source system",
        },
        {
            "finding_id": "FND-05",
            "title": "Marketing uses exceptions at an elevated rate",
            "evidence": f"Marketing's exception rate is {marketing_exception:.1f}% compared with {overall_exception:.1f}% company-wide.",
            "root_cause_hypothesis": "Late campaign intake and vendor timing pressure make competitive-bid exceptions a normalized workaround.",
            "recommendation": "Introduce earlier campaign procurement intake and require structured exception reason codes.",
            "requirement": "FR-08",
            "kpi": "Exception and undocumented-exception rates by department",
        },
        {
            "finding_id": "FND-06",
            "title": "Segregation-of-duties signals concentrate in Revenue",
            "evidence": f"Revenue accounts for {(revenue_self/self_total*100 if self_total else 0):.1f}% of self-approval indicators ({revenue_self:,} of {self_total:,}).",
            "root_cause_hypothesis": "Delegated approver configuration in high-velocity commercial teams permits requester/approver identity overlap.",
            "recommendation": "Enforce requester-versus-approver validation and audit delegated approval groups.",
            "requirement": "FR-07",
            "kpi": "Self-approval indicators by business unit",
        },
        {
            "finding_id": "FND-07",
            "title": "Near-threshold clusters warrant human review",
            "evidence": f"The indicator logic identified {len(patterns):,} employee/vendor clusters totaling ${patterns.combined_value.sum():,.0f} across flagged transactions.",
            "root_cause_hypothesis": "Clusters may reflect phased delivery, recurring purchases, budget timing, or threshold avoidance; the data alone cannot establish intent.",
            "recommendation": "Route indicators to a documented, context-aware review process; do not automate adverse conclusions.",
            "requirement": "FR-10",
            "kpi": "Indicator disposition and false-positive rate",
        },
    ]
    return findings


def write_metrics(path: Path, summary: dict, findings: list[dict]) -> None:
    path.write_text(json.dumps({"summary": summary, "findings": findings}, indent=2), encoding="utf-8")
