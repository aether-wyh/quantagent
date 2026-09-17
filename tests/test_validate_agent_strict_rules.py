from __future__ import annotations

from pathlib import Path
import sys
from types import ModuleType

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "langgraph" not in sys.modules:
    langgraph_stub = ModuleType("langgraph")
    graph_stub = ModuleType("langgraph.graph")
    graph_state_stub = ModuleType("langgraph.graph.state")
    graph_stub.END = object()  # type: ignore[attr-defined]
    graph_stub.StateGraph = object  # type: ignore[attr-defined]
    graph_state_stub.CompiledStateGraph = object  # type: ignore[attr-defined]
    sys.modules["langgraph"] = langgraph_stub
    sys.modules["langgraph.graph"] = graph_stub
    sys.modules["langgraph.graph.state"] = graph_state_stub

from quanta_agents.agents.validate_agent import OutputWeightsRuleChecker, ValidateAgent
from quanta_agents.prompt_loader import load_agent_prompt


def _strategy_output() -> dict[str, object]:
    return {
        "factor": {
            "function_name": "build_factor",
            "expected_characteristics": ["取值范围正确", "没有未来数据"],
        },
        "output_weights_df": {
            "function_name": "output_weights",
            "datetime_column": "trade_date",
        },
    }


def _passing_summary() -> dict[str, object]:
    return {
        "passed": True,
        "output_weights_check": {"passed": True, "details": "ok"},
        "intermediate_variable_checks": {
            "factor": {"passed": True, "details": "ok"},
        },
        "hypothesis_consistency_check": {"passed": True, "details": "ok"},
        "future_function_check": {"passed": True, "details": "ok"},
        "suggestions": [],
    }


def test_validation_keeps_dataset_column_descriptions_for_script_generation() -> None:
    description = (
        "stock_kline_daily_qfq: symbol_column=code; "
        "datetime_column=trade_date; actual columns=[code, trade_date, close]"
    )
    state = {
        "hypothesis_generation_meta": {"hypothesis": "测试假设"},
        "experiment_spec": {
            "train_start": "2020-01-01",
            "train_end": "2022-12-31",
            "validate_start": "2023-01-01",
            "validate_end": "2023-12-31",
            "backtest_start": "2024-01-01",
            "backtest_end": "2025-12-31",
        },
    }
    context = ValidateAgent._build_strategy_context(
        state,  # type: ignore[arg-type]
        {
            "strategy_output": {},
            "required_data": [{"table_key": "stock_kline_daily_qfq"}],
            "required_data_descriptions": description,
        },
    )

    prompt = load_agent_prompt(
        "validate_agent",
        "user_prompt_template",
        hypothesis="ADX按Wilder方法计算",
        strategy_output_json="{}",
        function_sources_json='{"build_factor": "def build_factor(): ..."}',
        required_data_descriptions=context["required_data_descriptions"],
        data_shapes="{}",
    )

    assert context["required_data_descriptions"] == description
    assert "symbol_column=code" in prompt
    assert "datetime_column=trade_date" in prompt
    assert "ADX按Wilder方法计算" in prompt
    assert "def build_factor()" in prompt


def test_validation_prompt_lists_forbidden_names() -> None:
    prompt = load_agent_prompt("validate_agent", "system_prompt")

    for token in (
        "open_",
        "read_",
        "load_",
        "save_",
        "load_factor",
        "save_result",
        "replace",
        "rename",
        "bisect",
        "numpy.searchsorted",
        "不得对字符串、列名或说明文字调用这些方法",
    ):
        assert token in prompt


def test_validation_prompt_respects_completed_period_dates() -> None:
    prompt = load_agent_prompt("validate_agent", "system_prompt")

    assert "不得用本月月末结果检查本月月末之前的日期" in prompt
    assert "正常使用上一个已完成周期的结果" in prompt


