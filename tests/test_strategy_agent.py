import pandas as pd
from unittest.mock import patch

from quanta_agents.agents.strategy_agent import StrategyAgent
from quanta_agents.period_data import filter_membership_for_period
from quanta_agents.prompt_loader import load_agent_prompt


def test_build_strategy_generation_meta_includes_validate_period():
    strategy_context = {
        "hypothesis": "test hypothesis",
        "required_data": [],
        "backtest_datasets": [],
        "train_start": "2024-01-01",
        "train_end": "2024-06-30",
        "validate_start": "2024-07-01",
        "validate_end": "2024-12-31",
        "calculation_contracts": [{"contract_id": "market_return"}],
    }
    strategy_result = {
        "train_period": {"start": "2024-01-01", "end": "2024-06-30"},
        "validate_period": {"start": "2024-07-01", "end": "2024-12-31"},
    }

    meta = StrategyAgent._build_strategy_generation_meta(strategy_context, strategy_result)

    assert meta["train_period"] == strategy_result["train_period"]
    assert meta["validate_period"] == strategy_result["validate_period"]
    assert meta["calculation_contracts"] == [{"contract_id": "market_return"}]


def test_previous_strategy_code_and_source_are_loaded_from_state():
    state = {
        "strategy_code": "def old_signal():\n    return 1",
        "code_text": "def fallback():\n    return 0",
    }

    code, source = StrategyAgent._extract_previous_strategy_code(state)  # type: ignore[arg-type]

    assert code == "def old_signal():\n    return 1"
    assert "strategy_code" in source


def test_strategy_prompt_contains_previous_code_source_and_diff():
    system_prompt = load_agent_prompt("strategy_agent", "system_prompt")
    prompt = load_agent_prompt(
        "strategy_agent",
        "user_prompt_template",
        hypothesis="测试假设",
        strategy_modification="只修改阈值",
        required_data_descriptions="daily_prices",
        calculation_contracts_json='[{"required_dates": ["t", "t-30"]}]',
        validation_summary_json='{"passed": false}',
        previous_strategy_code="def old_signal():\n    return 1",
        previous_strategy_source="WorkflowState.strategy_code",
        previous_code_diff="- return 0\n+ return 1",
        code_change_summary="只修改阈值，保留其他实现",
        position_plan_contract_json=(
            '{"mode": "fixed_target_until_exit", "single_stock_weight": 0.1}'
        ),
    )

    assert "WorkflowState.strategy_code" in prompt
    assert "def old_signal()" in prompt
    assert "- return 0" in prompt
    assert "只修改阈值，保留其他实现" in prompt
    assert '"t-30"' in prompt
    assert "fixed_target_until_exit" in prompt
    assert "目标比例为0时不能保存该计划" in system_prompt
    assert 'strategy_next_phase = "validate"' in prompt


