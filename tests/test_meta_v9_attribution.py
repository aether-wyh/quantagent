"""Independent synthetic pool allocation, execution and attribution checks."""
from copy import deepcopy
from dataclasses import asdict
import json

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.portfolio import AccountPolicy
from quanta_agents.meta_v7.attribution import compare_accounts, equal_pool_benchmark


def market():
    dates = pd.bdate_range("2019-01-01", periods=145)
    columns = ["sh600003", "sh600001", "sh600004", "sh600002"]
    price = pd.DataFrame(10., index=dates, columns=columns)
    fields = {name: price.copy() for name in ("open", "close", "raw_open", "raw_prev_close", "high", "low")}
    fields.update({"adjustment_factor": price * 0 + 1, "volume": price * 10000,
        "amount": price * 10_000_000, "is_st": price * 0, "is_delisting": price * 0,
        "open_observed": price * 0 + 1, "bar_observed": price * 0 + 1})
    return MarketPanel(fields, price.notna(), {"fixture": "synthetic_only"})


def policy(**changes):
    values = dict(capital=100_000., risk_free_rate=0., buy_commission=0., sell_commission=0.,
        sell_levy_before_2023_08_28=0., sell_levy_from_2023_08_28=0.,
        slippage=0., min_commission=0., lot_size=1, max_prior_day_amount_fraction=1.)
    return AccountPolicy(**{**values, **changes})


def run(p=None, **allocation):
    p = p or market()
    return equal_pool_benchmark(p, start=p.dates[120], end=p.dates[135],
        allocation={"top_n": 1, "rebalance_sessions": 1, "gross_exposure": .8,
                    "max_stock_weight": 1., **allocation}, policy=policy())


def test_pool_uses_every_name_normalizes_actual_count_and_fills_next_session():
    p = market()
    p.eligible.iloc[122:, 0] = False
    p.fields["is_st"].iloc[125:, 1] = 1.
    result = run(p)
    targets = result["targets"]
    assert targets.iloc[0].to_numpy() == pytest.approx([.2] * 4)
    assert targets.loc[p.dates[122]].to_numpy() == pytest.approx([0., .8/3, .8/3, .8/3])
    assert targets.loc[p.dates[125]].to_numpy() == pytest.approx([0., 0., .4, .4])
    assert targets.sum(axis=1).to_numpy() == pytest.approx([.8] * len(targets))
    assert set(result["trades"].loc[result["trades"].date == p.dates[120], "code"]) == set(p.symbols)
    assert result["trades"].signal_date.min() == p.dates[119]
    assert result["benchmark"]["top_n_applied"] is False
    assert result["summary"]["cost_multiplier"] == 1.


def test_binding_caps_leave_declared_cash_and_empty_pool_stays_cash():
    p = market()
    p.eligible.iloc[125:] = False
    result = run(p, max_stock_weight=.1)
    assert result["targets"].iloc[0].sum() == pytest.approx(.4)
    assert result["targets"].loc[p.dates[125]:].sum(axis=1).eq(0).all()
    assert result["benchmark"]["cap_redistribution"] is False


def test_pool_results_ignore_values_after_end_and_preserve_input():
    p = market()
    original = p.copy()
    before = run(p)
    for frame in p.fields.values():
        frame.iloc[136:] = np.nan
    p.eligible.iloc[136:] = False
    after = run(p)
    assert_frame_equal(before["targets"], after["targets"])
    assert_frame_equal(before["daily"], after["daily"])
    assert_frame_equal(original.eligible.iloc[:136], p.eligible.iloc[:136])


@pytest.mark.parametrize("allocation", [{"weighting": "inverse_volatility"}, {"membership_buffer": 3}])
def test_pool_rejects_controls_it_cannot_apply(allocation):
    with pytest.raises(ValueError):
        run(**allocation)


def test_pool_honors_cancellation_before_account():
    p = market()
    with pytest.raises(InterruptedError, match="cancelled"):
        equal_pool_benchmark(p, start=p.dates[120], end=p.dates[135], allocation={},
            policy=policy(), cancelled=lambda: True)


def account(returns, *, exposure=.8, account_policy=None):
    p = account_policy or policy()
    returns = np.asarray(returns, dtype=float)
    dates = pd.bdate_range("2020-01-01", periods=len(returns))
    daily = pd.DataFrame({"return": returns, "nav": p.capital * (1 + returns).cumprod(),
        "exposure": exposure, "fees": 1., "slippage": 2., "turnover": .1}, index=dates)
    return {"daily": daily, "policy": asdict(p), "summary": {"cost_multiplier": 1.}}


def test_negative_absolute_pnl_can_have_positive_relative_result():
    candidate = account([-.01, -.02, -.01, -.02], exposure=.6)
    benchmark = account([-.03, -.04, -.02, -.03], exposure=.9)
    result = compare_accounts(candidate, benchmark)
    assert result["candidate"]["net_return"] < 0
    assert result["benchmark"]["net_return"] < result["candidate"]["net_return"]
    expected = np.prod([.99, .98, .99, .98]) / np.prod([.97, .96, .98, .97]) - 1
    assert result["net_excess"]["cumulative_relative_return"] == pytest.approx(expected)
    assert result["net_excess"]["information_ratio"] > 0
    assert result["differences"]["mean_exposure"] == pytest.approx(-.3)
    assert result["exposure_matched"] is False
    assert result["formal_financial_success"] is False
    json.dumps(result, allow_nan=False)


def test_ols_recovers_known_descriptive_relation_and_same_account_zero_excess():
    base = np.array([-.02, -.01, .01, .02, 0.])
    result = compare_accounts(account(.001 + .5 * base), account(base))
    assert result["ols"]["beta"] == pytest.approx(.5)
    assert result["ols"]["daily_intercept"] == pytest.approx(.001)
    assert result["ols"]["r_squared"] == pytest.approx(1.)
    assert result["ols"]["causal_alpha_estimated"] is False
    same = compare_accounts(account(base), account(base))
    assert same["net_excess"]["cumulative_relative_return"] == 0.
    assert same["net_excess"]["information_ratio"] is None


@pytest.mark.parametrize("change", ["calendar", "missing", "policy", "multiplier", "nav", "partial_policy"])
def test_mismatched_costs_or_observations_are_rejected_without_row_dropping(change):
    candidate = account([-.01, .02, .01, -.02])
    benchmark = deepcopy(candidate)
    if change == "calendar":
        benchmark["daily"].index += pd.Timedelta(days=1)
    elif change == "missing":
        benchmark["daily"].iloc[1, 0] = np.nan
    elif change == "policy":
        benchmark["policy"]["slippage"] = .003
    elif change == "multiplier":
        benchmark["summary"]["cost_multiplier"] = 2.
    elif change == "nav":
        benchmark["daily"].iloc[2, 1] += 100
    else:
        del benchmark["policy"]["lot_size"]
    with pytest.raises(ValueError):
        compare_accounts(candidate, benchmark)


def test_degenerate_ols_is_unknown_not_zero_evidence():
    result = compare_accounts(account([.01, .02, .03]), account([0., 0., 0.]))
    assert result["ols"]["status"] == "not_evaluable"
    assert result["ols"]["beta"] is None
    assert result["ols"]["daily_intercept"] is None