def test_main_validation_uses_fixed_program_only(monkeypatch) -> None:
    output_weights = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2023-01-03", "2023-01-04"]),
            "000001.SZ": [0.5, 0.5],
            "cash": [0.5, 0.5],
        }
    )
    state = {
        "strategy_code": "",
        "strategy_result": {
            "output_weights": output_weights,
            "strategy_output": {
                "output_weights_df": {
                    "description": "目标比例",
                    "function_name": "output_weights",
                    "datetime_column": "trade_date",
                }
            },
            "universe": [
                {"symbols": ["000001.SZ"], "asset": "中国股票"}
            ],
            "validate_data_bundle": {},
        },
        "hypothesis_generation_meta": {"hypothesis": "测试策略"},
        "experiment_spec": {},
        "epoch_index": 1,
        "strategy_validate_round": 1,
        "max_epochs": 1,
        "history": [],
        "validation_result": {},
        "validation_summary": {},
        "validation_feedback": {},
        "test_result": None,
    }

    def must_not_run(*args, **kwargs):
        raise AssertionError("主流程不应调用大模型代码检查")

    outcomes: list[bool] = []
    monkeypatch.setattr(ValidateAgent, "_run_script_validation_loop", must_not_run)
    monkeypatch.setattr(ValidateAgent, "_run_analysis_loop", must_not_run)
    monkeypatch.setattr(
        ValidateAgent,
        "_apply_validation_outcome",
        staticmethod(
            lambda state, *, passed, validation_summary: outcomes.append(passed)
        ),
    )
    monkeypatch.setattr(
        "quanta_agents.agents.validate_agent.write_trace_json",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "quanta_agents.agents.validate_agent.print_agent_progress",
        lambda *args, **kwargs: None,
    )

    result = ValidateAgent().run(state)  # type: ignore[arg-type]

    assert outcomes == [True]
    assert result["validation_summary"]["passed"] is True
    assert result["validation_summary"]["program_validation_checks"][
        "output_weights_passed"
    ] is True


def test_uncalculable_intermediate_characteristic_blocks_validation() -> None:
    validation_result = {
        "intermediate_variable_checks": {
            "factor": {
                "取值范围正确": {"calculable": True, "passed": True},
                "没有未来数据": {"calculable": False, "passed": None},
            }
        }
    }

    result = ValidateAgent._run_intermediate_variable_rules(
        _strategy_output(),
        validation_result,
    )

    assert result["passed"] is False
    assert "factor.没有未来数据:not_calculable" in result["failed_items"]
    assert "factor.没有未来数据:failed_or_unfinished" in result["failed_items"]


def test_missing_or_empty_declared_intermediate_variable_blocks_validation() -> None:
    result = ValidateAgent._run_intermediate_variable_rules(
        _strategy_output(),
        {"intermediate_variable_checks": {"factor": {}}},
    )

    assert result["passed"] is False
    assert "factor.missing_or_empty_result" in result["failed_items"]
    assert "factor.取值范围正确:missing_or_invalid" in result["failed_items"]


def test_all_declared_intermediate_characteristics_must_explicitly_pass() -> None:
    validation_result = {
        "intermediate_variable_checks": {
            "factor": {
                "取值范围正确": {"calculable": True, "passed": True},
                "没有未来数据": {"calculable": True, "passed": True},
            }
        }
    }

    result = ValidateAgent._run_intermediate_variable_rules(
        _strategy_output(),
        validation_result,
    )

    assert result["passed"] is True
    assert result["failed_items"] == []


def test_explicit_chinese_result_keys_are_read_without_losing_the_result() -> None:
    validation_result = {
        "intermediate_variable_checks": {
            "factor": {
                "取值范围正确": {"可计算": True, "是否符合预期": True},
                "没有未来数据": {"可计算": True, "是否符合预期": True},
            }
        }
    }

    result = ValidateAgent._run_intermediate_variable_rules(
        _strategy_output(),
        validation_result,
    )

    assert result["passed"] is True
    assert result["failed_items"] == []


def test_canonical_result_keys_take_precedence_over_chinese_aliases() -> None:
    validation_result = {
        "intermediate_variable_checks": {
            "factor": {
                "取值范围正确": {
                    "calculable": False,
                    "passed": None,
                    "可计算": True,
                    "是否符合预期": True,
                },
                "没有未来数据": {"calculable": True, "passed": True},
            }
        }
    }

    result = ValidateAgent._run_intermediate_variable_rules(
        _strategy_output(),
        validation_result,
    )

    assert result["passed"] is False
    assert "factor.取值范围正确:not_calculable" in result["failed_items"]
    assert "factor.取值范围正确:failed_or_unfinished" in result["failed_items"]


