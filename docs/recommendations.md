# Evidence-Backed Findings and Recommendations

> All findings describe a deterministic synthetic dataset for a fictional company. Root causes are hypotheses to validate with stakeholders. Recommendations are proposals only; they were not implemented, and no savings or ROI is claimed.

## FND-01 — Engineering carries disproportionate Security-review drift

| Field | Detail |
|---|---|
| Finding | Engineering represents **19.3%** of purchase volume but **48.1%** of Security-review violations: 180 of 374. |
| Evidence | `RULE-004` and `RULE-014` violations joined to department and purchase category. |
| Root-cause hypothesis | Technology purchases use team-specific intake paths that do not consistently invoke the central Security gate. |
| Recommendation | Evaluate Security applicability at submission; block PO creation when a required Security review is absent; test software and AI category mapping. |
| System requirement | FR-06 |
| KPI | Security-review compliance by department and category |

## FND-02 — The July update improved Vendor Validation

| Field | Detail |
|---|---|
| Finding | Applicable Vendor Validation violations fell from **17.4% before** the update to **5.7% after**, a decrease of **11.7 points**. |
| Evidence | `RULE-010` violated requests divided by requests requiring validation in each period. |
| Root-cause hypothesis | NovaProcure's enforced vendor gate reduced a control that had been optional or inconsistently configured in ProcureFlow Classic. |
| Recommendation | Retain the enforced gate; monitor by source system; prioritize legacy-application retirement. |
| System requirement | FR-11 |
| KPI | Vendor Validation violation rate by source system |

## FND-03 — Urgent routing introduced a Procurement side effect

| Field | Detail |
|---|---|
| Finding | Procurement-related violation incidence among urgent requests rose from **3.7% before** the update to **10.4% after**. |
| Evidence | Urgent requests with `RULE-006`, `RULE-015`, or `RULE-018` divided by all urgent requests in each period. |
| Root-cause hypothesis | The fast-track branch prioritizes cycle time but does not always rejoin the mandatory Procurement gate. |
| Recommendation | Add a non-bypassable Procurement eligibility check and a regression test covering urgent unapproved-vendor, contractor, and dual-control scenarios. |
| System requirement | FR-12 |
| KPI | Urgent-request Procurement compliance |

## FND-04 — Austin shows a legacy travel-threshold adoption gap

| Field | Detail |
|---|---|
| Finding | After July, $5,000–$7,500 travel requests have a **57.1%** Finance-rule violation rate in Austin versus **12.5%** elsewhere. |
| Evidence | Post-update travel population joined to requester location, source system, and Finance-rule violations. |
| Root-cause hypothesis | A material share of Austin traffic remains on the legacy application, which still applies the former $7,500 threshold. |
| Recommendation | Complete Austin migration; add an effective-date configuration check and location-level validation to release readiness. |
| System requirement | FR-13 |
| KPI | Post-change compliance by office and source system |

## FND-05 — Marketing uses exceptions at an elevated rate

| Field | Detail |
|---|---|
| Finding | Marketing's exception rate is **2.7%**, versus **1.2%** company-wide. |
| Evidence | Requests whose event path contains Exception Approved, grouped by department. |
| Root-cause hypothesis | Late campaign intake and vendor timing pressure make competitive-bid exceptions a normalized workaround. |
| Recommendation | Introduce earlier campaign procurement intake, structured exception reasons, evidence requirements, and monthly owner review. |
| System requirement | FR-08 |
| KPI | Exception and undocumented-exception rates by department |

## FND-06 — Segregation-of-duties indicators concentrate in Revenue

| Field | Detail |
|---|---|
| Finding | Revenue accounts for **67.9%** of self-approval indicators: 129 of 190. |
| Evidence | `RULE-009` request IDs joined to requester's business unit. |
| Root-cause hypothesis | Delegated approver configuration in high-velocity commercial teams permits requester/approver identity overlap. |
| Recommendation | Enforce requester-versus-approver validation before accepting an approval and review membership of delegated groups. |
| System requirement | FR-07 |
| KPI | Self-approval indicators by business unit |

## FND-07 — Near-threshold clusters warrant human review

| Field | Detail |
|---|---|
| Finding | Indicator logic identifies **12 employee/vendor clusters** totalling **$340,538** across flagged transactions. |
| Evidence | Three or more purchases at 88%–100% of $10,000, same employee/vendor, within 21 days, combined value above threshold. |
| Root-cause hypothesis | Clusters may reflect phased delivery, recurring purchases, budget timing, or threshold avoidance. The data does not establish intent. |
| Recommendation | Route indicators to a documented, context-aware review process; collect disposition reasons and tune false positives; never automate an adverse conclusion. |
| System requirement | FR-10 |
| KPI | Indicator disposition, substantiation, and false-positive rates |

## Prioritization

| Priority | Action | Rationale |
|---|---|---|
| 1 | Repair urgent-route Procurement rejoin and regression tests | A post-release control issue with clear system ownership |
| 2 | Enforce Security eligibility at intake and before PO | Critical control with concentrated, actionable drift |
| 3 | Complete Austin legacy migration and configuration validation | Localized adoption issue with a strong effective-date signature |
| 4 | Enforce identity and authorization checks | Preventive design is stronger than retrospective detection |
| 5 | Structure exceptions and monitor Marketing intake | Combines policy clarity, user process, and evidence quality |
| 6 | Establish a fair indicator-review process | Preserves human judgment and enables responsible tuning |
