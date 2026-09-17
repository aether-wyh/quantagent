from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from quanta_agents.agents.strategy_agent import StrategyAgent
from quanta_agents.agents.validate_agent import OutputWeightsRuleChecker
from quanta_agents.exceptions import AgentExecutionError
from quanta_agents.local_parquet_backtest import _build_execution_schedule
from quanta_agents.period_data import combine_historical_membership_data
from quanta_agents.semantic.layer import SemanticLayer
from quanta_agents.semantic.metadata import (
    MetadataManager,
    ParquetConnector,
    historical_index_membership_table,
    normalize_historical_index_universe,
)


def _daily_rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for date in pd.to_datetime(["2024-01-02", "2024-01-03"]):
        for code, price in (("sz000001", 10.0), ("sh600000", 20.0)):
            rows.append(
                {
                    "date": date,
                    "code": code,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 1000.0,
                    "amount": 10_000.0,
                    "float_shares": 1_000_000.0,
                    "total_shares": 1_200_000.0,
                    "raw_prev_close": price,
                    "is_st": False,
                    "is_delisting": False,
                    "float_market_cap": price * 1_000_000.0,
                    "total_market_cap": price * 1_200_000.0,
                    "qfq_ratio": 1.0,
                    "vwap_qfq": price,
                    "prev_close": price,
                    "gu_1m": 0.1,
                    "gd_1m": 0.2,
                    "rbar_up17": 0.01,
                    "rbar_down17": -0.01,
                    "r_0931_1000": 0.001,
                    "r_1001_1030": 0.002,
                    "overnight_return": 0.003,
                }
            )
    return pd.DataFrame(rows)


def test_supported_historical_index_names_include_hs300_alias() -> None:
    assert normalize_historical_index_universe("hs300") == "csi300"
    assert normalize_historical_index_universe("csi300") == "csi300"
    for name in ("csi500", "csi800", "csi1000", "csiall"):
        assert normalize_historical_index_universe(name) == name
        assert historical_index_membership_table(name) == f"{name}_membership"


def test_research_planner_catalog_lists_historical_index_choices() -> None:
    manager = MetadataManager.from_yaml_files()
    available = set(manager.list_historical_universes())
    assert {"hs300", "csi300", "csi500", "csi800", "csi1000", "csiall"}.issubset(
        available
    )
    assert "cn_all_a" not in available
    assert manager.get_universe("hs300")["historical_membership"] == "csi300"


def test_csi500_parquet_rows_are_filtered_by_each_trade_date() -> None:
    with TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        parquet_path = root / "daily.parquet"
        membership_path = root / "csi500.txt"
        _daily_rows().to_parquet(parquet_path, index=False)
        membership_path.write_text(
            "SZ000001\t2024-01-02\t2024-01-02\n"
            "SH600000\t2024-01-03\t2024-01-03\n",
            encoding="utf-8",
        )
        metadata = MetadataManager(
            {
                "datasets": [
                    {
                        "name": "stock_kline_daily_qfq",
                        "type": "time_series",
                        "datetime_column": "trade_date",
                        "symbol_column": "code",
                    },
                    {
                        "name": "csi500_membership",
                        "type": "static",
                        "symbol_column": "code",
                    },
                ],
                "universes": {"csi500": {"symbols": ["999999.SH"]}},
            }
        )
        connector = ParquetConnector(
            str(parquet_path),
            historical_membership_paths={"csi500": str(membership_path)},
        )
        layer = SemanticLayer(metadata, default_engine="parquet")
        layer._connectors["parquet"] = connector
        try:
            assert layer.get_universe_list("csi500") == ["000001.SZ", "600000.SH"]
            result = layer.load_time_series_data(
                "stock_kline_daily_qfq",
                ["open", "close"],
                {"start": "2024-01-02", "end": "2024-01-03"},
                {"type": "named_pool", "value": "csi500"},
            )
        finally:
            connector.conn.close()

    assert result[["trade_date", "code"]].astype(str).values.tolist() == [
        ["2024-01-02", "000001.SZ"],
        ["2024-01-03", "600000.SH"],
    ]


def test_strategy_agent_adds_selected_historical_membership_table(tmp_path: Path) -> None:
    membership_path = tmp_path / "csi1000.txt"
    membership_path.write_text(
        "SZ000001\t2024-01-01\t2024-12-31\n",
        encoding="utf-8",
    )
    required_data = [
        {
            "table_key": "stock_kline_daily_qfq",
            "type": "time_series",
            "fields": ["open", "close"],
            "universe": {"type": "named_pool", "value": "csi1000"},
        }
    ]
    with (
        patch.dict("os.environ", {"QUANTA_DATA_ENGINE": "parquet"}, clear=False),
        patch(
            "quanta_agents.agents.strategy_agent.resolve_historical_index_membership_path",
            return_value=membership_path,
        ),
    ):
        prepared = StrategyAgent._prepare_required_data(
            required_data,
            "2024-01-01",
            "2024-12-31",
        )

    assert [item["table_key"] for item in prepared] == [
        "stock_kline_daily_qfq",
        "csi1000_membership",
    ]


def test_dataset_defined_does_not_add_index_membership() -> None:
    required_data = [
        {
            "table_key": "stock_kline_daily_qfq",
            "type": "time_series",
            "fields": ["open", "close"],
            "universe": {
                "type": "dataset_defined",
                "value": "stock_kline_daily_qfq",
            },
        }
    ]
    with patch.dict("os.environ", {"QUANTA_DATA_ENGINE": "parquet"}, clear=False):
        prepared = StrategyAgent._prepare_required_data(
            required_data,
            "2024-01-01",
            "2024-12-31",
        )
    assert [item["table_key"] for item in prepared] == ["stock_kline_daily_qfq"]


