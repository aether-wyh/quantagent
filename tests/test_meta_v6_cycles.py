"""Synthetic evidence and mocked researcher; no model or account execution."""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v6 import cycles


def write(path, value):
    cycles.save_once(path, value)


def overwrite_fixture(path, value):
    # Only synthetic temporary inputs are edited by these negative tests.
    path.write_text(json.dumps(value), encoding="utf-8")


def proposal(name="synthetic", **changes):
    return {"name": name, "components": [{"factor_key": "F1", "weight": .75},
                                          {"factor_key": "F2", "weight": .25}],
            "top_n": 20, "membership_buffer": 40, "weighting": "equal", "market_filter": "none",
            "crowding_gate_factor_key": "", "hypothesis": "SYNTHETIC economic hypothesis",
            "difference_from_other_candidate": "SYNTHETIC controlled application difference",
            "falsification": "SYNTHETIC test registered before account observations", **changes}


def setup(tmp_path, monkeypatch, proposals=None):
    root = tmp_path / "synthetic_research"
    rejection_path = root / "model_calls/02_combination_admission/admitted_receipt.json"
    decisions = [{"candidate": key, "decision": "reject", "reason": "SYNTHETIC original rejection " + key,
                  "evidence_ids": ["synthetic-evidence"]} for key in "ABCD"]
    rejection = {"runtime_identity": {"verified": True}, "response": {"decisions": decisions,
                   "factor_review": "SYNTHETIC preserve original refusal"}}
    write(rejection_path, rejection)
    write(root / "account_stage_result.json", {"status": "no_admitted_combination", "decisions": decisions,
                                               "formal_target_success": False})
    write(root / "combination_declaration.json", {"specs": [{"name": key} for key in "ABCD"],
                                                  "synthetic_fixture": True})
    write(root / "protocol.json", {"initial_stage_search": {"portfolio_candidates_max": 4},
                                    "data": {"exposure": "2015-2024 previously_exposed_development"}})
    fit = {"scope": {"date_range": ["2016-01-01", "2020-12-31"], "purged_signal_sessions": 21},
           "2021_2024_result_values_included": False, "test_marker": "SYNTHETIC_FIT_ONLY_MARKER",
           "factors": [{"factor_key": "F" + str(i), "name": "F" + str(i) + "_registered",
                        "status": "evaluated", "direction": -1 if i in (2, 5, 6) else 1} for i in range(1, 7)] + [
                            {"factor_key": "HF0091", "name": "HF0091_AMIHUD20", "direction": 1, "status": "evaluated"}]}
    write(root / "fit_factor_view.json", fit)
    write(root / "factor_index.json", {"fit_factor_view_sha256": cycles.file_hash(root / "fit_factor_view.json"),
                                       "library_snapshot_id": "synthetic-preserved-library-snapshot"})
    write(root / "temporal_archive.json", {"forbidden_marker": "SYNTHETIC_LATER_NUMERIC_MARKER"})
    original = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.json")}
    calls = []
    designs = [proposal()] if proposals is None else proposals

    def call(path, stage, prompt, schema):
        assert path == root and stage == "03_evidence_led_combination_design"
        calls.append({"stage": stage, "prompt": prompt, "schema": schema})
        receipt = {"model": "gpt-6-astra", "effort": "xhigh", "runtime_identity": {"verified": True},
                   "response": {"portfolios": deepcopy(designs), "learning_from_rejected_plans": "SYNTHETIC learning",
                                "evidence_and_limitations": "SYNTHETIC exposed evidence",
                                "selection_and_stop_rule": "SYNTHETIC fixed training selection"}}
        write(root / "model_calls" / stage / "admitted_receipt.json", receipt)
        return receipt

    monkeypatch.setattr(cycles, "call_researcher", call)
    return root, calls, original


def assert_originals(root, original):
    assert {name: (root / name).read_bytes() for name in original} == original


