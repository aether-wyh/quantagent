from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "openai" not in sys.modules:
    openai_stub = ModuleType("openai")

    class _DummyOpenAI:  # pragma: no cover - 只用于测试导入
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda *a, **k: None))

    setattr(openai_stub, "OpenAI", _DummyOpenAI)
    sys.modules["openai"] = openai_stub

from quanta_agents.agents.result_judge_v2 import ResultJudgeV2


class FakeLLM:
    def __init__(self, reply: dict[str, object]) -> None:
        self.reply = reply
        self.calls: list[dict[str, object]] = []

    def complete(self, **kwargs: object) -> str:
        self.calls.append(dict(kwargs))
        return json.dumps(self.reply, ensure_ascii=False)


def _report(
    *,
    median_sharpe: float,
    worst_sharpe: float,
    annual_return: float,
    drawdown: float,
    trades: int,
    cost_sharpe: float,
    delay_sharpe: float,
    passed: bool,
) -> dict[str, object]:
    return {
        "period_kind": "development",
        "fold_count": 3,
        "median_sharpe": median_sharpe,
        "worst_fold_sharpe": worst_sharpe,
        "median_annual_return": annual_return,
        "worst_fold_drawdown": drawdown,
        "total_trade_count": trades,
        "cost_stress_median_sharpe": cost_sharpe,
        "delay_stress_median_sharpe": delay_sharpe,
        "cost_stress_complete": True,
        "delay_stress_complete": True,
        "cost_stress_passed": cost_sharpe >= 0,
        "delay_stress_passed": delay_sharpe >= 0,
        "beats_cash_in_all_folds": annual_return > 0,
        "passed": passed,
    }


def _model_reply(
    *,
    adopted: bool = True,
    evidence_result: str = "supported",
    sample_adequacy: str = "adequate",
    calculation_valid: bool = True,
) -> dict[str, object]:
    return {
        "calculation_valid": calculation_valid,
        "sample_adequacy": sample_adequacy,
        "evidence_result": evidence_result,
        "adopted": adopted,
        "observed_deltas": {"median_sharpe_delta": 999},
        "mechanism_updates": [
            {
                "mechanism_id": "m1",
                "update": "strengthened",
                "reason": "实际方向与事前预测一致",
            }
        ],
        "next_action": "检查下一项事前登记的判断",
    }


def test_fixed_comparison_calculates_all_required_deltas() -> None:
    baseline = _report(
        median_sharpe=0.20,
        worst_sharpe=0.00,
        annual_return=0.04,
        drawdown=0.16,
        trades=200,
        cost_sharpe=0.10,
        delay_sharpe=0.05,
        passed=False,
    )
    candidate = _report(
        median_sharpe=0.35,
        worst_sharpe=0.06,
        annual_return=0.05,
        drawdown=0.13,
        trades=180,
        cost_sharpe=0.16,
        delay_sharpe=0.08,
        passed=False,
    )

    comparison = ResultJudgeV2.compare_reports(
        baseline, candidate, {"min_fold_count": 3, "min_trade_count": 100}
    )

    deltas = comparison["observed_deltas"]
    assert deltas["median_sharpe_delta"] == pytest.approx(0.35 - 0.20)
    assert deltas["worst_fold_sharpe_delta"] == pytest.approx(0.06)
    assert deltas["median_annual_return_delta"] == pytest.approx(0.01)
    assert deltas["worst_fold_drawdown_abs_delta"] == pytest.approx(0.13 - 0.16)
    assert deltas["total_trade_count_delta"] == -20
    assert deltas["cost_stress_median_sharpe_delta"] == pytest.approx(0.06)
    assert deltas["delay_stress_median_sharpe_delta"] == pytest.approx(0.03)
    assert comparison["relative_improvement"] is True
    assert comparison["stable_candidate"] is False
    assert comparison["program_adoption_eligible"] is True


