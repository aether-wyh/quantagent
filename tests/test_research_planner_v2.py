from __future__ import annotations

import json
from copy import deepcopy
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

    class _DummyOpenAI:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda *a, **k: None))

    setattr(openai_stub, "OpenAI", _DummyOpenAI)
    sys.modules["openai"] = openai_stub

from quanta_agents.agents.research_planner_v2 import ResearchPlannerV2
from quanta_agents.prompt_loader import load_agent_prompt_dict


def _theory_payload(reference: str = "") -> dict[str, object]:
    theories = []
    for index in range(4):
        theories.append(
            {
                "theory_id": f"theory_{index + 1}",
                "kind": "null" if index == 3 else "causal",
                "phenomenon_summary": f"解释 {index + 1}",
                "actor": "无特定主体" if index == 3 else f"主体 {index + 1}",
                "objective": "检验是否只是偶然" if index == 3 else "完成某种交易目的",
                "constraints": ["容量有限"],
                "sequence": ["先出现观察", "随后出现结果"],
                "extra_predictions": ["预期甲", "预期乙"],
                "counterexample": "额外预期同时不成立",
                "search_queries": [f"query {index + 1}"],
                "evidence_source_ids": [reference] if reference else [],
                "confidence": "low",
            }
        )
    return {
        "shared_observations": ["观察到一组价格和成交特征"],
        "theories": theories,
        "search_summary": "仍需回测",
    }


def _candidate_payload(*, field: str = "volume") -> dict[str, object]:
    return {
        "candidate_mode": "modify_one_rule",
        "category": "numeric_definition",
        "mechanism_id": "theory_1",
        "research_question": "这个定义是否优于当前写法",
        "change_kind": "definition",
        "changed_fields": ["signal_definition"],
        "strategy_modification": "只修改信号定义",
        "hypothesis": "保留当前采用版本的其他规则，只修改信号定义；在信号完成后的下一交易时点下单，并按原持有和退出规则执行。",
        "required_data": [
            {
                "table_key": "daily",
                "type": "time_series",
                "fields": ["open", "close", field],
                "universe": {"type": "dataset_defined", "value": "daily"},
                "time_range": {"start": "2018-01-01", "end": "2024-12-31"},
                "purpose": "计算信号",
            }
        ],
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
        "predicted_changes": [
            {"metric": "median_sharpe", "direction": "increase", "reason": "误判减少"}
        ],
        "judgment_is_wrong_if": "开发期多数分段没有改善",
        "unchanged_parts": ["下单和退出不变"],
        "evidence_used": [],
        "alternatives_not_selected": [],
    }


def _mechanism_candidate_payload() -> dict[str, object]:
    candidate = _candidate_payload()
    candidate.update(
        {
            "category": "mechanism_signal",
            "change_kind": "add_signal",
            "changed_fields": ["new_signal"],
            "research_question": "事先解释推出的新信号是否有独立作用",
            "strategy_modification": "在原规则上增加新信号",
            "hypothesis": "原规则与新信号同时成立后，下一交易时点下单，并按原规则退出。",
            "new_signal_definition": {
                "name": "close_location",
                "formula": "(close-low)/(high-low)",
                "operator": ">=",
                "value": 0.7,
            },
        }
    )
    added = deepcopy(candidate)
    added["variant_mode"] = "added_to_base"
    signal_only = deepcopy(candidate)
    signal_only.update(
        {
            "variant_mode": "signal_only",
            "hypothesis": "只按新信号选股，下一交易时点下单，并按原规则退出。",
            "strategy_modification": "去掉原信号条件，只保留新信号",
        }
    )
    candidate["mechanism_comparison"] = {
        "added_to_base": added,
        "signal_only": signal_only,
    }
    return candidate


