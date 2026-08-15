-- TraceGap business analysis library (SQLite)
-- Each numbered section is a standalone, decision-oriented question.

-- Q01. What is the enterprise process-health baseline?
SELECT
    COUNT(*) AS requests,
    ROUND(100.0 * AVG(aligned), 2) AS process_alignment_rate,
    ROUND(AVG(drift_score), 2) AS average_drift_score,
    ROUND(100.0 * AVG(exception_count > 0), 2) AS exception_rate,
    ROUND(100.0 * AVG(rework_count > 0), 2) AS rework_rate,
    ROUND(AVG(cycle_time_hours), 2) AS average_cycle_hours
FROM v_request_analysis;

-- Q02. Which departments have the highest Process Drift Score?
SELECT department_name, COUNT(*) AS requests,
       ROUND(AVG(drift_score), 2) AS average_drift_score,
       ROUND(100.0 * AVG(aligned), 2) AS alignment_rate
FROM v_request_analysis
GROUP BY department_name
ORDER BY average_drift_score DESC;

-- Q03. Which business units carry the greatest critical-control burden?
SELECT business_unit, COUNT(*) AS requests,
       SUM(critical_violation_count) AS critical_violations,
       ROUND(100.0 * AVG(critical_violation_count > 0), 2) AS affected_request_rate
FROM v_request_analysis
GROUP BY business_unit
ORDER BY affected_request_rate DESC;

-- Q04. Which rules are violated most frequently?
SELECT rv.rule_id, br.rule_name, br.severity,
       COUNT(DISTINCT rv.request_id) AS violated_requests
FROM rule_violations rv
JOIN business_rules br ON br.rule_id = rv.rule_id
GROUP BY rv.rule_id, br.rule_name, br.severity
ORDER BY violated_requests DESC;

-- Q05. Which rules create the largest gross transaction exposure?
SELECT rv.rule_id, rv.rule_name, rv.severity,
       COUNT(*) AS violation_records,
       ROUND(SUM(rv.amount_at_risk), 2) AS gross_affected_value,
       ROUND(AVG(rv.amount_at_risk), 2) AS average_affected_value
FROM rule_violations rv
GROUP BY rv.rule_id, rv.rule_name, rv.severity
ORDER BY gross_affected_value DESC;

-- Q06. Which required process steps are most frequently absent?
SELECT required_step, severity, COUNT(*) AS missing_count,
       ROUND(SUM(amount_at_risk), 2) AS affected_value
FROM rule_violations
WHERE violation_type IN ('Missing required step', 'Dual control incomplete')
GROUP BY required_step, severity
ORDER BY missing_count DESC;

-- Q07. Which teams use exceptions disproportionately relative to volume?
WITH company AS (
    SELECT AVG(exception_count > 0) AS company_rate FROM v_request_analysis
)
SELECT department_name, COUNT(*) AS requests,
       ROUND(100.0 * AVG(exception_count > 0), 2) AS exception_rate,
       ROUND(100.0 * (AVG(exception_count > 0) - company_rate), 2) AS variance_points
FROM v_request_analysis CROSS JOIN company
GROUP BY department_name
ORDER BY variance_points DESC;

-- Q08. What workflow variants are most common?
SELECT observed_path, COUNT(*) AS requests,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct,
       ROUND(AVG(drift_score), 2) AS average_drift_score
FROM v_request_analysis
GROUP BY observed_path
ORDER BY requests DESC
LIMIT 15;

-- Q09. Which categories experience the most rework?
SELECT purchase_type, COUNT(*) AS requests,
       SUM(rework_count > 0) AS reworked_requests,
       ROUND(100.0 * AVG(rework_count > 0), 2) AS rework_rate,
       ROUND(AVG(cycle_time_hours), 2) AS average_cycle_hours
FROM v_request_analysis
GROUP BY purchase_type
ORDER BY rework_rate DESC;

-- Q10. Did the July system update improve overall process alignment?
SELECT system_period, COUNT(*) AS requests,
       ROUND(100.0 * AVG(aligned), 2) AS alignment_rate,
       ROUND(AVG(drift_score), 2) AS average_drift_score,
       ROUND(100.0 * AVG(critical_violation_count > 0), 2) AS critical_request_rate
FROM v_request_analysis
GROUP BY system_period
ORDER BY CASE system_period WHEN 'Before update' THEN 1 ELSE 2 END;

