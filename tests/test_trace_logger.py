from __future__ import annotations

import builtins

import pytest

from quanta_agents.trace_logger import print_agent_progress


@pytest.mark.parametrize(
    "error",
    [
        OSError(22, "Invalid argument"),
        BrokenPipeError(32, "Broken pipe"),
        ValueError("I/O operation on closed file"),
    ],
)
def test_print_agent_progress_does_not_stop_work_when_output_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    def fail_print(*args: object, **kwargs: object) -> None:
        raise error

    monkeypatch.setattr(builtins, "print", fail_print)

    print_agent_progress(
        {"experiment_id": "exp_test", "epoch_index": 1},
        agent_name="StrategyTester",
        message="starting",
        output="details",
    )