def test_model_top_pass_cannot_hide_failed_analysis_child() -> None:
    summary = _passing_summary()
    summary["intermediate_variable_checks"] = {
        "factor": {"passed": None, "details": "not calculated"},
    }

    result = ValidateAgent._run_analysis_child_rules(_strategy_output(), summary)

    assert result["passed"] is False
    assert "intermediate_variable_checks.factor:failed_or_unfinished" in result["failed_items"]


def test_final_result_requires_program_and_all_analysis_children() -> None:
    validation_result = {
        "intermediate_variable_checks": {
            "factor": {
                "取值范围正确": {"calculable": True, "passed": True},
                "没有未来数据": {"calculable": False, "passed": None},
            }
        },
        "output_weights_check": {"passed": True, "details": "ok"},
    }
    summary = _passing_summary()

    passed = ValidateAgent._enforce_validation_rules(
        _strategy_output(),
        validation_result,
        summary,
    )

    assert passed is False
    assert summary["passed"] is False
    assert summary["program_validation_checks"]["output_weights_passed"] is True
    assert summary["program_validation_checks"]["intermediate_variables"]["passed"] is False


def _event_strategy_result(weights: pd.DataFrame) -> dict[str, object]:
    return {
        "output_weights": weights,
        "strategy_output": {
            "output_weights_df": {
                "datetime_column": "trigger_ts",
            }
        },
        "universe": [
            {
                "symbols": [],
                "asset": "中国股票",
                "type": "dataset_defined",
                "dataset": "periodic_minute_events",
            }
        ],
    }


def test_dataset_defined_event_universe_checks_actual_weight_columns():
    weights = pd.DataFrame(
        {
            "trigger_ts": ["2024-01-02 10:00:00"],
            "sh600000": [0.6],
            "sz000001": [0.3],
            "cash": [0.1],
        }
    )
    original_columns = weights.columns.tolist()

    result = ValidateAgent._run_output_weights_rules(
        _event_strategy_result(weights)
    )

    assert result["passed"] is True
    assert weights.columns.tolist() == original_columns


def test_dataset_defined_event_universe_rejects_numeric_and_string_short_weights():
    for negative_value in (-0.5, "-0.5"):
        weights = pd.DataFrame(
            {
                "trigger_ts": ["2024-01-02 10:00:00"],
                "sh600000": [negative_value],
                "sz000001": [1.0],
                "cash": [0.5],
            }
        )

        result = ValidateAgent._run_output_weights_rules(
            _event_strategy_result(weights)
        )

        assert result["passed"] is False
        assert "cn_stock_non_negative_weights" in result["failed_rules"]


