from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest

from quanta_agents.meta import benchmark


def _example_rows(last_open: float = 99.0, entry_close: float = 90.0):
    closes = [100.0, 95.0, 90.0, 80.0, 82.0, entry_close, last_open]
    opens = [100.0, 100.0, 95.0, 90.0, 80.0, 90.0, last_open]
    return tuple(
        benchmark._Bar(
            f"2000-01-{index + 3:02d}", opening,
            max(opening, close) + 1.0, min(opening, close) - 1.0, close, 1_000,
        )
        for index, (opening, close) in enumerate(zip(opens, closes))
    )


def _short_strategy():
    return {
        **benchmark.baseline_strategy(),
        "lookback": 3, "decline_threshold": 0.10,
        "confirmation_days": 1, "hold_days": 1, "stop_loss": 0.05,
    }


def test_signal_waits_for_next_open_and_accounts_for_cash_and_both_fees():
    rows = _example_rows()
    result = benchmark._simulate(rows, _short_strategy(), 0, len(rows))
    trade = result["diagnostics"]["trades"][0]
    assert trade["signal_date"] == rows[4].date
    assert trade["entry_date"] == rows[5].date
    assert trade["entry_price"] == 90.0
    assert trade["exit_date"] == rows[6].date
    assert trade["exit_price"] == 99.0
    assert trade["exit_reason"] == "holding_limit_next_open"
    expected = 99.0 / 90.0 * 0.999 / 1.001 - 1.0
    assert result["metrics"]["total_return"] == pytest.approx(expected)
    assert result["metrics"]["final_equity"] == pytest.approx(10_000 * (1 + expected))
    # Uninvested sessions are part of the portfolio path, not removed to inflate Sharpe.
    assert result["metrics"]["days"] == 7
    assert all(row["equity"] == 10_000.0 for row in result["daily"][:5])
    assert result["daily"][5]["equity"] == pytest.approx(10_000 / 1.001)
    assert result["metrics"]["fees_paid"] > 0


def test_close_stop_exits_at_actual_next_open_including_adverse_gap():
    rows = _example_rows(last_open=60.0, entry_close=70.0)
    result = benchmark._simulate(rows, _short_strategy(), 0, len(rows))
    trade = result["diagnostics"]["trades"][0]
    assert trade["exit_reason"] == "close_stop_next_open"
    assert trade["exit_price"] == 60.0
    assert trade["net_return"] == pytest.approx(60.0 / 90.0 * 0.999 / 1.001 - 1.0)


def test_future_bars_cannot_change_earlier_orders_or_equity():
    first = _example_rows()
    changed = _example_rows(last_open=30.0)
    before = benchmark._simulate(first, _short_strategy(), 0, len(first))
    after = benchmark._simulate(changed, _short_strategy(), 0, len(changed))
    assert before["daily"][:-1] == after["daily"][:-1]
    for key in ("entry_date", "entry_price", "signal_date", "capital_at_entry"):
        assert before["diagnostics"]["trades"][0][key] == after["diagnostics"]["trades"][0][key]


def test_predeclared_terminal_close_liquidation_pays_exit_fee():
    rows = _example_rows()[:-1]
    result = benchmark._simulate(rows, _short_strategy(), 0, len(rows))
    trade = result["diagnostics"]["trades"][0]
    assert trade["exit_reason"] == "terminal_close"
    assert trade["exit_price"] == rows[-1].close
    assert trade["net_return"] == pytest.approx(0.999 / 1.001 - 1.0)
    assert result["metrics"]["total_return"] == pytest.approx(trade["net_return"])


def test_split_starts_flat_and_may_use_preceding_close_for_signal():
    rows = _example_rows()
    result = benchmark._simulate(rows, _short_strategy(), 5, len(rows))
    assert result["metrics"]["days"] == 2
    assert result["diagnostics"]["trades"][0]["entry_date"] == rows[5].date
    assert result["diagnostics"]["trades"][0]["capital_at_entry"] == 10_000


