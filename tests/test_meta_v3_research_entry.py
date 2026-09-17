"""Shared-entry tools and saved-response integration; no paid model calls."""
import importlib.util
import json
from pathlib import Path
import time

import pytest

from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.kernel import module, ROOT
from quanta_agents.meta_v3.ledger import Ledger, digest
from quanta_agents.meta_v3.research_tools import ResearchTools, save_once
from quanta_agents.meta_v3.runtime import ResearchRuntime, action_schema, make_prompt, source_pins

spec = importlib.util.spec_from_file_location("prepare_v3_calibration", ROOT / "scripts/prepare_v3_calibration.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def new(tmp_path):
    case = fixture.prepare(tmp_path / "case", flat=True)
    task = {"case": case, "case_hash": digest(case), "idea": "研究是否存在覆盖成本的交易规则；用证据决定保留或弃权。", "documents": []}
    ledger = Ledger.create(tmp_path / "stage", policy=ClosingPolicy(task_calls=4, stage_calls=4),
        tasks={"test": task}, deadline_epoch=time.time() + 7200, provenance={"source_pins": source_pins()})
    return ResearchRuntime(ledger.root), task


def action(runtime, task, name, args):
    tools = runtime._tools("test")
    history = runtime.ledger.history("test")
    build = lambda menu, state, decision: (make_prompt(task, tools, history, menu, state, decision, runtime.plan["policy"]), action_schema(menu))
    intent = runtime.ledger.reserve("test", tools.menu(), build)
    response = {"action": name, "arguments_json": json.dumps(args), "public_summary": "Explicit engineering saved-response fixture",
                "self_review": dict.fromkeys(("assessment", "uncertainty", "next_step", "falsifier"), "Engineering fixture only")}
    module("meta.codex_gateway")._validate_output(response, intent["schema"])
    receipt = {"response": response, "usage": {"input_tokens": 10, "output_tokens": 10},
               "request_identity": {"intent_id": intent["intent_id"]}, "artifact_sha256": {}}
    runtime.ledger.receive_saved(intent["intent_id"], lambda *a, **k: receipt)
    runtime._apply(intent["intent_id"])
    return runtime.ledger.history("test")[-1]


def program():
    return {"version": "factor_strategy_program_v1", "factors": [], "target_weight_expression": "0.4",
            "hypothesis": "Arithmetic fixture, not an alpha claim", "applicability": ["Synthetic"], "invalidation_conditions": ["Nonzero fees"]}


def test_same_entry_inputs_program_funded_cost_feedback_authentic_final(tmp_path):
    runtime, task = new(tmp_path)
    one = action(runtime, task, "inspect_inputs", {"table": "fields", "offset": 0, "limit": 32})
    two = action(runtime, task, "develop_strategy", {"program": program()})
    assert two["result"]["public"]["raw_status"] == "completed_mechanical"
    assert two["result"]["public"]["costs_applied"] is True
    assert float(two["result"]["public"]["final_snapshot"]["cash"]) < 10000
    assert len(two["result"]["public"]["daily"]) == 12
    report = {"outcome": "abstain", "conclusion": "Constant synthetic prices lost money after declared costs.",
        "evidence_ids": [one["id"], two["id"]], "program_evidence_id": None,
        "limitations": ["Synthetic tiny sample, no real market validation"], "next_step": "Investigate real execution coverage.", "falsifiers": ["Correctly reproduced accounting differs"]}
    three = action(runtime, task, "submit_research_report", report)
    assert three["result"]["model_report"] == report
    assert runtime.ledger.status("test")["terminal"] == "submitted"
    assert not three["result"]["formal_target_success"]


def test_horizon_common_sample_and_condition_controls_are_saved(tmp_path):
    runtime, task = new(tmp_path)
    value = action(runtime, task, "diagnose_horizons", {"filter_expression": "activity > 2", "feature_expression": "activity", "horizons": [1, 3]})
    assert value["status"] == "applied", value
    summary = value["result"]["public"]["horizon_summary"]
    assert len(summary["descriptive_conditioning"]) == 2
    assert all(x["matched_mean_difference"] == 0 for x in summary["descriptive_conditioning"])
    page = action(runtime, task, "read_evidence", {"evidence_id": value["id"], "table": "events", "offset": 0, "limit": 2})
    assert len(page["result"]["public"]["rows"]) == 2


def test_unknown_execution_obligation_keeps_failure_and_cannot_submit_strategy(tmp_path):
    runtime, task = new(tmp_path)
    # New scope must freeze changed data before any call, never retune a run.
    case = task["case"]
    for row in case["raw_source_bindings"]["obligations"]:
        if row["date"] == case["decision_fixture"]["calendar"][3] and row["kind"] == "corporate_actions":
            row["status"] = "unknown"
    task["case_hash"] = digest(case)
    other = Ledger.create(tmp_path / "other", policy=ClosingPolicy(), tasks={"test": task}, deadline_epoch=time.time()+7200,
        provenance={"source_pins": source_pins()})
    runtime = ResearchRuntime(other.root)
    value = action(runtime, task, "develop_strategy", {"program": program()})
    assert value["result"]["public"]["raw_status"] == "failed"
    assert value["result"]["public"]["daily"] is None
    invalid = action(runtime, task, "submit_research_report", {"outcome": "strategy_for_development", "conclusion": "invalid",
        "evidence_ids": [value["id"]], "program_evidence_id": value["id"], "limitations": ["unknown"], "next_step": "check", "falsifiers": ["missing"]})
    assert invalid["status"] == "failed"
    assert runtime.ledger.status("test")["final_call"] is None


def test_saved_application_crash_recovers_without_program_execution(tmp_path, monkeypatch):
    runtime, task = new(tmp_path)
    original = runtime.ledger.finish_apply
    monkeypatch.setattr(runtime.ledger, "finish_apply", lambda *a, **k: (_ for _ in ()).throw(OSError("commit interruption")))
    with pytest.raises(OSError):
        action(runtime, task, "develop_strategy", {"program": program()})
    call = runtime.ledger.history("test")[-1]
    assert call["status"] == "applying"
    monkeypatch.setattr(ResearchTools, "execute", lambda *a, **k: pytest.fail("reexecuted tool"))
    monkeypatch.setattr(runtime.ledger, "finish_apply", original)
    runtime._apply(call["id"])
    assert runtime.ledger.history("test")[-1]["status"] == "applied"


def test_execution_compact_pages_return_all_cash_days_and_trades(tmp_path):
    runtime, task = new(tmp_path)
    value = action(runtime, task, "develop_strategy", {"program": program()})
    daily = action(runtime, task, "inspect_execution", {"evidence_id": value["id"], "table": "daily_compact", "offset": 0, "limit": 32})
    trades = action(runtime, task, "inspect_execution", {"evidence_id": value["id"], "table": "trades_compact", "offset": 0, "limit": 32})
    d, t = daily["result"]["public"], trades["result"]["public"]
    assert d["returned_rows"] == 12 and d["next_offset"] is None
    assert t["returned_rows"] == len(value["result"]["public"]["trades"]) and t["next_offset"] is None
    final = dict(zip(d["columns"], d["rows"][-1]))
    assert final["holdings"] == {} and float(final["cash_available"]) < 10000
    assert float(final["fees_paid_cumulative"]) > 0
    assert [dict(zip(t["columns"], row))["event_id"] for row in t["rows"]] == [row["event_id"] for row in value["result"]["public"]["trades"]]
