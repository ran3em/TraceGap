# Data Dictionary

## Source tables

| File / table | Grain | Primary key | Important relationships |
|---|---|---|---|
| `departments` | One row per department | `department_id` | Parent of employees and requests |
| `employees` | One row per employee | `employee_id` | Requester and event performer; belongs to department |
| `vendors` | One row per vendor | `vendor_id` | Parent of purchase requests |
| `business_rules` | One row per governed rule | `rule_id` | Parent of rule violations |
| `purchase_requests` | One row per purchase request | `request_id` | Links employee, department, vendor, events, process instance, violations |
| `workflow_events` | One activity at one timestamp | `event_id` | Child of request; performer is an employee |

## Analytical tables

| File / table | Grain | Purpose |
|---|---|---|
| `process_instances` | One row per request | Expected/observed paths, missing/extra steps, cycle time, variants, drift components |
| `rule_violations` | One row per request/rule violation record | Traceable rule, severity, type, evidence, gross affected value |
| `threshold_patterns` | One row per employee/vendor/date cluster | Human-review indicator for near-threshold patterns |
| `rule_summary.csv` | One row per rule | Applicable population, violation count, compliance, affected value |
| `path_variants.csv` | One row per observed path | Frequency, share, cycle time, value, organizational spread |
| `metrics.json` | One governed payload | Executive metrics and computed narrative findings |

## Key analytical fields

| Field | Definition |
|---|---|
| `aligned` | True when no applicable rule violation or sequence issue is detected |
| `drift_score` | Explainable 0–100 sum of severity, ordering, rework, exception, and rarity components |
| `expected_path` | Canonical readable path constructed from applicable rules |
| `observed_path` | Readable path reconstructed from timestamp-ordered events |
| `missing_steps` | JSON array of expected activities absent from the event log |
| `variant_frequency` | Number of requests with the identical observed path |
| `cycle_time_hours` | Hours between the first and last observed event |
| `amount_at_risk` | Gross request value associated with the violation; not loss or savings |
| `system_period` | Before update for dates prior to July 1, otherwise After update |

## Dataset profile

- 2,000 synthetic employee records across 10 departments and five offices.
- 140 synthetic vendors.
- 8,500 purchase requests in calendar year 2025.
- 44,862 workflow events.
- 18 business rules.
- 2,187 violation records.
- 12 threshold-review patterns.