def test_relative_improvement_can_be_next_baseline_without_stable_claim() -> None:
    baseline = _report(
        median_sharpe=0.20,
        worst_sharpe=0.00,
        annual_return=0.04,
        drawdown=0.16,
        trades=200,
        cost_sharpe=0.10,
        delay_sharpe=0.05,
        passed=False,
    )
    candidate = _report(
        median_sharpe=0.35,
        worst_sharpe=0.06,
        annual_return=0.05,
        drawdown=0.13,
        trades=180,
        cost_sharpe=0.16,
        delay_sharpe=0.08,
        passed=False,
    )
    fake = FakeLLM(_model_reply())

    result = ResultJudgeV2(client=fake, max_retries=1).run(
        baseline,
        candidate,
        {"mechanism_id": "m1", "prediction": "候选应改善多个分段"},
        {"min_fold_count": 3, "min_trade_count": 100},
    )

    assert result["adopted"] is True
    assert result["adoption_kind"] == "relative_improvement"
    assert result["stable_strategy"] is False
    assert result["observed_deltas"]["median_sharpe_delta"] == pytest.approx(0.15)
    assert fake.calls[0]["role"] == "result_judge_v2"


def test_model_cannot_adopt_candidate_that_fixed_rules_reject() -> None:
    baseline = _report(
        median_sharpe=0.40,
        worst_sharpe=0.10,
        annual_return=0.06,
        drawdown=0.12,
        trades=200,
        cost_sharpe=0.25,
        delay_sharpe=0.20,
        passed=True,
    )
    candidate = _report(
        median_sharpe=0.20,
        worst_sharpe=-0.10,
        annual_return=0.03,
        drawdown=0.20,
        trades=80,
        cost_sharpe=-0.05,
        delay_sharpe=-0.10,
        passed=False,
    )

    result = ResultJudgeV2(client=FakeLLM(_model_reply()), max_retries=1).run(
        baseline,
        candidate,
        {"mechanism_id": "m1", "prediction": "候选更好"},
        {"min_fold_count": 3, "min_trade_count": 50},
    )

    assert result["fixed_comparison"]["program_adoption_eligible"] is False
    assert result["adopted"] is False
    assert result["stable_strategy"] is False


def test_complete_passing_candidate_can_be_marked_stable() -> None:
    baseline = _report(
        median_sharpe=0.00,
        worst_sharpe=-0.20,
        annual_return=0.01,
        drawdown=0.20,
        trades=150,
        cost_sharpe=-0.10,
        delay_sharpe=-0.10,
        passed=False,
    )
    candidate = _report(
        median_sharpe=0.40,
        worst_sharpe=0.10,
        annual_return=0.06,
        drawdown=0.12,
        trades=160,
        cost_sharpe=0.20,
        delay_sharpe=0.15,
        passed=True,
    )

    result = ResultJudgeV2(client=FakeLLM(_model_reply()), max_retries=1).run(
        baseline,
        candidate,
        {"mechanism_id": "m1", "prediction": "候选更好"},
        {"min_fold_count": 3, "min_trade_count": 100},
    )

    assert result["adopted"] is True
    assert result["adoption_kind"] == "stable_strategy"
    assert result["stable_strategy"] is True


def test_inadequate_sample_forces_unknown_and_blocks_adoption() -> None:
    baseline = _report(
        median_sharpe=0.00,
        worst_sharpe=-0.20,
        annual_return=0.01,
        drawdown=0.20,
        trades=20,
        cost_sharpe=0.00,
        delay_sharpe=0.00,
        passed=False,
    )
    candidate = _report(
        median_sharpe=0.50,
        worst_sharpe=0.10,
        annual_return=0.08,
        drawdown=0.10,
        trades=25,
        cost_sharpe=0.40,
        delay_sharpe=0.30,
        passed=True,
    )

    result = ResultJudgeV2(client=FakeLLM(_model_reply()), max_retries=1).run(
        baseline,
        candidate,
        {"mechanism_id": "m1", "prediction": "候选更好"},
        {"min_fold_count": 3, "min_trade_count": 100},
    )

    assert result["sample_adequacy"] == "inadequate"
    assert result["evidence_result"] == "unknown"
    assert result["adopted"] is False
    assert result["stable_strategy"] is False


def test_prompt_does_not_seed_named_markets_or_actor_story() -> None:
    prompt = (
        SRC_DIR
        / "quanta_agents"
        / "prompts"
        / "agents"
        / "result_judge_v2.yaml"
    ).read_text(encoding="utf-8")

    assert "沪深300" not in prompt
    assert "中证1000" not in prompt
    assert "游资" not in prompt
