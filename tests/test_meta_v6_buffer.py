"""Synthetic checks for executed-inventory buffers and causal crowding rules."""
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.portfolio import AccountPolicy, DailyAccount, PortfolioSpec, target_weights


def panel(stocks=45):
    dates = pd.bdate_range("2019-01-01", "2019-08-30")
    columns = [f"sh{600000 + i:06d}" for i in range(stocks)]
    price = pd.DataFrame(10., index=dates, columns=columns)
    fields = {key: price.copy() for key in ("open", "close", "high", "low", "raw_open", "raw_prev_close")}
    fields.update({"amount": price * 1_000_000, "volume": price * 10000,
                   "adjustment_factor": price * 0 + 1, "is_st": price * 0,
                   "is_delisting": price * 0, "open_observed": price * 0 + 1})
    return SimpleNamespace(fields=fields, eligible=price.notna(), provenance={})


def zero_cost():
    # Isolate membership/cash mechanics without costs or lot rounding noise.
    return AccountPolicy(capital=10_000., risk_free_rate=0., buy_commission=0., sell_commission=0.,
                         sell_levy_before_2023_08_28=0., sell_levy_from_2023_08_28=0.,
                         slippage=0., min_commission=0., lot_size=1, max_prior_day_amount_fraction=1.)


def score(p):
    values = np.tile(np.arange(len(p.eligible.columns), 0, -1), (len(p.eligible), 1)).astype(float)
    return pd.DataFrame(values, index=p.eligible.index, columns=p.eligible.columns)


def generate(p, scores, spec, start, end):
    return target_weights(p, scores, spec, start=start, end=end)


def run(p, weights, start, end):
    return DailyAccount(p, zero_cost()).run(weights, start=start, end=end)


def transfer_with_attrs(weights):
    # Mimic a data handoff where numeric weights and the selection sidecar are
    # explicitly transferred together, not an implicit historical target state.
    transferred = pd.DataFrame(weights.to_numpy(copy=True), index=weights.index.copy(),
                               columns=weights.columns.copy())
    transferred.attrs = deepcopy(weights.attrs)
    return transferred


def test_weekly_last_actual_session_signals_execute_next_actual_session():
    p = panel(stocks=2)
    # Synthetic Friday closure: Thursday July 4 is this week's last session.
    closed = pd.Timestamp("2019-07-05")
    p.fields = {key: value.drop(index=closed) for key, value in p.fields.items()}
    p.eligible = p.eligible.drop(index=closed)
    alpha = score(p)
    alpha.loc["2019-07-04":"2019-07-11"] = [1., 2.]
    spec = PortfolioSpec("weekly", {"alpha": 1.}, top_n=1, max_stock_weight=1.,
                         rebalance_schedule="weekly_last_session")
    weights = generate(p, {"alpha": alpha}, spec, "2019-07-01", "2019-07-16")
    assert weights.index.tolist() == list(pd.to_datetime(["2019-06-28", "2019-07-04", "2019-07-12"]))
    result = run(p, weights, "2019-07-01", "2019-07-16")
    trades = result["trades"]
    assert trades.date.tolist() == list(pd.to_datetime([
        "2019-07-01", "2019-07-08", "2019-07-08", "2019-07-15", "2019-07-15"]))
    assert trades.signal_date.tolist() == list(pd.to_datetime([
        "2019-06-28", "2019-07-04", "2019-07-04", "2019-07-12", "2019-07-12"]))
    assert trades.side.tolist() == ["buy", "sell", "buy", "sell", "buy"]


def buffer_fixture():
    p = panel()
    alpha = score(p)
    # A starts first, falls to rank 40, then rank 41. B becomes first.
    alpha.loc["2019-07-02", p.eligible.columns[0]] = 5.5
    alpha.loc["2019-07-03":, p.eligible.columns[0]] = 4.5
    spec = PortfolioSpec("actual-inventory-buffer", {"alpha": 1.}, top_n=1,
                         max_stock_weight=1., rebalance_sessions=1, membership_buffer=40)
    return p, alpha, spec


def test_buffer_40_retains_actual_rank_40_holding_and_exits_at_rank_41():
    p, alpha, spec = buffer_fixture()
    weights = generate(p, {"alpha": alpha}, spec, "2019-07-02", "2019-07-04")
    a, b = p.eligible.columns[:2]
    # Numeric preview alone selects B; the actual retained inventory is supplied
    # only by the account via its frozen selection plans.
    assert weights.loc["2019-07-02", a] == 0 and weights.loc["2019-07-02", b] == 1
    assert weights.attrs["selection_plans"]["2019-07-02"]["order"].index(0) == 39
    assert weights.attrs["selection_plans"]["2019-07-03"]["order"].index(0) == 40
    result = run(p, transfer_with_attrs(weights), "2019-07-02", "2019-07-04")
    assert result["trades"].code.tolist() == [a, a, b]
    assert result["trades"].side.tolist() == ["buy", "sell", "buy"]
    assert result["trades"].date.tolist() == list(pd.to_datetime(["2019-07-02", "2019-07-04", "2019-07-04"]))


