# TraceGap Business Requirements Document

| Document field | Value |
|---|---|
| Product | TraceGap — Business Process Drift & Change Impact Intelligence |
| Organization | Northstar Technologies (fictional) |
| Process | Purchase-to-Pay |
| Analysis period | January–December 2025 |
| Status | Portfolio case study baseline |

> This document describes an independent portfolio case study using synthetic data. Northstar Technologies, its employees, and its transactions are fictional. No production implementation or realized benefit is claimed.

## Executive summary

Northstar documents Purchase-to-Pay controls in policy, but its transaction systems do not consistently enforce the same workflow. TraceGap provides a control layer that translates policy into executable rules, reconstructs observed event paths, compares expected and actual behavior, prioritizes drift, detects review indicators, and estimates the historical operational effect of proposed rule changes.

## Problem statement

Process owners cannot answer, from one governed source, whether every purchase received the approvals and reviews applicable to its amount, category, vendor risk, urgency, contract status, and effective policy date. Manual sampling obscures systematic drift, while application updates may improve one control and weaken another. This creates audit effort, inconsistent routing, avoidable rework, and uncertain change impact.

## Scope

**In scope**

- One year of synthetic Northstar Purchase-to-Pay requests and workflow events.
- Manager, Director, Finance, Procurement, Security, Legal, vendor, bid, exception, authorization, and sequence controls.
- Expected-versus-observed path comparison and request-level investigation.
- Department, business-unit, category, vendor, office, system, and time-period analysis.
- Historical impact simulation for selected Finance, Director, and Security rules.
- Potential threshold-avoidance indicators for human review.

**Out of scope**

- Invoice matching, accounts-payable ledger reconciliation, tax, currency conversion, and budget forecasting.
- Production identity, live application integration, automated disciplinary action, fraud conclusions, or predictive machine learning.
- Realized savings, ROI, or claims that Northstar implemented a recommendation.

## Stakeholders

| Stakeholder | What they care about | Information needed | Decisions supported |
|---|---|---|---|
| CFO | Financial-control coverage and approval workload | High-value bypasses, Finance demand, exposure by rule | Threshold policy, reviewer capacity, remediation priority |
| VP of Procurement | Vendor governance and sourcing discipline | Procurement bypasses, bid exceptions, vendor patterns | Routing design, supplier controls, exception policy |
| Finance Operations Manager | Queue health and reliable approvals | Cycle time, missing approvals, simulated workload | Staffing, SLAs, threshold configuration |
| Information Security | Technology risk entering the estate | Missing Security reviews by category, department, vendor | Intake gates and review scope |
| Legal | Contract and international-vendor coverage | Missing Legal reviews and affected contract value | Contract-routing rules and escalation |
| Department Managers | Timely purchasing with clear obligations | Team drift, rework, exception causes | Coaching, intake changes, local process ownership |
| Internal Audit | Complete, traceable control evidence | Rule applicability, violations, event audit trail | Sampling, control testing, follow-up |
| Employees | Predictable submission and approval experience | Required steps, status, return reasons | Complete requests correctly and plan lead time |
| Application Support Team | Stable configuration and adoption | Rule logic, application/office differences, sequence defects | Defect triage, release validation, legacy retirement |

## Business objectives

| ID | Objective | Measure |
|---|---|---|
| OBJ-01 | Make documented policy and actual system behavior directly comparable | Expected and observed paths available for every request |
| OBJ-02 | Identify control gaps consistently and traceably | Every violation links to a governed rule and evidence |
| OBJ-03 | Prioritize drift for operational review | Explainable 0–100 Process Drift Score |
| OBJ-04 | Measure application-change effectiveness and side effects | Before/after metrics by rule, office, and system |
| OBJ-05 | Estimate operational impact before changing a rule | Historical population and workload impact by team/category |
| OBJ-06 | Preserve human judgment for sensitive indicators | Threshold clusters are labelled as indicators, not conclusions |

## Business requirements

| ID | Requirement |
|---|---|
| BR-01 | The organization must maintain a governed catalog of Purchase-to-Pay business rules. |
| BR-02 | The organization must reconstruct the actual process path from application events. |
| BR-03 | Process owners must be able to identify missing, out-of-order, unauthorized, and self-approved workflow activity. |
| BR-04 | Management must be able to measure alignment and drift at transaction and aggregate levels. |
| BR-05 | Control owners must be able to trace a violation to policy, triggering facts, and event evidence. |
| BR-06 | Change owners must be able to compare performance before and after a system release. |
| BR-07 | Analysts must be able to estimate how selected policy changes would reclassify historical work. |
| BR-08 | Internal Audit must be able to identify potential near-threshold transaction clusters for human review. |
| BR-09 | Stakeholders must be able to filter analysis without changing source data. |
| BR-10 | Recommendations must be supported by measured evidence and explicitly separated from implemented outcomes. |

