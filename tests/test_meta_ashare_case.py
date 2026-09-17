from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta import ashare_case
from quanta_agents.meta.ashare_case import AShareCase, baseline_strategy, validate_strategy


@pytest.fixture
def market_config(tmp_path: Path) -> dict:
    root = tmp_path / "market"
    root.mkdir()
    dates = pd.bdate_range("2020-01-01", "2020-12-31")
    names = [f"sh60000{i}" for i in range(7)] + ["sh688001"]
    for index, code in enumerate(names):
        daily = np.arange(len(dates), dtype=float)
        close = 10 + index + daily * 0.01 + np.sin(daily / 8 + index) * 0.1
        opening = close / 1.002
        frame = pd.DataFrame({
            "date": dates, "code": code,
            "open": opening, "close": close,
            "high": close * 1.01, "low": opening * 0.99,
            "volume": 10_000_000.0, "amount": 100_000_000.0,
            "float_market_cap": 1e9, "total_market_cap": 2e9,
            "qfq_ratio": 1.0, "raw_open": opening,
            "raw_prev_close": pd.Series(close).shift(1).fillna(close[0]),
            "prev_close": pd.Series(close).shift(1),
            "is_st": False, "is_delisting": False,
        })
        if code == "sh600006":
            frame["is_st"] = True
        frame.to_parquet(root / f"{code}.parquet", index=False)
    membership = tmp_path / "csi500.txt"
    # The highest-price eligible stock only joins in May. It must not be bought before then.
    membership.write_text("\n".join(
        f"{code.upper()}\t{'2020-05-01' if code == 'sh600005' else '2019-01-01'}\t2021-01-01"
        for code in names), encoding="utf-8")
    calendar = tmp_path / "days.txt"
    calendar.write_text("\n".join(dates.strftime("%Y-%m-%d")), encoding="utf-8")
    return {"data_root": str(root), "membership_path": str(membership),
            "calendar_path": str(calendar), "warmup_start": "2020-01-01",
            "min_history_days": 5, "min_average_amount": 0,
            "splits": {"development": {"start": "2020-02-01", "end": "2020-08-31"},
                       "confirmation": {"start": "2020-09-01", "end": "2020-10-30"},
                       "final": {"start": "2020-11-01", "end": "2020-12-31"}}}


def active_strategy() -> dict:
    return {"score_expression": "close", "filter_expression": "1", "top_n": 5,
            "rebalance_days": 5, "gross_exposure": 0.8}


