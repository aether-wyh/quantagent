from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from quanta_agents.agents.strategy_tester import StrategyTester
from quanta_agents.event_parquet_backtest import run_event_parquet_backtest
from quanta_agents.state import BacktestResult, init_state


def test_strategy_tester_accepts_event_parquet_backend() -> None:
    with patch.dict(
        "os.environ",
        {"QUANTA_BACKTEST_DB_BACKEND": "event_parquet"},
        clear=False,
    ):
        assert StrategyTester._resolve_backtest_db_backend() == "event_parquet"


@pytest.mark.parametrize(
    ("strategy_params", "yaml_horizon", "expected_horizon", "expected_column"),
    [
        ({"event_horizon_minutes": 10}, 5, 10, "forward_10m"),
        ({"event_horizon_minutes": 20}, 5, 20, "forward_20m"),
        ({}, 5, 5, "forward_5m"),
    ],
)
def test_candidate_event_horizon_selects_matching_forward_column(
    tmp_path,
    strategy_params,
    yaml_horizon,
    expected_horizon,
    expected_column,
) -> None:
    event_path = tmp_path / "events.parquet"
    pd.DataFrame(
        [
            {
                "code": "sh600000",
                "trigger_ts": "2024-01-02 10:00:00",
                "trigger_position": 30,
                "forward_5m": 0.05,
                "forward_10m": 0.10,
                "forward_20m": 0.20,
            }
        ]
    ).to_parquet(event_path, index=False)
    weights = pd.DataFrame(
        {
            "trigger_ts": pd.to_datetime(["2024-01-02 10:00:00"]),
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )
    horizon, source = StrategyTester._resolve_event_horizon_minutes(
        {"event_horizon_minutes": yaml_horizon},
        {"params": strategy_params},
    )

    stats = run_event_parquet_backtest(
        weights,
        event_path=event_path,
        start="2024-01-02",
        end="2024-01-02",
        horizon_minutes=horizon,
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.0,
        cooldown_minutes=0,
    )

    assert horizon == expected_horizon
    assert source == (
        "strategy_result.params"
        if strategy_params
        else "experiment_spec.event_horizon_minutes"
    )
    assert stats["_trades_df"].iloc[0]["return_column"] == expected_column
    assert stats["_backtest_debug"]["holding_minutes"] == expected_horizon


@pytest.mark.parametrize("invalid_horizon", [0, 15, 5.5, True, "10"])
def test_candidate_event_horizon_rejects_unsupported_values(invalid_horizon) -> None:
    with pytest.raises(RuntimeError, match="5、10 或 20"):
        StrategyTester._resolve_event_horizon_minutes(
            {"event_horizon_minutes": 5},
            {"params": {"event_horizon_minutes": invalid_horizon}},
        )


def test_event_research_uses_validation_then_locked_backtest_window() -> None:
    spec = {
        "backtest_mode": "event_parquet",
        "validate_start": "2024-01-01",
        "validate_end": "2024-12-31",
        "backtest_start": "2025-01-01",
        "backtest_end": "2025-12-31",
    }

    development = StrategyTester._resolve_backtest_window(spec, "development")
    final_test = StrategyTester._resolve_backtest_window(spec, "final_test")

    assert [value.date().isoformat() for value in development] == [
        "2024-01-01",
        "2024-12-31",
    ]
    assert [value.date().isoformat() for value in final_test] == [
        "2025-01-01",
        "2025-12-31",
    ]


def test_event_development_report_contains_only_development_evidence() -> None:
    stats = {
        "annual_return": -1.0,
        "sharpe_ratio": -10.0,
        "max_drawdown": -1000000.0,
        "max_ddpercent": -1.0,
        "total_trade_count": 120,
        "event_gross_mean_return": 0.0002,
        "event_gross_up_rate": 0.41,
        "event_net_mean_return": -0.0014,
        "event_net_median_return": -0.0016,
        "event_net_win_rate": 0.30,
        "event_success_column": "joint_minute_hit",
        "event_success_observation_count": 120,
        "event_success_positive_count": 30,
        "event_success_rate": 0.25,
        "event_joint_minute_hit_rate": 0.25,
        "event_joint_minute_hit_count": 120,
        "event_joint_minute_hit_positive_count": 30,
        "yearly_event_stats": [{"period": "2024", "event_count": 120}],
        "monthly_event_stats": [{"period": "2024-01", "event_count": 120}],
        "cost_scenarios": [
            {"cost_multiplier": 0, "net_mean_return": 0.0002},
            {"cost_multiplier": 1, "net_mean_return": -0.0014},
        ],
        "event_horizon_source": "strategy_result.params",
        "_backtest_debug": {
            "raw_event_count": 200,
            "invalid_return_event_count": 10,
            "nonzero_signal_count": 180,
            "matched_before_cooldown_count": 170,
            "cooldown_removed_count": 50,
            "final_event_count": 120,
            "holding_minutes": 5,
            "event_return_columns": ["forward_5m"],
        },
    }
    result = BacktestResult(
        annual_return=-1.0,
        sharpe=-10.0,
        max_drawdown=-1000000.0,
        max_ddpercent=1.0,
        trade_count=120,
        win_rate=0.30,
        profit_loss_ratio=1.0,
        event_net_mean_return=-0.0014,
        event_gross_up_rate=0.41,
        event_joint_minute_hit_rate=0.25,
        event_success_rate=0.25,
        event_success_column="joint_minute_hit",
        event_success_metric="gross_up_rate",
        event_success_metric_value=0.41,
        passed=False,
        summary="development failed; FINAL_PERIOD_RESULT must not appear",
    )

    report = StrategyTester._build_event_development_report(
        stats=stats,
        backtest_result=result,
        experiment_spec={
            "train_start": "2022-01-01",
            "train_end": "2023-12-31",
            "backtest_start": "2099-01-01",
            "backtest_end": "2099-12-31",
            "evaluation": {"min_trade_count": 100},
        },
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 31),
    )

    assert report["period_kind"] == "development"
    assert report["event_horizon_minutes"] == 5
    assert report["event_horizon_source"] == "strategy_result.params"
    assert report["event_return_columns"] == ["forward_5m"]
    assert report["event_success_metric"] == "gross_up_rate"
    assert report["event_success_metric_value"] == 0.41
    assert report["folds"][0]["event_horizon_minutes"] == 5
    assert report["folds"][0]["event_return_columns"] == ["forward_5m"]
    assert report["folds"][0]["event_joint_minute_hit_rate"] == 0.25
    assert report["folds"][0]["event_success_metric"] == "gross_up_rate"
    assert report["development_period"] == {
        "start": "2024-01-01",
        "end": "2024-12-31",
    }
    assert report["flow_counts"]["final_event_count"] == 120
    assert report["overall"]["event_gross_up_rate"] == 0.41
    assert report["overall"]["event_joint_minute_hit_rate"] == 0.25
    assert report["overall"]["event_success_metric_value"] == 0.41
    assert report["by_year"] == [{"period": "2024", "event_count": 120}]
    assert "2099" not in str(report)


