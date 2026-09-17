from __future__ import annotations

import json

import pytest

from quanta_agents.agents.baseline_builder_v2 import BaselineBuilderV2
from quanta_agents.exceptions import AgentExecutionError


class FakeLLM:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def complete(self, **_kwargs: object) -> str:
        return json.dumps(self.payload, ensure_ascii=False)


INTERPRETATION = {
    "explicit_conditions": [
        {
            "id": "explicit_001",
            "condition_spec": {
                "field": "high_volume_consecutive_days",
                "operator": "==",
                "value": 2,
                "unit": "trading_days",
            },
        },
        {
            "id": "explicit_002",
            "condition_spec": {
                "field": "box_to_kline_max_ratio",
                "operator": "<",
                "value": 0.5,
                "unit": "ratio",
            },
        },
    ],
    "temporary_baseline_decisions": [
        {"id": "decision_001", "field": "volatility_limit", "value": 0.015},
        {"id": "decision_002", "field": "holding_days", "value": 5},
    ]
}
RUNTIME = {
    "data": {
        "table_key": "stock_kline_daily_qfq",
        "available_fields": [
            "open", "high", "low", "close", "volume", "amount", "float_shares"
        ],
        "backtest_dataset": "vnpy_stock_daily_qfq",
    },
    "universe": {
        "required_data": {
            "type": "dataset_defined",
            "value": "stock_kline_daily_qfq",
        }
    },
}


def payload() -> dict[str, object]:
    return {
        "hypothesis": "完整规则",
        "strategy_modification": "忠实基准，没有改进条件",
        "required_data": [
            {
                "table_key": "stock_kline_daily_qfq",
                "type": "time_series",
                "fields": ["open", "high", "low", "close", "volume"],
                "universe": {
                    "type": "dataset_defined",
                    "value": "stock_kline_daily_qfq",
                },
                "time_range": {"start": "2015-01-05", "end": "2024-12-31"},
                "purpose": "计算原始规则",
            }
        ],
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
        "missing_concepts": [],
        "candidate_mode": "baseline",
        "baseline_parameters": {
            "high_volume_consecutive_days": 2,
            "box_to_kline_max_ratio": 0.5,
            "volatility_limit": 0.015,
            "holding_days": 5,
        },
        "decision_map": [
            {
                "decision_id": "explicit_001",
                "source_kind": "explicit_condition",
                "field": "high_volume_consecutive_days",
                "operator": "==",
                "value": 2,
                "unit": "trading_days",
                "implemented_as": "连续检查两个交易日",
            },
            {
                "decision_id": "explicit_002",
                "source_kind": "explicit_condition",
                "field": "box_to_kline_max_ratio",
                "operator": "<",
                "value": 0.5,
                "unit": "ratio",
                "implemented_as": "箱体除以K线长度小于0.5",
            },
            {
                "decision_id": "decision_001",
                "source_kind": "temporary_decision",
                "field": "volatility_limit",
                "operator": "assign",
                "value": 0.015,
                "implemented_as": "阈值0.015",
            },
            {
                "decision_id": "decision_002",
                "source_kind": "temporary_decision",
                "field": "holding_days",
                "operator": "assign",
                "value": 5,
                "implemented_as": "持有5日",
            },
        ],
    }


def test_baseline_builder_accepts_runtime_data_and_maps_every_decision() -> None:
    result = BaselineBuilderV2(client=FakeLLM(payload()), max_retries=1).run(
        INTERPRETATION, RUNTIME
    )

    assert result["candidate_mode"] == "baseline"
    assert result["required_data"][0]["universe"]["type"] == "dataset_defined"


def test_baseline_builder_rejects_unapproved_data_field() -> None:
    bad = payload()
    bad["required_data"][0]["fields"].append("future_return")

    with pytest.raises(AgentExecutionError, match="没有的字段"):
        BaselineBuilderV2(client=FakeLLM(bad), max_retries=1).run(
            INTERPRETATION, RUNTIME
        )


def test_baseline_builder_requires_every_temporary_decision() -> None:
    bad = payload()
    bad["decision_map"] = [
        item for item in bad["decision_map"] if item["decision_id"] != "decision_002"
    ]

    with pytest.raises(AgentExecutionError, match="每个临时基准决定"):
        BaselineBuilderV2(client=FakeLLM(bad), max_retries=1).run(
            INTERPRETATION, RUNTIME
        )


def test_baseline_builder_rejects_missing_two_day_condition() -> None:
    bad = payload()
    bad["decision_map"] = [
        item for item in bad["decision_map"] if item["decision_id"] != "explicit_001"
    ]

    with pytest.raises(AgentExecutionError, match="explicit_001"):
        BaselineBuilderV2(client=FakeLLM(bad), max_retries=1).run(
            INTERPRETATION, RUNTIME
        )


def test_baseline_builder_rejects_wrong_half_ratio() -> None:
    bad = payload()
    bad["baseline_parameters"]["box_to_kline_max_ratio"] = 0.4
    for item in bad["decision_map"]:
        if item["decision_id"] == "explicit_002":
            item["value"] = 0.4

    with pytest.raises(AgentExecutionError, match="value 与输入 explicit_002 不一致"):
        BaselineBuilderV2(client=FakeLLM(bad), max_retries=1).run(
            INTERPRETATION, RUNTIME
        )
