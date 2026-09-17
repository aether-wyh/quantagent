from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "backtest_stop_cluster_accumulation.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "backtest_stop_cluster_accumulation", MODULE_PATH
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = MODULE
MODULE_SPEC.loader.exec_module(MODULE)


def quote_row(
    timestamp: str | pd.Timestamp,
    *,
    bid: float,
    ask: float,
    last: float | None = None,
    prev_close: float = 10.0,
    volume: int = 1_000_000,
    source_row_no: int = 1,
) -> dict[str, object]:
    row: dict[str, object] = {
        "code": "sz000001",
        "event_ts": pd.Timestamp(timestamp),
        "source_row_no": source_row_no,
        "last_price": float(last if last is not None else (bid + ask) / 2.0),
        "prev_close": prev_close,
    }
    for side, price in (("bid", bid), ("ask", ask)):
        for level in range(1, 11):
            row[f"{side}_price_{level}"] = price if level == 1 else 0.0
            row[f"{side}_volume_{level}"] = volume if level == 1 else 0
    return row


def candidate_rows(dates: list[pd.Timestamp]) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = []
    outcomes = []
    for index, date in enumerate(dates, start=1):
        breach = date + pd.Timedelta(hours=10)
        candidate_id = f"event_{index}"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "date": date,
                "code": "sz000001",
                "breach_ts": breach,
                "support_price": 10.0,
                "range_high": 10.5,
                "range_width": 0.5,
                "near_support_net_buy_ratio": 1.5,
                "stop_density_score": float(index),
            }
        )
        outcomes.append(
            {
                "candidate_id": candidate_id,
                "reclaim_ts": breach + pd.Timedelta(seconds=3)
                if index == 21
                else pd.NaT,
            }
        )
    return pd.DataFrame(candidates), pd.DataFrame(outcomes)


def test_executable_book_vwap_respects_visible_participation() -> None:
    row = quote_row("2026-01-02 10:00:00", bid=9.99, ask=10.0, volume=1_000)
    row["ask_price_2"] = 10.01
    row["ask_volume_2"] = 1_000

    price = MODULE.executable_book_vwap(
        row, side="ask", shares=150, participation=0.10
    )

    assert price == pytest.approx((100 * 10.0 + 50 * 10.01) / 150)
    assert (
        MODULE.executable_book_vwap(
            row, side="ask", shares=250, participation=0.10
        )
        is None
    )


def test_prepare_signals_uses_only_previous_trading_days() -> None:
    dates = list(pd.date_range("2026-01-01", periods=24, freq="D"))
    candidates, outcomes = candidate_rows(dates)
    settings = MODULE.BacktestSettings(score_lookback_days=20, min_score_events=20)

    signals = MODULE.prepare_signals(
        candidates, outcomes, [str(value.date()) for value in dates], settings
    )

    selected = signals.loc[signals["signal"]]
    assert selected["candidate_id"].tolist() == ["event_21"]
    assert selected.iloc[0]["score_cut"] == pytest.approx(16.2)


def test_entry_and_exit_wait_for_the_next_quote_and_obey_t_plus_one() -> None:
    settings = MODULE.BacktestSettings()
    reclaim = pd.Timestamp("2026-01-21 10:00:03")
    same_day = pd.DataFrame(
        [
            quote_row(reclaim, bid=9.99, ask=10.00, source_row_no=1),
            quote_row(reclaim + pd.Timedelta(seconds=3), bid=9.99, ask=10.00, source_row_no=2),
        ]
    )
    entry = MODULE.find_entry_quote(same_day, reclaim, settings)
    assert entry is not None
    assert entry["event_ts"] == reclaim + pd.Timedelta(seconds=3)

    position = {
        "entry_date_position": 20,
        "shares": 100,
        "target_price": 10.50,
        "stop_price": 9.50,
    }
    assert (
        MODULE.find_exit_for_day(
            position, same_day, date_position=20, settings=settings
        )
        is None
    )
    next_day = pd.DataFrame(
        [
            quote_row("2026-01-22 09:30:00", bid=10.50, ask=10.51, source_row_no=1),
            quote_row("2026-01-22 09:30:03", bid=10.49, ask=10.50, source_row_no=2),
        ]
    )
    exit_event = MODULE.find_exit_for_day(
        position, next_day, date_position=21, settings=settings
    )
    assert exit_event is not None
    assert exit_event["exit_ts"] == pd.Timestamp("2026-01-22 09:30:03")
    assert exit_event["exit_reason"] == "区间高位"
    assert exit_event["exit_price"] == pytest.approx(10.48)


