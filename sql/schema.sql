PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS v_request_analysis;
DROP TABLE IF EXISTS threshold_patterns;
DROP TABLE IF EXISTS rule_violations;
DROP TABLE IF EXISTS process_instances;
DROP TABLE IF EXISTS workflow_events;
DROP TABLE IF EXISTS purchase_requests;
DROP TABLE IF EXISTS business_rules;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    department_id TEXT PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE,
    business_unit TEXT NOT NULL,
    budget REAL NOT NULL CHECK (budget > 0)
);

CREATE TABLE employees (
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT NOT NULL,
    department_id TEXT NOT NULL REFERENCES departments(department_id),
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    manager_id TEXT,
    manager TEXT,
    approval_limit REAL NOT NULL CHECK (approval_limit >= 0),
    location TEXT NOT NULL,
    tenure_years REAL NOT NULL CHECK (tenure_years >= 0)
);

CREATE TABLE vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    vendor_category TEXT NOT NULL,
    approved_vendor INTEGER NOT NULL CHECK (approved_vendor IN (0, 1)),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('Low', 'Medium', 'High')),
    contract_status TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE business_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    rule_description TEXT NOT NULL,
    condition TEXT NOT NULL,
    required_step TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    effective_date TEXT NOT NULL,
    policy_owner TEXT NOT NULL
);

CREATE TABLE purchase_requests (
    request_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    department_id TEXT NOT NULL REFERENCES departments(department_id),
    vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
    request_date TEXT NOT NULL,
    purchase_type TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL,
    description TEXT NOT NULL,
    urgency TEXT NOT NULL CHECK (urgency IN ('Standard', 'Priority', 'Urgent')),
    risk_category TEXT NOT NULL CHECK (risk_category IN ('Low', 'Medium', 'High')),
    contract_required INTEGER NOT NULL CHECK (contract_required IN (0, 1)),
    security_review_required INTEGER NOT NULL CHECK (security_review_required IN (0, 1)),
    competitive_bid_required INTEGER NOT NULL CHECK (competitive_bid_required IN (0, 1)),
    exception_documented INTEGER NOT NULL CHECK (exception_documented IN (0, 1)),
    urgency_documented INTEGER NOT NULL CHECK (urgency_documented IN (0, 1)),
    final_status TEXT NOT NULL,
    source_system TEXT NOT NULL,
    system_period TEXT NOT NULL CHECK (system_period IN ('Before update', 'After update'))
);

CREATE TABLE workflow_events (
    event_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES purchase_requests(request_id),
    event_timestamp TEXT NOT NULL,
    activity TEXT NOT NULL,
    performed_by TEXT NOT NULL REFERENCES employees(employee_id),
    performer_role TEXT NOT NULL,
    system TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL
);

CREATE TABLE process_instances (
    request_id TEXT PRIMARY KEY REFERENCES purchase_requests(request_id),
    expected_path TEXT NOT NULL,
    observed_path TEXT NOT NULL,
    expected_steps TEXT NOT NULL,
    actual_steps TEXT NOT NULL,
    missing_steps TEXT NOT NULL,
    extra_steps TEXT NOT NULL,
    sequence_issues TEXT NOT NULL,
    step_count INTEGER NOT NULL,
    expected_step_count INTEGER NOT NULL,
    rework_count INTEGER NOT NULL,
    exception_count INTEGER NOT NULL,
    cycle_time_hours REAL NOT NULL,
    has_unusual_sequence INTEGER NOT NULL CHECK (has_unusual_sequence IN (0, 1)),
    variant_frequency INTEGER NOT NULL,
    rare_path INTEGER NOT NULL CHECK (rare_path IN (0, 1)),
    drift_score INTEGER NOT NULL CHECK (drift_score BETWEEN 0 AND 100),
    violation_points INTEGER NOT NULL,
    ordering_points INTEGER NOT NULL,
    rework_points INTEGER NOT NULL,
    exception_points INTEGER NOT NULL,
    rare_path_points INTEGER NOT NULL,
    violation_count INTEGER NOT NULL,
    critical_violation_count INTEGER NOT NULL,
    high_violation_count INTEGER NOT NULL,
    aligned INTEGER NOT NULL CHECK (aligned IN (0, 1))
);

CREATE TABLE rule_violations (
    violation_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES purchase_requests(request_id),
    rule_id TEXT NOT NULL REFERENCES business_rules(rule_id),
    rule_name TEXT NOT NULL,
    required_step TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    violation_type TEXT NOT NULL,
    evidence TEXT NOT NULL,
    amount_at_risk REAL NOT NULL CHECK (amount_at_risk >= 0)
);

CREATE TABLE threshold_patterns (
    pattern_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    department_name TEXT NOT NULL,
    vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
    vendor_name TEXT NOT NULL,
    request_ids TEXT NOT NULL,
    transaction_count INTEGER NOT NULL,
    first_date TEXT NOT NULL,
    last_date TEXT NOT NULL,
    combined_value REAL NOT NULL,
    threshold REAL NOT NULL,
    reason_flagged TEXT NOT NULL,
    review_status TEXT NOT NULL
);

CREATE INDEX idx_request_date ON purchase_requests(request_date);
CREATE INDEX idx_request_department ON purchase_requests(department_id);
CREATE INDEX idx_event_request_time ON workflow_events(request_id, event_timestamp);
CREATE INDEX idx_violation_rule ON rule_violations(rule_id);
CREATE INDEX idx_violation_request ON rule_violations(request_id);
CREATE INDEX idx_process_drift ON process_instances(drift_score DESC);

CREATE VIEW v_request_analysis AS
SELECT
    pr.request_id,
    pr.request_date,
    pr.amount,
    pr.purchase_type,
    pr.urgency,
    pr.risk_category,
    pr.final_status,
    pr.source_system,
    pr.system_period,
    d.department_name,
    d.business_unit,
    e.employee_id,
    e.employee_name,
    e.location,
    v.vendor_id,
    v.vendor_name,
    v.approved_vendor,
    v.risk_level AS vendor_risk,
    pi.observed_path,
    pi.expected_path,
    pi.drift_score,
    pi.aligned,
    pi.violation_count,
    pi.critical_violation_count,
    pi.high_violation_count,
    pi.exception_count,
    pi.rework_count,
    pi.cycle_time_hours,
    pi.has_unusual_sequence
FROM purchase_requests pr
JOIN departments d ON d.department_id = pr.department_id
JOIN employees e ON e.employee_id = pr.employee_id
JOIN vendors v ON v.vendor_id = pr.vendor_id
JOIN process_instances pi ON pi.request_id = pr.request_id;
