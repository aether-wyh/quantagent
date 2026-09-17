from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "research_stop_cluster_risk.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "research_stop_cluster_risk", MODULE_PATH
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = MODULE
MODULE_SPEC.loader.exec_module(MODULE)


def test_normalize_codes_accepts_plain_and_prefixed_codes() -> None:
    assert MODULE.normalize_codes("600000,sz000001,SH600000") == [
        "sh600000",
        "sz000001",
    ]
    with pytest.raises(ValueError, match="普通沪深股票"):
        MODULE.normalize_codes("sh510300")


def test_count_touch_episodes_merges_consecutive_quotes() -> None:
    prices = np.asarray([10.10, 10.01, 10.00, 10.01, 10.08, 10.00, 9.99, 10.07])
    assert MODULE.count_touch_episodes(prices, 10.00, 0.01) == 2


def test_visible_depth_to_level_uses_only_prices_above_support() -> None:
    values: dict[str, float] = {}
    for level in range(1, 11):
        values[f"bid_price_{level}"] = 10.01 - level * 0.01
        values[f"bid_volume_{level}"] = 100.0
    amount, inside = MODULE.visible_depth_to_level(pd.Series(values), 9.97)
    assert inside
    assert amount == pytest.approx((10.00 + 9.99 + 9.98 + 9.97) * 100.0)
    amount, inside = MODULE.visible_depth_to_level(pd.Series(values), 9.89)
    assert not inside
    assert np.isnan(amount)


def test_cache_key_changes_with_codes_and_settings(tmp_path: Path) -> None:
    settings = MODULE.ResearchSettings()
    first = MODULE.research_cache_key(
        root=tmp_path, codes=["sz000001"], settings=settings
    )
    second = MODULE.research_cache_key(
        root=tmp_path, codes=["sh600000"], settings=settings
    )
    third = MODULE.research_cache_key(
        root=tmp_path,
        codes=["sz000001"],
        settings=MODULE.ResearchSettings(lookback_minutes=30),
    )
    assert first != second
    assert first != third


def _synthetic_quotes() -> pd.DataFrame:
    times = pd.date_range("2026-06-15 09:30:00", "2026-06-15 10:02:00", freq="3s")
    phase = np.arange(len(times), dtype=float) * 2.0 * np.pi / 30.0
    last = np.round(10.00 + 0.05 * np.sin(phase), 2)
    quiet = (times >= pd.Timestamp("2026-06-15 09:54:00")) & (
        times <= pd.Timestamp("2026-06-15 09:55:00")
    )
    last[quiet] = 10.00
    last[times == pd.Timestamp("2026-06-15 09:55:03")] = 9.96
    last[times == pd.Timestamp("2026-06-15 09:55:06")] = 9.97
    rows: list[dict[str, object]] = []
    for row_number, (timestamp, price) in enumerate(zip(times, last), start=1):
        row: dict[str, object] = {
            "code": "sz000001",
            "event_ts": timestamp,
            "source_row_no": row_number,
            "last_price": float(price),
        }
        bid_one = float(price - 0.01)
        ask_one = float(price + 0.01)
        for level in range(1, 11):
            row[f"bid_price_{level}"] = bid_one - (level - 1) * 0.01
            row[f"bid_volume_{level}"] = 10_000
            row[f"ask_price_{level}"] = ask_one + (level - 1) * 0.01
            row[f"ask_volume_{level}"] = 10_000
        rows.append(row)
    return pd.DataFrame(rows)