## Functional requirements

| ID | Functional requirement | Priority |
|---|---|---|
| FR-01 | Load and relate requests, events, employees, departments, vendors, and business rules in SQLite. | Must |
| FR-02 | Reconstruct a timestamp-ordered workflow path for every purchase request. | Must |
| FR-03 | Determine the rules applicable to a request using transaction facts and effective dates. | Must |
| FR-04 | Compare expected required steps with observed events and record missing controls. | Must |
| FR-05 | Detect incorrect event ordering, including payment before purchase-order creation. | Must |
| FR-06 | Evaluate Security-review requirements using purchase category and vendor risk. | Must |
| FR-07 | Detect approval-limit breaches and requester self-approval. | Must |
| FR-08 | Identify exception use and missing exception/urgency documentation. | Must |
| FR-09 | Calculate request and aggregate Process Drift Scores with visible component contributions. | Must |
| FR-10 | Detect near-threshold employee/vendor clusters and present a human-review disclaimer. | Must |
| FR-11 | Compare Vendor Validation control performance before and after the July release. | Should |
| FR-12 | Compare urgent-routing Procurement compliance before and after the July release. | Should |
| FR-13 | Show office and source-system adoption differences after the release. | Should |
| FR-14 | Simulate historical impact for Finance threshold, Director threshold, and Security scope changes. | Must |
| FR-15 | Present executive health, path variants, rule drill-down, transaction evidence, change analysis, and recommendations in one application. | Must |

## Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Identical source data and seed must produce identical analytical outputs. |
| NFR-02 | Every score and flag must be explainable without machine-learning inference. |
| NFR-03 | Common filtered views should render interactively on a local workstation. |
| NFR-04 | Database relationships must pass SQLite foreign-key validation. |
| NFR-05 | The application must distinguish gross affected transaction value from loss or savings. |
| NFR-06 | Sensitive review indicators must not assert intent, misconduct, or fraud. |
| NFR-07 | The UI must use a consistent enterprise information hierarchy and accessible contrast. |
| NFR-08 | The repository must run from documented commands on Python 3.11 or newer. |

## Business rules

The executable catalog contains 18 rules (`RULE-001`–`RULE-018`). It covers manager, Finance, Director, Security, Legal, Procurement, competitive bid, authorization, segregation-of-duties, vendor validation, documented exception, PO-before-payment, international vendor, contractor, effective-dated travel threshold, urgency rationale, and equipment dual-control requirements. The source of truth is `data/raw/business_rules.csv`; executable predicates are registered in `src/rule_engine.py`.

## Assumptions

- Event timestamps are accurate enough to establish ordering.
- USD is the analysis currency; no FX conversion is required.
- Each request belongs to one requester, department, and vendor.
- Approval limits in the employee master are effective for the analysis period.
- A historical simulation reclassifies past work but does not forecast behavioral response.
- Gross affected value indicates the transaction value associated with a control gap, not financial loss.

## Constraints

- Synthetic data cannot validate actual user behavior or production integration complexity.
- The event log has no free-text attachment content, invoice lines, or budget ledger.
- Root causes are evidence-backed hypotheses requiring stakeholder validation.
- SQLite and local Streamlit are appropriate for a portfolio prototype, not enterprise scale or access control.

## Success metrics

| Metric | Definition | Synthetic baseline |
|---|---|---:|
| Process Alignment Rate | Requests satisfying all applicable rules and sequence checks | 82.61% |
| Critical Rule Compliance | Requests without a Critical-severity violation | 92.42% |
| High-Severity Violation Rate | Requests with at least one High-severity violation | 9.00% |
| Exception Rate | Requests containing Exception Approved | 1.15% |
| Rework Rate | Requests containing Returned for Revision | 5.14% |
| Average Process Drift Score | Mean request-level explainable drift score | 4.56 / 100 |
| Median Approval Cycle Time | Median elapsed time from first to last event | 52.64 hours |
| Process Step Completion Rate | Completed steps divided by expected steps, capped at 100% | 97.25% |