def test_strategy_agent_rewrites_slow_contract_code_before_execution():
    slow_code = '''
def calculation_contract_sample(
    daily_frame, market_dates, decision_date, contract, symbol_column, datetime_column
):
    return []

def output_weights():
    for decision_date in signal_dates:
        calculation_contract_sample(
            history,
            market_dates,
            decision_date,
            MARKET_RETURN_CONTRACT,
            "code",
            "trade_date",
        )
    return None

output_weights_df = output_weights()
strategy_output = {}
strategy_next_phase = "validate"
strategy_decision_reason = "待验证"
'''.strip()
    rewritten_code = '''
def output_weights():
    return None

output_weights_df = output_weights()
strategy_output = {
    "output_weights_df": {
        "description": "测试权重",
        "function_name": "output_weights",
        "datetime_column": "trade_date",
    }
}
strategy_next_phase = "validate"
strategy_decision_reason = "已按提示重写"
'''.strip()
    responses = [
        f"```python\n{slow_code}\n```",
        f"```python\n{rewritten_code}\n```",
    ]
    request_last_messages: list[str] = []
    executed_codes: list[str] = []

    def fake_complete_messages(messages, **kwargs):
        request_last_messages.append(str(messages[-1]["content"]))
        return responses[len(request_last_messages) - 1]

    def fake_execute(code, namespace):
        assert "calculation_contract_sample(\n            history," not in code
        executed_codes.append(code)
        namespace.update(
            {
                "output_weights_df": pd.DataFrame(
                    {"trade_date": pd.Series(dtype="datetime64[ns]"), "cash": []}
                ),
                "strategy_output": {
                    "output_weights_df": {
                        "description": "测试权重",
                        "function_name": "output_weights",
                        "datetime_column": "trade_date",
                    }
                },
                "strategy_next_phase": "validate",
                "strategy_decision_reason": "已按提示重写",
            }
        )
        return "ok", True

    strategy_context = {
        "hypothesis": "测试市场统计",
        "strategy_modification": "",
        "required_data": [],
        "required_data_descriptions": "",
        "train_data_bundle": {},
        "validate_data_bundle": {},
        "calculation_contracts": [],
        "research_category": "condition_necessity",
        "mechanism_id": "",
        "variant_mode": "",
        "new_signal_definition": {},
        "candidate_mode": "baseline",
        "experiment_spec": {},
        "universe": [],
        "backtest_datasets": [],
        "train_start": "2020-01-01",
        "train_end": "2020-06-30",
        "validate_start": "2020-07-01",
        "validate_end": "2020-12-31",
    }
    state = {"epoch_index": 1, "history": []}
    agent = StrategyAgent()
    agent.max_retries = 2

    with (
        patch.object(StrategyAgent, "_build_strategy_context", return_value=strategy_context),
        patch.object(StrategyAgent, "_build_sandbox_namespace", return_value={}),
        patch.object(StrategyAgent, "_write_code_trace"),
        patch.object(StrategyAgent, "_execute_code", side_effect=fake_execute),
        patch.object(StrategyAgent, "_validate_output", return_value=(True, "ok")),
        patch("quanta_agents.agents.strategy_agent.load_agent_prompt", return_value="prompt"),
        patch(
            "quanta_agents.agents.strategy_agent.llm_client.complete_messages",
            side_effect=fake_complete_messages,
        ),
        patch("quanta_agents.agents.strategy_agent.validate_generated_strategy_code"),
        patch("quanta_agents.agents.strategy_agent.print_agent_progress"),
        patch("quanta_agents.agents.strategy_agent.write_trace_json"),
        patch("quanta_agents.agents.strategy_agent.write_trace_text"),
    ):
        result = agent.run(state)  # type: ignore[arg-type]

    assert len(request_last_messages) == 2
    assert "循环外先把日线" in request_last_messages[1]
    assert executed_codes == [rewritten_code]
    assert result["strategy_code"] == rewritten_code


def test_strategy_agent_never_routes_generated_code_directly_to_test():
    phase, reason = StrategyAgent._resolve_next_phase(
        {
            "strategy_next_phase": "test",
            "strategy_decision_reason": "代码看起来可用",
        },
        has_validation_summary=True,
    )

    assert phase == "validate"
    assert "必须重新完成统计验证" in reason


def test_code_diff_records_only_actual_changes():
    diff = StrategyAgent._build_code_diff(
        "def signal():\n    return 1",
        "def signal():\n    return 2",
    )

    assert "--- previous_strategy.py" in diff
    assert "+++ generated_strategy.py" in diff
    assert "-    return 1" in diff
    assert "+    return 2" in diff


