"""Synthetic frozen-account files with a mocked account and mocked market load."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6 import temporal
from quanta_agents.meta_v6.portfolio import AccountPolicy, PortfolioSpec, account_metrics
from quanta_agents.meta_v6.portfolio_study import save_account
from quanta_agents.meta_v6.research import PROTOCOL, save_once


@pytest.fixture(autouse=True)
def forbid_unmocked_market_and_account(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("a synthetic temporal test attempted a real market load/account")
    monkeypatch.setattr(temporal, "load_panel", forbidden)
    monkeypatch.setattr(temporal, "DailyAccount", forbidden)


def _write(path, value):
    save_once(path, value)


def synthetic_native(policy, dates, *, zero_year=None):
    # Two synthetic observations per year; never presented as an exchange
    # calendar or executed market account. NAV/return identities are exact.
    actual = dates[dates.year >= 2016]
    returns = np.tile([.03, .01], 9)
    if policy.slippage > .001:
        returns -= .001
    if policy.max_prior_day_amount_fraction < .01:
        returns -= .002
    if zero_year is not None:
        returns[actual.year == zero_year] = 0.
    nav = policy.capital * np.cumprod(1 + returns)
    daily = pd.DataFrame({"nav": nav, "return": returns, "cash": nav * .2,
                          "position_value": nav * .8, "exposure": .8, "fees": 10.,
                          "slippage": 1., "turnover": .1, "trade_count": 1,
                          "blocked_orders": 0, "stale_value": 0., "stale_fraction": 0.,
                          "oldest_held_mark_sessions": 0}, index=actual)
    daily.index.name = "date"
    summary, annual = account_metrics(daily, policy, start=temporal.START, end=temporal.END, expected_calendar=dates)
    summary.update({"terminal_liquidation_cost_estimate": 1000., "terminal_liquidation_executed": False,
                    "accounting_mode": "synthetic_fixture_no_market_execution"})
    trades = pd.DataFrame({"date": [actual[0]], "side": ["synthetic"], "code": ["sh600000"]})
    return {"daily": daily, "annual": annual, "summary": summary, "trades": trades, "policy": asdict(policy)}


def setup(tmp_path, monkeypatch, *, prefix_change=None, zero_year=None):
    root = tmp_path / "synthetic_research"
    root.mkdir()
    dates = pd.DatetimeIndex(["2015-12-31", *[day for year in range(2016, 2025)
        for day in (f"{year}-01-04", f"{year}-12-31")]])
    columns = pd.Index(["sh600000"])
    panel = SimpleNamespace(dates=dates, eligible=pd.DataFrame(True, index=dates, columns=columns),
                            fingerprint=lambda: "synthetic-panel")
    _write(root / "protocol.json", PROTOCOL)
    spec = PortfolioSpec("A", {"synthetic_factor": 1.}, top_n=1, max_stock_weight=1., membership_buffer=40)
    other = PortfolioSpec("B", {"never_load_unselected_factor": 1.}, top_n=1, max_stock_weight=1.)
    declaration = {"specs": [asdict(spec), asdict(other)],
                   "implementation_sha256": temporal.file_hash(Path(temporal.__file__).with_name("portfolio.py"))}
    _write(root / "combination_declaration.json", declaration)
    admission = {"runtime_identity": {"verified": True}, "response": {"decisions": [
        {"candidate": "A", "decision": "admit_for_account_test"}]}}
    admission_path = root / "model_calls/02_combination_admission/admitted_receipt.json"
    _write(admission_path, admission)
    _write(root / "account_execution_intent.json", {
        "declaration_sha256": temporal.file_hash(root / "combination_declaration.json"),
        "admission_sha256": temporal.file_hash(admission_path), "allowed": ["A"]})
    policy = AccountPolicy()
    policies = {"base": policy, "slippage_x2": replace(policy, slippage=.002),
                "capacity_half": replace(policy, max_prior_day_amount_fraction=.005)}
    native, fit, summaries = {}, {}, {}
    for stress, pol in policies.items():
        native[stress] = synthetic_native(pol, dates, zero_year=zero_year)
        fit[stress] = native[stress]["daily"].loc[:temporal.FIT_END].copy()
        summary, annual = account_metrics(fit[stress], pol, start=temporal.START, end=temporal.FIT_END,
                                          expected_calendar=dates)
        summary.update({"terminal_liquidation_cost_estimate": 1000., "terminal_liquidation_executed": False})
        summary["net_excess_over_rf_growth"] = 1 + summary["return"] - (1 + pol.risk_free_rate) ** (len(fit[stress]) / 252)
        summary["net_excess_after_estimated_liquidation"] = summary["net_excess_over_rf_growth"] - .001
        summaries[stress] = summary
        save_account(root / "accounts/fit/A" / stress, {"daily": fit[stress], "trades": native[stress]["trades"],
                     "annual": annual, "summary": summary, "policy": asdict(pol)})
    winner = {"candidate": "A", "portfolio_id": spec.portfolio_id, "stress_feasible": True, "results": summaries}
    _write(root / "accounts/fit/A/result.json", winner)
    selection = {"selected": "A", "frozen_before_temporal_results": True, "training_observations": [winner],
                 "formal_target_success": False}
    _write(root / "selection.json", selection)
    _write(root / "account_stage_result.json", selection)
    _write(root / "fit_factor_view.json", {"synthetic_fixture": True, "2021_2024_result_values_included": False})
    _write(root / "factor_declaration.json", {"synthetic_fixture": True})
    score = root / "factors/synthetic/scores.parquet"
    score.parent.mkdir(parents=True)
    pd.DataFrame(1., index=dates, columns=columns).to_parquet(score)
    _write(root / "factor_index.json", {
        "scope": {"panel_fingerprint": "synthetic-panel", "data_fingerprint": "synthetic-data"},
        "fit_factor_view_sha256": temporal.file_hash(root / "fit_factor_view.json"),
        "factor_declaration_sha256": temporal.file_hash(root / "factor_declaration.json"),
        "factors": [{"name": "synthetic_factor", "status": "evaluated", "scores_path": str(score),
                     "data_fingerprint": "synthetic-data", "artifacts": [{"path": str(score), "sha256": temporal.file_hash(score)}]}]})
    monkeypatch.setattr(temporal, "load_panel", lambda path: panel)
    target_calls, account_calls = [], []

    def target_weights(market, scores, selected, *, start, end):
        assert market is panel and selected == spec
        assert list(scores) == ["synthetic_factor"]
        target_calls.append((selected.name, start, end))
        result = pd.DataFrame([[1.]], index=dates[:1], columns=columns)
        result.attrs = {"selection_plans": {"2015-12-31": {"synthetic_fixture": True}}, "portfolio_spec": asdict(spec)}
        return result

    class MockAccount:
        def __init__(self, market, pol):
            assert market is panel
            self.key = next(name for name, value in policies.items() if value == pol)
            self.policy = pol
        def run(self, targets, *, start, end, cancelled):
            assert targets.attrs["selection_plans"]["2015-12-31"]["synthetic_fixture"]
            assert not cancelled()
            account_calls.append((self.key, start, end, self.policy.capital))
            result = deepcopy(native[self.key])
            if prefix_change == self.key:
                result["daily"].iloc[2, result["daily"].columns.get_loc("cash")] += .000001
            if prefix_change == "missing_2024":
                result["daily"] = result["daily"].loc[:"2023-12-31"].copy()
            if prefix_change == "changed_returned_policy":
                result["policy"]["capital"] = 2_000_000.
            return result

    monkeypatch.setattr(temporal, "target_weights", target_weights)
    monkeypatch.setattr(temporal, "DailyAccount", MockAccount)
    return root, panel, native, fit, target_calls, account_calls


def test_one_frozen_winner_three_continuous_accounts_exact_prefix_and_correct_subperiod_capital(tmp_path, monkeypatch):
    root, panel, native, fit, targets, accounts = setup(tmp_path, monkeypatch)
    original_selection = (root / "selection.json").read_bytes()
    result = temporal.evaluate_temporal(root)
    assert result["selected"] == "A" and result["winner_reselected"] is False
    assert targets == [("A", "2016-01-01", "2024-12-31")]
    assert accounts == [(stress, "2016-01-01", "2024-12-31", 1_000_000.) for stress in temporal.STRESSES]
    assert (root / "selection.json").read_bytes() == original_selection
    for stress in temporal.STRESSES:
        row = result["observations"][stress]
        assert [year["year"] for year in row["annual"]] == list(range(2016, 2025))
        assert row["full_continuous_account"]["full_years"] == 9
        assert row["fit_prefix_check"]["all_fields_exact"] is True
        opening = float(fit[stress].nav.iloc[-1])
        segment = row["temporal_2021_2024"]["summary"]
        assert segment["opening_nav_from_2020_close"] == opening
        assert segment["opening_nav_from_2020_close"] != 1_000_000.
        assert segment["return"] == pytest.approx(native[stress]["daily"].nav.iloc[-1] / opening - 1)
        assert segment["account_restarted"] is False
        saved = pd.read_parquet(root / "accounts/temporal/A" / stress / "daily.parquet")
        assert_frame_equal(saved.loc[:"2020-12-31"], fit[stress], check_exact=True)
    assert result["formal_target_success"] is False and result["financial_success"] is False
    assert result["model_calls"] == 0 and result["new_account_executions"] == 3


def test_completed_stage_reloads_only_its_verified_artifacts_without_new_account(tmp_path, monkeypatch):
    root, _, _, _, targets, accounts = setup(tmp_path, monkeypatch)
    first = temporal.evaluate_temporal(root)
    second = temporal.evaluate_temporal(root)
    assert second == first
    assert len(accounts) == 3 and len(targets) == 1
    file = root / "accounts/temporal/A/base/prefix_check.json"
    file.write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="artifact changed"):
        temporal.evaluate_temporal(root)
    assert len(accounts) == 3


@pytest.mark.parametrize("stress", temporal.STRESSES)
def test_prefix_mismatch_preserves_actual_output_and_never_silently_reruns(tmp_path, monkeypatch, stress):
    root, _, _, _, _, accounts = setup(tmp_path, monkeypatch, prefix_change=stress)
    with pytest.raises(ValueError, match="differs from its saved training prefix"):
        temporal.evaluate_temporal(root)
    folder = root / "accounts/temporal/A" / stress
    assert (folder / "daily.parquet").is_file() and (folder / "summary.json").is_file()
    assert temporal.read(folder / "prefix_check.json")["passed"] is False
    assert temporal.read(root / "temporal_failure.json")["original_outputs_retained"] is True
    assert not (root / "temporal_stage_result.json").exists()
    count = len(accounts)
    with pytest.raises(ValueError, match="unfinished temporal stage"):
        temporal.evaluate_temporal(root)
    assert len(accounts) == count


def test_zero_variance_year_is_unknown_and_cannot_become_financial_success(tmp_path, monkeypatch):
    root, _, _, _, _, _ = setup(tmp_path, monkeypatch, zero_year=2023)
    result = temporal.evaluate_temporal(root)
    base = result["observations"]["base"]
    assert next(row for row in base["annual"] if row["year"] == 2023)["sharpe"] is None
    assert base["full_continuous_account"]["mean_full_year_sharpe"] is None
    assert base["temporal_2021_2024"]["summary"]["mean_full_year_sharpe"] is None
    assert result["financial_success"] is False


@pytest.mark.parametrize("mutation,expected", [("missing_2024", "omitted declared calendar"),
                                               ("changed_returned_policy", "different capital or policy")])
def test_truncated_output_or_changed_returned_policy_cannot_complete(tmp_path, monkeypatch, mutation, expected):
    root, _, _, _, _, accounts = setup(tmp_path, monkeypatch, prefix_change=mutation)
    with pytest.raises(ValueError, match=expected):
        temporal.evaluate_temporal(root)
    assert len(accounts) == 1
    assert (root / "accounts/temporal/A/base/daily.parquet").is_file()
    assert (root / "temporal_failure.json").is_file()
    assert not (root / "temporal_stage_result.json").exists()


@pytest.mark.parametrize("case", ["no_selection", "null_winner", "failed_fit_stress", "changed_scores", "extra_2025"])
def test_invalid_prerequisites_stop_before_any_account(tmp_path, monkeypatch, case):
    root, panel, _, _, _, accounts = setup(tmp_path, monkeypatch)
    if case == "no_selection":
        (root / "selection.json").unlink()
    elif case == "null_winner":
        path = root / "selection.json"
        value = temporal.read(path)
        value["selected"] = None
        path.write_text(__import__("json").dumps(value), encoding="utf-8")
    elif case == "failed_fit_stress":
        value = temporal.read(root / "selection.json")
        value["training_observations"][0]["stress_feasible"] = False
        for name in ("selection.json", "account_stage_result.json"):
            (root / name).write_text(__import__("json").dumps(value), encoding="utf-8")
    elif case == "changed_scores":
        (root / "factors/synthetic/scores.parquet").write_bytes(b"changed")
    else:
        panel.dates = panel.dates.append(pd.DatetimeIndex(["2025-01-02"]))
    with pytest.raises(ValueError):
        temporal.evaluate_temporal(root)
    assert accounts == []
    assert not (root / "temporal_intent.json").exists()
