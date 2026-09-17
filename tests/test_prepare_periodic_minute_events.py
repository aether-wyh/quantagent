from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("pyarrow")

MODULE_PATH = PROJECT_ROOT / "scripts" / "prepare_periodic_minute_events.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "prepare_periodic_minute_events", MODULE_PATH
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)
prepare_events = MODULE.prepare_events


def _legacy_valid_windows(
    spikes: list[int], upper: int
) -> list[tuple[tuple[int, ...], tuple[int, ...], int, int]]:
    results: list[tuple[tuple[int, ...], tuple[int, ...], int, int]] = []
    values = pd.Series(spikes, dtype="int64").to_numpy()
    for spike_index in range(4, len(values)):
        past = values[spike_index - 4 : spike_index + 1]
        gaps = pd.Series(past).diff().dropna().to_numpy(dtype=int)
        median_gap = float(pd.Series(gaps).median())
        if not 2 <= median_gap <= 10:
            continue
        if max(Counter(int(value) for value in gaps).values()) < 3:
            continue
        period = int(round(median_gap))
        current = int(past[-1])
        predicted = current + period
        trigger = predicted - 2
        if trigger < current or predicted + 1 >= upper or trigger + 1 >= upper:
            continue
        next_spike = int(values[spike_index + 1]) if spike_index + 1 < len(values) else -1
        results.append(
            (
                tuple(int(value) for value in past),
                tuple(int(value) for value in gaps),
                period,
                next_spike,
            )
        )
    return results


def test_vectorized_five_pulse_windows_match_previous_rule() -> None:
    vectorized = MODULE._valid_five_pulse_windows
    samples = [
        [],
        [10, 12, 14, 16, 18],
        [10, 20, 30, 40, 50],
        [10, 12, 14, 16, 21, 23],
        [100, 102, 104, 106, 108, 110, 118],
        [220, 222, 224, 226, 228, 230, 238],
    ]
    random = np.random.default_rng(20260805)
    for offset in (0, 120):
        for _ in range(200):
            count = int(random.integers(0, 35))
            positions = random.choice(120, size=count, replace=False) + offset
            samples.append(sorted(positions.tolist()))

    for spikes in samples:
        offset = 120 if spikes and min(spikes) >= 120 else 0
        upper = 240 if offset else 120
        windows, gaps, periods, next_spikes = vectorized(
            np.asarray(spikes, dtype="int16"), upper
        )
        actual = [
            (
                tuple(int(value) for value in window),
                tuple(int(value) for value in gap),
                int(period),
                int(next_spike),
            )
            for window, gap, period, next_spike in zip(
                windows, gaps, periods, next_spikes
            )
        ]
        assert actual == _legacy_valid_windows(spikes, upper)


def _minute_timestamp(date: pd.Timestamp, position: int) -> pd.Timestamp:
    if position < 120:
        return date.normalize() + pd.Timedelta(hours=9, minutes=31 + position)
    return date.normalize() + pd.Timedelta(hours=13, minutes=position - 119)


def _write_stock(
    path: Path,
    *,
    pulse_positions: tuple[int, ...],
    future_closes: dict[int, float] | None = None,
    event_lows: dict[int, float] | None = None,
    invalid_close_dates: set[pd.Timestamp] | None = None,
    periods: int = 21,
    missing_dates: set[pd.Timestamp] | None = None,
) -> pd.Timestamp:
    dates = pd.bdate_range("2024-01-02", periods=periods)
    event_date = dates[-1]
    rows: list[dict[str, object]] = []
    future_closes = future_closes or {}
    event_lows = event_lows or {}
    missing_dates = {date.normalize() for date in (missing_dates or set())}
    invalid_close_dates = {
        date.normalize() for date in (invalid_close_dates or set())
    }

    for day_number, date in enumerate(dates):
        if date.normalize() in missing_dates:
            continue
        history_amount = 100.0 if day_number % 2 == 0 else 200.0
        for position in range(240):
            close = 10.0
            amount = history_amount
            if date == event_date:
                amount = 150.0
                if position in pulse_positions:
                    amount = 1_000.0 + position
                    close = 10.1
                close = future_closes.get(position, close)
            if date.normalize() in invalid_close_dates and position == 239:
                close = float("nan")
            low = min(10.0, close) if np.isfinite(close) else 10.0
            if date == event_date:
                low = event_lows.get(position, low)
            rows.append(
                {
                    "datetime": _minute_timestamp(date, position),
                    "open": 10.0,
                    "high": max(10.0, close) if np.isfinite(close) else 10.0,
                    "low": low,
                    "close": close,
                    "volume": 1_000,
                    "amount": amount,
                }
            )

    pd.DataFrame(rows).to_parquet(path, index=False)
    return event_date


