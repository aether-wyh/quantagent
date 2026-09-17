from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd
import pytest

import quanta_agents.workflow_v2 as workflow_v2
from quanta_agents.state import BacktestResult
from quanta_agents.v2_runtime import default_cn_daily_v2_profile
from quanta_agents.workflow_v2 import ResearchLoopV2


class FakeInterpreter:
    def run(self, source_text: str, *_args, **_kwargs):
        return {
            "original_text": source_text,
            "temporary_baseline_decisions": [],
        }


class FakeBaselineBuilder:
    def run(self, *_args, **_kwargs):
        return {
            "hypothesis": "baseline",
            "strategy_modification": "baseline",
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
                    "purpose": "test",
                }
            ],
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "candidate_mode": "baseline",
            "baseline_parameters": {"window": 30},
            "decision_map": [],
            "missing_concepts": [],
        }


class FakePlanner:
    categories = [
        "numeric_definition",
        "mechanism_signal",
        "applicability",
        "condition_necessity",
        "trade_timing",
    ]

    def __init__(self) -> None:
        self.index = 0
        self.accepted_ids_seen: list[str] = []

    def build_theories(self, *_args, **_kwargs):
        return {
            "theories": [
                {
                    "theory_id": "m1",
                    "kind": "causal",
                    "extra_predictions": ["p1", "p2"],
                },
                {
                    "theory_id": "m2",
                    "kind": "causal",
                    "extra_predictions": ["p3", "p4"],
                },
                {
                    "theory_id": "m3",
                    "kind": "causal",
                    "extra_predictions": ["p5", "p6"],
                },
                {
                    "theory_id": "m0",
                    "kind": "null",
                    "extra_predictions": ["p7", "p8"],
                },
            ]
        }

    def propose_candidate(self, *, accepted_strategy, **_kwargs):
        self.accepted_ids_seen.append(str(accepted_strategy.get("candidate_id", "")))
        category = self.categories[self.index]
        self.index += 1
        candidate = {
            "candidate_mode": "modify_one_rule",
            "category": category,
            "mechanism_id": "m1",
            "research_question": category,
            "change_kind": (
                "remove_condition"
                if category == "condition_necessity"
                else "entry_or_exit"
                if category == "trade_timing"
                else "add_signal"
                if category == "mechanism_signal"
                else "definition"
            ),
            "changed_fields": [f"field_{self.index}"],
            "strategy_modification": f"change_{self.index}",
            "hypothesis": f"hypothesis_{self.index}",
            "required_data": FakeBaselineBuilder().run()["required_data"],
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "predicted_changes": [
                {"metric": "median_sharpe", "direction": "increase", "reason": "test"}
            ],
            "judgment_is_wrong_if": "no improvement",
        }
        if category == "mechanism_signal":
            candidate["new_signal_definition"] = {"field": "candidate_field"}
            added = dict(candidate)
            added["variant_mode"] = "added_to_base"
            signal_only = dict(candidate)
            signal_only.update(
                {
                    "variant_mode": "signal_only",
                    "strategy_modification": "use_candidate_field_only",
                    "hypothesis": "candidate_field_only",
                }
            )
            candidate["mechanism_comparison"] = {
                "added_to_base": added,
                "signal_only": signal_only,
            }
        return candidate


class FakeStrategyAgent:
    def __init__(self) -> None:
        self.previous_versions: list[tuple[str, int | None]] = []

    def run(self, state):
        meta = state["hypothesis_generation_meta"]
        candidate_text = str(state["current_candidate_id"])
        previous_code = str(state.get("strategy_code", ""))
        previous_version: int | None = None
        for line in previous_code.splitlines():
            if line.startswith("VERSION = "):
                previous_version = int(line.removeprefix("VERSION = ").strip())
                break
        self.previous_versions.append((candidate_text, previous_version))
        number = int(candidate_text.split("_")[1])
        daily = pd.DataFrame(
            {
                "trade_date": pd.date_range("2020-01-02", periods=8, freq="B"),
                "close": [10.0, 10.1, 10.0, 10.2, 10.3, 10.2, 10.4, 10.5],
            }
        )
        weights = pd.DataFrame(
            {
                "trade_date": pd.to_datetime(["2020-01-02", "2020-01-03"]),
                "000001.SZ": [0.1, 0.0],
                "cash": [0.9, 1.0],
            }
        )
        strategy_code = f"""
import numpy as np
import pandas as pd
VERSION = {number}
def build_mechanism_signal(train_data_bundle, validate_data_bundle):
    frame = validate_data_bundle["daily"]
    return pd.Series(
        np.arange(len(frame)) % 2 == 0,
        index=frame.index,
    )
def output_weights(train_data_bundle, validate_data_bundle, params):
    frame = validate_data_bundle["daily"]
    new_signal = build_mechanism_signal(train_data_bundle, validate_data_bundle)
    asset = np.where(new_signal, 0.1, 0.0)
    return pd.DataFrame({{
        "trade_date": frame["trade_date"].to_numpy(),
        "000001.SZ": asset,
        "cash": 1.0 - asset,
    }})
"""
        state["strategy_code"] = strategy_code
        state["code_text"] = strategy_code
        state["strategy_result"] = {
            "output_weights": weights,
            "strategy_output": {
                "output_weights_df": {"datetime_column": "trade_date"},
            },
            "params": {"version": number},
            "required_data": meta["required_data"],
            "backtest_datasets": meta["backtest_datasets"],
            "train_data_bundle": {},
            "validate_data_bundle": {"daily": daily},
        }
        state["strategy_generation_meta"] = {
            **meta,
            "code_change_ratio": 0.1,
        }
        state["phase"] = "validate"
        return state


class FakeValidateAgent:
    def run(self, state):
        state["validation_summary"] = {"passed": True}
        state["phase"] = "test"
        return state


def report(*, passed: bool, sharpe: float) -> dict[str, object]:
    return {
        "period_kind": "development",
        "fold_count": 3,
        "passed_fold_count": 3 if passed else 2,
        "fold_pass_ratio": 1.0 if passed else 2 / 3,
        "median_annual_return": 0.08,
        "median_sharpe": sharpe,
        "worst_fold_sharpe": 0.10 if passed else -0.05,
        "worst_fold_drawdown": 0.10,
        "total_trade_count": 300,
        "beats_cash_in_all_folds": passed,
        "cost_stress_median_sharpe": 0.5,
        "cost_stress_complete": True,
        "cost_stress_passed": True,
        "delay_stress_median_sharpe": 0.4,
        "delay_stress_complete": True,
        "delay_stress_passed": True,
        "passed": passed,
        "folds": [{}, {}, {}],
    }


class FakeTester:
    def run(self, state):
        stage = state["experiment_spec"].get("stage")
        if state.get("evaluation_stage") == "final_test":
            state["test_result"] = BacktestResult(
                annual_return=0.07,
                sharpe=0.8,
                max_drawdown=-50000,
                max_ddpercent=0.05,
                trade_count=120,
                passed=True,
                summary="passed",
            )
            state["backtest_debug"] = {
                "transaction_cost_rule": {
                    "buy_rate": 0.0003,
                    "sell_rate_before_change": 0.0013,
                    "sell_rate_change_date": "2023-08-28",
                    "sell_rate_from_change": 0.0008,
                    "slippage_rate_each_side": 0.00025,
                }
            }
            state["phase"] = "test"
            return state
        if stage == "confirmation":
            candidate_number = int(str(state["current_candidate_id"]).split("_")[1])
            state["development_report"] = report(
                passed=True,
                sharpe=0.8 + candidate_number * 0.05,
            )
        else:
            candidate_number = int(str(state["current_candidate_id"]).split("_")[1])
            state["development_report"] = report(
                passed=False,
                sharpe=0.1 + candidate_number * 0.05,
            )
        state["test_result"] = BacktestResult(
            annual_return=0.05,
            sharpe=0.3,
            max_drawdown=-50000,
            passed=False,
            summary="development",
        )
        state["phase"] = "test"
        return state


class FakeJudge:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, *_args, **_kwargs):
        self.calls += 1
        adopted = self.calls == 2
        return {
            "calculation_valid": True,
            "sample_adequacy": "adequate",
            "evidence_result": "supported" if adopted else "rejected",
            "adopted": adopted,
            "adoption_kind": "relative_improvement" if adopted else "not_adopted",
            "stable_strategy": False,
            "observed_deltas": {},
            "mechanism_updates": [],
            "next_action": "continue",
        }


