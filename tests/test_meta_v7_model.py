"""V7 orchestration with fake transport and explicit synthetic stage evidence.

No model, factor engine, account or real market data is executed.  Verified=True
below is a transport fixture, never provider or runtime authenticity evidence.
"""
from copy import deepcopy
import json
from pathlib import Path
import time

import pandas as pd
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v7.controller import V7ResearchKernel
from quanta_agents.meta_v7 import model
from quanta_agents.research_kernel.store import serial, write_json


def action(kind="query_assets", payload=None):
    return {"action": kind, "reason": "synthetic orchestration fixture, no research conclusion",
            "payload_json": json.dumps(payload or {})}


def make_kernel(path, calls=8):
    dates = pd.bdate_range("2019-01-01", "2020-02-28")
    frame = pd.DataFrame(10., index=dates, columns=["synthetic_only"])
    panel = MarketPanel({"open": frame, "close": frame.copy()}, frame.notna(), {"synthetic": True})
    kernel = V7ResearchKernel(path / "study")
    kernel.initialize({"project_root": str(path / "project"), "study_id": "synthetic_study",
        "split_plan": {"train_start": "2019-02-01", "train_end": "2019-12-31",
                       "validation_start": "2020-01-01", "validation_end": "2020-02-28",
                       "max_label_horizon": 20, "embargo_sessions": 0},
        "budget": {"max_model_calls": calls}}, panel)
    kernel.assets.register({"id": "weak", "name": "weak fixture", "expression": "close",
        "roles": ["condition", "interaction"], "source": {"synthetic": True}, "metadata": {}})
    return kernel


def strategy():
    return {"version": 1, "name": "synthetic candidate", "score": {"op": "factor", "id": "weak"},
            "allocation": {"top_n": 1, "max_stock_weight": 1.}}


class FakeGateway:
    def __init__(self, response=None, *, verified=True, error=None, model_name="gpt-6-astra", effort="xhigh", usage=None):
        self.response = action() if response is None else response
        self.verified, self.error, self.model_name, self.effort = verified, error, model_name, effort
        self.usage = {"input_tokens": 11, "output_tokens": 3, "total_tokens": 14} if usage is None else usage
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        receipt = {"model": self.model_name, "effort": self.effort, "response": deepcopy(self.response),
            "usage": deepcopy(self.usage), "runtime_identity": {"verified": self.verified,
                "level": "synthetic_transport_fixture_not_authentication"}, "fixture_only": True}
        folder = Path(kwargs["workdir"])
        write_json(folder / "fixture_receipt.json", receipt)
        write_json(folder / "fixture_response.json", self.response)
        (folder / "fixture_prompt.txt").write_text(kwargs["prompt"], encoding="utf-8")
        if self.error:
            raise self.error
        return receipt


def verifier(monkeypatch, *, verified=None, fail=None):
    from quanta_agents.meta_v6 import gateway
    checks, captures = [], []
    def verify(folder, **kwargs):
        checks.append((folder, kwargs))
        if fail:
            raise fail
        receipt = json.loads((Path(folder) / "fixture_receipt.json").read_text(encoding="utf-8"))
        if verified is not None:
            receipt["runtime_identity"]["verified"] = verified
        return receipt
    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    monkeypatch.setattr(gateway, "capture_saved_session", lambda *args: captures.append(args))
    return checks, captures


def seed_calls(kernel, number):
    with kernel.store.transaction() as db:
        for ordinal in range(number):
            db.execute("INSERT INTO model_calls VALUES (?,?,?,?,?,?,?)", (
                "fixture_prior_" + str(ordinal), "applied", "not_a_real_session", serial(action()),
                serial({"fixture_only": True}), None, time.time()))


def finish_factors(kernel, job_id):
    report = {"scope": {"fixture_only": True}, "factors": {"weak": {"roles": ["condition"],
        "coverage": {"observed_cells": 10, "fraction": 1.}, "horizons": {}, "risk": {}}},
        "correlations": [], "conditions": [], "interactions": [], "limitations": ["Synthetic stage fixture"]}
    eid = kernel.store.put_evidence("synthetic_factor_fixture", report)
    with kernel.store.transaction() as db:
        db.execute("UPDATE factor_jobs SET status='completed',evidence_id=? WHERE id=?", (eid, job_id))
    return eid


def finished_batch(kernel):
    job = kernel.evaluate_factors(["weak"])
    finish_factors(kernel, job["job_id"])
    batch = kernel.submit_batch([strategy()], controls=[])
    finish_batch(kernel, batch)
    return batch


def finish_batch(kernel, batch):
    with kernel.store.transaction() as db:
        for row in batch["attempts"]:
            db.execute("UPDATE attempts SET status='completed' WHERE id=?", (row["id"],))
            db.execute("UPDATE runs SET status='completed' WHERE id=?", (row["run_id"],))
    # No native account is fabricated: this is explicitly marked context data.
    eid = kernel.store.put_evidence("synthetic_paired_context", {"batch_id": batch["batch_id"],
        "arms": [], "fixture_only": True, "financial_execution": False})
    with kernel.store.connect() as db:
        kernel.store.set_meta(db, "batch_evidence:" + batch["batch_id"], eid)


