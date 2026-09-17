"""Recovery, resource boundaries, lineage roles and isolated-patch failure tests."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_campaign.model import ModelLoop, SCHEMAS
from quanta_agents.factor_campaign.resources import ResourceGuard, CostLedger, GIB
from quanta_agents.factor_campaign.lineage import (LineageRegistry, classify_transformation,
                                                  select_parents, redundancy, build_revision)
from quanta_agents.factor_campaign.revisions import RevisionManager
from quanta_agents.meta_v6.factors import FactorSpec


PROPOSAL = {"kind": "propose", "templates": [], "evidence_ids": [], "rationale": "Synthetic gateway recovery fixture"}


class SyntheticGateway:
    def __init__(self, *, timeout=False, completed=True, interrupt=False):
        self.calls, self.timeout, self.completed, self.interrupt = 0, timeout, completed, interrupt

    def run(self, **kwargs):
        from quanta_agents.meta_v6.gateway import base
        self.calls += 1
        folder = kwargs["workdir"]
        # Check the real pinned gateway's durable intent contract and schema dialect.
        base._intent_binding((folder / "intent.json").read_bytes(),
                             prompt_hash=base._prompt_hash(kwargs["prompt"]), schema=kwargs["schema"])
        base._validate_output(PROPOSAL, kwargs["schema"])
        if self.completed:
            (folder / "synthetic_original.json").write_text(json.dumps(PROPOSAL), encoding="utf-8")
        if self.interrupt:
            raise KeyboardInterrupt("synthetic process interruption")
        if self.timeout:
            raise TimeoutError("model timed out")
        return None


def synthetic_verifier(folder, **kwargs):
    response = json.loads((folder / "synthetic_original.json").read_text(encoding="utf-8"))
    return {"response": response, "model": "gpt-6-astra", "effort": "xhigh",
            "runtime_identity": {"verified": True}, "usage": {"input_tokens": 100, "output_tokens": 30,
            "reasoning_output_tokens": 20, "cached_input_tokens": 10}}


def test_model_preregistration_replay_and_native_schema(tmp_path):
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway()
    first = loop.request("v10.proposal.1", "propose", {"synthetic": True}, gateway=gateway)
    assert first["status"] == "ready"
    second = loop.request("v10.proposal.1", "propose", {"synthetic": True}, gateway=gateway)
    assert second == first and gateway.calls == 1
    with pytest.raises(ValueError, match="changed"):
        loop.request("v10.proposal.1", "propose", {"synthetic": False}, gateway=gateway)
    applications = []
    for _ in range(2):
        outcome = loop.apply_once("v10.proposal.1", lambda response, action_id: applications.append(action_id) or {"ok": True})
    assert applications == ["v10.proposal.1"] and outcome["status"] == "applied"
    costs = loop.cost.summary()
    assert costs["model_calls"] == 1 and costs["known_total_tokens"] == 130
    assert costs["currency_cost"] is None


def test_timeout_saved_completion_recovers_without_second_model_call(tmp_path):
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway(timeout=True)
    result = loop.request("a", "propose", {}, gateway=gateway)
    assert result["status"] == "ready" and gateway.calls == 1
    assert loop.recover("a")["status"] == "ready"
    assert loop.cost.summary()["failed_model_calls"] == 1
    assert loop.cost.summary()["known_total_tokens"] == 130


def test_no_saved_completion_blocks_duplicate_paid_calls(tmp_path):
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway(timeout=True, completed=False)
    assert loop.request("a", "propose", {}, gateway=gateway)["status"] == "waiting"
    assert loop.request("a", "propose", {}, gateway=gateway)["status"] == "waiting"
    assert loop.request("b", "propose", {}, gateway=gateway)["blocker"]["reason"] == "unresolved_previous_model_call"
    assert gateway.calls == 1 and loop.cost.summary()["unknown_usage_calls"] == 1


def test_terminal_no_answer_can_be_released_but_partial_answer_cannot(tmp_path):
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway(timeout=True, completed=False)
    loop.request("a", "propose", {}, gateway=gateway)
    assert loop.release_failed_attempt("a")["status"] == "waiting"
    folder = tmp_path / "model_calls/a"
    (folder / "process_exit.json").write_text(json.dumps({"exit_observed":True,"process_exit_code":1}))
    (folder / "codex_events.jsonl").write_text("")
    (folder / "response.json").write_text("partial answer")
    assert loop.release_failed_attempt("a")["status"] == "waiting"
    # Only the synthetic fixture removes its made-up partial artifact.
    (folder / "response.json").unlink()
    assert loop.release_failed_attempt("a")["status"] == "failed_terminal"
    complete = SyntheticGateway()
    assert loop.request("b", "propose", {}, gateway=complete)["status"] == "ready"
    assert complete.calls == 1 and loop.cost.summary()["model_calls"] == 2


def test_process_interrupt_recovers_and_outbox_replays_stable_id(tmp_path):
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway(interrupt=True)
    with pytest.raises(KeyboardInterrupt):
        loop.request("a", "propose", {}, gateway=gateway)
    recovered = ModelLoop(tmp_path, verifier=synthetic_verifier)
    assert recovered.recover("a")["status"] == "ready"
    committed = {}
    def interrupted_handler(response, action_id):
        committed.setdefault(action_id, {"effect": 1})
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        recovered.apply_once("a", interrupted_handler)
    result = recovered.apply_once("a", lambda response, action_id: committed.setdefault(action_id, {"effect": 2}))
    assert result["application"] == {"effect": 1} and len(committed) == 1


def test_precall_orphan_after_intent_write_is_adopted(tmp_path, monkeypatch):
    from quanta_agents.factor_campaign import model
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway()
    original = model.write_json
    def interrupted(path, value):
        original(path, value)
        if Path(path).name == "intent.json":
            raise KeyboardInterrupt("crash before ledger insertion")
    monkeypatch.setattr(model, "write_json", interrupted)
    with pytest.raises(KeyboardInterrupt):
        loop.request("a", "propose", {}, gateway=gateway)
    assert loop._row("a") is None and gateway.calls == 0
    monkeypatch.setattr(model, "write_json", original)
    assert loop.request("a", "propose", {}, gateway=gateway)["status"] == "ready"
    assert gateway.calls == 1


def test_ambiguous_orphan_does_not_start_a_model(tmp_path):
    loop, gateway = ModelLoop(tmp_path, verifier=synthetic_verifier), SyntheticGateway()
    folder = tmp_path / "model_calls/a"
    folder.mkdir(parents=True)
    (folder / "codex_events.jsonl").write_text("original ambiguous artifact")
    result = loop.request("a", "propose", {}, gateway=gateway)
    assert result["status"] == "waiting" and gateway.calls == 0


@pytest.mark.parametrize("memory,disk,allowed", [(6,10,True),(5.99,10,False),(6,9.99,False),(None,20,False)])
def test_exact_resource_boundaries(tmp_path, memory, disk, allowed):
    guard = ResourceGuard(tmp_path, snapshotter=lambda _: {"available_memory_bytes": memory * GIB if memory else None, "disk_free_bytes": disk * GIB})
    assert guard.check()["allowed"] is allowed
    assert guard.workers_after_calibration()["workers"] == (1 if allowed else 0)


def test_second_worker_requires_calibration_and_peak_headroom(tmp_path):
    guard = ResourceGuard(tmp_path, snapshotter=lambda _: {"available_memory_bytes": 10*GIB, "disk_free_bytes": 20*GIB})
    assert guard.workers_after_calibration()["workers"] == 1
    assert guard.workers_after_calibration({"single_process_completed": True, "worker_peak_private_bytes": GIB})["workers"] == 2
    assert guard.workers_after_calibration({"single_process_completed": True, "worker_peak_private_bytes": 2*GIB})["workers"] == 1


def test_cost_recovery_keeps_failure_unknown_currency_and_deduplicates(tmp_path):
    costs = CostLedger(tmp_path)
    costs.record("a", kind="model_call", failed=True, usage={}, cpu_seconds=1)
    assert costs.summary()["unknown_usage_calls"] == 1
    for _ in range(2):
        costs.record("a", kind="model_call", usage={"input_tokens": 10, "output_tokens": 20, "reasoning_output_tokens": 15})
    costs.record("a", kind="model_call", usage={"input_tokens": None})
    result = costs.summary()
    assert result["model_calls"] == 1 and result["known_total_tokens"] == 30
    assert result["failed_model_calls"] == 1 and result["unknown_usage_calls"] == 0


def test_repeated_execution_measurements_are_new_cost_not_overwrites(tmp_path):
    costs = CostLedger(tmp_path)
    for _ in range(2):
        with costs.measure("same-test", kind="patch_tests"):
            assert costs.summary()["unfinished_measurements"] == 1
    assert costs.summary()["events"] == 2
    assert costs.summary()["unfinished_measurements"] == 0


def test_terminated_numeric_attempt_has_unknown_total_not_fabricated_zero(tmp_path):
    costs = CostLedger(tmp_path)
    costs.record("simulated-killed-attempt", kind="numeric_factor", status="started", cpu_seconds=None,
                 wall_seconds=None, peak_memory_bytes=None)
    report=costs.summary()
    assert report["unfinished_measurements"] == 1 and report["events_without_wall_measurement"] == 1
    assert report["events_without_memory_measurement"] == 1 and report["peak_memory_bytes"] is None


def test_inlined_registered_aggregate_is_combination():
    parents = [{"factor_id": "a", "expression": "pct_change(close,5)"},
               {"factor_id": "b", "expression": "pct_change(close,20)"}]
    result = classify_transformation("0.4 * pct_change(close,5) + 0.6 * pct_change(close,20)", parents)
    assert result["transformation_kind"] == "registered_factor_aggregation"
    assert result["aggregate_members"] == ["a", "b"] and result["acceptance_route"] == "combination"
    result = classify_transformation("pct_change(close,5) * (volume / rolling_mean(volume,20))", parents)
    assert result["acceptance_route"] == "single_factor"


def test_lineage_immutable_definitions_and_value_correlation_separate(tmp_path):
    store = LineageRegistry(tmp_path)
    a = store.register("a", "close / open")
    b = store.register("b", "(close/open)")
    assert a["counts_as_new_definition"] and b["definition_duplicates"] == ["a"]
    inherited = store.register("a", "close/open", origin="inherited", version="V11A")
    assert not inherited["counts_as_new_definition"] and inherited["inherited_definition"]
    assert len(store.export()["sightings"]) == 3
    with pytest.raises(ValueError, match="immutable"):
        store.register("a", "high / low")
    rng = np.random.default_rng(42)
    x = pd.DataFrame(rng.normal(size=(220,110)))
    r = redundancy(x, 2*x)
    assert r["highly_correlated"] and not r["numeric_duplicate_on_common_sample"]
    assert redundancy(x, x.copy())["numeric_duplicate_on_common_sample"]
    assert not redundancy(x.iloc[:2], x.iloc[:2])["highly_correlated"]


def test_parent_routes_retain_increment_and_condition_with_negative_ic():
    selected = select_parents([
        {"factor_id":"q", "worst_ic":.05, "roles":["return"]},
        {"factor_id":"c", "worst_ic":-.02, "roles":["return"], "incremental":{"delta_ic":.02,"passed":True,"common_sample_sha256":"s"}},
        {"factor_id":"r", "worst_ic":-.1, "roles":["condition"]},
    ],limit=3)
    assert [(r["parent_id"],r["selection_route"]) for r in selected] == [("q","quality"),("c","complement"),("r","condition")]
    with pytest.raises(ValueError, match="Unauthorized"):
        select_parents([{"factor_id":"bad","years":[2025]}])


def test_repair_new_identity_and_declared_fields():
    parent = FactorSpec("p", "pct_change(close, 5)")
    repair = build_revision(parent, "pct_change(close, 6)", reason="syntax failed", repair_number=1, evidence_ids=["failure1"])
    assert repair.factor_id != parent.factor_id and repair.parents == (parent.factor_id,)
    with pytest.raises(ValueError, match="unadmitted"):
        build_revision(parent, "volume", reason="test", repair_number=1, evidence_ids=["failure1"])


def revision_fixture(tmp_path):
    workspace = tmp_path / "source"
    target = workspace / "src/quanta_agents/factor_campaign/controller.py"
    target.parent.mkdir(parents=True)
    target.write_text("def choose():\n    return 'old'\n", encoding="utf-8")
    frozen = workspace / "src/quanta_agents/factor_campaign/protocol.py"
    frozen.write_text("YEARS=(2019,2020,2021,2022,2023,2024)\n", encoding="utf-8")
    manager = RevisionManager(workspace, tmp_path / "artifacts", [frozen])
    kwargs = dict(component="scheduler", hypothesis="Measurable fix", falsifier="No measured improvement",
                  evidence_ids=["ev.failure"], next_version="V11A")
    changes = {"src/quanta_agents/factor_campaign/controller.py":"def choose():\n    return 'new'\n"}
    return manager, kwargs, changes, frozen


@pytest.mark.parametrize("path", ["../protocol.py", "src/quanta_agents/factor_campaign/protocol.py", "src/quanta_agents/meta/codex_gateway.py", "src/quanta_agents/factor_campaign/revisions.py"])
def test_patches_cannot_change_frozen_or_old_code(tmp_path,path):
    manager,kwargs,_,_ = revision_fixture(tmp_path)
    with pytest.raises(ValueError):
        manager.stage("p", {path:"x=1\n"}, **kwargs)


def test_patch_failed_tests_retained_no_activation(tmp_path):
    manager,kwargs,changes,_ = revision_fixture(tmp_path)
    staged = manager.stage("p",changes,**kwargs)
    report = manager.verify("p",test_runner=lambda p:{"passed":False}, independent_auditor=lambda *a: pytest.fail("No audit after failed test"))
    assert report["status"] == "rejected" and Path(staged["workspace"]).exists()
    with pytest.raises(ValueError,match="verified"):
        manager.activate("p")
    assert not manager.active_path.exists()


def test_patch_requires_independent_audit_and_rolls_back_failed_smoke(tmp_path):
    manager,kwargs,changes,_ = revision_fixture(tmp_path)
    manager.stage("p",changes,**kwargs)
    report = manager.verify("p",test_runner=lambda p:{"passed":True}, independent_auditor=lambda *a:{"approved":True,"independent":False,"evidence_id":"a"})
    assert report["status"] == "rejected"
    report = manager.verify("p",test_runner=lambda p:{"passed":True}, independent_auditor=lambda *a:{"approved":True,"independent":True,"evidence_id":"a"})
    assert report["status"] == "verified"
    with pytest.raises(ValueError,match="smoke"):
        manager.activate("p",smoke_test=lambda p:False)
    assert json.loads(manager.active_path.read_text())["version"] == "V10A"
    assert (manager.patches / "p/rollback.json").exists()
    assert manager.activate("p",smoke_test=lambda p:True)["version"] == "V11A"
    assert manager.rollback("p",reason="runtime regression")["version"] == "V10A"


def test_source_change_after_audit_blocks_activation(tmp_path):
    manager,kwargs,changes,_ = revision_fixture(tmp_path)
    staged = manager.stage("p",changes,**kwargs)
    manager.verify("p",test_runner=lambda p:{"passed":True}, independent_auditor=lambda *a:{"approved":True,"independent":True,"evidence_id":"a"})
    (Path(staged["workspace"])/next(iter(changes))).write_text("x=9\n",encoding="utf-8")
    with pytest.raises(ValueError,match="changed"):
        manager.activate("p")


def test_interrupted_patch_copy_preserved_and_restaged(tmp_path, monkeypatch):
    from quanta_agents.factor_campaign import revisions
    manager,kwargs,changes,_ = revision_fixture(tmp_path)
    original = revisions.shutil.copytree
    def interrupt(*args, **kw):
        result = original(*args, **kw)
        raise KeyboardInterrupt("copy interrupted before manifest")
    monkeypatch.setattr(revisions.shutil,"copytree",interrupt)
    with pytest.raises(KeyboardInterrupt):
        manager.stage("p",changes,**kwargs)
    monkeypatch.setattr(revisions.shutil,"copytree",original)
    staged = manager.stage("p",changes,**kwargs)
    assert Path(staged["workspace"]).name == "workspace_attempt_2"
    assert (manager.patches/"p/workspace").is_dir()