def test_v2_runs_all_research_categories_restores_failure_and_tests_final(
    tmp_path: Path, monkeypatch
) -> None:
    planner = FakePlanner()
    profile = default_cn_daily_v2_profile()
    # 这个通用流程夹具没有“连续N日”规则，不声明本实验专用约定。
    del profile["baseline_defaults"]["market_day_continuity_contract"]
    profile["research_budget"]["max_formal_candidates"] = 5
    profile["stability_requirements"].update(
        {
            "confirmation_min_median_sharpe": 0.5,
            "confirmation_min_median_annual_return": 0.05,
            "confirmation_min_total_trade_count": 100,
            "confirmation_min_cost_stress_sharpe": 0.0,
            "confirmation_min_delay_stress_sharpe": 0.0,
        }
    )
    monkeypatch.setattr(workflow_v2, "get_trace_run_dir", lambda _state: tmp_path)
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *a, **k: tmp_path)
    monkeypatch.setattr(
        workflow_v2,
        "check_generated_daily_position_plans",
        lambda *_args, **_kwargs: {"passed": True},
    )

    strategy_agent = FakeStrategyAgent()
    loop = ResearchLoopV2(
        interpreter=FakeInterpreter(),
        baseline_builder=FakeBaselineBuilder(),
        planner=planner,
        judge=FakeJudge(),
        strategy_agent=strategy_agent,
        validate_agent=FakeValidateAgent(),
        tester=FakeTester(),
    )
    result = loop.run(
        "一句话",
        runtime_profile=profile,
        experiment_id="v2_test",
    )

    assert result["category_coverage_complete"] is True
    assert result["covered_categories"] == FakePlanner.categories
    # 第一个候选失败后仍从基准出发；第二个候选采用后，后续从candidate_003出发。
    assert planner.accepted_ids_seen == [
        "candidate_001",
        "candidate_001",
        "candidate_003",
        "candidate_003",
        "candidate_003",
    ]
    # 机制对照必须从 added_to_base 的 VERSION=3 开始修改，不能退回已采用的 VERSION=1。
    assert ("candidate_003_signal_only", 3) in strategy_agent.previous_versions
    assert result["selected_candidate_id"] == "candidate_003"
    assert [item["candidate_id"] for item in result["confirmation_candidates"]] == [
        "candidate_003",
    ]
    assert result["confirmation_stable"] is True
    assert result["final_test_report"]["passed"] is True
    assert result["final_test_report"]["transaction_cost_rule"] == {
        "buy_rate": 0.0003,
        "sell_rate_before_change": 0.0013,
        "sell_rate_change_date": "2023-08-28",
        "sell_rate_from_change": 0.0008,
        "slippage_rate_each_side": 0.00025,
    }
    audit = result["observer_audit"]
    assert audit["questions"]["number_and_definition"]["formally_tested"] is True
    assert audit["questions"]["mechanism_and_new_signal"][
        "mechanism_linked_new_signal_tested"
    ] is True
    assert audit["questions"]["applicability_or_environment"]["formally_tested"] is True
    assert audit["observer_conclusion"]["overall_passed"] is True


def test_final_report_prefers_cost_rule_carried_by_test_result() -> None:
    final_report = workflow_v2._result_to_final_report(
        {
            "passed": True,
            "transaction_cost_rule": {"source": "test_result"},
            "backtest_debug": {
                "transaction_cost_rule": {"source": "nested_debug"}
            },
        },
        backtest_debug={
            "transaction_cost_rule": {"source": "state_debug"}
        },
    )

    assert final_report["transaction_cost_rule"] == {"source": "test_result"}


def test_final_report_does_not_invent_missing_cost_rule() -> None:
    final_report = workflow_v2._result_to_final_report(
        BacktestResult(
            annual_return=0.07,
            sharpe=0.8,
            max_drawdown=-50000,
            passed=True,
            summary="passed",
        ),
        backtest_debug={},
    )

    assert "transaction_cost_rule" not in final_report


def test_development_reports_and_saved_candidate_history_are_compact() -> None:
    large_marker = "LARGE_RECOMPUTE_DETAIL_" * 20_000
    raw_report = report(passed=False, sharpe=0.2)
    raw_report.update(
        {
            "candidate_id": "candidate_001",
            "epoch_index": 1,
            "gap_trading_days": 20,
            "date_source": "test_dates",
            "transaction_cost_rule": {"description": "实际费用"},
            "double_cost_rule": {"description": "双倍实际费用"},
            "recompute_records": [{"output_weights": large_marker}],
        }
    )
    raw_report["folds"] = [
        {
            "name": "fold_1",
            "annual_return": 0.08,
            "sharpe": 0.2,
            "trade_count": 100,
            "_target_weights_df": large_marker,
        }
    ]

    class LargeReportTester:
        def run(self, state):
            state["development_report"] = raw_report
            state["phase"] = "test"
            return state

    loop = ResearchLoopV2.__new__(ResearchLoopV2)
    loop.tester = LargeReportTester()
    state = {}
    compact = loop._run_development_test(state, experiment_spec={})

    assert compact["median_sharpe"] == 0.2
    assert compact["candidate_id"] == "candidate_001"
    assert compact["folds"][0]["trade_count"] == 100
    assert compact["transaction_cost_rule"] == {"description": "实际费用"}
    assert compact["double_cost_rule"] == {"description": "双倍实际费用"}
    assert "recompute_records" not in compact
    assert "_target_weights_df" not in compact["folds"][0]
    assert state["development_report"] == compact

    run_record = {"candidate_records": []}
    saved = ResearchLoopV2._record_candidate(
        run_record,
        {"strategy_generation_meta": {}},
        candidate_id="candidate_001",
        candidate={"category": "baseline"},
        report=raw_report,
        status="adopted",
        extra={
            "mechanism_comparison_results": {
                "signal_only": {
                    "report": raw_report,
                    "output_weights": large_marker,
                }
            }
        },
    )
    saved_text = str(saved)

    assert "LARGE_RECOMPUTE_DETAIL" not in saved_text
    assert "recompute_records" not in saved_text
    assert saved["development_report"]["median_sharpe"] == 0.2
    assert saved["development_report"]["transaction_cost_rule"] == {
        "description": "实际费用"
    }
    assert saved["mechanism_comparison_results"]["signal_only"]["report"][
        "median_sharpe"
    ] == 0.2


def test_partial_parameter_probe_reuses_checked_code_and_only_runs_missing_value(
    monkeypatch,
) -> None:
    loop = ResearchLoopV2.__new__(ResearchLoopV2)
    loop._next_epoch = 10
    monkeypatch.setattr(workflow_v2, "restore_accepted_snapshot", lambda _state: None)

    restored: list[dict[str, object]] = []

    def restore_saved(state, **kwargs):
        restored.append(kwargs)
        state["strategy_result"] = {
            "params": {
                "consolidation_std_max": 0.0105,
                "volume_multiplier": 2.0,
            }
        }

    loop._restore_saved_candidate_strategy = restore_saved
    loop._generate_and_validate = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("续跑时不应重新生成数值比较代码")
    )
    checked_probe_candidates: list[dict[str, object]] = []

    def check_probe_values(_state, probe_candidate, _experiment_spec):
        checked_probe_candidates.append(probe_candidate)
        return {
            "passed": True,
            "param_name": "consolidation_std_max",
            "checked_values": [0.0105, 0.0115, 0.0125, 0.0135, 0.0145],
        }

    loop._check_parameter_probe_values = check_probe_values

    tested: list[tuple[str, float]] = []

    def run_test(state, *, experiment_spec):
        del experiment_spec
        value = float(state["strategy_result"]["params"]["consolidation_std_max"])
        tested.append((str(state["current_candidate_id"]), value))
        return {
            **report(passed=False, sharpe=value),
            "candidate_id": state["current_candidate_id"],
            "epoch_index": state["epoch_index"],
        }

    loop._run_development_test = run_test
    candidate = {
        "hypothesis": "测试盘整波动率",
        "strategy_modification": "只改盘整波动率",
        "parameter_probe": {
            "param_name": "consolidation_std_max",
            "values": [0.0105, 0.0115, 0.0125, 0.0135, 0.0145],
        },
    }
    old_results = [
        {
            "param_name": "consolidation_std_max",
            "value": value,
            "development_report": {
                **report(passed=False, sharpe=value),
                "candidate_id": f"probe_consolidation_std_max_{index:02d}",
                "epoch_index": index + 2,
            },
        }
        for index, value in enumerate(
            [0.0105, 0.0115, 0.0125, 0.0135], start=1
        )
    ]
    progress: list[list[dict[str, object]]] = []

    state = {
        "strategy_result": {
            "params": {
                "consolidation_std_max": 0.015,
                "volume_multiplier": 2.0,
            }
        }
    }
    results = loop._run_parameter_probe(
        state,
        candidate,
        experiment_spec={},
        existing_probe_results=old_results,
        on_probe_result=lambda items: progress.append(items),
        saved_probe_code="CHECKED_CODE",
        saved_probe_generation_meta={},
        saved_probe_code_sha256="abc123",
    )

    assert len(restored) == 1
    assert restored[0]["code_text"] == "CHECKED_CODE"
    assert restored[0]["expected_hash"] == "abc123"
    assert len(checked_probe_candidates) == 1
    probe_candidate = restored[0]["candidate"]
    assert "0.0105, 0.0115, 0.0125, 0.0135, 0.0145" in probe_candidate[
        "strategy_modification"
    ]
    assert "不能写成只允许初始值0.0105" in probe_candidate[
        "strategy_modification"
    ]
    assert "不得检查该参数必须等于第一个数值" in probe_candidate["hypothesis"]
    assert tested == [("probe_consolidation_std_max_05", 0.0145)]
    assert [item["value"] for item in results] == [
        0.0105,
        0.0115,
        0.0125,
        0.0135,
        0.0145,
    ]
    assert len(progress) == 5
    assert len(progress[-1]) == 5


