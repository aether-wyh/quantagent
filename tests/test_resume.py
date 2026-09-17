from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

import quanta_agents.resume as resume_module
from quanta_agents.agents import StrategyTester
from quanta_agents.resume import (
    _backtest_feedback_from_last_development_candidate,
    _cap_required_data,
    _hide_final_dates,
    restore_frozen_candidate_for_final_test,
    restore_latest_diagnostics_state_from_trace,
    restore_next_hypothesis_state_from_trace,
)


def test_resume_caps_required_data_before_final_period() -> None:
    result = _cap_required_data(
        [
            {
                "table_key": "events",
                "time_range": {"start": "2022-01-01", "end": "2025-12-31"},
            }
        ],
        latest_allowed_date="2024-12-31",
    )

    assert result[0]["time_range"] == {
        "start": "2022-01-01",
        "end": "2024-12-31",
    }


def test_resume_hides_final_dates_from_research_text() -> None:
    text = _hide_final_dates("2025-01-01至2025-12-31为最终回测期")

    assert "2025-01-01" not in text
    assert "2025-12-31" not in text
    assert "不得读取" in text


def test_resume_feedback_uses_last_development_candidate() -> None:
    feedback = _backtest_feedback_from_last_development_candidate(
        [
            {
                "candidate_id": "candidate_001",
                "period_kind": "development",
                "result": {"summary": "第一条开发期结果"},
            },
            {
                "candidate_id": "candidate_002",
                "period_kind": "development",
                "result": {"summary": "最后一条开发期结果"},
            },
            {
                "candidate_id": "candidate_002",
                "period_kind": "final_test",
                "result": {"summary": "不得进入研究提示词的最终期结果"},
            },
        ]
    )

    assert feedback == "最后一条开发期结果"
    assert "最终期结果" not in feedback


def test_resume_feedback_requires_development_candidate() -> None:
    with pytest.raises(FileNotFoundError, match="开发期候选"):
        _backtest_feedback_from_last_development_candidate(
            [
                {
                    "candidate_id": "candidate_001",
                    "period_kind": "final_test",
                    "result": {"summary": "最终期结果"},
                },
                {
                    "candidate_id": "candidate_002",
                    "result": {"summary": "缺少时期标记的结果"},
                },
            ]
        )