def test_new_cycle_keeps_four_rejections_exposure_and_positive_weights_apply_original_direction_once(tmp_path, monkeypatch):
    second = proposal("risk-use", components=[{"factor_key": "F5", "weight": .4},
                                               {"factor_key": "HF0091", "weight": .6}],
                      crowding_gate_factor_key="F6")
    root, calls, original = setup(tmp_path, monkeypatch, [proposal(), second])
    declaration = cycles.design_combinations(root)
    assert_originals(root, original)
    assert len(calls) == 1
    prompt = calls[0]["prompt"]
    assert "SYNTHETIC_FIT_ONLY_MARKER" in prompt and "SYNTHETIC_LATER_NUMERIC_MARKER" not in prompt
    assert "21-session" in prompt and "2016-2020" in prompt
    folder = root / "cycles" / cycles.CYCLE
    protocol = cycles.read(folder / "protocol.json")
    assert protocol["new_portfolio_proposals_max"] == 2
    assert protocol["cumulative_portfolio_proposals_ceiling_after_this_cycle"] == 6
    assert protocol["prior_stage"]["portfolio_proposals"] == 4
    assert protocol["prior_stage"]["account_candidates_executed"] == 0
    assert "2015-2024 previously exposed" in protocol["all_data_exposure"]
    assert protocol["new_factor_directions_allowed"] is False
    assert declaration["prior_proposals_retained"] == 4 and declaration["new_proposals"] == 2
    assert declaration["cumulative_proposals"] == 6
    assert [s["name"] for s in declaration["specs"]] == ["R1", "R2"]
    assert declaration["specs"][0]["factor_weights"] == {"F1_registered": .75, "F2_registered": -.25}
    assert declaration["specs"][1]["factor_weights"] == {"F5_registered": -.4, "HF0091_AMIHUD20": .6}
    assert declaration["specs"][1]["crowding_gate_factor"] == "F6_registered"
    assert all(s["gross_exposure"] == 1 and s["max_stock_weight"] == .05
               and s["rebalance_schedule"] == "weekly_last_session" for s in declaration["specs"])
    assert declaration["source_receipt_sha256"] == cycles.file_hash(
        root / "model_calls/03_evidence_led_combination_design/admitted_receipt.json")
    assert declaration["protocol_sha256"] == cycles.file_hash(folder / "protocol.json")
    assert protocol["prior_stage"]["result_sha256"] == cycles.file_hash(root / "account_stage_result.json")
    assert protocol["fit_view_sha256"] == cycles.file_hash(root / "fit_factor_view.json")


def test_zero_new_portfolios_is_an_explicit_recorded_abstention(tmp_path, monkeypatch):
    root, calls, original = setup(tmp_path, monkeypatch, [])
    declaration = cycles.design_combinations(root)
    assert declaration["specs"] == [] and declaration["cumulative_proposals"] == 4
    assert declaration["new_proposals"] == 0 and len(calls) == 1
    assert_originals(root, original)


def test_more_than_two_proposals_preserves_original_model_reply_but_cannot_compile(tmp_path, monkeypatch):
    root, calls, original = setup(tmp_path, monkeypatch, [proposal("one"), proposal("two"), proposal("three")])
    with pytest.raises(ValueError, match="two-proposal"):
        cycles.design_combinations(root)
    assert len(calls) == 1
    assert len(cycles.read(root / "model_calls/03_evidence_led_combination_design/admitted_receipt.json")["response"]["portfolios"]) == 3
    assert not (root / "cycles" / cycles.CYCLE / "combination_declaration.json").exists()
    assert_originals(root, original)


@pytest.mark.parametrize("key", ["F3", "F4"])
def test_previously_rejected_f3_f4_cannot_restart_even_with_original_direction(tmp_path, monkeypatch, key):
    root, _, original = setup(tmp_path, monkeypatch, [proposal(components=[{"factor_key": key, "weight": 1.}])])
    with pytest.raises(ValueError, match="cannot be silently reinstated"):
        cycles.design_combinations(root)
    assert_originals(root, original)
    assert not (root / "cycles" / cycles.CYCLE / "combination_declaration.json").exists()