def test_output_weights_rule_still_rejects_truly_missing_universe():
    weights = pd.DataFrame(
        {
            "trigger_ts": ["2024-01-02 10:00:00"],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )

    result = OutputWeightsRuleChecker.run(
        weights,
        {"output_weights_df": {"datetime_column": "trigger_ts"}},
        [],
    )

    assert result["passed"] is False
    assert "universe_available_for_market_constraint" in result["failed_rules"]


def test_event_strategy_policy_failure_stops_validation_immediately(monkeypatch) -> None:
    weights = pd.DataFrame(
        {
            "trigger_ts": ["2022-01-04 10:00:00"],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )
    strategy_result = _event_strategy_result(weights)
    state = {
        "strategy_code": "import os\nblocked = os.environ.get('SECRET')",
        "strategy_result": strategy_result,
        "experiment_spec": {
            "backtest_mode": "event_parquet",
            "train_start": "2020-01-01",
            "train_end": "2020-12-31",
            "validate_start": "2021-01-01",
            "validate_end": "2021-12-31",
            "backtest_start": "2022-01-01",
            "backtest_end": "2022-12-31",
        },
        "epoch_index": 1,
        "strategy_validate_round": 1,
        "max_epochs": 1,
        "history": [],
    }

    def must_not_run(*args, **kwargs):
        raise AssertionError("事件策略代码检查失败后不应继续调用模型验证")

    outcomes: list[bool] = []
    monkeypatch.setattr(ValidateAgent, "_run_script_validation_loop", must_not_run)
    monkeypatch.setattr(ValidateAgent, "_run_analysis_loop", must_not_run)
    monkeypatch.setattr(
        ValidateAgent,
        "_apply_validation_outcome",
        staticmethod(
            lambda state, *, passed, validation_summary: outcomes.append(passed)
        ),
    )
    monkeypatch.setattr(
        "quanta_agents.agents.validate_agent.write_trace_json",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "quanta_agents.agents.validate_agent.print_agent_progress",
        lambda *args, **kwargs: None,
    )

    result = ValidateAgent().run(state)  # type: ignore[arg-type]

    assert outcomes == [False]
    assert result["validation_summary"]["passed"] is False
    assert (
        result["validation_result"]["strategy_code_policy_check"]["passed"]
        is False
    )


@pytest.mark.parametrize(
    "code",
    [
        "with open('secret.txt') as handle:\n    value = handle.read()",
        "import shutil\nshutil.copy('a', 'b')",
        "import os\nvalue = os.environ.get('SECRET')",
        "import subprocess\nsubprocess.run(['whoami'])",
        "import requests\nrequests.get('https://example.com')",
        "value = load_factor()",
        "save_result({})",
        "value = validate_data_bundle['events'].replace(0, 1)",
        "value = validate_data_bundle['events'].rename(columns={})",
    ],
    ids=[
        "file",
        "file-copy",
        "environment",
        "process",
        "network",
        "load-prefix",
        "save-prefix",
        "replace-method",
        "rename-method",
    ],
)
def test_model_generated_validation_code_is_blocked_before_execution(
    monkeypatch,
    code: str,
) -> None:
    executed = False

    def unexpected_execute(*args, **kwargs):
        nonlocal executed
        executed = True
        raise AssertionError("不安全的验证代码不应执行")

    monkeypatch.setattr(
        ValidateAgent,
        "_execute_code",
        staticmethod(unexpected_execute),
    )

    output, success = ValidateAgent._execute_model_check_code(code, {})

    assert success is False
    assert "验证代码安全检查失败" in output
    assert executed is False


def test_safe_model_generated_validation_code_still_executes() -> None:
    namespace: dict[str, object] = {}
    code = "validation_result = {'intermediate_variable_checks': {}}"

    _, success = ValidateAgent._execute_model_check_code(code, namespace)

    assert success is True
    assert namespace["validation_result"] == {"intermediate_variable_checks": {}}


def test_validation_code_allows_dataframe_copy() -> None:
    code = 'copied = validate_data_bundle["events"].copy()'

    ValidateAgent._validate_model_check_code(code)


def test_model_generated_validation_code_can_use_result_fields_for_evaluation() -> None:
    code = """
validation_result = {
    "intermediate_variable_checks": {
        "joint_minute_hit": validate_data_bundle["events"]["joint_minute_hit"].mean()
    }
}
"""

    ValidateAgent._validate_model_check_code(code)


def test_wide_sparse_weights_are_checked_without_dataframe_apply(monkeypatch) -> None:
    row_count = 120
    data: dict[str, object] = {
        "trigger_ts": pd.date_range("2024-01-02 10:00:00", periods=row_count, freq="min"),
    }
    for position in range(row_count):
        values = [0.0] * row_count
        values[position] = 1.0
        data[f"sh{600000 + position:06d}"] = pd.arrays.SparseArray(
            values,
            fill_value=0.0,
        )
    data["cash"] = [0.0] * row_count
    weights = pd.DataFrame(data)

    def fail_apply(*args, **kwargs):
        raise AssertionError("稀疏宽表不应调用 DataFrame.apply")

    monkeypatch.setattr(pd.DataFrame, "apply", fail_apply)
    result = OutputWeightsRuleChecker.run(
        weights,
        {"output_weights_df": {"datetime_column": "trigger_ts"}},
        [
            {
                "asset": "中国股票",
                "type": "dataset_defined",
                "dataset": "periodic_minute_events",
                "symbols": [],
            }
        ],
    )

    assert result["passed"] is True