def _write_trace(
    path: Path,
    *,
    payload: dict[str, object],
    epoch_index: int,
    agent: str,
    stage: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "logged_at": "2026-08-10T00:00:00+00:00",
                "agent": agent,
                "stage": stage,
                "epoch_index": epoch_index,
                "strategy_validate_round": 1,
                "payload": payload,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _write_candidate_artifacts(
    run_root: Path,
    *,
    epoch_index: int,
    candidate_id: str,
    hypothesis: str,
    summary: str,
    report_marker: str,
    params_value: int,
    research_trial_count: int,
    passed: bool = False,
) -> None:
    epoch_root = run_root / f"epoch_{epoch_index:03d}"
    strategy_params = {
        "candidate": params_value,
        "generic_selection_conditions": [
            {
                "feature": "pulse1_position",
                "operator": ">=",
                "value": params_value,
            }
        ],
    }
    strategy_code = (
        "params = {"
        f"'candidate': {params_value}, "
        "'generic_selection_conditions': ["
        "{'feature': 'pulse1_position', 'operator': '>=', "
        f"'value': {params_value}}}"
        "]}\n"
        "strategy_output = {"
        "'output_weights_df': {"
        "'description': '测试权重', "
        "'function_name': 'output_weights', "
        "'datetime_column': 'trigger_ts'"
        "}}\n"
    )
    strategy_sha256 = hashlib.sha256(strategy_code.encode("utf-8")).hexdigest()
    code_path = (
        epoch_root
        / "strategyagent"
        / "round_001"
        / f"step_01_{candidate_id}.py"
    )
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(strategy_code, encoding="utf-8")

    research_payload: dict[str, object] = {
        "decision": "baseline" if epoch_index == 1 else "test_candidate",
        "candidate_mode": "baseline" if epoch_index == 1 else "refinement",
        "hypothesis": hypothesis,
        "strategy_modification": "" if epoch_index == 1 else "候选二修改",
        "required_data": [
            {
                "table_key": "events",
                "type": "time_series",
                "fields": ["trigger_ts"],
                "time_range": {"start": "2022-01-01", "end": "2025-12-31"},
                "purpose": "研究分钟事件",
            }
        ],
        "backtest_datasets": ["events"],
        "core_hypothesis": f"核心假设{epoch_index}",
        "fixed_parts": ["固定部分"],
        "changeable_parts": ["可改部分"],
        "candidate_directions": [{"id": f"direction_{epoch_index}"}],
        "selected_direction_id": f"direction_{epoch_index}",
        "knowledge_record": {"measured_facts": [report_marker]},
    }
    _write_trace(
        epoch_root
        / "hypothesisagent"
        / "structured_output"
        / f"attempt_01_{candidate_id}.json",
        payload=research_payload,
        epoch_index=epoch_index,
        agent="HypothesisAgent",
        stage="structured_output",
    )
    _write_trace(
        epoch_root
        / "strategyagent"
        / "round_001"
        / "structured_output"
        / f"attempt_01_{candidate_id}.json",
        payload={
            "strategy_generation_meta": {
                "source": candidate_id,
                "strategy_code_sha256": strategy_sha256,
            }
        },
        epoch_index=epoch_index,
        agent="StrategyAgent",
        stage="structured_output",
    )

    development_report: dict[str, object] = {
        "report_kind": "event_parquet",
        "period_kind": "development",
        "passed": passed,
        "development_period": {
            "start": "2024-01-01",
            "end": "2024-12-31",
        },
        "marker": report_marker,
    }
    result: dict[str, object] = {
        "passed": passed,
        "summary": summary,
    }
    candidate: dict[str, object] = {
        "candidate_id": candidate_id,
        "candidate_mode": research_payload["candidate_mode"],
        "strategy_code_sha256": strategy_sha256,
        "strategy_params": strategy_params,
        "epoch_index": epoch_index,
        "strategy_validate_round": 1,
        "hypothesis": hypothesis,
        "strategy_modification": research_payload["strategy_modification"],
        "period_kind": "development",
        "seen_period": {"start": "2024-01-01", "end": "2024-12-31"},
        "result": result,
        "research_decision": research_payload["decision"],
        "knowledge_record": research_payload["knowledge_record"],
        "candidate_directions": research_payload["candidate_directions"],
        "selected_direction_id": research_payload["selected_direction_id"],
        "development_report": development_report,
    }
    experiment: dict[str, object] = {
        "trial_id": f"trial_{epoch_index:04d}",
        "candidate_id": candidate_id,
        "period_kind": "development",
        "seen_period": {"start": "2024-01-01", "end": "2024-12-31"},
        "result": result,
    }
    _write_trace(
        epoch_root
        / "manageragent"
        / "candidate_record"
        / f"{candidate_id}.json",
        payload={
            "candidate": candidate,
            "experiment": experiment,
            "research_trial_count": research_trial_count,
            "technical_retry_count": 0,
            "final_test_count": 0,
        },
        epoch_index=epoch_index,
        agent="ManagerAgent",
        stage="candidate_record",
    )


def _write_final_test_source_yaml(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """user_idea: 测试冻结候选
train_start: "2022-01-01"
train_end: "2023-12-31"
validate_start: "2024-01-01"
validate_end: "2024-12-31"
backtest_start: "2025-01-01"
backtest_end: "2025-12-31"
backtest_mode: event_parquet
universe:
  - symbols: dataset:events
    asset: 中国股票
    description: 测试事件
""",
        encoding="utf-8",
    )


def _normalized_code_sha256(path: Path) -> str:
    code = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _write_failed_final_test_attempt(
    trace_root: Path,
    *,
    experiment_id: str,
    candidate_id: str,
    code_sha256: str,
    strategy_params: dict[str, object],
    final_period: dict[str, str],
    result: dict[str, object] | None = None,
    error: str = (
        "backtest_error: "
        "strategy_output.output_weights_df.datetime_column is required"
    ),
) -> None:
    run_root = trace_root / experiment_id / "epochs_15" / "epoch_011"
    _write_trace(
        run_root
        / "finaltestrunner"
        / "final_test_started"
        / "started.json",
        payload={
            "candidate_id": candidate_id,
            "strategy_code_sha256": code_sha256,
            "strategy_params": strategy_params,
            "final_test_period": final_period,
            "final_test_count_before_start": 0,
            "final_test_attempt": 1,
            "technical_retry_of": "",
        },
        epoch_index=11,
        agent="FinalTestRunner",
        stage="final_test_started",
    )
    recorded_result = {} if result is None else result
    candidate = {
        "candidate_id": candidate_id,
        "period_kind": "final_test",
        "strategy_code_sha256": code_sha256,
        "strategy_params": strategy_params,
        "seen_period": final_period,
        "result": recorded_result,
        "error": error,
    }
    experiment = {
        "candidate_id": candidate_id,
        "period_kind": "final_test",
        "strategy_code_sha256": code_sha256,
        "seen_period": final_period,
        "result": recorded_result,
        "error": error,
    }
    _write_trace(
        run_root / "manageragent" / "candidate_record" / "failed.json",
        payload={
            "candidate": candidate,
            "experiment": experiment,
            "research_trial_count": 11,
            "technical_retry_count": 1,
            "final_test_count": 1,
        },
        epoch_index=11,
        agent="ManagerAgent",
        stage="candidate_record",
    )


def test_restore_frozen_candidate_prepares_only_final_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    written: list[dict[str, object]] = []
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: written.append(dict(kwargs["payload"])),
    )

    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    run_root = (
        tmp_path
        / "experiment_traces"
        / "source_experiment"
        / "epochs_15"
    )
    _write_candidate_artifacts(
        run_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    code_path = next(
        run_root.glob(
            "epoch_011/strategyagent/round_001/step_01_candidate_011.py"
        )
    )
    code_sha256 = _normalized_code_sha256(code_path)

    state = restore_frozen_candidate_for_final_test(
        source_experiment_id="source_experiment",
        source_yaml=source_yaml,
        expected_candidate_id="candidate_011",
        expected_code_sha256=code_sha256,
        new_experiment_id="candidate_011_final_2025",
        max_epochs=15,
    )

    assert state["phase"] == "final_test"
    assert state["evaluation_stage"] == "final_test"
    assert state["epoch_index"] == 11
    assert state["current_candidate_id"] == "candidate_011"
    assert state["candidate_frozen"] is True
    assert state["quality_passed"] is True
    assert state["ready_for_final"] is True
    assert state["awaiting_final_test_approval"] is False
    assert state["test_result"] is None
    assert state["final_test_result"] is None
    assert state["final_test_count"] == 0
    assert state["backtest_feedback"] == ""
    assert state["strategy_result"]["params"] == {
        "candidate": 11,
        "generic_selection_conditions": [
            {
                "feature": "pulse1_position",
                "operator": ">=",
                "value": 11,
            }
        ],
    }
    assert state["strategy_result"]["strategy_output"] == {
        "output_weights_df": {
            "description": "测试权重",
            "function_name": "output_weights",
            "datetime_column": "trigger_ts",
        }
    }
    assert state["experiment_spec"]["run_final_test"] is True
    assert state["experiment_spec"]["allow_final_test"] is True
    assert state["experiment_spec"]["frozen_candidate_id"] == "candidate_011"
    assert state["experiment_spec"]["frozen_strategy_code_sha256"] == code_sha256
    assert state["experiment_spec"]["final_test_attempt"] == 1
    assert state["experiment_spec"]["technical_retry_of"] == ""
    assert state["development_period"] == {
        "start": "2024-01-01",
        "end": "2024-12-31",
    }
    assert state["final_test_period"] == {
        "start": "2025-01-01",
        "end": "2025-12-31",
    }
    assert written[0]["candidate_id"] == "candidate_011"
    assert written[0]["final_test_count"] == 0
    assert written[0]["strategy_output"] == state["strategy_result"][
        "strategy_output"
    ]


def test_restored_strategy_output_passes_real_tester_time_column_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored.json",
    )
    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    source_root = tmp_path / "experiment_traces" / "source" / "epochs_15"
    _write_candidate_artifacts(
        source_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    code_path = next(
        source_root.glob("epoch_011/strategyagent/round_001/*.py")
    )
    state = restore_frozen_candidate_for_final_test(
        source_experiment_id="source",
        source_yaml=source_yaml,
        expected_candidate_id="candidate_011",
        expected_code_sha256=_normalized_code_sha256(code_path),
        new_experiment_id="real_tester_check",
        max_epochs=15,
    )
    strategy_result = dict(state["strategy_result"])
    strategy_result["output_weights"] = pd.DataFrame(
        {
            "trigger_ts": [pd.Timestamp("2025-01-02 10:00:00")],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )

    template, base_class, normalized, tradable_columns = (
        StrategyTester._resolve_template_from_output_weights_df(
            strategy_result
        )
    )
    StrategyTester._validate_event_long_only_weights(
        normalized,
        tradable_columns,
    )

    assert template == "portfolio"
    assert base_class == "StrategyTemplate"
    assert isinstance(normalized.index, pd.DatetimeIndex)
    assert normalized.index[0] == pd.Timestamp("2025-01-02 10:00:00")
    assert tradable_columns == ["sh600000"]


def test_restore_frozen_candidate_allows_one_empty_result_technical_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    written: list[dict[str, object]] = []
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: written.append(dict(kwargs["payload"])),
    )
    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    source_root = tmp_path / "experiment_traces" / "source" / "epochs_15"
    _write_candidate_artifacts(
        source_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    code_path = next(
        source_root.glob("epoch_011/strategyagent/round_001/*.py")
    )
    code_sha256 = _normalized_code_sha256(code_path)
    frozen_params = {
        "candidate": 11,
        "generic_selection_conditions": [
            {
                "feature": "pulse1_position",
                "operator": ">=",
                "value": 11,
            }
        ],
    }
    final_period = {"start": "2025-01-01", "end": "2025-12-31"}
    _write_failed_final_test_attempt(
        tmp_path / "experiment_traces",
        experiment_id="failed_final",
        candidate_id="candidate_011",
        code_sha256=code_sha256,
        strategy_params=frozen_params,
        final_period=final_period,
    )

    state = restore_frozen_candidate_for_final_test(
        source_experiment_id="source",
        source_yaml=source_yaml,
        expected_candidate_id="candidate_011",
        expected_code_sha256=code_sha256,
        new_experiment_id="final_retry_once",
        max_epochs=15,
        technical_retry_of="failed_final",
    )

    assert state["phase"] == "final_test"
    assert state["current_candidate_id"] == "candidate_011"
    assert state["experiment_spec"]["final_test_attempt"] == 2
    assert state["experiment_spec"]["technical_retry_of"] == "failed_final"
    assert state["technical_retry_count"] == 1
    assert state["final_test_count"] == 0
    assert state["strategy_result"]["params"] == frozen_params
    assert state["strategy_result"]["strategy_output"]["output_weights_df"][
        "datetime_column"
    ] == "trigger_ts"
    assert written[0]["final_test_attempt"] == 2
    assert written[0]["technical_retry_of"] == "failed_final"
    assert written[0]["technical_retry_validation"]["error"] == (
        "backtest_error: "
        "strategy_output.output_weights_df.datetime_column is required"
    )


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("result", "包含测试结果"),
        ("missing_error", "没有技术错误"),
        ("other_error", "不是允许重试"),
        ("candidate", "候选编号不一致"),
        ("params", "冻结参数不一致"),
        ("period", "时期不一致"),
    ],
)
def test_technical_retry_rejects_changed_or_viewable_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    message: str,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored.json",
    )
    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    source_root = tmp_path / "experiment_traces" / "source" / "epochs_15"
    _write_candidate_artifacts(
        source_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    code_path = next(
        source_root.glob("epoch_011/strategyagent/round_001/*.py")
    )
    code_sha256 = _normalized_code_sha256(code_path)
    frozen_params = {
        "candidate": 11,
        "generic_selection_conditions": [
            {
                "feature": "pulse1_position",
                "operator": ">=",
                "value": 11,
            }
        ],
    }
    recorded_candidate = "candidate_999" if case == "candidate" else "candidate_011"
    recorded_params = (
        {"candidate": 999}
        if case == "params"
        else frozen_params
    )
    recorded_period = (
        {"start": "2025-02-01", "end": "2025-12-31"}
        if case == "period"
        else {"start": "2025-01-01", "end": "2025-12-31"}
    )
    recorded_result = {"passed": False} if case == "result" else None
    if case == "missing_error":
        recorded_error = ""
    elif case == "other_error":
        recorded_error = "backtest_error: unrelated failure"
    else:
        recorded_error = (
            "backtest_error: "
            "strategy_output.output_weights_df.datetime_column is required"
        )
    _write_failed_final_test_attempt(
        tmp_path / "experiment_traces",
        experiment_id="failed_final",
        candidate_id=recorded_candidate,
        code_sha256=code_sha256,
        strategy_params=recorded_params,
        final_period=recorded_period,
        result=recorded_result,
        error=recorded_error,
    )

    with pytest.raises((ValueError, RuntimeError), match=message):
        restore_frozen_candidate_for_final_test(
            source_experiment_id="source",
            source_yaml=source_yaml,
            expected_candidate_id="candidate_011",
            expected_code_sha256=code_sha256,
            new_experiment_id="retry_must_fail",
            max_epochs=15,
            technical_retry_of="failed_final",
        )


def test_technical_retry_rejects_a_second_started_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored.json",
    )
    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    source_root = tmp_path / "experiment_traces" / "source" / "epochs_15"
    _write_candidate_artifacts(
        source_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    code_path = next(
        source_root.glob("epoch_011/strategyagent/round_001/*.py")
    )
    code_sha256 = _normalized_code_sha256(code_path)
    frozen_params = {
        "candidate": 11,
        "generic_selection_conditions": [
            {
                "feature": "pulse1_position",
                "operator": ">=",
                "value": 11,
            }
        ],
    }
    final_period = {"start": "2025-01-01", "end": "2025-12-31"}
    _write_failed_final_test_attempt(
        tmp_path / "experiment_traces",
        experiment_id="failed_final",
        candidate_id="candidate_011",
        code_sha256=code_sha256,
        strategy_params=frozen_params,
        final_period=final_period,
    )
    _write_trace(
        tmp_path
        / "experiment_traces"
        / "second_attempt"
        / "epochs_15"
        / "epoch_011"
        / "finaltestrunner"
        / "final_test_started"
        / "started.json",
        payload={
            "candidate_id": "candidate_011",
            "strategy_code_sha256": code_sha256,
            "strategy_params": frozen_params,
            "final_test_period": final_period,
            "final_test_count_before_start": 0,
            "final_test_attempt": 2,
            "technical_retry_of": "failed_final",
        },
        epoch_index=11,
        agent="FinalTestRunner",
        stage="final_test_started",
    )

    with pytest.raises(RuntimeError, match="只有一次最终测试启动记录"):
        restore_frozen_candidate_for_final_test(
            source_experiment_id="source",
            source_yaml=source_yaml,
            expected_candidate_id="candidate_011",
            expected_code_sha256=code_sha256,
            new_experiment_id="third_attempt_forbidden",
            max_epochs=15,
            technical_retry_of="failed_final",
        )


def test_restore_frozen_candidate_rejects_parameter_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored.json",
    )
    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    run_root = tmp_path / "experiment_traces" / "source" / "epochs_15"
    _write_candidate_artifacts(
        run_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    record_path = next(
        run_root.glob("epoch_011/manageragent/candidate_record/*.json")
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["payload"]["candidate"]["strategy_params"]["candidate"] = 999
    record_path.write_text(
        json.dumps(record, ensure_ascii=False),
        encoding="utf-8",
    )
    code_path = next(
        run_root.glob("epoch_011/strategyagent/round_001/*.py")
    )

    with pytest.raises(ValueError, match="代码参数"):
        restore_frozen_candidate_for_final_test(
            source_experiment_id="source",
            source_yaml=source_yaml,
            expected_candidate_id="candidate_011",
            expected_code_sha256=_normalized_code_sha256(code_path),
            new_experiment_id="final_should_not_start",
            max_epochs=15,
        )


def test_restore_frozen_candidate_rejects_wrong_digest_and_repeat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored.json",
    )
    source_yaml = tmp_path / "experiments" / "source.yaml"
    _write_final_test_source_yaml(source_yaml)
    run_root = tmp_path / "experiment_traces" / "source" / "epochs_15"
    _write_candidate_artifacts(
        run_root,
        epoch_index=11,
        candidate_id="candidate_011",
        hypothesis="冻结候选十一",
        summary="开发期通过",
        report_marker="candidate_011_report",
        params_value=11,
        research_trial_count=11,
        passed=True,
    )
    code_path = next(
        run_root.glob("epoch_011/strategyagent/round_001/*.py")
    )
    code_sha256 = _normalized_code_sha256(code_path)

    with pytest.raises(ValueError, match="明确指定值"):
        restore_frozen_candidate_for_final_test(
            source_experiment_id="source",
            source_yaml=source_yaml,
            expected_candidate_id="candidate_011",
            expected_code_sha256="0" * 64,
            new_experiment_id="wrong_digest",
            max_epochs=15,
        )

    _write_trace(
        tmp_path
        / "experiment_traces"
        / "already_final"
        / "epochs_15"
        / "epoch_011"
        / "finaltestrunner"
        / "final_test_started"
        / "started.json",
        payload={
            "candidate_id": "candidate_011",
            "strategy_code_sha256": code_sha256,
            "final_test_count_before_start": 0,
        },
        epoch_index=11,
        agent="FinalTestRunner",
        stage="final_test_started",
    )

    with pytest.raises(RuntimeError, match="已经执行过最终测试"):
        restore_frozen_candidate_for_final_test(
            source_experiment_id="source",
            source_yaml=source_yaml,
            expected_candidate_id="candidate_011",
            expected_code_sha256=code_sha256,
            new_experiment_id="repeat_should_not_start",
            max_epochs=15,
        )


def test_restore_next_hypothesis_merges_lineage_and_ignores_incomplete_epoch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored_trace.json",
    )

    source_yaml = tmp_path / "experiments" / "source.yaml"
    source_yaml.parent.mkdir(parents=True, exist_ok=True)
    source_yaml.write_text(
        """user_idea: 研究分钟事件，2025-01-01至2025-12-31为最终回测期
train_start: "2022-01-01"
train_end: "2023-12-31"
validate_start: "2024-01-01"
validate_end: "2024-12-31"
backtest_start: "2025-01-01"
backtest_end: "2025-12-31"
universe:
  - symbols: dataset:events
    asset: 中国股票
    description: 测试事件
""",
        encoding="utf-8",
    )

    ancestor_root = (
        tmp_path
        / "experiment_traces"
        / "ancestor_experiment"
        / "epochs_3"
    )
    _write_candidate_artifacts(
        ancestor_root,
        epoch_index=1,
        candidate_id="candidate_001",
        hypothesis="候选一，最终期为2025-01-01至2025-12-31",
        summary="候选一开发期结果",
        report_marker="candidate_001_report",
        params_value=1,
        research_trial_count=1,
    )
    _write_trace(
        ancestor_root
        / "epoch_002"
        / "researchdiagnosticsagent"
        / "diagnostic_report"
        / "ancestor_diagnostic.json",
        payload={
            "request_id": "ancestor_diagnostic",
            "period_access": {"final_period_read": False},
        },
        epoch_index=2,
        agent="ResearchDiagnosticsAgent",
        stage="diagnostic_report",
    )

    source_root = (
        tmp_path
        / "experiment_traces"
        / "resumed_experiment"
        / "epochs_5"
    )
    _write_trace(
        source_root
        / "epoch_002"
        / "resumeloader"
        / "restored_state"
        / "resume.json",
        payload={
            "resumed_from": "ancestor_experiment",
            "new_experiment_id": "resumed_experiment",
            "final_period_read": False,
        },
        epoch_index=2,
        agent="ResumeLoader",
        stage="restored_state",
    )
    _write_trace(
        source_root
        / "epoch_002"
        / "researchdiagnosticsagent"
        / "diagnostic_report"
        / "current_diagnostic.json",
        payload={
            "request_id": "current_diagnostic",
            "period_access": {"final_period_read": False},
        },
        epoch_index=2,
        agent="ResearchDiagnosticsAgent",
        stage="diagnostic_report",
    )
    _write_candidate_artifacts(
        source_root,
        epoch_index=2,
        candidate_id="candidate_002",
        hypothesis="候选二，最终期为2025-01-01至2025-12-31",
        summary="候选二开发期结果",
        report_marker="candidate_002_report",
        params_value=2,
        research_trial_count=2,
    )
    decoy_code_path = (
        source_root
        / "epoch_002"
        / "strategyagent"
        / "round_002"
        / "step_99_decoy.py"
    )
    decoy_code_path.parent.mkdir(parents=True, exist_ok=True)
    decoy_code_path.write_text(
        "params = {'candidate': 999, 'generic_selection_conditions': []}\n",
        encoding="utf-8",
    )

    _write_trace(
        source_root
        / "epoch_003"
        / "hypothesisagent"
        / "structured_output"
        / "incomplete.json",
        payload={
            "hypothesis": "未完成的候选三不得恢复",
            "required_data": [],
            "backtest_datasets": [],
        },
        epoch_index=3,
        agent="HypothesisAgent",
        stage="structured_output",
    )
    _write_trace(
        source_root
        / "epoch_003"
        / "researchdiagnosticsagent"
        / "diagnostic_report"
        / "later_diagnostic.json",
        payload={
            "request_id": "later_diagnostic",
            "period_access": {"final_period_read": False},
        },
        epoch_index=3,
        agent="ResearchDiagnosticsAgent",
        stage="diagnostic_report",
    )
    _write_trace(
        source_root
        / "epoch_002"
        / "manageragent"
        / "candidate_record"
        / "candidate_002_final.json",
        payload={
            "candidate": {
                "candidate_id": "candidate_002",
                "epoch_index": 2,
                "period_kind": "final_test",
                "strategy_params": {"final_secret": "FINAL_PARAMS_SECRET"},
                "result": {"summary": "最终期结果不得恢复"},
            }
        },
        epoch_index=2,
        agent="ManagerAgent",
        stage="candidate_record",
    )

    state = restore_next_hypothesis_state_from_trace(
        source_experiment_id="resumed_experiment",
        source_yaml=source_yaml,
        new_experiment_id="new_experiment",
        max_epochs=5,
        expected_candidate_id="candidate_002",
    )

    assert state["phase"] == "hypothesis"
    assert state["research_stage"] == "iteration"
    assert state["epoch_index"] == 3
    assert state["current_candidate_id"] == "candidate_003"
    assert [
        record["candidate_id"] for record in state["candidate_records"]
    ] == ["candidate_001", "candidate_002"]
    assert [
        record["strategy_params"]["candidate"]
        for record in state["candidate_records"]
    ] == [1, 2]
    assert state["candidate_records"][1]["strategy_params"][
        "generic_selection_conditions"
    ] == [
        {"feature": "pulse1_position", "operator": ">=", "value": 2}
    ]
    assert state["research_trial_count"] == 2
    assert state["development_report"]["marker"] == "candidate_002_report"
    assert state["backtest_feedback"] == "候选二开发期结果"
    assert "candidate': 2" in state["strategy_code"]
    assert state["strategy_generation_meta"]["source"] == "candidate_002"
    assert state["hypothesis_generation_meta"]["knowledge_record"] == {
        "measured_facts": ["candidate_002_report"]
    }
    assert "未完成的候选三" not in str(state["hypothesis_generation_meta"])
    assert state["hypothesis_generation_meta"]["required_data"][0]["time_range"][
        "end"
    ] == "2024-12-31"
    assert state["translation_meta"]["core_hypothesis"] == "核心假设1"
    assert [
        report["request_id"] for report in state["diagnostic_records"]
    ] == ["ancestor_diagnostic", "current_diagnostic"]
    assert state["final_test_period"] == {}
    assert state["final_test_result"] is None
    assert state["final_test_count"] == 0
    assert state["experiment_spec"]["run_final_test"] is False
    assert state["experiment_spec"]["allow_final_test"] is False
    assert "backtest_start" not in state["experiment_spec"]
    assert "2025-01-01" not in state["experiment_spec"]["user_idea"]
    assert "最终期结果" not in str(state)
    assert "FINAL_PARAMS_SECRET" not in str(state)

    with pytest.raises(FileNotFoundError, match="candidate_003"):
        restore_next_hypothesis_state_from_trace(
            source_experiment_id="resumed_experiment",
            source_yaml=source_yaml,
            new_experiment_id="should_not_start",
            max_epochs=5,
            expected_candidate_id="candidate_003",
        )


