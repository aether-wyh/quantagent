from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pandas as pd

from quanta_agents.agents.strategy_tester import StrategyTester
from quanta_agents.research_evaluation import build_development_folds
from quanta_agents.state import init_state
from quanta_agents.v2_runtime import build_stage_spec, default_cn_daily_v2_profile


def _state():
    state = init_state(
        "walk-forward test",
        max_epochs=2,
        experiment_spec={
            "experiment_id": "exp_walk_forward_test",
            "train_start": "2020-01-01",
            "train_end": "2022-12-30",
            "validate_start": "2023-01-02",
            "validate_end": "2023-12-29",
            "backtest_start": "2024-01-02",
            "backtest_end": "2024-12-31",
            "development_folds": 3,
            "gap_trading_days": 10,
            "run_cost_stress": True,
            "run_delay_stress": True,
            "slippage": 0.00025,
            "evaluation": {
                "min_sharpe_ratio": 0.5,
                "min_return_rate": 0.03,
                "max_drawdown": 0.2,
            },
        },
    )
    state["strategy_code"] = "def output_weights(*args):\n    return None\n"
    state["strategy_result"] = {
        "output_weights": pd.DataFrame(
            [{"datetime": "2023-01-02", "000001.SZ": 0.8, "cash": 0.2}]
        ),
        "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
    }
    state["evaluation_stage"] = "development"
    return state


def _stats() -> dict[str, object]:
    return {
        "capital": 1_000_000.0,
        "end_balance": 1_100_000.0,
        "total_return": 0.1,
        "annual_return": 0.1,
        "sharpe_ratio": 1.0,
        "max_drawdown": -50_000.0,
        "max_ddpercent": -0.05,
        "total_trade_count": 20,
        "_backtest_debug": {
            "transaction_cost_rule": {
                "type": "dated",
                "description": "测试中的实际分日期费用",
            }
        },
    }


def _stats_with_actual_slippage(*_args, **kwargs) -> dict[str, object]:
    stats = _stats()
    stats["_backtest_debug"] = {
        "transaction_cost_rule": {
            "type": "dated",
            "description": "测试中的实际分日期费用",
            "slippage_rate_each_side": kwargs["slippage"],
        }
    }
    return stats


def test_local_parquet_development_runs_folds_and_stress_tests() -> None:
    state = _state()
    weights = state["strategy_result"]["output_weights"]
    market_dates = pd.bdate_range("2023-01-02", "2023-12-29")

    with patch.dict("os.environ", {"QUANTA_BACKTEST_DB_BACKEND": "parquet"}, clear=False):
        with patch(
            "quanta_agents.local_parquet_backtest.load_market_dates",
            return_value=market_dates,
        ):
            prepared_bundles = [{"fold": number} for number in range(3)]
            with patch(
                "quanta_agents.local_parquet_backtest.prepare_target_weight_backtest_market",
                side_effect=prepared_bundles,
            ) as prepare_market:
                with patch.object(
                    StrategyTester,
                    "_recompute_output_weights_for_backtest",
                    return_value=(weights, {}),
                ) as recompute:
                    with patch(
                        "quanta_agents.local_parquet_backtest.run_target_weight_backtest",
                        side_effect=_stats_with_actual_slippage,
                    ) as local_backtest:
                        with patch.object(StrategyTester, "_export_backtest_artifacts", return_value={}):
                            result = StrategyTester().run(state)

    assert recompute.call_count == 3
    assert prepare_market.call_count == 3
    assert local_backtest.call_count == 9
    assert all(call.kwargs["start"].year == 2023 for call in local_backtest.call_args_list)
    assert all(call.kwargs["end"].year == 2023 for call in local_backtest.call_args_list)
    training_ends = [call.kwargs["training_end"] for call in recompute.call_args_list]
    assert training_ends == sorted(training_ends)
    for fold_number, prepared_bundle in enumerate(prepared_bundles):
        fold_calls = local_backtest.call_args_list[fold_number * 3 : fold_number * 3 + 3]
        assert all(
            call.kwargs["prepared_market"] is prepared_bundle
            for call in fold_calls
        )
    assert result["test_result"] is not None
    assert result["test_result"].passed is True
    assert result["development_report"]["fold_count"] == 3
    assert result["development_report"]["cost_stress_passed"] is True
    assert result["development_report"]["delay_stress_passed"] is True
    assert result["development_report"]["transaction_cost_rule"] == {
        "type": "dated",
        "description": "测试中的实际分日期费用",
        "slippage_rate_each_side": 0.00025,
    }
    assert result["development_report"]["double_cost_rule"] == {
        "type": "dated",
        "description": "测试中的实际分日期费用",
        "slippage_rate_each_side": 0.0005,
    }


