"""Generated subprocess fixtures; no model or market/account execution."""
import json
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from quanta_agents.meta_v6.jobs import run_job


def command(code):
    return [sys.executable, "-c", code]


def test_normal_exit_preserves_output_and_terminal_receipt(tmp_path):
    out = tmp_path / "job"
    result = run_job(command("from pathlib import Path; print('observed'); Path('worker_checkpoint.json').write_text('saved')"),
        cwd=tmp_path, output_dir=out, timeout_seconds=5)
    assert result["status"] == "completed"
    assert result["primary_exit_code"] == 0 and result["all_owned_processes_exited"]
    assert "observed" in (out / "worker.log").read_text()
    assert json.loads((out / "job_result.json").read_text())["status"] == "completed"
    assert result["process_outcome_only"] and result["automatic_retry"] is False
    with pytest.raises(FileExistsError):
        run_job(command("raise Exception('must not execute')"), cwd=tmp_path, output_dir=out, timeout_seconds=1)


def test_sleep_timeout_retains_actual_checkpoint(tmp_path):
    out = tmp_path / "job"
    out.mkdir()
    result = run_job(command("from pathlib import Path; import time; Path('worker_checkpoint.json').write_text('partial'); time.sleep(20)"),
        cwd=out, output_dir=out, timeout_seconds=.6)
    assert result["status"] == "timed_out" and result["reason"] == "worker_wall_limit"
    assert result["stop_requested"] and result["all_owned_processes_exited"]
    assert result["wall_seconds"] < 4
    assert (out / "worker_checkpoint.json").read_text() == "partial"
    assert "return" not in result and "nav" not in result


def test_deadline_preserves_closing_and_cleanup_window(tmp_path):
    deadline = time.time() + 2.8
    result = run_job(command("import time; time.sleep(20)"), cwd=tmp_path,
        output_dir=tmp_path / "job", timeout_seconds=20, deadline_epoch=deadline,
        closing_seconds=1, termination_grace_seconds=.4)
    assert result["status"] == "timed_out" and result["reason"] == "closing_window_reserved"
    assert result["finished_epoch"] < deadline - 1 + .2
    assert result["all_owned_processes_exited"]


def test_already_in_closing_never_dispatches(tmp_path):
    result = run_job(command("raise Exception('must not dispatch')"), cwd=tmp_path,
        output_dir=tmp_path / "job", timeout_seconds=20, deadline_epoch=time.time() + 10,
        closing_seconds=10)
    assert result["status"] == "not_started" and result["reason"] == "closing_window_reserved"
    assert result["spawned"] is False and result["primary_exit_code"] is None


def test_callback_and_cancel_file(tmp_path):
    cancel = threading.Event()
    timer = threading.Timer(.5, cancel.set)
    timer.start()
    try:
        result = run_job(command("import time; time.sleep(20)"), cwd=tmp_path,
            output_dir=tmp_path / "callback", timeout_seconds=10, cancelled=cancel.is_set)
    finally:
        timer.cancel()
    assert result["status"] == "cancelled" and result["all_owned_processes_exited"]
    out = tmp_path / "file"
    out.mkdir()
    (out / "cancel.request").touch()
    result = run_job(command("raise Exception('must not dispatch')"), cwd=tmp_path,
        output_dir=out, timeout_seconds=10)
    assert result["status"] == "not_started" and result["spawned"] is False


def test_nonzero_exit_remains_failed(tmp_path):
    result = run_job(command("import sys; print('raw failure'); sys.exit(7)"),
        cwd=tmp_path, output_dir=tmp_path / "job", timeout_seconds=5)
    assert result["status"] == "failed" and result["primary_exit_code"] == 7
    assert "raw failure" in (tmp_path / "job/worker.log").read_text()


def test_output_threshold_stops_and_retains_bytes(tmp_path):
    result = run_job(command("import time; print('x'*100000, flush=True); time.sleep(20)"),
        cwd=tmp_path, output_dir=tmp_path / "job", timeout_seconds=5, max_output_bytes=16000)
    assert result["status"] == "output_limit" and result["all_owned_processes_exited"]
    assert result["retained_bytes_before_final_receipt"] > 16000


def test_exit_zero_cannot_hide_output_limit_breach(tmp_path):
    result = run_job(command("print('x'*100000, flush=True)"),
        cwd=tmp_path, output_dir=tmp_path / "job", timeout_seconds=5, max_output_bytes=16000)
    assert result["status"] == "output_limit" and result["all_owned_processes_exited"]


@pytest.mark.skipif(os.name != "nt", reason="Windows Job descendant containment")
def test_child_cannot_escape_when_primary_exits(tmp_path):
    code = "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)']); print('parent done')"
    result = run_job(command(code), cwd=tmp_path, output_dir=tmp_path / "job", timeout_seconds=.8)
    assert result["status"] == "timed_out" and result["primary_exit_code"] == 0
    assert result["metrics"]["total_processes"] >= 2
    assert result["all_owned_processes_exited"]


def test_invalid_budget_rejected_without_artifacts(tmp_path):
    with pytest.raises(ValueError):
        run_job(command("pass"), cwd=tmp_path, output_dir=tmp_path / "job", timeout_seconds=float("inf"))
    assert not (tmp_path / "job").exists()