def test_prepare_events_detects_five_regular_pulses_and_future_hit(
    tmp_path: Path,
) -> None:
    minute_dir = tmp_path / "minute"
    minute_dir.mkdir()
    event_date = _write_stock(
        minute_dir / "sh600000.parquet",
        pulse_positions=(10, 12, 14, 16, 21, 23),
        future_closes={26: 10.05, 31: 10.10, 41: 10.20},
    )
    output = tmp_path / "events.parquet"

    summary = prepare_events(
        minute_dir=minute_dir,
        output=output,
        start=None,
        end=str(event_date.date()),
        event_start=str(event_date.date()),
        event_end=str(event_date.date()),
        workers=1,
        min_minute_amount=500.0,
        spike_z=5.0,
    )

    events = pd.read_parquet(output)
    primary = events.loc[
        events["candidate_id"].eq(f"{event_date:%Y%m%d}_sh600000_021")
    ].iloc[0]
    assert summary["files_processed"] == 1
    assert summary["events_written"] == len(events)
    assert summary["effective_start"] == "2024-01-02"
    assert primary["code"] == "sh600000"
    assert primary["trigger_position"] == 21
    assert primary["period"] == 2
    assert primary["gap_min"] == 2
    assert primary["gap_max"] == 5
    assert primary["past_up_count"] == 5
    assert bool(primary["no_early_spike"])
    assert bool(primary["pre_window_up"])
    assert bool(primary["volume_hit"])
    assert bool(primary["next_up"])
    assert bool(primary["joint_minute_hit"])
    assert primary["target_minute_return"] == pytest.approx(0.01)
    assert primary["forward_5m"] == pytest.approx(0.005)
    assert primary["forward_10m"] == pytest.approx(0.01)
    assert primary["forward_20m"] == pytest.approx(0.02)
    assert primary["pulse_return_sum"] == pytest.approx(0.05)
    assert primary["rise_concentration"] == pytest.approx(1.0)
    assert primary["pulse_close_position_mean"] == pytest.approx(1.0)
    assert primary["pulse1_ts"] == _minute_timestamp(event_date, 10)
    assert primary["pulse5_ts"] == _minute_timestamp(event_date, 21)
    assert primary["predicted_ts"] == _minute_timestamp(event_date, 23)
    assert primary["trigger_low_to_prev5_close_ma5_distance"] == pytest.approx(0.0)
    assert primary["trigger_low_to_live_close_ma5_distance"] == pytest.approx(
        10.0 / 10.02 - 1.0
    )
    assert primary[
        "analysis_only_full_day_low_to_close_ma5_distance"
    ] == pytest.approx(0.0)
    assert not list(tmp_path.glob(".events.parts-*"))


def _prepare_distance_case(
    root: Path,
    *,
    event_lows: dict[int, float] | None = None,
    future_closes: dict[int, float] | None = None,
    invalid_close_dates: set[pd.Timestamp] | None = None,
) -> pd.Series:
    minute_dir = root / "minute"
    minute_dir.mkdir(parents=True)
    event_date = _write_stock(
        minute_dir / "sh600000.parquet",
        pulse_positions=(10, 12, 14, 16, 18),
        event_lows=event_lows,
        future_closes=future_closes,
        invalid_close_dates=invalid_close_dates,
    )
    output = root / "events.parquet"
    prepare_events(
        minute_dir=minute_dir,
        output=output,
        start=None,
        end=str(event_date.date()),
        event_start=str(event_date.date()),
        event_end=str(event_date.date()),
        workers=1,
        min_minute_amount=500.0,
        spike_z=5.0,
    )
    events = pd.read_parquet(output)
    return events.loc[
        events["candidate_id"].eq(f"{event_date:%Y%m%d}_sh600000_018")
    ].iloc[0]