@pytest.mark.parametrize("blocked_by", ["limit_up", "unobserved_open", "zero_prior_capacity"])
def test_unfilled_old_selection_is_not_retained_as_a_holding(blocked_by):
    p, alpha, spec = buffer_fixture()
    a, b = p.eligible.columns[:2]
    if blocked_by == "limit_up":
        p.fields["open"].loc["2019-07-02", a] = 11.
        p.fields["raw_open"].loc["2019-07-02", a] = 11.
    elif blocked_by == "unobserved_open":
        p.fields["open_observed"].loc["2019-07-02", a] = 0.
    else:
        p.fields["amount"].loc["2019-07-01", a] = 0.
    weights = generate(p, {"alpha": alpha}, spec, "2019-07-02", "2019-07-03")
    assert weights.loc["2019-07-01", a] == 1.
    result = run(p, transfer_with_attrs(weights), "2019-07-02", "2019-07-03")
    assert result["trades"].code.tolist() == [b], "an unfilled A must not displace the current top-ranked B"
    assert result["trades"].date.tolist() == [pd.Timestamp("2019-07-03")]
    assert result["daily"].loc["2019-07-02", "cash"] == 10_000.
    assert result["daily"].loc["2019-07-02", "position_value"] == 0.


def test_partial_real_fill_counts_as_held_for_the_buffer():
    p, alpha, spec = buffer_fixture()
    a = p.eligible.columns[0]
    p.fields["amount"].loc["2019-07-01", a] = 100.
    weights = generate(p, {"alpha": alpha}, spec, "2019-07-02", "2019-07-03")
    result = run(p, transfer_with_attrs(weights), "2019-07-02", "2019-07-03")
    assert result["trades"].code.tolist() == [a, a]
    assert result["trades"].side.tolist() == ["buy", "buy"]
    assert result["trades"].notional.tolist() == pytest.approx([100., 9_900.])


@pytest.mark.parametrize("five_day_end,expected_high_weight,expected_cash", [
    (11., .1, 1_000.), (10., .2, 0.), (9., .2, 0.),
])
def test_crowding_uses_raw_high_quintile_and_positive_five_day_return_without_redistribution(
        five_day_end, expected_high_weight, expected_cash):
    p = panel(stocks=5)
    raw_crowding = score(p)
    raw_crowding.loc[:, :] = np.arange(1., 6.)
    high = p.eligible.columns[-1]
    p.fields["close"].loc["2019-07-01", high] = five_day_end
    # A negative signal orientation must not invert which raw score is crowded.
    spec = PortfolioSpec("raw-crowding-gate", {"crowding": -1.}, top_n=5, max_stock_weight=1.,
                         crowding_gate_factor="crowding", membership_buffer=40)
    weights = generate(p, {"crowding": raw_crowding}, spec, "2019-07-02", "2019-07-02")
    assert weights.iloc[0, :-1].tolist() == pytest.approx([.2] * 4)
    assert weights.iloc[0, -1] == pytest.approx(expected_high_weight)
    plan = weights.attrs["selection_plans"]["2019-07-01"]
    assert plan["gate"][:-1] == [1.] * 4
    assert plan["gate"][-1] == (0.5 if five_day_end > 10 else 1.)
    result = run(p, transfer_with_attrs(weights), "2019-07-02", "2019-07-02")
    assert result["daily"].iloc[0].cash == pytest.approx(expected_cash)
    by_code = result["trades"].set_index("code")["notional"]
    assert by_code.loc[high] == pytest.approx(10_000. * expected_high_weight)
    assert by_code.drop(high).tolist() == pytest.approx([2_000.] * 4)


def test_future_perturbation_cannot_change_old_plans_or_trades_after_attrs_handoff():
    p = panel()
    alpha = score(p)
    for i in range(len(alpha)):
        alpha.iloc[i] = np.roll(alpha.iloc[i].to_numpy(), i // 5)
    crowding = score(p) * -1
    spec = PortfolioSpec("causal-buffer-and-gate", {"alpha": 1.}, top_n=5,
                         max_stock_weight=.2, rebalance_schedule="weekly_last_session",
                         membership_buffer=40, crowding_gate_factor="crowding")
    start, end, boundary = "2019-07-01", "2019-08-15", pd.Timestamp("2019-07-22")
    weights = generate(p, {"alpha": alpha, "crowding": crowding}, spec, start, end)
    original = run(p, transfer_with_attrs(weights), start, end)
    changed = deepcopy(p)
    for key in ("open", "close", "raw_open", "raw_prev_close", "high", "low"):
        changed.fields[key].loc[boundary:] = 12.
    changed.fields["amount"].loc[boundary:] *= 100.
    changed.eligible.loc[boundary:] = False
    new_alpha, new_crowding = alpha.copy(), crowding.copy()
    new_alpha.loc[boundary:] *= -1000.
    new_crowding.loc[boundary:] *= -1000.
    regenerated = generate(changed, {"alpha": new_alpha, "crowding": new_crowding}, spec, start, end)
    for day, plan in weights.attrs["selection_plans"].items():
        if pd.Timestamp(day) < boundary:
            assert regenerated.attrs["selection_plans"][day] == plan
    assert weights.attrs["selection_plans"] != regenerated.attrs["selection_plans"]
    for passed in (weights, regenerated):
        after = run(changed, transfer_with_attrs(passed), start, end)
        assert_frame_equal(original["daily"].loc[lambda frame: frame.index < boundary],
                           after["daily"].loc[lambda frame: frame.index < boundary])
        assert_frame_equal(original["trades"].loc[lambda frame: frame.date < boundary].reset_index(drop=True),
                           after["trades"].loc[lambda frame: frame.date < boundary].reset_index(drop=True))
