from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "openai" not in sys.modules:
    openai_stub = ModuleType("openai")

    class _DummyOpenAI:  # pragma: no cover - 仅用于测试导入
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda *a, **k: None))

    setattr(openai_stub, "OpenAI", _DummyOpenAI)
    sys.modules["openai"] = openai_stub

from quanta_agents.agents.input_interpreter_v2 import InputInterpreterV2
from quanta_agents.exceptions import AgentExecutionError


SOURCE_TEXT = "30天盘整，连续两天放量达到之前平均的两倍"


class FakeLLM:
    def __init__(self, replies: list[dict[str, object]]) -> None:
        self.replies = list(replies)
        self.calls: list[dict[str, object]] = []

    def complete(self, **kwargs: object) -> str:
        self.calls.append(dict(kwargs))
        return json.dumps(self.replies.pop(0), ensure_ascii=False)


def _valid_payload() -> dict[str, object]:
    return {
        "schema_version": "input_interpretation_v2",
        "original_text": SOURCE_TEXT,
        "explicit_conditions": [
            {
                "id": "explicit_001",
                "statement": "30天盘整",
                "source": "user",
                "evidence_quote": "30天盘整",
                "condition_spec": {
                    "field": "consolidation_window_days",
                    "operator": "==",
                    "value": 30,
                    "unit": "trading_days",
                },
            },
            {
                "id": "explicit_002",
                "statement": "连续两天放量达到之前平均的两倍",
                "source": "user",
                "evidence_quote": "连续两天放量达到之前平均的两倍",
                "condition_spec": {
                    "field": "high_volume_consecutive_days",
                    "operator": "==",
                    "value": 2,
                    "unit": "trading_days",
                },
            },
        ],
        "ambiguous_items": [
            {
                "id": "ambiguous_001",
                "item": "盘整",
                "reason": "原文没有给出波动率算法与上限",
                "source": "user",
                "evidence_quote": "盘整",
            }
        ],
        "unknown_items": [
            {
                "id": "unknown_001",
                "item": "交易范围",
                "reason": "计算时需要知道使用哪些股票",
                "source": "runtime",
                "runtime_key": "universe",
            }
        ],
        "temporary_baseline_decisions": [
            {
                "id": "decision_001",
                "field": "consolidation_definition",
                "value": "30日收盘收益率标准差",
                "source": "default",
                "reason": "第一次计算需要一个明确算法",
                "resolves_item_id": "ambiguous_001",
            },
            {
                "id": "decision_002",
                "field": "universe",
                "value": "dataset_defined",
                "source": "runtime",
                "runtime_key": "universe",
                "reason": "采用本次运行设置",
                "resolves_item_id": "unknown_001",
            },
        ],
        "automatic_mode": {
            "enabled": True,
            "can_continue": True,
            "blocking_reason": "",
        },
    }


def test_interpreter_parses_strict_json_and_preserves_original_text() -> None:
    fake = FakeLLM([_valid_payload()])
    result = InputInterpreterV2(client=fake, max_retries=1).run(
        SOURCE_TEXT,
        {"universe": "dataset_defined"},
    )

    assert result["original_text"] == SOURCE_TEXT
    assert result["explicit_conditions"][0]["source"] == "user"
    assert result["automatic_mode"]["can_continue"] is True
    assert fake.calls[0]["role"] == "input_interpreter_v2"


def test_interpreter_keeps_default_and_runtime_sources_visible() -> None:
    result = InputInterpreterV2(
        client=FakeLLM([_valid_payload()]),
        max_retries=1,
    ).run(SOURCE_TEXT, {"universe": "dataset_defined"})

    sources = {
        item["field"]: item["source"]
        for item in result["temporary_baseline_decisions"]
    }
    assert sources == {
        "consolidation_definition": "default",
        "universe": "runtime",
    }


def test_interpreter_rejects_condition_not_supported_by_original_text() -> None:
    payload = _valid_payload()
    payload["explicit_conditions"].append(  # type: ignore[union-attr]
            {
                "id": "explicit_003",
                "statement": "沪深300",
                "source": "user",
                "evidence_quote": "沪深300",
                "condition_spec": {
                    "field": "named_pool",
                    "operator": "==",
                    "value": "沪深300",
                    "unit": "pool",
                },
        }
    )

    with pytest.raises(AgentExecutionError, match="不在用户原文中"):
        InputInterpreterV2(
            client=FakeLLM([payload]),
            max_retries=1,
        ).run(SOURCE_TEXT, {"universe": "dataset_defined"})


