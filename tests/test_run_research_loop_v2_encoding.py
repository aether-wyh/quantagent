from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_research_loop_v2.py"


def _load_runner_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_research_loop_v2", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_help_is_written_as_utf8() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0
    output = completed.stdout.decode("utf-8", errors="strict")
    assert "从一句话或一份研报运行研究循环V2" in output
    assert "正式候选上限" in output
    assert "--allow-stopped-selected-resume" in output
    assert "--recheck-after-rule-fix-from-result" in output
    assert "0 表示不新增候选，直接检查确认期" in output


def test_runner_traceback_is_written_as_utf8(tmp_path: Path) -> None:
    request_path = tmp_path / "idea.yaml"
    request_path.write_text("user_idea: 测试想法\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(request_path),
            "--max-candidates",
            "0",
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    error_text = completed.stderr.decode("utf-8", errors="strict")
    assert "--max-candidates 必须大于0" in error_text


def test_rule_fix_recheck_cli_is_separate_from_normal_resume(tmp_path: Path) -> None:
    request_path = tmp_path / "idea.yaml"
    request_path.write_text("user_idea: 测试想法\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(request_path),
            "--resume-selected-from-result",
            str(tmp_path / "normal.json"),
            "--recheck-after-rule-fix-from-result",
            str(tmp_path / "rule_fix.json"),
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    error_text = completed.stderr.decode("utf-8", errors="strict")
    assert "只能选择一种" in error_text


def test_data_manifest_replaces_claimed_available_fields(tmp_path: Path) -> None:
    module = _load_runner_module()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "available_fields": [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                    "prev_close",
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    profile = module.default_cn_daily_v2_profile()

    resolved = module._apply_data_manifest(
        profile,
        str(tmp_path / "*.parquet"),
    )

    assert resolved == str(manifest_path.resolve())
    assert profile["data"]["available_fields"] == [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "prev_close",
    ]
    assert len(profile["data"]["manifest_sha256"]) == 64
    assert profile["data"]["manifest_summary"] == {}


def test_data_manifest_rejects_missing_required_price_field(tmp_path: Path) -> None:
    module = _load_runner_module()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"available_fields": ["open", "high", "low", "close"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="volume"):
        module._apply_data_manifest(
            module.default_cn_daily_v2_profile(),
            str(tmp_path / "*.parquet"),
        )


def test_initial_named_universe_is_recorded_as_runtime_choice() -> None:
    module = _load_runner_module()
    profile = module.default_cn_daily_v2_profile()

    module._apply_initial_universe(profile, "csiall")

    assert profile["universe"]["required_data"] == {
        "type": "named_pool",
        "value": "csiall",
    }
    assert profile["universe"]["experiment_entry"]["type"] == "named_pool"
    assert profile["universe"]["experiment_entry"]["value"] == "csiall"
    assert "不是用户条件" in profile["universe"]["description"]


def test_dataset_defined_initial_universe_keeps_default_profile() -> None:
    module = _load_runner_module()
    profile = module.default_cn_daily_v2_profile()
    original = json.loads(json.dumps(profile["universe"], ensure_ascii=False))

    module._apply_initial_universe(profile, "dataset_defined")

    assert profile["universe"] == original
