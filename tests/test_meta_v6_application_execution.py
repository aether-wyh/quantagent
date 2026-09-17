"""Synthetic declarations and mocked accounts; no market/model execution."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta_v6 import application_execution as ae
from quanta_agents.meta_v6.portfolio import PortfolioSpec, account_metrics
from quanta_agents.meta_v6.portfolio_study import file_hash
from quanta_agents.meta_v6.research import PROTOCOL, save_once


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(value), encoding="utf-8")


@pytest.fixture(autouse=True)
def no_external_execution(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("test attempted real market, account or model execution")
    monkeypatch.setattr(ae, "load_panel", forbidden)
    monkeypatch.setattr(ae, "DailyAccount", forbidden)
    from quanta_agents.meta_v6 import research
    monkeypatch.setattr(research, "call_researcher", forbidden)


def native(policy, dates, name, end, mode):
    grid = dates[(dates >= ae.START) & (dates <= end)]
    returns = np.resize([.03, .01], len(grid))
    if policy.slippage > .001:
        returns -= .001
    if policy.max_prior_day_amount_fraction < .01:
        returns -= .002
    if mode == "infeasible":
        returns[:] = 0.
    if mode == "zero_later":
        returns[grid.year == 2023] = 0.
    nav = policy.capital * np.cumprod(1 + returns)
    daily = pd.DataFrame({"nav": nav, "return": returns, "cash": nav * .2,
        "position_value": nav * .8, "exposure": .8, "fees": 10., "slippage": 1.,
        "turnover": .2 if name == "I1" else .1, "trade_count": 1, "blocked_orders": 0,
        "stale_value": 0., "stale_fraction": 0., "oldest_held_mark_sessions": 0}, index=grid)
    daily.index.name = "date"
    summary, annual = account_metrics(daily, policy, start=ae.START, end=end, expected_calendar=dates)
    summary.update(terminal_liquidation_cost_estimate=1000., terminal_liquidation_executed=False,
                   accounting_mode="synthetic_mock_not_market_execution")
    trades = pd.DataFrame({"date": [grid[0]], "code": ["synthetic"], "side": ["fixture"], "units": [1.]})
    if mode == "large_liquidation" and policy.slippage > .001:
        summary["terminal_liquidation_cost_estimate"] = 1e9
    if end == ae.END:
        if mode == "daily_mismatch":
            daily.loc[grid[2], "cash"] += 1e-6
        elif mode == "trades_mismatch":
            trades.loc[0, "units"] += 1e-6
        elif mode == "annual_mismatch":
            annual.loc[0, "sharpe"] += 1e-6
        elif mode == "dtype_mismatch":
            daily["trade_count"] = daily["trade_count"].astype(float)
        elif mode == "truncated":
            daily = daily.loc[:"2023-12-31"]
    result = {"daily": daily, "trades": trades, "annual": annual, "summary": summary, "policy": asdict(policy)}
    if mode == "wrong_policy":
        result["policy"]["capital"] = 2e6
    return result


def setup(tmp_path, monkeypatch, *, count=2, mode=None):
    root = tmp_path / "generated"
    folder = root / "cycles" / ae.CYCLE
    factor_folder = root / "cycles" / ae.FACTOR_CYCLE
    dates = pd.DatetimeIndex(["2015-12-31", *[day for year in range(2016, 2025)
        for day in (f"{year}-01-04", f"{year}-12-31")]], name="date")
    columns = pd.Index(["sh600000", "sh600001"], name="symbol")
    panel = SimpleNamespace(dates=dates, eligible=pd.DataFrame(True, index=dates, columns=columns),
                            fingerprint=lambda: "fixed-generated-panel")
    save_once(root / "protocol.json", PROTOCOL)
    old = []
    for i in range(9):
        path = root / "factors" / f"old_factor_{i}" / "scores.parquet"
        path.parent.mkdir(parents=True)
        pd.DataFrame(1., index=dates, columns=columns).to_parquet(path)
        old.append({"name": f"old_factor_{i}", "factor_key": f"OLD{i}", "status": "evaluated",
            "scores_path": str(path), "data_fingerprint": "old-data", "artifacts": [ae._proof(path)]})
    old_index = {"factors": old, "scope": {"panel_fingerprint": "fixed-generated-panel", "data_fingerprint": "old-data"}}
    save_once(root / "factor_index.json", old_index)
    path = factor_folder / "factors/new_factor/scores.parquet"
    path.parent.mkdir(parents=True)
    pd.DataFrame(2., index=dates, columns=columns).to_parquet(path)
    new = {"name": "new_factor", "factor_key": "F8", "status": "evaluated", "scores_path": str(path),
           "data_fingerprint": "new-data", "artifacts": [ae._proof(path)]}
    fit = {"2021_2024_result_values_included": False, "factors": [*old, new]}
    save_once(factor_folder / "fit_factor_view.json", fit)
    source = root / "preparation/frozen_source.py"
    source.parent.mkdir(parents=True)
    source.write_text("# generated original source\n", encoding="utf-8")
    index = {"status": "completed", "factors": [new], "prior_factors": old, "prior_scores_recomputed": 0,
        "scope": {"panel_fingerprint": "fixed-generated-panel", "data_fingerprint": "new-data"},
        "fit_factor_view_sha256": file_hash(factor_folder / "fit_factor_view.json"),
        "library_snapshot_id": "generated-snapshot", "source_proofs": [ae._proof(source)], "artifacts": [ae._proof(path)]}
    save_once(factor_folder / "factor_index.json", index)
    save_once(folder / "protocol.json", {"cycle_id": ae.CYCLE, "generated": True})
    admitted_fit = {**fit, "separately_bound_fit_only_supplement": "generated CI/role view"}
    save_once(folder / "admitted_fit_factor_view.json", admitted_fit)
    save_once(folder / "application_declaration.json", {"roles": "generated accepted model response"})
    model = root / "model_calls/05_information_application_design/admitted_receipt.json"
    save_once(model, {"generated": True, "runtime_identity": {"verified": True}})
    specs = [PortfolioSpec(f"I{i+1}", {"new_factor": .5, "old_factor_0": -.5}, top_n=20,
        max_stock_weight=.05, rebalance_schedule="weekly_last_session", membership_buffer=40,
        metadata={"generated": True}) for i in range(count)]
    declaration = {"specs": [asdict(s) for s in specs], "prior_proposals_retained": 6,
        "new_proposals": count, "cumulative_proposals": 6 + count,
        "fit_factor_view_sha256": file_hash(folder / "admitted_fit_factor_view.json"),
        "original_expansion_fit_view_sha256": index["fit_factor_view_sha256"],
        "source_receipt_sha256": file_hash(model), "library_snapshot_id": index["library_snapshot_id"],
        "input_artifacts": [ae._proof(model)]}
    save_once(folder / "combination_declaration.json", declaration)
    monkeypatch.setattr(ae, "_declaration", lambda _: (folder, ae.read(folder / "protocol.json"),
        ae.read(folder / "combination_declaration.json"), ae.read(folder / "admitted_fit_factor_view.json")))
    # The declaration/gateway adapter is mocked; keep the real execution/helper
    # sources pinned without requiring a concurrently implemented design module.
    monkeypatch.setattr(ae, "SOURCE_NAMES", tuple(n for n in ae.SOURCE_NAMES if n != "information_application.py"))
    calls, loads = [], []

    def load(_):
        assert (folder / "account_execution_intent.json").exists()
        if (folder / "account_stage_result.json").exists():
            assert (folder / "temporal_intent.json").exists()
        loads.append("panel")
        return panel
    monkeypatch.setattr(ae, "load_panel", load)

    def targets(market, scores, spec, *, start, end):
        assert market is panel and set(scores) == {"new_factor", "old_factor_0"}
        values = pd.DataFrame([[.5, .5]], index=dates[:1], columns=columns)
        values.attrs = {"selection_plans": {"2015-12-31": {"actual_holdings_buffer": True}}, "spec": asdict(spec)}
        return values
    monkeypatch.setattr(ae, "target_weights", targets)

    class Account:
        def __init__(self, market, policy):
            assert market is panel
            self.policy = policy
        def run(self, weights, *, start, end, cancelled):
            assert not cancelled() and weights.attrs["selection_plans"]
            name = weights.attrs["spec"]["name"]
            stress = next(k for k, v in ae._policies().items() if v == self.policy)
            calls.append((name, stress, start, end, self.policy.capital))
            if mode == "raise_capacity" and stress == "capacity_half":
                raise RuntimeError("synthetic account failure")
            return native(self.policy, dates, name, end, mode)
    monkeypatch.setattr(ae, "DailyAccount", Account)
    return root, folder, calls, loads


def test_three_proposals_nine_accounts_reuse_scores_intent_first_and_old_history_unchanged(tmp_path, monkeypatch):
    root, folder, calls, loads = setup(tmp_path, monkeypatch, count=3)
    old = (root / "factor_index.json").read_bytes()
    result = ae.evaluate_application_accounts(root)
    assert result["selected"] == "I2"  # I2/I3 exact tie -> original order.
    assert result["status"] == "completed" and result["new_account_executions"] == 9
    assert result["cumulative_portfolio_proposals"] == 9 and result["prior_portfolio_proposals_retained"] == 6
    assert all(c[2:] == (ae.START, ae.FIT_END, 1e6) for c in calls)
    assert (root / "factor_index.json").read_bytes() == old
    assert not (folder / "accounts/temporal").exists()
    assert ae.evaluate_application_accounts(root) == result and len(calls) == 9 and len(loads) == 1


def test_selected_continuous_all_three_prefix_tables_and_same_capital(tmp_path, monkeypatch):
    root, folder, calls, loads = setup(tmp_path, monkeypatch)
    selection = ae.evaluate_application_accounts(root)
    frozen = (folder / "selection.json").read_bytes()
    result = ae.evaluate_application_temporal(root)
    assert result["selected"] == selection["selected"] == "I2" and result["new_account_executions"] == 3
    assert calls[6:] == [("I2", k, ae.START, ae.END, 1e6) for k in ae.STRESSES]
    for observation in result["observations"].values():
        check = observation["fit_prefix_check"]
        assert all(check[k] for k in ("passed", "all_fields_exact", "dtypes_exact", "trades_exact", "annual_exact"))
        assert observation["temporal_2021_2024"]["summary"]["opening_nav_from_2020_close"] != 1e6
        assert [r["year"] for r in observation["annual"]] == list(range(2016, 2025))
    assert (folder / "selection.json").read_bytes() == frozen
    assert result["financial_success"] is False and result["winner_reselected"] is False
    assert result["annual_account_reset"] is False and result["independent_holdout"] is False
    assert ae.evaluate_application_temporal(root) == result and len(calls) == 9 and len(loads) == 2


def test_zero_proposals_terminal_without_numeric_load_or_invented_winner(tmp_path, monkeypatch):
    root, _, calls, loads = setup(tmp_path, monkeypatch, count=0)
    result = ae.evaluate_application_accounts(root)
    assert result["status"] == "no_proposals" and result["selected"] is None
    assert calls == loads == [] and result["new_account_executions"] == 0
    with pytest.raises(ValueError, match="winner"):
        ae.evaluate_application_temporal(root)
    assert calls == loads == []


@pytest.mark.parametrize("mode", ["infeasible", "large_liquidation"])
def test_no_feasible_is_explicit_and_respects_liquidation_estimate(tmp_path, monkeypatch, mode):
    root, _, calls, _ = setup(tmp_path, monkeypatch, mode=mode)
    result = ae.evaluate_application_accounts(root)
    assert len(calls) == 6 and result["status"] == "no_feasible_portfolio" and result["selected"] is None
    with pytest.raises(ValueError, match="winner"):
        ae.evaluate_application_temporal(root)


@pytest.mark.parametrize("mode", ["daily_mismatch", "trades_mismatch", "annual_mismatch", "dtype_mismatch"])
def test_exact_prefix_failure_retains_actual_outputs_and_refuses_implicit_retry(tmp_path, monkeypatch, mode):
    root, folder, calls, _ = setup(tmp_path, monkeypatch, mode=mode)
    ae.evaluate_application_accounts(root)
    with pytest.raises(ValueError, match="saved fitting prefix"):
        ae.evaluate_application_temporal(root)
    destination = folder / "accounts/temporal/I2/base"
    assert (destination / "daily.parquet").exists() and (destination / "trades.parquet").exists()
    assert ae.read(destination / "prefix_check.json")["passed"] is False
    assert (folder / "temporal_failure.json").exists()
    previous_calls = len(calls)
    with pytest.raises(ValueError, match="unfinished"):
        ae.evaluate_application_temporal(root)
    assert len(calls) == previous_calls


def test_real_failure_preserves_completed_stresses_and_fixed_expected_units(tmp_path, monkeypatch):
    root, folder, calls, _ = setup(tmp_path, monkeypatch, mode="raise_capacity")
    with pytest.raises(RuntimeError, match="synthetic"):
        ae.evaluate_application_accounts(root)
    failure = ae.read(folder / "account_failure.json")
    assert failure["started_accounts"] == 3 and len(failure["completed_accounts"]) == 2
    assert len(failure["expected_accounts"]) == 6 and (folder / "accounts/fit/I1/base/daily.parquet").exists()
    assert not (folder / "account_stage_result.json").exists()
    with pytest.raises(ValueError, match="unfinished"):
        ae.evaluate_application_accounts(root)
    assert len(calls) == 3


@pytest.mark.parametrize("change", ["model", "score", "source", "counts", "fit_future", "old_records"])
def test_frozen_metadata_or_source_drift_rejected_before_numeric_read(tmp_path, monkeypatch, change):
    root, folder, calls, loads = setup(tmp_path, monkeypatch)
    if change in {"model", "source", "score"}:
        path = {"model": root / "model_calls/05_information_application_design/admitted_receipt.json",
                "source": root / "preparation/frozen_source.py",
                "score": root / "cycles" / ae.FACTOR_CYCLE / "factors/new_factor/scores.parquet"}[change]
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "counts":
        path = folder / "combination_declaration.json"; value = ae.read(path); value["prior_proposals_retained"] = 0; write(path, value)
    elif change == "fit_future":
        path = root / "cycles" / ae.FACTOR_CYCLE / "fit_factor_view.json"; value = ae.read(path); value["2021_2024_result_values_included"] = True; write(path, value)
    else:
        path = root / "factor_index.json"; value = ae.read(path); value["factors"].pop(); write(path, value)
    with pytest.raises(ValueError):
        ae.evaluate_application_accounts(root)
    assert calls == loads == [] and not (folder / "account_execution_intent.json").exists()


def test_cancel_before_numeric_read_retains_intent_and_failure(tmp_path, monkeypatch):
    root, folder, calls, loads = setup(tmp_path, monkeypatch)
    (folder / "cancel.request").write_text("cancel", encoding="utf-8")
    with pytest.raises(ValueError, match="cancelled"):
        ae.evaluate_application_accounts(root)
    assert (folder / "account_execution_intent.json").exists() and (folder / "account_failure.json").exists()
    assert calls == loads == []


def test_saved_artifact_tamper_blocks_reuse(tmp_path, monkeypatch):
    root, folder, calls, _ = setup(tmp_path, monkeypatch)
    ae.evaluate_application_accounts(root)
    path = folder / "accounts/fit/I2/base/daily.parquet"
    path.write_bytes(path.read_bytes() + b"x")
    with pytest.raises(ValueError, match="artifact changed"):
        ae.evaluate_application_accounts(root)
    assert len(calls) == 6


def test_zero_variance_later_year_remains_unknown(tmp_path, monkeypatch):
    root, _, _, _ = setup(tmp_path, monkeypatch, mode="zero_later")
    ae.evaluate_application_accounts(root)
    result = ae.evaluate_application_temporal(root)
    assert result["observations"]["base"]["full_continuous_account"]["mean_full_year_sharpe"] is None
    assert next(r for r in result["observations"]["base"]["annual"] if r["year"] == 2023)["sharpe"] is None


def test_call05_original_response_is_pinned_and_rechecked_during_dispatch(tmp_path, monkeypatch):
    root, folder, calls, _ = setup(tmp_path, monkeypatch)
    call = root / "model_calls" / ae.DESIGN_CALL
    response = call / "response.json"
    save_once(response, {"original": "generated call05 bytes"})
    receipt = ae.read(call / "admitted_receipt.json")
    receipt["artifact_sha256"] = {"response.json": file_hash(response)}
    write(call / "admitted_receipt.json", receipt)
    declaration = ae.read(folder / "combination_declaration.json")
    declaration["source_receipt_sha256"] = file_hash(call / "admitted_receipt.json")
    declaration["input_artifacts"] = [ae._proof(call / "admitted_receipt.json")]
    write(folder / "combination_declaration.json", declaration)
    original_load = ae.load_panel
    def mutate_after_intent(path):
        panel = original_load(path)
        response.write_text('{"changed": true}', encoding="utf-8")
        return panel
    monkeypatch.setattr(ae, "load_panel", mutate_after_intent)
    with pytest.raises(ValueError, match="artifact changed"):
        ae.evaluate_application_accounts(root)
    assert not calls
    assert (folder / "account_failure.json").exists()


def test_no_silent_temporal_reselection_after_fit_summary_mutation(tmp_path, monkeypatch):
    root, folder, calls, loads = setup(tmp_path, monkeypatch)
    ae.evaluate_application_accounts(root)
    path = folder / "accounts/fit/I2/base/derived_summary.json"
    summary = ae.read(path); summary["mean_full_year_sharpe"] += 1
    write(path, summary)
    with pytest.raises(ValueError, match="artifact changed"):
        ae.evaluate_application_temporal(root)
    assert len(calls) == 6 and len(loads) == 1
    assert not (folder / "temporal_intent.json").exists()


def test_required_score_replacement_during_read_is_not_blessed(tmp_path, monkeypatch):
    root, folder, calls, _ = setup(tmp_path, monkeypatch)
    original = pd.read_parquet
    def changed(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if Path(path).name == "scores.parquet":
            Path(path).write_bytes(Path(path).read_bytes() + b"changed")
        return result
    monkeypatch.setattr(pd, "read_parquet", changed)
    with pytest.raises(ValueError, match="score changed during"):
        ae.evaluate_application_accounts(root)
    assert not calls and (folder / "account_failure.json").exists()


def test_recovery_router_uses_only_explicit_receipt_and_never_calls_old_compiler(tmp_path, monkeypatch):
    import sys
    from quanta_agents.meta_v6 import information_application
    calls = []
    monkeypatch.setattr(information_application, "verify_application_declaration", lambda root: calls.append("original") or (1, 2, 3, 4))
    module = SimpleNamespace(verify_recovered_application_declaration=lambda root: calls.append("recovered") or (5, 6, 7, 8))
    monkeypatch.setitem(sys.modules, "quanta_agents.meta_v6.application_reference_recovery", module)
    assert ae._declaration(tmp_path) == (1, 2, 3, 4)
    receipt = tmp_path / "cycles" / ae.CYCLE / "reference_recovery_receipt.json"
    save_once(receipt, {"generated_fixture": True})
    assert ae._declaration(tmp_path) == (5, 6, 7, 8)
    assert calls == ["original", "recovered"]


def test_incomplete_recovery_is_rejected_without_fallback(tmp_path, monkeypatch):
    import sys
    from quanta_agents.meta_v6 import information_application
    def old_forbidden(root):
        raise AssertionError("recovery refusal must not fall back to the original compiler")
    def recovery_refuses(root):
        raise ValueError("unverified generated recovery")
    monkeypatch.setattr(information_application, "verify_application_declaration", old_forbidden)
    monkeypatch.setitem(sys.modules, "quanta_agents.meta_v6.application_reference_recovery",
                        SimpleNamespace(verify_recovered_application_declaration=recovery_refuses))
    save_once(tmp_path / "cycles" / ae.CYCLE / "reference_recovery_receipt.json", {"status": "incomplete"})
    with pytest.raises(ValueError, match="unverified"):
        ae._declaration(tmp_path)


def test_completed_recovery_proofs_are_bound_into_account_intent(tmp_path, monkeypatch):
    root, folder, calls, _ = setup(tmp_path, monkeypatch, count=0)
    intent = folder / "reference_recovery_intent.json"
    save_once(intent, {"generated_original_failure": True})
    failure = folder / "original_compilation_failure.json"
    save_once(failure, {"status": "original rejected reference retained"})
    receipt = {"status": "completed", "intent_sha256": file_hash(intent), "economic_decisions_unchanged": True,
        "original_assessment_refs_restored": True, "model_calls": 0, "account_executions": 0,
        "input_artifacts": [ae._proof(failure)], "source_proofs": [],
        "artifacts": [ae._proof(folder / "combination_declaration.json"), ae._proof(folder / "application_declaration.json")]}
    save_once(folder / "reference_recovery_receipt.json", receipt)
    ae.evaluate_application_accounts(root)
    proof_paths = {Path(p["path"]).name for p in ae.read(folder / "account_execution_intent.json")["input_artifacts"]}
    assert {"reference_recovery_receipt.json", "reference_recovery_intent.json", "original_compilation_failure.json",
            "application_reference_recovery.py"} <= proof_paths
    assert calls == []
    failure.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        ae.evaluate_application_accounts(root)