def test_strategy_tester_confirmation_folds_use_only_available_history() -> None:
    state = _state()
    confirmation = build_stage_spec(
        default_cn_daily_v2_profile(),
        experiment_id="exp_confirmation_history_test",
        stage="confirmation",
    )
    state["experiment_spec"] = confirmation
    weights = state["strategy_result"]["output_weights"]
    market_dates = pd.bdate_range("2022-01-04", "2024-12-31")
    expected_folds = build_development_folds(
        confirmation,
        trading_dates=market_dates,
    )

    with patch.dict("os.environ", {"QUANTA_BACKTEST_DB_BACKEND": "parquet"}, clear=False):
        with patch(
            "quanta_agents.local_parquet_backtest.load_market_dates",
            return_value=market_dates,
        ):
            with patch(
                "quanta_agents.local_parquet_backtest.prepare_target_weight_backtest_market",
                side_effect=[{"fold": number} for number in range(3)],
            ):
                with patch.object(
                    StrategyTester,
                    "_recompute_output_weights_for_backtest",
                    return_value=(weights, {}),
                ) as recompute:
                    with patch(
                        "quanta_agents.local_parquet_backtest.run_target_weight_backtest",
                        side_effect=[_stats() for _ in range(9)],
                    ) as local_backtest:
                        with patch.object(
                            StrategyTester,
                            "_export_backtest_artifacts",
                            return_value={},
                        ):
                            StrategyTester().run(state)

    for fold_number in range(3):
        base_call, double_call, delay_call = local_backtest.call_args_list[
            fold_number * 3 : fold_number * 3 + 3
        ]
        assert base_call.kwargs["buy_cost"] == 0.0003
        assert base_call.kwargs["sell_cost_before_change"] == 0.0013
        assert base_call.kwargs["sell_cost"] == 0.0008
        assert base_call.kwargs["sell_cost_change_date"] == "2023-08-28"
        assert double_call.kwargs["buy_cost"] == 0.0006
        assert double_call.kwargs["sell_cost_before_change"] == 0.0026
        assert double_call.kwargs["sell_cost"] == 0.0016
        assert double_call.kwargs["sell_cost_change_date"] == "2023-08-28"
        assert delay_call.kwargs["sell_cost_before_change"] == 0.0013
        assert delay_call.kwargs["sell_cost"] == 0.0008

    actual_training_ends = [
        call.kwargs["training_end"]
        for call in recompute.call_args_list
    ]
    assert actual_training_ends == [fold.train_end for fold in expected_folds]
    assert actual_training_ends[0] == "2021-12-31"
    assert all(
        training_end < fold.test_start
        for training_end, fold in zip(actual_training_ends, expected_folds, strict=True)
    )


