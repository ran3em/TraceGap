# Requirements Traceability Matrix

This matrix connects business intent to executable components and UAT evidence. Requirement wording is authoritative in [business_requirements.md](business_requirements.md).

| Objective | Business requirement | Functional requirement | System component | UAT test |
|---|---|---|---|---|
| OBJ-01 | BR-01 | FR-01 — Load related enterprise data | `src/database.py`, `sql/schema.sql` | UAT-01 |
| OBJ-01 | BR-02 | FR-02 — Reconstruct ordered workflow paths | `src/process_engine.py` | UAT-02 |
| OBJ-02 | BR-03 | FR-03 — Evaluate applicable rules | `src/rule_engine.py` | UAT-03 |
| OBJ-02 | BR-03 | FR-04 — Detect missing required steps | `src/rule_engine.py` | UAT-04 |
| OBJ-02 | BR-03 | FR-05 — Detect incorrect ordering | `src/process_engine.py`, `src/rule_engine.py` | UAT-05 |
| OBJ-02 | BR-05 | FR-06 — Evaluate Security-review scope | Rule Engine, Rule Compliance page | UAT-06 |
| OBJ-02 | BR-03 | FR-07 — Validate authorization and segregation of duties | Rule Engine, Transaction Investigator | UAT-07 |
| OBJ-02 | BR-05 | FR-08 — Validate exception and urgency documentation | Rule Engine, Rule Compliance page | UAT-08 |
| OBJ-03 | BR-04 | FR-09 — Calculate explainable drift scores | `src/drift_scoring.py`, Drift Intelligence page | UAT-09 |
| OBJ-06 | BR-08 | FR-10 — Detect near-threshold clusters | `src/threshold_detection.py`, Threshold page | UAT-10 |
| OBJ-04 | BR-06 | FR-11 — Compare Vendor Validation before/after | Metrics pipeline, System Change page | UAT-11 |
| OBJ-04 | BR-06 | FR-12 — Compare urgent Procurement routing | Metrics pipeline, System Change page | UAT-12 |
| OBJ-04 | BR-06 | FR-13 — Analyze adoption by office/system | SQL analysis, System Change page | UAT-13 |
| OBJ-05 | BR-07 | FR-14 — Simulate selected rule changes | `src/change_simulator.py`, Simulator page | UAT-14 |
| OBJ-01 | BR-09 | FR-15 — Provide integrated decision-support UI | `app.py` and nine application pages | UAT-15 |

## Coverage summary

- 6/6 business objectives are traced.
- 10/10 business requirements are represented in at least one functional requirement.
- 15/15 functional requirements map to an implemented component and UAT scenario.
- UAT covers data integrity, rule logic, reconstruction, scoring, indicators, release analysis, simulation, filtering, and evidence display.

