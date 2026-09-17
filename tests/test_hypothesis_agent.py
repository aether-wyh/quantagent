from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "openai" not in sys.modules:
    openai_stub = ModuleType("openai")

    class _DummyOpenAI:  # pragma: no cover - test bootstrap stub
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda *a, **k: None))

    setattr(openai_stub, "OpenAI", _DummyOpenAI)
    sys.modules["openai"] = openai_stub

import quanta_agents.agents.hypothesis_agent as hypothesis_agent_module
from quanta_agents.agents.hypothesis_agent import HypothesisAgent
from quanta_agents.exceptions import AgentExecutionError
from quanta_agents.prompt_loader import load_agent_prompt
from quanta_agents.state import BacktestResult, init_state


class HypothesisAgentSchemaTest(TestCase):
    def test_research_optimizer_prompt_keeps_original_research_plan(self) -> None:
        marker = "先试HF0280，再试HF0078"
        prompt = load_agent_prompt(
            "research_optimizer_agent",
            "user_prompt",
            user_idea=marker,
            current_hypothesis="上一轮策略",
            current_required_data_json="[]",
            current_backtest_datasets_json="[]",
            previous_research_json="{}",
            backtest_feedback="上一轮夏普低于目标",
            development_report_json="{}",
            candidate_history_json="[]",
        )

        self.assertIn(marker, prompt)
        self.assertIn("全部开发期候选历史", prompt)
        self.assertIn("最终测试时期", prompt)

    def test_candidate_mode_is_evidence_driven_after_baseline(self) -> None:
        self.assertEqual(HypothesisAgent._candidate_mode(1)[0], "baseline")
        self.assertEqual(HypothesisAgent._candidate_mode(2)[0], "evidence_driven")
        self.assertEqual(HypothesisAgent._candidate_mode(3)[0], "evidence_driven")
        self.assertIn("不得按轮数", HypothesisAgent._candidate_mode(4)[1])

    def test_formal_development_candidate_count_requires_period_kind(self) -> None:
        state = {
            "candidate_records": [
                {"candidate_id": "candidate_001", "period_kind": "development"},
                {"candidate_id": "candidate_without_period"},
                {"candidate_id": "candidate_final", "period_kind": "final_test"},
            ]
        }

        count = HypothesisAgent._formal_development_candidate_count(state)  # type: ignore[arg-type]

        self.assertEqual(count, 1)

    def test_development_report_for_prompt_removes_artifact_paths(self) -> None:
        state = {
            "development_report": {
                "median_sharpe": 0.8,
                "failure_reasons": ["delay failed"],
                "recompute_records": [{"large": "payload"}],
                "folds": [
                    {
                        "name": "development_fold_01",
                        "sharpe": 0.7,
                        "artifacts": {"daily": "large.csv"},
                    }
                ],
            }
        }

        report = HypothesisAgent._development_report_for_prompt(state)  # type: ignore[arg-type]

        self.assertEqual(report["median_sharpe"], 0.8)
        self.assertNotIn("recompute_records", report)
        self.assertNotIn("artifacts", report["folds"][0])

    def test_development_report_for_prompt_rejects_non_development_report(
        self,
    ) -> None:
        state = {
            "development_report": {
                "period_kind": "final_test",
                "median_sharpe": 9.9,
                "summary": "FINAL_REPORT_SECRET",
            }
        }

        report = HypothesisAgent._development_report_for_prompt(state)  # type: ignore[arg-type]

        self.assertEqual(report, {})

    def test_event_development_report_keeps_research_evidence(self) -> None:
        state = {
            "development_report": {
                "report_kind": "event_parquet",
                "period_kind": "development",
                "event_horizon_minutes": 10,
                "event_horizon_source": "strategy_result.params",
                "event_return_columns": ["forward_10m"],
                "event_success_metric": "gross_up_rate",
                "event_success_metric_value": 0.4857,
                "development_period": {"start": "2024-01-01", "end": "2024-12-31"},
                "flow_counts": {
                    "raw_event_count": 593564,
                    "final_event_count": 337076,
                },
                "overall": {
                    "event_gross_mean_return": 0.000133,
                    "event_net_mean_return": -0.001467,
                    "event_gross_up_rate": 0.4131,
                    "event_joint_minute_hit_rate": 0.2674,
                    "event_success_metric": "gross_up_rate",
                    "event_success_metric_value": 0.4857,
                },
                "by_year": [{"period": "2024", "event_count": 337076}],
                "by_month": [{"period": "2024-01", "event_count": 28000}],
                "cost_scenarios": [
                    {"cost_multiplier": 0, "net_mean_return": 0.000133},
                    {"cost_multiplier": 1, "net_mean_return": -0.001467},
                ],
                "backtest_debug": {"holding_minutes": 5},
                "artifacts": {"trades": "large.csv"},
                "folds": [
                    {
                        "name": "development",
                        "event_horizon_minutes": 10,
                        "event_horizon_source": "strategy_result.params",
                        "event_return_columns": ["forward_10m"],
                        "event_joint_minute_hit_rate": 0.2674,
                        "event_success_metric": "gross_up_rate",
                        "event_success_metric_value": 0.4857,
                    }
                ],
            }
        }

        report = HypothesisAgent._development_report_for_prompt(state)  # type: ignore[arg-type]

        self.assertEqual(report["report_kind"], "event_parquet")
        self.assertEqual(report["event_horizon_minutes"], 10)
        self.assertEqual(report["event_horizon_source"], "strategy_result.params")
        self.assertEqual(report["event_return_columns"], ["forward_10m"])
        self.assertEqual(report["event_success_metric"], "gross_up_rate")
        self.assertEqual(report["event_success_metric_value"], 0.4857)
        self.assertEqual(report["folds"][0]["event_horizon_minutes"], 10)
        self.assertEqual(report["flow_counts"]["final_event_count"], 337076)
        self.assertEqual(report["overall"]["event_gross_up_rate"], 0.4131)
        self.assertEqual(
            report["overall"]["event_joint_minute_hit_rate"], 0.2674
        )
        self.assertEqual(report["by_year"][0]["period"], "2024")
        self.assertNotIn("artifacts", report)
        evidence = HypothesisAgent._candidate_development_report_for_prompt(state)  # type: ignore[arg-type]
        self.assertEqual(evidence["event_horizon_minutes"], 10)
        self.assertEqual(evidence["event_horizon_source"], "strategy_result.params")
        self.assertEqual(evidence["event_return_columns"], ["forward_10m"])
        self.assertEqual(evidence["event_success_metric"], "gross_up_rate")
        self.assertEqual(evidence["event_success_metric_value"], 0.4857)

    def test_merge_hypothesis_with_modification_builds_complete_logic(self) -> None:
        merged = HypothesisAgent._merge_hypothesis_with_modification(
            "均值回归策略，使用布林带上下轨进出场。",
            "加入波动率过滤，波动率过高时不入场。",
        )

        self.assertIn("均值回归策略", merged)
        self.assertIn("策略修正整合", merged)
        self.assertIn("波动率过滤", merged)

    def test_format_backtest_result_summary_contains_metrics(self) -> None:
        state = {
            "test_result": BacktestResult(
                annual_return=0.12,
                sharpe=1.55,
                max_drawdown=-12000.0,
                passed=True,
                summary="回测表现稳定",
                max_ddpercent=0.08,
            )
        }

        summary = HypothesisAgent._format_backtest_result_summary(state)  # type: ignore[arg-type]

        self.assertIn("回测表现稳定", summary)
        self.assertIn("annual_return=12.00%", summary)
        self.assertIn("sharpe=1.55", summary)
        self.assertIn("max_drawdown_amount=-12000.00", summary)
        self.assertIn("max_ddpercent=8.00%", summary)
        self.assertIn("passed=True", summary)

    def test_extract_dataset_metadata_keeps_only_selected_fields(self) -> None:
        dataset_metadata_yaml = """
datasets:
  - table_key: stock_kline_daily_qfq
    description: 股票日K线数据集（前复权）
    type: time_series
    source:
      engine: dolphindb
      database: ohlcv_daily
      table: stock_kline_daily_qfq
    granularity: 1d
    symbol_column: code
    datetime_column: trade_date
    fields:
      - name: open
        meaning: 开盘价
      - name: close
        meaning: 收盘价
  - table_key: basic_stock_info
    description: 股票基本信息数据集
    type: static
    granularity: none
    fields:
      - name: code
        meaning: 股票代码
"""

        extracted = HypothesisAgent._extract_dataset_metadata(dataset_metadata_yaml)

        self.assertIn("table_key: stock_kline_daily_qfq", extracted)
        self.assertIn("description: 股票日K线数据集（前复权）", extracted)
        self.assertIn("type: time_series", extracted)
        self.assertIn("granularity: 1d", extracted)
        self.assertIn("- name: open", extracted)
        self.assertIn("meaning: 开盘价", extracted)
        self.assertIn("- name: close", extracted)
        self.assertIn("meaning: 收盘价", extracted)
        self.assertIn("table_key: basic_stock_info", extracted)
        self.assertIn("fields:", extracted)
        self.assertNotIn("source:", extracted)
        self.assertNotIn("symbol_column:", extracted)

    def test_build_dataset_tools_exposes_available_backtest_datasets(self) -> None:
        tools, handlers = HypothesisAgent._build_dataset_tools([])

        tool_names = [str(tool.get("function", {}).get("name", "")) for tool in tools]
        self.assertIn("get_available_backtest_datasets", tool_names)
        self.assertIn("get_available_backtest_datasets", handlers)

        result = handlers["get_available_backtest_datasets"]()

        self.assertIsInstance(result, dict)
        self.assertIn("count", result)
        self.assertIn("datasets", result)
        self.assertGreaterEqual(int(result["count"]), 1)
        self.assertIsInstance(result["datasets"], list)

        datasets_by_key = {
            str(item.get("table_key")): item for item in result["datasets"]
        }
        daily_dataset = datasets_by_key["vnpy_stock_daily_qfq"]
        self.assertIn("description", daily_dataset)
        self.assertEqual(daily_dataset["interval"], "1d")
        self.assertIn("periodic_level2_events", datasets_by_key)

    def test_parse_output_rejects_backtest_dataset_not_in_backtest_catalog(self) -> None:
        payload = {
            "hypothesis": "策略逻辑",
            "required_data": [
                {
                    "table_key": "stock_kline_daily_qfq",
                    "type": "time_series",
                    "fields": ["close"],
                    "universe": {
                        "type": "named_pool",
                        "value": "沪深300",
                    },
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "purpose": "价格数据",
                }
            ],
            "backtest_datasets": ["not_a_backtest_dataset"],
        }

        with self.assertRaisesRegex(ValueError, "backtest_datasets"):
            HypothesisAgent._parse_output(json.dumps(payload))

    def test_parse_output_accepts_ok_payload(self) -> None:
        payload = {
            "hypothesis": "基于布林带均值回归策略，使用股票日K线数据计算布林带。布林带由中轨（N日移动平均线）和上下轨（中轨 ± K倍标准差）构成。当收盘价触及或突破上轨时，产生卖出信号；当收盘价触及或突破下轨时，产生买入信号。持仓周期为1个交易日，次日开盘执行反向操作平仓。参数N和K通过训练期数据优化，验证期和回测期使用固定参数。",
            "required_data": [
                {
                    "table_key": "stock_kline_daily_qfq",
                    "type": "time_series",
                    "fields": ["open", "close"],
                    "universe": {
                        "type": "named_pool",
                        "value": "沪深300",
                    },
                    "time_range": {
                        "start": "2020-01-01",
                        "end": "2025-12-31",
                    },
                    "purpose": "计算布林带中轨（移动平均）和上下轨（标准差倍数），并生成买卖信号",
                }
            ],
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "missing_concepts": [
                {
                    "concept": "布林带中轨（移动平均线）",
                    "purpose": "作为价格中枢，计算上下轨的基准",
                },
                {
                    "concept": "布林带上下轨（中轨 ± K倍标准差）",
                    "purpose": "作为价格极端区域的阈值，触发买卖信号",
                },
            ],
            "strategy_modification": "由于数据集中没有直接提供布林带指标，策略将基于stock_kline_daily_qfq的close字段计算N日移动平均线和标准差，进而构建布林带。参数N和K通过训练期数据优化，验证期和回测期使用固定参数。",
        }

        parsed = HypothesisAgent._parse_output(json.dumps(payload, ensure_ascii=False))

        self.assertEqual(parsed["hypothesis"], payload["hypothesis"])
        self.assertIn("required_data", parsed)
        self.assertEqual(parsed["required_data"][0]["table_key"], "stock_kline_daily_qfq")
        self.assertEqual(parsed["required_data"][0]["universe"]["type"], "named_pool")
        self.assertEqual(parsed["required_data"][0]["universe"]["value"], "沪深300")
        self.assertEqual(
            parsed["required_data"][0]["time_range"],
            {"start": "2020-01-01", "end": "2025-12-31"},
        )
        self.assertEqual(parsed["missing_concepts"][0]["concept"], "布林带中轨（移动平均线）")

    def test_parse_output_accepts_symbol_list_universe(self) -> None:
        payload = {
            "hypothesis": "双标的配对交易",
            "required_data": [
                {
                    "table_key": "stock_kline_daily_qfq",
                    "type": "time_series",
                    "fields": ["close"],
                    "universe": {
                        "type": "symbol_list",
                        "value": ["000001.SZ", "600000.SH"],
                    },
                    "time_range": {
                        "start": "2020-01-01",
                        "end": "2025-12-31",
                    },
                    "purpose": "配对交易信号计算",
                }
            ],
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "missing_concepts": [],
            "strategy_modification": "以指定股票列表作为交易范围。",
        }

        parsed = HypothesisAgent._parse_output(json.dumps(payload, ensure_ascii=False))

        universe = parsed["required_data"][0]["universe"]
        self.assertEqual(universe["type"], "symbol_list")
        self.assertEqual(universe["value"], ["000001.SZ", "600000.SH"])

    def test_parse_output_allows_panel_without_fields(self) -> None:
        payload = {
            "hypothesis": "使用横截面因子进行打分选股",
            "required_data": [
                {
                    "table_key": "momentum_factor_data",
                    "type": "panel",
                    "universe": {
                        "type": "named_pool",
                        "value": "hs300",
                    },
                    "time_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31",
                    },
                    "purpose": "读取全量横截面因子面板数据用于排序",
                }
            ],
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "missing_concepts": [],
            "strategy_modification": "面板数据按时间窗口直接读取。",
        }

        parsed = HypothesisAgent._parse_output(json.dumps(payload, ensure_ascii=False))

        self.assertEqual(parsed["required_data"][0]["type"], "panel")
        self.assertEqual(parsed["required_data"][0]["fields"], [])
        self.assertEqual(parsed["required_data"][0]["universe"]["value"], "hs300")

    def test_parse_output_rejects_panel_without_universe(self) -> None:
        payload = {
            "hypothesis": "使用横截面因子进行打分选股",
            "required_data": [
                {
                    "table_key": "momentum_factor_data",
                    "type": "panel",
                    "time_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31",
                    },
                    "purpose": "读取横截面因子面板数据用于排序",
                }
            ],
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "missing_concepts": [],
            "strategy_modification": "面板数据按时间窗口直接读取。",
        }

        with self.assertRaisesRegex(ValueError, "required_data\\[0\\]\\.universe must be an object"):
            HypothesisAgent._parse_output(json.dumps(payload, ensure_ascii=False))

    def test_run_retries_with_field_feedback_when_required_fields_missing(self) -> None:
        prompts: list[str] = []
        responses = iter(
            [
                json.dumps({"missing_concepts": [], "strategy_modification": ""}, ensure_ascii=False),
                json.dumps(
                    {
                        "hypothesis": "布林带均值回归策略",
                        "required_data": [
                            {
                                "table_key": "stock_kline_daily_qfq",
                                "fields": ["close"],
                                "universe": {"type": "named_pool", "value": "hs300"},
                                "time_range": {"start": "2020-01-01", "end": "2025-12-31"},
                                "purpose": "生成布林带信号",
                            }
                        ],
                        "backtest_datasets": ["vnpy_stock_daily_qfq"],
                        "missing_concepts": [],
                        "strategy_modification": "",
                    },
                    ensure_ascii=False,
                ),
            ]
        )

        original_complete_with_tools = hypothesis_agent_module.llm_client.complete_with_tools
        original_write_trace_json = hypothesis_agent_module.write_trace_json
        original_print_agent_progress = hypothesis_agent_module.print_agent_progress
        try:
            def fake_complete_with_tools(
                *,
                system_prompt: str,
                user_prompt: str,
                tools: list[dict[str, object]],
                tool_handlers: dict[str, object],
                temperature: float,
                max_tokens: int,
                max_tool_rounds: int,
                require_json_object: bool,
                final_json_instruction: str,
                **kwargs: object,
            ) -> tuple[str, list[dict[str, object]]]:
                prompts.append(user_prompt)
                return next(responses), []

            hypothesis_agent_module.llm_client.complete_with_tools = fake_complete_with_tools
            hypothesis_agent_module.write_trace_json = lambda *args, **kwargs: Path("/tmp/fake.json")
            hypothesis_agent_module.print_agent_progress = lambda *args, **kwargs: None

            agent = HypothesisAgent()
            agent.max_retries = 2
            state = {
                "user_idea": "布林带均值回归策略",
                "experiment_spec": {"scenario": "", "universe": [{"symbols": "hs300"}]},
                "epoch_index": 1,
                "max_epochs": 1,
                "hypothesis": "",
                "backtest_feedback": "",
                "validate_feedback": "这段验证反馈不应传给 HypothesisAgent",
                "statistical_feedback": "",
                "history": [],
            }

            result = agent.run(state)

            self.assertEqual(result["hypothesis_generation_meta"]["hypothesis"], "布林带均值回归策略")
            self.assertEqual(len(prompts), 2)
            self.assertNotIn("验证反馈", prompts[0])
            self.assertNotIn("这段验证反馈不应传给 HypothesisAgent", prompts[0])
            self.assertIn("必须包含非空的 hypothesis 字段", prompts[1])
            self.assertIn("required_data 字段", prompts[1])
            self.assertIn("missing required string field: hypothesis", prompts[1])
        finally:
            hypothesis_agent_module.llm_client.complete_with_tools = original_complete_with_tools
            hypothesis_agent_module.write_trace_json = original_write_trace_json
            hypothesis_agent_module.print_agent_progress = original_print_agent_progress