def test_generate_and_validate_retries_when_probe_code_only_accepts_first_value(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class ProbeStrategyAgent:
        def __init__(self) -> None:
            self.calls = 0
            self.validation_summaries: list[str] = []

        def run(self, state):
            self.calls += 1
            self.validation_summaries.append(str(state.get("validation_summary", {})))
            fixed_check = (
                "\n    if holding_days != 2.0:\n"
                "        raise ValueError('holding_days must be 2')"
                if self.calls == 1
                else ""
            )
            code = f"""
import pandas as pd
params = {{"holding_days": 2.0}}
def output_weights(train_data_bundle, validate_data_bundle, params):
    holding_days = float(params["holding_days"]){fixed_check}
    return pd.DataFrame({{"trade_date": ["2020-01-02"], "cash": [1.0]}})
output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)
strategy_output = {{
    "output_weights_df": {{
        "description": "weights",
        "datetime_column": "trade_date",
        "expected_characteristics": ["cash between zero and one"],
    }}
}}
strategy_next_phase = "validate"
strategy_decision_reason = "probe"
"""
            state["strategy_code"] = code
            state["code_text"] = code
            state["strategy_result"] = {
                "params": {"holding_days": 2.0},
                "train_data_bundle": {},
                "validate_data_bundle": {},
                "universe": [],
            }
            state["strategy_generation_meta"] = {}
            state["phase"] = "validate"
            return state

    class ProbeValidateAgent:
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state):
            self.calls += 1
            state["validation_summary"] = {"passed": True}
            state["phase"] = "test"
            return state

    strategy_agent = ProbeStrategyAgent()
    validate_agent = ProbeValidateAgent()
    loop = ResearchLoopV2.__new__(ResearchLoopV2)
    loop._next_epoch = 1
    loop.strategy_agent = strategy_agent
    loop.validate_agent = validate_agent
    loop._check_daily_future_data = lambda *_args, **_kwargs: {"passed": True}
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *a, **k: tmp_path)

    state: dict[str, object] = {}
    candidate = {
        "hypothesis": "比较持有期",
        "strategy_modification": "只改持有天数",
        "parameter_probe": {
            "param_name": "holding_days",
            "values": [2.0, 3.0, 4.0],
        },
    }
    loop._generate_and_validate(
        state,
        candidate,
        candidate_id="probe_code",
        experiment_spec={},
    )

    assert strategy_agent.calls == 2
    assert validate_agent.calls == 1
    assert "holding_days=3.0" in strategy_agent.validation_summaries[1]
    assert state["parameter_probe_value_check"] == {
        "passed": True,
        "param_name": "holding_days",
        "checked_values": [2.0, 3.0, 4.0],
    }


def test_calculation_contract_failure_rewrites_code_before_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class ContractStrategyAgent:
        def __init__(self) -> None:
            self.calls = 0
            self.feedback_seen: list[str] = []

        def run(self, state):
            self.calls += 1
            self.feedback_seen.append(str(state.get("validation_summary", {})))
            state["strategy_code"] = "def output_weights(*args):\n    return None"
            state["code_text"] = state["strategy_code"]
            state["strategy_result"] = {
                "params": {},
                "train_data_bundle": {},
                "validate_data_bundle": {},
            }
            state["strategy_generation_meta"] = {}
            state["phase"] = "validate"
            return state

    class ContractValidateAgent:
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state):
            self.calls += 1
            state["phase"] = "test"
            return state

    checks = 0

    def check_contract(_code, _contracts):
        nonlocal checks
        checks += 1
        if checks == 1:
            raise workflow_v2.CalculationContractError("中间缺行股票被错误排除")
        return {"passed": True, "checked_contracts": []}

    strategy_agent = ContractStrategyAgent()
    validate_agent = ContractValidateAgent()
    loop = ResearchLoopV2.__new__(ResearchLoopV2)
    loop._next_epoch = 1
    loop.strategy_agent = strategy_agent
    loop.validate_agent = validate_agent
    loop._check_daily_future_data = lambda *_args, **_kwargs: {"passed": True}
    monkeypatch.setattr(workflow_v2, "check_generated_calculation_contracts", check_contract)
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *a, **k: tmp_path)

    state: dict[str, object] = {}
    loop._generate_and_validate(
        state,
        {
            "hypothesis": "共同样本",
            "strategy_modification": "按精确日期取样",
            "calculation_contracts": [{"contract_id": "market_return"}],
        },
        candidate_id="contract_candidate",
        experiment_spec={},
    )

    assert strategy_agent.calls == 2
    assert validate_agent.calls == 1
    assert "中间缺行股票被错误排除" in strategy_agent.feedback_seen[1]
    assert state["calculation_contract_check"]["passed"] is True


def test_consecutive_market_day_failure_rewrites_code_before_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class ConsecutiveStrategyAgent:
        def __init__(self) -> None:
            self.calls = 0
            self.feedback_seen: list[str] = []

        def run(self, state):
            self.calls += 1
            self.feedback_seen.append(str(state.get("validation_summary", {})))
            state["strategy_code"] = "def output_weights(*args):\n    return None"
            state["code_text"] = state["strategy_code"]
            state["strategy_result"] = {
                "params": {},
                "train_data_bundle": {},
                "validate_data_bundle": {},
            }
            state["strategy_generation_meta"] = {}
            state["phase"] = "validate"
            return state

    class ConsecutiveValidateAgent:
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state):
            self.calls += 1
            state["phase"] = "test"
            return state

    checks = 0

    def check_consecutive(_code, _candidate, *, continuity_contract=None):
        nonlocal checks
        assert continuity_contract is None
        checks += 1
        if checks == 1:
            raise workflow_v2.CalculationContractError(
                "缺少紧邻市场日K线时不能退到更早一条股票记录"
            )
        return {"passed": True, "checked_requirements": [{"consecutive_days": 2}]}

    strategy_agent = ConsecutiveStrategyAgent()
    validate_agent = ConsecutiveValidateAgent()
    loop = ResearchLoopV2.__new__(ResearchLoopV2)
    loop._next_epoch = 1
    loop.strategy_agent = strategy_agent
    loop.validate_agent = validate_agent
    loop._check_daily_future_data = lambda *_args, **_kwargs: {"passed": True}
    monkeypatch.setattr(
        workflow_v2,
        "check_generated_consecutive_market_days",
        check_consecutive,
    )
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *a, **k: tmp_path)

    state: dict[str, object] = {}
    loop._generate_and_validate(
        state,
        {
            "hypothesis": "连续两天放量，第二天形成信号",
            "strategy_modification": "按实际交易日检查",
        },
        candidate_id="consecutive_candidate",
        experiment_spec={},
    )

    assert strategy_agent.calls == 2
    assert validate_agent.calls == 1
    assert "缺少紧邻市场日K线" in strategy_agent.feedback_seen[1]
    assert state["consecutive_market_day_check"]["passed"] is True


