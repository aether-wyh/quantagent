from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import numpy as np

from quanta_agents.factor_campaign.protocol import default_protocol, validate_protocol
from quanta_agents.factor_campaign.candidates import expand, merge_catalog, execution_queue
from quanta_agents.factor_campaign.selection import annual_floor, descriptive_pass, version_decision, memberships
from quanta_agents.factor_campaign.campaign import Campaign


class ControllerTests(unittest.TestCase):
    def test_frozen_metrics_cannot_be_changed_by_revision(self):
        cfg = default_protocol(".")
        for field, value in [("single_factor_threshold_strict", .049), ("evaluation_years", [2019, 2020]),
                             ("numeric_after_2024_allowed", True), ("year_tail_purge", 5)]:
            changed = deepcopy(cfg); changed[field] = value
            with self.assertRaises(ValueError):
                validate_protocol(changed)

    def test_noise_cannot_pass_by_dropping_its_bad_year(self):
        rows = [{"year": y, "mean_pearson_ic": .06, "valid_days": 230, "evaluation_coverage": .99} for y in range(2019, 2025)]
        report = {"annual": rows}
        self.assertTrue(descriptive_pass(report))
        rows[2]["mean_pearson_ic"] = -.02
        self.assertFalse(descriptive_pass(report))
        self.assertEqual(annual_floor(report), -.02)
        rows.pop(2)
        self.assertFalse(descriptive_pass(report))
        self.assertIsNone(annual_floor(report))

    def test_exact_threshold_is_failure_and_combo_cannot_use_factor_threshold(self):
        rows = [{"year": y, "mean_pearson_ic": .05, "valid_days": 230, "evaluation_coverage": .99} for y in range(2019, 2025)]
        self.assertFalse(descriptive_pass({"annual": rows}))
        for row in rows:
            row["mean_pearson_ic"] = .07
        self.assertFalse(descriptive_pass({"annual": rows}, "combination"))

    def test_caps_trigger_review_not_scientific_success(self):
        b = default_protocol(".")["budget"]
        self.assertEqual(version_decision({"numeric_wall_seconds": 21600}, b), "review_incomplete_scale")
        self.assertEqual(version_decision({"primary_evaluated": 300, "combinations_evaluated": 200, "plateau_extensions": 2}, b), "review_completed_scale")
        self.assertEqual(version_decision({"primary_evaluated": 299, "combinations_evaluated": 200, "plateau_extensions": 2}, b), "complete_minimum")

    def test_control_and_invalid_attempts_not_inflated(self):
        family = {"family_id": "a", "expression_template": "pct_change(close,{w})",
                  "parameters": [{"name": "w", "values": [5, 10]}], "mechanism": "reversal",
                  "controls": [{"name": "same", "expression_template": "pct_change(close,{w})"}], "parents": []}
        rows, attempts = expand([family], origin={"test": True})
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(attempts), 4)
        merged, duplicate = merge_catalog(rows, rows)
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(duplicate), 2)
        bad = deepcopy(family); bad["expression_template"] = "future_return"
        rejected, attempts = expand([bad], origin={})
        self.assertEqual(sum(r["origin"] == "new" for r in rejected), 0)
        self.assertEqual(sum(r["status"] == "implementation_rejected" for r in attempts), 2)

    def test_membership_quality_is_training_only(self):
        rows = [{"factor_id": str(i), "roles": ["risk" if i == 0 else "return"]} for i in range(8)]
        reports = {str(i): {"direction": 1, "direction_fit": {"raw_train_mean_pearson_ic": (i + 1) / 100}, "annual": [{"year": 2024, "mean_pearson_ic": 1000 if i == 0 else -1}]} for i in range(8)}
        signatures = {str(i): np.random.default_rng(i).normal(size=500) for i in range(8)}
        first = memberships(rows, reports, signatures, sizes=(4,))
        for report in reports.values():
            report["annual"][0]["mean_pearson_ic"] *= -1
        self.assertEqual(first, memberships(rows, reports, signatures, sizes=(4,)))
        self.assertEqual(first[0]["feature_ids"], ("4", "5", "6", "7"))
        self.assertIn("0", first[2]["feature_ids"])

    def test_mixed_execution_queue_cannot_starve_old_parent_search(self):
        rows = []
        for origin, route, count in (("reference", "reference", 46), ("new", "structure", 300), ("new", "old_parent_window", 300)):
            for i in range(count):
                rows.append({"factor_id": route + str(i), "family_id": route + str(i % 10),
                             "origin": origin, "route": route, "controls": []})
        first = execution_queue(rows)[:300]
        self.assertEqual(sum(r["origin"] == "reference" for r in first), 46)
        self.assertEqual(sum(r["route"] == "old_parent_window" for r in first), 127)
        self.assertEqual(sum(r["route"] == "structure" for r in first), 127)

    def test_redundancy_pool_suppresses_twins_unless_actual_increment_passes(self):
        from quanta_agents.factor_campaign.selection import factor_pool
        rows = [{"factor_id": str(i), "origin": "new", "roles": ["return"]} for i in range(4)]
        reports = {str(i): {"direction_fit": {"raw_train_mean_pearson_ic": .1 - i * .01}} for i in range(4)}
        reports["1"]["high_correlation_ids"] = ["0"]
        chosen = factor_pool(rows, reports, maximum=3)
        self.assertNotIn("1", {r["factor_id"] for r in chosen})
        reports["1"].update(complementarity_passed=True, complementarity_delta=.005)
        chosen = factor_pool(rows, reports, maximum=3)
        self.assertIn("1", {r["factor_id"] for r in chosen})


if __name__ == "__main__":
    unittest.main()