def _research_payload(decision: str = "diagnose_only") -> dict[str, object]:
    payload: dict[str, object] = {
        "decision": decision,
        "previous_change_review": {
            "expected": ["减少交易"],
            "actual": ["交易数仅下降2笔"],
            "conclusion": "rejected",
        },
        "facts": [
            {
                "statement": "交易数从659变为657",
                "source": "开发期完整报告",
                "numbers": {"before": 659, "after": 657},
            }
        ],
        "possible_causes": [
            {
                "cause": "日常比例调整产生小额交易",
                "supporting_evidence": ["目标比例未变时仍有交易"],
                "opposing_evidence": [],
                "missing_evidence": ["小额交易费用"],
                "confidence": "medium",
            },
            {
                "cause": "震荡策略本身亏损",
                "supporting_evidence": [],
                "opposing_evidence": [],
                "missing_evidence": ["按市场状态计算的收益"],
                "confidence": "low",
            },
        ],
        "selected_cause": "",
        "requested_diagnostics": [
            {
                "id": "period_metrics",
                "reason": "按时期拆分收益",
                "parameters": {},
            }
        ],
        "hypothesis": "保持上一轮完整策略不变",
        "required_data": [
            {
                "table_key": "stock_kline_daily_qfq",
                "type": "time_series",
                "fields": ["open", "close"],
                "universe": {"type": "named_pool", "value": "沪深300"},
                "time_range": {"start": "2020-01-01", "end": "2025-12-31"},
                "purpose": "生成策略信号",
            }
        ],
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
        "missing_concepts": [],
        "strategy_modification": "",
        "unchanged_parts": ["全部策略规则"],
        "expected_results": [],
        "judgment_is_wrong_if": "",
        "stop_reason": "",
        "knowledge_record": {
            "measured_facts": [],
            "tested_conclusions": [],
            "unverified_guesses": [],
        },
    }
    if decision == "modify_one_rule":
        payload.update(
            {
                "selected_cause": "日常比例调整产生小额交易",
                "requested_diagnostics": [],
                "strategy_modification": "目标股票和目标比例不变时不重复调整",
                "unchanged_parts": ["选股", "退出", "仓位上限"],
                "expected_results": ["交易数至少下降20%"],
                "judgment_is_wrong_if": "交易数下降不足5%",
            }
        )
    if decision == "stop":
        payload.update(
            {
                "requested_diagnostics": [],
                "stop_reason": "现有数据无法支持原始研究方案",
            }
        )
    return payload


