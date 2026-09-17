from __future__ import annotations

from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

import pandas as pd


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

from quanta_agents.agents.strategy_tester import StrategyTester
from quanta_agents.agents.strategy_agent import StrategyAgent
from quanta_agents.agents.manager_agent import ManagerAgent
from quanta_agents.agents.validate_agent import OutputWeightsRuleChecker, ValidateAgent
from quanta_agents.experiment_runner import _run_single_experiment
from quanta_agents.state import init_state


def test_validate_stops_when_validation_rounds_and_epochs_are_exhausted() -> None:
    state = init_state("test idea", max_epochs=1)
    state["epoch_index"] = 1
    state["strategy_validate_round"] = 2
    state["test_result"] = object()  # type: ignore[assignment]

    with patch(
        "quanta_agents.agents.validate_agent.get_max_strategy_validate_rounds",
        return_value=2,
    ):
        ValidateAgent._apply_validation_outcome(
            state,
            passed=False,
            validation_summary={"intermediate_variable_checks": {}},
        )

    assert state["phase"] == "done"
    assert state["epoch_index"] == 1
    assert state["strategy_validate_round"] == 2
    assert state["test_result"] is None


def test_validate_failure_increments_round_and_returns_to_strategy() -> None:
    state = init_state("test idea", max_epochs=1)
    state["epoch_index"] = 1
    state["strategy_validate_round"] = 1
    state["test_result"] = object()  # type: ignore[assignment]

    with patch(
        "quanta_agents.agents.validate_agent.get_max_strategy_validate_rounds",
        return_value=2,
    ):
        ValidateAgent._apply_validation_outcome(
            state,
            passed=False,
            validation_summary={"intermediate_variable_checks": {}},
        )

    assert state["phase"] == "strategy"
    assert state["strategy_validate_round"] == 2
    assert state["test_result"] is None


def test_backtest_failure_counts_rounds_and_stops_when_all_limits_are_exhausted() -> None:
    retry_state = init_state("test idea", max_epochs=1)
    retry_state["strategy_validate_round"] = 1
    retry_state["test_result"] = object()  # type: ignore[assignment]

    with patch(
        "quanta_agents.agents.strategy_tester.get_max_strategy_validate_rounds",
        return_value=2,
    ):
        StrategyTester._route_backtest_failure(retry_state, "test error")

    assert retry_state["phase"] == "strategy"
    assert retry_state["strategy_validate_round"] == 2
    assert retry_state["test_result"] is None

    exhausted_state = init_state("test idea", max_epochs=1)
    exhausted_state["epoch_index"] = 1
    exhausted_state["strategy_validate_round"] = 2
    exhausted_state["test_result"] = object()  # type: ignore[assignment]

    with patch(
        "quanta_agents.agents.strategy_tester.get_max_strategy_validate_rounds",
        return_value=2,
    ):
        StrategyTester._route_backtest_failure(exhausted_state, "test error")

    assert exhausted_state["phase"] == "done"
    assert exhausted_state["epoch_index"] == 1
    assert exhausted_state["strategy_validate_round"] == 2
    assert exhausted_state["test_result"] is None

    multi_epoch_state = init_state("test idea", max_epochs=3)
    multi_epoch_state["epoch_index"] = 1
    multi_epoch_state["strategy_validate_round"] = 2

    with patch(
        "quanta_agents.agents.strategy_tester.get_max_strategy_validate_rounds",
        return_value=2,
    ):
        StrategyTester._route_backtest_failure(multi_epoch_state, "test error")

    assert multi_epoch_state["phase"] == "done"
    assert multi_epoch_state["epoch_index"] == 1
    assert "not sent to research optimization" in multi_epoch_state["manager_notes"]


def test_manager_preserves_failure_reason_after_done() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["manager_notes"] = "Validation did not pass."

    result = ManagerAgent().dispatch(state)

    assert result["manager_notes"] == "Validation did not pass."


def test_experiment_is_failed_when_workflow_has_no_backtest_result() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["manager_notes"] = "Backtest kept failing."

    with patch("quanta_agents.experiment_runner.run_workflow", return_value=state):
        outcome = _run_single_experiment(
            "idea.yaml",
            "test idea",
            {"experiment_id": "exp_failed"},
            1,
        )

    assert outcome.success is False
    assert outcome.final_state is state
    assert outcome.error == "Backtest kept failing."


