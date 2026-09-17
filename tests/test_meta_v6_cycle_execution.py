"""Generated files and mocked accounts only: no models or real market reads."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta_v6 import cycle_execution as ce
from quanta_agents.meta_v6.portfolio import AccountPolicy, PortfolioSpec, account_metrics
from quanta_agents.meta_v6.portfolio_study import file_hash
from quanta_agents.meta_v6.research import PROTOCOL, save_once


@pytest.fixture(autouse=True)
def no_real_execution(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("generated cycle test attempted a real data/model/account call")
    monkeypatch.setattr(ce, "load_panel", forbidden)
    monkeypatch.setattr(ce, "DailyAccount", forbidden)
    from quanta_agents.meta_v6 import cycles, research
    monkeypatch.setattr(cycles, "call_researcher", forbidden)
    monkeypatch.setattr(research, "call_researcher", forbidden)


def fake_native(policy, dates, name, end, mode):
    days = dates[(dates >= ce.START) & (dates <= end)]
    returns = np.tile([.03, .01], 9)[:len(days)].copy()
    if policy.slippage > .001:
        returns -= .001
    if policy.max_prior_day_amount_fraction < .01:
        returns -= .002
    if mode == "no_feasible":
        returns[:] = 0.
    if mode == "zero_2023":
        returns[days.year == 2023] = 0.
    nav = policy.capital * np.cumprod(1 + returns)
    daily = pd.DataFrame({"nav": nav, "return": returns, "cash": nav * .2,
        "position_value": nav * .8, "exposure": .8, "fees": 10., "slippage": 1.,
        "turnover": .2 if name == "R1" else .1, "trade_count": 1, "blocked_orders": 0,
        "stale_value": 0., "stale_fraction": 0., "oldest_held_mark_sessions": 0}, index=days)
    daily.index.name = "date"
    summary, annual = account_metrics(daily, policy, start=ce.START, end=end, expected_calendar=dates)
    summary.update(terminal_liquidation_cost_estimate=1000., terminal_liquidation_executed=False,
                   accounting_mode="synthetic_fixture_no_market_execution")
    trades = pd.DataFrame({"date": [days[0]], "code": ["sh600000"], "side": ["synthetic"]})
    native = {"daily": daily, "trades": trades, "annual": annual, "summary": summary, "policy": asdict(policy)}
    if end == ce.END and mode == "prefix_mismatch":
        native["daily"].iloc[2, native["daily"].columns.get_loc("cash")] += .000001
    if end == ce.END and mode == "truncated":
        native["daily"] = daily.loc[:"2023-12-31"].copy()
    if mode == "wrong_policy":
        native["policy"]["capital"] *= 2
    return native


def setup(tmp_path, monkeypatch, *, proposal_count=2, mode=None):
    root = tmp_path / "generated_research"
    folder = root / "cycles" / ce.CYCLE
    dates = pd.DatetimeIndex(["2015-12-31", *[day for year in range(2016, 2025)
        for day in (f"{year}-01-04", f"{year}-12-31")]], name="date")
    columns = pd.Index(["sh600000"], name="symbol")
    panel = SimpleNamespace(dates=dates, eligible=pd.DataFrame(True, index=dates, columns=columns),
                            fingerprint=lambda: "generated-fixed-panel")
    save_once(root / "protocol.json", PROTOCOL)
    save_once(root / "account_stage_result.json", {"status": "no_admitted_combination"})
    rejection_path = root / "model_calls/02_combination_admission/admitted_receipt.json"
    save_once(rejection_path, {"runtime_identity": {"verified": True}, "response": {"decisions": [
        {"candidate": name, "decision": "reject"} for name in "ABCD"]}})
    fit = {"2021_2024_result_values_included": False, "factors": [
        {"factor_key": "F1", "name": "generated_price", "direction": -1, "status": "evaluated"},
        {"factor_key": "F2", "name": "generated_trend", "direction": 1, "status": "evaluated"}]}
    save_once(root / "fit_factor_view.json", fit)
    save_once(root / "factor_declaration.json", {"generated_fixture": True})
    entries = []
    for factor in fit["factors"]:
        path = root / "factors" / factor["name"] / "scores.parquet"
        path.parent.mkdir(parents=True)
        pd.DataFrame(1., index=dates, columns=columns).to_parquet(path)
        entries.append({"name": factor["name"], "status": "evaluated", "scores_path": str(path),
            "data_fingerprint": "generated-data", "artifacts": [{"path": str(path), "sha256": file_hash(path)}]})
    index = {"scope": {"panel_fingerprint": "generated-fixed-panel", "data_fingerprint": "generated-data"},
        "fit_factor_view_sha256": file_hash(root / "fit_factor_view.json"),
        "factor_declaration_sha256": file_hash(root / "factor_declaration.json"),
        "library_snapshot_id": "generated-library-snapshot", "factors": entries}
    save_once(root / "factor_index.json", index)
    protocol = {"cycle_id": ce.CYCLE, "capital": 1000000, "new_portfolio_proposals_max": 2,
        "new_factor_directions_allowed": False, "gross_exposure": 1., "max_stock_weight": .05,
        "prior_stage": {"result_sha256": file_hash(root / "account_stage_result.json"),
            "model_rejection_sha256": file_hash(rejection_path), "account_candidates_executed": 0},
        "fit_view_sha256": index["fit_factor_view_sha256"], "factor_library_snapshot_id": index["library_snapshot_id"]}
    save_once(folder / "protocol.json", protocol)
    proposals, specs = [], []
    for i in range(proposal_count):
        proposal = {"name": "generated_model_name_" + str(i), "components": [
            {"factor_key": "F1", "weight": .5}, {"factor_key": "F2", "weight": .5}],
            "top_n": 20, "membership_buffer": 40, "weighting": "equal", "market_filter": "none",
            "crowding_gate_factor_key": "", "hypothesis": "generated hypothesis", "falsification": "generated condition",
            "difference_from_other_candidate": "generated application"}
        proposals.append(proposal)
        specs.append(PortfolioSpec("R" + str(i + 1), {"generated_price": -.5, "generated_trend": .5},
            top_n=20, max_stock_weight=.05, rebalance_schedule="weekly_last_session", membership_buffer=40,
            metadata={"model_name": proposal["name"], "hypothesis": proposal["hypothesis"],
                "falsification": proposal["falsification"], "cycle_id": ce.CYCLE, "source_call": ce.DESIGN_CALL}))
    receipt_path = root / "model_calls" / ce.DESIGN_CALL / "admitted_receipt.json"
    save_once(receipt_path, {"runtime_identity": {"verified": True}, "response": {"portfolios": proposals}})
    declaration = {"specs": [asdict(spec) for spec in specs], "protocol_sha256": file_hash(folder / "protocol.json"),
        "source_receipt_sha256": file_hash(receipt_path),
        "implementation_sha256": file_hash(Path(ce.__file__).with_name("portfolio.py")),
        "new_proposals": proposal_count, "prior_proposals_retained": 4,
        "cumulative_proposals": 4 + proposal_count, "no_account_results_used_for_this_design": True}
    save_once(folder / "combination_declaration.json", declaration)
    calls, target_calls = [], []
    monkeypatch.setattr(ce, "load_panel", lambda path: panel)

    def targets(market, scores, spec, *, start, end):
        assert market is panel and spec.factor_weights == {"generated_price": -.5, "generated_trend": .5}
        assert set(scores) == {"generated_price", "generated_trend"}
        target_calls.append((spec.name, start, end))
        result = pd.DataFrame([[1.]], index=dates[:1], columns=columns)
        result.attrs = {"selection_plans": {"2015-12-31": {"generated_fixture": True}},
                        "portfolio_spec": asdict(spec)}
        return result

    class Account:
        def __init__(self, market, policy):
            assert market is panel
            self.policy = policy
        def run(self, targets, *, start, end, cancelled):
            assert not cancelled()
            assert targets.attrs["selection_plans"]["2015-12-31"]["generated_fixture"]
            name = targets.attrs["portfolio_spec"]["name"]
            key = next(k for k, v in ce._policies().items() if v == self.policy)
            calls.append((name, key, start, end, self.policy.capital))
            if mode == "raise_capacity" and key == "capacity_half":
                raise RuntimeError("generated worker failure")
            return fake_native(self.policy, dates, name, end, mode)
    monkeypatch.setattr(ce, "target_weights", targets)
    monkeypatch.setattr(ce, "DailyAccount", Account)
    return root, folder, panel, calls, target_calls


def test_two_model_portfolios_six_fit_accounts_tie_break_and_old_history_untouched(tmp_path, monkeypatch):
    root, folder, _, calls, targets = setup(tmp_path, monkeypatch)
    prior = (root / "account_stage_result.json").read_bytes()
    selection = ce.evaluate_cycle_accounts(root)
    assert selection["selected"] == "R2"  # Exact mean-Sharpe tie, lower turnover.
    assert selection["new_account_executions"] == 6 and selection["cumulative_portfolio_proposals"] == 6
    assert all(call[2:] == ("2016-01-01", "2020-12-31", 1_000_000.) for call in calls)
    assert targets == [(name, "2016-01-01", "2020-12-31") for name in ("R1", "R2")]
    assert (root / "account_stage_result.json").read_bytes() == prior
    assert not (root / "selection.json").exists() and not (root / "accounts").exists()
    assert not (folder / "accounts/temporal").exists()
    assert selection["frozen_before_temporal_results"] and selection["model_calls"] == 0
    assert selection["financial_success"] is False
    assert ce.evaluate_cycle_accounts(root) == selection
    assert len(calls) == 6


def test_frozen_winner_three_continuous_accounts_exact_prefix_and_boundary_nav(tmp_path, monkeypatch):
    root, folder, _, calls, targets = setup(tmp_path, monkeypatch)
    ce.evaluate_cycle_accounts(root)
    original_selection = (folder / "selection.json").read_bytes()
    result = ce.evaluate_cycle_temporal(root)
    assert result["selected"] == "R2" and result["new_account_executions"] == 3
    assert calls[6:] == [("R2", stress, "2016-01-01", "2024-12-31", 1_000_000.) for stress in ce.STRESSES]
    assert targets[-1] == ("R2", "2016-01-01", "2024-12-31")
    for stress, observation in result["observations"].items():
        fit = pd.read_parquet(folder / "accounts/fit/R2" / stress / "daily.parquet")
        full = pd.read_parquet(folder / "accounts/temporal/R2" / stress / "daily.parquet")
        pd.testing.assert_frame_equal(full.loc[:ce.FIT_END], fit, check_exact=True)
        segment = observation["temporal_2021_2024"]["summary"]
        assert segment["opening_nav_from_2020_close"] == fit.nav.iloc[-1] != 1_000_000.
        assert segment["return"] == pytest.approx(full.nav.iloc[-1] / fit.nav.iloc[-1] - 1)
        assert [row["year"] for row in observation["annual"]] == list(range(2016, 2025))
        assert observation["fit_prefix_check"]["all_fields_exact"]
    assert (folder / "selection.json").read_bytes() == original_selection
    assert result["formal_target_success"] is False and result["independent_holdout"] is False
    assert ce.evaluate_cycle_temporal(root) == result and len(calls) == 9


def test_zero_proposals_no_market_accounts_or_fabricated_winner(tmp_path, monkeypatch):
    root, _, _, calls, targets = setup(tmp_path, monkeypatch, proposal_count=0)
    def no_load(*args):
        raise AssertionError("empty cycle loaded market")
    monkeypatch.setattr(ce, "load_panel", no_load)
    result = ce.evaluate_cycle_accounts(root)
    assert result["selected"] is None and result["new_account_executions"] == 0
    assert calls == [] and targets == []
    with pytest.raises(ValueError, match="winner"):
        ce.evaluate_cycle_temporal(root)


def test_zero_variance_fit_infeasible_and_temporal_unknown_preserved(tmp_path, monkeypatch):
    root, _, _, calls, _ = setup(tmp_path / "zero_fit", monkeypatch, mode="no_feasible")
    result = ce.evaluate_cycle_accounts(root)
    assert len(calls) == 6 and result["selected"] is None
    assert all(row["stress_feasible"] is False for row in result["training_observations"])
    root, _, _, _, _ = setup(tmp_path / "zero_later", monkeypatch, mode="zero_2023")
    ce.evaluate_cycle_accounts(root)
    temporal = ce.evaluate_cycle_temporal(root)
    observed = temporal["observations"]["base"]
    assert observed["full_continuous_account"]["mean_full_year_sharpe"] is None
    assert observed["temporal_2021_2024"]["summary"]["mean_full_year_sharpe"] is None
    assert next(r for r in observed["annual"] if r["year"] == 2023)["sharpe"] is None


@pytest.mark.parametrize("mode,expected", [("prefix_mismatch", "saved fitting prefix"), ("truncated", "fixed calendar")])
def test_temporal_failure_retains_full_observed_files_and_no_automatic_rerun(tmp_path, monkeypatch, mode, expected):
    root, folder, _, calls, _ = setup(tmp_path, monkeypatch, mode=mode)
    ce.evaluate_cycle_accounts(root)
    with pytest.raises(ValueError, match=expected):
        ce.evaluate_cycle_temporal(root)
    assert (folder / "accounts/temporal/R2/base/daily.parquet").exists()
    assert (folder / "temporal_failure.json").exists() and not (folder / "temporal_stage_result.json").exists()
    count = len(calls)
    with pytest.raises(ValueError, match="unfinished"):
        ce.evaluate_cycle_temporal(root)
    assert len(calls) == count


@pytest.mark.parametrize("mode", ["raise_capacity", "wrong_policy"])
def test_fit_failures_retain_originals_and_prevent_rerun(tmp_path, monkeypatch, mode):
    root, folder, _, calls, _ = setup(tmp_path, monkeypatch, mode=mode)
    with pytest.raises((ValueError, RuntimeError)):
        ce.evaluate_cycle_accounts(root)
    assert (folder / "accounts/fit/R1/base/daily.parquet").exists()
    assert (folder / "account_failure.json").exists()
    assert not (folder / "selection.json").exists()
    count = len(calls)
    with pytest.raises(ValueError, match="unfinished"):
        ce.evaluate_cycle_accounts(root)
    assert len(calls) == count


@pytest.mark.parametrize("kind", ["receipt", "declaration", "scores", "prior_rejection", "future_view", "extra_2025"])
def test_changed_sources_or_unadmitted_scope_rejected_before_accounts(tmp_path, monkeypatch, kind):
    root, folder, panel, calls, _ = setup(tmp_path, monkeypatch)
    if kind == "extra_2025":
        panel.dates = panel.dates.append(pd.DatetimeIndex(["2025-01-02"]))
    else:
        path = {"receipt": root / "model_calls" / ce.DESIGN_CALL / "admitted_receipt.json",
            "declaration": folder / "combination_declaration.json",
            "scores": root / "factors/generated_price/scores.parquet",
            "prior_rejection": root / "model_calls/02_combination_admission/admitted_receipt.json",
            "future_view": root / "fit_factor_view.json"}[kind]
        if kind == "scores":
            path.write_bytes(b"changed")
        else:
            value = ce.read(path)
            if kind == "receipt":
                value["runtime_identity"]["verified"] = False
            elif kind == "declaration":
                value["specs"][0]["factor_weights"]["generated_price"] *= -1
            elif kind == "prior_rejection":
                value["response"]["decisions"][0]["decision"] = "admit_for_account_test"
            else:
                value["2021_2024_result_values_included"] = True
            path.write_text(__import__("json").dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        ce.evaluate_cycle_accounts(root)
    assert calls == [] and not (folder / "account_execution_intent.json").exists()


def test_output_hash_and_frozen_selection_cannot_be_rewritten(tmp_path, monkeypatch):
    root, folder, _, calls, _ = setup(tmp_path, monkeypatch)
    ce.evaluate_cycle_accounts(root)
    path = folder / "accounts/fit/R2/base/derived_summary.json"
    path.write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="artifact changed"):
        ce.evaluate_cycle_temporal(root)
    assert len(calls) == 6 and not (folder / "temporal_intent.json").exists()


def test_cancellation_and_exclusive_stage_claim(tmp_path, monkeypatch):
    root, folder, _, calls, _ = setup(tmp_path, monkeypatch)
    (folder / "cancel.request").touch()
    with pytest.raises(ValueError, match="cancellation"):
        ce.evaluate_cycle_accounts(root)
    assert calls == []
    (folder / "cancel.request").unlink()
    with pytest.raises(ValueError, match="unfinished"):
        ce.evaluate_cycle_accounts(root)
    with pytest.raises(FileExistsError):
        ce._claim(folder / "account_execution_intent.json", {})


@pytest.mark.parametrize("mutation", ["negative_weight", "boolean_weight", "rejected_direction", "third_proposal"])
def test_model_transcription_cannot_reverse_directions_or_expand_cycle(tmp_path, monkeypatch, mutation):
    root, _, _, calls, _ = setup(tmp_path, monkeypatch)
    proposals = ce.read(root / "model_calls" / ce.DESIGN_CALL / "admitted_receipt.json")["response"]["portfolios"]
    fit = ce.read(root / "fit_factor_view.json")
    if mutation == "negative_weight":
        proposals[0]["components"][0]["weight"] = -.5
    elif mutation == "boolean_weight":
        proposals[0]["components"][0]["weight"] = True
    elif mutation == "rejected_direction":
        fit["factors"].append({"factor_key": "F3", "name": "rejected_factor", "direction": 1, "status": "evaluated"})
        proposals[0]["components"][0]["factor_key"] = "F3"
    else:
        proposals.append(deepcopy(proposals[0]))
    with pytest.raises(ValueError):
        ce._compile_specs(proposals, fit)
    assert calls == []


def test_stress_gate_deducts_liquidation_before_comparing_risk_free_growth():
    policy = AccountPolicy()
    native = {"return": (1.02 ** 5 - 1) + .005, "sessions": 1260,
        "terminal_liquidation_cost_estimate": 10000., "mean_full_year_sharpe": 1.1,
        "all_full_year_sharpes_available": True, "turnover": 1.}
    annual = pd.DataFrame([{"year": year, "full_calendar_year": True,
                           "calendar_complete": True, "sharpe": 1.1} for year in range(2016, 2021)])
    derived = ce._summary(native, policy)
    assert derived["net_excess_over_rf_growth"] > 0
    assert derived["net_excess_after_estimated_liquidation"] < 0
    assert ce._feasible(derived, annual) is False
    native["terminal_liquidation_cost_estimate"] = 1000.
    assert ce._feasible(ce._summary(native, policy), annual) is True