def test_mechanism_signal_failure_rewrites_before_other_checks_or_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class MechanismStrategyAgent:
        def __init__(self) -> None:
            self.calls = 0
            self.feedback_seen: list[str] = []

        def run(self, state):
            self.calls += 1
            self.feedback_seen.append(str(state.get("validation_summary", {})))
            state["strategy_code"] = "def output_weights(*args):\n    return None"
            state["code_text"] = state["strategy_code"]
            state["strategy_result"] = {
                "params": {},
                "train_data_bundle": {},
                "validate_data_bundle": {},
            }
            state["strategy_generation_meta"] = dict(
                state["hypothesis_generation_meta"]
            )
            state["phase"] = "validate"
            return state

    class MechanismValidateAgent:
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state):
            self.calls += 1
            state["phase"] = "test"
            return state

    mechanism_checks = 0

    def check_mechanism(
        _code,
        _strategy_result,
        *,
        reference_source=None,
        event_mode=False,
    ):
        nonlocal mechanism_checks
        assert reference_source == "主版本新信号定义"
        assert event_mode is False
        mechanism_checks += 1
        if mechanism_checks == 1:
            raise workflow_v2.MechanismSignalValidationError(
                "D1.high 的 >= 被改成 >，并漏掉 D1.close <= U"
            )
        return {"passed": True, "definition_matches_added_to_base": True}

    future_checks = 0

    def check_future(*_args, **_kwargs):
        nonlocal future_checks
        future_checks += 1
        return {"passed": True}

    strategy_agent = MechanismStrategyAgent()
    validate_agent = MechanismValidateAgent()
    loop = ResearchLoopV2.__new__(ResearchLoopV2)
    loop._next_epoch = 1
    loop.strategy_agent = strategy_agent
    loop.validate_agent = validate_agent
    loop._check_daily_future_data = check_future
    monkeypatch.setattr(
        workflow_v2,
        "check_generated_mechanism_signal",
        check_mechanism,
    )
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *a, **k: tmp_path)

    state: dict[str, object] = {}
    loop._generate_and_validate(
        state,
        {
            "category": "mechanism_signal",
            "variant_mode": "replace_related_rule",
            "new_signal_definition": {"formula": "统一定义"},
            "hypothesis": "机制对照",
            "strategy_modification": "只替换相关旧条件",
        },
        candidate_id="candidate_007_replace_related_rule",
        experiment_spec={},
        mechanism_signal_reference_source="主版本新信号定义",
    )

    assert strategy_agent.calls == 2
    assert mechanism_checks == 2
    assert future_checks == 1
    assert validate_agent.calls == 1
    assert "漏掉 D1.close <= U" in strategy_agent.feedback_seen[1]
    assert state["mechanism_signal_check"]["passed"] is True


def test_formal_parameter_candidate_can_be_saved_without_recursive_reference() -> None:
    formal = {"hypothesis": "正式候选", "selected_parameter": {"value": 0.0125}}
    decision = {
        "decision": "formal_test",
        "selected_value": 0.0125,
        "formal_candidate": formal,
    }

    candidate = workflow_v2._formal_candidate_from_probe_decision(
        decision,
        [{"value": 0.0125, "development_report": {"median_sharpe": 1.0}}],
    )

    assert "formal_candidate" not in candidate["probe_decision"]
    assert candidate["probe_decision"]["selected_value"] == 0.0125
    json.dumps(workflow_v2._json_safe(candidate), ensure_ascii=False)