def test_price_distance_fields_do_not_use_prices_after_trigger(
    tmp_path: Path,
) -> None:
    baseline = _prepare_distance_case(tmp_path / "baseline")
    later_low = _prepare_distance_case(
        tmp_path / "later_low",
        event_lows={100: 8.0},
    )
    changed_day_close = _prepare_distance_case(
        tmp_path / "changed_day_close",
        future_closes={239: 11.0},
    )

    safe_fields = (
        "trigger_low_to_prev5_close_ma5_distance",
        "trigger_low_to_live_close_ma5_distance",
    )
    for field in safe_fields:
        assert later_low[field] == pytest.approx(baseline[field])
        assert changed_day_close[field] == pytest.approx(baseline[field])

    analysis_field = "analysis_only_full_day_low_to_close_ma5_distance"
    assert baseline[analysis_field] == pytest.approx(0.0)
    assert later_low[analysis_field] == pytest.approx(-0.2)
    assert changed_day_close[analysis_field] == pytest.approx(10.0 / 10.2 - 1.0)


def test_price_distance_fields_require_their_complete_day_closes(
    tmp_path: Path,
) -> None:
    dates = pd.bdate_range("2024-01-02", periods=21)
    missing_fifth_close = _prepare_distance_case(
        tmp_path / "missing_fifth_close",
        invalid_close_dates={dates[-6]},
    )
    missing_most_recent_close = _prepare_distance_case(
        tmp_path / "missing_most_recent_close",
        invalid_close_dates={dates[-2]},
    )

    assert pd.isna(
        missing_fifth_close["trigger_low_to_prev5_close_ma5_distance"]
    )
    assert np.isfinite(
        missing_fifth_close["trigger_low_to_live_close_ma5_distance"]
    )
    assert np.isfinite(
        missing_fifth_close[
            "analysis_only_full_day_low_to_close_ma5_distance"
        ]
    )

    assert pd.isna(
        missing_most_recent_close["trigger_low_to_prev5_close_ma5_distance"]
    )
    assert pd.isna(
        missing_most_recent_close["trigger_low_to_live_close_ma5_distance"]
    )
    assert pd.isna(
        missing_most_recent_close[
            "analysis_only_full_day_low_to_close_ma5_distance"
        ]
    )


def test_prepare_events_rejects_pattern_without_three_equal_gaps(
    tmp_path: Path,
) -> None:
    minute_dir = tmp_path / "minute"
    minute_dir.mkdir()
    event_date = _write_stock(
        minute_dir / "sz000001.parquet",
        pulse_positions=(10, 12, 14, 17, 20),
    )
    output = tmp_path / "events.parquet"

    prepare_events(
        minute_dir=minute_dir,
        output=output,
        start="2024-01-02",
        end=str(event_date.date()),
        event_start=str(event_date.date()),
        event_end=str(event_date.date()),
        workers=1,
        min_minute_amount=500.0,
        spike_z=5.0,
    )

    events = pd.read_parquet(output)
    assert events.empty
    assert "candidate_id" in events.columns
    assert "forward_20m" in events.columns
    assert "trigger_low_to_prev5_close_ma5_distance" in events.columns
    assert "trigger_low_to_live_close_ma5_distance" in events.columns
    assert "analysis_only_full_day_low_to_close_ma5_distance" in events.columns
    assert not list(tmp_path.glob(".events.parts-*"))


def test_prepare_events_advances_history_on_market_date_missing_for_stock(
    tmp_path: Path,
) -> None:
    minute_dir = tmp_path / "minute"
    minute_dir.mkdir()
    dates = pd.bdate_range("2024-01-02", periods=22)
    _write_stock(
        minute_dir / "sh600000.parquet",
        pulse_positions=(),
        periods=22,
    )
    missing_date = dates[10]
    event_date = _write_stock(
        minute_dir / "sz000001.parquet",
        pulse_positions=(10, 12, 14, 16, 18),
        periods=22,
        missing_dates={missing_date},
    )
    calendar_file = tmp_path / "calendar.txt"
    calendar_file.write_text(
        "\n".join(date.date().isoformat() for date in dates), encoding="utf-8"
    )
    output = tmp_path / "events.parquet"

    prepare_events(
        minute_dir=minute_dir,
        output=output,
        start=str(dates[0].date()),
        end=str(event_date.date()),
        event_start=str(event_date.date()),
        event_end=str(event_date.date()),
        calendar_file=calendar_file,
        codes="sz000001",
        workers=1,
        min_minute_amount=500.0,
        spike_z=5.0,
    )

    assert pd.read_parquet(output).empty


def test_prepare_events_rejects_start_without_warmup(tmp_path: Path) -> None:
    minute_dir = tmp_path / "minute"
    minute_dir.mkdir()

    with pytest.raises(ValueError, match="start 必须早于 event_start"):
        prepare_events(
            minute_dir=minute_dir,
            output=tmp_path / "events.parquet",
            start="2024-02-01",
            event_start="2024-02-01",
            workers=1,
        )
