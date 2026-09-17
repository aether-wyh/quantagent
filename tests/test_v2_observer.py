from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from quanta_agents.v2_observer import audit_v2_loop


def _stable_development_report() -> dict[str, object]:
    return {
        "period_kind": "development",
        "fold_count": 3,
        "passed": True,
        "median_annual_return": 0.08,
        "median_sharpe": 0.90,
        "worst_fold_sharpe": 0.20,
        "total_trade_count": 450,
        "beats_cash_in_all_folds": True,
        "cost_stress_complete": True,
        "cost_stress_passed": True,
        "delay_stress_complete": True,
        "delay_stress_passed": True,
        "folds": [{"name": "a"}, {"name": "b"}, {"name": "c"}],
    }


def test_observer_requires_actual_formal_coverage_and_stable_results() -> None:
    run_record = {
        "mechanism_hypotheses": [
            {"mechanism_id": "m1", "testable_prediction": "预测一"},
            {"mechanism_id": "m2", "testable_prediction": "预测二"},
        ],
        "candidate_records": [
            {
                "candidate_id": "n1",
                "research_category": "numerical_definition",
                "status": "tested",
                "development_report": {"passed": False},
            },
            {
                "candidate_id": "s1",
                "research_category": "mechanism_signal",
                "mechanism_id": "m1",
                "new_signal": {"field": "candidate_field"},
                "mechanism_comparison_results": {
                    "added_to_base": {"report": {"passed": False}},
                    "signal_only": {"report": {"passed": False}},
                },
                "status": "tested",
                "development_report": {"passed": False},
            },
            {
                "candidate_id": "a1",
                "research_category": "applicability",
                "status": "tested",
                "development_report": {"passed": False},
            },
            {
                "candidate_id": "r1",
                "research_category": "rule_ablation",
                "status": "tested",
                "development_report": {"passed": False},
            },
            {
                "candidate_id": "h1",
                "research_category": "holding_period",
                "status": "tested",
                "development_report": {"passed": False},
            },
        ],
        "selected_candidate_id": "best1",
        "selected_development_report": _stable_development_report(),
        "final_test_report": {
            "passed": True,
            "annual_return": 0.06,
            "sharpe": 0.70,
            "max_ddpercent": 0.12,
            "trade_count": 120,
        },
    }

    result = audit_v2_loop(run_record)

    assert result["questions"]["number_and_definition"]["formally_tested"] is True
    mechanism = result["questions"]["mechanism_and_new_signal"]
    assert mechanism["competing_mechanisms_recorded"] is True
    assert mechanism["mechanism_linked_new_signal_tested"] is True
    assert result["questions"]["applicability_or_environment"]["formally_tested"] is True
    assert result["additional_checks"]["rule_ablation"]["formally_tested"] is True
    assert result["additional_checks"]["holding_period"]["formally_tested"] is True
    stable = result["questions"]["stable_strategy"]
    assert stable["development_stable"] is True
    assert stable["final_test"]["passed"] is True
    assert result["observer_conclusion"]["overall_passed"] is True


def test_observer_does_not_count_prose_or_plans_as_completed_tests() -> None:
    run_record = {
        "notes": "以后可以改数字、换适用对象、加入新信号并调整持有期",
        "research_plan": [
            {
                "candidate_id": "n1",
                "research_category": "numerical_definition",
                "status": "planned",
            },
            {
                "candidate_id": "a1",
                "research_category": "applicability",
                "status": "planned",
            },
        ],
        "mechanism_hypotheses": [
            {"mechanism_id": "m1", "testable_prediction": "只有一个解释"}
        ],
        "candidate_records": [
            {
                "candidate_id": "s1",
                "research_category": "mechanism_signal",
                "mechanism_id": "m1",
                "new_signal": {"field": "candidate_field"},
                "status": "planned",
            }
        ],
        "selected_candidate_id": "bad",
        "selected_development_report": {
            **_stable_development_report(),
            "passed": False,
            "worst_fold_sharpe": -0.40,
        },
    }

    result = audit_v2_loop(run_record)

    numeric = result["questions"]["number_and_definition"]
    assert numeric["aware"] is True
    assert numeric["formally_tested"] is False
    assert result["questions"]["mechanism_and_new_signal"][
        "competing_mechanisms_recorded"
    ] is False
    assert result["questions"]["mechanism_and_new_signal"][
        "mechanism_linked_new_signal_tested"
    ] is False
    applicability = result["questions"]["applicability_or_environment"]
    assert applicability["aware"] is True
    assert applicability["formally_tested"] is False
    assert result["questions"]["stable_strategy"]["development_stable"] is False
    assert result["questions"]["stable_strategy"]["final_test"]["status"] == "not_run"
    assert result["observer_conclusion"]["overall_passed"] is False


def test_observer_respects_explicitly_disabled_stress_checks() -> None:
    report = _stable_development_report()
    report.pop("cost_stress_complete")
    report.pop("cost_stress_passed")
    report.pop("delay_stress_complete")
    report.pop("delay_stress_passed")

    result = audit_v2_loop(
        {
            "observer_requirements": {
                "require_cost_stress": False,
                "require_delay_stress": False,
            },
            "selected_development_report": report,
        }
    )

    assert result["questions"]["stable_strategy"]["development_stable"] is True
