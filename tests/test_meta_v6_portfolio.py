"""Independent synthetic checks of signal timing and continuous account economics."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quanta_agents.meta_v6.portfolio import (
    AccountPolicy, DailyAccount, PortfolioSpec, account_metrics, target_weights,
)


def panel(*, periods=150, stocks=3, start="2019-07-01"):
    dates = pd.bdate_range(start, periods=periods)
    columns = [f"sh60000{i}" for i in range(stocks)]
    price = pd.DataFrame(10., index=dates, columns=columns)
    fields = {name: price.copy() for name in ("open", "close", "raw_open", "raw_prev_close", "high", "low")}
    fields.update({"adjustment_factor": price * 0 + 1, "volume": price * 10000,
        "amount": price * 10_000_000, "is_st": price * 0, "is_delisting": price * 0,
        "open_observed": price * 0 + 1, "bar_observed": price * 0 + 1})
    return SimpleNamespace(fields=fields, eligible=price.notna(), provenance={})


def policy(**kwargs):
    values = dict(capital=10_000., risk_free_rate=0., buy_commission=0., sell_commission=0.,
                  sell_levy_before_2023_08_28=0., sell_levy_from_2023_08_28=0.,
                  slippage=0., min_commission=0., lot_size=1, max_prior_day_amount_fraction=1.)
    return AccountPolicy(**{**values, **kwargs})


def targets(p, positions, weights):
    return pd.DataFrame(weights, index=p.eligible.index[list(positions)], columns=p.eligible.columns)


def run(p, t, *, account_policy=None, start_i=1, end_i=None, cost_multiplier=1.):
    end_i = len(p.eligible) - 1 if end_i is None else end_i
    return DailyAccount(p, account_policy or policy()).run(t, start=p.eligible.index[start_i],
        end=p.eligible.index[end_i], cost_multiplier=cost_multiplier)


def test_targets_respect_120_session_warmup_missing_slots_and_next_day_execution():
    p = panel()
    score = p.fields["close"] * 0
    score.iloc[:, 0] = 3
    score.iloc[:, 1] = 2
    score.iloc[:, 2] = np.nan
    spec = PortfolioSpec("top3", {"factor": 1.}, top_n=3, rebalance_sessions=1, max_stock_weight=1.)
    weights = target_weights(p, {"factor": score}, spec, start=p.eligible.index[118], end=p.eligible.index[122])
    assert weights.loc[p.eligible.index[117:119]].eq(0).all().all()
    assert weights.loc[p.eligible.index[119]].sum() == pytest.approx(2/3)
    assert weights.loc[p.eligible.index[119], p.eligible.columns[2]] == 0
    result = run(p, weights, start_i=118, end_i=122)
    assert result["trades"].date.min() == p.eligible.index[120]
    assert result["trades"].signal_date.min() == p.eligible.index[119]
    assert result["daily"].loc[p.eligible.index[118:120], "trade_count"].eq(0).all()


def test_every_active_factor_required_without_silent_per_stock_reweight():
    p = panel()
    first = p.fields["close"].copy()
    second = first.copy()
    first.iloc[:, 0] = 999
    second.iloc[:, 0] = np.nan
    spec = PortfolioSpec("combo", {"first": 1., "second": 1.}, top_n=1, rebalance_sessions=1, max_stock_weight=1.)
    weights = target_weights(p, {"first": first, "second": second}, spec,
                             start=p.eligible.index[120], end=p.eligible.index[125])
    assert weights.iloc[:, 0].eq(0).all()
    assert weights.sum(axis=1).eq(1).all()


@pytest.mark.parametrize("market_filter", ["none", "trend60", "trend120"])
def test_future_market_values_cannot_change_earlier_targets_or_fills(market_filter):
    p = panel(periods=160)
    growth = np.arange(len(p.eligible))[:, None] * np.array([.01, .015, .02])[None, :]
    for name in ("open", "close", "raw_open", "raw_prev_close", "high", "low"):
        p.fields[name] += growth
    score = p.fields["close"].pct_change(3, fill_method=None)
    spec = PortfolioSpec("causal", {"factor": 1.}, top_n=2, rebalance_sessions=2,
                         max_stock_weight=.5, market_filter=market_filter)
    before_targets = target_weights(p, {"factor": score}, spec,
        start=p.eligible.index[125], end=p.eligible.index[155])
    before = run(p, before_targets, start_i=125, end_i=155)
    boundary = p.eligible.index[140]
    for name in ("open", "close", "raw_open", "raw_prev_close", "high", "low"):
        p.fields[name].iloc[140:] *= 8
    p.fields["volume"].iloc[140:] = 0
    p.fields["amount"].iloc[140:] = 0
    p.fields["is_st"].iloc[140:] = 1
    p.fields["is_delisting"].iloc[140:] = 1
    p.fields["open_observed"].iloc[140:] = 0
    p.eligible.iloc[140:] = False
    changed_score = p.fields["close"].pct_change(3, fill_method=None)
    after_targets = target_weights(p, {"factor": changed_score}, spec,
        start=p.eligible.index[125], end=p.eligible.index[155])
    after = run(p, after_targets, start_i=125, end_i=155)
    assert_frame_equal(before_targets.loc[before_targets.index < boundary], after_targets.loc[after_targets.index < boundary])
    assert_frame_equal(before["daily"].loc[before["daily"].index < boundary], after["daily"].loc[after["daily"].index < boundary])
    assert_frame_equal(before["trades"].loc[before["trades"].date < boundary].reset_index(drop=True),
                       after["trades"].loc[after["trades"].date < boundary].reset_index(drop=True))


def test_open_fill_cannot_depend_on_same_day_volume_amount_high_low_close_or_eligible():
    p = panel(periods=4, stocks=1)
    t = targets(p, [0], [[.5]])
    before = run(p, t, end_i=1)
    for name in ("volume", "amount"):
        p.fields[name].iloc[1] = 0
    for name in ("high", "low", "close"):
        p.fields[name].iloc[1] = np.nan
    p.eligible.iloc[1] = False
    after = run(p, t, end_i=1)
    assert len(before["trades"]) == 1
    assert_frame_equal(before["trades"], after["trades"])
    assert after["daily"].iloc[0].stale_value > 0


def test_holdings_and_cash_continue_across_year_boundary():
    p = panel(periods=4, stocks=1, start="2019-12-30")
    p.fields["close"].iloc[:, 0] = [10., 11., 12., 9.]
    p.fields["open"].iloc[:, 0] = [10., 10., 11., 10.]
    p.fields["raw_open"] = p.fields["open"].copy()
    t = targets(p, [0], [[1.]])
    result = run(p, t)
    assert len(result["trades"]) == 1
    assert result["daily"].nav.tolist() == pytest.approx([11_000., 12_000., 9_000.])
    assert result["daily"]["return"].tolist() == pytest.approx([.1, 12/11-1, 9/12-1])
    annual = result["annual"].set_index("year")
    assert annual.loc[2019, "return"] == pytest.approx(.1)
    assert annual.loc[2020, "return"] == pytest.approx(9/11-1)
    assert result["summary"]["return"] == pytest.approx(-.1)


def test_roundtrip_commission_levy_and_slippage_are_charged_once():
    p = panel(periods=4, stocks=1)
    t = targets(p, [0, 1], [[.5], [0.]])
    costs = policy(buy_commission=.001, sell_commission=.001,
                   sell_levy_before_2023_08_28=.002, slippage=.01)
    result = run(p, t, account_policy=costs)
    trades = result["trades"]
    assert trades.side.tolist() == ["buy", "sell"]
    assert trades.adjusted_units.tolist() == [500., 500.]
    assert trades.price.tolist() == pytest.approx([10.1, 9.9])
    expected_fees = 5_050*.001 + 4_950*(.001+.002)
    expected_slip = 500*.1*2
    assert trades.fees.sum() == pytest.approx(expected_fees)
    assert result["daily"].fees.sum() == pytest.approx(expected_fees)
    assert result["summary"]["fees"] == pytest.approx(expected_fees)
    assert result["daily"].iloc[-1]["nav"] == pytest.approx(costs.capital - expected_fees - expected_slip)
    assert result["daily"].iloc[-1].position_value == 0
    assert result["daily"].iloc[-1].fees == 0


def test_limit_up_buy_limit_down_sell_and_missing_open_do_not_fill():
    p = panel(periods=5, stocks=3)
    p.fields["open"].iloc[1] = [11., 10., np.nan]
    p.fields["raw_open"].iloc[1] = [11., 10., np.nan]
    p.fields["open"].iloc[2, 1] = 9.
    p.fields["raw_open"].iloc[2, 1] = 9.
    t = targets(p, [0, 1], [[.3, .3, .3], [0., 0., 0.]])
    result = run(p, t)
    assert result["trades"].code.tolist() == [p.eligible.columns[1]]
    assert result["trades"].side.tolist() == ["buy"]
    assert result["daily"].iloc[1].blocked_orders >= 1
    assert result["daily"].iloc[-1].position_value > 0


def test_missing_observation_flag_blocks_fill_even_if_numeric_placeholders_exist():
    p = panel(periods=3, stocks=1)
    p.fields["open_observed"].iloc[1, 0] = 0.
    result = run(p, targets(p, [0], [[.5]]))
    assert result["trades"].empty, "unobserved opening prices must not become executable fills"


def test_missing_open_exit_is_counted_as_blocked_order():
    p = panel(periods=4, stocks=1)
    p.fields["open"].iloc[2, 0] = np.nan
    p.fields["raw_open"].iloc[2, 0] = np.nan
    result = run(p, targets(p, [0, 1], [[.5], [0.]]))
    assert result["trades"].side.tolist() == ["buy"]
    assert result["daily"].iloc[1].blocked_orders == 1, "a known full-exit target must retain its blocked intent"


def test_cash_stays_nonnegative_under_minimum_fees_lots_and_turnover():
    p = panel(periods=8, stocks=3)
    t = targets(p, [0, 1, 2, 3, 4, 5, 6], [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.],
        [1/3, 1/3, 1/3], [1., 0., 0.], [0., 1., 0.], [0., 0., 0.]])
    costs = policy(capital=3_000., min_commission=17., lot_size=100,
                   buy_commission=.003, sell_commission=.003, slippage=.002)
    result = run(p, t, account_policy=costs)
    assert result["daily"].cash.ge(0).all()
    assert result["daily"].exposure.between(0, 1).all()
    assert np.allclose(result["daily"].nav, result["daily"].cash + result["daily"].position_value)
    assert np.allclose(result["trades"].raw_share_equivalent % 100, 0)
    assert result["daily"].nav.le(costs.capital + 1e-7).all()


def test_cost_stress_reduces_same_flat_price_roundtrip_nav():
    p = panel(periods=4, stocks=1)
    t = targets(p, [0, 1], [[.5], [0.]])
    costs = policy(buy_commission=.001, sell_commission=.001,
                   sell_levy_before_2023_08_28=.002, slippage=.002)
    results = [run(p, t, account_policy=costs, cost_multiplier=x) for x in (0., 1., 2.)]
    assert all(len(result["trades"]) == 2 for result in results)
    values = [result["daily"].nav.iloc[-1] for result in results]
    assert values[0] == costs.capital
    assert values[0] > values[1] > values[2]
    assert results[2]["summary"]["cost_multiplier"] == 2.
    assert results[2]["summary"]["formal_target_success"] is False


def metric_frame(dates, returns, capital=10_000.):
    returns = np.asarray(returns, dtype=float)
    frame = pd.DataFrame({"return": returns, "nav": capital*np.cumprod(1+returns)}, index=pd.DatetimeIndex(dates))
    for name in ("fees", "slippage", "turnover", "exposure", "stale_value", "stale_fraction",
                 "oldest_held_mark_sessions", "trade_count", "blocked_orders"):
        frame[name] = 0.
    return frame


def test_full_year_average_keeps_negative_year_and_constant_year_disables_comparison():
    dates = ["2019-01-02", "2019-12-31", "2020-01-02", "2020-12-31"]
    frame = metric_frame(dates, [.03, -.01, -.03, .01])
    summary, annual = account_metrics(frame, policy(), start="2019-01-01", end="2020-12-31",
                                      expected_calendar=pd.DatetimeIndex(dates))
    assert annual.sharpe.iloc[0] > 0 and annual.sharpe.iloc[1] < 0
    assert summary["mean_full_year_sharpe"] == pytest.approx(annual.sharpe.mean())
    assert summary["full_years"] == 2
    flat_year = metric_frame(dates, [.03, -.01, 0., 0.])
    summary, annual = account_metrics(flat_year, policy(), start="2019-01-01", end="2020-12-31",
                                      expected_calendar=pd.DatetimeIndex(dates))
    assert summary["full_years"] == 2
    assert summary["mean_full_year_sharpe"] is None
    assert summary["all_full_year_sharpes_available"] is False
    assert summary["threshold_exceeded_on_supplied_simulation"] is False


def test_missing_requested_calendar_year_cannot_disappear_from_target_comparison():
    dates = ["2019-01-02", "2019-12-31", "2021-01-04", "2021-12-31"]
    frame = metric_frame(dates, [.03, -.01, .03, -.01])
    expected = pd.DatetimeIndex(sorted(dates + ["2020-01-02", "2020-12-31"]))
    summary, annual = account_metrics(frame, policy(), start="2019-01-01", end="2021-12-31",
                                      expected_calendar=expected)
    assert summary["mean_full_year_sharpe"] is None, "the absent 2020 must not silently leave the denominator"
    assert summary["all_full_year_sharpes_available"] is False
    assert summary["full_years"] == 3
    assert annual.set_index("year").loc[2020, "sessions"] == 0
    assert not annual.set_index("year").loc[2020, "calendar_complete"]


def test_terminal_cost_estimate_uses_the_applicable_year_levy():
    p = panel(periods=3, stocks=1, start="2019-01-02")
    costs = policy(slippage=.001, sell_commission=.0003,
                   sell_levy_before_2023_08_28=.001, sell_levy_from_2023_08_28=.0005)
    result = run(p, targets(p, [0], [[.5]]), account_policy=costs)
    expected = result["summary"]["terminal_inventory_value"] * (.001+.0003+.001)
    assert result["summary"]["terminal_liquidation_cost_estimate"] == pytest.approx(expected)
    assert result["summary"]["terminal_liquidation_executed"] is False


def test_one_missing_calendar_session_blocks_full_year_target_comparison():
    dates = ["2019-01-02", "2019-12-31"]
    frame = metric_frame(dates, [.03, -.01])
    expected = pd.DatetimeIndex(["2019-01-02", "2019-06-03", "2019-12-31"])
    summary, annual = account_metrics(frame, policy(), start="2019-01-01", end="2019-12-31",
                                      expected_calendar=expected)
    assert annual.iloc[0].expected_sessions == 3
    assert not annual.iloc[0].calendar_complete
    assert summary["mean_full_year_sharpe"] is None
    assert summary["threshold_exceeded_on_supplied_simulation"] is False


def test_flagged_special_delisting_exit_uses_observed_open_without_old_limit_floor():
    p = panel(periods=4, stocks=2)
    p.fields["is_delisting"].iloc[2:] = 1
    p.fields["is_st"].iloc[2:] = 1
    for name in ("open", "raw_open", "close"):
        p.fields[name].iloc[2:] = 2.
    t = targets(p, [0, 1], [[.5, 0.], [0., .5]])
    result = run(p, t)
    assert result["trades"].side.tolist() == ["buy", "sell"]
    assert result["trades"].code.nunique() == 1  # cannot open new delisting positions
    assert result["trades"].iloc[1].price == 2.
    assert result["daily"].nav.iloc[-1] == 6_000.
    assert result["daily"].iloc[-1].position_value == 0.
    assert result["summary"]["execution_certified"] is False
