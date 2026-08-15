# User Acceptance Testing

## Test approach

Tests use the deterministic FY2025 synthetic dataset produced with seed `20250317`. Acceptance requires both the scripted assertion and the visible application behavior where applicable.

| ID | Requirement | Scenario and precondition | Steps | Expected result | Status |
|---|---|---|---|---|---|
| UAT-01 | FR-01 | Relational database build | Run the pipeline; enable foreign keys; run `PRAGMA foreign_key_check` | Nine core tables load; no orphaned foreign keys; request and event counts are 8,500 and 44,862 | Pass |
| UAT-02 | FR-02 | Reconstruct a known request path | Select a request; order events by timestamp; compare to `process_instances.actual_steps` | Stored activities and displayed observed path match event order | Pass |
| UAT-03 | FR-03 | Evaluate rule applicability | Use requests below/above $10,000 and dates around July 1 | Finance and effective-dated travel rules apply only when their conditions are true | Pass |
| UAT-04 | FR-04 | Detect a missing required step | Select a request with `RULE-002`; inspect events and Investigator | Finance Approval is absent, a High violation exists, and the expected path shows Finance | Pass |
| UAT-05 | FR-05 | Detect payment-before-PO | Select a `RULE-012` request; inspect event timestamps | Critical incorrect-sequence violation is recorded; score includes ordering points | Pass |
| UAT-06 | FR-06 | Evaluate Security scope | Compare Software, AI Services, and high-risk Equipment with other categories | Applicable technology requests expect Security; absent reviews appear in rule drill-down | Pass |
| UAT-07 | FR-07 | Validate authorization and segregation | Inspect `RULE-008` and `RULE-009` cases against employee and event data | Evidence names the approval actor/limit or requester identity; severity is Critical | Pass |
| UAT-08 | FR-08 | Validate exception documentation | Select an Exception Approved event whose request is undocumented | `RULE-011` is recorded; Marketing roll-up shows elevated exception use | Pass |
| UAT-09 | FR-09 | Verify drift calculation | Recalculate components for selected high-drift and aligned requests | Component sum matches stored score, capped at 100; aligned request has no violations/sequence issues | Pass |
| UAT-10 | FR-10 | Detect near-threshold cluster | Run detection at $10,000, 88%, 21 days, minimum 3 | 12 clusters are returned; each meets amount, date, actor/vendor, and combined-value conditions; disclaimer is visible | Pass |
| UAT-11 | FR-11 | Measure Vendor Validation update effect | Compare applicable `RULE-010` requests before and after July | Violation rate changes from 17.4% to 5.7%; calculation uses applicable populations | Pass |
| UAT-12 | FR-12 | Measure urgent Procurement side effect | Filter urgent requests and Procurement-related rules by period | Violation incidence changes from 3.7% before to 10.4% after | Pass |
| UAT-13 | FR-13 | Identify adoption difference | Filter post-update requests; group by office and source system | Austin has a materially larger legacy-system share and its $5K–$7.5K travel violation rate exceeds other offices | Pass |
| UAT-14 | FR-14 | Simulate policy change | Set Finance threshold to $5,000; then Director to $40,000; expand Security scope | Net reclassified requests, affected percentage, hours, departments, and categories update without changing source data | Pass |
| UAT-15 | FR-15 | Navigate integrated application | Open every navigation item; apply filters; select a rule/request; change simulator controls | Nine pages render without runtime errors; filter/drill-down results remain internally consistent | Pass |

## KPI calculation checks

| KPI | Acceptance formula |
|---|---|
| Process Alignment Rate | `aligned requests / all requests` |
| Critical Rule Compliance | `1 - requests with any Critical violation / all requests` |
| High-Severity Violation Rate | `requests with any High violation / all requests` |
| Exception Rate | `requests with Exception Approved / all requests` |
| Rework Rate | `requests with Returned for Revision / all requests` |
| Average Process Drift Score | Arithmetic mean of capped request scores |
| Median Approval Cycle Time | Median hours between first and last event per request |
| Process Step Completion Rate | Mean of `min(actual step count / expected step count, 1)` |

## Exit criteria

- All 15 functional requirements have passing UAT coverage.
- Generated metrics reconcile across CSV, SQLite, Python, and displayed pages.
- SQL analysis executes without syntax error.
- App smoke test returns healthy and critical pages pass visual inspection.
- Ethical language is present on the threshold, simulator, recommendation, README, and case-study surfaces.