def _threshold_candidate_payload() -> dict[str, object]:
    candidate = _candidate_payload()
    candidate.update(
        {
            "research_question": "volume_ratio 的门槛是否过严",
            "change_kind": "threshold",
            "changed_fields": ["volume_ratio"],
            "strategy_modification": "只把 volume_ratio 改为 __SELECTED_VALUE__",
            "hypothesis": "其余规则不变，volume_ratio >= __SELECTED_VALUE__ 时触发。",
            "parameter_probe": {
                "param_name": "volume_ratio",
                "values": [1.5, 1.75, 2.0, 2.25],
            },
        }
    )
    return candidate


def _new_numeric_boundary_payload(*, with_probe: bool) -> dict[str, object]:
    candidate = _candidate_payload()
    candidate.update(
        {
            "research_question": "负收益股票占比过高时是否应禁止信号",
            "changed_fields": ["negative_return_share_threshold"],
        }
    )
    if with_probe:
        candidate.update(
            {
                "change_kind": "threshold",
                "strategy_modification": (
                    "只增加市场状态条件：负收益股票占比达到 "
                    "__SELECTED_VALUE__ 时禁止信号"
                ),
                "hypothesis": (
                    "其余规则不变；负收益股票占比低于 __SELECTED_VALUE__ 时保留信号。"
                ),
                "parameter_probe": {
                    "param_name": "negative_return_share_threshold",
                    "values": [0.7, 0.75, 0.8],
                },
            }
        )
    else:
        candidate.update(
            {
                "change_kind": "applicability_rule",
                "strategy_modification": (
                    "只增加市场状态条件：负收益股票占比达到75%时禁止信号"
                ),
                "hypothesis": "其余规则不变；负收益股票占比低于0.75时保留信号。",
            }
        )
    return candidate


class _TheoryLLM:
    def __init__(self, payload: dict[str, object], events: list[dict[str, object]]) -> None:
        self.payload = payload
        self.events = events
        self.system_prompt = ""
        self.user_prompt = ""

    def complete_with_tools(self, system_prompt: str, user_prompt: str, *args: object, **kwargs: object):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return json.dumps(self.payload, ensure_ascii=False), self.events

    def complete(self, *args: object, **kwargs: object) -> str:
        return json.dumps(self.payload, ensure_ascii=False)


class _RetryTheoryLLM:
    def __init__(self, bad: dict[str, object], good: dict[str, object]) -> None:
        self.bad = bad
        self.good = good
        self.repair_calls = 0

    def complete_with_tools(self, *args: object, **kwargs: object):
        return json.dumps(self.bad, ensure_ascii=False), []

    def complete(self, *args: object, **kwargs: object) -> str:
        self.repair_calls += 1
        return json.dumps(self.good, ensure_ascii=False)


class _CandidateLLM:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.payloads = list(payloads)
        self.calls: list[str] = []

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: object) -> str:
        self.calls.append(user_prompt)
        return json.dumps(self.payloads.pop(0), ensure_ascii=False)