def test_code_change_ratio_detects_lazy_and_large_rewrites():
    previous = "\n".join(["def signal():", "    value = 1", "    return value"])
    unchanged_ratio = StrategyAgent._code_change_ratio(previous, previous)
    local_ratio = StrategyAgent._code_change_ratio(
        previous,
        "\n".join(["def signal():", "    value = 2", "    return value"]),
    )
    rewrite_ratio = StrategyAgent._code_change_ratio(
        previous,
        "\n".join(["class NewStrategy:", "    pass", "result = NewStrategy()"]),
    )

    assert unchanged_ratio == 0.0
    assert 0.0 < local_ratio < rewrite_ratio


def test_membership_period_filter_removes_future_rows_and_hides_future_exit_dates():
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ"],
            "start_date": ["2023-01-01", "2024-07-15", "2025-01-01", "2022-01-01"],
            "end_date": ["2026-12-31", None, "2025-12-31", "2023-12-31"],
            "source": ["a", "b", "c", "d"],
        }
    )

    scoped = filter_membership_for_period(
        membership,
        "2024-07-01",
        "2024-12-31",
    )

    assert scoped["code"].tolist() == ["000001.SZ", "000002.SZ"]
    assert scoped["end_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-12-31",
        "2024-12-31",
    ]
    assert scoped["source"].tolist() == ["a", "b"]
    assert membership.loc[0, "end_date"] == "2026-12-31"


def test_strategy_agent_scopes_membership_separately_for_train_and_validation():
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ"],
            "start_date": ["2023-01-01", "2024-07-15", "2025-01-01", "2022-01-01"],
            "end_date": ["2026-12-31", "2026-12-31", "2025-12-31", "2023-12-31"],
        }
    )
    required_data = [
        {
            "table_key": "csi300_membership",
            "type": "static",
            "fields": ["code", "start_date", "end_date"],
        }
    ]

    def fake_load(items):
        return [{**item, "data": membership.copy(deep=True)} for item in items]

    with patch(
        "quanta_agents.agents.strategy_agent.load_required_data",
        side_effect=fake_load,
    ):
        train_bundle, validate_bundle = StrategyAgent._load_required_inputs(
            required_data,
            "2024-01-01",
            "2024-06-30",
            "2024-07-01",
            "2024-12-31",
        )

    train_membership = train_bundle["csi300_membership"]
    validate_membership = validate_bundle["csi300_membership"]
    assert train_membership["code"].tolist() == ["000001.SZ"]
    assert train_membership["end_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-06-30"
    ]
    assert validate_membership["code"].tolist() == ["000001.SZ", "000002.SZ"]
    assert validate_membership["end_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-12-31",
        "2024-12-31",
    ]


def test_dataset_defined_universe_is_preserved_without_expanding_symbols():
    result = StrategyAgent._normalize_universe_entries(
        {
            "universe": [
                {
                    "symbols": [],
                    "asset": "中国股票",
                    "type": "dataset_defined",
                    "dataset": "periodic_minute_events",
                    "description": "股票由事件数据决定",
                }
            ]
        },
        None,
    )

    assert result == [
        {
            "symbols": [],
            "asset": "中国股票",
            "type": "dataset_defined",
            "dataset": "periodic_minute_events",
            "description": "股票由事件数据决定",
        }
    ]


def test_named_pool_type_and_value_are_preserved_without_static_symbols():
    with patch(
        "quanta_agents.agents.strategy_agent.get_universe_list",
        return_value=[],
    ):
        for pool_name in ("csiall", "csi1000"):
            result = StrategyAgent._normalize_universe_entries(
                {
                    "universe": [
                        {
                            "symbols": [],
                            "asset": "中国股票",
                            "type": "named_pool",
                            "value": pool_name,
                        }
                    ]
                },
                None,
            )

            assert result == [
                {
                    "symbols": [],
                    "asset": "中国股票",
                    "type": "named_pool",
                    "named_pool": pool_name,
                }
            ]