def _write_completed_selected_resume_fixture(tmp_path: Path) -> Path:
    run_dir = tmp_path / "old_v2_run"
    code_dir = run_dir / "epoch_004" / "strategyagent" / "round_001"
    meta_dir = code_dir / "structured_output"
    validation_dir = (
        run_dir
        / "epoch_004"
        / "validateagent"
        / "round_001"
        / "structured_output"
    )
    meta_dir.mkdir(parents=True)
    validation_dir.mkdir(parents=True)

    code_text = (
        "import pandas as pd\n"
        "params = {'version': 2}\n"
        "def output_weights(train_data_bundle, validate_data_bundle, params):\n"
        "    return pd.DataFrame({'trade_date': ['2020-01-02'], 'cash': [1.0]})\n"
        "output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)\n"
        "strategy_output = {'output_weights_df': {'datetime_column': 'trade_date'}}\n"
        "strategy_next_phase = 'validate'\n"
        "strategy_decision_reason = 'selected research code'\n"
    )
    code_path = code_dir / "step_01_selected.py"
    code_path.write_text(code_text, encoding="utf-8")
    code_sha = hashlib.sha256(code_text.encode("utf-8")).hexdigest()
    generation_meta = {
        "hypothesis": "selected research hypothesis",
        "strategy_modification": "selected research change",
        "candidate_mode": "modify_one_rule",
        "required_data": FakeBaselineBuilder().run()["required_data"],
        "backtest_datasets": ["vnpy_stock_daily_qfq"],
    }
    (meta_dir / "meta.json").write_text(
        json.dumps(
            {"payload": {"strategy_generation_meta": generation_meta}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (validation_dir / "validation.json").write_text(
        json.dumps(
            {
                "payload": {
                    "validation_summary": {
                        "passed": True,
                        "strategy_code_sha256": code_sha,
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    selected_report = {
        **report(passed=False, sharpe=0.82),
        "candidate_id": "candidate_002",
        "epoch_index": 4,
    }
    records: list[dict[str, object]] = []
    for number in range(1, 9):
        candidate_id = f"candidate_{number:03d}"
        candidate_report = {
            **report(passed=False, sharpe=0.1 + number / 100),
            "candidate_id": candidate_id,
            "epoch_index": number + 2,
        }
        if number == 2:
            candidate_report = selected_report
        status = "adopted" if number in {1, 2} else "rejected"
        if number == 8:
            status = "technical_failure"
        records.append(
            {
                "candidate_id": candidate_id,
                "category": "baseline" if number == 1 else "applicability",
                "research_category": (
                    "baseline" if number == 1 else "applicability"
                ),
                "status": status,
                "adopted": status == "adopted",
                "development_report": candidate_report,
                "confirmation_report": {
                    "marker": "CONFIRMATION_SECRET_IN_HISTORY"
                },
            }
        )

    runtime_profile = default_cn_daily_v2_profile()
    del runtime_profile["baseline_defaults"]["market_day_continuity_contract"]
    old_record = {
        "schema_version": "research_loop_v2",
        "experiment_id": "old_completed_v2",
        "source_text": "一句测试想法",
        "runtime_profile": runtime_profile,
        "finished_at": "2026-08-14T00:00:00+00:00",
        "input_interpretation": {"original_text": "一句测试想法"},
        "theory_book": {"theories": [{"theory_id": "old_theory"}]},
        "candidate_records": records,
        "planned_candidates": [
            {
                "candidate_id": "candidate_002",
                "category": "applicability",
                **generation_meta,
            }
        ],
        "selected_candidate_id": "candidate_002",
        "selected_research_report": selected_report,
        "selected_development_report": {
            "marker": "CONFIRMATION_SECRET_SELECTED_DEVELOPMENT"
        },
        "covered_categories": [
            "numeric_definition",
            "mechanism_signal",
            "applicability",
            "condition_necessity",
            "trade_timing",
        ],
        "confirmation_report": {"marker": "CONFIRMATION_SECRET_TOP_LEVEL"},
        "final_test_report": {"marker": "FINAL_SECRET_TOP_LEVEL"},
    }
    result_path = run_dir / "research_loop_v2_result.json"
    result_path.write_text(
        json.dumps(old_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result_path


def _write_selected_resume_of_resume_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, Path, str]:
    source_result_path = _write_completed_selected_resume_fixture(tmp_path)
    source_record = json.loads(source_result_path.read_text(encoding="utf-8"))
    source_code_path = (
        source_result_path.parent
        / "epoch_004"
        / "strategyagent"
        / "round_001"
        / "step_01_selected.py"
    ).resolve()
    source_code_sha = hashlib.sha256(
        source_code_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()

    continued_dir = tmp_path / "continued_v2_run"
    (continued_dir / "epoch_001").mkdir(parents=True)
    continued_record = json.loads(json.dumps(source_record, ensure_ascii=False))
    continued_record["experiment_id"] = "continued_v2"
    continued_record.pop("finished_at", None)
    continued_record["candidate_records"] = continued_record[
        "candidate_records"
    ][:7]
    categories = {
        "candidate_002": "mechanism_signal",
        "candidate_003": "numeric_definition",
        "candidate_004": "applicability",
        "candidate_005": "condition_necessity",
        "candidate_006": "trade_timing",
        "candidate_007": "mechanism_signal",
    }
    for row in continued_record["candidate_records"]:
        candidate_id = str(row["candidate_id"])
        if candidate_id not in categories:
            continue
        row["category"] = categories[candidate_id]
        row["research_category"] = categories[candidate_id]
    continued_record["covered_categories"] = []
    continued_record["resumed_selected_from"] = {
        "experiment_id": source_record["experiment_id"],
        "result_path": str(source_result_path.resolve()),
        "selected_candidate_id": source_record["selected_candidate_id"],
        "strategy_code_path": str(source_code_path),
        "strategy_code_sha256": source_code_sha,
        "selected_research_report_reused": True,
        "old_confirmation_reused": False,
        "old_final_test_reused": False,
        "source_finished_at": source_record["finished_at"],
        "source_was_stopped": False,
        "additional_candidates": 5,
    }
    continued_result_path = continued_dir / "research_loop_v2_result.json"
    continued_result_path.write_text(
        json.dumps(continued_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return (
        continued_result_path,
        source_result_path,
        source_code_path,
        source_code_sha,
    )


def test_selected_resume_restores_exact_checked_code_and_research_only_history(
    tmp_path: Path,
) -> None:
    result_path = _write_completed_selected_resume_fixture(tmp_path)

    bundle = ResearchLoopV2._load_selected_candidate_resume_bundle(result_path)

    expected_sha = hashlib.sha256(
        str(bundle["strategy_code"]).encode("utf-8")
    ).hexdigest()
    assert bundle["selected_candidate_id"] == "candidate_002"
    assert bundle["strategy_code_sha256"] == expected_sha
    assert Path(str(bundle["strategy_code_path"])).name == "step_01_selected.py"
    assert bundle["selected_research_report"]["median_sharpe"] == 0.82
    assert bundle["next_candidate_number"] == 9
    assert bundle["source_was_stopped"] is False
    history_text = json.dumps(bundle["candidate_history"], ensure_ascii=False)
    assert "confirmation_report" not in history_text
    assert "CONFIRMATION_SECRET" not in history_text
    assert "FINAL_SECRET" not in history_text


def test_selected_resume_can_continue_from_a_previous_continuation(
    tmp_path: Path,
) -> None:
    (
        continued_result_path,
        _source_result_path,
        source_code_path,
        source_code_sha,
    ) = _write_selected_resume_of_resume_fixture(tmp_path)

    bundle = ResearchLoopV2._load_selected_candidate_resume_bundle(
        continued_result_path,
        allow_stopped=True,
    )

    assert bundle["source_result_path"] == str(continued_result_path.resolve())
    assert bundle["source_experiment_id"] == "continued_v2"
    assert bundle["source_was_stopped"] is True
    assert bundle["selected_candidate_id"] == "candidate_002"
    assert bundle["strategy_code_path"] == str(source_code_path)
    assert bundle["strategy_code_sha256"] == source_code_sha
    assert bundle["next_candidate_number"] == 8
    assert bundle["covered_categories"] == [
        "mechanism_signal",
        "numeric_definition",
        "applicability",
        "condition_necessity",
        "trade_timing",
    ]
    assert [row["candidate_id"] for row in bundle["candidate_history"]] == [
        f"candidate_{number:03d}" for number in range(1, 8)
    ]


@pytest.mark.parametrize(
    ("changed_field", "error_text"),
    [
        ("selected_candidate_id", "入选候选编号与来源结果不一致"),
        ("strategy_code_sha256", "策略代码 SHA 与来源结果不一致"),
        ("strategy_code_path", "策略代码路径与来源结果不一致"),
        ("experiment_id", "实验编号与来源结果不一致"),
    ],
)
def test_selected_resume_rejects_tampered_continuation_source(
    tmp_path: Path,
    changed_field: str,
    error_text: str,
) -> None:
    continued_result_path, _source_path, _code_path, _code_sha = (
        _write_selected_resume_of_resume_fixture(tmp_path)
    )
    record = json.loads(continued_result_path.read_text(encoding="utf-8"))
    changed_values = {
        "selected_candidate_id": "candidate_003",
        "strategy_code_sha256": "0" * 64,
        "strategy_code_path": str((tmp_path / "forged_strategy.py").resolve()),
        "experiment_id": "forged_experiment",
    }
    record["resumed_selected_from"][changed_field] = changed_values[
        changed_field
    ]
    continued_result_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=error_text):
        ResearchLoopV2._load_selected_candidate_resume_bundle(
            continued_result_path,
            allow_stopped=True,
        )


def test_selected_resume_rejects_continuation_source_cycle(tmp_path: Path) -> None:
    continued_result_path, _source_path, _code_path, _code_sha = (
        _write_selected_resume_of_resume_fixture(tmp_path)
    )
    record = json.loads(continued_result_path.read_text(encoding="utf-8"))
    record["resumed_selected_from"]["result_path"] = str(
        continued_result_path.resolve()
    )
    record["resumed_selected_from"]["experiment_id"] = record["experiment_id"]
    record["resumed_selected_from"]["source_finished_at"] = ""
    record["resumed_selected_from"]["source_was_stopped"] = True
    continued_result_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="续跑来源形成循环"):
        ResearchLoopV2._load_selected_candidate_resume_bundle(
            continued_result_path,
            allow_stopped=True,
        )


def test_selected_resume_rejects_failed_candidate_as_start(tmp_path: Path) -> None:
    result_path = _write_completed_selected_resume_fixture(tmp_path)
    old_record = json.loads(result_path.read_text(encoding="utf-8"))
    old_record["selected_candidate_id"] = "candidate_008"
    result_path.write_text(
        json.dumps(old_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="不是研究期已采用候选"):
        ResearchLoopV2._load_selected_candidate_resume_bundle(result_path)


def test_selected_resume_requires_explicit_permission_for_stopped_run(
    tmp_path: Path,
) -> None:
    result_path = _write_completed_selected_resume_fixture(tmp_path)
    old_record = json.loads(result_path.read_text(encoding="utf-8"))
    old_record.pop("finished_at")
    old_record["candidate_records"] = old_record["candidate_records"][:6]
    categories = {
        "candidate_002": "mechanism_signal",
        "candidate_003": "numeric_definition",
        "candidate_004": "applicability",
        "candidate_005": "condition_necessity",
        "candidate_006": "trade_timing",
    }
    for row in old_record["candidate_records"]:
        candidate_id = str(row["candidate_id"])
        if candidate_id not in categories:
            continue
        row["category"] = categories[candidate_id]
        row["research_category"] = categories[candidate_id]
    old_record["covered_categories"] = []
    old_record["planned_candidates"].append(
        {
            "candidate_id": "candidate_007",
            "category": "mechanism_signal",
            "unfinished_marker": "DO_NOT_RESUME_THIS_PLAN",
        }
    )
    result_path.write_text(
        json.dumps(old_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="只能从已经完成"):
        ResearchLoopV2._load_selected_candidate_resume_bundle(result_path)

    bundle = ResearchLoopV2._load_selected_candidate_resume_bundle(
        result_path,
        allow_stopped=True,
    )

    assert bundle["source_was_stopped"] is True
    assert bundle["next_candidate_number"] == 7
    assert bundle["covered_categories"] == [
        "mechanism_signal",
        "numeric_definition",
        "applicability",
        "condition_necessity",
        "trade_timing",
    ]
    history_text = json.dumps(bundle["candidate_history"], ensure_ascii=False)
    assert "candidate_007" not in history_text
    assert "DO_NOT_RESUME_THIS_PLAN" not in history_text


def test_stopped_selected_resume_permission_requires_result_path() -> None:
    loop = ResearchLoopV2.__new__(ResearchLoopV2)

    with pytest.raises(
        ValueError,
        match="allow_stopped_selected_resume 只能和",
    ):
        loop.run(
            "一句测试想法",
            allow_stopped_selected_resume=True,
        )


def test_selected_resume_continues_numbering_without_retesting_old_candidates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result_path = _write_completed_selected_resume_fixture(tmp_path)
    new_run_dir = tmp_path / "new_v2_run"
    new_run_dir.mkdir()
    planner_calls: list[dict[str, object]] = []

    class ContinuePlanner:
        def __init__(self) -> None:
            self.index = 0

        def propose_candidate(self, **kwargs):
            planner_calls.append(kwargs)
            self.index += 1
            return {
                "candidate_mode": "modify_one_rule",
                "category": "applicability",
                "mechanism_id": "old_theory",
                "research_question": f"new question {self.index}",
                "change_kind": "definition",
                "changed_fields": [f"new_field_{self.index}"],
                "strategy_modification": f"new change {self.index}",
                "hypothesis": f"new hypothesis {self.index}",
                "required_data": FakeBaselineBuilder().run()["required_data"],
                "backtest_datasets": ["vnpy_stock_daily_qfq"],
                "predicted_changes": [],
                "judgment_is_wrong_if": "no improvement",
            }

    class RejectJudge:
        def run(self, *_args, **_kwargs):
            return {
                "calculation_valid": True,
                "sample_adequacy": "adequate",
                "evidence_result": "rejected",
                "adopted": False,
                "adoption_kind": "not_adopted",
                "stable_strategy": False,
                "observed_deltas": {},
                "mechanism_updates": [],
                "next_action": "continue",
            }

    class TrackingTester(FakeTester):
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def run(self, state):
            self.calls.append(
                (
                    str(state["experiment_spec"].get("stage", "")),
                    str(state["current_candidate_id"]),
                )
            )
            return super().run(state)

    tester = TrackingTester()
    planner = ContinuePlanner()
    monkeypatch.setattr(
        workflow_v2,
        "get_trace_run_dir",
        lambda _state: new_run_dir,
    )
    monkeypatch.setattr(
        workflow_v2,
        "write_trace_json",
        lambda *args, **kwargs: new_run_dir,
    )
    loop = ResearchLoopV2(
        interpreter=FakeInterpreter(),
        baseline_builder=FakeBaselineBuilder(),
        planner=planner,
        judge=RejectJudge(),
        strategy_agent=FakeStrategyAgent(),
        validate_agent=FakeValidateAgent(),
        tester=tester,
    )
    restored_hashes: list[str] = []

    def restore_selected(state, **kwargs):
        restored_hashes.append(str(kwargs["expected_hash"]))
        candidate = dict(kwargs["candidate"])
        state["current_candidate_id"] = kwargs["candidate_id"]
        state["hypothesis_generation_meta"] = candidate
        state["strategy_generation_meta"] = {
            **dict(kwargs["saved_generation_meta"]),
            "strategy_code_sha256": kwargs["expected_hash"],
        }
        state["strategy_code"] = kwargs["code_text"]
        state["code_text"] = kwargs["code_text"]
        state["strategy_result"] = {
            "params": {"version": 2},
            "required_data": candidate["required_data"],
            "backtest_datasets": candidate["backtest_datasets"],
            "train_data_bundle": {},
            "validate_data_bundle": {},
        }
        state["phase"] = "test"

    loop._restore_saved_candidate_strategy = restore_selected
    loop._check_daily_future_data = lambda *_args, **_kwargs: {"passed": True}
    profile = default_cn_daily_v2_profile()
    # 恢复流程夹具的假设没有“连续N日”规则。
    del profile["baseline_defaults"]["market_day_continuity_contract"]
    result = loop.run(
        "一句测试想法",
        runtime_profile=profile,
        experiment_id="new_continued_v2",
        run_final_if_confirmed=False,
        resume_selected_from_result=result_path,
        additional_candidates=2,
    )

    assert restored_hashes == [
        result["resumed_selected_from"]["strategy_code_sha256"]
    ]
    assert [item["candidate_id"] for item in result["planned_candidates"]] == [
        "candidate_009",
        "candidate_010",
    ]
    assert [item["candidate_id"] for item in result["candidate_records"]] == [
        *(f"candidate_{number:03d}" for number in range(1, 9)),
        "candidate_009",
        "candidate_010",
    ]
    research_calls = [item for item in tester.calls if item[0] == "research"]
    confirmation_calls = [
        item for item in tester.calls if item[0] == "confirmation"
    ]
    assert research_calls == [
        ("research", "candidate_009"),
        ("research", "candidate_010"),
    ]
    assert confirmation_calls == [("confirmation", "candidate_002")]
    assert len(planner_calls) == 2
    assert all(
        call["development_report"]["median_sharpe"] == 0.82
        for call in planner_calls
    )
    planner_text = json.dumps(planner_calls, ensure_ascii=False, default=str)
    assert "CONFIRMATION_SECRET" not in planner_text
    assert "FINAL_SECRET" not in planner_text
    assert all(
        call["accepted_strategy"]["candidate_id"] == "candidate_002"
        for call in planner_calls
    )


def test_selected_resume_with_zero_candidates_runs_confirmation_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result_path = _write_completed_selected_resume_fixture(tmp_path)
    old_record = json.loads(result_path.read_text(encoding="utf-8"))
    selected_record = next(
        item
        for item in old_record["candidate_records"]
        if item["candidate_id"] == "candidate_004"
    )
    selected_record["status"] = "adopted"
    selected_record["adopted"] = True
    selected_record["development_report"]["epoch_index"] = 4
    old_record["selected_candidate_id"] = "candidate_004"
    old_record["selected_research_report"] = selected_record[
        "development_report"
    ]
    selected_plan = dict(old_record["planned_candidates"][0])
    selected_plan["candidate_id"] = "candidate_004"
    old_record["planned_candidates"].append(selected_plan)
    for number in range(9, 12):
        candidate_id = f"candidate_{number:03d}"
        old_record["candidate_records"].append(
            {
                "candidate_id": candidate_id,
                "category": "applicability",
                "research_category": "applicability",
                "status": "rejected",
                "adopted": False,
                "development_report": {
                    **report(passed=False, sharpe=0.1),
                    "candidate_id": candidate_id,
                    "epoch_index": number + 2,
                },
            }
        )
    result_path.write_text(
        json.dumps(old_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    new_run_dir = tmp_path / "confirmation_only_v2_run"
    new_run_dir.mkdir()
    monkeypatch.setattr(
        workflow_v2,
        "get_trace_run_dir",
        lambda _state: new_run_dir,
    )
    monkeypatch.setattr(
        workflow_v2,
        "write_trace_json",
        lambda *args, **kwargs: new_run_dir,
    )

    class NoCandidatePlanner:
        def __init__(self) -> None:
            self.calls = 0

        def propose_candidate(self, **_kwargs):
            self.calls += 1
            raise AssertionError("候选数量为 0 时不应调用计划器")

    class TrackingTester(FakeTester):
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def run(self, state):
            self.calls.append(
                (
                    str(state["experiment_spec"].get("stage", "")),
                    str(state["current_candidate_id"]),
                )
            )
            result = super().run(state)
            if state["experiment_spec"].get("stage") == "confirmation":
                state["development_report"][
                    "delay_stress_median_sharpe"
                ] = 0.6
            return result

    planner = NoCandidatePlanner()
    tester = TrackingTester()
    loop = ResearchLoopV2(
        interpreter=FakeInterpreter(),
        baseline_builder=FakeBaselineBuilder(),
        planner=planner,
        judge=FakeJudge(),
        strategy_agent=FakeStrategyAgent(),
        validate_agent=FakeValidateAgent(),
        tester=tester,
    )

    def restore_selected(state, **kwargs):
        candidate = dict(kwargs["candidate"])
        state["current_candidate_id"] = kwargs["candidate_id"]
        state["hypothesis_generation_meta"] = candidate
        state["strategy_generation_meta"] = {
            **dict(kwargs["saved_generation_meta"]),
            "strategy_code_sha256": kwargs["expected_hash"],
        }
        state["strategy_code"] = kwargs["code_text"]
        state["code_text"] = kwargs["code_text"]
        state["strategy_result"] = {
            "params": {"version": 2},
            "required_data": candidate["required_data"],
            "backtest_datasets": candidate["backtest_datasets"],
            "train_data_bundle": {},
            "validate_data_bundle": {},
        }
        state["phase"] = "test"

    loop._restore_saved_candidate_strategy = restore_selected
    loop._check_daily_future_data = lambda *_args, **_kwargs: {"passed": True}
    profile = default_cn_daily_v2_profile()
    del profile["baseline_defaults"]["market_day_continuity_contract"]
    result = loop.run(
        "一句测试想法",
        runtime_profile=profile,
        experiment_id="confirmation_only_v2",
        run_final_if_confirmed=False,
        resume_selected_from_result=result_path,
        additional_candidates=0,
    )

    assert planner.calls == 0
    assert tester.calls == [("confirmation", "candidate_004")]
    assert result["planned_candidates"] == []
    assert [item["candidate_id"] for item in result["candidate_records"]] == [
        f"candidate_{number:03d}" for number in range(1, 12)
    ]
    assert result["selected_candidate_id"] == "candidate_004"
    assert result["resumed_selected_from"]["additional_candidates"] == 0
    assert result["confirmation_stable"] is True
    assert result["confirmation_candidates"][0]["candidate_id"] == (
        "candidate_004"
    )
    assert result["final_test_report"] == {}


def _fresh_rule_fix_report(
    candidate_id: str,
    epoch_index: int,
    *,
    sharpe: float,
) -> dict[str, object]:
    value = report(passed=False, sharpe=sharpe)
    value.update(
        {
            "candidate_id": candidate_id,
            "epoch_index": epoch_index,
            "fold_count": 4,
            "passed_fold_count": 2,
            "fold_pass_ratio": 0.5,
            "folds": [
                {
                    "name": f"development_fold_{index:02d}",
                    "period_kind": "development",
                    "seen_period": True,
                }
                for index in range(1, 5)
            ],
        }
    )
    return value


def _write_rule_fix_recheck_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, Path, dict[str, object]]:
    run_dir = tmp_path / "old_rule_fix_run"
    profile = default_cn_daily_v2_profile()
    del profile["baseline_defaults"]["market_day_continuity_contract"]
    baseline = FakeBaselineBuilder().run()
    baseline.update(
        {
            "category": "baseline",
            "hypothesis": "完整的candidate_001基准定义",
            "strategy_modification": "完整的candidate_001基准实现",
        }
    )
    candidate_004 = {
        **FakeBaselineBuilder().run(),
        "candidate_id": "candidate_004",
        "candidate_mode": "modify_one_rule",
        "category": "applicability",
        "mechanism_id": "old_theory",
        "research_question": "小流通市值是否改善表现",
        "change_kind": "add_filter",
        "changed_fields": ["float_market_cap"],
        "hypothesis": "完整的candidate_004小流通市值计划",
        "strategy_modification": "只增加当日流通市值不高于中位数条件",
        "predicted_changes": [],
    }

    def write_checked_code(
        *,
        epoch_index: int,
        version: int,
        generation_meta: dict[str, object],
    ) -> Path:
        code_dir = (
            run_dir
            / f"epoch_{epoch_index:03d}"
            / "strategyagent"
            / "round_001"
        )
        validation_dir = (
            run_dir
            / f"epoch_{epoch_index:03d}"
            / "validateagent"
            / "round_001"
            / "structured_output"
        )
        (code_dir / "structured_output").mkdir(parents=True)
        validation_dir.mkdir(parents=True)
        code_text = (
            "import pandas as pd\n"
            f"OLD_VERSION = {version}\n"
            f"params = {{'version': {version}}}\n"
            "def output_weights(train_data_bundle, validate_data_bundle, params):\n"
            "    return pd.DataFrame({'trade_date': ['2020-01-02'], 'cash': [1.0]})\n"
            "output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)\n"
            "strategy_output = {'output_weights_df': {'datetime_column': 'trade_date'}}\n"
            "strategy_next_phase = 'validate'\n"
            "strategy_decision_reason = 'old checked code'\n"
        )
        code_path = code_dir / f"step_01_candidate_{version:03d}.py"
        code_path.write_text(code_text, encoding="utf-8")
        code_sha = hashlib.sha256(code_text.encode("utf-8")).hexdigest()
        (code_dir / "structured_output" / "meta.json").write_text(
            json.dumps(
                {"payload": {"strategy_generation_meta": generation_meta}},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (validation_dir / "validation.json").write_text(
            json.dumps(
                {
                    "payload": {
                        "validation_summary": {
                            "passed": True,
                            "strategy_code_sha256": code_sha,
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return code_path

    baseline_code_path = write_checked_code(
        epoch_index=1,
        version=1,
        generation_meta=baseline,
    )
    candidate_004_code_path = write_checked_code(
        epoch_index=4,
        version=4,
        generation_meta=candidate_004,
    )
    baseline_trace_dir = (
        run_dir / "epoch_001" / "baselinebuilderv2" / "structured_output"
    )
    baseline_trace_dir.mkdir(parents=True)
    (baseline_trace_dir / "baseline.json").write_text(
        json.dumps({"payload": baseline}, ensure_ascii=False),
        encoding="utf-8",
    )

    categories = {
        1: "baseline",
        2: "mechanism_signal",
        3: "numeric_definition",
        4: "applicability",
        5: "condition_necessity",
        6: "trade_timing",
        7: "mechanism_signal",
    }
    records: list[dict[str, object]] = []
    for number, category in categories.items():
        candidate_id = f"candidate_{number:03d}"
        old_report = _fresh_rule_fix_report(
            candidate_id,
            number if number in {1, 4} else number + 4,
            sharpe=8.0 + number,
        )
        status = "adopted" if number in {1, 4} else "rejected"
        records.append(
            {
                "candidate_id": candidate_id,
                "category": category,
                "research_category": category,
                "status": status,
                "adopted": status == "adopted",
                "development_report": old_report,
                "judge_result": {
                    "adopted": status == "adopted",
                    "observed_deltas": {"old_secret_metric": number},
                },
                "change_spec": {"strategy_modification": f"old change {number}"},
            }
        )
    selected_report = next(
        item["development_report"]
        for item in records
        if item["candidate_id"] == "candidate_004"
    )
    old_record = {
        "schema_version": "research_loop_v2",
        "experiment_id": "old_rule_fix_v2",
        "source_text": "一句测试想法",
        "runtime_profile": profile,
        "input_interpretation": {"original_text": "一句测试想法"},
        "theory_book": {"theories": [{"theory_id": "old_theory"}]},
        "candidate_records": records,
        "planned_candidates": [candidate_004],
        "selected_candidate_id": "candidate_004",
        "selected_research_report": selected_report,
        "confirmation_report": {"marker": "OLD_CONFIRMATION_MUST_NOT_BE_USED"},
        "final_test_report": {"marker": "OLD_FINAL_MUST_NOT_BE_USED"},
    }
    result_path = run_dir / "research_loop_v2_result.json"
    result_path.write_text(
        json.dumps(old_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result_path, baseline_code_path, candidate_004_code_path, profile


def test_rule_fix_recheck_rejects_tampered_checked_sha(tmp_path: Path) -> None:
    result_path, _baseline_code, candidate_004_code, _profile = (
        _write_rule_fix_recheck_fixture(tmp_path)
    )
    candidate_004_code.write_text(
        candidate_004_code.read_text(encoding="utf-8") + "\n# tampered\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="无法唯一找到与旧候选代码 SHA 一致"):
        ResearchLoopV2._load_rule_fix_recheck_bundle(result_path)


def test_rule_fix_recheck_requires_complete_candidate_004_plan(
    tmp_path: Path,
) -> None:
    result_path, _baseline_code, _candidate_004_code, _profile = (
        _write_rule_fix_recheck_fixture(tmp_path)
    )
    old_record = json.loads(result_path.read_text(encoding="utf-8"))
    old_record["planned_candidates"] = []
    result_path.write_text(
        json.dumps(old_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="缺少 candidate_004 完整计划"):
        ResearchLoopV2._load_rule_fix_recheck_bundle(result_path)


class RuleFixPlanner:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def propose_candidate(self, **kwargs):
        self.calls.append(kwargs)
        return {
            **FakeBaselineBuilder().run(),
            "candidate_mode": "modify_one_rule",
            "category": "applicability",
            "mechanism_id": "old_theory",
            "research_question": "008继续研究",
            "change_kind": "definition",
            "changed_fields": ["candidate_008_field"],
            "strategy_modification": "candidate_008 change",
            "hypothesis": "candidate_008 hypothesis",
            "predicted_changes": [],
            "judgment_is_wrong_if": "no improvement",
        }


class RuleFixJudge:
    def __init__(self, *, adopt_candidate_004: bool) -> None:
        self.adopt_candidate_004 = adopt_candidate_004
        self.calls: list[tuple[str, str]] = []

    def run(self, baseline_report, candidate_report, *_args, **_kwargs):
        baseline_id = str(baseline_report.get("candidate_id", ""))
        candidate_id = str(candidate_report.get("candidate_id", ""))
        self.calls.append((baseline_id, candidate_id))
        adopted = candidate_id == "candidate_004" and self.adopt_candidate_004
        return {
            "calculation_valid": True,
            "sample_adequacy": "adequate",
            "evidence_result": "supported" if adopted else "rejected",
            "adopted": adopted,
            "adoption_kind": "relative_improvement" if adopted else "not_adopted",
            "stable_strategy": False,
            "observed_deltas": {},
            "mechanism_updates": [],
            "next_action": "continue",
        }


class RuleFixTester:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def run(self, state):
        stage = str(state["experiment_spec"].get("stage", ""))
        candidate_id = str(state["current_candidate_id"])
        self.calls.append((stage, candidate_id))
        sharpes = {
            "candidate_001": 0.10,
            "candidate_004": 0.50,
            "candidate_008": 0.20,
        }
        state["development_report"] = _fresh_rule_fix_report(
            candidate_id,
            int(state["epoch_index"]),
            sharpe=sharpes.get(candidate_id, 0.0),
        )
        state["test_result"] = BacktestResult(
            annual_return=0.01,
            sharpe=sharpes.get(candidate_id, 0.0),
            max_drawdown=-10000,
            max_ddpercent=0.01,
            trade_count=300,
            passed=False,
            summary="rule fix test",
        )
        state["phase"] = "test"
        return state


def _run_rule_fix_recheck_test_flow(
    tmp_path: Path,
    monkeypatch,
    *,
    adopt_candidate_004: bool,
) -> tuple[dict[str, object], RuleFixPlanner, RuleFixJudge, RuleFixTester]:
    source_path, _baseline_code, _candidate_004_code, profile = (
        _write_rule_fix_recheck_fixture(tmp_path)
    )
    new_run_dir = tmp_path / "new_rule_fix_run"
    new_run_dir.mkdir()
    monkeypatch.setattr(
        workflow_v2,
        "get_trace_run_dir",
        lambda _state: new_run_dir,
    )
    monkeypatch.setattr(
        workflow_v2,
        "write_trace_json",
        lambda *args, **kwargs: new_run_dir,
    )
    planner = RuleFixPlanner()
    judge = RuleFixJudge(adopt_candidate_004=adopt_candidate_004)
    tester = RuleFixTester()
    strategy_agent = FakeStrategyAgent()
    loop = ResearchLoopV2(
        interpreter=FakeInterpreter(),
        baseline_builder=FakeBaselineBuilder(),
        planner=planner,
        judge=judge,
        strategy_agent=strategy_agent,
        validate_agent=FakeValidateAgent(),
        tester=tester,
    )
    loop._check_daily_future_data = lambda *_args, **_kwargs: {"passed": True}
    result = loop.run(
        "一句测试想法",
        runtime_profile=profile,
        experiment_id="new_rule_fix_v2",
        run_final_if_confirmed=False,
        recheck_after_rule_fix_from_result=source_path,
        additional_candidates=1,
    )
    return result, planner, judge, tester


def test_rule_fix_recheck_reruns_001_and_004_then_continues_from_008(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result, planner, judge, tester = _run_rule_fix_recheck_test_flow(
        tmp_path,
        monkeypatch,
        adopt_candidate_004=True,
    )

    assert [item["candidate_id"] for item in result["planned_candidates"]] == [
        "candidate_001",
        "candidate_004",
        "candidate_008",
    ]
    assert [item["candidate_id"] for item in result["candidate_records"]] == [
        f"candidate_{number:03d}" for number in range(1, 9)
    ]
    records = {item["candidate_id"]: item for item in result["candidate_records"]}
    assert records["candidate_001"]["development_report"]["median_sharpe"] == 0.10
    assert records["candidate_004"]["development_report"]["median_sharpe"] == 0.50
    assert records["candidate_002"]["development_report"] == {}
    assert records["candidate_002"]["judge_result"] == {}
    assert records["candidate_002"]["legacy_evidence_only"] is True
    assert "1%-1.7%" in records["candidate_002"]["legacy_comparison_note"]
    assert result["rule_fix_recheck_from"]["old_development_reports_reused"] is False
    assert result["rule_fix_recheck_from"]["old_confirmation_reused"] is False
    assert result["rule_fix_recheck_from"]["old_final_test_reused"] is False
    assert result["rule_fix_recheck_from"]["status"] == "completed"
    assert result["rule_fix_recheck_from"]["selected_candidate_id_after_recheck"] == (
        "candidate_004"
    )
    assert result["selected_candidate_id"] == "candidate_004"
    assert planner.calls[0]["accepted_strategy"]["candidate_id"] == "candidate_004"
    assert judge.calls == [
        ("candidate_001", "candidate_004"),
        ("candidate_004", "candidate_008"),
    ]
    assert [item for item in tester.calls if item[0] == "research"] == [
        ("research", "candidate_001"),
        ("research", "candidate_004"),
        ("research", "candidate_008"),
    ]
    result_text = json.dumps(result, ensure_ascii=False, default=str)
    assert "OLD_CONFIRMATION_MUST_NOT_BE_USED" not in result_text
    assert "OLD_FINAL_MUST_NOT_BE_USED" not in result_text
    assert "old_secret_metric" not in result_text


def test_rule_fix_recheck_falls_back_to_fresh_baseline_when_004_not_better(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result, planner, judge, tester = _run_rule_fix_recheck_test_flow(
        tmp_path,
        monkeypatch,
        adopt_candidate_004=False,
    )

    records = {item["candidate_id"]: item for item in result["candidate_records"]}
    assert records["candidate_004"]["status"] == "rejected"
    assert records["candidate_004"]["adopted"] is False
    assert result["rule_fix_recheck_from"]["candidate_004_adopted_after_recheck"] is False
    assert result["rule_fix_recheck_from"]["selected_candidate_id_after_recheck"] == (
        "candidate_001"
    )
    assert result["selected_candidate_id"] == "candidate_001"
    assert planner.calls[0]["accepted_strategy"]["candidate_id"] == "candidate_001"
    assert judge.calls == [
        ("candidate_001", "candidate_004"),
        ("candidate_001", "candidate_008"),
    ]
    assert ("confirmation", "candidate_001") in tester.calls


def test_rule_fix_recheck_stops_when_technical_repair_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path, _baseline_code, _candidate_004_code, profile = (
        _write_rule_fix_recheck_fixture(tmp_path)
    )
    new_run_dir = tmp_path / "failed_rule_fix_run"
    new_run_dir.mkdir()
    monkeypatch.setattr(
        workflow_v2,
        "get_trace_run_dir",
        lambda _state: new_run_dir,
    )
    monkeypatch.setattr(
        workflow_v2,
        "write_trace_json",
        lambda *args, **kwargs: new_run_dir,
    )
    loop = ResearchLoopV2(
        planner=RuleFixPlanner(),
        judge=RuleFixJudge(adopt_candidate_004=True),
        strategy_agent=FakeStrategyAgent(),
        validate_agent=FakeValidateAgent(),
        tester=RuleFixTester(),
    )

    def fail_repair(*_args, **_kwargs):
        raise RuntimeError("current membership check failed")

    loop._generate_and_validate = fail_repair
    with pytest.raises(RuntimeError, match="规则修复重跑失败"):
        loop.run(
            "一句测试想法",
            runtime_profile=profile,
            experiment_id="failed_rule_fix_v2",
            recheck_after_rule_fix_from_result=source_path,
            additional_candidates=1,
        )

    partial = json.loads(
        (new_run_dir / "research_loop_v2_result.json").read_text(encoding="utf-8")
    )
    assert partial["rule_fix_recheck_from"]["status"] == "failed"
    assert partial["selected_research_report"] == {}
    assert partial["confirmation_report"] == {}
    assert "current membership check failed" in partial["rule_fix_recheck_from"][
        "error"
    ]