def test_development_only_experiment_succeeds_when_candidate_is_frozen() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["quality_passed"] = True
    state["ready_for_final"] = True
    state["candidate_frozen"] = True
    state["awaiting_final_test_approval"] = True

    with patch("quanta_agents.experiment_runner.run_workflow", return_value=state):
        outcome = _run_single_experiment(
            "idea.yaml",
            "test idea",
            {"experiment_id": "exp_development"},
            1,
        )

    assert outcome.success is True
    assert outcome.ready_for_final is True
    assert outcome.quality_passed is True
    assert outcome.final_test_run is False


def test_arbitrary_test_result_is_not_treated_as_success() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["test_result"] = {"passed": True}  # type: ignore[typeddict-item]

    with patch("quanta_agents.experiment_runner.run_workflow", return_value=state):
        outcome = _run_single_experiment(
            "idea.yaml",
            "test idea",
            {"experiment_id": "exp_old_result"},
            1,
        )

    assert outcome.success is False
    assert outcome.ready_for_final is False


def test_requested_final_test_requires_a_passing_final_result() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["quality_passed"] = True
    state["ready_for_final"] = True
    state["candidate_frozen"] = True
    state["final_test_result"] = {"passed": False}  # type: ignore[typeddict-item]

    with patch("quanta_agents.experiment_runner.run_workflow", return_value=state):
        outcome = _run_single_experiment(
            "idea.yaml",
            "test idea",
            {
                "experiment_id": "exp_final_failed",
                "run_final_test": True,
                "allow_final_test": True,
            },
            1,
        )

    assert outcome.success is False
    assert outcome.ready_for_final is True
    assert outcome.quality_passed is False
    assert outcome.final_test_run is True


def test_requested_final_test_succeeds_only_with_passing_final_result() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["quality_passed"] = True
    state["ready_for_final"] = True
    state["candidate_frozen"] = True
    state["final_test_result"] = {"passed": True}  # type: ignore[typeddict-item]

    with patch("quanta_agents.experiment_runner.run_workflow", return_value=state):
        outcome = _run_single_experiment(
            "idea.yaml",
            "test idea",
            {
                "experiment_id": "exp_final_passed",
                "run_final_test": True,
                "allow_final_test": True,
            },
            1,
        )

    assert outcome.success is True
    assert outcome.ready_for_final is True
    assert outcome.quality_passed is True
    assert outcome.final_test_run is True


def test_runtime_environment_can_keep_final_period_disabled() -> None:
    state = init_state("test idea", max_epochs=1)
    state["phase"] = "done"
    state["quality_passed"] = True
    state["ready_for_final"] = True
    state["candidate_frozen"] = True
    state["awaiting_final_test_approval"] = True

    with patch.dict(
        "os.environ",
        {
            "QUANTA_RUN_FINAL_TEST": "false",
            "QUANTA_ALLOW_FINAL_TEST": "false",
            "QUANTA_DEVELOPMENT_FOLDS": "4",
            "QUANTA_GAP_TRADING_DAYS": "12",
        },
        clear=False,
    ), patch(
        "quanta_agents.experiment_runner.run_workflow",
        return_value=state,
    ) as run_mock:
        outcome = _run_single_experiment(
            "idea.yaml",
            "test idea",
            {
                "experiment_id": "exp_env_override",
                "run_final_test": True,
                "allow_final_test": True,
            },
            1,
        )

    effective_spec = run_mock.call_args.kwargs["experiment_spec"]
    assert effective_spec["run_final_test"] is False
    assert effective_spec["allow_final_test"] is False
    assert effective_spec["development_folds"] == 4
    assert effective_spec["gap_trading_days"] == 12
    assert outcome.success is True
    assert outcome.final_test_run is False


