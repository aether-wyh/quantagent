from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_frozen_final_test


def _ready_state() -> dict[str, object]:
    code = (
        "params = {'threshold': 1}\n"
        "strategy_output = {'output_weights_df': {"
        "'description': 'test', "
        "'function_name': 'output_weights', "
        "'datetime_column': 'trigger_ts'}}\n"
    )
    code_sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest()
    return {
        "phase": "final_test",
        "candidate_frozen": True,
        "ready_for_final": True,
        "final_test_count": 0,
        "current_candidate_id": "candidate_011",
        "strategy_code": code,
        "strategy_result": {
            "params": {"threshold": 1},
            "strategy_output": {
                "output_weights_df": {
                    "description": "test",
                    "function_name": "output_weights",
                    "datetime_column": "trigger_ts",
                }
            },
        },
        "experiment_spec": {
            "experiment_id": "final_2025",
            "frozen_strategy_code_sha256": code_sha256,
            "final_test_attempt": 1,
            "technical_retry_of": "",
        },
        "final_test_period": {
            "start": "2025-01-01",
            "end": "2025-12-31",
        },
    }


def test_run_final_test_only_calls_tester_then_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _ready_state()
    calls: list[str] = []
    started: list[dict[str, object]] = []

    class FakeTester:
        pass

    class FakeManager:
        @staticmethod
        def dispatch(tested_state):
            calls.append("manager")
            tested_state["phase"] = "done"
            tested_state["final_test_count"] = 1
            tested_state["final_test_result"] = SimpleNamespace(
                passed=False,
                summary="final result",
            )
            return tested_state

    def fake_tester_step(tester, tested_state, *, period_kind):
        assert isinstance(tester, FakeTester)
        assert period_kind == "final_test"
        calls.append("final_test")
        tested_state["phase"] = "final_test"
        return tested_state

    monkeypatch.setattr(run_frozen_final_test, "StrategyTester", FakeTester)
    monkeypatch.setattr(run_frozen_final_test, "ManagerAgent", FakeManager)
    monkeypatch.setattr(
        run_frozen_final_test,
        "_run_tester_step",
        fake_tester_step,
    )
    monkeypatch.setattr(
        run_frozen_final_test,
        "write_trace_json",
        lambda *args, **kwargs: started.append(dict(kwargs["payload"])),
    )

    result = run_frozen_final_test.run_final_test_only(state)

    assert calls == ["final_test", "manager"]
    assert result["phase"] == "done"
    assert result["final_test_count"] == 1
    assert started[0]["candidate_id"] == "candidate_011"
    assert started[0]["final_test_count_before_start"] == 0
    assert started[0]["final_test_attempt"] == 1
    assert started[0]["strategy_output"] == state["strategy_result"][
        "strategy_output"
    ]


def test_run_final_test_only_rejects_parameter_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _ready_state()

    def fake_tester_step(tester, tested_state, *, period_kind):
        tested_state["strategy_result"]["params"]["threshold"] = 2
        tested_state["phase"] = "final_test"
        return tested_state

    monkeypatch.setattr(
        run_frozen_final_test,
        "_run_tester_step",
        fake_tester_step,
    )
    monkeypatch.setattr(
        run_frozen_final_test,
        "write_trace_json",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(RuntimeError, match="修改了冻结参数"):
        run_frozen_final_test.run_final_test_only(state)


def test_main_sets_event_environment_and_uses_exact_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_path = tmp_path / "events.parquet"
    event_path.write_bytes(b"test")
    state = _ready_state()
    observed: dict[str, object] = {}

    def fake_restore(**kwargs):
        observed["restore"] = kwargs
        return state

    def fake_run(restored_state):
        assert restored_state is state
        restored_state["phase"] = "done"
        restored_state["final_test_count"] = 1
        restored_state["final_quality_passed"] = False
        restored_state["final_test_result"] = SimpleNamespace(
            passed=False,
            summary="2025 result",
        )
        return restored_state

    monkeypatch.setattr(
        run_frozen_final_test,
        "restore_frozen_candidate_for_final_test",
        fake_restore,
    )
    monkeypatch.setattr(run_frozen_final_test, "run_final_test_only", fake_run)
    for key in (
        "QUANTA_DATA_ENGINE",
        "QUANTA_BACKTEST_DB_BACKEND",
        "QUANTA_EVENT_FEATURES_PATH",
        "QUANTA_MINUTE_EVENT_FEATURES_PATH",
        "QUANTA_RUN_FINAL_TEST",
        "QUANTA_ALLOW_FINAL_TEST",
    ):
        monkeypatch.setenv(key, "test-original")

    result = run_frozen_final_test.main(
        [
            "--source-experiment",
            "source_experiment",
            "--source-yaml",
            "experiments/source.yaml",
            "--candidate",
            "candidate_011",
            "--expected-code-sha256",
            state["experiment_spec"]["frozen_strategy_code_sha256"],
            "--new-experiment",
            "final_2025",
            "--max-epochs",
            "15",
            "--event-path",
            str(event_path),
        ]
    )

    assert result == 0
    assert observed["restore"] == {
        "source_experiment_id": "source_experiment",
        "source_yaml": "experiments/source.yaml",
        "expected_candidate_id": "candidate_011",
        "expected_code_sha256": state["experiment_spec"][
            "frozen_strategy_code_sha256"
        ],
        "new_experiment_id": "final_2025",
        "max_epochs": 15,
        "technical_retry_of": None,
    }
    assert os.environ["QUANTA_DATA_ENGINE"] == "research_parquet"
    assert os.environ["QUANTA_BACKTEST_DB_BACKEND"] == "event_parquet"
    assert os.environ["QUANTA_EVENT_FEATURES_PATH"] == str(event_path.resolve())
    assert os.environ["QUANTA_RUN_FINAL_TEST"] == "true"
    assert os.environ["QUANTA_ALLOW_FINAL_TEST"] == "true"
