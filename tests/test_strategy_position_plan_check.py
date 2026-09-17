from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest

import quanta_agents.workflow_v2 as workflow_v2
from quanta_agents.state import init_state
from quanta_agents.strategy_position_plan_check import (
    PositionPlanValidationError,
    check_generated_daily_position_plans,
)
from quanta_agents.workflow_v2 import ResearchLoopV2


_GOOD_POSITION_PLAN_CODE = """
import pandas as pd

def build_daily_position_plan_weights(
    trading_dates,
    new_plans_by_date,
    single_stock_weight,
):
    symbols = sorted({
        plan["code"]
        for plans in new_plans_by_date.values()
        for plan in plans
    })
    rows = []
    active_plans = {}
    for trade_date in trading_dates:
        expired = [
            code
            for code, plan in active_plans.items()
            if plan["last_target_date"] < trade_date
        ]
        for code in expired:
            del active_plans[code]

        new_plans = [
            plan
            for plan in new_plans_by_date.get(trade_date, [])
            if plan["code"] not in active_plans
        ]
        used_cash = sum(plan["target_weight"] for plan in active_plans.values())
        available_cash = max(0.0, 1.0 - used_cash)
        if new_plans:
            desired_cash = single_stock_weight * len(new_plans)
            if len(new_plans) < 10 and desired_cash <= available_cash:
                new_weight = single_stock_weight
            else:
                new_weight = available_cash / len(new_plans)
            if new_weight > 0:
                for plan in new_plans:
                    active_plans[plan["code"]] = {
                        "last_target_date": plan["last_target_date"],
                        "target_weight": new_weight,
                    }

        row = {code: 0.0 for code in symbols}
        for code, plan in active_plans.items():
            row[code] = plan["target_weight"]
        row["trade_date"] = trade_date
        row["cash"] = 1.0 - sum(row[code] for code in symbols)
        rows.append(row)
    return pd.DataFrame(rows, columns=["trade_date", *symbols, "cash"])

def output_weights(train_data_bundle, validate_data_bundle, params):
    return build_daily_position_plan_weights(
        params["trading_dates"],
        params["new_plans_by_date"],
        params["single_stock_weight"],
    )
"""


_BAD_GLOBAL_REWEIGHT_CODE = """
import pandas as pd

def build_daily_position_plan_weights(
    trading_dates,
    new_plans_by_date,
    single_stock_weight,
):
    symbols = sorted({
        plan["code"]
        for plans in new_plans_by_date.values()
        for plan in plans
    })
    rows = []
    active_plans = {}
    for trade_date in trading_dates:
        active_plans = {
            code: plan
            for code, plan in active_plans.items()
            if plan["last_target_date"] >= trade_date
        }
        for plan in new_plans_by_date.get(trade_date, []):
            active_plans[plan["code"]] = plan

        active_codes = sorted(active_plans)
        if len(active_codes) < 10:
            stock_weight = single_stock_weight
        else:
            stock_weight = 1.0 / len(active_codes)
        row = {code: 0.0 for code in symbols}
        for code in active_codes:
            row[code] = stock_weight
        row["trade_date"] = trade_date
        row["cash"] = 1.0 - stock_weight * len(active_codes)
        rows.append(row)
    return pd.DataFrame(rows, columns=["trade_date", *symbols, "cash"])

def output_weights(train_data_bundle, validate_data_bundle, params):
    return build_daily_position_plan_weights(
        params["trading_dates"],
        params["new_plans_by_date"],
        params["single_stock_weight"],
    )
"""


_BAD_ZERO_WEIGHT_PLAN_CODE = _GOOD_POSITION_PLAN_CODE.replace(
    "            if new_weight > 0:\n"
    "                for plan in new_plans:\n"
    "                    active_plans[plan[\"code\"]] = {\n"
    "                        \"last_target_date\": plan[\"last_target_date\"],\n"
    "                        \"target_weight\": new_weight,\n"
    "                    }",
    "            for plan in new_plans:\n"
    "                active_plans[plan[\"code\"]] = {\n"
    "                    \"last_target_date\": plan[\"last_target_date\"],\n"
    "                    \"target_weight\": new_weight,\n"
    "                }",
)


_BAD_POST_PLAN_MEMBERSHIP_CODE = _GOOD_POSITION_PLAN_CODE.replace(
    "def output_weights(train_data_bundle, validate_data_bundle, params):\n"
    "    return build_daily_position_plan_weights(\n"
    "        params[\"trading_dates\"],\n"
    "        params[\"new_plans_by_date\"],\n"
    "        params[\"single_stock_weight\"],\n"
    "    )",
    "def _apply_daily_membership_constraint(weights, membership_lookup):\n"
    "    return weights\n\n"
    "def output_weights(train_data_bundle, validate_data_bundle, params):\n"
    "    planned_weights = build_daily_position_plan_weights(\n"
    "        params[\"trading_dates\"],\n"
    "        params[\"new_plans_by_date\"],\n"
    "        params[\"single_stock_weight\"],\n"
    "    )\n"
    "    planned_weights = _apply_daily_membership_constraint(\n"
    "        planned_weights, params[\"membership_lookup\"]\n"
    "    )\n"
    "    return planned_weights",
)


