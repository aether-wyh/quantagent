"""Synthetic-only execution integration; no asset, model or market-data calls."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.portfolio import AccountPolicy, DailyAccount, PortfolioSpec, target_weights
from quanta_agents.research_kernel import execution
from quanta_agents.research_kernel.compiler import CapabilityGap, strategy_id


def panel(stocks=45, *, first="2018-01-01", last="2020-12-31", flat=False):
    dates = pd.bdate_range(first, last)
    columns = [f"sh{600000 + j:06d}" for j in range(stocks)]
    t, j = np.arange(len(dates))[:, None], np.arange(stocks)[None, :]
    close = pd.DataFrame(12. * np.exp(np.cumsum(.0001 + .004 * np.sin(t / 11 + j), axis=0)),
                         index=dates, columns=columns)
    if flat:
        close[:] = 10.
    previous = close.shift(1).fillna(close.iloc[0])
    opening = previous * (1. + .001 * np.cos(t / 7 + j)) if not flat else close.copy()
    fields = {"open": opening, "close": close, "high": np.maximum(opening, close) * 1.005,
              "low": np.minimum(opening, close) * .995,
              "raw_open": opening.copy(), "raw_prev_close": previous.copy(),
              "volume": close * 0 + 1_000_000., "amount": close * 0 + 100_000_000.,
              "adjustment_factor": close * 0 + 1., "is_st": close * 0,
              "is_delisting": close * 0, "open_observed": close * 0 + 1.}
    return MarketPanel(fields, close.notna(), {"fixture": "generated_prices_not_real_research"})


def frames(p, count=5):
    t, j = np.arange(len(p.eligible))[:, None], np.arange(len(p.eligible.columns))[None, :]
    return {f"F{k}": pd.DataFrame(np.round(np.sin(t / (7 + k) + j * (k + .1)), 2),
                                  index=p.eligible.index, columns=p.eligible.columns)
            for k in range(1, count + 1)}


def factor(name):
    return {"op": "factor", "id": name}


def op(name, *args, **kw):
    return {"op": name, "args": list(args), **kw}


def const(value):
    return {"op": "constant", "value": value}


def spec(score=None, **allocation):
    return {"version": 1, "name": "synthetic", "score": score or factor("F1"),
            "allocation": {"top_n": 20, "gross_exposure": 1., "max_stock_weight": .05,
                           "weighting": "equal", "rebalance_sessions": 5,
                           "rebalance_schedule": "weekly_last_session", "membership_buffer": 40,
                           **allocation}}


def zero_cost():
    return AccountPolicy(capital=10_000., risk_free_rate=0., buy_commission=0., sell_commission=0.,
                         sell_levy_before_2023_08_28=0., sell_levy_from_2023_08_28=0.,
                         slippage=0., min_commission=0., lot_size=1, max_prior_day_amount_fraction=1.)


def test_r2_two_factor_explicit_rank_weekly_buffer_matches_v6_all_native_tables_exact():
    p = panel()
    scores = frames(p, 2)
    # Partial eligibility is tested before ranking, including missing alpha,
    # observable-history seasoning, ST and delisting exclusions.
    p.eligible.iloc[::17, 1] = False
    p.fields["is_st"].loc["2019-03-01":"2019-03-20", p.symbols[2]] = 1.
    p.fields["is_delisting"].loc["2020-06-01":, p.symbols[3]] = 1.
    scores["F1"].iloc[::13, 0] = np.nan
    old = PortfolioSpec("R2", {"F1": .5, "F2": -.5}, top_n=20, max_stock_weight=.05,
                        rebalance_schedule="weekly_last_session", membership_buffer=40)
    score = op("weighted_sum", op("rank", factor("F1")), op("rank", op("negate", factor("F2"))),
               weights=[.5, .5])
    declared = spec(score)
    declared["name"] = "R2"
    old_targets = target_weights(p, scores, old, start="2019-01-01", end="2020-12-31")
    baseline = DailyAccount(p).run(old_targets, start="2019-01-01", end="2020-12-31")
    result = execution.execute_strategy(p, scores, declared, start="2019-01-01", end="2020-12-31")
    for key in ("daily", "trades", "annual"):
        assert_frame_equal(result[key], baseline[key], check_exact=True, check_dtype=True)
    assert_frame_equal(result["targets"], old_targets, check_exact=True)
    assert result["targets"].attrs["selection_plans"] == old_targets.attrs["selection_plans"]
    for key in baseline["summary"]:
        if key != "duration_seconds":
            assert result["summary"][key] == baseline["summary"][key]
    assert result["policy"] == baseline["policy"]
    assert result["strategy_id"] == strategy_id(declared)
    assert result["diagnostics"]["mean_full_year_net_sharpe"] == baseline["annual"].sharpe.mean()
    assert result["diagnostics"]["formal_target_success"] is False


@pytest.mark.parametrize("count", [3, 5])
def test_arbitrary_three_and_five_factor_expressions_with_nonhardcoded_gate(count):
    p = panel(stocks=8, last="2019-08-30", flat=True)
    scores = frames(p, count)
    for k, value in enumerate(scores.values(), 1):
        value[:] = np.arange(8.) + k
    scores["custom_guard"] = scores["F1"] * 0 + 1.
    scores["custom_guard"].iloc[:, -1] = .5
    declared = spec(op("weighted_sum", *[factor(f"F{k}") for k in range(1, count + 1)],
                       weights=[1 / count] * count), top_n=2, max_stock_weight=.5,
                    rebalance_schedule="sessions", rebalance_sessions=1, membership_buffer=0)
    declared["gate"] = factor("custom_guard")
    result = execution.execute_strategy(p, scores, declared, start="2019-07-02", end="2019-07-02", policy=zero_cost())
    assert result["targets"].iloc[0, -2:].tolist() == [.5, .25]
    assert result["daily"].iloc[0].cash == 2500.
    assert set(result["trades"].code) == set(p.symbols[-2:])
    assert execution.strategy_factor_ids(declared) == set(scores)


def test_score_has_no_implicit_rank_or_direction_and_inputs_are_not_changed():
    p = panel(stocks=3, last="2019-08-30", flat=True)
    f = frames(p, 2)
    f["F1"][:] = [1., 2., 100.]
    f["F2"][:] = [100., 2., 1.]
    original = {key: value.copy(deep=True) for key, value in f.items()}
    declared = spec(op("add", factor("F1"), op("multiply", const(2), factor("F2"))),
                    top_n=1, max_stock_weight=1., membership_buffer=0)
    result = execution.execute_strategy(p, f, declared, start="2019-07-01", end="2019-07-03", policy=zero_cost())
    assert result["trades"].code.tolist() == [p.symbols[0]]
    for key in f:
        assert_frame_equal(f[key], original[key], check_exact=True)


@pytest.mark.parametrize("missing", [np.nan, 0.])
def test_missing_or_zero_gate_keeps_ranked_slot_cash_instead_of_opening_or_redistributing(missing):
    p = panel(stocks=3, last="2019-08-30", flat=True)
    f = frames(p, 1); f["F1"][:] = [3., 2., 1.]
    f["guard"] = f["F1"] * 0 + 1.; f["guard"].iloc[:, 0] = missing
    declared = spec(top_n=2, max_stock_weight=.5, membership_buffer=40)
    declared["gate"] = factor("guard")
    result = execution.execute_strategy(p, f, declared, start="2019-07-01", end="2019-07-01", policy=zero_cost())
    assert result["targets"].iloc[0].tolist() == [0., .5, 0.]
    assert result["daily"].iloc[0].cash == 5000.
    assert result["trades"].code.tolist() == [p.symbols[1]]
    key = "missing_gate_on_scored_cells" if np.isnan(missing) else "zero_gate_on_scored_cells"
    assert result["diagnostics"]["coverage"][key] == 1


def test_gate_applies_after_cap_and_inverse_risk_is_explicit_positive_and_generic():
    p = panel(stocks=3, last="2019-08-30", flat=True)
    f = frames(p, 1); f["F1"][:] = [3., 2., 1.]
    f["risk_measure"] = f["F1"] * 0; f["risk_measure"][:] = [1., 2., np.nan]
    f["guard"] = f["F1"] * 0 + 1.; f["guard"].iloc[:, 0] = .5
    declared = spec(top_n=2, max_stock_weight=.5, weighting="inverse_volatility", membership_buffer=40)
    declared.update(risk_score=factor("risk_measure"), gate=factor("guard"))
    result = execution.execute_strategy(p, f, declared, start="2019-07-01", end="2019-07-01", policy=zero_cost())
    assert result["targets"].iloc[0].tolist() == pytest.approx([.25, 1 / 3, 0.])
    assert result["diagnostics"]["coverage"]["invalid_or_missing_risk_on_scored_cells"] == 1
    assert result["daily"].iloc[0].cash >= 10_000 * (1 - .25 - 1 / 3)


def test_all_invalid_risk_is_cash_with_explicit_coverage_and_no_fabricated_sharpe():
    p = panel(stocks=3, last="2019-08-30", flat=True)
    f = frames(p, 1); f["risk_measure"] = f["F1"] * 0; f["risk_measure"][:] = [0., -1., np.nan]
    declared = spec(top_n=2, max_stock_weight=.5, weighting="inverse_volatility")
    declared["risk_score"] = factor("risk_measure")
    result = execution.execute_strategy(p, f, declared, start="2019-07-01", end="2019-07-05", policy=zero_cost())
    assert result["trades"].empty
    assert (result["daily"].cash == 10000).all()
    assert result["summary"]["sharpe"] is None
    assert result["diagnostics"]["coverage"]["invalid_or_missing_risk_on_scored_cells"] == 3


@pytest.mark.parametrize("invalid", [-.01, 1.01])
def test_out_of_range_gate_refused_before_account(monkeypatch, invalid):
    p = panel(stocks=2, last="2019-08-30")
    declared = spec(); declared["gate"] = const(invalid)
    monkeypatch.setattr(execution, "DailyAccount", lambda *a, **kw: pytest.fail("must not construct account"))
    with pytest.raises(ValueError, match="gate values"):
        execution.execute_strategy(p, frames(p, 1), declared, start="2019-07-01", end="2019-07-05")


@pytest.mark.parametrize("extra", [{"exit": {"stop_loss": .1}}, {"holding_minutes": 20},
                                  {"score": {"op": "cross_sectional_ols", "args": []}}])
def test_unknown_execution_capabilities_are_rejected_not_ignored(monkeypatch, extra):
    declared = spec(); declared.update(extra)
    monkeypatch.setattr(execution, "DailyAccount", lambda *a, **kw: pytest.fail("must not construct account"))
    with pytest.raises((ValueError, CapabilityGap)):
        execution.execute_strategy(None, {}, declared, start="2019-01-01", end="2019-12-31")


def test_missing_gate_asset_refuses_whole_strategy_not_silent_factor_subset():
    declared = spec(); declared["gate"] = factor("missing_guard")
    with pytest.raises(ValueError, match="required strategy factor frames unavailable"):
        execution.execute_strategy(None, {"F1": None}, declared, start="2019-01-01", end="2019-12-31")


def test_rank_pool_uses_history_liquidity_st_and_delisting_filters():
    p = panel(stocks=5, last="2019-08-30", flat=True)
    f = frames(p, 1); f["F1"][:] = [1., 2., 3., 4., 5.]
    p.fields["close"].iloc[-130:-25, 4] = np.nan  # Not 120 complete preceding sessions.
    p.fields["amount"].loc["2019-06-01":"2019-07-05", p.symbols[3]] = 0.
    p.fields["is_st"].loc["2019-06-28", p.symbols[2]] = 1.
    p.fields["is_delisting"].loc["2019-06-28", p.symbols[1]] = 1.
    declared = spec(op("rank", factor("F1")), top_n=1, max_stock_weight=1., membership_buffer=0)
    result = execution.execute_strategy(p, f, declared, start="2019-07-01", end="2019-07-01", policy=zero_cost())
    assert result["trades"].code.tolist() == [p.symbols[0]]
    assert result["diagnostics"]["coverage"]["seasoned_eligible_cells"] == 1


def test_buffer_uses_executed_holdings_not_unfilled_historical_target():
    p = panel(stocks=45, last="2019-08-30", flat=True)
    f = frames(p, 1); f["F1"][:] = np.arange(45., 0., -1)
    f["F1"].loc["2019-07-02", p.symbols[0]] = 5.5  # Prior top falls to rank 40.
    p.fields["open_observed"].loc["2019-07-02", p.symbols[0]] = 0.
    declared = spec(top_n=1, max_stock_weight=1., rebalance_schedule="sessions", rebalance_sessions=1)
    result = execution.execute_strategy(p, f, declared, start="2019-07-02", end="2019-07-03", policy=zero_cost())
    assert result["trades"].code.tolist() == [p.symbols[1]]
    assert result["trades"].date.tolist() == [pd.Timestamp("2019-07-03")]
    assert result["daily"].loc["2019-07-02", "cash"] == 10000.


def test_future_data_and_eligibility_cannot_change_prior_targets_plans_or_trades():
    p = panel(stocks=45, last="2019-08-30")
    f = frames(p, 3)
    declared = spec(op("weighted_sum", op("rank", factor("F1")),
                       op("rank", op("lag", factor("F2"), window=3)), weights=[.5, .5]))
    declared["gate"] = op("where", op("gt", factor("F3"), const(0)), const(.5), const(1))
    start, end, boundary = "2019-07-01", "2019-08-16", pd.Timestamp("2019-07-22")
    result = execution.execute_strategy(p, f, declared, start=start, end=end)
    changed = p.copy(); changed_frames = {key: value.copy(deep=True) for key, value in f.items()}
    for key in ("open", "close", "high", "low", "raw_open", "raw_prev_close"):
        changed.fields[key].loc[boundary:] *= 2.
    changed.fields["amount"].loc[boundary:] *= 20.
    changed.eligible.loc[boundary:] = False
    for frame in changed_frames.values():
        frame.loc[boundary:] *= -100.
    after = execution.execute_strategy(changed, changed_frames, declared, start=start, end=end)
    assert_frame_equal(result["targets"].loc[lambda x: x.index < boundary],
                       after["targets"].loc[lambda x: x.index < boundary], check_exact=True)
    for day, plan in result["targets"].attrs["selection_plans"].items():
        if pd.Timestamp(day) < boundary:
            assert plan == after["targets"].attrs["selection_plans"][day]
    assert_frame_equal(result["daily"].loc[lambda x: x.index < boundary],
                       after["daily"].loc[lambda x: x.index < boundary], check_exact=True)
    assert_frame_equal(result["trades"].loc[lambda x: x.date < boundary].reset_index(drop=True),
                       after["trades"].loc[lambda x: x.date < boundary].reset_index(drop=True), check_exact=True)


def test_short_evaluation_does_not_reject_on_later_invalid_gate():
    p = panel(stocks=2, last="2019-08-30")
    f = frames(p, 1); f["guard"] = f["F1"] * 0 + 1.
    f["guard"].loc["2019-08-01":] = 2.
    declared = spec(); declared["gate"] = factor("guard")
    execution.execute_strategy(p, f, declared, start="2019-07-01", end="2019-07-31")


def test_cancel_before_execution_and_during_actual_daily_loop_is_not_zero_return(monkeypatch):
    with pytest.raises(InterruptedError, match="cancelled"):
        execution.execute_strategy(None, {}, {}, start="2019-01-01", end="2019-12-31", cancelled=lambda: True)
    p = panel(stocks=2, last="2019-08-30")
    state = {"inside_account": False, "days": 0}
    original_run = DailyAccount.run
    def run(self, *args, **kwargs):
        state["inside_account"] = True
        return original_run(self, *args, **kwargs)
    def cancelled():
        if state["inside_account"]:
            state["days"] += 1
            return state["days"] >= 3
        return False
    monkeypatch.setattr(DailyAccount, "run", run)
    with pytest.raises(InterruptedError, match="cancelled"):
        execution.execute_strategy(p, frames(p, 1), spec(), start="2019-07-01", end="2019-07-31", cancelled=cancelled)
    assert state["days"] == 3


def test_diagnostics_cost_addback_is_observational_and_does_not_deduct_costs_twice():
    p = panel(stocks=2, last="2019-08-30", flat=True)
    f = frames(p, 1); f["F1"][:] = [2., 1.]
    result = execution.execute_strategy(p, f, spec(top_n=1, max_stock_weight=1., membership_buffer=0),
                                        start="2019-07-01", end="2019-07-02")
    cost = result["diagnostics"]["cost_observations"]
    assert cost["actual_fees"] == result["trades"].fees.sum()
    assert cost["observed_fill_slippage"] == result["trades"].slippage.sum()
    assert cost["net_pnl"] == result["daily"].nav.iloc[-1] - result["policy"]["capital"]
    assert cost["same_filled_unit_price_pnl"] == pytest.approx(0., abs=1e-8)
    assert cost["is_zero_cost_counterfactual"] is False
    assert result["diagnostics"]["negative_net_return"] is True
    assert result["diagnostics"]["causal_effect_estimated"] is False
    # Public diagnostics remain JSON-safe even when a full-year score is unavailable.
    json.dumps(result["diagnostics"], allow_nan=False)