@pytest.mark.parametrize("weight", [-1., 0., 1.001, float("inf"), float("nan"), True])
def test_invalid_weight_cannot_flip_direction_or_create_unregistered_weight(tmp_path, monkeypatch, weight):
    root, _, original = setup(tmp_path, monkeypatch, [proposal(components=[{"factor_key": "F2", "weight": weight}])])
    with pytest.raises(ValueError):
        cycles.design_combinations(root)
    assert_originals(root, original)
    assert not (root / "cycles" / cycles.CYCLE / "combination_declaration.json").exists()


@pytest.mark.parametrize("changes", [
    {"components": []},
    {"components": [{"factor_key": "unregistered", "weight": 1.}]},
    {"components": [{"factor_key": "F1", "weight": .5}, {"factor_key": "F1", "weight": .5}]},
    {"top_n": 10}, {"top_n": 20.0}, {"membership_buffer": 60},
    {"weighting": "optimized"}, {"market_filter": "future_regime"}, {"crowding_gate_factor_key": "F5"},
])
def test_unregistered_controls_are_rejected_without_rewriting_prior_attempts(tmp_path, monkeypatch, changes):
    root, _, original = setup(tmp_path, monkeypatch, [proposal(**changes)])
    with pytest.raises(ValueError):
        cycles.design_combinations(root)
    assert_originals(root, original)
    assert not (root / "cycles" / cycles.CYCLE / "combination_declaration.json").exists()


@pytest.mark.parametrize("top_n,buffer,weighting,market", [(20, 0, "equal", "none"),
    (40, 80, "inverse_volatility", "trend60"), (60, 120, "equal", "trend120")])
def test_declared_control_choices_compile_without_changing_capital_contract(tmp_path, monkeypatch, top_n, buffer, weighting, market):
    root, _, _ = setup(tmp_path, monkeypatch, [proposal(top_n=top_n, membership_buffer=buffer,
                                                      weighting=weighting, market_filter=market)])
    spec = cycles.design_combinations(root)["specs"][0]
    assert (spec["top_n"], spec["membership_buffer"], spec["weighting"], spec["market_filter"]) == (top_n, buffer, weighting, market)
    assert spec["max_stock_weight"] == .05 and spec["gross_exposure"] == 1.


@pytest.mark.parametrize("changed", ["unfinished", "identity", "not_rejected", "duplicate_candidates",
                                     "inconsistent_stage_result", "fit_hash", "later_values"])
def test_invalid_prior_closure_or_fit_scope_refuses_before_model_call(tmp_path, monkeypatch, changed):
    root, calls, _ = setup(tmp_path, monkeypatch)
    prior = root / "account_stage_result.json"
    rejection = root / "model_calls/02_combination_admission/admitted_receipt.json"
    if changed in {"unfinished", "inconsistent_stage_result"}:
        value = cycles.read(prior)
        if changed == "unfinished":
            value["status"] = "still_running"
        else:
            value["decisions"][0]["decision"] = "admit_for_account_test"
        overwrite_fixture(prior, value)
    elif changed in {"identity", "not_rejected", "duplicate_candidates"}:
        value = cycles.read(rejection)
        if changed == "identity":
            value["runtime_identity"]["verified"] = False
        elif changed == "not_rejected":
            value["response"]["decisions"][0]["decision"] = "needs_more_factor_evidence"
        else:
            value["response"]["decisions"] = [deepcopy(value["response"]["decisions"][0])] * 4
        overwrite_fixture(rejection, value)
    elif changed == "fit_hash":
        with (root / "fit_factor_view.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
    else:
        fit = cycles.read(root / "fit_factor_view.json")
        fit["2021_2024_result_values_included"] = True
        overwrite_fixture(root / "fit_factor_view.json", fit)
        index = cycles.read(root / "factor_index.json")
        index["fit_factor_view_sha256"] = cycles.file_hash(root / "fit_factor_view.json")
        overwrite_fixture(root / "factor_index.json", index)
    with pytest.raises(ValueError):
        cycles.design_combinations(root)
    assert calls == []
