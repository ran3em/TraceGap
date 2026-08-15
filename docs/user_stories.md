# User Stories and Acceptance Criteria

## US-01 — Executive process health

**As a CFO, I want** a concise view of alignment, critical controls, exceptions, drift, and cycle time **so that** I can prioritize governance attention.

- Given the processed dataset, when the Executive page loads, then all headline metrics equal the governed metric definitions.
- Trends distinguish pre- and post-update periods.
- Affected transaction value is never labelled as loss or savings.

## US-02 — Observed path variants

**As a Process Owner, I want** to see the most common actual workflow paths **so that** I can distinguish the standard process from local variants.

- Paths are ordered from timestamped workflow events.
- Path counts respond to department, category, risk, amount, and date filters.
- Rework and skipped-step rates are recalculated for the filtered population.

## US-03 — Rule applicability

**As an Internal Audit analyst, I want** to know how many transactions each rule applied to **so that** compliance rates have a valid denominator.

- Applicability is evaluated from request and vendor facts.
- Effective-dated travel thresholds use the request date.
- Rules with no applicable transactions return 100% compliance without division errors.

## US-04 — Missing mandatory approvals

**As a Finance Operations Manager, I want** missing Finance approvals identified **so that** I can review high-value requests that bypassed policy.

- A request above $10,000 expects Finance approval.
- A missing event produces one traceable `RULE-002` violation.
- The investigator shows the absent step in the expected-versus-actual comparison.

## US-05 — Security coverage

**As an Information Security reviewer, I want** software, AI, and high-risk technology purchases evaluated consistently **so that** risky vendors do not enter the estate without review.

- Software and AI Services trigger the category rule.
- High-risk Equipment triggers the vendor-risk rule.
- Rule drill-down includes category, department, vendor, amount, and evidence.

## US-06 — Contract routing

**As Legal counsel, I want** high-value contracts and high-risk international vendors routed to Legal **so that** contractual risk receives review.

- Contract-required requests above $50,000 expect Legal Review.
- High-risk non-US vendors expect Legal Review.
- One observed Legal event can satisfy both applicable requirements.

## US-07 — Authorization validation

**As Internal Audit, I want** approval amounts compared with employee authorization limits **so that** out-of-limit approvals can be investigated.

- Manager and Director approval actors are joined to the employee master.
- Amounts above the actor's limit create a Critical violation with actor and limit evidence.
- Missing employee master data cannot silently pass validation.

## US-08 — Segregation of duties

**As an Application Support analyst, I want** self-approval attempts detected **so that** delegated approval configuration can be corrected.

- Any approval event performed by the requester triggers `RULE-009`.
- The flag is described as an indicator, not misconduct.
- Business-unit aggregation is available for pattern analysis.

## US-09 — Explainable prioritization

**As a Department Manager, I want** a transparent Process Drift Score **so that** I can understand why one request ranks above another.

- Scores remain between 0 and 100.
- Component points are stored for violations, ordering, rework, exceptions, and path rarity.
- No machine-learning terminology or probability claim is used.

## US-10 — Threshold indicators

**As an Internal Audit analyst, I want** repeated near-threshold employee/vendor clusters highlighted **so that** I can decide whether contextual review is appropriate.

- A pattern requires at least three 88%–100% threshold purchases within 21 days.
- The combined value exceeds the Finance threshold.
- Every page and export includes the human-review disclaimer.

## US-11 — Release effectiveness

**As a Product Operations analyst, I want** before/after rule performance **so that** I can determine whether NovaProcure achieved the intended control change.

- July 1 is the configured change boundary.
- Vendor Validation is shown with applicable-request denominators.
- Results can be split by source system and office.

## US-12 — Unintended consequences

**As an Application Support lead, I want** compliance issues that worsened after go-live surfaced **so that** regression defects are not hidden by aggregate improvement.

- Urgent Procurement-related violations are compared before and after July.
- The application separates an observed association from a confirmed root cause.
- Recommended follow-up includes a routing regression test.

## US-13 — Transaction investigation

**As a Control Owner, I want** one request's facts, expected path, observed path, rule evidence, and event trail together **so that** I can complete a defensible review.

- Search accepts a request ID.
- Expected and actual paths are visually distinct.
- Every violation links to its rule ID, severity, type, and evidence.

## US-14 — Historical impact simulation

**As a Policy Owner, I want** to modify selected thresholds and scopes **so that** I can estimate retrospective workload before proposing a change.

- The Finance and Director thresholds can be increased or decreased.
- Security scope can include AI Services and Equipment.
- Outputs show net reviews, affected share, workload assumption, departments, and categories.
- The page states that results are historical reclassification, not prediction.

## US-15 — Evidence-backed recommendations

**As a Business Systems Analyst, I want** recommendations linked to evidence, a root-cause hypothesis, a requirement, and a KPI **so that** stakeholders can evaluate the proposed change without confusing it with an implemented outcome.

- Evidence values come from `data/processed/metrics.json`.
- Each recommendation names a functional requirement and monitoring KPI.
- No recommendation claims realized ROI or production adoption.

