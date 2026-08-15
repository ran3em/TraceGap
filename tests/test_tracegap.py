from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path

import pandas as pd

from src.change_simulator import simulate_finance_threshold
from src.config import DB_PATH, PROCESSED_DIR, RAW_DIR
from src.rule_engine import applicable_rule_ids


class TraceGapTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.requests = pd.read_csv(PROCESSED_DIR / "requests_enriched.csv", parse_dates=["request_date"])
        cls.processes = pd.read_csv(PROCESSED_DIR / "process_instances.csv")
        cls.violations = pd.read_csv(PROCESSED_DIR / "rule_violations.csv")
        cls.events = pd.read_csv(RAW_DIR / "event_log.csv", parse_dates=["event_timestamp"])
        cls.patterns = pd.read_csv(PROCESSED_DIR / "threshold_patterns.csv", parse_dates=["first_date", "last_date"])
        cls.metrics = json.loads((PROCESSED_DIR / "metrics.json").read_text(encoding="utf-8"))

    def test_dataset_scale_and_uniqueness(self) -> None:
        self.assertEqual(len(self.requests), 8_500)
        self.assertGreaterEqual(len(self.events), 30_000)
        self.assertLessEqual(len(self.events), 50_000)
        self.assertEqual(self.requests.request_id.nunique(), len(self.requests))
        self.assertEqual(self.events.event_id.nunique(), len(self.events))

    def test_rule_catalog_has_eighteen_rules(self) -> None:
        rules = pd.read_csv(RAW_DIR / "business_rules.csv")
        self.assertEqual(len(rules), 18)
        self.assertEqual(rules.rule_id.nunique(), 18)
        self.assertTrue({"Low", "Medium", "High", "Critical"}.issuperset(rules.severity.unique()))

    def test_process_reconstruction_matches_event_order(self) -> None:
        sample_ids = self.processes.sample(50, random_state=17).request_id
        processes = self.processes.set_index("request_id")
        for request_id in sample_ids:
            expected = self.events[self.events.request_id == request_id].sort_values("event_timestamp").activity.tolist()
            self.assertEqual(json.loads(processes.loc[request_id, "actual_steps"]), expected)

    def test_effective_dated_travel_rule(self) -> None:
        before = pd.Series({"request_date": pd.Timestamp("2025-06-30"), "purchase_type": "Travel", "amount": 6_000, "approved_vendor": True, "vendor_risk": "Low", "contract_required": False, "country": "United States", "final_status": "Paid", "urgency": "Standard", "exception_count": 0})
        after = before.copy()
        after.request_date = pd.Timestamp("2025-07-01")
        self.assertNotIn("RULE-016", applicable_rule_ids(before))
        self.assertIn("RULE-016", applicable_rule_ids(after))

    def test_drift_score_is_bounded_and_explainable(self) -> None:
        component_sum = self.processes[["violation_points", "ordering_points", "rework_points", "exception_points", "rare_path_points"]].sum(axis=1).clip(upper=100)
        self.assertTrue(self.processes.drift_score.between(0, 100).all())
        self.assertTrue((component_sum == self.processes.drift_score).all())
        self.assertTrue((self.processes.loc[self.processes.aligned.astype(bool), "violation_count"] == 0).all())

    def test_threshold_patterns_meet_indicator_definition(self) -> None:
        self.assertEqual(len(self.patterns), 12)
        request_index = self.requests.set_index("request_id")
        for row in self.patterns.itertuples():
            ids = [item.strip() for item in row.request_ids.split(",")]
            cluster = request_index.loc[ids]
            self.assertGreaterEqual(len(cluster), 3)
            self.assertTrue(cluster.amount.between(8_800, 10_000, inclusive="left").all())
            self.assertEqual(cluster.employee_id.nunique(), 1)
            self.assertEqual(cluster.vendor_id.nunique(), 1)
            self.assertLessEqual((cluster.request_date.max() - cluster.request_date.min()).days, 21)
            self.assertGreater(cluster.amount.sum(), 10_000)

    def test_simulation_reconciles_population(self) -> None:
        result = simulate_finance_threshold(self.requests, 10_000, 5_000)
        expected = int(((self.requests.amount > 5_000) & (self.requests.amount <= 10_000)).sum())
        self.assertEqual(result["additional_reviews"], expected)
        self.assertEqual(result["net_workload_change"], expected)
        self.assertAlmostEqual(result["affected_pct"], expected / len(self.requests) * 100)

    def test_governed_metrics_reconcile(self) -> None:
        summary = self.metrics["summary"]
        self.assertAlmostEqual(summary["process_alignment_rate"], self.processes.aligned.mean() * 100, places=2)
        self.assertAlmostEqual(summary["average_process_drift_score"], self.processes.drift_score.mean(), places=2)
        self.assertAlmostEqual(summary["median_approval_cycle_time_hours"], self.processes.cycle_time_hours.median(), places=2)
        self.assertEqual(summary["total_violations"], len(self.violations))

    def test_database_integrity_and_analysis_sql(self) -> None:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM purchase_requests").fetchone()[0], 8_500)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM workflow_events").fetchone()[0], len(self.events))
            sql = (Path(__file__).resolve().parents[1] / "sql" / "analysis.sql").read_text(encoding="utf-8")
            connection.executescript(sql)


if __name__ == "__main__":
    unittest.main()