def test_interpreter_rejects_explicit_condition_without_machine_readable_value() -> None:
    payload = _valid_payload()
    del payload["explicit_conditions"][1]["condition_spec"]  # type: ignore[index]

    with pytest.raises(AgentExecutionError, match="condition_spec"):
        InputInterpreterV2(
            client=FakeLLM([payload]),
            max_retries=1,
        ).run(SOURCE_TEXT, {"universe": "dataset_defined"})


def test_interpreter_rejects_unlinked_default_condition() -> None:
    payload = _valid_payload()
    payload["temporary_baseline_decisions"].append(  # type: ignore[union-attr]
        {
            "id": "decision_003",
            "field": "extra_filter",
            "value": "new_filter",
            "source": "default",
            "reason": "新增过滤条件",
            "resolves_item_id": "missing_item",
        }
    )

    with pytest.raises(AgentExecutionError, match="已记录的含糊项或未知项"):
        InputInterpreterV2(
            client=FakeLLM([payload]),
            max_retries=1,
        ).run(SOURCE_TEXT, {"universe": "dataset_defined"})


def test_interpreter_retries_when_exit_execution_differs_from_runtime() -> None:
    runtime_exit = "买入日记为T，完整持有5个实际交易日后，在T+5开盘卖出"
    wrong = _valid_payload()
    wrong["unknown_items"].append(  # type: ignore[union-attr]
        {
            "id": "unknown_002",
            "item": "退出时间",
            "reason": "原文没有说明退出时间",
            "source": "default",
        }
    )
    wrong["temporary_baseline_decisions"].append(  # type: ignore[union-attr]
        {
            "id": "decision_003",
            "field": "exit_execution",
            "value": "买入后第5个实际交易日收盘卖出",
            "source": "default",
            "reason": "第一次计算需要退出时间",
            "resolves_item_id": "unknown_002",
        }
    )
    corrected = deepcopy(wrong)
    corrected["temporary_baseline_decisions"][-1]["value"] = runtime_exit  # type: ignore[index]
    fake = FakeLLM([wrong, corrected])

    result = InputInterpreterV2(client=fake, max_retries=2).run(
        SOURCE_TEXT,
        {
            "universe": "dataset_defined",
            "execution": {"exit_execution": runtime_exit},
        },
    )

    assert len(fake.calls) == 2
    assert result["temporary_baseline_decisions"][-1]["value"] == runtime_exit
    assert "execution.exit_execution" in str(fake.calls[1]["user_prompt"])


def test_interpreter_retries_when_missing_bar_policy_differs_from_runtime() -> None:
    runtime_policy = (
        "某股票当日缺少K线时不成交；已有计划持仓目标继续到原退出日，"
        "不得因缺K清零；恢复K线后按当日仍有效的计划执行；"
        "未买到不顺延原计划退出日；不得读取或推断下一交易日是否有K线"
    )
    wrong = _valid_payload()
    wrong["unknown_items"].append(  # type: ignore[union-attr]
        {
            "id": "unknown_002",
            "item": "缺少K线时如何处理",
            "reason": "原文没有说明停牌或缺少K线时如何处理",
            "source": "default",
        }
    )
    wrong["temporary_baseline_decisions"].append(  # type: ignore[union-attr]
        {
            "id": "decision_003",
            "field": "missing_bar_policy",
            "value": "缺K时清零，恢复后重新计算持有期",
            "source": "default",
            "reason": "第一次计算需要缺K处理办法",
            "resolves_item_id": "unknown_002",
        }
    )
    corrected = deepcopy(wrong)
    corrected["temporary_baseline_decisions"][-1]["value"] = runtime_policy  # type: ignore[index]
    fake = FakeLLM([wrong, corrected])

    result = InputInterpreterV2(client=fake, max_retries=2).run(
        SOURCE_TEXT,
        {
            "universe": "dataset_defined",
            "execution": {"missing_bar_policy": runtime_policy},
        },
    )

    assert len(fake.calls) == 2
    assert result["temporary_baseline_decisions"][-1]["value"] == runtime_policy
    assert "execution.missing_bar_policy" in str(fake.calls[1]["user_prompt"])
