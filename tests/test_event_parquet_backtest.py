from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("pyarrow")

MODULE_PATH = PROJECT_ROOT / "src" / "quanta_agents" / "event_parquet_backtest.py"
MODULE_SPEC = importlib.util.spec_from_file_location("event_parquet_backtest", MODULE_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)
normalize_stock_code = MODULE.normalize_stock_code
run_event_parquet_backtest = MODULE.run_event_parquet_backtest
load_events = MODULE._load_events
prepare_weight_signals = MODULE._prepare_weight_signals


def _write_events(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_normalize_stock_code_supports_common_exchange_formats() -> None:
    assert normalize_stock_code("sh600000") == "sh600000"
    assert normalize_stock_code("600000.SH") == "sh600000"
    assert normalize_stock_code("600000.SSE") == "sh600000"
    assert normalize_stock_code("sz000001") == "sz000001"
    assert normalize_stock_code("000001.SZSE") == "sz000001"
    assert normalize_stock_code("bj920000") == "bj920000"
    assert normalize_stock_code("920000.BSE") == "bj920000"


def test_event_backtest_matches_weights_applies_cooldown_and_costs(tmp_path: Path) -> None:
    event_path = tmp_path / "events.parquet"
    _write_events(
        event_path,
        [
            {
                "code": "600000.SH",
                "trigger_ts": "2026-01-05 09:40:00",
                "trigger_position": 10,
                "forward_5m": 0.10,
                "joint_minute_hit": True,
            },
            {
                "code": "sh600000",
                "trigger_ts": "2026-01-05 09:50:00",
                "trigger_position": 20,
                "forward_5m": 0.50,
                "joint_minute_hit": True,
            },
            {
                "code": "600000.SSE",
                "trigger_ts": "2026-01-05 10:00:00",
                "trigger_position": 30,
                "forward_5m": -0.04,
                "joint_minute_hit": False,
            },
            {
                "code": "000001.SZ",
                "trigger_ts": "2026-01-06 09:40:00",
                "trigger_position": 10,
                "forward_5m": 0.02,
                "joint_minute_hit": True,
            },
            {
                "code": "000001.SZ",
                "trigger_ts": "2026-01-07 09:40:00",
                "trigger_position": 10,
                "forward_5m": 0.80,
            },
        ],
    )
    weights = pd.DataFrame(
        {
            "signal_time": pd.to_datetime(
                [
                    "2026-01-05 09:40:00",
                    "2026-01-05 09:50:00",
                    "2026-01-05 10:00:00",
                    "2026-01-06 09:40:00",
                    "2026-01-07 09:40:00",
                ]
            ),
            "600000.SH": [0.5, 0.5, 0.5, 0.0, 0.0],
            "000001.SZSE": [0.0, 0.0, 0.0, -0.25, 1.0],
            "cash": [0.5, 0.5, 0.5, 0.75, 0.0],
        }
    )

    stats = run_event_parquet_backtest(
        weights,
        event_path=event_path,
        start="2026-01-05",
        end="2026-01-06",
        horizon_minutes=5,
        buy_cost=0.001,
        sell_cost=0.002,
        slippage=0.0005,
        cooldown_minutes=20,
        capital=100_000.0,
    )

    trades = stats["_trades_df"]
    daily = stats["_daily_df"].set_index("date")
    assert trades["code"].tolist() == ["sh600000", "sh600000", "sz000001"]
    assert trades["trigger_position"].tolist() == [10, 30, 10]
    assert trades["side"].tolist() == ["long", "long", "short"]
    assert trades["gross_return"].tolist() == pytest.approx([0.10, -0.04, -0.02])
    assert trades["net_return"].tolist() == pytest.approx([0.096, -0.044, -0.024])
    assert trades["weighted_net_return"].tolist() == pytest.approx([0.048, -0.022, -0.006])
    assert daily.loc[pd.Timestamp("2026-01-05"), "return"] == pytest.approx(0.026)
    assert daily.loc[pd.Timestamp("2026-01-06"), "return"] == pytest.approx(-0.006)
    assert daily.loc[pd.Timestamp("2026-01-05"), "trade_count"] == 2
    assert daily.loc[pd.Timestamp("2026-01-06"), "trade_count"] == 1
    assert stats["total_trade_count"] == 3
    assert stats["end_balance"] == pytest.approx(101_984.4)
    assert stats["total_return"] == pytest.approx(0.019844)
    assert stats["max_drawdown"] == pytest.approx(-615.6)
    assert stats["max_ddpercent"] == pytest.approx(-0.006)
    assert stats["win_rate"] == pytest.approx(1 / 3)
    assert stats["profit_loss_ratio"] == pytest.approx(0.096 / 0.034)
    assert stats["event_success_column"] == "joint_minute_hit"
    assert stats["event_success_count"] == 2
    assert stats["event_success_observation_count"] == 2
    assert stats["event_success_positive_count"] == 1
    assert stats["event_success_rate"] == pytest.approx(0.5)
    assert stats["event_success_ci_low"] < 0.5 < stats["event_success_ci_high"]
    assert stats["event_joint_minute_hit_rate"] == pytest.approx(0.5)
    assert stats["event_joint_minute_hit_count"] == 2
    assert stats["event_joint_minute_hit_positive_count"] == 1
    assert stats["event_gross_mean_return"] == pytest.approx(0.04 / 3)
    assert stats["event_gross_median_return"] == pytest.approx(-0.02)
    assert stats["event_gross_up_rate"] == pytest.approx(1 / 3)
    assert stats["event_net_mean_return"] == pytest.approx(0.028 / 3)
    assert stats["event_net_median_return"] == pytest.approx(-0.024)
    assert stats["event_net_win_rate"] == pytest.approx(1 / 3)
    assert stats["yearly_event_stats"][0]["event_count"] == 3
    assert sum(item["event_count"] for item in stats["monthly_event_stats"]) == 3
    assert stats["cost_scenarios"][0]["net_mean_return"] == pytest.approx(0.04 / 3)
    assert stats["cost_scenarios"][1]["net_mean_return"] == pytest.approx(0.028 / 3)
    assert stats["_backtest_debug"]["final_event_count"] == 3
    assert stats["_backtest_debug"]["cooldown_removed_count"] == 1
    assert stats["event_return_column"] == "forward_5m"
    assert stats["_backtest_debug"]["event_return_columns"] == ["forward_5m"]
    for key in ("annual_return", "sharpe_ratio", "capital"):
        assert isinstance(stats[key], float)


def test_event_backtest_normalizes_object_signal_times(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "events.parquet"
    _write_events(
        event_path,
        [
            {
                "code": "600000.SH",
                "trigger_ts": "2026-01-05 09:40:00",
                "trigger_position": 10,
                "forward_5m": 0.01,
            }
        ],
    )

    monkeypatch.setattr(
        MODULE,
        "_prepare_weight_signals",
        lambda *_args, **_kwargs: pd.DataFrame(
            {
                "trigger_ts": pd.Series(
                    ["2026-01-05 09:40:00"],
                    dtype="object",
                ),
                "code": ["sh600000"],
                "weight": [1.0],
            }
        ),
    )

    stats = run_event_parquet_backtest(
        pd.DataFrame({"placeholder": [1]}),
        event_path=event_path,
        start="2026-01-05",
        end="2026-01-05",
        cooldown_minutes=0,
    )

    assert stats["total_trade_count"] == 1


def test_event_backtest_accepts_all_cash_with_no_signals(tmp_path: Path) -> None:
    event_path = tmp_path / "events.parquet"
    _write_events(
        event_path,
        [
            {
                "code": "600000.SH",
                "trigger_ts": "2026-01-05 09:40:00",
                "trigger_position": 10,
                "forward_5m": 0.01,
            }
        ],
    )
    weights = pd.DataFrame(
        {
            "trigger_ts": pd.to_datetime(["2026-01-05 09:40:00"]),
            "sh600000": pd.arrays.SparseArray([0.0], fill_value=0.0),
            "cash": [1.0],
        }
    )

    stats = run_event_parquet_backtest(
        weights,
        event_path=event_path,
        start="2026-01-05",
        end="2026-01-05",
        cooldown_minutes=0,
    )

    assert stats["total_trade_count"] == 0
    assert stats["_backtest_debug"]["nonzero_signal_count"] == 0
    assert stats["_backtest_debug"]["final_event_count"] == 0


def test_event_backtest_accepts_datetime_index_and_return_alias(tmp_path: Path) -> None:
    event_path = tmp_path / "events.parquet"
    _write_events(
        event_path,
        [
            {
                "code": "000001.SZSE",
                "trigger_ts": "2026-02-02 10:15:00",
                "trigger_position": 45,
                "return_10m": 0.03,
            }
        ],
    )
    weights = pd.DataFrame(
        {"000001.SZ": [1.0]},
        index=pd.DatetimeIndex(["2026-02-02 10:15:00"], name="trigger_ts"),
    )

    stats = run_event_parquet_backtest(
        weights,
        event_path=event_path,
        start="2026-02-02",
        end="2026-02-02",
        horizon_minutes=10,
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.0,
    )

    assert stats["total_trade_count"] == 1
    assert stats["total_return"] == pytest.approx(0.03)
    assert stats["_trades_df"].iloc[0]["code"] == "sz000001"
    assert stats["_trades_df"].iloc[0]["return_column"] == "return_10m"


def test_sparse_weight_table_reads_only_stored_nonzero_values() -> None:
    weights = pd.DataFrame(
        {
            "trigger_ts": pd.to_datetime(
                ["2026-02-02 10:15:00", "2026-02-02 10:16:00"]
            ),
            "600000.SH": pd.arrays.SparseArray([0.5, 0.0], fill_value=0.0),
            "000001.SZ": pd.arrays.SparseArray([0.0, 1.0], fill_value=0.0),
            "cash": [0.5, 0.0],
        }
    )

    signals = prepare_weight_signals(weights, None)

    assert signals[["code", "weight"]].to_dict("records") == [
        {"code": "sh600000", "weight": 0.5},
        {"code": "sz000001", "weight": 1.0},
    ]


def test_event_backtest_rejects_missing_required_event_column(tmp_path: Path) -> None:
    event_path = tmp_path / "events.parquet"
    _write_events(
        event_path,
        [
            {
                "code": "600000.SH",
                "trigger_ts": "2026-01-05 09:40:00",
                "forward_20m": 0.01,
            }
        ],
    )
    weights = pd.DataFrame(
        {"600000.SH": [1.0]},
        index=pd.DatetimeIndex(["2026-01-05 09:40:00"]),
    )

    with pytest.raises(ValueError, match="trigger_position"):
        run_event_parquet_backtest(
            weights,
            event_path=event_path,
            start="2026-01-05",
            end="2026-01-05",
            horizon_minutes=20,
        )


def test_event_reader_filters_locked_period_before_loading_results(tmp_path: Path) -> None:
    event_path = tmp_path / "events.parquet"
    _write_events(
        event_path,
        [
            {
                "code": "600000.SH",
                "trigger_ts": "2024-12-31 14:00:00",
                "trigger_position": 180,
                "forward_5m": 0.01,
            },
            {
                "code": "600000.SH",
                "trigger_ts": "2025-01-02 10:00:00",
                "trigger_position": 29,
                "forward_5m": 0.99,
            },
        ],
    )

    events = load_events(
        [str(event_path)],
        5,
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-12-31"),
    )

    assert events["trigger_ts"].dt.strftime("%Y-%m-%d").tolist() == ["2024-12-31"]