-- Q11. Which compliance issues increased or decreased after the update?
WITH period_rules AS (
    SELECT pr.system_period, rv.rule_id, rv.rule_name,
           COUNT(DISTINCT rv.request_id) AS violations
    FROM purchase_requests pr
    JOIN rule_violations rv ON rv.request_id = pr.request_id
    GROUP BY pr.system_period, rv.rule_id, rv.rule_name
), period_totals AS (
    SELECT system_period, COUNT(*) AS period_requests
    FROM purchase_requests
    GROUP BY system_period
), pivoted AS (
    SELECT pr.rule_id, pr.rule_name,
           MAX(CASE WHEN pr.system_period = 'Before update' THEN 100.0 * pr.violations / pt.period_requests END) AS before_rate,
           MAX(CASE WHEN pr.system_period = 'After update' THEN 100.0 * pr.violations / pt.period_requests END) AS after_rate
    FROM period_rules pr
    JOIN period_totals pt ON pt.system_period = pr.system_period
    GROUP BY pr.rule_id, pr.rule_name
)
SELECT rule_id, rule_name, ROUND(before_rate, 2) AS before_rate,
       ROUND(after_rate, 2) AS after_rate,
       ROUND(after_rate - before_rate, 2) AS change_points
FROM pivoted
ORDER BY change_points DESC;

-- Q12. Which offices appear to remain on the legacy system after July?
SELECT e.location, pr.source_system, COUNT(*) AS post_update_requests,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY e.location), 2) AS office_share
FROM purchase_requests pr
JOIN employees e ON e.employee_id = pr.employee_id
WHERE pr.system_period = 'After update'
GROUP BY e.location, pr.source_system
ORDER BY e.location, office_share DESC;

-- Q13. Are urgent purchases associated with more violations?
SELECT urgency, COUNT(*) AS requests,
       ROUND(AVG(violation_count), 2) AS violations_per_request,
       ROUND(100.0 * AVG(aligned), 2) AS alignment_rate,
       ROUND(AVG(drift_score), 2) AS drift_score
FROM v_request_analysis
GROUP BY urgency
ORDER BY drift_score DESC;

-- Q14. Which employees approved beyond their authorization limits?
SELECT rv.request_id, pr.amount, we.performed_by, e.employee_name,
       e.approval_limit, d.department_name, we.event_timestamp
FROM rule_violations rv
JOIN purchase_requests pr ON pr.request_id = rv.request_id
JOIN workflow_events we ON we.request_id = rv.request_id
    AND we.activity IN ('Manager Approval', 'Director Approval')
JOIN employees e ON e.employee_id = we.performed_by
JOIN departments d ON d.department_id = pr.department_id
WHERE rv.rule_id = 'RULE-008' AND pr.amount > e.approval_limit
ORDER BY pr.amount - e.approval_limit DESC;

-- Q15. What potential threshold-avoidance clusters require review?
SELECT pattern_id, employee_id, department_name, vendor_name,
       transaction_count, first_date, last_date,
       combined_value, threshold, reason_flagged
FROM threshold_patterns
ORDER BY combined_value DESC;

-- Q16. Which vendors are associated with unusually high exception rates?
WITH vendor_stats AS (
    SELECT vendor_id, vendor_name, COUNT(*) AS requests,
           AVG(exception_count > 0) AS exception_rate
    FROM v_request_analysis
    GROUP BY vendor_id, vendor_name
), benchmark AS (
    SELECT AVG(exception_count > 0) AS company_rate FROM v_request_analysis
)
SELECT vendor_id, vendor_name, requests,
       ROUND(100.0 * exception_rate, 2) AS exception_rate,
       ROUND(100.0 * (exception_rate - company_rate), 2) AS variance_points
FROM vendor_stats CROSS JOIN benchmark
WHERE requests >= 20
ORDER BY variance_points DESC;

-- Q17. How long does each observed workflow step add to cycle time?
WITH timed AS (
    SELECT request_id, activity, event_timestamp,
           LAG(event_timestamp) OVER (PARTITION BY request_id ORDER BY event_timestamp) AS prior_timestamp
    FROM workflow_events
), elapsed AS (
    SELECT activity,
           (julianday(event_timestamp) - julianday(prior_timestamp)) * 24.0 AS elapsed_hours
    FROM timed WHERE prior_timestamp IS NOT NULL
)
SELECT activity, COUNT(*) AS occurrences,
       ROUND(AVG(elapsed_hours), 2) AS average_hours_since_prior_step
FROM elapsed
GROUP BY activity
ORDER BY average_hours_since_prior_step DESC;

-- Q18. What percentage of high-value requests bypassed required controls?
SELECT
    COUNT(*) AS high_value_requests,
    SUM(violation_count > 0) AS requests_with_control_gaps,
    ROUND(100.0 * AVG(violation_count > 0), 2) AS bypass_rate,
    ROUND(SUM(CASE WHEN violation_count > 0 THEN amount ELSE 0 END), 2) AS affected_value
FROM v_request_analysis
WHERE amount > 25000;