def test_init_and_manifest_never_decode_market_rows(market_config, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("market rows decoded during metadata operation")

    monkeypatch.setattr(ashare_case.pq, "read_table", forbidden)
    case = AShareCase(market_config)
    manifest = case.manifest()
    assert case._loaded == {}
    assert manifest["final_sealed"]
    assert not manifest["promotion_enabled"]
    assert manifest["asset_file_count"] == 7
    assert manifest == case.manifest()
    json.dumps(manifest, allow_nan=False)


def test_development_decode_predicates_and_final_seal(market_config, monkeypatch):
    original = ashare_case.pq.read_table
    calls = []

    def observed(*args, **kwargs):
        calls.append(kwargs["filters"])
        return original(*args, **kwargs)

    monkeypatch.setattr(ashare_case.pq, "read_table", observed)
    case = AShareCase(market_config)
    packet = case.development_packet()
    assert packet["loaded_through"] == "2020-08-31"
    assert set(case._loaded) == {"development"}
    assert all(pd.Timestamp(filters[1][2]) == pd.Timestamp("2020-08-31") for filters in calls)
    assert case._loaded["development"]["fields"]["close"].index.max() == pd.Timestamp("2020-08-31")
    with pytest.raises(PermissionError, match="sealed"):
        case.evaluate(active_strategy(), "final")
    assert set(case._loaded) == {"development"}


def test_real_execution_adapter_historical_membership_st_lots_and_reuse(market_config):
    case = AShareCase(market_config)
    original_manifest = case.manifest()
    strategy = active_strategy()
    result = case.evaluate(strategy)
    assert result["scope"] == "integration_only"
    assert result["score"] == result["metrics"]["sharpe_ratio"]
    assert not result["promotion_enabled"]
    assert result["metrics"]["total_commission"] > 0
    assert result["metrics"]["terminal_position_value"] == pytest.approx(0)
    raw = next(iter(case._evaluation_raw.values()))
    trades = raw["_trades_df"]
    code_column = "code" if "code" in trades else "symbol"
    assert "sh600006" not in set(trades[code_column])
    future_member = trades.loc[trades[code_column].eq("sh600005")]
    if len(future_member):
        assert pd.to_datetime(future_member.date).min() >= pd.Timestamp("2020-05-01")
    buys = trades.loc[trades.side.eq("buy")]
    assert np.allclose(buys.raw_shares / 100, np.round(buys.raw_shares / 100))
    assert case.evaluate(strategy) == result
    assert len(case._evaluation_raw) == 1
    assert original_manifest == case.manifest()
    json.dumps(result, allow_nan=False)


def test_future_market_changes_cannot_change_development_results(market_config):
    first = AShareCase(market_config)
    strategy = active_strategy()
    result_before = first.evaluate(strategy)
    diagnosis_before = first.diagnose(strategy, "pct_change(close, 10)", 5)
    for path in Path(market_config["data_root"]).glob("*.parquet"):
        frame = pd.read_parquet(path)
        mask = frame.date > "2020-08-31"
        for column in ("open", "high", "low", "close", "raw_open", "raw_prev_close", "prev_close"):
            frame.loc[mask, column] *= 3
        frame.to_parquet(path, index=False)
    second = AShareCase(market_config)
    result_after = second.evaluate(strategy)
    diagnosis_after = second.diagnose(strategy, "pct_change(close, 10)", 5)
    assert result_after["metrics"] == result_before["metrics"]
    assert diagnosis_after["groups"] == diagnosis_before["groups"]
    assert diagnosis_after["yearly"] == diagnosis_before["yearly"]
    assert diagnosis_after["groups_by_year"] == diagnosis_before["groups_by_year"]
    assert diagnosis_after["paired_daily_spread"] == diagnosis_before["paired_daily_spread"]
    assert first._loaded["development"]["content_sha256"] == second._loaded["development"]["content_sha256"]


def test_changed_snapshot_rejected_before_decoding(market_config):
    case = AShareCase(market_config)
    path = Path(market_config["data_root"]) / "sh600000.parquet"
    frame = pd.read_parquet(path)
    frame["amount"] *= 2
    frame.to_parquet(path, index=False)
    with pytest.raises(RuntimeError, match="snapshot changed"):
        case.development_packet()


@pytest.mark.parametrize("change", [
    {"score_expression": "lag(close, -1)"},
    {"filter_expression": "forward_return > 0"},
    {"score_expression": "close.shift(-1)"},
    {"top_n": True}, {"gross_exposure": float("nan")}, {"rebalance_days": 0},
])
def test_unsafe_or_unbounded_strategy_rejected(change):
    strategy = baseline_strategy()
    strategy.update(change)
    with pytest.raises(ValueError):
        validate_strategy(strategy)


def test_diagnostic_is_bounded_to_development_and_records_gross_limit(market_config):
    case = AShareCase(market_config)
    report = case.diagnose(active_strategy(), "pct_change(close, 10)", horizon=5)
    assert report["split"] == "development"
    assert report["observations"] > 0
    assert report["last_allowed_outcome_date"] == "2020-08-31"
    assert "Gross event-level" in report["limitations"][0]
    assert set(case._loaded) == {"development"}
    with pytest.raises(ValueError):
        case.diagnose(active_strategy(), "close", 0)


def test_confirmation_is_lazy_and_does_not_unlock_final(market_config):
    case = AShareCase(market_config)
    result = case.evaluate(active_strategy(), "confirmation")
    assert result["loaded_through"] == "2020-10-30"
    assert case.confirmation_access_count == 1
    assert not result["confirmation_reusable_for_selection"]
    assert set(case._loaded) == {"confirmation"}
    with pytest.raises(PermissionError):
        case.evaluate(active_strategy(), "final")


def test_overlapping_splits_rejected(market_config):
    bad = copy.deepcopy(market_config)
    bad["splits"]["confirmation"]["start"] = "2020-08-01"
    with pytest.raises(ValueError, match="disjoint"):
        AShareCase(bad)


def test_future_members_and_st_stocks_do_not_influence_current_cross_section(market_config):
    case = AShareCase(market_config)
    loaded = case._load("development")
    strategy = active_strategy()
    strategy["filter_expression"] = "cs_rank(close) > 0.7"
    weights_before, _ = case._weights(strategy, loaded)
    # These values belong to stocks outside today's tradable universe. Rolling
    # price history remains present, but cross-sectional ranks must ignore them.
    loaded["fields"]["close"].loc[:"2020-04-30", "sh600005"] *= 1000
    loaded["fields"]["close"].loc[:, "sh600006"] *= 1000
    weights_after, _ = case._weights(strategy, loaded)
    pd.testing.assert_frame_equal(weights_before.loc[:"2020-04-30"], weights_after.loc[:"2020-04-30"])


def test_future_uniform_qfq_rescaling_does_not_change_research_features_or_weights(market_config):
    first = AShareCase(market_config)
    loaded_before = first._load("development")
    strategy = active_strategy()
    strategy["score_expression"] = "cs_rank(close)"
    weights_before, _ = first._weights(strategy, loaded_before)
    path = Path(market_config["data_root"]) / "sh600002.parquet"
    frame = pd.read_parquet(path)
    for column in ("open", "high", "low", "close", "prev_close", "qfq_ratio"):
        frame[column] *= 0.25
    frame.to_parquet(path, index=False)
    second = AShareCase(market_config)
    loaded_after = second._load("development")
    for column in ("open", "high", "low", "close"):
        pd.testing.assert_frame_equal(loaded_before["fields"][column], loaded_after["fields"][column])
    weights_after, _ = second._weights(strategy, loaded_after)
    pd.testing.assert_frame_equal(weights_before, weights_after)


def test_fixed_stock_cap_and_missing_slots_leave_cash(market_config):
    case = AShareCase(market_config)
    loaded = case._load("development")
    strategy = active_strategy()
    strategy["gross_exposure"] = 1.0
    weights, _ = case._weights(strategy, loaded)
    assert float(weights.max().max()) <= 0.10
    assert float(weights.sum(axis=1).max()) <= 0.50 + 1e-12
    strategy["top_n"] = 10
    strategy["gross_exposure"] = 0.8
    weights, _ = case._weights(strategy, loaded)
    assert float(weights.loc[:"2020-04-30"].max().max()) == pytest.approx(0.08)
    assert float(weights.loc[:"2020-04-30"].sum(axis=1).max()) == pytest.approx(0.40)


def test_diagnostic_annual_groups_and_paired_dates_can_be_recomputed(market_config, monkeypatch):
    case = AShareCase(market_config)
    dates = pd.bdate_range("2019-12-02", "2020-02-28")
    columns = case.codes
    day_direction = np.where(dates.year == 2019, 1.0, -1.0)
    rates = np.arange(len(columns), dtype=float) * .001 - .002
    opening = pd.DataFrame(np.cumprod(1 + day_direction[:, None] * rates[None, :], axis=0), index=dates, columns=columns)
    feature = pd.DataFrame(np.tile(np.arange(len(columns)), (len(dates), 1)), index=dates, columns=columns)
    eligible = pd.DataFrame(True, index=dates, columns=columns)
    eligible.loc[:, columns[5:]] = False
    loaded = {"fields": {"open": opening, "close": opening, "float_market_cap": feature},
        "eligible": eligible, "market_dates": dates, "loaded_through": str(dates[-1].date()), "datahash": "test"}
    monkeypatch.setattr(case, "_load", lambda split: loaded)
    result = case.diagnose(active_strategy(), "float_market_cap", 2)
    future = opening.shift(-3) / opening.shift(-1) - 1
    assert sum(row["observations"] for row in result["groups_by_year"]) == result["observations"]
    assert {row["year"] for row in result["groups_by_year"]} == {2019, 2020}
    for row in result["groups_by_year"]:
        values = future.loc[dates.year == row["year"], columns[row["group"] - 1]].dropna()
        assert row["observations"] == len(values)
        assert row["mean_gross_forward_return"] == pytest.approx(values.mean())
        assert row["equal_date_mean_gross_forward_return"] == pytest.approx(values.mean())
    spread = (future[columns[4]] - future[columns[0]]).dropna()
    assert result["paired_daily_spread"]["paired_signal_dates"] == len(spread)
    assert result["paired_daily_spread"]["mean_gross_forward_spread"] == pytest.approx(spread.mean())
    assert result["paired_daily_spread"]["positive_fraction"] == pytest.approx(spread.gt(0).mean())


def test_constant_diagnostic_has_no_invented_paired_comparison(market_config):
    result = AShareCase(market_config).diagnose(active_strategy(), "1", 5)
    assert len(result["groups"]) == 1
    assert result["paired_daily_spread"]["paired_signal_dates"] == 0
    assert result["paired_daily_spread"]["mean_gross_forward_spread"] is None
    json.dumps(result, allow_nan=False)


def test_tasks_have_distinct_initial_definitions_but_shared_market_exposure(market_config, monkeypatch):
    from quanta_agents.meta.ashare_tasks import TASKS, task_definition
    monkeypatch.setattr(ashare_case.pq, "read_table", lambda *args, **kwargs: pytest.fail("unexpected market read"))
    cases = [AShareCase({**market_config, "task": task}) for task in TASKS]
    assert len({case.manifest()["case_id"] for case in cases}) == len(TASKS)
    assert len({case.manifest()["evaluation_family_id"] for case in cases}) == 1
    assert len({case.manifest()["mechanism_family"] for case in cases}) == 3
    assert cases[0].initial_strategy() == baseline_strategy()
    for case in cases:
        validate_strategy(case.initial_strategy())
        assert case._loaded == {}
    changed = task_definition("volume_expansion")
    changed["baseline"]["top_n"] = 99
    assert task_definition("volume_expansion")["baseline"]["top_n"] == 10
    with pytest.raises(ValueError, match="unknown"):
        AShareCase({**market_config, "task": "best_answer"})


def test_research_metrics_do_not_satisfy_execution_gate(market_config):
    result = AShareCase(market_config).evaluate(active_strategy())
    assert result["execution_valid"] is False
    assert result["execution_invalid_reasons"]
    assert result["execution_debug"]["raw_share_inventory_cash_ledger_valid"] is False
