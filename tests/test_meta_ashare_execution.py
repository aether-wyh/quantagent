from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "src/quanta_agents/local_parquet_backtest.py"
SPEC = importlib.util.spec_from_file_location("meta_ashare_execution", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DATES = pd.bdate_range("2024-01-02", periods=3)
CODE = "sh600000"


def market(ratios=(1.0, 1.0, 1.0), raw_opens=(10.0, 10.0, 10.0)):
    bars = {}
    for day, ratio, raw_open in zip(DATES, ratios, raw_opens):
        bars[day] = pd.DataFrame([{
            "raw_code": CODE, "trade_date": day,
            "open": raw_open * ratio, "close": raw_open * ratio,
            "high": raw_open * ratio, "low": raw_open * ratio,
            "volume": 1_000_000.0, "qfq_ratio": ratio,
            "raw_open": raw_open, "raw_prev_close": raw_open,
            "prev_close": raw_open * ratio, "is_st": False, "is_delisting": False,
        }]).set_index("raw_code", drop=False)
    return {
        "start": DATES[0], "end": DATES[-1], "calendar_codes": (CODE,),
        "raw_codes": (CODE,), "market_dates": DATES, "bars_by_date": bars,
    }


def run(bundle=None, targets=(1.0, 0.0), capital=1005.0, **kwargs):
    bundle = market() if bundle is None else bundle
    weights = pd.DataFrame({CODE: targets}, index=DATES[:len(targets)])
    params = dict(
        start=DATES[0], end=DATES[-1], capital=capital,
        buy_cost=0.0003, sell_cost=0.0008, raw_share_lots=True,
        min_commission=5.0, prepared_market=bundle,
    )
    params.update(kwargs)
    return MODULE.run_target_weight_backtest(weights, **params)


@pytest.mark.parametrize("ratio", [0.25, 0.6, 1.0, 1.6])
def test_raw_lots_preserve_cash_notional_across_qfq_scales(ratio):
    result = run(market((ratio,) * 3), capital=10005.0)
    trades = result["_trades_df"]
    assert trades["side"].tolist() == ["buy", "sell"]
    assert trades["raw_shares"].tolist() == pytest.approx([1000.0, 1000.0])
    assert trades["shares"].tolist() == pytest.approx([1000.0 / ratio] * 2)
    assert trades["turnover"].tolist() == pytest.approx([10000.0] * 2)
    # Sell levy remains payable in addition to the minimum commission.
    assert trades["commission"].tolist() == pytest.approx([5.0, 10.0])
    assert result["end_balance"] == pytest.approx(9990.0)
    assert result["_daily_df"]["cash"].min() >= 0


@pytest.mark.parametrize("capital, expected_count", [(1004.99, 0), (1005.0, 2)])
def test_minimum_commission_is_reserved_before_buying(capital, expected_count):
    result = run(capital=capital)
    assert result["total_trade_count"] == expected_count
    assert result["_daily_df"]["cash"].min() >= 0
    if expected_count:
        assert result["_trades_df"]["commission"].tolist() == pytest.approx([5, 5.5])
        assert result["end_balance"] == pytest.approx(994.5)


def test_raw_lot_rounding_applies_to_buy_increment_after_adjustment():
    result = run(
        market((0.5, 0.5, 0.625)), targets=(0.5, 1.0), capital=2000.0,
        buy_cost=0.0, sell_cost=0.0, min_commission=0.0,
    )
    trades = result["_trades_df"]
    assert trades["side"].tolist() == ["buy", "buy"]
    assert trades["raw_shares"].tolist() == pytest.approx([100.0, 100.0])


def test_full_exit_sells_adjustment_residual_and_documents_approximation():
    result = run(market((0.5, 0.5, 0.625)))
    trades = result["_trades_df"]
    assert trades["raw_shares"].tolist() == pytest.approx([100.0, 125.0])
    assert result["_daily_df"].iloc[-1]["position_value"] == 0
    assert "approximation" in result["_backtest_debug"]["corporate_action_accounting"]
    assert result["_backtest_debug"]["capacity_verified"] is False


def test_signals_execute_next_open_and_inventory_is_not_sold_same_day():
    trades = run()["_trades_df"]
    assert trades["date"].tolist() == [DATES[1], DATES[2]]
    assert trades["side"].tolist() == ["buy", "sell"]


def test_same_day_final_close_and_volume_do_not_decide_open_orders():
    reference = run()
    perturbed = market()
    perturbed["bars_by_date"][DATES[1]].loc[CODE, ["close", "volume"]] = [0.0, 0.0]
    observed = run(perturbed)
    pd.testing.assert_frame_equal(reference["_trades_df"], observed["_trades_df"])


def test_missing_open_blocks_trade_without_looking_at_daily_volume():
    bundle = market()
    bundle["bars_by_date"][DATES[1]].loc[CODE, ["open", "raw_open"]] = [0.0, 0.0]
    result = run(bundle)
    assert result["total_trade_count"] == 0


def test_raw_price_limit_blocks_buy_even_when_adjusted_price_is_small():
    bundle = market((0.25,) * 3)
    bar = bundle["bars_by_date"][DATES[1]]
    bar.loc[CODE, ["raw_open", "open"]] = [11.0, 2.75]
    assert run(bundle)["total_trade_count"] == 0


def test_initial_capital_is_part_of_high_watermark():
    weights = pd.DataFrame({CODE: [1.0]}, index=[DATES[0] - pd.Timedelta(days=1)])
    result = MODULE.run_target_weight_backtest(
        weights, prepared_market=market(), start=DATES[0], end=DATES[-1],
        capital=1005.0, buy_cost=0.0003, sell_cost=0.0008,
        raw_share_lots=True, min_commission=5.0,
    )
    assert result["max_drawdown"] == pytest.approx(-5.0)
    assert result["max_ddpercent"] == pytest.approx(-5.0 / 1005.0)


@pytest.mark.parametrize("field,value", [("qfq_ratio", 0.0), ("open", 11.0)])
def test_invalid_or_inconsistent_share_conversion_fails_closed(field, value):
    bundle = market()
    bundle["bars_by_date"][DATES[1]].loc[CODE, field] = value
    with pytest.raises(ValueError, match="qfq_ratio|真实股数"):
        run(bundle)


@pytest.mark.parametrize("options", [
    {"min_commission": float("nan")}, {"min_commission": -1},
    {"lot_size": 0}, {"lot_size": 1.5}, {"raw_share_lots": "yes"},
    {"sell_cost": 0.0001},
])
def test_new_mode_rejects_invalid_execution_configuration(options):
    with pytest.raises(ValueError):
        run(**options)


def test_legacy_default_keeps_adjusted_unit_lots_and_no_minimum_fee():
    result = run(
        market((0.6,) * 3), capital=1005.0,
        raw_share_lots=False, min_commission=0.0,
    )
    trades = result["_trades_df"]
    assert trades["shares"].tolist() == pytest.approx([100.0, 100.0])
    assert "raw_shares" not in trades.columns
    assert trades["commission"].tolist() == pytest.approx([0.18, 0.48])
