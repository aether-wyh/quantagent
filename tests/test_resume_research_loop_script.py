from __future__ import annotations

import os
from pathlib import Path

from scripts import resume_research_loop


def test_raw_minute_dir_default_matches_minute_run_script(monkeypatch) -> None:
    monkeypatch.delenv("QUANTA_RAW_MINUTE_DATA_DIR", raising=False)

    args = resume_research_loop.parse_args(["--source-experiment", "exp_source"])

    assert Path(args.raw_minute_dir) == resume_research_loop.DEFAULT_RAW_MINUTE_DATA_DIR


def test_main_sets_requested_raw_minute_dir_before_workflow(
    tmp_path, monkeypatch
) -> None:
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    observed: dict[str, str] = {}
    state = {
        "experiment_spec": {"experiment_id": "exp_new"},
        "epoch_index": 2,
        "phase": "diagnostics",
    }

    monkeypatch.setattr(
        resume_research_loop,
        "restore_research_state_from_trace",
        lambda **kwargs: state,
    )

    def fake_continue_workflow(restored_state):
        observed["raw_minute_dir"] = os.environ["QUANTA_RAW_MINUTE_DATA_DIR"]
        return restored_state

    monkeypatch.setattr(
        resume_research_loop, "continue_workflow", fake_continue_workflow
    )
    for key in (
        "QUANTA_EVENT_FEATURES_PATH",
        "QUANTA_MINUTE_EVENT_FEATURES_PATH",
        "QUANTA_RAW_MINUTE_DATA_DIR",
        "QUANTA_RUN_FINAL_TEST",
        "QUANTA_ALLOW_FINAL_TEST",
    ):
        monkeypatch.setenv(key, "test-original")

    result = resume_research_loop.main(
        [
            "--source-experiment",
            "exp_source",
            "--raw-minute-dir",
            str(raw_directory),
        ]
    )

    assert result == 0
    assert observed["raw_minute_dir"] == str(raw_directory)
