"""Synthetic artifacts and mocked researcher only; no real values or account."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from quanta_agents.meta_v6 import information_application as app, gateway


def write(path, value):
    app.save_once(path, value)


def edit(path, operation):
    value = app.read(path)
    operation(value)
    path.write_text(app.dump(value), encoding="utf8")


def receipt(root, stage, response, prompt="SYNTHETIC prompt"):
    folder = root / "model_calls" / stage
    write(folder / "response.json", response)
    write(folder / "runtime_session.jsonl", {"synthetic": True})
    (folder / "prompt.txt").write_text(prompt, encoding="utf8")
    result = {"model": "gpt-6-astra", "effort": "xhigh", "response": response,
        "runtime_identity": {"verified": True, "model": "gpt-6-astra", "effort": "xhigh"},
        "artifact_sha256": {name: app.file_hash(folder / name) for name in ("response.json", "runtime_session.jsonl", "prompt.txt")}}
    write(folder / "admitted_receipt.json", result)
    return result


def synthetic_fit():
    scope = {"date_range": ["2016-01-01", "2020-12-31"], "purged_signal_sessions": 21}
    prior = [{"factor_key": f"F{i}", "factor_id": f"prior{i}", "name": f"old{i}", "expression": f"pct_change(close,{i})",
        "direction": 1, "status": "evaluated", "scope": scope} for i in range(1, 7)]
    prior += [{"factor_key": f"S{i}", "factor_id": f"seed{i}", "name": f"seed{i}", "expression": f"pct_change(close,{i+7})",
        "direction": -1, "status": "evaluated", "scope": scope} for i in range(3)]
    new = [{"factor_key": key, "factor_id": key, "name": key, "expression": expression, "direction": direction,
        "role": role, "status": "evaluated", "comparison_complete": True, "scope": scope,
        "declared_primary_horizon": 20, "annual": [{"year": y, "ic": .01} for y in range(2016, 2021)]}
        for key, expression, direction, role in [("HF0280", "hf0280_triple_ols20_v1", 1, "return_prediction"),
            ("F7", "rolling_std(pct_change(close,1),20)", -1, "risk_information"), ("F8", "pct_change(amount,20)", -1, "return_prediction")]]
    new[1]["risk_information"] = {"status": "evaluated", "summary": {"marker": "COMPLETE_RISK_FIT"},
        "annual": [{"year": y, "future_vol": .1} for y in range(2016, 2021)],
        "bootstrap": [{"metric": "future_vol", "ci_low": -.1, "ci_high": .2}],
        "quantiles": [{"metric": "future_vol", "quantile": 1, "mean_risk": .3}],
        "common_sample": [{"common_stock_days": 100}], "comparison": {"comparison_complete": True},
        "full_range_aggregates_reused": False, "risk_labels_registered_as_signal_fields": False}
    return {"factors": prior + new, "scope": scope, "new_factor_keys": [r["factor_key"] for r in new],
        "prior_factor_keys": [r["factor_key"] for r in prior], "library_snapshot_id": "synthetic-snapshot", "library_snapshot_hash": "synthetic-hash",
        "2021_2024_result_values_included": False, "next_model_may_read_full_range_artifacts": False}


def response(fit):
    items = []
    for i, factor in enumerate(fit["factors"]):
        if factor["factor_key"] not in fit["new_factor_keys"]:
            continue
        risk = factor["role"] == "risk_information"
        items.append({"factor_key": factor["factor_key"], "role": factor["role"], "evidence_status": factor["status"],
            "return_support": "not_this_role" if risk else "limited_in_scope",
            "risk_support": "limited_in_scope" if risk else "not_this_role", "incremental_support": "limited_in_scope",
            "application": "inverse_volatility_control" if risk else "return_rank",
            "evidence_refs": ([f"/factors/{i}/risk_information/{name}" for name in
                ("summary", "annual", "bootstrap", "quantiles", "common_sample", "comparison")] if risk else [f"/factors/{i}/annual"]),
            "reason": "SYNTHETIC role evidence", "control_limitations": "limited descriptive evidence",
            "falsification": "unfavorable matched account comparison", "risk_review": {name: "SYNTHETIC risk review" for name in
                ("future_vol", "future_downside", "future_entry_max_loss", "annual_stability", "common_sample_and_controls", "bootstrap_uncertainty")}})
    base = {"name": "baseline", "components": [{"factor_key": "HF0280", "weight": .5}, {"factor_key": "F8", "weight": .5}],
        "top_n": 20, "membership_buffer": 0, "weighting": "equal", "schedule": "weekly_last_session", "market_filter": "none",
        "crowding_gate_factor_key": "", "risk_information_factor_key": "", "control_against": "", "changed_control": "baseline",
        "hypothesis": "SYNTHETIC baseline", "information_application": "only original signed raw scores", "falsification": "SYNTHETIC costs overwhelm effect"}
    risk = {**deepcopy(base), "name": "risk_weight", "weighting": "inverse_volatility", "risk_information_factor_key": "F7",
            "control_against": "baseline", "changed_control": "weighting"}
    schedule = {**deepcopy(base), "name": "lower_turnover", "schedule": "every_20_sessions", "control_against": "baseline", "changed_control": "schedule"}
    return {"factor_assessments": items, "portfolios": [base, risk, schedule], "old_account_failure_and_cost_diagnosis": "SYNTHETIC saved losses and costs",
        "competing_explanations": "unresolved causal claims", "selection_and_stopping": "frozen complete-year stress selection",
        "exposure_and_limitations": "all earlier failures retained; exposed development"}


@pytest.fixture(autouse=True)
def no_real_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("real gateway forbidden in synthetic tests")
    monkeypatch.setattr(gateway, "CodexGateway", forbidden)


@pytest.fixture
def environment(tmp_path, monkeypatch):
    root, folder = tmp_path / "synthetic_run", tmp_path / "synthetic_run/cycles" / app.FACTOR_CYCLE
    fit = synthetic_fit()
    new = fit["factors"][9:]
    originals = [{"factor_key": r["factor_key"], "original": {"name": r["name"], "expression": r["expression"],
        "direction": r["direction"], "primary_horizon": 20, "role": r["role"]}} for r in new]
    model = receipt(root, app.FACTOR_CALL, {"factors": [r["original"] for r in originals[1:]]})
    write(root / "protocol.json", app.PROTOCOL)
    declaration = {"model_factors": model["response"]["factors"], "source_receipt_sha256": app.file_hash(root / "model_calls" / app.FACTOR_CALL / "admitted_receipt.json")}
    write(folder / "factor_declaration.json", declaration)
    write(folder / "factor_execution_intent.json", {"declarations": originals})
    fit["factor_declaration_sha256"] = app.file_hash(folder / "factor_declaration.json")
    write(root / "fit_factor_view.json", {"factors": fit["factors"][:9]})
    prior_index = {"factors": fit["factors"][:9], "fit_factor_view_sha256": app.file_hash(root / "fit_factor_view.json")}
    write(root / "factor_index.json", prior_index)
    write(folder / "fit_factor_view.json", fit)
    write(folder / "output_library_snapshot.json", {"snapshot_id": fit["library_snapshot_id"], "snapshot_hash": fit["library_snapshot_hash"]})
    write(folder / "factor_index.json", {"status": "completed", "factors": new, "prior_factors": prior_index["factors"],
        "fit_factor_view_sha256": app.file_hash(folder / "fit_factor_view.json"), "intent_sha256": app.file_hash(folder / "factor_execution_intent.json"),
        "factor_declaration_sha256": fit["factor_declaration_sha256"], "library_snapshot_id": fit["library_snapshot_id"], "source_proofs": []})
    write(folder / "jobs/01_factor_execution/job_result.json", {"status": "completed", "all_owned_processes_exited": True, "primary_exit_code": 0})
    summary = {"fees": 100., "slippage": 120., "turnover": 8., "mean_exposure": .8, "trade_count": 12,
        "blocked_orders": 1, "stale_held_sessions": 4, "max_stale_fraction": .2, "terminal_inventory_value": 700000., "terminal_liquidation_cost_estimate": 1100.}
    observation = {"selected": "R2", "training_observations": [{"candidate": "R1", "results": {"base": summary}, "stress_feasible": False}],
        "temporal_observations": {stress: {"full_continuous_account": {**summary, "marker": "OLD_FAILURE_2021_2024"}}
            for stress in ("base", "slippage_x2", "capacity_half")}, "previous_proposals_retained": 6, "financial_success": False}
    write(folder / "prior_account_observations.json", observation)
    old = root / "cycles/02_evidence_led_combinations"
    write(old / "combination_declaration.json", {"cumulative_proposals": 6, "specs": []})
    write(old / "selection.json", {"selected": "R2"})
    write(old / "temporal_stage_result.json", {"financial_success": False})
    write(root / "model_calls/02_combination_admission/admitted_receipt.json", {"runtime_identity": {"verified": True},
        "response": {"decisions": [{"candidate": key, "decision": "reject"} for key in "ABCD"]}})
    write(folder / "account_cost_attribution_protocol.json", {"kind": "SYNTHETIC fixed actual units, not counterfactual"})
    write(folder / "prior_account_cost_attribution.json", {"protocol_sha256": app.file_hash(folder / "account_cost_attribution_protocol.json"),
        "financial_success": False, "new_account_executions": 0, "sources": [],
        "annual": [{"view": view, "year": year, "actual_net_pnl": -10., "observed_fees": 4., "price_pnl_at_same_actual_units": -6.}
            for view, end in (("R1_fit", 2020), ("R2_fit", 2020), ("R2_continuous", 2024)) for year in range(2016, end+1)]})
    supplement_protocol = {"scope": {"date_range": ["2016-01-01", "2020-12-02"], "fit_signal_sessions": 1197,
        "new_2021_2024_values_read": False, "2025_values_read": False}, "method": {"block_length": 20,
        "repetitions": 1000, "seed": 20260909, "confidence": .95, "horizons": [1, 5, 20]},
        "source_proofs": [], "proposal_timing": {"post_hoc_supplement": True, "pre_results_preregistration_claimed": False}}
    write(folder / "return_ic_bootstrap_protocol.json", supplement_protocol)
    write(folder / "return_ic_bootstrap.json", {**supplement_protocol, "status": "completed",
        "protocol_sha256": app.file_hash(folder / "return_ic_bootstrap_protocol.json"),
        "factor_index_sha256": app.file_hash(folder / "factor_index.json"), "fit_factor_view_sha256": app.file_hash(folder / "fit_factor_view.json"),
        "factor_job_result_sha256": app.file_hash(folder / "jobs/01_factor_execution/job_result.json"),
        "factor_count": 12, "factors": [{"factor_key": r["factor_key"], "direction": r["direction"], "source_factor_status": r["status"],
            "horizons": [{"horizon": 20, "ci_low": -.2, "ci_high": .2}]} for r in fit["factors"]]})
    monkeypatch.setattr(app, "closed_observations", lambda path: deepcopy(observation))
    exposures, calls, paid = [], [], []
    class Library:
        def __init__(self, path): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def load_snapshot(self, key): return {"snapshot_hash": fit["library_snapshot_hash"]}
        def record_exposure(self, **kwargs):
            exposures.append(kwargs)
            return "synthetic-exposure"
    monkeypatch.setattr(app, "FactorLibrary", Library)
    proposed = response(fit)
    def researcher(path, stage, prompt, schema):
        assert stage == app.CALL and path == root
        calls.append(prompt)
        saved = root / "model_calls" / stage / "admitted_receipt.json"
        if saved.exists(): return app.read(saved)
        paid.append(stage)
        return receipt(root, stage, deepcopy(proposed), prompt)
    monkeypatch.setattr(app, "call_researcher", researcher)
    before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    return root, fit, proposed, exposures, calls, paid, before


def test_compile_signed_components_control_pairs_and_fixed20():
    fit = synthetic_fit()
    result = app.validate_application_response(response(fit), fit, {"new_portfolio_proposals_max": 3})
    assert [s["name"] for s in result["specs"]] == ["I1", "I2", "I3"]
    assert result["specs"][0]["factor_weights"] == {"HF0280": .5, "F8": -.5}
    assert "F7" not in result["specs"][1]["factor_weights"]
    assert result["specs"][1]["weighting"] == "inverse_volatility"
    assert (result["specs"][2]["rebalance_schedule"], result["specs"][2]["rebalance_sessions"]) == ("sessions", 20)


def test_end_to_end_frozen_views_and_readonly_account_handoff(environment):
    root, fit, proposed, exposures, calls, paid, before = environment
    result = app.propose_information_application(root)
    folder, protocol, verified, model_fit = app.verify_application_declaration(root)
    assert result == verified and result["cumulative_proposals"] == 9 and result["prior_proposals_retained"] == 6
    assert len(exposures) == len(paid) == 1
    assert "COMPLETE_RISK_FIT" in calls[0] and "OLD_FAILURE_2021_2024" in calls[0] and "reported_cost_total" in calls[0]
    assert "not a generated or validated tradable residual score" in calls[0]
    assert "price_pnl_at_same_actual_units" in calls[0] and "post_hoc_supplement" in calls[0] and "ci_low" in calls[0]
    assert protocol["new_2025_numeric_data_allowed"] is False and protocol["new_2021_2024_factor_values_allowed"] is False
    assert app.file_hash(folder / "application_declaration.json") == result["application_declaration_sha256"]
    assert {key: (root / key).read_bytes() for key in before} == before
    assert app.propose_information_application(root) == result and len(paid) == len(exposures) == 1


@pytest.mark.parametrize("count", [0, 1])
def test_zero_or_baseline_only_is_valid_and_no_account(environment, count):
    root, _, proposed, _, _, _, _ = environment
    proposed["portfolios"] = proposed["portfolios"][:count]
    result = app.propose_information_application(root)
    assert len(result["specs"]) == count and result["account_executions"] == 0


@pytest.mark.parametrize("problem", ["job_live", "index_running", "fit_hash", "later_year", "2025_scope", "unpurged", "identity", "response_tamper", "old_removed", "decl_direction"])
def test_refuse_invalid_source_before_model(environment, problem):
    root, _, _, _, calls, _, _ = environment
    folder = root / "cycles" / app.FACTOR_CYCLE
    if problem == "job_live": edit(folder / "jobs/01_factor_execution/job_result.json", lambda x: x.update(all_owned_processes_exited=False))
    elif problem == "index_running": edit(folder / "factor_index.json", lambda x: x.update(status="running"))
    elif problem == "fit_hash": edit(folder / "fit_factor_view.json", lambda x: x.update(marker="tampered"))
    elif problem == "identity": edit(root / "model_calls" / app.FACTOR_CALL / "admitted_receipt.json", lambda x: x["runtime_identity"].update(effort="high"))
    elif problem == "response_tamper": edit(root / "model_calls" / app.FACTOR_CALL / "response.json", lambda x: x.update(marker="tampered"))
    elif problem == "decl_direction": edit(folder / "factor_execution_intent.json", lambda x: x["declarations"][1]["original"].update(direction=1))
    else:
        def change_fit(x):
            if problem == "later_year": x["factors"][9]["annual"][0]["year"] = 2021
            elif problem == "2025_scope": x["scope"]["date_range"][1] = "2025-12-31"
            elif problem == "unpurged": x["scope"]["purged_signal_sessions"] = 20
            elif problem == "old_removed": x["factors"].pop(0)
        edit(folder / "fit_factor_view.json", change_fit)
        edit(folder / "factor_index.json", lambda x: x.update(fit_factor_view_sha256=app.file_hash(folder / "fit_factor_view.json")))
    with pytest.raises(ValueError): app.propose_information_application(root)
    assert calls == []


@pytest.mark.parametrize("problem", ["risk_rank", "sign_flip", "multi_control", "duplicate", "partial_increment", "risk_return_only", "risk_wrong_formula", "unknown_operand", "old_rejected", "extra_field", "nan_weight", "four_proposals", "same_name", "unmatched_risk", "missing_role"])
def test_invalid_application_is_rejected_purely(problem):
    fit = synthetic_fit()
    value = response(fit)
    if problem == "risk_rank": value["portfolios"][0]["components"][1]["factor_key"] = "F7"
    elif problem == "sign_flip": value["portfolios"][0]["components"][1]["weight"] = -.5
    elif problem == "multi_control": value["portfolios"][1]["top_n"] = 40
    elif problem == "duplicate": value["portfolios"][2] = {**deepcopy(value["portfolios"][0]), "name": "renamed", "control_against": "baseline", "changed_control": "schedule"}
    elif problem == "partial_increment":
        fit["factors"][10]["risk_information"]["comparison"]["comparison_complete"] = False
        value["factor_assessments"][1]["incremental_support"] = "supported_in_scope"
    elif problem == "risk_return_only": value["factor_assessments"][1]["evidence_refs"] = ["/factors/10/annual"]
    elif problem == "risk_wrong_formula": fit["factors"][10]["expression"] = "rolling_std(pct_change(close,1),19)"
    elif problem == "unknown_operand": value["portfolios"][0]["components"][0]["factor_key"] = "residual_ic"
    elif problem == "old_rejected": value["portfolios"][0]["components"][0]["factor_key"] = "F3"
    elif problem == "extra_field": value["portfolios"][0]["window"] = 30
    elif problem == "nan_weight": value["portfolios"][0]["components"][0]["weight"] = float("nan")
    elif problem == "four_proposals": value["portfolios"].append(deepcopy(value["portfolios"][0]))
    elif problem == "same_name": value["portfolios"][1]["name"] = "baseline"
    elif problem == "unmatched_risk": value["portfolios"] = [value["portfolios"][1]]
    elif problem == "missing_role": value["factor_assessments"].pop()
    with pytest.raises(ValueError): app.validate_application_response(value, fit, {"new_portfolio_proposals_max": 3})


@pytest.mark.parametrize("status", ["failed", "duplicate"])
def test_unavailable_attempts_retained_without_admission(status):
    fit = synthetic_fit()
    fit["factors"][9]["status"] = status
    value = response(fit)
    item = value["factor_assessments"][0]
    item.update(return_support="not_evaluable", risk_support="not_this_role", incremental_support="not_evaluable", application="none")
    value["portfolios"] = []
    result = app.validate_application_response(value, fit, {"new_portfolio_proposals_max": 3})
    assert result["factor_assessments"][0]["evidence_status"] == status
    item["application"] = "return_rank"
    with pytest.raises(ValueError): app.validate_application_response(value, fit, {"new_portfolio_proposals_max": 3})


def test_bad_model_response_retained_with_no_automatic_retry(environment):
    root, _, proposed, _, _, paid, _ = environment
    proposed["portfolios"][1]["top_n"] = 40
    with pytest.raises(ValueError): app.propose_information_application(root)
    folder = root / "cycles" / app.CYCLE
    assert app.read(folder / "application_validation_failure.json")["automatic_retry"] is False
    assert not (folder / "combination_declaration.json").exists()
    assert (root / "model_calls" / app.CALL / "admitted_receipt.json").exists() and len(paid) == 1


def test_readonly_verifier_rejects_changed_specs(environment):
    root, *_ = environment
    app.propose_information_application(root)
    edit(root / "cycles" / app.CYCLE / "combination_declaration.json", lambda x: x["specs"][0].update(rebalance_sessions=20))
    with pytest.raises(ValueError): app.verify_application_declaration(root)


def test_null_year_summary_and_expression_whitespace_are_compatible():
    fit = synthetic_fit()
    fit["factors"][9]["annual"].append({"year": None, "ic": .1})
    app._fit_only(fit["factors"])
    fit["factors"][10]["expression"] = "rolling_std(pct_change(close, 1), 20)"
    assert len(app.validate_application_response(response(fit), fit, {"new_portfolio_proposals_max": 3})["specs"]) == 3


@pytest.mark.parametrize("problem", ["missing_ci", "ci_wrong_binding", "ci_2025", "cost_missing_year", "cost_protocol", "ci_factor_omission"])
def test_supplement_binding_and_scope_fail_before_call(environment, problem):
    root, _, _, _, calls, _, _ = environment
    folder = root / "cycles" / app.FACTOR_CYCLE
    if problem == "missing_ci": (folder / "return_ic_bootstrap.json").unlink()
    elif problem == "ci_wrong_binding": edit(folder / "return_ic_bootstrap.json", lambda x: x.update(fit_factor_view_sha256="wrong"))
    elif problem == "ci_2025": edit(folder / "return_ic_bootstrap.json", lambda x: x["scope"].update(**{"2025_values_read": True}))
    elif problem == "cost_missing_year": edit(folder / "prior_account_cost_attribution.json", lambda x: x["annual"].pop())
    elif problem == "cost_protocol": edit(folder / "account_cost_attribution_protocol.json", lambda x: x.update(kind="changed"))
    elif problem == "ci_factor_omission": edit(folder / "return_ic_bootstrap.json", lambda x: x["factors"].pop())
    with pytest.raises((ValueError, FileNotFoundError)): app.propose_information_application(root)
    assert calls == []


def test_receipt_with_rebound_but_wrong_prompt_is_rejected(environment):
    root, *_ = environment
    app.propose_information_application(root)
    folder = root / "model_calls" / app.CALL
    (folder / "prompt.txt").write_text("another task prompt", encoding="utf8")
    edit(folder / "admitted_receipt.json", lambda x: x["artifact_sha256"].update({"prompt.txt": app.file_hash(folder / "prompt.txt")}))
    with pytest.raises(ValueError, match="call05 prompt"): app.verify_application_declaration(root)


@pytest.mark.parametrize("candidate", [0, 1])
def test_unnamed_inverse_volatility_cannot_bypass_risk_admission(candidate):
    fit = synthetic_fit()
    value = response(fit)
    value["portfolios"][candidate].update(weighting="inverse_volatility", risk_information_factor_key="")
    with pytest.raises(ValueError, match="explicit F7"):
        app.validate_application_response(value, fit, {"new_portfolio_proposals_max": 3})