def test_translation_can_route_to_initial_research_before_code(monkeypatch) -> None:
    translation_payload = {
        "hypothesis": "先研究训练期资料，再冻结一个候选。",
        "required_data": _research_payload()["required_data"],
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
        "missing_concepts": [],
        "strategy_modification": "",
        "translation_notes": {
            "core_hypothesis": {
                "market_mechanism": "规律成交可能表示尚未完成的买入",
                "observable_pattern": "固定间隔放量",
                "expected_outcome": "预计下一批附近上涨",
                "evidence_against": "训练期没有相对优势",
            },
            "fixed_parts": [],
            "changeable_parts": [],
            "candidate_dimensions": [],
            "hard_constraints": [],
        },
    }
    monkeypatch.setattr(
        hypothesis_agent_module.llm_client,
        "complete_with_tools",
        lambda **kwargs: (json.dumps(translation_payload, ensure_ascii=False), []),
    )
    monkeypatch.setattr(hypothesis_agent_module, "write_trace_text", lambda *a, **k: None)
    monkeypatch.setattr(hypothesis_agent_module, "write_trace_json", lambda *a, **k: None)
    monkeypatch.setattr(hypothesis_agent_module, "print_agent_progress", lambda *a, **k: None)
    state = init_state(
        "分钟事件",
        max_epochs=3,
        experiment_spec={
            "scenario": "分钟事件",
            "initial_research_before_strategy": True,
        },
    )

    result = HypothesisAgent().run(state)

    assert result["phase"] == "hypothesis"
    assert result["research_stage"] == "initial_research"
    assert result["strategy_result"] == {}
    assert result["translation_meta"]["core_hypothesis"]["expected_outcome"]