@pytest.mark.parametrize("budget", [2, 3, 8])
def test_exact_call_budget_includes_rejected_final_request_and_never_dispatches_extra(tmp_path, budget):
    kernel = make_kernel(tmp_path, budget)
    fake = FakeGateway()
    for ordinal in range(budget):
        result = model.model_step(kernel, gateway=fake)
        assert result["status"] == ("applied" if ordinal < budget-1 else "action_rejected")
    assert len(fake.calls) == budget
    assert kernel.status()["model_calls"] == budget
    assert model.model_step(kernel, gateway=fake)["status"] in {"stopped", "model_budget_exhausted"}
    assert len(fake.calls) == budget
    assert kernel.status()["stopped"]
    assert json.loads(kernel.store.rows("SELECT usage FROM model_calls ORDER BY created DESC LIMIT 1")[0]["usage"])["total_tokens"] == 14


@pytest.mark.parametrize("state", ["queued", "running"])
def test_numerical_pending_blocks_context_and_paid_transport(tmp_path, monkeypatch, state):
    kernel = make_kernel(tmp_path)
    kernel.evaluate_factors(["weak"])
    with kernel.store.connect() as db:
        db.execute("UPDATE factor_jobs SET status=?", (state,))
    monkeypatch.setattr(model, "build_context", lambda *a, **kw: pytest.fail("pending job must precede context"))
    fake = FakeGateway()
    assert model.model_step(kernel, gateway=fake) == {"status": "pending_numerical_stages", "count": 1}
    assert not fake.calls and kernel.status()["model_calls"] == 0


@pytest.mark.parametrize("options", [{"verified": False}, {"model_name": "another-model"}, {"effort": "low"}])
def test_identity_checked_before_any_action_admission(tmp_path, options):
    kernel = make_kernel(tmp_path)
    fake = FakeGateway(action("evaluate_factors", {"ids": ["weak"]}), **options)
    with pytest.raises(ValueError):
        model.model_step(kernel, gateway=fake)
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    assert row["status"] == "needs_recovery"
    assert kernel.pending() == 0
    assert kernel.store.rows("SELECT * FROM actions") == []
    assert (Path(row["directory"]) / "fixture_response.json").exists()


def test_saved_receipt_recovery_uses_same_ordinal_and_no_second_transport(tmp_path, monkeypatch):
    kernel = make_kernel(tmp_path, 3)
    fake = FakeGateway(action("evaluate_factors", {"ids": ["weak"]}), error=TimeoutError("completion saved"))
    with pytest.raises(TimeoutError):
        model.model_step(kernel, gateway=fake)
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    original = (Path(row["directory"]) / "fixture_response.json").read_bytes()
    checks, captures = verifier(monkeypatch)
    recovered = model.model_step(kernel, gateway=fake)
    assert recovered["call_id"] == row["id"] and recovered["status"] == "applied"
    assert len(fake.calls) == len(checks) == 1 and not captures
    assert kernel.status()["model_calls"] == 1 and kernel.pending() == 1
    repeated = model.recover_model_call(kernel, row["id"])
    assert repeated["result"] == recovered["result"] and kernel.pending() == 1
    assert (Path(row["directory"]) / "fixture_response.json").read_bytes() == original


def test_unknown_completion_blocks_paid_retry_even_with_remaining_budget(tmp_path, monkeypatch):
    kernel = make_kernel(tmp_path, 8)
    fake = FakeGateway(error=TimeoutError("unknown original completion"))
    with pytest.raises(TimeoutError):
        model.model_step(kernel, gateway=fake)
    checks, _ = verifier(monkeypatch, fail=ValueError("saved evidence unavailable"))
    for _ in range(2):
        with pytest.raises(ValueError, match="saved evidence"):
            model.model_step(kernel, gateway=fake)
    assert len(fake.calls) == 1 and len(checks) == 2
    assert kernel.status()["model_calls"] == 1


def test_offline_capture_cannot_admit_if_identity_remains_unknown(tmp_path, monkeypatch):
    kernel = make_kernel(tmp_path)
    fake = FakeGateway(verified=False)
    with pytest.raises(ValueError):
        model.model_step(kernel, gateway=fake)
    checks, captures = verifier(monkeypatch, verified=False)
    with pytest.raises(ValueError, match="identity"):
        model.model_step(kernel, gateway=fake)
    assert len(checks) == 2 and len(captures) == 1 and len(fake.calls) == 1
    assert kernel.store.rows("SELECT * FROM actions") == []


