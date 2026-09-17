"""V5 runs through actual V4 admission/ledger/tools; all gateway replies are fixtures."""
from copy import deepcopy
import json
import time

import pytest

from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.runtime import action_schema
from quanta_agents.meta_v5.runtime import V5Runtime, create_stage
from quanta_agents.meta_v5.tools import ACTIONS, V5ResearchTools
from test_meta_v3_research_entry import fixture, program, new as old_stage
from test_meta_v4_controller import contracts, scripted_gateway
from test_meta_v5_analytics import policy as stability_policy


def stage(tmp_path, ids=("test",), calls=8):
    tasks = {}
    for index, name in enumerate(ids):
        case = fixture.prepare(tmp_path / name, flat=True)
        tasks[name] = {"case": case, "case_hash": digest(case), "idea": "Evaluate annual evidence and report limits.", "documents": [],
            "v5": {"action_limits": dict.fromkeys(ACTIONS, 32), "required_scope_id": "generated_execution",
                   "execution_scope_id": "generated_execution", "execution_unit_id": "fixture_portfolio",
                   "benchmark_program_hashes": [], "revision_baseline_profile_id": None, "priority": index}}
    return create_stage(tmp_path / "stage", tasks=tasks, controller_policy=contracts(tasks),
        stability_policy=stability_policy(), bundles=[], policy=ClosingPolicy(task_calls=calls, stage_calls=calls * len(tasks)),
        deadline_epoch=time.time()+7200, identity_route=None)


def action(runtime, name, args):
    tools = runtime._tools("test")
    intent = runtime.ledger.reserve("test", tools.menu(),
        lambda menu, state, decision: ("Explicit generated V5 integration test; no model", action_schema(menu)))
    response = {"action": name, "arguments_json": json.dumps(args), "public_summary": "Generated fixture only",
                "self_review": dict.fromkeys(("assessment", "uncertainty", "next_step", "falsifier"), "Engineering fixture")}
    runtime.gateway_module._validate_output(response, intent["schema"])
    receipt = {"response": response, "usage": {"input_tokens": 10, "output_tokens": 10},
               "request_identity": {"intent_id": intent["intent_id"]}, "artifact_sha256": {},
               "model_verified": True, "engineering_fixture": True}
    runtime.ledger.receive_saved(intent["intent_id"], lambda *a, **k: receipt)
    runtime._apply(intent["intent_id"])
    return runtime.ledger.history("test")[-1]