def test_parse_research_output_accepts_diagnose_only() -> None:
    parsed = HypothesisAgent._parse_output(
        json.dumps(_research_payload(), ensure_ascii=False),
        research_mode=True,
    )

    assert parsed["decision"] == "diagnose_only"
    assert parsed["requested_diagnostics"] == [
        {
            "id": "period_metrics",
            "reason": "按时期拆分收益",
            "parameters": {},
        }
    ]
    assert parsed["strategy_modification"] == ""


def test_parse_research_output_normalizes_short_missing_concepts() -> None:
    payload = _research_payload()
    payload["missing_concepts"] = ["费用明细"]

    parsed = HypothesisAgent._parse_output(
        json.dumps(payload, ensure_ascii=False),
        research_mode=True,
    )

    assert parsed["missing_concepts"] == [
        {
            "concept": "费用明细",
            "purpose": "研究优化时发现仍需明确",
            "alternative": "",
        }
    ]


def test_retry_prompt_states_nested_field_formats() -> None:
    prompt = HypothesisAgent._build_retry_user_prompt(
        "原始输入",
        ValueError("字段格式错误"),
        '{"bad": true}',
    )

    assert "time_range" in prompt
    assert "missing_concepts" in prompt
    assert "不能写成字符串" in prompt


def test_parse_research_output_requires_two_possible_causes() -> None:
    payload = _research_payload("modify_one_rule")
    payload["possible_causes"] = payload["possible_causes"][:1]  # type: ignore[index]

    with TestCase().assertRaisesRegex(ValueError, "at least two"):
        HypothesisAgent._parse_output(
            json.dumps(payload, ensure_ascii=False),
            research_mode=True,
        )


