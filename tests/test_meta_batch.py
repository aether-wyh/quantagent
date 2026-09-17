from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from quanta_agents.meta import batch


class FakeHTTP:
    """In-memory HTTP responses with explicit lost-response injection; no models."""
    def __init__(self):
        self.health = {"ok": True, "model": batch.MODEL, "effort": batch.EFFORT,
                       "source_hash": "a" * 64, "active_run": None}
        self.source = {"id": "source-1", "status": "completed", "mode": "live",
                       "config": {"case_type": "ashare", "model": batch.MODEL, "effort": batch.EFFORT},
                       "steps": {"meta_proposal": {
            "name": "frozen method", "research_instructions": "Test competing explanations before choosing an experiment."}}}
        self.runs = {}
        self.posts = []
        self.gets = []
        self.lose_response = False
        self.drop_before_create = False

    def get(self, path):
        self.gets.append(path)
        if path == "/api/health":
            return copy.deepcopy(self.health)
        if path == "/api/runs/source-1":
            return copy.deepcopy(self.source)
        if path == "/api/runs":
            return {"runs": [{"id": k, "request_key": v["request_key"]} for k, v in self.runs.items()]}
        return copy.deepcopy(self.runs[path.removeprefix("/api/runs/")])

    def post(self, path, body):
        self.posts.append((path, copy.deepcopy(body)))
        if path.endswith("/control"):
            run_id = path.split("/")[3]
            self.runs[run_id]["status"] = "cancelled"
            return {"ok": True}
        assert path == "/api/runs"
        if self.drop_before_create:
            raise TimeoutError("request delivery unknown")
        run_id = f"run-{len(self.runs) + 1}"
        frozen = copy.deepcopy(self.source["steps"]["meta_proposal"])
        frozen["source_run_id"] = "source-1"
        self.runs[run_id] = {"id": run_id, "status": "running", "mode": body["mode"],
            "request_key": body["request_key"], "phase": "prepare", "elapsed_seconds": 1.0,
            "last_error": None, "calls": [], "usage": {"reported_total_tokens": 0, "unknown_calls": 0, "is_partial": False},
            "config": {"model": batch.MODEL, "effort": batch.EFFORT,
                       "source_manifest": {"hash": self.health["source_hash"]}, "case_type": "ashare",
                       "case_config": {"task": body["task"]}, "evaluation_split": body["evaluation_split"],
                       "only_architecture": body["only_architecture"],
                       "research_calls_per_architecture": body["research_calls"], "frozen_candidate": frozen}}
        if self.lose_response:
            raise TimeoutError("server committed but response was lost")
        return {"run_id": run_id}

    def finish(self, run_id="run-1", *, status="completed", tokens=100, score=0.5):
        run = self.runs[run_id]
        run.update(status=status, phase="finish", elapsed_seconds=25.0,
                   calls=[{"status": "completed", "usage": {"input_tokens": tokens - 10, "output_tokens": 10,
                                                             "cached_input_tokens": 20, "reasoning_output_tokens": 5},
                           "receipt": {"response": {"ok": True}}}],
                   usage={"reported_total_tokens": tokens, "unknown_calls": 0, "is_partial": False})
        if status == "completed":
            arm = run["config"]["only_architecture"]
            run["comparison"] = {"arm_results": {arm: {
                "split": "development", "score": score, "metrics": {"sharpe_ratio": score, "max_ddpercent": -0.12},
                "execution_valid": False}}}


@pytest.fixture
def configured(tmp_path):
    api = FakeHTTP()
    plan = batch.create_plan("http://127.0.0.1:8999", "source-1", tmp_path, client=api)
    return tmp_path, api, plan


def test_plan_is_frozen_balanced_and_starts_no_runs(configured):
    root, api, plan = configured
    assert not api.posts
    assert len(plan["entries"]) == 8
    assert [e["architecture"] for e in plan["entries"]] == ["baseline", "candidate", "candidate", "baseline"] * 2
    assert all(e["request"]["evaluation_split"] == "development" for e in plan["entries"])
    assert all(e["request"]["research_calls"] == 12 for e in plan["entries"])
    assert plan["model"] == batch.MODEL and plan["effort"] == batch.EFFORT
    assert "not a controllable model seed" in plan["repeat_meaning"]
    assert len({e["request_key"] for e in plan["entries"]}) == 8
    before = (root / "plan.json").read_bytes()
    report = batch.tick(root, client=api)
    assert len(api.posts) == 1 and report["status"] == "running"
    assert (root / "plan.json").read_bytes() == before
    with pytest.raises(FileExistsError):
        batch.create_plan("http://127.0.0.1:8999", "source-1", root, client=api)