def _synthetic_trades(quotes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    source_row_no = 1
    for timestamp in pd.date_range(
        "2026-06-15 09:34:00", "2026-06-15 09:54:50", freq="10s"
    ):
        quote_index = int(
            np.searchsorted(
                quotes["event_ts"].to_numpy(dtype="datetime64[ns]"),
                np.datetime64(timestamp),
                side="right",
            )
            - 1
        )
        price = float(quotes.iloc[quote_index]["last_price"])
        rows.append(
            {
                "code": "sz000001",
                "event_ts": timestamp,
                "source_row_no": source_row_no,
                "bs_flag": "B" if source_row_no % 2 else "S",
                "trade_price": price,
                "trade_quantity": 100,
                "trade_amount": price * 100,
                "bid_order_id": source_row_no,
                "ask_order_id": source_row_no + 100_000,
            }
        )
        source_row_no += 1

    event_time = pd.Timestamp("2026-06-15 09:55:00.500")
    for offset_ms, price, quantity in (
        (0, 9.94, 50_000),
        (100, 9.93, 40_000),
        (200, 9.92, 30_000),
    ):
        rows.append(
            {
                "code": "sz000001",
                "event_ts": event_time + pd.Timedelta(milliseconds=offset_ms),
                "source_row_no": source_row_no,
                "bs_flag": "S",
                "trade_price": price,
                "trade_quantity": quantity,
                "trade_amount": price * quantity,
                "bid_order_id": source_row_no,
                "ask_order_id": source_row_no + 100_000,
            }
        )
        source_row_no += 1
    rows.append(
        {
            "code": "sz000001",
            "event_ts": event_time + pd.Timedelta(seconds=5),
            "source_row_no": source_row_no,
            "bs_flag": "B",
            "trade_price": 9.97,
            "trade_quantity": 20_000,
            "trade_amount": 9.97 * 20_000,
            "bid_order_id": source_row_no,
            "ask_order_id": source_row_no + 100_000,
        }
    )
    return pd.DataFrame(rows).sort_values(["event_ts", "source_row_no"]).reset_index(drop=True)


def test_analyze_code_day_keeps_scores_before_outcome() -> None:
    quotes = _synthetic_quotes()
    trades = _synthetic_trades(quotes)
    settings = MODULE.ResearchSettings(min_history_quotes=200)

    events = MODULE.analyze_code_day(quotes, trades, settings)

    assert len(events) == 1
    event = events.iloc[0]
    assert event["code"] == "sz000001"
    assert event["breach_ts"] == pd.Timestamp("2026-06-15 09:55:00.500")
    assert event["support_price"] == pytest.approx(9.95)
    assert event["touch_episodes"] >= 2
    assert 0 <= event["stop_density_score"] <= 100
    assert 0 <= event["sweep_ease_score"] <= 100
    assert bool(event["cascade_10s"])
    assert event["continuation_ticks_10s"] >= 3
    assert bool(event["reclaimed_60s"])
    assert event["post_sell_amount_10s"] > event["baseline_sell_10s_p95"]


def test_trigger_trade_is_not_counted_as_following_sell_flow() -> None:
    quotes = _synthetic_quotes()
    trades = _synthetic_trades(quotes)
    event_time = pd.Timestamp("2026-06-15 09:55:00.500")
    keep = trades["event_ts"].lt(event_time + pd.Timedelta(milliseconds=1))
    trades = trades.loc[keep].copy()

    events = MODULE.analyze_code_day(
        quotes,
        trades,
        MODULE.ResearchSettings(min_history_quotes=200),
    )

    assert len(events) == 1
    event = events.iloc[0]
    assert event["post_sell_amount_10s"] == 0
    assert event["continuation_ticks_10s"] == 0
    assert not bool(event["cascade_10s"])


def test_chronological_evaluation_uses_earlier_score_cuts() -> None:
    rows = []
    for index, date in enumerate(pd.date_range("2026-01-01", periods=8, freq="D"), start=1):
        rows.append(
            {
                "candidate_id": str(index),
                "date": date,
                "code": "sz000001",
                "stop_density_score": float(index),
                "sweep_ease_score": float(index),
                "combined_risk_score": float(index),
                "baseline_sell_10s_median": 10.0,
                "baseline_sell_10s_p95": 20.0,
                "post_sell_amount_10s": 30.0 if index >= 7 else 5.0,
                "continuation_ticks_10s": 4.0 if index >= 7 else 1.0,
                "cascade_10s": index >= 7,
                "reclaimed_60s": False,
            }
        )

    result = MODULE.chronological_evaluation(pd.DataFrame(rows))

    assert result["available"]
    assert result["earlier_event_count"] == 6
    assert result["later_event_count"] == 2
    later = result["scores"]["stop_density_score"]["later_dates"]
    assert later["low"]["events"] == 0
    assert later["high"]["events"] == 2
    assert later["high"]["cascade_rate"] == 1.0


def test_chronological_evaluation_rejects_overlapping_score_groups() -> None:
    rows = []
    for index, date in enumerate(pd.date_range("2026-01-01", periods=8, freq="D")):
        rows.append(
            {
                "candidate_id": str(index),
                "date": date,
                "code": "sz000001",
                "stop_density_score": 50.0,
                "sweep_ease_score": 50.0,
                "combined_risk_score": 50.0,
                "baseline_sell_10s_median": 10.0,
                "baseline_sell_10s_p95": 20.0,
                "post_sell_amount_10s": 5.0,
                "continuation_ticks_10s": 3.0,
                "cascade_10s": False,
                "reclaimed_60s": False,
            }
        )

    result = MODULE.chronological_evaluation(pd.DataFrame(rows))

    density = result["scores"]["stop_density_score"]
    assert not density["available"]
    assert density["low_cut_from_earlier_dates"] == density["high_cut_from_earlier_dates"]


def test_chronological_evaluation_uses_requested_cascade_ticks() -> None:
    rows = []
    for index, date in enumerate(pd.date_range("2026-01-01", periods=8, freq="D"), start=1):
        rows.append(
            {
                "candidate_id": str(index),
                "date": date,
                "code": "sz000001",
                "stop_density_score": float(index),
                "sweep_ease_score": float(index),
                "combined_risk_score": float(index),
                "baseline_sell_10s_median": 10.0,
                "baseline_sell_10s_p95": 20.0,
                "post_sell_amount_10s": 5.0,
                "continuation_ticks_10s": 4.0,
                "cascade_10s": False,
                "reclaimed_60s": False,
            }
        )

    result = MODULE.chronological_evaluation(pd.DataFrame(rows), cascade_ticks=5)

    later_high = result["scores"]["stop_density_score"]["later_dates"]["high"]
    assert later_high["deep_break_rate"] == 0.0
    assert result["by_stock_later_dates"][0]["deep_break_rate"] == 0.0