def test_candidate_history_excludes_final_test_and_keeps_prediction() -> None:
    state = {
        "candidate_records": [
            {
                "candidate_id": "candidate_001",
                "candidate_mode": "modify_one_rule",
                "period_kind": "development",
                "hypothesis": "开发期策略；2025-01-01至2025-12-31为最终时期",
                "strategy_modification": "只改一项",
                "expected_results": ["交易数下降20%"],
                "judgment_is_wrong_if": "交易数下降不足5%",
                "result": {"sharpe": -1.2},
                "development_report": {"median_sharpe": -1.2},
            },
            {
                "candidate_id": "candidate_001",
                "period_kind": "final_test",
                "hypothesis": "绝不能进入研究提示词的最终结果",
                "result": {"sharpe": 9.9},
            },
            {
                "candidate_id": "candidate_without_period",
                "hypothesis": "MISSING_PERIOD_SECRET",
                "result": {"sharpe": 8.8},
            },
        ],
        "development_period": {"start": "2024-01-01", "end": "2024-12-31"},
    }

    history = HypothesisAgent._candidate_history_for_prompt(state)  # type: ignore[arg-type]

    assert len(history) == 1
    assert history[0]["candidate_id"] == "candidate_001"
    assert history[0]["expected_results"] == ["交易数下降20%"]
    assert "最终结果" not in json.dumps(history, ensure_ascii=False)
    assert "MISSING_PERIOD_SECRET" not in json.dumps(history, ensure_ascii=False)
    assert "2025-" not in json.dumps(history, ensure_ascii=False)


def test_candidate_history_keeps_required_research_evidence_under_size_limit() -> None:
    records = []
    for index in range(1, 8):
        selected_id = f"S{index}" if index > 1 else ""
        monthly = [
            {
                "period": f"2024-{month:02d}",
                "event_count": 100 + month,
                "gross_mean_return": month / 10000,
                "net_mean_return": month / 10000 - 0.0016,
                "gross_up_rate": 0.4 + month / 1000,
                "label_positive_rate": 0.3,
                "gross_mean_ci95_daily_cluster": [0.00001, 0.0002],
            }
            for month in range(1, 13)
        ]
        records.append(
            {
                "candidate_id": f"candidate_{index:03d}",
                "candidate_mode": "baseline" if index == 1 else "test_candidate",
                "period_kind": "development",
                "epoch_index": index,
                "hypothesis": (
                    "基准完整规则：past_up_count>=4、no_early_spike=true、"
                    "pre_window_up=true。" + "基准说明" * 80
                ),
                "strategy_modification": f"只使用 feature_{index}>={index}",
                "research_decision": "baseline" if index == 1 else "test_candidate",
                "selected_cause": f"原因{index}",
                "expected_results": [f"候选{index}毛收益方向稳定"],
                "judgment_is_wrong_if": f"候选{index}开发期毛收益为负",
                "previous_change_review": {
                    "conclusion": "supported",
                    "actual": ["REPEATED_LONG_REVIEW" * 200],
                },
                "objective_assessment": {
                    "long": "REPEATED_OBJECTIVE_EVIDENCE" * 200
                },
                "selected_direction_id": selected_id,
                "candidate_directions": (
                    [
                        {
                            "id": selected_id,
                            "type": "screened_candidate",
                            "exact_change": f"只使用 feature_{index}>={index}",
                            "official_test_status": "untested",
                        }
                    ]
                    if selected_id
                    else []
                )
                + [
                    {
                        "id": f"U{index}",
                        "type": "hypothesis_branch",
                        "research_question": f"未测方向{index}",
                        "exact_change": f"改用 alternative_{index}<=0",
                        "official_test_status": "untested",
                        "supporting_evidence": ["REPEATED_DIRECTION_EVIDENCE" * 200],
                    }
                ],
                "untested_plans": [
                    {
                        "direction_id": f"U{index}",
                        "reason_not_selected_now": "本轮先检验已选规则",
                        "evidence_needed": ["需要独立正式回测"],
                    }
                ],
                "result": {
                    "trade_count": 1000 + index,
                    "summary": "REPEATED_LONG_SUMMARY" * 200,
                },
                "development_report": {
                    "report_kind": "event_parquet",
                    "period_kind": "development",
                    "passed": False,
                    "overall": {
                        "total_trade_count": 1000 + index,
                        "event_gross_mean_return": index / 10000,
                        "event_gross_median_return": 0.0,
                        "event_gross_up_rate": 0.45,
                        "event_net_mean_return": index / 10000 - 0.0016,
                        "event_net_median_return": -0.0016,
                        "event_net_win_rate": 0.3,
                    },
                    "by_year": [
                        {
                            "period": "2024",
                            "event_count": 1000 + index,
                            "gross_mean_return": index / 10000,
                            "net_mean_return": index / 10000 - 0.0016,
                        }
                    ],
                    "by_month": monthly,
                    "failure_reasons": ["REPEATED_LONG_SUMMARY" * 200],
                    "folds": [{"summary": "REPEATED_LONG_SUMMARY" * 200}],
                },
            }
        )
    state = {
        "candidate_records": records,
        "development_period": {"start": "2024-01-01", "end": "2024-12-31"},
    }

    history = HypothesisAgent._candidate_history_for_prompt(state)  # type: ignore[arg-type]
    text = json.dumps(history, ensure_ascii=False, separators=(",", ":"))

    assert len(history) == 7
    assert "past_up_count>=4" in history[0]["strategy_rule"]
    assert history[1]["strategy_rule"] == "只使用 feature_2>=2"
    for index, candidate in enumerate(history, start=1):
        evidence = candidate["development_evidence"]
        if index > 1:
            assert candidate["strategy_rule"] == f"只使用 feature_{index}>={index}"
        assert candidate["research_decision"] in {"baseline", "test_candidate"}
        assert candidate["expected_results"]
        assert evidence["event_count"] == 1000 + index
        assert evidence["event_gross_mean_return"] == index / 10000
        assert evidence["event_net_mean_return"] == index / 10000 - 0.0016
        assert evidence["monthly_stability"]["month_count"] == 12
        assert evidence["monthly_stability"]["gross_positive_month_count"] == 12
        assert candidate["untested_directions"][0]["id"] == f"U{index}"
        assert candidate["untested_directions"][0]["exact_change"]
    assert "development_report" not in text
    assert "REPEATED_LONG_SUMMARY" not in text
    assert "REPEATED_OBJECTIVE_EVIDENCE" not in text
    assert "REPEATED_DIRECTION_EVIDENCE" not in text
    history_bytes = len(text.encode("utf-8"))
    assert history_bytes < 28000
    assert 72000 + history_bytes < 100000