def test_legacy_named_pool_field_is_preserved():
    with patch(
        "quanta_agents.agents.strategy_agent.get_universe_list",
        return_value=["000001.SZ"],
    ):
        result = StrategyAgent._normalize_universe_entries(
            {
                "universe": [
                    {
                        "symbols": [],
                        "asset": "中国股票",
                        "named_pool": "csi1000",
                    }
                ]
            },
            None,
        )

    assert result == [
        {
            "symbols": ["000001.SZ"],
            "asset": "中国股票",
            "type": "named_pool",
            "named_pool": "csi1000",
        }
    ]


def test_universe_without_symbols_named_pool_or_dataset_is_still_empty():
    result = StrategyAgent._normalize_universe_entries(
        {"universe": [{"symbols": [], "asset": "中国股票"}]},
        None,
    )

    assert result == []


def _event_namespace(weights: pd.DataFrame, datetime_column: str) -> dict[str, object]:
    return {
        "pd": pd,
        "strategy_context": {
            "hypothesis": "测试分钟事件策略",
            "strategy_modification": "",
            "experiment_spec": {
                "backtest_mode": "event_parquet",
                "event_horizon_minutes": 5,
            },
        },
        "params": {"event_horizon_minutes": 5},
        "output_weights": lambda: weights,
        "output_weights_df": weights,
        "strategy_output": {
            "output_weights_df": {
                "description": "测试事件权重",
                "function_name": "output_weights",
                "datetime_column": datetime_column,
            }
        },
        "strategy_next_phase": "validate",
        "strategy_decision_reason": "测试",
    }


def test_event_output_requires_trigger_ts_and_long_only_weights():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    invalid_time = pd.DataFrame(
        {"date": ["2025-01-02"], "sh600000": [1.0], "cash": [0.0]}
    )
    valid, message = StrategyAgent._validate_output(
        code,
        _event_namespace(invalid_time, "date"),
    )
    assert not valid
    assert "trigger_ts" in message

    short_weights = pd.DataFrame(
        {
            "trigger_ts": ["2025-01-02 10:00:00"],
            "sh600000": [-0.5],
            "cash": [1.5],
        }
    )
    valid, message = StrategyAgent._validate_output(
        code,
        _event_namespace(short_weights, "trigger_ts"),
    )
    assert not valid
    assert "cash" in message

    negative_weight = pd.DataFrame(
        {
            "trigger_ts": ["2025-01-02 10:00:00"],
            "sh600000": [-0.5],
            "sz000001": [1.0],
            "cash": [0.5],
        }
    )
    valid, message = StrategyAgent._validate_output(
        code,
        _event_namespace(negative_weight, "trigger_ts"),
    )
    assert not valid
    assert "negative" in message


def test_event_output_accepts_minute_time_and_nonnegative_weights():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {
            "trigger_ts": ["2025-01-02 10:00:00"],
            "sh600000": [0.6],
            "sz000001": [0.3],
            "cash": [0.1],
        }
    )

    valid, message = StrategyAgent._validate_output(
        code,
        _event_namespace(weights, "trigger_ts"),
    )

    assert valid, message


def test_event_output_requires_explicit_event_horizon_param():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {"trigger_ts": ["2025-01-02 10:00:00"], "sh600000": [1.0], "cash": [0.0]}
    )
    namespace = _event_namespace(weights, "trigger_ts")
    namespace["params"] = {}

    valid, message = StrategyAgent._validate_output(code, namespace)

    assert not valid
    assert "params" in message
    assert "event_horizon_minutes" in message


def test_event_output_rejects_horizon_change_without_explicit_research_approval():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {"trigger_ts": ["2025-01-02 10:00:00"], "sh600000": [1.0], "cash": [0.0]}
    )
    namespace = _event_namespace(weights, "trigger_ts")
    namespace["params"] = {"event_horizon_minutes": 10}
    namespace["strategy_context"]["strategy_modification"] = (
        "比较把持有时间从5分钟改为10分钟和改为20分钟的结果，暂不批准修改。"
    )

    valid, message = StrategyAgent._validate_output(code, namespace)

    assert not valid
    assert "experiment_spec" in message