def test_missing_usage_remains_unknown(tmp_path):
    kernel = make_kernel(tmp_path)
    result = model.model_step(kernel, gateway=FakeGateway(usage={}))
    assert result["usage"] == {}
    assert json.loads(kernel.store.rows("SELECT usage FROM model_calls")[0]["usage"]) == {}


@pytest.mark.parametrize("budget", [2, 3, 8])
def test_final_reserved_call_can_review_batch_and_close_without_extra_call(tmp_path, budget):
    kernel = make_kernel(tmp_path, budget)
    batch = finished_batch(kernel)
    seed_calls(kernel, budget-1)
    fake = FakeGateway(action("review_batch", {"batch_id": batch["batch_id"], "verdict": "stop",
        "conclusion": "Synthetic evidence is rejected; no profitability claim."}))
    result = model.model_step(kernel, gateway=fake)
    assert result["status"] == "applied"
    assert kernel.status()["stopped"]
    assert kernel.status()["model_calls"] == budget and len(fake.calls) == 1
    assert len(kernel.store.rows("SELECT * FROM batch_reviews")) == 1


def test_final_call_cannot_freeze_validation_without_review_budget(tmp_path):
    kernel = make_kernel(tmp_path, 3)
    batch = finished_batch(kernel)
    seed_calls(kernel, 2)
    fake = FakeGateway(action("review_batch", {"batch_id": batch["batch_id"], "verdict": "freeze_for_validation",
        "conclusion": "synthetic freeze", "candidate_run_id": batch["attempts"][0]["run_id"]}))
    result = model.model_step(kernel, gateway=fake)
    assert result["status"] == "action_rejected"
    assert kernel.status()["validation_jobs"] == []
    assert kernel.status()["model_calls"] == 3


def test_real_model_action_sequence_closes_only_after_explicit_validation_review(tmp_path):
    kernel = make_kernel(tmp_path, 8)
    fake = FakeGateway(action("evaluate_factors", {"ids": ["weak"]}))
    one = model.model_step(kernel, gateway=fake)
    assert kernel.pending() == 1
    finish_factors(kernel, one["result"]["job_id"])
    fake.response = action("propose_batch", {"specs": [strategy()], "controls": []})
    two = model.model_step(kernel, gateway=fake)
    batch = two["result"]
    finish_batch(kernel, batch)
    fake.response = action("review_batch", {"batch_id": batch["batch_id"], "verdict": "freeze_for_validation",
        "conclusion": "synthetic freeze, validation not yet observed", "candidate_run_id": batch["attempts"][0]["run_id"]})
    three = model.model_step(kernel, gateway=fake)
    job = three["result"]["validation_job_id"]
    assert kernel.pending() == 1 and not kernel.status()["stopped"]
    fake.response = action("review_validation", {"job_id": job, "conclusion": "Synthetic validation does not establish independence."})
    assert model.model_step(kernel, gateway=fake)["status"] == "pending_numerical_stages"
    assert len(fake.calls) == 3
    with kernel.store.connect() as db:
        db.execute("UPDATE validation_jobs SET status='failed',error='synthetic numerical failure' WHERE id=?", (job,))
    four = model.model_step(kernel, gateway=fake)
    assert four["result"]["status"] == "research_closed"
    assert four["result"]["independent_profitability_proven"] is False
    assert kernel.status()["stopped"] and len(fake.calls) == 4


def test_cli_runs_queued_numerics_before_next_model_and_stops_after_failed_job(tmp_path, monkeypatch):
    from quanta_agents.meta_v7 import cli
    kernel = make_kernel(tmp_path, 3)
    kernel.evaluate_factors(["weak"])
    seen = []
    monkeypatch.setattr(cli, "run_supervised", lambda k: seen.append("numerics") or {"job_status": "timed_out"})
    monkeypatch.setattr(model, "model_step", lambda *a, **kw: pytest.fail("pending numerical failure cannot trigger model"))
    result = cli.main(["iterate", "--root", str(kernel.root), "--steps", "3"])
    assert result == [{"job_status": "timed_out"}] and seen == ["numerics"]


def test_external_action_id_does_not_refund_a_model_slot(tmp_path):
    kernel = make_kernel(tmp_path, 2)
    seed_calls(kernel, 1)
    with pytest.raises(ValueError, match="closing"):
        kernel.apply_action(action("evaluate_factors", {"ids": ["weak"]}), action_id="external-not-model-call")
    assert kernel.pending() == 0


def test_final_reject_review_is_settled_without_a_second_iteration(tmp_path):
    kernel = make_kernel(tmp_path, 2)
    batch = finished_batch(kernel)
    seed_calls(kernel, 1)
    fake = FakeGateway(action("review_batch", {"batch_id": batch["batch_id"], "verdict": "reject",
        "conclusion": "Synthetic mechanism rejected, budget consumed."}))
    assert model.model_step(kernel, gateway=fake)["status"] == "applied"
    assert kernel.status()["stopped"]
    assert len(fake.calls) == 1 and kernel.status()["model_calls"] == 2
