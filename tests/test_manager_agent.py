from pathlib import Path

from quanta_agents.agents.manager_agent import ManagerAgent
from quanta_agents.state import BacktestResult, init_state


def test_project_root_points_to_repository_root():
    root = ManagerAgent._project_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "experiments").is_dir()


def test_archive_experiment_artifacts_copies_yaml_and_strategy_outputs(tmp_path):
    root = tmp_path
    experiments_dir = root / "experiments"
    experiments_dir.mkdir(parents=True)
    (experiments_dir / "idea_test.yaml").write_text("experiment_id: exp_idea_test_123\n", encoding="utf-8")

    trace_root = root / "experiment_traces" / "exp_idea_test_123" / "epochs_1" / "epoch_001" / "strategyagent" / "round_001"
    structured_output_dir = trace_root / "structured_output"
    structured_output_dir.mkdir(parents=True)
    (structured_output_dir / "attempt_01.json").write_text('{"ok": true}', encoding="utf-8")
    (trace_root / "step_01.py").write_text("print('ok')\n", encoding="utf-8")

    backtest_outputs_dir = root / "experiment_traces" / "exp_idea_test_123" / "epochs_1" / "epoch_001" / "strategytester" / "backtest_outputs"
    backtest_outputs_dir.mkdir(parents=True)
    (backtest_outputs_dir / "result.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    state = {
        "experiment_spec": {"experiment_id": "exp_idea_test_123"},
        "epoch_index": 1,
        "max_epochs": 1,
        "strategy_validate_round": 1,
    }

    archive_dir = ManagerAgent._archive_experiment_artifacts(state, project_root=root)

    assert archive_dir is not None
    assert (archive_dir / "idea_test.yaml").exists()
    assert (archive_dir / "attempt_01.json").exists()
    assert (archive_dir / "step_01.py").exists()
    assert (archive_dir / "backtest_outputs" / "result.csv").exists()


def _backtest_result(*, sharpe: float = 1.2, passed: bool = True) -> BacktestResult:
    return BacktestResult(
        annual_return=0.15,
        sharpe=sharpe,
        max_drawdown=-10_000.0,
        max_ddpercent=0.10,
        trade_count=50,
        win_rate=0.55,
        profit_loss_ratio=1.3,
        passed=passed,
        summary="test result",
    )


def test_manager_uses_selected_event_success_metric_and_records_it():
    common_evaluation = {
        "min_trade_count": 100,
        "min_event_net_mean": 0.0,
        "min_event_success_rate": 0.35,
    }
    result = BacktestResult(
        annual_return=0.10,
        sharpe=1.0,
        max_drawdown=-1_000.0,
        max_ddpercent=0.01,
        trade_count=8_919,
        event_net_mean_return=0.0005193,
        event_gross_up_rate=0.4857,
        event_joint_minute_hit_rate=0.2674,
        event_success_rate=0.2674,
        event_success_column="joint_minute_hit",
        event_success_metric="gross_up_rate",
        event_success_metric_value=0.4857,
        passed=False,
        summary="gross metric passes",
    )
    gross_state = init_state(
        "test gross event success",
        experiment_spec={
            "evaluation": {
                **common_evaluation,
                "event_success_metric": "gross_up_rate",
            }
        },
    )
    joint_state = init_state(
        "test joint event success",
        experiment_spec={
            "evaluation": {
                **common_evaluation,
                "event_success_metric": "joint_minute_hit",
            }
        },
    )
    legacy_state = init_state(
        "test legacy event success",
        experiment_spec={"evaluation": common_evaluation},
    )

    assert ManagerAgent._passes_development_gate(gross_state, result) is True
    assert ManagerAgent._passes_development_gate(joint_state, result) is False
    assert ManagerAgent._passes_development_gate(legacy_state, result) is False

    ManagerAgent._record_experiment(
        gross_state,
        period_kind="development",
        result=result,
    )
    candidate = gross_state["candidate_records"][0]
    experiment = gross_state["experiment_records"][0]
    assert candidate["event_success_metric"] == "gross_up_rate"
    assert candidate["event_success_metric_value"] == 0.4857
    assert candidate["event_joint_minute_hit_rate"] == 0.2674
    assert experiment["event_success_metric"] == "gross_up_rate"
    assert experiment["event_success_metric_value"] == 0.4857