def test_restore_latest_diagnostics_uses_ancestor_candidate_without_new_trial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resume_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        resume_module,
        "write_trace_json",
        lambda *args, **kwargs: tmp_path / "ignored_trace.json",
    )

    source_yaml = tmp_path / "experiments" / "source.yaml"
    source_yaml.parent.mkdir(parents=True, exist_ok=True)
    source_yaml.write_text(
        """user_idea: 研究分钟事件，2025-01-01至2025-12-31为最终回测期
train_start: "2022-01-01"
train_end: "2023-12-31"
validate_start: "2024-01-01"
validate_end: "2024-12-31"
backtest_start: "2025-01-01"
backtest_end: "2025-12-31"
universe:
  - symbols: dataset:events
    asset: 中国股票
    description: 测试事件
""",
        encoding="utf-8",
    )

    ancestor_root = (
        tmp_path
        / "experiment_traces"
        / "candidate_source"
        / "epochs_5"
    )
    for epoch_index in (1, 2, 3):
        _write_candidate_artifacts(
            ancestor_root,
            epoch_index=epoch_index,
            candidate_id=f"candidate_{epoch_index:03d}",
            hypothesis=f"候选{epoch_index}，最终期为2025-01-01至2025-12-31",
            summary=f"候选{epoch_index}开发期结果",
            report_marker=f"candidate_{epoch_index:03d}_report",
            params_value=epoch_index,
            research_trial_count=epoch_index,
        )

    source_root = (
        tmp_path
        / "experiment_traces"
        / "diagnose_only_source"
        / "epochs_5"
    )
    _write_trace(
        source_root
        / "epoch_004"
        / "resumeloader"
        / "restored_state"
        / "resume.json",
        payload={
            "resumed_from": "candidate_source",
            "new_experiment_id": "diagnose_only_source",
            "candidate_record_count": 3,
            "research_trial_count": 3,
            "final_period_read": False,
        },
        epoch_index=4,
        agent="ResumeLoader",
        stage="restored_state",
    )
    _write_trace(
        source_root
        / "epoch_004"
        / "researchdiagnosticsagent"
        / "diagnostic_report"
        / "existing_report.json",
        payload={
            "request_id": "candidate_003_epoch_004_diagnostic_01",
            "source_candidate_id": "candidate_003",
            "research_epoch": 4,
            "period_access": {"final_period_read": False},
            "results": [{"id": "period_metrics", "status": "completed"}],
        },
        epoch_index=4,
        agent="ResearchDiagnosticsAgent",
        stage="diagnostic_report",
    )
    _write_trace(
        source_root
        / "epoch_004"
        / "hypothesisagent"
        / "structured_output"
        / "diagnose_only.json",
        payload={
            "decision": "diagnose_only",
            "candidate_mode": "diagnose_only",
            "hypothesis": "候选3，最终期为2025-01-01至2025-12-31",
            "strategy_modification": "",
            "required_data": [
                {
                    "table_key": "events",
                    "type": "time_series",
                    "fields": ["trigger_ts"],
                    "time_range": {
                        "start": "2022-01-01",
                        "end": "2025-12-31",
                    },
                    "purpose": "研究分钟事件",
                }
            ],
            "backtest_datasets": ["events"],
            "requested_diagnostics": [
                {
                    "id": "execution_price_audit",
                    "reason": "核对成交价格",
                    "parameters": {},
                    "decision_if_positive": "继续候选研究",
                    "decision_if_negative": "修正取价定义",
                }
            ],
            "knowledge_record": {
                "measured_facts": ["已有固定分析应当保留"]
            },
        },
        epoch_index=4,
        agent="HypothesisAgent",
        stage="structured_output",
    )

    state = restore_latest_diagnostics_state_from_trace(
        source_experiment_id="diagnose_only_source",
        source_yaml=source_yaml,
        new_experiment_id="diagnostics_v2",
        max_epochs=5,
        expected_candidate_id="candidate_003",
    )

    assert state["phase"] == "diagnostics"
    assert state["epoch_index"] == 4
    assert state["current_candidate_id"] == "candidate_004"
    assert state["research_trial_count"] == 3
    assert [
        record["candidate_id"] for record in state["candidate_records"]
    ] == ["candidate_001", "candidate_002", "candidate_003"]
    assert [
        record["strategy_params"]["candidate"]
        for record in state["candidate_records"]
    ] == [1, 2, 3]
    assert state["development_report"]["marker"] == "candidate_003_report"
    assert state["backtest_feedback"] == "候选3开发期结果"
    assert "candidate': 3" in state["strategy_code"]
    assert state["hypothesis_generation_meta"]["decision"] == "diagnose_only"
    assert state["hypothesis_generation_meta"]["required_data"][0]["time_range"][
        "end"
    ] == "2024-12-31"
    assert state["diagnostic_round"] == 1
    assert [
        report["request_id"] for report in state["diagnostic_records"]
    ] == ["candidate_003_epoch_004_diagnostic_01"]
    assert state["diagnostic_request"]["source_candidate_id"] == "candidate_003"
    assert state["diagnostic_request"]["research_epoch"] == 4
    assert state["diagnostic_request"]["request_id"] == (
        "candidate_003_epoch_004_diagnostic_02"
    )
    assert [
        item["id"] for item in state["diagnostic_request"]["items"]
    ] == ["execution_price_audit"]
    assert state["final_test_period"] == {}
    assert state["final_test_result"] is None
    assert state["final_test_count"] == 0
    assert state["experiment_spec"]["run_final_test"] is False
    assert state["experiment_spec"]["allow_final_test"] is False
    assert "2025-01-01" not in state["experiment_spec"]["user_idea"]