def test_sanitize_research_value_hides_date_variants_and_date_keys() -> None:
    value = {
        "2025/01/02": "斜杠日期为2025/01/02",
        "2026年": {"2026年1月3日": "中文日期为2026年1月3日"},
        "allowed": "截至2024年12月31日",
        "statistics": "样本数2025，统计值1234，股票代码600519",
    }

    sanitized = HypothesisAgent._sanitize_research_value(
        value,
        latest_allowed_date="2024-12-31",
    )

    text = json.dumps(sanitized, ensure_ascii=False)
    assert "2025/01/02" not in text
    assert "2026年" not in text
    assert "2026年1月3日" not in text
    assert "截至2024年12月31日" in text
    assert "样本数2025，统计值1234，股票代码600519" in text
    assert "2024-12-31" in sanitized
    assert "2024年" in sanitized


def test_diagnostic_history_for_prompt_keeps_metrics_and_removes_repetition() -> None:
    monthly = [
        {
            "period": f"2023-{month:02d}",
            "event_count": month * 100,
            "gross_mean_return": month / 10000,
            "gross_up_rate": 0.4,
            "unused_detail": "x" * 1000,
        }
        for month in range(1, 13)
    ]
    candidates = [
        {
            "condition": {"feature": f"f{index}", "operator": "<=", "value": index},
            "training_event_count_before_cooldown": 1000 + index,
            "training_gross_mean_before_cooldown": 0.001 + index / 10000,
            "training": {
                "event_count": 1000 + index,
                "gross_mean_return": 0.001,
                "unused_detail": "y" * 1000,
            },
            "fixed_evaluation": {
                "event_count": 500 + index,
                "gross_mean_return": 0.0008,
                "unused_detail": "z" * 1000,
            },
            "development": {"duplicate": "d" * 1000},
            "training_covers_configured_cost": False,
        }
        for index in range(12)
    ]
    reports = [
        {
            "request_id": "diagnostic_01",
            "period_access": {"final_period_read": False},
            "results": [
                {
                    "id": "period_metrics",
                    "status": "completed",
                    "periods": {
                        "train": {
                            "overall": {
                                "event_count": 12000,
                                "gross_mean_return": 0.0002,
                            },
                            "by_year": [],
                            "by_month": monthly,
                        }
                    },
                },
                {
                    "id": "feature_screening",
                    "status": "completed",
                    "tested_condition_count": 713,
                    "top_training_selected_candidates": candidates,
                },
            ],
        }
    ]

    compact = HypothesisAgent._diagnostic_history_for_prompt(reports)
    text = json.dumps(compact, ensure_ascii=False)

    period_result = compact[0]["results"][0]  # type: ignore[index]
    feature_result = compact[0]["results"][1]  # type: ignore[index]
    monthly_stability = period_result["periods"]["train"][  # type: ignore[index]
        "monthly_stability"
    ]
    assert monthly_stability["month_count"] == 12
    assert monthly_stability["event_count_total"] == 7800
    assert monthly_stability["gross_mean_return_max"] == 0.0012
    assert monthly_stability["gross_positive_month_count"] == 12
    assert len(feature_result["top_training_selected_candidates"]) == 8  # type: ignore[arg-type]
    assert "unused_detail" not in text
    assert '"development"' not in text
    assert len(text) < 15000


