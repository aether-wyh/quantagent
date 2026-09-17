"""Protocol-only fake transport and generated state; no paid model or market run."""
from copy import deepcopy
import json
import time

import pytest

from quanta_agents.meta_v7.model import model_step
from quanta_agents.meta_v7.protocol import CONTRACT, build_context, compact_factors, validate_action
from quanta_agents.research_kernel.store import serial
from test_meta_v7_controller import initialize, factors_done, strategy
from test_research_kernel_protocol import FakeGateway, install_fake_saved_verifier, action


def calls_used(kernel, number):
    with kernel.store.connect() as db:
        for i in range(number):
            db.execute("INSERT INTO model_calls VALUES (?,?,?,?,?,?,?)",
                (f"synthetic_call_{i}", "applied", "synthetic_no_transport", None,
                 serial({"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}), None, time.time()))


@pytest.mark.parametrize("response", [
    action("evaluate_factors", {"ids": ["F1"], "future_values": True}),
    action("evaluate_factors", {}),
    action("review_batch", {"batch_id": "b", "verdict": "stop"}),
    action("review_validation", {"job_id": "v", "conclusion": "done", "independent": True}),
    {"action": "evaluate_factors", "reason": "x", "payload_json": '{"ids":["F1"],"ids":["F2"]}'},
    {"action": "evaluate_factors", "reason": "x", "payload_json": '{"ids":NaN}'},
    {"action": "evaluate_factors", "reason": "x", "payload_json": "[]"},
    {"action": "evaluate_factors", "reason": "x", "payload_json": "{}", "fix": True},
])
def test_new_action_schema_rejects_invalid_bytes_without_mutating_original(response):
    original = deepcopy(response)
    with pytest.raises((ValueError, TypeError)):
        validate_action(response)
    assert response == original


def test_action_response_limit_is_utf8_and_short_schema_accepts_declared_factor_phase():
    response = action("evaluate_factors", {"ids": ["F1"], "horizons": [5], "pairs": []}, reason="中"*200)
    size = len(serial(response).encode())
    with pytest.raises(ValueError):
        validate_action(response, max_bytes=size-1)
    assert validate_action(response, max_bytes=size) == ("evaluate_factors", {"ids": ["F1"], "horizons": [5], "pairs": []})


def test_context_automatically_contains_factor_values_catalogue_scope_and_complete_evidence(tmp_path):
    kernel, panel, config = initialize(tmp_path)
    row, report = factors_done(kernel, panel, ["F1", "F2", "weak"])
    context = build_context(kernel)
    packet = context["packet"]
    assert len(packet["factor_evidence"]) == 1
    assert packet["factor_evidence"][0]["evidence_id"] == row["evidence_id"]
    assert packet["factor_evidence"][0]["factors"]["weak"]["ic"]["5"]["mean_ic"] is None
    assert packet["factor_evidence"][0]["scope"]["end"] == config["split_plan"]["train_end"]
    assert {r["id"] for r in packet["catalogue"]} == {"F1", "F2", "weak"}
    assert len(packet["factor_evidence"][0]["correlations"]) == 3
    assert context["utf8_bytes"] == len(context["prompt"].encode()) <= 120000
    whole = kernel.store.evidence(packet["full_ledger_evidence_id"], limit=100, max_bytes=2000000)["value"]
    assert whole["stage_evidence"][0]["evidence_id"] == row["evidence_id"]


def test_context_contains_actual_requested_delta_not_earlier_query(tmp_path):
    kernel, _, _ = initialize(tmp_path)
    kernel.apply_action(action("query_assets", {"query": "weak"}))
    revision = kernel.status()["revision"]
    eid = kernel.store.put_evidence("generated_detail", {"items": [{"marker": "requested_current_detail"}]})
    kernel.apply_action(action("get_evidence", {"evidence_id": eid, "pointer": "/items", "limit": 1}))
    context = build_context(kernel, after_revision=revision)
    assert [item["kind"] for item in context["packet"]["recent_actions"]] == ["action_get_evidence"]
    assert "requested_current_detail" in context["prompt"]


def test_large_query_is_indexed_losslessly_under_context_limit(tmp_path):
    kernel, _, _ = initialize(tmp_path, budget={"max_context_bytes": 14000})
    eid = kernel.store.put_evidence("generated_large", {"rows": [{"text": "x"*350, "index": i} for i in range(30)]})
    kernel.apply_action(action("get_evidence", {"evidence_id": eid, "pointer": "/rows", "limit": 30}))
    context = build_context(kernel)
    assert context["utf8_bytes"] <= 14000
    delta = context["packet"]["recent_actions"][0]
    assert "full_evidence_id" in delta["data"]
    saved = kernel.store.evidence(delta["data"]["full_evidence_id"], limit=100, max_bytes=25000)["value"]
    assert saved["data"]["result"]["value"][-1]["index"] == 29


def test_full_ledger_reference_preserves_more_than_first_page_of_project_trials(tmp_path):
    kernel, _, _ = initialize(tmp_path)
    for index in range(103):
        kernel.project.record_trial(kernel.v7["study_id"], f"t{index}", "fixture", {"parameter": index})
    context = build_context(kernel)
    eid = context["packet"]["full_ledger_evidence_id"]
    values = kernel.store.evidence(eid, pointer="/trials", offset=100, limit=100, max_bytes=2000000)["value"]
    assert [row["trial_id"] for row in values] == ["t100", "t101", "t102"]


def test_reserved_closing_call_cannot_request_new_factor_or_portfolio(tmp_path):
    kernel, _, _ = initialize(tmp_path, budget={"max_model_calls": 4})
    calls_used(kernel, 3)
    assert kernel.status()["closing_only"]
    for response in (action("evaluate_factors", {"ids": ["F1"], "horizons": [5]}),
                     action("propose_batch", {"specs": [strategy()]}),
                     action("register_factor", {"asset": {"id": "extra", "expression": "close"}})):
        with pytest.raises(ValueError, match="closing budget"):
            kernel.apply_action(response)
    assert kernel.status()["attempts"] == 0 and kernel.status()["factor_jobs"] == []


def test_invalid_real_path_model_action_remains_original_and_is_feedback_not_rewritten(tmp_path):
    kernel, _, _ = initialize(tmp_path)
    response = action("propose_batch", {"specs": [strategy()]})  # no factor evidence yet
    gateway = FakeGateway(response)
    result = model_step(kernel, gateway=gateway)
    assert result["status"] == "action_rejected" and "Evaluate these factors" in result["result"]["error"]
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    assert json.loads(row["response"]) == response
    assert kernel.status()["attempts"] == 0
    context = build_context(kernel)
    assert "action_rejected" in context["prompt"] and "Evaluate these factors" in context["prompt"]


def test_pending_numerical_stage_does_not_spend_model_call(tmp_path):
    kernel, _, _ = initialize(tmp_path)
    kernel.evaluate_factors(["F1"], horizons=[5])
    gateway = FakeGateway()
    assert model_step(kernel, gateway=gateway)["status"] == "pending_numerical_stages"
    assert not gateway.calls and kernel.status()["model_calls"] == 0


def test_paid_transport_recovery_is_offline_and_usage_fields_are_not_fabricated(tmp_path, monkeypatch):
    kernel, _, _ = initialize(tmp_path)
    gateway = FakeGateway(error=RuntimeError("after saved completion"), usage={"input_tokens": 111, "output_tokens": 23,
        "total_tokens": 134, "cached_input_tokens": 7, "reasoning_output_tokens": 19})
    with pytest.raises(RuntimeError, match="after saved"):
        model_step(kernel, gateway=gateway)
    install_fake_saved_verifier(monkeypatch)
    recovered = model_step(kernel, gateway=gateway)
    assert len(gateway.calls) == 1 and kernel.status()["model_calls"] == 1
    assert recovered["status"] == "applied"
    assert recovered["usage"] == gateway.usage
    assert json.loads(kernel.store.rows("SELECT usage FROM model_calls")[0]["usage"]) == gateway.usage


def test_unverified_transport_cannot_apply_or_silently_pay_again(tmp_path, monkeypatch):
    kernel, _, _ = initialize(tmp_path)
    gateway = FakeGateway(verified=False)
    with pytest.raises(ValueError, match="identity"):
        model_step(kernel, gateway=gateway)
    install_fake_saved_verifier(monkeypatch, force_verified=False)
    with pytest.raises(ValueError, match="identity"):
        model_step(kernel, gateway=gateway)
    assert len(gateway.calls) == 1 and kernel.status()["model_calls"] == 1
    assert kernel.store.rows("SELECT * FROM actions") == []


def test_budget_exhaustion_is_persisted_before_gateway_and_does_not_claim_finished_research(tmp_path):
    kernel, _, _ = initialize(tmp_path, budget={"max_model_calls": 4})
    calls_used(kernel, 4)
    gateway = FakeGateway()
    assert model_step(kernel, gateway=gateway)["status"] == "model_budget_exhausted"
    assert not gateway.calls and kernel.status()["stopped"]
    assert kernel.store.meta("model_stopped") is True
    events = kernel.store.rows("SELECT payload FROM events WHERE kind='model_budget_exhausted'")
    assert len(events) == 1 and "research_review_complete" in json.loads(events[0]["payload"])
    assert model_step(kernel, gateway=gateway)["status"] == "stopped"
    assert len(kernel.store.rows("SELECT * FROM events WHERE kind='model_budget_exhausted'")) == 1


def test_new_capability_request_does_not_stop_or_promote_unsupported_factor(tmp_path):
    kernel, _, _ = initialize(tmp_path)
    request = {"capability": "new causal industry primitive", "reason": "missing declared source",
               "acceptance_tests": ["generated example", "future perturbation invariance"]}
    result = kernel.apply_action(action("request_extension", request))
    assert not result["executable"] and result["status"] == "capability_request_recorded"
    assert not kernel.status()["stopped"]
    assert "new causal industry primitive" in build_context(kernel)["prompt"]


def test_12_factor_4_arm_review_fits_32kb_and_discovery_returns_after_review(tmp_path):
    """Generated report-shape regression, with no factor/account/model execution.

    Values below are arbitrary fixture metadata. They assert preservation, not
    empirical performance or any result from the real V7 study.
    """
    from itertools import combinations
    kernel, _, _ = initialize(tmp_path, budget={"max_context_bytes": 32000})
    ids = [f"shape_factor_{i:02d}" for i in range(12)]
    for i, identity in enumerate(ids):
        kernel.assets.register({"id": identity, "name": f"Generated factor {i:02d}",
            "expression": f"rolling_mean(close,{i+2})", "roles": ["return", "condition"],
            "metadata": {"fixture_only": True}})
    annual_ic = [{"year": year, "mean_ic": .012345, "observed_days": 240,
                  "calendar_days": 244, "missing_days": 4} for year in range(2016, 2021)]
    factor_report = {"status": "completed", "fixture_only": True,
        "scope": {"start": "2016-01-01", "end": "2020-12-31", "role": "training_development",
                  "validation_values_returned": False},
        "factors": {identity: {"roles": ["return", "condition"],
            "coverage": {"fraction": .9, "pool_cells": 100000, "observed_cells": 90000, "missing_cells": 10000},
            "horizons": {str(h): {"mean_ic": .001*(i-6), "observed_days": 1197, "missing_days": 23,
                                     "annual": deepcopy(annual_ic)} for h in (5, 20)},
            "risk": {str(h): {metric: {"mean_ic": -.004} for metric in
                ("future_vol", "future_downside", "future_entry_max_loss")} for h in (5, 20)}}
            for i, identity in enumerate(ids)},
        "correlations": [{"left": left, "right": right, "mean_ic": .123456, "observed_days": 1200}
                         for left, right in combinations(ids, 2)],
        "conditions": [{"left": ids[i], "right": ids[(i+1) % 12], "horizon": h, "condition": condition,
                        "mean_ic": -.012345, "observed_days": 1170}
                       for i in range(12) for h in (5, 20) for condition in ("rank_le_half", "rank_gt_half")],
        "interactions": [{"left": ids[i], "right": ids[(i+1) % 12], "status": "evaluated",
                          "horizons": {str(h): {"raw_ic": {"mean_ic": .002}, "partial_ic": {"mean_ic": -.001}}
                                       for h in (5, 20)}} for i in range(12)],
        "limitations": ["Generated shape fixture only; no financial observation or independent evidence."]}
    factor_eid = kernel.store.put_evidence("factor_lab", factor_report)
    with kernel.store.transaction() as db:
        db.execute("INSERT INTO factor_jobs(id,spec,status,evidence_id) VALUES (?,?,?,?)",
                   ("shape_factor_job", serial({"fixture_only": True}), "completed", factor_eid))
        db.execute("INSERT INTO stage_evidence VALUES (?,?,?)", ("shape_factor_job", factor_eid, "factor_lab"))
    ref = lambda identity: {"op": "factor", "id": identity}
    proposal = {"name": "Generated original structure",
        "score": {"op": "weighted_sum", "weights": [.5, .5], "args": [
            {"op": "rank", "args": [ref(ids[0])]}, {"op": "rank", "args": [ref(ids[1])]}]},
        "gate": {"op": "where", "args": [{"op": "gt", "args": [
            {"op": "rank", "args": [ref(ids[2])]}, {"op": "constant", "value": .5}]},
            {"op": "constant", "value": 1}, {"op": "constant", "value": .5}]},
        "risk_score": ref(ids[3]),
        "allocation": {"top_n": 20, "max_stock_weight": .05, "weighting": "inverse_volatility"},
        "metadata": {"fixture_only": True, "kernel_control_parent": "shape_parent"}}
    arms = []
    for i, role in enumerate(("proposal", "omit_1", "without_gate", "equal_weight")):
        row = {"name": f"Generated arm {i}", "role": role, "control_parent": "shape_parent",
               "run_id": f"shape_run_{i}", "status": "failed" if i == 3 else "completed",
               "strategy": deepcopy(proposal), "error": None}
        if i == 3:
            row["error"] = {"type": "GeneratedFailure", "message": "retained failed comparison branch"}
            row["evidence_id"] = kernel.store.put_evidence("stage_failure", row["error"])
        else:
            row["summary"] = {"sharpe": .2+i*.01, "fees": 100+i, "slippage": 200+i,
                "turnover": 10+i, "mean_exposure": .8, "mean_full_year_sharpe": .1,
                "worst_full_year_sharpe": -.1, "full_years": 5, "formal_target_success": False}
            row["annual"] = [{"year": year, "sharpe": .1, "return": .02, "mean_exposure": .8,
                              "calendar_complete": True} for year in range(2016, 2021)]
            row["delta_from_proposal"] = {"sharpe": i*.01, "fees": i, "slippage": i, "mean_exposure": 0}
            row["evidence_id"] = kernel.store.put_evidence("account_shape_fixture", {"summary": row["summary"], "fixture_only": True})
        arms.append(row)
    uncertainty = [{"control_parent": "shape_parent", "baseline_run_id": "shape_run_0", "report": {
        "contrasts": [{"candidate": f"shape_run_{i}", "percentile_interval": [-.1, .2],
                       "simultaneous_family_interval": [-.2, .3], "status": "computed"} for i in (1, 2)],
        "selection_adjusted": False, "independent_trial_count_used": None}}]
    batch_id = "shape_batch"
    batch = {"batch_id": batch_id, "arms": arms, "paired_uncertainty": uncertainty, "fixture_only": True}
    batch_eid = kernel.store.put_evidence("v7_paired_batch", batch)
    hypothesis = "原假设：弱单因子仅通过条件交互补充另一信息源；配对反例和成本应共同决定下一轮。"
    with kernel.store.transaction() as db:
        kernel.store.set_meta(db, "batch_evidence:" + batch_id, batch_eid)
        kernel.store.event(db, "batch_registered", {"batch_id": batch_id, "reason": hypothesis})
        for i, arm in enumerate(arms):
            db.execute("INSERT INTO runs(id,spec,status,evidence_id,error,updated) VALUES (?,?,?,?,?,?)",
                (arm["run_id"], serial({"strategy": proposal}), arm["status"], arm["evidence_id"],
                 serial(arm["error"]) if arm["error"] else None, time.time()))
            db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?)", (f"shape_attempt_{i}", batch_id,
                arm["run_id"], arm["name"], arm["role"], arm["status"],
                serial(arm["error"]) if arm["error"] else None, time.time()))
    review = build_context(kernel)
    packet = review["packet"]
    assert review["utf8_bytes"] == len(review["prompt"].encode()) <= 32000
    assert packet["factor_evidence"] == [{"evidence_id": factor_eid, "scope": factor_report["scope"],
        "factor_ids": ids, "pointer": "/factors", "status": "full_training_diagnostics_retained_for_targeted_query"}]
    assert {row["id"] for row in packet["catalogue"]} == set(ids[:4])
    paired = packet["paired_results"][0]
    assert paired["hypothesis"] == hypothesis and paired["evidence_id"] == batch_eid
    assert paired["arms"][0]["strategy"] == proposal
    assert len(paired["arms"]) == 4 and paired["arms"][3]["status"] == "failed"
    assert paired["arms"][3]["error"]["message"] == "retained failed comparison branch"
    assert paired["paired_uncertainty"] == uncertainty
    assert paired["arms"][1]["summary"]["fees"] == 101 and len(paired["arms"][1]["annual"]) == 5
    # The same unabridged discovery summary plus four arms exceeds the old limit.
    repeated = deepcopy(packet)
    repeated["factor_evidence"] = [{"evidence_id": factor_eid, **compact_factors(factor_report)}]
    repeated["catalogue"] = [{key: kernel.assets.get(identity).get(key) for key in
                              ("id", "name", "expression", "roles", "status")} for identity in ids]
    assert len((CONTRACT + "\nRESEARCH_STATE_JSON\n" + serial(repeated)).encode()) > 32000
    # Every omitted discovery remains readable through the actual model tool.
    recovered = kernel.apply_action(action("get_evidence", {"evidence_id": factor_eid,
        "pointer": "/factors/" + ids[-1], "limit": 100}))
    assert recovered["value"] == factor_report["factors"][ids[-1]]
    kernel.review_batch(batch_id, "revise", "generated review complete; restore discovery for a new hypothesis")
    after = build_context(kernel, after_revision=kernel.status()["revision"])
    assert after["utf8_bytes"] <= 32000
    restored = after["packet"]["factor_evidence"][0]
    assert restored["evidence_id"] == factor_eid and set(restored["factors"]) == set(ids)
    assert "factor_ids" not in restored and {row["id"] for row in after["packet"]["catalogue"]} == set(ids)
    assert restored["factors"][ids[-1]]["ic"]["5"]["mean_ic"] == factor_report["factors"][ids[-1]]["horizons"]["5"]["mean_ic"]
    saved = kernel.store.evidence(factor_eid, pointer="/factors", limit=100, max_bytes=2000000)["value"]
    assert saved == factor_report["factors"]
    assert kernel.status()["executions"] == 0 and kernel.status()["model_calls"] == 0