def test_confirmation_reloads_membership_after_compacted_snapshot() -> None:
    state = _state()
    confirmation = build_stage_spec(
        default_cn_daily_v2_profile(),
        experiment_id="exp_confirmation_membership_reload_test",
        stage="confirmation",
    )
    state["experiment_spec"] = confirmation
    weights = state["strategy_result"]["output_weights"]
    state["strategy_result"].update(
        {
            "required_data": [
                {
                    "table_key": "stock_kline_daily_qfq",
                    "type": "time_series",
                    "fields": ["open", "high", "low", "close", "volume"],
                    "universe": {"type": "named_pool", "value": "csiall"},
                },
                {
                    "table_key": "csiall_membership",
                    "type": "static",
                    "fields": ["code", "start_date", "end_date"],
                },
            ],
            # 入选候选的快照会清空大数据表，确认期必须按折重新加载。
            "train_data_bundle": {},
            "validate_data_bundle": {},
        }
    )
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": pd.to_datetime(["2020-01-01"]),
            "end_date": pd.to_datetime(["2024-12-31"]),
        }
    )
    market_dates = pd.bdate_range("2022-01-04", "2024-12-31")

    def recompute_for_fold(*_args, **_kwargs):
        return weights.copy(), {"_membership_df": membership.copy()}

    with patch.dict("os.environ", {"QUANTA_BACKTEST_DB_BACKEND": "parquet"}, clear=False):
        with patch(
            "quanta_agents.local_parquet_backtest.load_market_dates",
            return_value=market_dates,
        ):
            with patch(
                "quanta_agents.local_parquet_backtest.prepare_target_weight_backtest_market",
                side_effect=[{"fold": number} for number in range(3)],
            ):
                with patch.object(
                    StrategyTester,
                    "_recompute_output_weights_for_backtest",
                    side_effect=recompute_for_fold,
                ) as recompute:
                    with patch(
                        "quanta_agents.local_parquet_backtest.run_target_weight_backtest",
                        side_effect=[_stats() for _ in range(9)],
                    ) as local_backtest:
                        with patch.object(
                            StrategyTester,
                            "_export_backtest_artifacts",
                            return_value={},
                        ):
                            result = StrategyTester().run(state)

    assert recompute.call_count == 3
    assert result["development_report"]["fold_count"] == 3
    assert all(
        call.args[3] >= datetime(2022, 1, 1)
        and call.args[4] <= datetime(2024, 12, 31)
        for call in recompute.call_args_list
    )
    assert local_backtest.call_count == 9
    assert all(
        call.kwargs["membership_df"]["code"].tolist() == ["000001.SZ"]
        for call in local_backtest.call_args_list
    )
    assert all(
        call.kwargs["start"] >= datetime(2022, 1, 1)
        and call.kwargs["end"] <= datetime(2024, 12, 31)
        for call in local_backtest.call_args_list
    )


def test_delay_moves_sparse_signals_by_one_real_market_day() -> None:
    weights = pd.DataFrame(
        [
            {"datetime": "2024-01-02", "000001.SZ": 0.8, "cash": 0.2},
            {"datetime": "2024-01-10", "000001.SZ": 0.3, "cash": 0.7},
        ]
    )
    strategy_result = {
        "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}}
    }

    delayed = StrategyTester._delay_output_weights_one_day(
        weights,
        strategy_result,
        pd.bdate_range("2024-01-02", "2024-01-12"),
    )

    assert delayed["datetime"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-03",
        "2024-01-11",
    ]
    assert delayed["000001.SZ"].tolist() == [0.8, 0.3]


def test_reloaded_membership_hides_dates_after_requested_period() -> None:
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ"],
            "start_date": ["2020-01-01", "2025-01-01"],
            "end_date": ["2025-12-31", None],
        }
    )
    required = [
        {
            "table_key": "csi300_membership",
            "type": "static",
            "fields": ["code", "start_date", "end_date"],
        }
    ]

    with patch(
        "quanta_agents.agents.strategy_tester.load_required_data",
        return_value=[{"table_key": "csi300_membership", "data": membership}],
    ):
        bundle = StrategyTester._reload_required_bundle(
            required,
            "2023-01-01",
            "2023-12-31",
        )

    visible = bundle["csi300_membership"]
    assert visible["code"].tolist() == ["000001.SZ"]
    assert visible["end_date"].dt.strftime("%Y-%m-%d").tolist() == ["2023-12-31"]


def test_final_test_uses_locked_period_once() -> None:
    state = _state()
    state["evaluation_stage"] = "final_test"
    weights = state["strategy_result"]["output_weights"]

    with patch.dict("os.environ", {"QUANTA_BACKTEST_DB_BACKEND": "parquet"}, clear=False):
        with patch.object(
            StrategyTester,
            "_recompute_output_weights_for_backtest",
            return_value=(weights, {}),
        ) as recompute:
            with patch(
                "quanta_agents.local_parquet_backtest.run_target_weight_backtest",
                return_value=_stats(),
            ) as local_backtest:
                with patch.object(StrategyTester, "_export_backtest_artifacts", return_value={}):
                    result = StrategyTester().run(state)

    assert recompute.call_count == 1
    assert local_backtest.call_count == 1
    assert local_backtest.call_args.kwargs["start"] == datetime(2024, 1, 2)
    assert local_backtest.call_args.kwargs["end"] == datetime(2024, 12, 31)
    assert result["test_result"] is not None
    assert result["backtest_debug"]["transaction_cost_rule"] == {
        "type": "dated",
        "description": "测试中的实际分日期费用",
    }
