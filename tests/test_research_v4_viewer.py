"""The status file is progress evidence, never worker liveness evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "research_viewer", Path(__file__).resolve().parents[1] / "scripts/serve_research_v3.py"
)
VIEWER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VIEWER)


class ControllerSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "status.json"

    def save(self, **values):
        data = {"stages": [], "observed_at": "2026-09-08T05:00:00+00:00", **values}
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_status_is_reloaded_without_restart(self):
        self.save(new_v4_research_calls=0)
        self.assertEqual(VIEWER.controller_snapshot(self.path)["new_v4_research_calls"], 0)
        self.save(new_v4_research_calls=1)
        self.assertEqual(VIEWER.controller_snapshot(self.path)["new_v4_research_calls"], 1)

    def test_saved_live_claim_is_not_attestation(self):
        self.save(live=True, worker_observation={"live": True})
        result = VIEWER.controller_snapshot(self.path)
        self.assertFalse(result["worker_observation"]["live"])
        self.assertEqual(result["worker_observation"]["status"], "not_configured")

    def test_viewer_cannot_be_counted_as_research_worker(self):
        ident = {"pid": 1, "create_time": 123, "cmdline": ["python", "serve_research_v3.py"]}
        (self.path.parent / "worker.json").write_text(json.dumps(ident), encoding="utf-8")
        self.save(worker_identity_path="worker.json")
        with patch.object(VIEWER.psutil, "Process") as process:
            process.return_value.is_running.return_value = True
            process.return_value.create_time.return_value = ident["create_time"]
            process.return_value.cmdline.return_value = ident["cmdline"]
            self.assertFalse(VIEWER.controller_snapshot(self.path)["worker_observation"]["live"])

    def test_bad_status_returns_visible_error(self):
        self.path.write_text("{partial", encoding="utf-8")
        self.assertIn("error", VIEWER.controller_snapshot(self.path))

    def test_missing_timestamp_is_unknown_age(self):
        self.save(observed_at=None)
        self.assertIsNone(VIEWER.controller_snapshot(self.path)["snapshot_age_seconds"])

    def test_configured_cycle_results_are_loaded_before_v3_history(self):
        report = {"title": "Generated cycle results", "summary": "Audited fixture only",
            "facts": ["No financial acceptance"], "columns": ["Candidate", "Value"],
            "rows": [["A", 12]], "limitations": "Generated test data", "next_step": "Review"}
        summary_path = self.path.parent / "cycle_results.json"
        summary_path.write_text(json.dumps(report), encoding="utf-8")
        self.save(cycle_results_summary_path=str(summary_path))
        result = VIEWER.controller_snapshot(self.path)
        self.assertEqual(result["cycle_results_summary"], report)
        self.assertEqual(result["cycle_results_summary_status"]["status"], "available")
        self.assertLess(VIEWER.PAGE.index('id="cycle-results"'), VIEWER.PAGE.index('<h2>V3 历史研究账</h2>'))

    def test_missing_cycle_results_do_not_reuse_a_saved_result_claim(self):
        self.save(cycle_results_summary_path=str(self.path.parent / "missing.json"),
                  cycle_results_summary={"title": "Stale result must not appear"})
        result = VIEWER.controller_snapshot(self.path)
        self.assertNotIn("cycle_results_summary", result)
        self.assertEqual(result["cycle_results_summary_status"]["status"], "not_available")

    def test_actual_ledger_invalid_final_is_finished_delivery_failure(self):
        from quanta_agents.meta_v3.closing import ClosingPolicy
        from quanta_agents.meta_v3.ledger import Ledger
        ledger = Ledger.create(self.path.parent / 'actual_ledger', tasks={'extension': {}},
            policy=ClosingPolicy(task_calls=1, stage_calls=1),
            deadline_epoch=time.time() + 7200, provenance={'fixture_only': True})
        intent = ledger.reserve('extension', ('submit_research_report',),
            lambda *args: ('Generated viewer fixture; no model call', {'type': 'object'}))
        self.assertEqual(VIEWER.research_snapshot(ledger.root)['state'], '模型调用等待返回')
        receipt = {'response': {'action': 'submit_research_report', 'arguments_json': '{}'},
            'request_identity': {'intent_id': intent['intent_id']},
            'usage': {'input_tokens': 10, 'output_tokens': 10}, 'artifact_sha256': {},
            'engineering_fixture': True}
        ledger.receive_saved(intent['intent_id'], lambda *args, **kwargs: receipt)
        ledger.begin_apply(intent['intent_id'])
        ledger.finish_apply(intent['intent_id'], {'error': 'Generated invalid final schema'},
                            failed=True, final=True)
        result = VIEWER.research_snapshot(ledger.root)
        self.assertEqual(result['tasks'][0]['terminal'], 'invalid_final')
        self.assertIsNone(result['tasks'][0]['final_call'])
        self.assertEqual(result['state'], '终稿交付失败')
        self.assertEqual(result['pending_calls'], 0)
        self.assertEqual(result['known_tokens'], 20)


if __name__ == "__main__":
    unittest.main()