@pytest.mark.parametrize("field,value", [
    ("lookback", True), ("lookback", 3.0), ("lookback", 2),
    ("confirmation_days", 5), ("hold_days", 0), ("volume_filter", -1),
    ("stop_loss", float("nan")), ("decline_threshold", float("inf")),
    ("volume_filter", "1.2"), ("hold_days", 10 ** 1000),
])
def test_dsl_rejects_bad_types_nonfinite_and_out_of_bounds(field, value):
    strategy = benchmark.baseline_strategy()
    strategy[field] = value
    with pytest.raises(ValueError):
        benchmark.evaluate(strategy)


def test_dsl_rejects_code_extra_keys_and_missing_fields():
    with pytest.raises(ValueError, match="allowlist"):
        benchmark.evaluate({**benchmark.baseline_strategy(), "code": "print('not executable')"})
    incomplete = benchmark.baseline_strategy()
    del incomplete["stop_loss"]
    with pytest.raises(ValueError, match="missing"):
        benchmark.evaluate(incomplete)
    with pytest.raises(ValueError, match="split"):
        benchmark.evaluate(benchmark.baseline_strategy(), "all")


def test_fixture_is_reproducible_finite_and_explicitly_not_alpha_evidence():
    first = benchmark.evaluate(benchmark.baseline_strategy())
    second = benchmark.evaluate(benchmark.baseline_strategy())
    assert first == second
    assert first["kind"] == "synthetic_fixture"
    assert first["score"] == first["metrics"]["sharpe"]
    assert len(first["data_hash"]) == 64
    assert len(first["scoring_hash"]) == 64
    assert len(first["subperiods"]) == 3
    json.dumps(first, allow_nan=False)
    assert math.isfinite(first["score"])
    assert "not evidence" in first["limitations"]
    assert benchmark.strategy_schema()["additionalProperties"] is False


def test_no_trades_is_honest_zero_return_and_not_eligible():
    rows = tuple(benchmark._Bar(f"2000-01-{i + 1:02d}", 100, 100, 100, 100, 1_000) for i in range(20))
    result = benchmark._simulate(rows, _short_strategy(), 0, len(rows))
    assert result["metrics"]["completed_trades"] == 0
    assert result["metrics"]["total_return"] == 0.0
    assert result["metrics"]["sharpe"] == 0.0
    assert result["diagnostics"]["evidence_status"] == "insufficient_trades_synthetic_only"


def test_development_packet_and_results_do_not_depend_on_hidden_bars(monkeypatch):
    original = benchmark._bars()
    packet = benchmark.development_packet()
    evaluation = benchmark.evaluate(benchmark.baseline_strategy())
    modified = original[:benchmark.DEVELOPMENT_DAYS] + tuple(
        replace(row, open=row.open * 2, high=row.high * 2, low=row.low * 2, close=row.close * 2)
        for row in original[benchmark.DEVELOPMENT_DAYS:]
    )
    monkeypatch.setattr(benchmark, "_bars", lambda: modified)
    assert packet == benchmark.development_packet()
    assert evaluation == benchmark.evaluate(benchmark.baseline_strategy())
    assert all(row["date"] <= original[benchmark.DEVELOPMENT_DAYS - 1].date for row in packet["recent_ohlcv"])


def test_periods_are_sequential_and_final_result_is_separately_labeled():
    manifest = benchmark.case_manifest()
    dev, final = manifest["splits"]["development"], manifest["splits"]["final"]
    assert dev["end"] < final["start"]
    result = benchmark.evaluate(benchmark.baseline_strategy(), split="final")
    assert result["split"] == "final"
    assert result["metrics"]["days"] == final["rows"]
    assert result["subperiods"][0]["start"] == final["start"]
    assert result["data_hash"] != benchmark.evaluate(benchmark.baseline_strategy())["data_hash"]