def test_stop_trigger_stays_active_until_a_bid_can_fill_it() -> None:
    settings = MODULE.BacktestSettings()
    position = {
        "entry_date_position": 0,
        "shares": 100,
        "target_price": 10.50,
        "stop_price": 9.50,
    }
    first_day = pd.DataFrame(
        [
            quote_row(
                "2026-01-02 09:30:00",
                bid=0.0,
                ask=9.41,
                last=9.40,
                source_row_no=1,
            )
        ]
    )

    assert (
        MODULE.find_exit_for_day(
            position, first_day, date_position=1, settings=settings
        )
        is None
    )
    assert position["pending_exit_reason"] == "止损"

    later_day = pd.DataFrame(
        [quote_row("2026-01-03 09:30:00", bid=9.30, ask=9.31, source_row_no=1)]
    )
    exit_event = MODULE.find_exit_for_day(
        position, later_day, date_position=2, settings=settings
    )

    assert exit_event is not None
    assert exit_event["exit_reason"] == "止损"
    assert exit_event["exit_price"] == pytest.approx(9.29)


def test_terminal_liquidation_is_zero_without_an_executable_bid() -> None:
    settings = MODULE.BacktestSettings()
    position = {
        "shares": 100,
        "pending_exit_ts": pd.Timestamp("2026-01-03 14:50:00"),
    }
    quotes = pd.DataFrame(
        [
            quote_row(
                "2026-01-03 14:50:03",
                bid=0.0,
                ask=9.01,
                last=9.00,
                source_row_no=1,
            )
        ]
    )

    value = MODULE.terminal_liquidation(position, quotes, settings)

    assert value["liquidation_net_value"] == 0.0
    assert pd.isna(value["liquidation_price"])


def test_run_backtest_completes_one_realistic_trade() -> None:
    dates = list(pd.date_range("2026-01-01", periods=24, freq="D"))
    date_strings = [str(value.date()) for value in dates]
    candidates, outcomes = candidate_rows(dates)
    outcomes.loc[outcomes["candidate_id"].eq("event_24"), "reclaim_ts"] = (
        dates[23] + pd.Timedelta(hours=10, seconds=3)
    )
    settings = MODULE.BacktestSettings(score_lookback_days=20, min_score_events=20)
    quote_days: dict[str, pd.DataFrame] = {}
    for date in dates:
        date_key = str(date.date())
        rows = [
            quote_row(date + pd.Timedelta(hours=10), bid=9.99, ask=10.00, source_row_no=1),
            quote_row(date + pd.Timedelta(hours=14, minutes=55), bid=9.99, ask=10.00, source_row_no=2),
        ]
        quote_days[date_key] = pd.DataFrame(rows)
    event_date = dates[20]
    quote_days[str(event_date.date())] = pd.DataFrame(
        [
            quote_row(event_date + pd.Timedelta(hours=10, seconds=3), bid=10.00, ask=10.01, source_row_no=1),
            quote_row(event_date + pd.Timedelta(hours=10, seconds=6), bid=10.00, ask=10.01, source_row_no=2),
            quote_row(event_date + pd.Timedelta(hours=10, seconds=9), bid=10.00, ask=10.01, source_row_no=3),
            quote_row(event_date + pd.Timedelta(hours=14, minutes=55), bid=9.99, ask=10.00, source_row_no=4),
        ]
    )
    next_date = dates[21]
    quote_days[str(next_date.date())] = pd.DataFrame(
        [
            quote_row(next_date + pd.Timedelta(hours=9, minutes=30), bid=10.50, ask=10.51, source_row_no=1),
            quote_row(next_date + pd.Timedelta(hours=9, minutes=30, seconds=3), bid=10.49, ask=10.50, source_row_no=2),
            quote_row(next_date + pd.Timedelta(hours=14, minutes=55), bid=10.49, ask=10.50, source_row_no=3),
        ]
    )

    summary, trades, daily, signals, open_positions = MODULE.run_backtest(
        candidates,
        outcomes,
        date_strings,
        lambda date: quote_days[date].copy(),
        settings,
    )

    assert summary["trade_count"] == 1
    assert summary["all_rule_signal_count"] == 2
    assert summary["signal_count"] == 1
    assert summary["open_position_count"] == 0
    assert open_positions.empty
    assert len(signals.loc[signals["signal"]]) == 2
    assert not bool(
        signals.loc[signals["candidate_id"].eq("event_24"), "selected_for_backtest"].iloc[0]
    )
    assert trades.iloc[0]["entry_ts"] == event_date + pd.Timedelta(hours=10, seconds=9)
    assert trades.iloc[0]["exit_ts"] == next_date + pd.Timedelta(hours=9, minutes=30, seconds=3)
    assert trades.iloc[0]["holding_days"] == 1
    assert trades.iloc[0]["net_pnl"] > 0
    assert daily.iloc[-1]["equity"] > settings.initial_cash