def test_backtest_window_never_invents_missing_dates() -> None:
    with pytest.raises(ValueError, match="requires explicit"):
        StrategyTester._resolve_backtest_window({}, "development")


def test_event_recompute_keeps_training_data_inside_train_period() -> None:
    spec = {
        "train_start": "2022-01-01",
        "train_end": "2023-12-31",
        "validate_start": "2024-01-01",
        "validate_end": "2024-12-31",
        "backtest_start": "2025-01-01",
        "backtest_end": "2025-12-31",
    }
    state = init_state("minute event test", max_epochs=1, experiment_spec=spec)
    state["strategy_code"] = """
def output_weights(train_data_bundle, validate_data_bundle, params):
    return validate_data_bundle["periodic_minute_events"].copy()

params = {}
output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)
"""
    strategy_result = {
        "required_data": [
            {
                "table_key": "periodic_minute_events",
                "type": "auxiliary",
                "fields": ["trigger_ts", "code"],
                "time_range": {"start": "2022-01-01", "end": "2023-12-31"},
            }
        ],
        "strategy_output": {
            "output_weights_df": {"datetime_column": "trigger_ts"}
        },
    }
    train_bundle = {
        "periodic_minute_events": pd.DataFrame(
            {"trigger_ts": [pd.Timestamp("2023-12-29 14:00:00")], "cash": [1.0]}
        )
    }
    development_bundle = {
        "periodic_minute_events": pd.DataFrame(
            {
                "trigger_ts": [pd.Timestamp("2024-01-02 10:00:00")],
                "sh600000": [1.0],
                "cash": [0.0],
            }
        )
    }

    with patch.object(
        StrategyTester,
        "_reload_required_bundle",
        side_effect=[train_bundle, development_bundle],
    ) as reload_bundle:
        _, metadata = StrategyTester._recompute_output_weights_for_backtest(
            state,
            strategy_result,
            spec,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

    assert reload_bundle.call_args_list[0].args[1:] == (
        "2022-01-01",
        "2023-12-31",
    )
    assert reload_bundle.call_args_list[1].args[1:] == (
        "2024-01-01",
        "2024-12-31",
    )
    assert metadata["train_range"] == {
        "start": "2022-01-01",
        "end": "2023-12-31",
    }
    assert metadata["params_source"] == "strategy_code.params"


def test_event_recompute_uses_frozen_params_and_skips_top_level_output_call() -> None:
    spec = {
        "backtest_mode": "event_parquet",
        "train_start": "2022-01-01",
        "train_end": "2023-12-31",
    }
    state = init_state("frozen params", max_epochs=1, experiment_spec=spec)
    state["strategy_code"] = """
params = {"threshold": 999}
def output_weights(train_data_bundle, validate_data_bundle, params):
    if params["threshold"] != 4:
        raise ValueError("params were not frozen")
    return validate_data_bundle["periodic_minute_events"].copy()
output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)
"""
    strategy_result = {
        "params": {"threshold": 4},
        "required_data": [
            {
                "table_key": "periodic_minute_events",
                "type": "auxiliary",
                "fields": ["trigger_ts", "code"],
            }
        ],
        "strategy_output": {
            "output_weights_df": {"datetime_column": "trigger_ts"}
        },
    }
    train_bundle = {"periodic_minute_events": pd.DataFrame()}
    development = pd.DataFrame(
        {
            "trigger_ts": [pd.Timestamp("2024-01-02 10:00:00")],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )

    with patch.object(
        StrategyTester,
        "_reload_required_bundle",
        side_effect=[train_bundle, {"periodic_minute_events": development}],
    ):
        weights, metadata = StrategyTester._recompute_output_weights_for_backtest(
            state,
            strategy_result,
            spec,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )

    assert weights.equals(development)
    assert metadata["params_source"] == "strategy_result.params"


def test_recompute_replaces_generated_validation_dates_with_requested_window() -> None:
    spec = {
        "train_start": "2022-01-01",
        "train_end": "2023-12-31",
        "validate_start": "2024-01-01",
        "validate_end": "2024-12-31",
        "backtest_start": "2025-01-01",
        "backtest_end": "2025-12-31",
    }
    state = init_state("date replacement test", max_epochs=1, experiment_spec=spec)
    state["strategy_code"] = """
params = {
    "validation_start": "2024-01-01",
    "validation_end": "2024-12-31",
}

def output_weights(train_data_bundle, validate_data_bundle, params):
    return pd.DataFrame(
        {
            "trade_date": [pd.Timestamp(params["validation_start"])],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )

output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)
"""
    strategy_result = {
        "required_data": [
            {
                "table_key": "stock_kline_daily_qfq",
                "type": "time_series",
                "fields": ["close"],
                "time_range": {"start": "2022-01-01", "end": "2023-12-31"},
            }
        ],
        "strategy_output": {
            "output_weights_df": {"datetime_column": "trade_date"}
        },
    }
    empty_bundle = {
        "stock_kline_daily_qfq": pd.DataFrame(
            {"trade_date": pd.to_datetime([]), "close": pd.Series(dtype=float)}
        )
    }

    with patch.object(
        StrategyTester,
        "_reload_required_bundle",
        side_effect=[empty_bundle, empty_bundle],
    ):
        output_weights, _ = StrategyTester._recompute_output_weights_for_backtest(
            state,
            strategy_result,
            spec,
            datetime(2025, 1, 1),
            datetime(2025, 12, 31),
        )

    assert output_weights["trade_date"].tolist() == [pd.Timestamp("2025-01-01")]


def test_recompute_replaces_walk_forward_training_and_execution_dates() -> None:
    spec = {
        "train_start": "2022-01-01",
        "train_end": "2023-12-31",
    }
    state = init_state("walk-forward date replacement", max_epochs=1, experiment_spec=spec)
    state["strategy_code"] = """
params = {
    "train_start": "2022-01-01",
    "train_end": "2023-12-31",
    "training_end": "2023-12-31",
    "first_decision_date": "2023-12-31",
    "first_execution_date": "2024-01-01",
    "final_execution_date": "2024-12-31",
}

def output_weights(train_data_bundle, validate_data_bundle, params):
    assert params["train_start"] == "2022-01-01"
    assert params["train_end"] == "2024-12-31"
    assert params["training_end"] == "2024-12-31"
    assert params["first_decision_date"] == "2024-12-31"
    assert params["first_execution_date"] == "2025-01-02"
    assert params["final_execution_date"] == "2025-12-31"
    return pd.DataFrame(
        {
            "trade_date": [pd.Timestamp(params["first_decision_date"])],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )
"""
    strategy_result = {
        "required_data": [
            {
                "table_key": "stock_kline_daily_qfq",
                "type": "time_series",
                "fields": ["close"],
            }
        ],
        "strategy_output": {
            "output_weights_df": {"datetime_column": "trade_date"}
        },
    }
    empty_bundle = {
        "stock_kline_daily_qfq": pd.DataFrame(
            {"trade_date": pd.to_datetime([]), "close": pd.Series(dtype=float)}
        )
    }

    with patch.object(
        StrategyTester,
        "_reload_required_bundle",
        side_effect=[empty_bundle, empty_bundle],
    ):
        output_weights, metadata = StrategyTester._recompute_output_weights_for_backtest(
            state,
            strategy_result,
            spec,
            datetime(2025, 1, 2),
            datetime(2025, 12, 31),
            training_end=datetime(2024, 12, 31),
        )

    assert output_weights["trade_date"].tolist() == [pd.Timestamp("2024-12-31")]
    assert metadata["train_range"] == {
        "start": "2022-01-01",
        "end": "2024-12-31",
    }


@pytest.mark.parametrize("negative_weight", [-0.2, "-0.2"])
def test_event_recomputed_weights_reject_short_positions(negative_weight: object) -> None:
    weights = pd.DataFrame(
        {
            "sh600000": [negative_weight],
            "cash": [1.0],
        },
        index=pd.DatetimeIndex(["2025-01-02 10:00:00"], name="trigger_ts"),
    )

    with pytest.raises(RuntimeError, match="cannot be negative"):
        StrategyTester._validate_event_long_only_weights(weights, ["sh600000"])


def test_event_recomputed_weights_accept_long_only_budget() -> None:
    weights = pd.DataFrame(
        {
            "sh600000": [0.6],
            "sz000001": [0.3],
            "cash": [0.1],
        },
        index=pd.DatetimeIndex(["2025-01-02 10:00:00"], name="trigger_ts"),
    )

    StrategyTester._validate_event_long_only_weights(
        weights,
        ["sh600000", "sz000001"],
    )


def test_event_recomputed_weights_accept_sparse_long_only_budget() -> None:
    weights = pd.DataFrame(
        {
            "sh600000": pd.arrays.SparseArray([0.6, 0.0], fill_value=0.0),
            "sz000001": pd.arrays.SparseArray([0.3, 0.0], fill_value=0.0),
            "cash": [0.1, 1.0],
        },
        index=pd.DatetimeIndex(
            ["2025-01-02 10:00:00", "2025-01-02 10:01:00"],
            name="trigger_ts",
        ),
    )

    StrategyTester._validate_event_long_only_weights(
        weights,
        ["sh600000", "sz000001"],
    )
