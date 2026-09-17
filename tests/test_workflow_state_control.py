from __future__ import annotations

from unittest.mock import patch

from quanta_agents.agents.manager_agent import ManagerAgent
from quanta_agents.state import (
    BacktestResult,
    derive_experiment_periods,
    init_state,
)
from quanta_agents.workflow import (
    continue_workflow,
    _run_strategy_step,
    _run_tester_step,
    _run_validation_step,
    run_workflow,
)


def test_workflow_requires_validation_even_if_generated_code_requests_test() -> None:
    class GeneratedStrategy:
        @staticmethod
        def run(state):
            state["strategy_result"] = {"output_weights": object()}
            state["phase"] = "test"
            return state

    state = init_state("test idea")
    state["phase"] = "strategy"

    result = _run_strategy_step(GeneratedStrategy(), state)  # type: ignore[arg-type]

    assert result["phase"] == "validate"
    assert "ignored generated next phase" in result["history"][-1]


def test_successful_validation_routes_to_development_backtest() -> None:
    class PassingValidation:
        @staticmethod
        def run(state):
            state["phase"] = "test"
            return state

    state = init_state("test idea")

    result = _run_validation_step(PassingValidation(), state)  # type: ignore[arg-type]

    assert result["phase"] == "backtest"
    assert result["evaluation_stage"] == "development"


def test_development_backtest_stops_when_dates_are_missing() -> None:
    class TesterMustNotRun:
        @staticmethod
        def run(state):
            raise AssertionError("tester must not run without explicit development dates")

    state = init_state("test idea", experiment_spec={})

    result = _run_tester_step(
        TesterMustNotRun(),
        state,
        period_kind="development",
    )  # type: ignore[arg-type]

    assert result["phase"] == "done"
    assert result["test_result"] is None
    assert "Development period" in result["last_test_error"]


def test_final_test_uses_locked_dates_and_clears_feedback() -> None:
    class FakeTester:
        @staticmethod
        def run(state):
            assert state["experiment_spec"]["backtest_start"] == "2024-01-01"
            assert state["experiment_spec"]["backtest_end"] == "2024-12-31"
            state["test_result"] = BacktestResult(
                annual_return=0.1,
                sharpe=0.8,
                max_drawdown=-100.0,
                max_ddpercent=0.1,
                trade_count=10,
                passed=False,
                summary="final",
            )
            state["backtest_feedback"] = "must not survive"
            state["phase"] = "test"
            return state

    state = init_state(
        "test idea",
        experiment_spec={
            "validate_start": "2023-01-01",
            "validate_end": "2023-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
            "final_test_start": "2024-01-01",
            "final_test_end": "2024-12-31",
        },
    )

    result = _run_tester_step(FakeTester(), state, period_kind="final_test")  # type: ignore[arg-type]

    assert result["phase"] == "final_test"
    assert result["backtest_feedback"] == ""
    assert result["technical_retry_count"] == 0


def test_run_workflow_passes_checkpointer_and_thread_id() -> None:
    calls: dict[str, object] = {}

    class FakeApp:
        @staticmethod
        def invoke(state, config):
            calls["state"] = state
            calls["config"] = config
            return state

    checkpointer = object()
    with patch("quanta_agents.workflow.build_workflow", return_value=FakeApp()) as build:
        result = run_workflow(
            "test idea",
            max_epochs=1,
            checkpointer=checkpointer,
            thread_id="research-thread",
        )

    build.assert_called_once_with(checkpointer=checkpointer)
    assert result["phase"] == "hypothesis"
    config = calls["config"]
    assert isinstance(config, dict)
    assert config["configurable"] == {"thread_id": "research-thread"}


def test_continue_workflow_keeps_restored_epoch() -> None:
    calls: dict[str, object] = {}

    class FakeApp:
        @staticmethod
        def invoke(state, config):
            calls["state"] = state
            calls["config"] = config
            return state

    state = init_state("test idea", max_epochs=3)
    state["epoch_index"] = 2
    state["phase"] = "diagnostics"
    with patch("quanta_agents.workflow.build_workflow", return_value=FakeApp()):
        result = continue_workflow(state, thread_id="restored-thread")

    assert result["epoch_index"] == 2
    assert result["phase"] == "diagnostics"
    assert calls["state"] is state
    assert calls["config"]["configurable"] == {"thread_id": "restored-thread"}


def test_period_defaults_keep_backtest_dates_for_final_test() -> None:
    periods = derive_experiment_periods(
        {
            "validate_start": "2022-01-01",
            "validate_end": "2022-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
        }
    )

    assert periods["development_period"] == ("2022-01-01", "2022-12-31")
    assert periods["final_test_period"] == ("2023-01-01", "2023-12-31")
    assert periods["test_period"] == periods["final_test_period"]


def test_manager_refuses_overlapping_development_and_final_periods() -> None:
    state = init_state(
        "test idea",
        experiment_spec={
            "validate_start": "2023-01-01",
            "validate_end": "2023-12-31",
            "backtest_start": "2023-06-01",
            "backtest_end": "2024-05-31",
            "allow_final_test": True,
            "evaluation": {"min_sharpe_ratio": 0.0},
        },
    )
    state["phase"] = "backtest"
    state["test_result"] = BacktestResult(
        annual_return=0.1,
        sharpe=1.0,
        max_drawdown=-100.0,
        max_ddpercent=0.1,
        trade_count=10,
        passed=True,
        summary="development",
    )

    result = ManagerAgent().dispatch(state)

    assert result["phase"] == "done"
    assert result["quality_passed"] is True
    assert result["ready_for_final"] is False
    assert result["final_test_count"] == 0
    assert "overlap" in result["manager_notes"]


def test_development_test_error_updates_retry_count_and_candidate_id() -> None:
    class FailingTester:
        @staticmethod
        def run(state):
            state["test_result"] = None
            state["backtest_feedback"] = "backtest_error: test failure"
            state["epoch_index"] = 2
            state["phase"] = "hypothesis"
            return state

    state = init_state(
        "test idea",
        max_epochs=2,
        experiment_spec={
            "validate_start": "2022-01-01",
            "validate_end": "2022-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
        },
    )

    result = _run_tester_step(FailingTester(), state, period_kind="development")  # type: ignore[arg-type]

    assert result["technical_retry_count"] == 1
    assert result["current_candidate_id"] == "candidate_002"
    assert result["phase"] == "hypothesis"


def test_final_test_error_cannot_start_a_new_research_round() -> None:
    class FailingFinalTester:
        @staticmethod
        def run(state):
            state["test_result"] = None
            state["backtest_feedback"] = "backtest_error: final failure"
            state["epoch_index"] = 2
            state["strategy_validate_round"] = 2
            state["phase"] = "hypothesis"
            return state

    state = init_state(
        "test idea",
        max_epochs=2,
        experiment_spec={
            "validate_start": "2022-01-01",
            "validate_end": "2022-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
        },
    )

    result = _run_tester_step(FailingFinalTester(), state, period_kind="final_test")  # type: ignore[arg-type]

    assert result["phase"] == "final_test"
    assert result["epoch_index"] == 1
    assert result["strategy_validate_round"] == 1
    assert result["current_candidate_id"] == "candidate_001"
    assert result["backtest_feedback"] == ""
    assert result["last_test_error"] == "backtest_error: final failure"