def test_plan_rejects_unregistered_task_and_scales_call_reservation(tmp_path):
    api = FakeHTTP()
    with pytest.raises(ValueError, match="registered task"):
        batch.create_plan("http://127.0.0.1:8999", "source-1", tmp_path / "unknown",
                          tasks=["invented_task"], client=api)
    with pytest.raises(ValueError, match="reservations exceed"):
        batch.create_plan("http://127.0.0.1:8999", "source-1", tmp_path / "too_large", calls=18, client=api)
    plan = batch.create_plan("http://127.0.0.1:8999", "source-1", tmp_path / "bounded",
                             tasks=["relative_strength"], calls=18, client=api)
    assert plan["limits"]["reserve_tokens_per_entry"] == 1_500_000
    assert len(plan["entries"]) == 4 and not api.posts


@pytest.mark.parametrize("field,value", [("status", "running"), ("mode", "fixture"),
                                         ("case_type", "synthetic"), ("model", "other"), ("effort", "high")])
def test_source_must_be_completed_live_ashare_with_frozen_model(tmp_path, field, value):
    api = FakeHTTP()
    target = api.source if field in {"status", "mode"} else api.source["config"]
    target[field] = value
    with pytest.raises(ValueError, match="completed live A-share"):
        batch.create_plan("http://127.0.0.1:8999", "source-1", tmp_path, client=api)
    assert not api.posts and not (tmp_path / "plan.json").exists()


