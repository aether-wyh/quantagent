"""Mocked combination orchestration; no market, gateway or account execution."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from quanta_agents.meta_v6 import portfolio_study as study
from quanta_agents.meta_v6.portfolio import PortfolioSpec


def save(path, value):
    study.save_once(path, value)


def model_receipt():
    return {"runtime_identity": {"verified": True}, "response": {
        "factors": [{"name": f"F{i}_synthetic", "direction": -1 if i in (2, 5, 6) else 1}
                    for i in range(1, 7)],
        "combination_plan": "SYNTHETIC original A-D plan; no financial observation",
        "selection_rule": "SYNTHETIC train-only Sharpe then lower turnover",
        "failure_conditions": "SYNTHETIC reject nonpositive stress excess including terminal liquidation"}}


@pytest.fixture(autouse=True)
def no_unmocked_heavy_work(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("test attempted an unmocked market load, model or account")
    monkeypatch.setattr(study, "load_panel", forbidden)
    monkeypatch.setattr(study, "DailyAccount", forbidden)
    monkeypatch.setattr(study, "call_researcher", forbidden)


def test_declared_four_arms_preserve_signs_equal_components_and_execution_rules(tmp_path):
    original = model_receipt()
    save(tmp_path / "model_calls/01_hypotheses/admitted_receipt.json", original)
    specs, declaration = study.declared_combinations(tmp_path)
    arms = {spec.name: spec for spec in specs}
    base = {"F1_synthetic": 1, "F2_synthetic": -1, "F3_synthetic": 1, "F4_synthetic": 1}
    assert list(arms) == ["A", "B", "C", "D"]
    assert arms["A"].factor_weights == base
    assert arms["B"].factor_weights == {**base, "HF0091_AMIHUD20": 1}
    assert arms["C"].factor_weights == arms["D"].factor_weights == {**base, "F5_synthetic": -1}
    assert all(spec.top_n == 20 and spec.max_stock_weight == .05 and spec.membership_buffer == 40
               and spec.rebalance_schedule == "weekly_last_session" and spec.weighting == "equal"
               for spec in specs)
    assert [spec.crowding_gate_factor for spec in specs] == ["", "", "", "F6_synthetic"]
    assert declaration["source_plan"] == original["response"]["combination_plan"]


def test_admission_prompt_reads_only_fit_view_not_archived_temporal_numbers(tmp_path, monkeypatch):
    save(tmp_path / "fit_factor_view.json", {"scope": {"date_range": ["2016-01-01", "2020-12-31"]},
          "library_snapshot_id": "synthetic-snapshot", "2021_2024_result_values_included": False,
          "factors": [{"name": "F1", "fit_test_marker": "FIT_ONLY_SYNTHETIC_VALUE"}]})
    save(tmp_path / "factor_declaration.json", {"synthetic_fixture": True})
    save(tmp_path / "factor_index.json", {
        "fit_factor_view_sha256": study.file_hash(tmp_path / "fit_factor_view.json"),
        "factor_declaration_sha256": study.file_hash(tmp_path / "factor_declaration.json"),
        "library_path": "synthetic-mocked-library"})
    save(tmp_path / "archived_temporal_summary.json", {"forbidden": "TEMPORAL_2021_2024_SYNTHETIC_VALUE"})
    monkeypatch.setattr(study, "declared_combinations", lambda root: ([], {"plan": "SYNTHETIC declaration"}))
    seen = []
    exposures = []

    class MockLibrary:
        def __init__(self, path):
            assert path == "synthetic-mocked-library"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def record_exposure(self, **kwargs):
            exposures.append(kwargs)
            return "synthetic-exposure-event"

    from quanta_agents.meta_v6 import library
    monkeypatch.setattr(library, "FactorLibrary", MockLibrary)

    def call(root, stage, prompt, schema):
        seen.append((stage, prompt))
        receipt = {"response": {"decisions": [{"candidate": arm, "decision": "reject", "reason": "synthetic",
                                                 "evidence_ids": []} for arm in "ABCD"]}}
        save(root / "model_calls" / stage / "admitted_receipt.json", receipt)
        return receipt

    monkeypatch.setattr(study, "call_researcher", call)
    result = study.admit_combinations(tmp_path)
    assert len(result["response"]["decisions"]) == 4
    assert len(seen) == 1 and seen[0][0] == "02_combination_admission"
    assert "FIT_ONLY_SYNTHETIC_VALUE" in seen[0][1]
    assert "TEMPORAL_2021_2024_SYNTHETIC_VALUE" not in seen[0][1]
    assert exposures[0]["scope"]["date_range"] == ["2016-01-01", "2020-12-31"]
    assert exposures[0]["used_for_selection"] is True


def setup_accounts(tmp_path, monkeypatch, *, allowed=("A", "B", "C"), terminal_cost=0., near_rf=False):
    specs = [PortfolioSpec(arm, {"synthetic": 1.}, top_n=1, max_stock_weight=1., membership_buffer=40)
             for arm in "ABCD"]
    declaration = {"specs": [asdict(spec) for spec in specs], "synthetic_fixture": True}
    save(tmp_path / "combination_declaration.json", declaration)
    monkeypatch.setattr(study, "declared_combinations", lambda root: (specs, declaration))
    save(tmp_path / "model_calls/02_combination_admission/admitted_receipt.json", {
        "runtime_identity": {"verified": True}, "response": {"decisions": [
            {"candidate": arm, "decision": "admit_for_account_test" if arm in allowed else "reject"}
            for arm in "ABCD"]}})
    source = tmp_path / "factors/synthetic/scores.parquet"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"SYNTHETIC mocked score artifact; not a real parquet")
    save(tmp_path / "fit_factor_view.json", {"synthetic_fixture": True, "2021_2024_result_values_included": False})
    save(tmp_path / "factor_index.json", {
        "scope": {"panel_fingerprint": "synthetic-panel", "data_fingerprint": "synthetic-data"},
        "fit_factor_view_sha256": study.file_hash(tmp_path / "fit_factor_view.json"),
        "factors": [{"status": "evaluated", "name": "synthetic", "scores_path": str(source),
                     "data_fingerprint": "synthetic-data",
                     "artifacts": [{"path": str(source), "sha256": study.file_hash(source)}]}]})
    score = pd.DataFrame([[1.]], index=pd.to_datetime(["2015-12-31"]), columns=["sh600000"])
    monkeypatch.setattr(study.pd, "read_parquet", lambda path: score.copy())
    market = SimpleNamespace(fingerprint=lambda: "synthetic-panel")
    monkeypatch.setattr(study, "load_panel", lambda root: market)
    target_calls, account_calls, saves = [], [], []

    def targets(panel, scores, spec, *, start, end):
        assert panel is market and list(scores) == ["synthetic"]
        target_calls.append((spec.name, start, end))
        frame = score.copy()
        frame.attrs = {"arm": spec.name, "selection_plans": {"2015-12-31": {"synthetic_frozen_plan": True}}}
        return frame

    class MockAccount:
        def __init__(self, panel, policy):
            assert panel is market
            self.policy = policy

        def run(self, weights, *, start, end, cancelled):
            assert weights.attrs["selection_plans"]["2015-12-31"]["synthetic_frozen_plan"]
            assert cancelled() is False
            arm = weights.attrs["arm"]
            account_calls.append((arm, start, end, asdict(self.policy)))
            value = 1.02**5 - 1 + .0001 if near_rf else .20
            if arm == "C" and self.policy.slippage == .002:
                value = .01
            summary = {"sessions": 1260, "return": value, "all_full_year_sharpes_available": True,
                       "mean_full_year_sharpe": 10. if arm == "C" else 1.5,
                       "turnover": 50. if arm == "B" else 100.,
                       "terminal_liquidation_cost_estimate": terminal_cost,
                       "terminal_liquidation_executed": False}
            return {"summary": summary, "policy": asdict(self.policy)}

    monkeypatch.setattr(study, "target_weights", targets)
    monkeypatch.setattr(study, "DailyAccount", MockAccount)
    monkeypatch.setattr(study, "save_account", lambda path, result: saves.append((Path(path), result)))
    return target_calls, account_calls, saves


def test_training_only_selection_applies_independent_stresses_then_turnover_tie_break(tmp_path, monkeypatch):
    targets, accounts, saved = setup_accounts(tmp_path, monkeypatch)
    result = study.evaluate_accounts(tmp_path)
    assert result["selected"] == "B", "C's better Sharpe fails slippage stress; A/B tie favors B's turnover"
    assert targets == [(arm, "2016-01-01", "2020-12-31") for arm in "ABC"]
    assert len(accounts) == len(saved) == 9
    assert all(start == "2016-01-01" and end == "2020-12-31" for _, start, end, _ in accounts)
    for offset in range(0, 9, 3):
        base, slip, capacity = [row[3] for row in accounts[offset:offset + 3]]
        assert {k for k in base if base[k] != slip[k]} == {"slippage"}
        assert {k for k in base if base[k] != capacity[k]} == {"max_prior_day_amount_fraction"}
        assert slip["slippage"] == 2 * base["slippage"]
        assert capacity["max_prior_day_amount_fraction"] == base["max_prior_day_amount_fraction"] / 2
    assert study.read(tmp_path / "selection.json") == result
    assert result["frozen_before_temporal_results"] is True
    assert study.read(tmp_path / "account_stage_result.json") == result


def test_no_admission_never_loads_market_or_dispatches_account(tmp_path, monkeypatch):
    _, accounts, _ = setup_accounts(tmp_path, monkeypatch, allowed=())
    monkeypatch.setattr(study, "load_panel", lambda *args: pytest.fail("no admitted arms must not load market"))
    result = study.evaluate_accounts(tmp_path)
    assert result["status"] == "no_admitted_combination"
    assert accounts == []


def test_terminal_liquidation_cost_can_disqualify_tiny_positive_training_excess(tmp_path, monkeypatch):
    setup_accounts(tmp_path, monkeypatch, allowed=("A",), terminal_cost=1_000., near_rf=True)
    result = study.evaluate_accounts(tmp_path)
    # Synthetic pre-liquidation excess = 0.0001 * 1m = 100; required terminal
    # liquidation stress costs 1000. It cannot pass the declared stress rule.
    assert result["selected"] is None, "positive unliquidated excess cannot bypass the declared terminal-cost stress"


@pytest.mark.parametrize("changed", ["scores", "fit_view", "panel", "factor_data"])
def test_mutated_inputs_cannot_reach_any_account(tmp_path, monkeypatch, changed):
    _, accounts, saved = setup_accounts(tmp_path, monkeypatch)
    if changed == "scores":
        (tmp_path / "factors/synthetic/scores.parquet").write_bytes(b"modified synthetic scores")
    elif changed == "fit_view":
        with (tmp_path / "fit_factor_view.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
    elif changed == "panel":
        monkeypatch.setattr(study, "load_panel", lambda root: SimpleNamespace(fingerprint=lambda: "other-panel"))
    else:
        import json
        path = tmp_path / "factor_index.json"
        index = study.read(path)
        index["factors"][0]["data_fingerprint"] = "other-data"
        path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ValueError, match="changed|differs|another"):
        study.evaluate_accounts(tmp_path)
    assert accounts == [] and saved == []
    assert not (tmp_path / "selection.json").exists()