def test_development_result_is_recorded_and_can_feed_next_research_round():
    state = init_state(
        "test idea",
        max_epochs=2,
        experiment_spec={
            "validate_start": "2022-01-01",
            "validate_end": "2022-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
            "evaluation": {"min_sharpe_ratio": 2.0},
        },
    )
    state["phase"] = "backtest"
    state["hypothesis_generation_meta"] = {
        "candidate_mode": "modify_one_rule",
        "decision": "modify_one_rule",
        "selected_cause": "退出规则造成大额亏损",
        "expected_results": ["盈亏比上升"],
        "judgment_is_wrong_if": "盈亏比没有改善",
    }
    state["strategy_code"] = "def output_weights():\n    return None\n"
    state["strategy_generation_meta"] = {
        "code_diff": "+ return None",
        "previous_strategy_source": "WorkflowState.strategy_code",
    }
    selection_conditions = [
        {"feature": "pulse1_position", "operator": ">=", "value": 224}
    ]
    state["strategy_result"] = {
        "params": {
            "generic_selection_conditions": selection_conditions,
            "holding_minutes": 5,
            "event_horizon_minutes": 10,
        }
    }
    state["development_report"] = {"folds": [{"name": "2022", "passed": False}]}
    state["diagnostic_request"] = {"request_id": "old"}
    state["diagnostic_report"] = {"status": "completed"}
    state["diagnostic_round"] = 1
    state["test_result"] = _backtest_result(sharpe=0.5, passed=False)

    result = ManagerAgent().dispatch(state)

    assert result["phase"] == "hypothesis"
    assert result["research_trial_count"] == 1
    assert result["final_test_count"] == 0
    assert result["diagnostic_request"] == {}
    assert result["diagnostic_report"] == {}
    assert result["diagnostic_round"] == 0
    assert "backtest_metrics" in result["backtest_feedback"]
    assert result["candidate_records"][0]["period_kind"] == "development"
    assert result["candidate_records"][0]["candidate_mode"] == "modify_one_rule"
    assert result["experiment_records"][0]["candidate_mode"] == "modify_one_rule"
    assert len(result["candidate_records"][0]["strategy_code_sha256"]) == 64
    assert result["candidate_records"][0]["strategy_params"] == {
        "generic_selection_conditions": [
            {"feature": "pulse1_position", "operator": ">=", "value": 224}
        ],
        "holding_minutes": 5,
        "event_horizon_minutes": 10,
    }
    assert result["candidate_records"][0]["event_horizon_minutes"] == 10
    assert result["candidate_records"][0]["strategy_params"] is not state[
        "strategy_result"
    ]["params"]
    assert result["candidate_records"][0]["strategy_params"][
        "generic_selection_conditions"
    ] is not selection_conditions
    assert result["candidate_records"][0]["code_diff"] == "+ return None"
    assert result["candidate_records"][0]["code_source"] == "WorkflowState.strategy_code"
    assert result["candidate_records"][0]["development_report"] == {
        "folds": [{"name": "2022", "passed": False}]
    }
    assert result["development_report"] == {
        "folds": [{"name": "2022", "passed": False}]
    }
    assert result["candidate_records"][0]["expected_results"] == ["盈亏比上升"]
    assert (
        result["candidate_records"][0]["judgment_is_wrong_if"]
        == "盈亏比没有改善"
    )
    assert result["experiment_records"][0]["seen_period"] == {
        "start": "2022-01-01",
        "end": "2022-12-31",
    }


def test_failed_development_report_cannot_be_frozen_by_median_metrics():
    state = init_state(
        "test uneven development folds",
        max_epochs=2,
        experiment_spec={
            "validate_start": "2022-01-01",
            "validate_end": "2024-12-31",
            "backtest_start": "2025-01-01",
            "backtest_end": "2025-12-31",
            "evaluation": {"min_sharpe_ratio": 0.5},
        },
    )
    state["phase"] = "backtest"
    state["development_report"] = {
        "period_kind": "development",
        "passed": False,
        "median_sharpe": 0.8,
        "worst_fold_sharpe": -1.1,
    }
    state["test_result"] = _backtest_result(sharpe=0.8, passed=False)

    result = ManagerAgent().dispatch(state)

    assert result["phase"] == "hypothesis"
    assert result["quality_passed"] is False
    assert result["candidate_frozen"] is False
    assert result["research_trial_count"] == 1


def test_passing_development_result_waits_for_explicit_final_test_approval():
    state = init_state(
        "test idea",
        experiment_spec={
            "validate_start": "2022-01-01",
            "validate_end": "2022-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
            "evaluation": {"min_sharpe_ratio": 1.0},
        },
    )
    state["phase"] = "backtest"
    state["test_result"] = _backtest_result()

    result = ManagerAgent().dispatch(state)

    assert result["phase"] == "done"
    assert result["candidate_frozen"] is True
    assert result["awaiting_final_test_approval"] is True
    assert result["final_test_count"] == 0
    assert result["backtest_feedback"] == ""


def test_approved_final_test_uses_separate_result_and_never_becomes_feedback():
    state = init_state(
        "test idea",
        experiment_spec={
            "validate_start": "2022-01-01",
            "validate_end": "2022-12-31",
            "backtest_start": "2023-01-01",
            "backtest_end": "2023-12-31",
            "allow_final_test": True,
            "evaluation": {"min_sharpe_ratio": 1.0},
        },
    )
    state["phase"] = "backtest"
    state["test_result"] = _backtest_result()

    scheduled = ManagerAgent().dispatch(state)

    assert scheduled["phase"] == "final_test"
    assert scheduled["test_result"] is None
    assert scheduled["research_trial_count"] == 1
    assert scheduled["candidate_frozen"] is True

    final_result = _backtest_result(sharpe=0.4, passed=False)
    scheduled["test_result"] = final_result
    scheduled["backtest_feedback"] = "development feedback must be cleared"
    completed = ManagerAgent().dispatch(scheduled)

    assert completed["phase"] == "done"
    assert completed["final_test_result"] is final_result
    assert completed["final_quality_passed"] is False
    assert completed["backtest_feedback"] == ""
    assert completed["final_test_count"] == 1
    assert completed["experiment_records"][-1]["period_kind"] == "final_test"
    assert completed["experiment_records"][-1]["seen_period"] == {
        "start": "2023-01-01",
        "end": "2023-12-31",
    }


def test_backtest_feedback_keeps_event_metrics_for_next_iteration():
    result = BacktestResult(
        annual_return=0.02,
        sharpe=0.4,
        max_drawdown=-1000.0,
        passed=False,
        summary=(
            "event_count=12, event_net_mean=0.0400%, "
            "target_buy_up_70=42.00%"
        ),
        trade_count=12,
        win_rate=0.5,
    )

    feedback = ManagerAgent._build_backtest_feedback(result)

    assert "event_net_mean=0.0400%" in feedback
    assert "target_buy_up_70=42.00%" in feedback