def test_strategy_agent_does_not_fall_back_to_static_index_symbols(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing-csi500.txt"
    required_data = [
        {
            "table_key": "stock_kline_daily_qfq",
            "type": "time_series",
            "fields": ["open", "close"],
            "universe": {"type": "named_pool", "value": "csi500"},
        }
    ]
    with (
        patch.dict("os.environ", {"QUANTA_DATA_ENGINE": "parquet"}, clear=False),
        patch(
            "quanta_agents.agents.strategy_agent.resolve_historical_index_membership_path",
            return_value=missing_path,
        ),
    ):
        try:
            StrategyAgent._prepare_required_data(
                required_data,
                "2024-01-01",
                "2024-12-31",
            )
        except AgentExecutionError as exc:
            assert "不能改用当前静态名单" in str(exc)
        else:
            raise AssertionError("缺少历史成分文件时不应继续使用静态名单")


def test_selected_membership_table_is_combined_for_backtest() -> None:
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2024-01-02"],
            "end_date": ["2024-01-03"],
        }
    )
    required_data = [
        {
            "table_key": "stock_kline_daily_qfq",
            "universe": {"type": "named_pool", "value": "csi800"},
        },
        {
            "table_key": "csi800_membership",
            "fields": ["code", "start_date", "end_date"],
        },
    ]
    combined = combine_historical_membership_data(
        {"csi800_membership": membership},
        required_data,
    )
    assert combined is not None
    assert combined.equals(membership)


def test_execution_schedule_requires_membership_on_decision_and_execution_dates() -> None:
    weights = pd.DataFrame(
        {"sz000001": [1.0]},
        index=pd.to_datetime(["2024-01-02"]),
    )
    market_dates = pd.DatetimeIndex(pd.to_datetime(["2024-01-02", "2024-01-03"]))

    execution_only = {
        "sz000001": [(pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-03"))]
    }
    schedule = _build_execution_schedule(weights, market_dates, execution_only)
    assert float(schedule[pd.Timestamp("2024-01-03")]["sz000001"]) == 0.0

    both_dates = {
        "sz000001": [(pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03"))]
    }
    schedule = _build_execution_schedule(weights, market_dates, both_dates)
    assert float(schedule[pd.Timestamp("2024-01-03")]["sz000001"]) == 1.0


def test_execution_schedule_keeps_accepted_target_after_membership_ends() -> None:
    market_dates = pd.DatetimeIndex(
        pd.to_datetime(
            [
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-08",
                "2024-01-09",
            ]
        )
    )
    weights = pd.DataFrame(
        {"sz000001": [0.4, 0.4, 0.4, 0.2, 0.0]},
        index=pd.to_datetime(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"]
        ),
    )
    membership = {
        "sz000001": [(pd.Timestamp("2023-01-01"), pd.Timestamp("2024-01-03"))]
    }

    schedule = _build_execution_schedule(weights, market_dates, membership)

    assert [
        float(schedule[date]["sz000001"])
        for date in market_dates[1:]
    ] == [0.4, 0.4, 0.4, 0.2, 0.0]


def test_execution_schedule_retries_entry_after_execution_day_rejection() -> None:
    market_dates = pd.DatetimeIndex(
        pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    )
    weights = pd.DataFrame(
        {"sz000001": [0.4, 0.4, 0.4]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
    )
    membership = {
        "sz000001": [
            (pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-02")),
            (pd.Timestamp("2024-01-04"), pd.Timestamp("2024-01-05")),
        ]
    }

    schedule = _build_execution_schedule(weights, market_dates, membership)

    assert float(schedule[pd.Timestamp("2024-01-03")]["sz000001"]) == 0.0
    assert float(schedule[pd.Timestamp("2024-01-04")]["sz000001"]) == 0.0
    assert float(schedule[pd.Timestamp("2024-01-05")]["sz000001"]) == 0.4


def test_weight_check_requires_membership_when_target_is_first_created() -> None:
    output_weights = pd.DataFrame(
        {"date": [pd.Timestamp("2024-01-02")], "000001.SZ": [1.0]}
    )
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2024-01-03"],
            "end_date": ["2024-01-03"],
        }
    )
    market = pd.DataFrame(
        {"trade_date": pd.to_datetime(["2024-01-02", "2024-01-03"])}
    )
    passed, details = OutputWeightsRuleChecker._check_historical_membership(
        output_weights,
        "date",
        ["000001.SZ"],
        membership,
        market,
    )
    assert passed is False
    assert "decision=2024-01-02" in details


def test_weight_check_allows_fixed_target_after_membership_ends() -> None:
    output_weights = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            ),
            "000001.SZ": [0.4, 0.4, 0.2, 0.0],
        }
    )
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2023-01-01"],
            "end_date": ["2024-01-02"],
        }
    )
    market = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"]
            )
        }
    )

    passed, details = OutputWeightsRuleChecker._check_historical_membership(
        output_weights,
        "date",
        ["000001.SZ"],
        membership,
        market,
    )

    assert passed is True
    assert "unchanged, reduced and closed" in details


def test_weight_check_rejects_increase_after_membership_ends() -> None:
    output_weights = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "000001.SZ": [0.2, 0.4],
        }
    )
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2023-01-01"],
            "end_date": ["2024-01-02"],
        }
    )
    market = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                ["2024-01-02", "2024-01-03", "2024-01-04"]
            )
        }
    )

    passed, details = OutputWeightsRuleChecker._check_historical_membership(
        output_weights,
        "date",
        ["000001.SZ"],
        membership,
        market,
    )

    assert passed is False
    assert "increase 0.2->0.4" in details