class ResearchPlannerV2Test(TestCase):
    def test_static_prompt_does_not_seed_named_answers(self) -> None:
        prompt = json.dumps(load_agent_prompt_dict("research_planner_v2"), ensure_ascii=False)
        for forbidden in ("沪深300", "游资", "机构"):
            self.assertNotIn(forbidden, prompt)

    def test_candidate_prompt_only_lists_historical_named_pools(self) -> None:
        llm = _CandidateLLM([_candidate_payload()])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development"},
            candidate_history=[],
            available_data=[
                {
                    "table_key": "daily",
                    "type": "time_series",
                    "fields": ["open", "close", "volume"],
                }
            ],
        )

        self.assertIn('"hs300"', llm.calls[0])
        self.assertIn('"csi1000"', llm.calls[0])
        self.assertNotIn('"cn_all_a"', llm.calls[0])

    def test_build_theories_keeps_only_sources_with_confirmed_cutoff(self) -> None:
        usable_hash = "a" * 64
        late_hash = "b" * 64
        events = [
            {
                "tool_name": "search_web",
                "result": {
                    "results": [
                        {
                            "title": "old paper",
                            "url": "https://example.com/old",
                            "published_at": "2019-01-01",
                            "retrieved_at": "2026-01-01",
                            "summary": "old",
                            "content_sha256": usable_hash,
                            "cutoff_status": "within_cutoff",
                            "usable_for_evidence": True,
                        },
                        {
                            "title": "late paper",
                            "url": "https://example.com/late",
                            "published_at": "2025-01-01",
                            "retrieved_at": "2026-01-01",
                            "summary": "late",
                            "content_sha256": late_hash,
                            "cutoff_status": "after_cutoff",
                            # 即使来源误把它标成可用，截止日状态也必须优先。
                            "usable_for_evidence": True,
                        },
                    ]
                },
            }
        ]
        payload = _theory_payload(reference=usable_hash)
        payload["theories"][1]["evidence_source_ids"] = [late_hash]  # type: ignore[index]
        planner = ResearchPlannerV2(llm=_TheoryLLM(payload, events), web_client=object())

        result = planner.build_theories("一句话现象", source_cutoff_date="2020-12-31")

        self.assertEqual(result["theories"][0]["evidence_source_ids"], [usable_hash[:16]])
        self.assertEqual(result["theories"][1]["evidence_source_ids"], [])
        self.assertEqual(result["theories"][1]["external_evidence_status"], "unverified")
        self.assertEqual(len(result["research_sources"]), 1)
        visible_result = json.dumps(result, ensure_ascii=False)
        self.assertIn("old paper", visible_result)
        self.assertNotIn("late paper", visible_result)
        self.assertNotIn("https://example.com/late", visible_result)
        self.assertNotIn(late_hash, visible_result)
        self.assertEqual(
            result["web_tool_events"],
            [
                {
                    "tool_name": "search_web",
                    "result": {
                        "passed": True,
                        "status": "ok",
                        "usable_result_count": 1,
                        "excluded_result_count": 1,
                    },
                }
            ],
        )

    def test_web_tool_handler_hides_unusable_material_before_llm_receives_it(self) -> None:
        usable_hash = "c" * 64

        class MixedWebClient:
            @staticmethod
            def search_web(*args: object, **kwargs: object) -> dict[str, object]:
                return {
                    "passed": True,
                    "status": "ok",
                    "query": "query",
                    "results": [
                        {
                            "title": "usable source",
                            "url": "https://example.com/usable",
                            "summary": "usable summary",
                            "published_at": "2019-01-01",
                            "content_sha256": usable_hash,
                            "cutoff_status": "within_cutoff",
                            "usable_for_evidence": True,
                        },
                        {
                            "title": "late secret",
                            "url": "https://example.com/late-secret",
                            "summary": "late secret summary",
                            "published_at": "2025-01-01",
                            "content_sha256": "d" * 64,
                            "cutoff_status": "after_cutoff",
                            "usable_for_evidence": False,
                        },
                        {
                            "title": "unknown secret",
                            "url": "https://example.com/unknown-secret",
                            "summary": "unknown secret summary",
                            "published_at": None,
                            "content_sha256": "e" * 64,
                            "cutoff_status": "unknown",
                            "usable_for_evidence": False,
                        },
                    ],
                }

            @staticmethod
            def open_url(*args: object, **kwargs: object) -> dict[str, object]:
                return {
                    "passed": True,
                    "status": "ok",
                    "title": "late opened secret",
                    "url": "https://example.com/opened-late",
                    "summary": "late opened summary",
                    "content": "late opened body",
                    "cutoff_status": "after_cutoff",
                    "usable_for_evidence": False,
                }

        planner = ResearchPlannerV2(
            llm=_TheoryLLM(_theory_payload(), []),
            web_client=MixedWebClient(),
        )
        _tools, handlers = planner._web_tools("2020-12-31")

        search_result = handlers["search_web"]("query")
        open_result = handlers["open_url"]("https://example.com/opened-late")

        visible = json.dumps([search_result, open_result], ensure_ascii=False)
        self.assertIn("usable source", visible)
        self.assertEqual(search_result["usable_result_count"], 1)
        self.assertEqual(search_result["excluded_result_count"], 2)
        self.assertEqual(open_result["status"], "filtered_by_cutoff")
        self.assertEqual(open_result["excluded_result_count"], 1)
        for forbidden in (
            "late secret",
            "unknown secret",
            "late opened secret",
            "late opened summary",
            "late opened body",
            "https://example.com/late-secret",
            "https://example.com/unknown-secret",
            "https://example.com/opened-late",
        ):
            self.assertNotIn(forbidden, visible)

    def test_theory_book_requires_one_null_explanation(self) -> None:
        payload = _theory_payload()
        for theory in payload["theories"]:  # type: ignore[index]
            theory["kind"] = "causal"
        planner = ResearchPlannerV2(llm=_TheoryLLM(payload, []), web_client=object())

        with self.assertRaisesRegex(ValueError, "纯偶然解释"):
            planner.build_theories("一句话现象", source_cutoff_date="2020-12-31")

    def test_theory_shape_error_is_repaired_without_repeating_search(self) -> None:
        bad = _theory_payload()
        bad["theories"].append({"theory_id": "broken"})  # type: ignore[union-attr]
        llm = _RetryTheoryLLM(bad, _theory_payload())
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.build_theories("一句话现象", source_cutoff_date="2020-12-31")

        self.assertEqual(len(result["theories"]), 4)
        self.assertEqual(llm.repair_calls, 1)

    def test_unavailable_first_choice_is_replaced_with_implementable_candidate(self) -> None:
        bad = _candidate_payload(field="missing_field")
        good = _candidate_payload(field="volume")
        llm = _CandidateLLM([bad, good])
        planner = ResearchPlannerV2(llm=llm, web_client=object())
        available_data = [
            {
                "table_key": "daily",
                "type": "time_series",
                "fields": ["open", "close", "volume"],
            }
        ]

        result = planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development", "median_sharpe": 0.2},
            candidate_history=[],
            available_data=available_data,
        )

        self.assertEqual(result["planner_attempt"], 2)
        self.assertEqual(result["data_feasibility"], "confirmed")
        self.assertIn("missing_field", llm.calls[1])

    def test_new_numeric_boundary_is_rewritten_as_parameter_probe(self) -> None:
        bad = _new_numeric_boundary_payload(with_probe=False)
        good = _new_numeric_boundary_payload(with_probe=True)
        llm = _CandidateLLM([bad, good])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.propose_candidate(
            source_text="30天盘整，连续两天放量达到2倍，实体比例小于0.5",
            theory_book=_theory_payload(),
            accepted_strategy={
                "hypothesis": "沿用原始规则",
                "params": {
                    "consolidation_days": 30,
                    "volume_ratio": 2.0,
                    "body_ratio": 0.5,
                },
            },
            development_report={"period_kind": "development"},
            candidate_history=[],
            available_data=[
                {
                    "table_key": "daily",
                    "type": "time_series",
                    "fields": ["open", "close", "volume"],
                }
            ],
        )

        self.assertEqual(result["planner_attempt"], 2)
        self.assertEqual(result["change_kind"], "threshold")
        self.assertEqual(
            result["parameter_probe"]["param_name"],
            "negative_return_share_threshold",
        )
        self.assertIn("新数值界线: 0.75", llm.calls[1])
        self.assertIn("parameter_probe", llm.calls[1])

    def test_natural_and_accepted_numeric_values_do_not_require_probe(self) -> None:
        candidate = _candidate_payload()
        candidate.update(
            {
                "change_kind": "applicability_rule",
                "changed_fields": ["score_range"],
                "strategy_modification": (
                    "只要求分数在0到1之间，并保留已有0.75界线和原始30、2、0.5"
                ),
                "hypothesis": (
                    "原始30天、2倍、0.5不变；分数需满足0 <= score <= 1，"
                    "旧界线0.75不变。"
                ),
            }
        )
        llm = _CandidateLLM([candidate])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.propose_candidate(
            source_text="原始条件为30天、2倍和0.5，不含这段分数说明",
            theory_book=_theory_payload(),
            accepted_strategy={
                "hypothesis": "当前采用版本已有0.75界线",
                "params": {"existing_limit": 0.75},
            },
            development_report={"period_kind": "development"},
            candidate_history=[],
            available_data=[
                {
                    "table_key": "daily",
                    "type": "time_series",
                    "fields": ["open", "close", "volume"],
                }
            ],
        )

        self.assertEqual(result["planner_attempt"], 1)
        self.assertNotIn("parameter_probe", result)

    def test_final_period_records_are_not_shown_to_candidate_planner(self) -> None:
        llm = _CandidateLLM([_candidate_payload()])
        planner = ResearchPlannerV2(llm=llm, web_client=object())
        planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={
                "period_kind": "development",
                "median_sharpe": 0.2,
                "final_test_report": {"secret": "NEVER_SHOW"},
            },
            candidate_history=[
                {"period_kind": "final_test", "summary": "FINAL_SECRET"},
                {"period_kind": "development", "summary": "DEV_OK"},
            ],
            available_data=[
                {
                    "table_key": "daily",
                    "type": "time_series",
                    "fields": ["open", "close", "volume"],
                }
            ],
        )

        self.assertNotIn("NEVER_SHOW", llm.calls[0])
        self.assertNotIn("FINAL_SECRET", llm.calls[0])
        self.assertIn("DEV_OK", llm.calls[0])

    def test_large_backtest_details_are_not_shown_to_candidate_planner(self) -> None:
        llm = _CandidateLLM([_candidate_payload()])
        planner = ResearchPlannerV2(llm=llm, web_client=object())
        large_marker = "LARGE_WEIGHT_DETAIL_" * 20_000
        development_report = {
            "period_kind": "development",
            "fold_count": 4,
            "median_annual_return": 0.08,
            "median_sharpe": 0.7,
            "worst_fold_sharpe": 0.1,
            "total_trade_count": 800,
            "transaction_cost_rule": {
                "buy_rate": 0.0003,
                "sell_rate_before_change": 0.0013,
                "sell_rate_change_date": "2023-08-28",
                "sell_rate_from_change": 0.0008,
            },
            "double_cost_rule": {
                "buy_rate": 0.0006,
                "sell_rate_before_change": 0.0026,
                "sell_rate_change_date": "2023-08-28",
                "sell_rate_from_change": 0.0016,
            },
            "recompute_records": [{"output_weights": large_marker}],
            "folds": [
                {
                    "name": "fold_1",
                    "annual_return": 0.08,
                    "sharpe": 0.7,
                    "trade_count": 200,
                    "_target_weights_df": large_marker,
                }
            ],
        }

        planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report=development_report,
            candidate_history=[
                {
                    "candidate_id": "candidate_001",
                    "development_report": development_report,
                    "mechanism_comparison_results": {
                        "signal_only": {
                            "report": development_report,
                            "output_weights": large_marker,
                        }
                    },
                }
            ],
            available_data=[
                {
                    "table_key": "daily",
                    "type": "time_series",
                    "fields": ["open", "close", "volume"],
                }
            ],
        )

        shown = llm.calls[0]
        self.assertNotIn("LARGE_WEIGHT_DETAIL", shown)
        self.assertNotIn("recompute_records", shown)
        self.assertNotIn("_target_weights_df", shown)
        self.assertIn('"median_sharpe": 0.7', shown)
        self.assertIn('"trade_count": 200', shown)
        self.assertIn('"sell_rate_before_change": 0.0013', shown)
        self.assertIn('"sell_rate_before_change": 0.0026', shown)
        self.assertLess(len(shown), 100_000)

    def test_extra_category_cannot_skip_five_required_categories(self) -> None:
        extra = _candidate_payload()
        extra["category"] = "extra_liquidity_shape"
        regular = _candidate_payload()
        llm = _CandidateLLM([extra, regular])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development"},
            candidate_history=[],
            covered_categories=[],
            available_data=[
                {"table_key": "daily", "type": "time_series", "fields": ["open", "close", "volume"]}
            ],
        )

        self.assertEqual(result["category"], "numeric_definition")
        self.assertIn("未正式检查", llm.calls[1])

    def test_extra_category_is_allowed_after_five_required_categories(self) -> None:
        extra = _candidate_payload()
        extra["category"] = "extra_liquidity_shape"
        planner = ResearchPlannerV2(llm=_CandidateLLM([extra]), web_client=object())

        result = planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development"},
            candidate_history=[],
            covered_categories=sorted(ResearchPlannerV2._categories),
            available_data=[
                {"table_key": "daily", "type": "time_series", "fields": ["open", "close", "volume"]}
            ],
        )

        self.assertEqual(result["category"], "extra_liquidity_shape")

    def test_unparseable_named_pool_is_replaced_by_computable_scope(self) -> None:
        bad = _candidate_payload()
        bad["required_data"][0]["universe"] = {  # type: ignore[index]
            "type": "named_pool",
            "value": "csi1000_not_registered",
        }
        good = _candidate_payload()
        llm = _CandidateLLM([bad, good])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development"},
            candidate_history=[],
            available_data=[
                {"table_key": "daily", "type": "time_series", "fields": ["open", "close", "volume"]}
            ],
        )

        self.assertEqual(result["required_data"][0]["universe"]["type"], "dataset_defined")
        self.assertIn("目前不能解析", llm.calls[1])
        self.assertIn("现有字段", llm.calls[1])

    def test_static_all_a_example_is_not_accepted_as_v2_named_pool(self) -> None:
        bad = _candidate_payload()
        bad["required_data"][0]["universe"] = {  # type: ignore[index]
            "type": "named_pool",
            "value": "cn_all_a",
        }
        good = _candidate_payload()
        llm = _CandidateLLM([bad, good])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development"},
            candidate_history=[],
            available_data=[
                {
                    "table_key": "daily",
                    "type": "time_series",
                    "fields": ["open", "close", "volume"],
                }
            ],
        )

        self.assertEqual(result["required_data"][0]["universe"]["type"], "dataset_defined")
        self.assertIn("cn_all_a", llm.calls[1])
        self.assertIn("dataset_defined", llm.calls[1])

    def test_mechanism_signal_requires_added_and_signal_only_candidates(self) -> None:
        bad = _mechanism_candidate_payload()
        del bad["mechanism_comparison"]["signal_only"]  # type: ignore[index]
        good = _mechanism_candidate_payload()
        llm = _CandidateLLM([bad, good])
        planner = ResearchPlannerV2(llm=llm, web_client=object())

        result = planner.propose_candidate(
            source_text="一句话现象",
            theory_book=_theory_payload(),
            accepted_strategy={"hypothesis": "当前采用版本"},
            development_report={"period_kind": "development"},
            candidate_history=[],
            covered_categories=["numeric_definition"],
            available_data=[
                {"table_key": "daily", "type": "time_series", "fields": ["open", "close", "volume"]}
            ],
        )

        self.assertIn("signal_only", result["mechanism_comparison"])
        self.assertIn("缺少可回测候选", llm.calls[1])

    def test_mechanism_variants_must_keep_same_signal_definition(self) -> None:
        candidate = _mechanism_candidate_payload()
        candidate["mechanism_comparison"]["signal_only"]["new_signal_definition"]["value"] = 0.8  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "同一个新信号定义"):
            ResearchPlannerV2._validate_candidate_shape(candidate)

    def test_parameter_probe_formal_candidate_only_replaces_selected_value(self) -> None:
        planned = ResearchPlannerV2._validate_candidate_shape(_threshold_candidate_payload())
        judge = _CandidateLLM(
            [
                {
                    "decision": "formal_test",
                    "parameter_shape": "wide_stable",
                    "selected_value": 1.75,
                    "reason": "相邻值表现接近",
                    "formal_candidate": {"research_question": "偷偷改问题"},
                }
            ]
        )
        planner = ResearchPlannerV2(llm=judge, web_client=object())

        result = planner.finalize_parameter_probe(
            planned_candidate=planned,
            accepted_strategy={"params": {"volume_ratio": 2.0}},
            probe_results=[{"value": 1.75, "development_report": {"median_sharpe": 0.4}}],
        )
        formal = result["formal_candidate"]

        for field in ("research_question", "change_kind", "changed_fields", "required_data"):
            self.assertEqual(formal[field], planned[field])
        self.assertIn("1.75", formal["hypothesis"])
        self.assertIn("1.75", formal["strategy_modification"])
        self.assertNotIn("__SELECTED_VALUE__", formal["hypothesis"])
        self.assertEqual(
            formal["selected_parameter"],
            {"param_name": "volume_ratio", "value": 1.75},
        )

    def test_shared_market_dates_and_common_sample_require_contract(self) -> None:
        candidate = _candidate_payload()
        candidate["hypothesis"] = (
            "以当前股票范围内同时具有t日、t-1日和t-30日收盘价的股票为共同计算范围，"
            "计算两个收益中位数。"
        )

        with self.assertRaisesRegex(ValueError, "必须提供 calculation_contracts"):
            ResearchPlannerV2._validate_candidate_shape(candidate)

    def test_calculation_contract_records_date_and_sample_rules(self) -> None:
        candidate = _candidate_payload()
        candidate["hypothesis"] = (
            "按统一市场交易日 t、t-1、t-30 取收盘价，并用共同股票样本计算。"
        )
        candidate["calculation_contracts"] = [
            {
                "contract_id": "market_return",
                "table_key": "daily",
                "date_basis": "shared_market_trading_calendar",
                "required_dates": ["T", "T-1", "T-30"],
                "required_value_columns": ["close"],
                "allow_missing_intermediate_rows": True,
                "use_common_sample": True,
                "empty_sample_action": "condition_false",
            }
        ]

        result = ResearchPlannerV2._validate_candidate_shape(candidate)

        assert result["calculation_contracts"] == [
            {
                "contract_id": "market_return",
                "table_key": "daily",
                "date_basis": "shared_market_trading_calendar",
                "required_dates": ["t", "t-1", "t-30"],
                "required_offsets": [0, 1, 30],
                "required_value_columns": ["close"],
                "allow_missing_intermediate_rows": True,
                "use_common_sample": True,
                "empty_sample_action": "condition_false",
            }
        ]

    def test_candidate_008_wording_cannot_use_per_symbol_row_positions(self) -> None:
        candidate = _candidate_payload()
        candidate["hypothesis"] = (
            "以当前股票范围内同时具有t日、t-1日和t-30日收盘价的股票为共同计算范围。"
        )
        candidate["calculation_contracts"] = [
            {
                "contract_id": "market_return",
                "table_key": "daily",
                "date_basis": "per_symbol_observation_sequence",
                "required_dates": ["t", "t-1", "t-30"],
                "required_value_columns": ["close"],
                "allow_missing_intermediate_rows": True,
                "use_common_sample": True,
                "empty_sample_action": "condition_false",
            }
        ]

        with self.assertRaisesRegex(ValueError, "shared_market_trading_calendar"):
            ResearchPlannerV2._validate_candidate_shape(candidate)