def test_diagnostic_history_keeps_low_ma5_screening_and_post_trigger_warning() -> None:
    safe_fields = (
        "trigger_low_to_prev5_close_ma5_distance",
        "trigger_low_to_live_close_ma5_distance",
    )
    monthly_stability = {
        "month_count": 2,
        "gross_positive_month_count": 2,
        "net_positive_month_count": 1,
        "gross_mean_return_min": 0.001,
        "gross_mean_return_median": 0.0015,
        "gross_mean_return_max": 0.002,
        "net_mean_return_min": -0.0006,
        "net_mean_return_median": 0.0001,
        "net_mean_return_max": 0.0008,
        "unused_detail": "remove",
    }
    candidates = []
    for field in safe_fields:
        for index in range(5):
            candidates.append(
                {
                    "selection_rank": len(candidates) + 1,
                    "condition": {
                        "feature": field,
                        "operator": "<=",
                        "value": index / 100,
                    },
                    "selection_quantile_level": 0.1 + index / 10,
                    "selection": {
                        "event_count": 800,
                        "gross_mean_return": 0.002,
                        "net_mean_return": 0.0004,
                        "gross_up_rate": 0.52,
                        "monthly_stability": monthly_stability,
                    },
                    "confirmation": {
                        "event_count": 400,
                        "gross_mean_return": 0.001,
                        "net_mean_return": -0.0006,
                        "gross_up_rate": 0.49,
                        "monthly_stability": monthly_stability,
                    },
                    "changes_from_baseline": {
                        "selection": {"gross_mean_return_change": 0.0005},
                        "confirmation": {"gross_mean_return_change": 0.0002},
                    },
                }
            )
    reports = [
        {
            "request_id": "low_ma5_01",
            "results": [
                {
                    "id": "low_ma5_distance_screening",
                    "status": "completed",
                    "safe_fields": list(safe_fields),
                    "minimum_selection_event_count_rule": (
                        "max(100, ceil(selection_baseline_event_count * 0.05))"
                    ),
                    "baseline": {
                        "selection": {
                            "event_count": 1_000,
                            "gross_mean_return": 0.0015,
                            "monthly_stability": monthly_stability,
                        },
                        "confirmation": {
                            "event_count": 500,
                            "gross_mean_return": 0.0008,
                            "monthly_stability": monthly_stability,
                        },
                    },
                    "training_ranked_candidates": candidates,
                    "full_day_descriptive_analysis": {
                        "field": "analysis_only_full_day_low_to_close_ma5_distance",
                        "status": "descriptive_only",
                        "strategy_eligible": False,
                        "can_nominate_candidate": False,
                        "reason": "触发后才完整可见",
                        "bins": [
                            {
                                "lower_exclusive": None,
                                "upper_inclusive": -0.02,
                                "selection": {
                                    "event_count": 100,
                                    "monthly_stability": monthly_stability,
                                },
                                "confirmation": {
                                    "event_count": 50,
                                    "monthly_stability": monthly_stability,
                                },
                            }
                        ],
                    },
                    "warning": "完整日字段不能提名候选。",
                }
            ],
        }
    ]

    compact = HypothesisAgent._diagnostic_history_for_prompt(reports)
    result = compact[0]["results"][0]  # type: ignore[index]

    assert result["id"] == "low_ma5_distance_screening"
    assert result["minimum_selection_event_count_rule"].startswith("max(100")
    assert len(result["training_ranked_candidates"]) == 6
    assert {
        item["condition"]["feature"]
        for item in result["training_ranked_candidates"]
    } == set(safe_fields)
    full_day = result["full_day_descriptive_analysis"]
    assert full_day["strategy_eligible"] is False
    assert full_day["can_nominate_candidate"] is False
    assert full_day["bins"][0]["can_nominate_candidate"] is False
    metric_groups = [
        result["baseline"]["selection"],
        result["baseline"]["confirmation"],
        *[
            item[period]
            for item in result["training_ranked_candidates"]
            for period in ("selection", "confirmation")
        ],
        full_day["bins"][0]["selection"],
        full_day["bins"][0]["confirmation"],
    ]
    assert all(item["monthly_stability"]["month_count"] == 2 for item in metric_groups)
    assert all(
        "unused_detail" not in item["monthly_stability"]
        for item in metric_groups
    )


def test_diagnostic_history_removes_exact_duplicate_partial_results() -> None:
    repeated_partial = {
        "id": "execution_price_audit",
        "status": "partial",
        "periods": {"development": {"missing_count": 12}},
        "limitations": ["缺少逐笔成交价"],
    }
    reports = [
        {
            "request_id": "diagnostic_01",
            "partial_results": ["execution_price_audit"],
            "results": [repeated_partial],
        },
        {
            "request_id": "diagnostic_02",
            "partial_results": ["execution_price_audit"],
            "results": [dict(repeated_partial)],
        },
        {
            "request_id": "diagnostic_03",
            "partial_results": ["execution_price_audit"],
            "results": [
                {
                    **repeated_partial,
                    "periods": {"development": {"missing_count": 9}},
                }
            ],
        },
    ]

    compact = HypothesisAgent._diagnostic_history_for_prompt(reports)

    assert [report["request_id"] for report in compact] == [
        "diagnostic_01",
        "diagnostic_03",
    ]
    assert sum(len(report["results"]) for report in compact) == 2
    assert all(
        report["partial_results"] == ["execution_price_audit"]
        for report in compact
    )


