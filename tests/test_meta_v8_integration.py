"""Generated execution and protocol integration; no market data or real gateway."""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v7.controller import V7ResearchKernel
from quanta_agents.meta_v7.protocol import build_context, validate_action
from quanta_agents.research_kernel.store import serial
from test_meta_v7_controller import initialize, factors_done, strategy


def setup_v8(tmp_path):
    _, panel, config = initialize(tmp_path, study="old_fixture")
    config = {**config, "study_id": "v8_fixture", "research_profile": "v8"}
    kernel = V7ResearchKernel(tmp_path / "v8_fixture")
    kernel.initialize(config, panel)
    factors_done(kernel, panel, ["F1", "weak"])
    batch = kernel.submit_batch([strategy()], controls=[])
    kernel.execute_pending(panel)
    parent = batch["attempts"][0]["run_id"]
    plan = {"parent_run_id": parent, "allowed_paths": ["/allocation/top_n"],
            "hypothesis": "Concentrating the same ranking changes holdings breadth.",
            "falsifier": "No improvement at the same cost and cap policy."}
    return kernel, panel, batch["batch_id"], parent, plan


def action(kind, payload):
    return {"action": kind, "reason": "Generated integration contract", "payload_json": serial(payload)}


def test_bound_revision_survives_restart_and_action_recovery_without_duplicate(tmp_path):
    kernel, panel, batch, parent, plan = setup_v8(tmp_path)
    kernel.apply_action(action("review_batch", {"batch_id": batch, "verdict": "revise",
        "conclusion": "Test only breadth; retain score, caps and calendar.", "revision_plan": plan}))
    original = json.loads(kernel.store.rows("SELECT spec FROM runs WHERE id=?", (parent,))[0]["spec"])
    context = build_context(kernel)
    assert context["packet"]["state"]["version"] == "meta_v8.0.0-dev"
    assert parent in context["prompt"] and "allowed_paths" in context["prompt"]
    kernel = V7ResearchKernel(kernel.root)
    response = action("revise_batch", {"parent_run_id": parent, "review_batch_id": batch,
        "changes": [{"path": "/allocation/top_n", "value": 2}], "controls": []})
    result = kernel.apply_action(response, action_id="fixture_revision_call")
    count = kernel.status()["attempts"]
    assert kernel.apply_action(response, action_id="fixture_revision_call") == result
    assert kernel.status()["attempts"] == count
    assert "revision" in result
    child = json.loads(kernel.store.rows("SELECT spec FROM runs WHERE id=?",
        (result["attempts"][0]["run_id"],))[0]["spec"])["strategy"]
    assert child["allocation"]["top_n"] == 2
    assert child["score"] == original["strategy"]["score"]
    for key in original["strategy"]["allocation"]:
        if key != "top_n":
            assert child["allocation"][key] == original["strategy"]["allocation"][key]
    kernel.execute_pending(panel)
    assert kernel.pending() == 0
    assert json.loads(kernel.store.rows("SELECT spec FROM runs WHERE id=?", (parent,))[0]["spec"]) == original


def test_review_requires_plan_and_free_proposal_cannot_bypass_it(tmp_path):
    kernel, _, batch, parent, plan = setup_v8(tmp_path)
    with pytest.raises((ValueError, TypeError)):
        kernel.review_batch(batch, "revise", "Change one thing")
    kernel.review_batch(batch, "revise", "Change breadth", revision_plan=plan)
    count = kernel.status()["attempts"]
    with pytest.raises(ValueError, match="revise_batch"):
        kernel.submit_batch([strategy("unbound")])
    with pytest.raises(ValueError):
        kernel.apply_action(action("revise_batch", {"parent_run_id": parent, "review_batch_id": batch,
            "changes": [{"path": "/allocation/gross_exposure", "value": .8}]}))
    assert kernel.status()["attempts"] == count


def test_partial_revision_write_recovers_without_registering_another_attempt(tmp_path, monkeypatch):
    kernel, _, batch, parent, plan = setup_v8(tmp_path)
    kernel.review_batch(batch, "revise", "Change breadth", revision_plan=plan)
    response = action("revise_batch", {"parent_run_id": parent, "review_batch_id": batch,
        "changes": [{"path": "/allocation/top_n", "value": 2}]})
    original_event = kernel.store.event
    def interrupted(db, kind, payload):
        if kind == "revision_registered":
            raise RuntimeError("fixture crash after submission")
        return original_event(db, kind, payload)
    monkeypatch.setattr(kernel.store, "event", interrupted)
    with pytest.raises(RuntimeError, match="fixture crash"):
        kernel.apply_action(response, action_id="interrupted_fixture")
    saved = json.loads(kernel.store.rows("SELECT result FROM actions WHERE id=?", ("interrupted_fixture",))[0]["result"])
    assert "revision" not in saved
    attempts = kernel.status()["attempts"]
    monkeypatch.setattr(kernel.store, "event", original_event)
    recovered = kernel.apply_action(response, action_id="interrupted_fixture")
    assert "revision" in recovered
    assert recovered["batch_id"] == saved["batch_id"]
    assert kernel.status()["attempts"] == attempts
    assert kernel.apply_action(response, action_id="interrupted_fixture") == recovered


def test_reject_keeps_new_mechanism_route_open(tmp_path):
    kernel, _, batch, _, _ = setup_v8(tmp_path)
    kernel.review_batch(batch, "reject", "Retain the failure; start a distinct conditional hypothesis.")
    result = kernel.submit_batch([strategy("different mechanism", "weak")])
    assert result["attempts"][0]["status"] == "queued"


def test_new_action_envelope_rejects_unknown_and_duplicate_fields():
    with pytest.raises(ValueError):
        validate_action(action("revise_batch", {"parent_run_id": "r", "review_batch_id": "b",
            "changes": [], "arbitrary_python": "pass"}))
    with pytest.raises(ValueError):
        validate_action({"action": "revise_batch", "reason": "fixture",
            "payload_json": '{"parent_run_id":"r","parent_run_id":"s","review_batch_id":"b","changes":[]} '})


def test_old_configuration_retains_v7_and_cannot_change_profile(tmp_path):
    kernel, panel, config = initialize(tmp_path)
    assert kernel.research_profile == "v7"
    assert kernel.status()["version"] == "meta_v7.0.0"
    with pytest.raises(ValueError, match="frozen"):
        kernel.initialize({**config, "research_profile": "v8"}, panel)
    with pytest.raises(ValueError, match="v8"):
        kernel.revise_batch("r", "b", [])


def test_review_context_keeps_used_factor_support(tmp_path):
    kernel, _, _, _, _ = setup_v8(tmp_path)
    context = build_context(kernel)
    factor_packet = context["packet"]["factor_evidence"][0]
    assert "F1" in factor_packet["factors"]
    assert "mean_ic" in serial(factor_packet)
    assert "evidence_support" in factor_packet