-- Q19. Rank departments by compliance improvement over time.
WITH department_period AS (
    SELECT department_name, system_period, AVG(aligned) AS alignment_rate
    FROM v_request_analysis
    GROUP BY department_name, system_period
), changes AS (
    SELECT department_name,
           MAX(CASE WHEN system_period = 'Before update' THEN alignment_rate END) AS before_rate,
           MAX(CASE WHEN system_period = 'After update' THEN alignment_rate END) AS after_rate
    FROM department_period GROUP BY department_name
)
SELECT department_name, ROUND(100.0 * before_rate, 2) AS before_rate,
       ROUND(100.0 * after_rate, 2) AS after_rate,
       ROUND(100.0 * (after_rate - before_rate), 2) AS improvement_points,
       DENSE_RANK() OVER (ORDER BY after_rate - before_rate DESC) AS improvement_rank
FROM changes
ORDER BY improvement_rank;

-- Q20. Which requests contain unusual event sequences?
SELECT request_id, department_name, amount, purchase_type,
       observed_path, drift_score, cycle_time_hours
FROM v_request_analysis
WHERE has_unusual_sequence = 1
ORDER BY drift_score DESC, amount DESC;

-- Q21. How does alignment change month by month?
SELECT strftime('%Y-%m', request_date) AS month,
       COUNT(*) AS requests,
       ROUND(100.0 * AVG(aligned), 2) AS alignment_rate,
       ROUND(AVG(drift_score), 2) AS average_drift_score
FROM v_request_analysis
GROUP BY strftime('%Y-%m', request_date)
ORDER BY month;

-- Q22. Where are Security-review violations concentrated?
SELECT ra.department_name, ra.purchase_type,
       COUNT(DISTINCT rv.request_id) AS violated_requests,
       ROUND(SUM(rv.amount_at_risk), 2) AS affected_value
FROM rule_violations rv
JOIN v_request_analysis ra ON ra.request_id = rv.request_id
WHERE rv.rule_id IN ('RULE-004', 'RULE-014')
GROUP BY ra.department_name, ra.purchase_type
ORDER BY violated_requests DESC;

-- Q23. Which workflow variants account for most critical violations?
WITH variant_critical AS (
    SELECT ra.observed_path, COUNT(DISTINCT ra.request_id) AS requests,
           SUM(ra.critical_violation_count) AS critical_violations
    FROM v_request_analysis ra
    WHERE ra.critical_violation_count > 0
    GROUP BY ra.observed_path
)
SELECT observed_path, requests, critical_violations,
       ROUND(100.0 * critical_violations / SUM(critical_violations) OVER (), 2) AS share_pct,
       ROUND(100.0 * SUM(critical_violations) OVER (ORDER BY critical_violations DESC ROWS UNBOUNDED PRECEDING)
             / SUM(critical_violations) OVER (), 2) AS cumulative_share_pct
FROM variant_critical
ORDER BY critical_violations DESC
LIMIT 20;

-- Q24. Which common paths create the longest cycle times?
SELECT observed_path, COUNT(*) AS requests,
       ROUND(AVG(cycle_time_hours), 2) AS average_cycle_hours,
       ROUND(AVG(drift_score), 2) AS average_drift_score
FROM v_request_analysis
GROUP BY observed_path
HAVING COUNT(*) >= 20
ORDER BY average_cycle_hours DESC
LIMIT 15;

-- Q25. How do the legacy and new applications compare after go-live?
SELECT source_system, COUNT(*) AS requests,
       ROUND(100.0 * AVG(aligned), 2) AS alignment_rate,
       ROUND(AVG(drift_score), 2) AS average_drift_score,
       ROUND(100.0 * AVG(has_unusual_sequence), 2) AS unusual_sequence_rate
FROM v_request_analysis
WHERE system_period = 'After update'
GROUP BY source_system
ORDER BY alignment_rate DESC;

-- Q26. Does transaction value correlate with process drift?
WITH value_bands AS (
    SELECT *, CASE
        WHEN amount < 1000 THEN '1. Under $1K'
        WHEN amount <= 10000 THEN '2. $1K-$10K'
        WHEN amount <= 25000 THEN '3. $10K-$25K'
        WHEN amount <= 50000 THEN '4. $25K-$50K'
        ELSE '5. Above $50K' END AS amount_band
    FROM v_request_analysis
)
SELECT amount_band, COUNT(*) AS requests,
       ROUND(100.0 * AVG(aligned), 2) AS alignment_rate,
       ROUND(AVG(drift_score), 2) AS average_drift_score,
       ROUND(AVG(cycle_time_hours), 2) AS average_cycle_hours
FROM value_bands
GROUP BY amount_band
ORDER BY amount_band;