def test_validation_failure_stops_without_consuming_research_iteration() -> None:
    state = init_state("test idea", max_epochs=2)
    state["strategy_validate_round"] = 2
    summary = {
        "intermediate_variable_checks": {"factor": {"passed": False}},
        "future_function_check": {"passed": False, "details": "uses future data"},
        "output_weights_check": {"passed": False, "details": "bad weights"},
        "suggestions": ["fix dates"],
    }

    with patch(
        "quanta_agents.agents.validate_agent.get_max_strategy_validate_rounds",
        return_value=2,
    ):
        ValidateAgent._apply_validation_outcome(
            state,
            passed=False,
            validation_summary=summary,
        )

    assert state["phase"] == "done"
    assert state["epoch_index"] == 1
    assert state["validation_feedback"]["validation_summary"] == summary
    assert "without consuming a research iteration" in state["manager_notes"]
    assert state["validation_feedback"]["suggestions"] == ["fix dates"]


def test_function_source_extraction_includes_called_private_helpers() -> None:
    code = """
def _leaf():
    return 1

def _run():
    return _leaf()

def output_weights():
    return _run()

def unrelated():
    return 2
"""

    sources = ValidateAgent._extract_function_sources(code, ["output_weights"])

    assert list(sources) == ["_leaf", "_run", "output_weights"]
    assert "unrelated" not in sources


def test_output_weights_allows_unchanged_target_after_membership_ends() -> None:
    weights = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "000001.SZ": [1.0, 1.0],
            "cash": [0.0, 0.0],
        }
    )
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2024-01-01"],
            "end_date": ["2024-01-02"],
        }
    )
    strategy_output = {
        "output_weights_df": {"datetime_column": "trade_date"},
    }
    universe = [{"asset": "中国股票", "symbols": ["000001.SZ"]}]

    result = OutputWeightsRuleChecker.run(
        weights,
        strategy_output,
        universe,
        membership,
    )

    assert result["passed"] is True
    assert "historical_index_membership" not in result["failed_rules"]


def test_output_weights_rejects_target_increase_after_membership_ends() -> None:
    weights = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "000001.SZ": [0.5, 1.0],
            "cash": [0.5, 0.0],
        }
    )
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2024-01-01"],
            "end_date": ["2024-01-02"],
        }
    )
    strategy_output = {
        "output_weights_df": {"datetime_column": "trade_date"},
    }
    universe = [{"asset": "中国股票", "symbols": ["000001.SZ"]}]

    result = OutputWeightsRuleChecker.run(
        weights,
        strategy_output,
        universe,
        membership,
    )

    assert result["passed"] is False
    assert "historical_index_membership" in result["failed_rules"]


def test_strategy_agent_adds_historical_membership_for_parquet_hs300(tmp_path: Path) -> None:
    membership_path = tmp_path / "csi300.txt"
    membership_path.write_text(
        "SZ000001\t2024-01-01\t2024-12-31\n",
        encoding="utf-8",
    )
    required_data = [
        {
            "table_key": "stock_kline_daily_qfq",
            "type": "time_series",
            "fields": ["open", "close"],
            "universe": {"type": "named_pool", "value": "hs300"},
            "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "purpose": "test",
        }
    ]

    with patch.dict(
        "os.environ",
        {
            "QUANTA_DATA_ENGINE": "parquet",
            "QUANTA_CSI300_MEMBERSHIP_FILE": str(membership_path),
        },
        clear=False,
    ):
        prepared = StrategyAgent._prepare_required_data(
            required_data,
            "2024-01-01",
            "2024-12-31",
        )

    membership_items = [
        item for item in prepared if item.get("table_key") == "csi300_membership"
    ]
    assert len(membership_items) == 1
    assert membership_items[0]["fields"] == ["code", "start_date", "end_date"]


def test_validate_sandbox_receives_universe_and_actual_params() -> None:
    strategy_context = {
        "strategy_code": "",
        "strategy_output": {},
        "params": {"adx_period": 14},
        "universe": [{"asset": "中国股票", "symbols": ["000001.SZ"]}],
        "train_data_bundle": {},
        "validate_data_bundle": {},
        "required_data": [],
        "experiment_periods": {},
    }

    namespace, notes = ValidateAgent._build_script_sandbox_namespace(strategy_context)

    assert notes == []
    assert namespace["params"] == {"adx_period": 14}
    assert namespace["universe"] == [
        {"asset": "中国股票", "symbols": ["000001.SZ"]}
    ]