def test_event_output_accepts_horizon_change_explicitly_approved_by_research():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {"trigger_ts": ["2025-01-02 10:00:00"], "sh600000": [1.0], "cash": [0.0]}
    )
    namespace = _event_namespace(weights, "trigger_ts")
    namespace["params"] = {"event_horizon_minutes": 10}
    namespace["strategy_context"]["strategy_modification"] = (
        "保持D6筛选不变，只把评价和持有时间从5分钟改为10分钟。"
    )
    namespace["strategy_context"]["hypothesis"] = "使用trigger后第10分钟收盘评价。"

    valid, message = StrategyAgent._validate_output(code, namespace)

    assert valid, message


def test_event_output_accepts_trigger_minute_horizon_definition():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {"trigger_ts": ["2025-01-02 10:00:00"], "sh600000": [1.0], "cash": [0.0]}
    )
    namespace = _event_namespace(weights, "trigger_ts")
    namespace["params"] = {"event_horizon_minutes": 10}
    namespace["strategy_context"]["strategy_modification"] = (
        "评价时间改为trigger后第10分钟收盘。"
    )

    valid, message = StrategyAgent._validate_output(code, namespace)

    assert valid, message


def test_event_output_accepts_explicit_event_horizon_assignment():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {"trigger_ts": ["2025-01-02 10:00:00"], "sh600000": [1.0], "cash": [0.0]}
    )
    namespace = _event_namespace(weights, "trigger_ts")
    namespace["params"] = {"event_horizon_minutes": 10}
    namespace["strategy_context"]["strategy_modification"] = (
        "本轮唯一变化：event_horizon_minutes=10。"
    )

    valid, message = StrategyAgent._validate_output(code, namespace)

    assert valid, message


def test_event_output_does_not_treat_rejected_horizon_change_as_approval():
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"
    weights = pd.DataFrame(
        {"trigger_ts": ["2025-01-02 10:00:00"], "sh600000": [1.0], "cash": [0.0]}
    )
    namespace = _event_namespace(weights, "trigger_ts")
    namespace["params"] = {"event_horizon_minutes": 10}
    namespace["strategy_context"]["strategy_modification"] = (
        "把评价和持有时间从5分钟改为10分钟的方案被否决。"
    )

    valid, message = StrategyAgent._validate_output(code, namespace)

    assert not valid
    assert "experiment_spec" in message


def test_event_output_checks_wide_sparse_weights_without_dataframe_sum(monkeypatch):
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
    code = "def output_weights():\n    return weights\noutput_weights_df = output_weights()"

    def fail_sum(*args, **kwargs):
        raise AssertionError("稀疏宽表不应调用 DataFrame.sum")

    monkeypatch.setattr(pd.DataFrame, "sum", fail_sum)
    valid, message = StrategyAgent._validate_output(
        code,
        _event_namespace(weights, "trigger_ts"),
    )

    assert valid, message


def test_periodic_required_data_removes_result_fields_before_loading() -> None:
    prepared = StrategyAgent._prepare_required_data(
        [
            {
                "table_key": "periodic_minute_events",
                "type": "auxiliary",
                "fields": [
                    "candidate_id",
                    "return_stability",
                    "trigger_low_to_prev5_close_ma5_distance",
                    "analysis_only_full_day_low_to_close_ma5_distance",
                    "forward_5m",
                    "joint_minute_hit",
                    "next_spike_position",
                ],
                "time_range": "2022-01-01 to 2025-12-31",
            }
        ],
        "2022-01-01",
        "2023-12-31",
    )

    assert prepared[0]["fields"] == [
        "candidate_id",
        "return_stability",
        "trigger_low_to_prev5_close_ma5_distance",
    ]
    assert prepared[0]["time_range"] == {
        "start": "2022-01-01",
        "end": "2023-12-31",
    }