def test_fresh_v5_runs_actual_controller_and_closes_without_promotion(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    calls = scripted_gateway(runtime, monkeypatch)
    result = runtime.run()
    assert calls == ["test", "test"]
    assert result["kind"] == "quanta_research_v5_001"
    assert result["tasks"]["test"]["terminal"] == "submitted"
    assert not result["research_goal_achieved"]
    prompt = json.loads(runtime.ledger.call(result["tasks"]["test"]["calls"][0]["id"])["intent"]["prompt"])
    assert "v5_scope_contract" in prompt and "v5" in prompt["public_tool_contract"]
    assert "profile_execution" in prompt["allowed_actions"]
    runtime.run()
    assert calls == ["test", "test"], "finished work cannot rerun"


def test_old_v4_plan_cannot_be_relabelled_v5(tmp_path):
    old, _ = old_stage(tmp_path)
    with pytest.raises(AdmissionBlocked, match="not a newly frozen V5"):
        V5Runtime(old.root)


def test_v5_source_drift_prevents_dispatch(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    calls = scripted_gateway(runtime, monkeypatch)
    monkeypatch.setattr("quanta_agents.meta_v5.runtime.v5_source_pins", lambda: {"changed": "x"})
    with pytest.raises(AdmissionBlocked, match="V5 source drift"):
        runtime.run()
    assert calls == []


def test_narrow_execution_cannot_claim_stability_without_profile(tmp_path):
    runtime = stage(tmp_path)
    executed = action(runtime, "develop_strategy", {"program": program()})
    assert executed["status"] == "applied"
    result = action(runtime, "submit_research_report", {"outcome": "strategy_for_development", "conclusion": "Unsupported candidate",
        "evidence_ids": [executed["id"]], "program_evidence_id": executed["id"], "limitations": ["Synthetic"],
        "next_step": "More evidence", "falsifiers": ["Missing annual evidence"]})
    assert result["status"] == "failed"
    assert runtime.ledger.status("test")["terminal"] == "invalid_final"
    assert "all executed candidates" in str(result["result"])


def test_v5_saved_action_crash_recovery_does_not_reexecute(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    original = runtime.ledger.finish_apply
    monkeypatch.setattr(runtime.ledger, "finish_apply", lambda *a, **k: (_ for _ in ()).throw(OSError("commit interruption")))
    with pytest.raises(OSError):
        action(runtime, "inspect_inputs", {"table": "fields", "offset": 0, "limit": 32})
    call = runtime.ledger.history("test")[-1]
    monkeypatch.setattr(V5ResearchTools, "execute", lambda *a, **k: pytest.fail("tool reexecuted after saved result"))
    monkeypatch.setattr(runtime.ledger, "finish_apply", original)
    runtime._apply(call["id"])
    assert runtime.ledger.history("test")[-1]["status"] == "applied"


def test_v5_source_failure_is_local_and_priority_preserves_ready_gate(tmp_path, monkeypatch):
    runtime = stage(tmp_path, ids=("unavailable", "independent"))
    source = runtime.plan["tasks"]["unavailable"]["case"]["raw_source_bindings"]["source_artifacts"][0]
    from pathlib import Path
    (Path(source["root"]) / source["rows_file"]).unlink()
    calls = scripted_gateway(runtime, monkeypatch)
    result = runtime.run()
    assert calls == ["independent", "independent"]
    assert result["tasks"]["independent"]["terminal"] == "submitted"
    assert result["work_schedule"]["tasks"]["unavailable"]["status"] == "blocked_task_source"


def test_last_call_is_still_reserved_for_report(tmp_path):
    runtime = stage(tmp_path, calls=2)
    action(runtime, "inspect_inputs", {"table": "fields", "offset": 0, "limit": 32})
    tools = runtime._tools("test")
    intent = runtime.ledger.reserve("test", tools.menu(), lambda menu, state, decision: ("Closing test", action_schema(menu)))
    assert intent["schema"]["properties"]["action"]["enum"] == ["submit_research_report"]


def catalog_stage(tmp_path):
    from test_meta_v5_workflow import DEMO
    tools, catalog, _ = DEMO.create_demo_tools(tmp_path / "inputs")
    bundle = catalog.bundle("synthetic_difference")
    contract = {**tools.v5_contract, "revision_baseline_profile_id": "synthetic_difference", "priority": 0}
    tasks = {"test": {"case": tools.case, "case_hash": digest(tools.case), "idea": "Read generated annual differences", "documents": [], "v5": contract}}
    return create_stage(tmp_path / "ledger", tasks=tasks, controller_policy=contracts(tasks),
        stability_policy=catalog.policy, bundles=[bundle], policy=ClosingPolicy(task_calls=4, stage_calls=4),
        deadline_epoch=time.time()+7200, identity_route=None)


def test_actual_v5_action_is_ledger_settled_and_can_support_legal_abstention(tmp_path):
    runtime = catalog_stage(tmp_path)
    one = action(runtime, "inspect_stability", {"profile_id": "synthetic_difference", "table": "cells", "offset": 0, "limit": 1})
    assert one["status"] == "applied" and one["result"]["public"]["returned_rows"] == 1
    report = {"outcome": "abstain", "conclusion": "Full evidence review remains incomplete.", "evidence_ids": [one["id"]],
              "program_evidence_id": None, "limitations": ["Generated engineering evidence"], "next_step": "Inspect retained annual cells", "falsifiers": ["Independent evidence meets the frozen criteria"]}
    final = action(runtime, "submit_research_report", report)
    assert final["result"]["legal_submission"] and not final["result"]["formal_target_success"]
    assert runtime.ledger.status("test")["terminal"] == "submitted"


def test_actual_v5_page_recovers_from_committed_result_without_reading_source_again(tmp_path, monkeypatch):
    runtime = catalog_stage(tmp_path)
    original = runtime.ledger.finish_apply
    monkeypatch.setattr(runtime.ledger, "finish_apply", lambda *a, **k: (_ for _ in ()).throw(OSError("commit interruption")))
    with pytest.raises(OSError):
        action(runtime, "inspect_stability", {"profile_id": "synthetic_difference", "table": "cells", "offset": 0, "limit": 1})
    call = runtime.ledger.history("test")[-1]
    monkeypatch.setattr(V5ResearchTools, "execute", lambda *a, **k: pytest.fail("V5 page producer called twice"))
    monkeypatch.setattr(runtime.ledger, "finish_apply", original)
    runtime._apply(call["id"])
    result = runtime.ledger.history("test")[-1]
    assert result["status"] == "applied" and result["result"]["public"]["returned_rows"] == 1