def test_restart_monitor_does_not_repeat_post(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    for _ in range(3):
        report = batch.tick(root, client=api)
    assert len(api.posts) == 1
    assert report["current_run_id"] == "run-1"
    assert report["counts"]["planned"] == 8 and report["counts"]["not_started"] == 7


def test_creation_timeout_after_commit_recovers_by_key_without_post(configured):
    root, api, _ = configured
    api.lose_response = True
    first = batch.tick(root, client=api)
    assert first["status"] == "attention"
    assert first["usage"]["is_partial"] and first["usage"]["reserved_tokens"] == 1_000_000
    second = batch.tick(root, client=api)
    assert second["current_run_id"] == "run-1"
    assert second["status"] == "running"
    assert len(api.posts) == 1


def test_creation_timeout_without_ledger_match_never_reposts(configured):
    root, api, _ = configured
    api.drop_before_create = True
    batch.tick(root, client=api)
    for _ in range(3):
        report = batch.tick(root, client=api)
    assert report["status"] == "attention"
    assert len(api.posts) == 1
    assert not api.runs
    assert report["usage"]["unknown_entries"] == 1
    assert report["entries"][0]["known_tokens"] is None


def test_crash_after_intent_before_ack_reconciles_existing_key(configured):
    root, api, plan = configured
    state = json.loads((root / "state.json").read_text())
    state["entries"][0].update(status="creating", post_attempted=True)
    (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
    api.post("/api/runs", plan["entries"][0]["request"])
    report = batch.tick(root, client=api)
    assert report["current_run_id"] == "run-1" and len(api.posts) == 1


def test_known_failed_first_arm_remains_in_denominator_and_other_arm_starts(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.finish(status="failed")
    observed = batch.tick(root, client=api)
    assert observed["counts"]["failed"] == 1
    assert len(api.posts) == 1
    next_report = batch.tick(root, client=api)
    assert len(api.posts) == 2
    assert api.posts[-1][1]["only_architecture"] == "candidate"
    assert len(next_report["entries"]) == 8
    assert next_report["entries"][0]["status"] == "failed"
    assert next_report["usage"]["known_tokens"] == 100


def test_cancel_stops_entire_batch_and_retains_future_members(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.finish(status="cancelled")
    report = batch.tick(root, client=api)
    assert report["status"] == "cancelled"
    batch.tick(root, client=api)
    assert len(api.posts) == 1
    assert report["counts"]["not_started"] == 7


def test_pause_waits_and_does_not_resume_or_create_another_run(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.runs["run-1"]["status"] = "paused"
    report = batch.tick(root, client=api)
    assert report["status"] == "paused"
    batch.tick(root, client=api)
    assert len(api.posts) == 1
    api.runs["run-1"]["status"] = "running"
    assert batch.tick(root, client=api)["status"] == "running"


def test_pause_with_inflight_usage_keeps_waiting_with_reservation(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.runs["run-1"].update(status="paused", calls=[{"status": "running", "usage": None}],
                            usage={"reported_total_tokens": 0, "unknown_calls": 1, "is_partial": True})
    report = batch.tick(root, client=api)
    assert report["status"] == "paused" and report["usage"]["is_partial"]
    assert report["usage"]["reserved_tokens"] == 1_000_000 and len(api.posts) == 1


@pytest.mark.parametrize("run_status,expected", [("pausing", "paused"), ("cancelling", "cancelling")])
def test_transient_controls_wait_for_existing_call(configured, run_status, expected):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.runs["run-1"].update(status=run_status, calls=[{"status": "running", "usage": None}],
                            usage={"reported_total_tokens": 0, "unknown_calls": 1, "is_partial": True})
    report = batch.tick(root, client=api)
    assert report["status"] == expected
    assert report["usage"]["is_partial"] and len(api.posts) == 1


@pytest.mark.parametrize("field", ["source", "instructions"])
def test_frozen_service_or_proposal_change_stops_before_creation(configured, field):
    root, api, _ = configured
    if field == "source":
        api.health["source_hash"] = "b" * 64
    else:
        api.source["steps"]["meta_proposal"]["research_instructions"] += " changed"
    report = batch.tick(root, client=api)
    assert report["status"] == "frozen_mismatch" and not api.posts
    assert batch.tick(root, client=api)["status"] == "frozen_mismatch"


def test_unknown_settled_usage_stops_instead_of_counting_zero(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.runs["run-1"].update(status="failed", calls=[{"status": "failed", "usage": None}],
                            usage={"reported_total_tokens": 0, "unknown_calls": 1, "is_partial": True})
    report = batch.tick(root, client=api)
    assert report["status"] == "attention"
    assert report["usage"]["is_partial"] and report["usage"]["reserved_tokens"] == 1_000_000
    batch.tick(root, client=api)
    assert len(api.posts) == 1


def test_normal_inflight_unknown_usage_is_monitored_with_reservation(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.runs["run-1"].update(calls=[{"status": "running", "usage": None}],
                            usage={"reported_total_tokens": 0, "unknown_calls": 1, "is_partial": True})
    report = batch.tick(root, client=api)
    assert report["status"] == "running"
    assert report["usage"]["is_partial"] and report["usage"]["reserved_tokens"] == 1_000_000


def test_uncertain_call_stops_even_if_usage_is_known(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.finish(status="failed")
    api.runs["run-1"]["calls"][0]["status"] = "uncertain"
    report = batch.tick(root, client=api)
    assert report["status"] == "attention"
    assert len(api.posts) == 1


def test_insufficient_next_entry_reservation_stops(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    api.finish(tokens=7_500_000)
    batch.tick(root, client=api)
    report = batch.tick(root, client=api)
    assert report["status"] == "budget_exceeded"
    assert len(api.posts) == 1


def test_wall_limit_cancels_own_active_run_once_and_reconciles_receipt(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    batch.tick(root, client=api)
    state = json.loads((root / "state.json").read_text())
    state["started_at"] = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
    report = batch.tick(root, client=api)
    assert report["status"] == "budget_exceeded"
    assert api.posts[-1] == ("/api/runs/run-1/control", {"action": "cancel"})
    api.finish(status="cancelled", tokens=250)
    reconciled = batch.tick(root, client=api)
    assert len(api.posts) == 2
    assert reconciled["usage"]["known_tokens"] == 250
    assert reconciled["status"] == "budget_exceeded"


def test_wall_limit_cancels_acknowledged_run_before_first_observation(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    state = json.loads((root / "state.json").read_text())
    state["started_at"] = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
    assert batch.tick(root, client=api)["status"] == "budget_exceeded"
    assert api.posts[-1] == ("/api/runs/run-1/control", {"action": "cancel"})


def test_inconsistent_usage_after_known_observation_marks_report_partial(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    batch.tick(root, client=api)
    api.runs["run-1"]["usage"]["reported_total_tokens"] = 999
    report = batch.tick(root, client=api)
    assert report["status"] == "attention"
    assert report["usage"]["is_partial"] and report["usage"]["unknown_entries"] == 1
    assert report["usage"]["reserved_tokens"] == 1_000_000
    assert len(api.posts) == 1


def test_other_active_worker_is_not_interrupted(configured):
    root, api, _ = configured
    api.health["active_run"] = "unrelated-user-run"
    report = batch.tick(root, client=api)
    assert report["status"] == "waiting" and not api.posts


def test_reports_all_entries_and_never_promotes_high_development_sharpe(configured):
    root, api, _ = configured
    for index in range(1, 9):
        batch.tick(root, client=api)
        api.finish(f"run-{index}", score=1.5)
        report = batch.tick(root, client=api)
    assert report["status"] == "completed"
    assert report["counts"]["completed"] == 8
    assert report["usage"]["known_tokens"] == 800
    assert not report["promotion"] and not report["formal_target_success"]
    assert all(e["development_sharpe_gt_1"] and not e["execution_valid"] and not e["formal_target_success"] for e in report["entries"])
    assert (root / "report.md").read_text(encoding="utf-8").count("entry_") == 8


def test_plan_tampering_and_remote_urls_fail_closed(configured):
    root, api, _ = configured
    plan = json.loads((root / "plan.json").read_text())
    plan["research_calls"] = 18
    (root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        batch.tick(root, client=api)
    assert not api.posts
    with pytest.raises(ValueError, match="localhost"):
        batch.HTTPClient("https://example.com")


def test_missing_state_never_resets_paid_creation_history(configured):
    root, api, _ = configured
    batch.tick(root, client=api)
    (root / "state.json").unlink()
    with pytest.raises(ValueError, match="state is missing"):
        batch.tick(root, client=api)
    assert len(api.posts) == 1


def test_batch_lock_prevents_two_dispatchers(configured):
    root, api, _ = configured
    with batch.BatchLock(root):
        with pytest.raises(RuntimeError, match="another dispatcher"):
            batch.tick(root, client=api)
    assert not api.posts