def test_position_plan_check_accepts_frozen_batch_weights() -> None:
    report = check_generated_daily_position_plans(_GOOD_POSITION_PLAN_CODE)

    assert report["passed"] is True
    assert report["first_batch_weight"] == 0.10
    assert report["later_batch_weight"] == 0.08
    assert report["zero_weight_retry_weight"] == 0.10


def test_position_plan_check_rejects_reweighting_all_active_codes() -> None:
    with pytest.raises(PositionPlanValidationError, match="FIRST_A"):
        check_generated_daily_position_plans(_BAD_GLOBAL_REWEIGHT_CODE)


def test_position_plan_check_rejects_zero_weight_plan_that_blocks_retry() -> None:
    with pytest.raises(PositionPlanValidationError, match="ZERO_RETRY"):
        check_generated_daily_position_plans(_BAD_ZERO_WEIGHT_PLAN_CODE)


def test_position_plan_check_rejects_membership_filter_after_fixed_plan() -> None:
    with pytest.raises(PositionPlanValidationError, match="固定持有计划后"):
        check_generated_daily_position_plans(_BAD_POST_PLAN_MEMBERSHIP_CODE)


def test_position_plan_check_rejects_unused_helper() -> None:
    unused_code = _GOOD_POSITION_PLAN_CODE.replace(
        "return build_daily_position_plan_weights(\n"
        "        params[\"trading_dates\"],\n"
        "        params[\"new_plans_by_date\"],\n"
        "        params[\"single_stock_weight\"],\n"
        "    )",
        "return pd.DataFrame()",
    )

    with pytest.raises(PositionPlanValidationError, match="必须实际调用"):
        check_generated_daily_position_plans(unused_code)


def test_v2_skips_position_plan_check_without_fixed_target_declaration(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        workflow_v2,
        "check_generated_daily_strategy",
        lambda *_args, **_kwargs: {"passed": True},
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("未声明固定目标比例时不应运行持仓计划检查")

    monkeypatch.setattr(
        workflow_v2,
        "check_generated_daily_position_plans",
        fail_if_called,
    )
    state = {
        "strategy_code": "def output_weights(*args):\n    return None",
        "strategy_result": {
            "validate_data_bundle": {
                "daily": pd.DataFrame(
                    {"trade_date": pd.date_range("2024-01-02", periods=3)}
                )
            }
        },
    }

    report = ResearchLoopV2._check_daily_future_data(
        state,  # type: ignore[arg-type]
        {"backtest_mode": "daily"},
    )

    assert report["position_plan_check"]["skipped"] is True


class _RewritingStrategyAgent:
    def __init__(self, first_code: str) -> None:
        self.calls = 0
        self.feedback: list[str] = []
        self.first_code = first_code

    def run(self, state):
        self.calls += 1
        self.feedback.append(str(state.get("validation_summary", {})))
        code = (
            self.first_code
            if self.calls == 1
            else _GOOD_POSITION_PLAN_CODE
        )
        state["strategy_code"] = code
        state["code_text"] = code
        state["strategy_result"] = {
            "params": {},
            "train_data_bundle": {},
            "validate_data_bundle": {
                "daily": pd.DataFrame(
                    {"trade_date": pd.date_range("2024-01-02", periods=3)}
                )
            },
            "strategy_output": {
                "output_weights_df": {"datetime_column": "trade_date"}
            },
        }
        state["strategy_generation_meta"] = {}
        state["phase"] = "validate"
        return state


class _PassingValidateAgent:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, state):
        self.calls += 1
        state["validation_summary"] = {"passed": True}
        state["phase"] = "test"
        return state


@pytest.mark.parametrize(
    ("first_code", "error_marker"),
    [
        (_BAD_GLOBAL_REWEIGHT_CODE, "FIRST_A"),
        (_BAD_ZERO_WEIGHT_PLAN_CODE, "ZERO_RETRY"),
        (_BAD_POST_PLAN_MEMBERSHIP_CODE, "固定持有计划后"),
    ],
)
def test_v2_rewrites_invalid_position_plan_code_before_regular_validation(
    monkeypatch,
    first_code: str,
    error_marker: str,
) -> None:
    strategy_agent = _RewritingStrategyAgent(first_code)
    validate_agent = _PassingValidateAgent()
    monkeypatch.setattr(
        workflow_v2,
        "check_generated_daily_strategy",
        lambda *_args, **_kwargs: {"passed": True},
    )
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *args, **kwargs: None)
    loop = ResearchLoopV2(
        strategy_agent=strategy_agent,
        validate_agent=validate_agent,
    )
    state = init_state("test")
    candidate = {
        "hypothesis": "test",
        "strategy_modification": "test",
        "required_data": [],
        "backtest_datasets": [],
    }

    loop._generate_and_validate(
        state,
        deepcopy(candidate),
        candidate_id="candidate_001",
        experiment_spec={
            "backtest_mode": "daily",
            "position_plan_contract": {"mode": "fixed_target_until_exit"},
        },
        max_technical_rounds=2,
    )

    assert strategy_agent.calls == 2
    assert validate_agent.calls == 1
    assert error_marker in strategy_agent.feedback[1]
    assert state["position_plan_check"]["passed"] is True
    assert state["future_data_check"]["position_plan_check"]["passed"] is True
