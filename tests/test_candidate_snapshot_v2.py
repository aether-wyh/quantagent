from __future__ import annotations

import pandas as pd
import pytest

from quanta_agents.candidate_snapshot import (
    capture_candidate_snapshot,
    restore_accepted_snapshot,
    restore_candidate_snapshot,
)


def _candidate_state() -> dict[str, object]:
    return {
        "current_candidate_id": "candidate_003",
        "strategy_code": "params = {'threshold': 0.5}",
        "code_text": "params = {'threshold': 0.5}",
        "strategy_result": {
            "params": {"threshold": 0.5},
            "output_weights": pd.DataFrame({"600000.SH": [0.1, 0.0]}),
        },
        "strategy_generation_meta": {"source": "candidate_002"},
        "hypothesis_generation_meta": {"hypothesis": "基准假设"},
        "development_report": {"passed": True, "fold_pass_ratio": 1.0},
    }


def test_capture_candidate_snapshot_keeps_an_independent_accepted_copy() -> None:
    state = _candidate_state()

    snapshot = capture_candidate_snapshot(state)

    assert snapshot["candidate_id"] == "candidate_003"
    assert state["accepted_candidate_id"] == "candidate_003"
    accepted = state["accepted_snapshot"]
    assert accepted["candidate_id"] == snapshot["candidate_id"]  # type: ignore[index]
    assert accepted["strategy_code"] == snapshot["strategy_code"]  # type: ignore[index]
    pd.testing.assert_frame_equal(
        accepted["strategy_result"]["output_weights"],  # type: ignore[index]
        snapshot["strategy_result"]["output_weights"],  # type: ignore[index]
    )

    state["strategy_result"]["params"]["threshold"] = 0.9  # type: ignore[index]
    assert accepted["strategy_result"]["params"]["threshold"] == 0.5  # type: ignore[index]


def test_restore_accepted_snapshot_restores_candidate_and_clears_work_results() -> None:
    state = _candidate_state()
    capture_candidate_snapshot(state)

    state.update(
        {
            "current_candidate_id": "candidate_004",
            "strategy_code": "params = {'threshold': 0.9}",
            "code_text": "params = {'threshold': 0.9}",
            "strategy_result": {"params": {"threshold": 0.9}},
            "strategy_generation_meta": {"source": "candidate_003"},
            "hypothesis_generation_meta": {"hypothesis": "失败假设"},
            "development_report": {"passed": False},
            "test_result": object(),
            "final_test_result": object(),
            "validation_result": {"passed": False},
            "validation_summary": {"passed": False},
            "validation_feedback": {"error": "验证失败"},
            "last_test_error": "回测失败",
            "backtest_feedback": "失败结果",
            "quality_passed": True,
            "candidate_frozen": True,
            "formal_trial_status": "failed",
            "judge_result": {"adopted": False},
            "strategy_validate_round": 3,
        }
    )

    restored = restore_accepted_snapshot(state)

    assert restored["current_candidate_id"] == "candidate_003"
    assert restored["strategy_code"] == "params = {'threshold': 0.5}"
    assert restored["strategy_result"]["params"] == {"threshold": 0.5}  # type: ignore[index]
    assert restored["strategy_generation_meta"] == {"source": "candidate_002"}
    assert restored["hypothesis_generation_meta"] == {"hypothesis": "基准假设"}
    assert restored["development_report"] == {"passed": True, "fold_pass_ratio": 1.0}
    assert restored["test_result"] is None
    assert restored["final_test_result"] is None
    assert restored["validation_result"] == {}
    assert restored["validation_summary"] == {}
    assert restored["validation_feedback"] == {}
    assert restored["last_test_error"] == ""
    assert restored["backtest_feedback"] == ""
    assert restored["quality_passed"] is False
    assert restored["candidate_frozen"] is False
    assert restored["formal_trial_status"] == ""
    assert restored["judge_result"] == {}
    assert restored["strategy_validate_round"] == 1


def test_restore_candidate_snapshot_rejects_incomplete_snapshot() -> None:
    with pytest.raises(ValueError, match="缺少字段"):
        restore_candidate_snapshot(
            _candidate_state(),
            {"snapshot_version": 2, "candidate_id": "candidate_003"},
        )


def test_snapshot_reuses_large_frames_but_copies_params() -> None:
    state = _candidate_state()
    frame = pd.DataFrame({"x": [1.0]})
    state["strategy_result"] = {
        "output_weights": frame,
        "train_data_bundle": {"daily": frame},
        "params": {"window": 30},
    }

    snapshot = capture_candidate_snapshot(state)

    assert snapshot["strategy_result"]["output_weights"] is frame  # type: ignore[index]
    assert snapshot["strategy_result"]["train_data_bundle"]["daily"] is frame  # type: ignore[index]
    state["strategy_result"]["params"]["window"] = 10  # type: ignore[index]
    assert snapshot["strategy_result"]["params"]["window"] == 30  # type: ignore[index]