def test_research_run_receives_complete_development_evidence_without_final_test(
    monkeypatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_complete_with_tools(**kwargs):
        captured["system_prompt"] = kwargs["system_prompt"]
        captured["user_prompt"] = kwargs["user_prompt"]
        return json.dumps(_research_payload(), ensure_ascii=False), []

    monkeypatch.setattr(
        hypothesis_agent_module.llm_client,
        "complete_with_tools",
        fake_complete_with_tools,
    )
    monkeypatch.setattr(hypothesis_agent_module, "write_trace_text", lambda *a, **k: None)
    monkeypatch.setattr(hypothesis_agent_module, "write_trace_json", lambda *a, **k: None)
    monkeypatch.setattr(
        hypothesis_agent_module,
        "print_agent_progress",
        lambda *a, **k: None,
    )

    state = init_state(
        "ADX市场状态策略",
        max_epochs=3,
        experiment_spec={
            "scenario": "沪深300日线；2025-01-01至2025-12-31为最终时期",
            "validate_start": "2024-01-01",
            "validate_end": "2024-12-31",
        },
    )
    state["epoch_index"] = 2
    state["backtest_feedback"] = "trade_count=659, median_sharpe=-1.47"
    state["development_report"] = {
        "median_sharpe": -1.47,
        "cost_stress_median_sharpe": -1.81,
        "delay_stress_median_sharpe": -1.19,
        "folds": [{"name": "fold_01", "trade_count": 218, "sharpe": 0.91}],
    }
    state["diagnostic_round"] = 1
    state["diagnostic_report"] = {
        "request_id": "forbidden-current",
        "period_access": {"final_period_read": True},
        "results": [{"id": "CURRENT_FINAL_DIAGNOSTIC_SECRET"}],
    }
    state["diagnostic_records"] = [
        {
            "request_id": "allowed-development",
            "period_access": {"final_period_read": False},
            "results": [{"id": "rule_waterfall", "train_gross_mean": 0.0001}],
        },
        {
            "request_id": "forbidden-final",
            "period_access": {"final_period_read": True},
            "results": [{"id": "FINAL_DIAGNOSTIC_SECRET"}],
        },
    ]
    state["hypothesis_generation_meta"] = {
        "hypothesis": "保持上一轮完整策略不变",
        "required_data": _research_payload()["required_data"],
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
        "strategy_modification": "连续三日确认ADX状态",
        "expected_results": ["减少交易"],
    }
    state["candidate_records"] = [
        {
            "candidate_id": "candidate_001",
            "period_kind": "development",
            "hypothesis": "开发期策略",
            "result": {"trade_count": 659},
            "development_report": state["development_report"],
        },
        {
            "candidate_id": "candidate_001",
            "period_kind": "final_test",
            "hypothesis": "FINAL_SECRET_MARKER",
            "result": {"sharpe": 9.9},
        },
    ]

    result = HypothesisAgent().run(state)

    assert result["phase"] == "diagnostics"
    assert result["hypothesis_generation_meta"]["decision"] == "diagnose_only"
    assert result["diagnostic_request"]["source_candidate_id"] == "candidate_001"
    assert "trade_count=659" in captured["user_prompt"]
    assert "cost_stress_median_sharpe" in captured["user_prompt"]
    assert "candidate_001" in captured["user_prompt"]
    assert "rule_waterfall" in captured["user_prompt"]
    assert "train_gross_mean" in captured["user_prompt"]
    assert "FINAL_SECRET_MARKER" not in captured["user_prompt"]
    assert "FINAL_DIAGNOSTIC_SECRET" not in captured["user_prompt"]
    assert "CURRENT_FINAL_DIAGNOSTIC_SECRET" not in captured["user_prompt"]
    assert "2025-" not in captured["system_prompt"]
    assert "2025-" not in captured["user_prompt"]
    assert "至少提出两个有实质区别的可能原因" in captured["system_prompt"]


def test_event_research_requires_core_diagnostics_and_two_formal_candidates_before_stop(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        hypothesis_agent_module.llm_client,
        "complete_with_tools",
        lambda **kwargs: (json.dumps(_research_payload("stop"), ensure_ascii=False), []),
    )
    monkeypatch.setattr(hypothesis_agent_module, "write_trace_text", lambda *a, **k: None)
    monkeypatch.setattr(hypothesis_agent_module, "write_trace_json", lambda *a, **k: None)
    monkeypatch.setattr(hypothesis_agent_module, "print_agent_progress", lambda *a, **k: None)
    state = init_state(
        "分钟事件",
        max_epochs=3,
        experiment_spec={
            "backtest_mode": "event_parquet",
            "train_start": "2022-01-01",
            "train_end": "2023-12-31",
            "validate_start": "2024-01-01",
            "validate_end": "2024-12-31",
        },
    )
    state["epoch_index"] = 2
    state["candidate_records"] = [
        {"candidate_id": "candidate_001", "period_kind": "development"}
    ]

    result = HypothesisAgent().run(state)

    assert result["phase"] == "diagnostics"
    assert result["hypothesis_generation_meta"]["decision"] == "diagnose_only"
    assert [item["id"] for item in result["diagnostic_request"]["items"]] == [
        "core_variant_comparison",
        "event_response_curve",
        "feature_screening",
    ]

    result["diagnostic_report"] = {
        "results": [
            {"id": "feature_screening", "status": "completed"},
            {"id": "event_response_curve", "status": "completed"},
            {"id": "next_pulse_mechanism", "status": "completed"},
            {"id": "core_variant_comparison", "status": "completed"},
        ]
    }
    result["diagnostic_round"] = 1

    with TestCase().assertRaisesRegex(AgentExecutionError, "正式候选数量不足"):
        HypothesisAgent().run(result)

    result["candidate_records"].append(
        {"candidate_id": "candidate_002", "period_kind": "development"}
    )
    allowed = HypothesisAgent().run(result)

    assert allowed["phase"] == "done"
    assert allowed["hypothesis_generation_meta"]["decision"] == "stop"
