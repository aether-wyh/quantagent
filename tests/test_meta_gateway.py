from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from quanta_agents.meta import codex_gateway as gateway_module
from quanta_agents.meta.codex_gateway import (
    CodexGateway, GatewayCancelled, GatewayError, GatewayTimeout,
    ModelPolicyViolation, ToolPolicyViolation, _EventParser,
)


class _Input(io.StringIO):
    def close(self):
        self.saved = self.getvalue()
        super().close()


class _Process:
    def __init__(self, command, events, response, *, returncode=0, hanging=False):
        self.command = command
        self.stdout = io.StringIO("".join(json.dumps(item) + "\n" for item in events))
        self.stderr = io.StringIO("provider diagnostic\n")
        self.stdin = _Input()
        self.returncode = None if hanging else returncode
        self.pid = 543210
        self.killed = False
        if response is not None:
            Path(command[command.index("-o") + 1]).write_text(json.dumps(response), encoding="utf-8")

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


def _install_process(monkeypatch, events, response=None, **process_options):
    captured = {}
    monkeypatch.setattr(CodexGateway, "_preflight", lambda self: gateway_module._DISABLED_FEATURES)

    def popen(command, **kwargs):
        process = _Process(command, events, response, **process_options)
        captured.update(process=process, command=command, kwargs=kwargs)
        return process

    monkeypatch.setattr(gateway_module.subprocess, "Popen", popen)
    monkeypatch.setattr(gateway_module, "_create_process_job", lambda process: None)
    monkeypatch.setattr(gateway_module, "_kill_process_tree", lambda process: process.kill())
    return captured


def _run(tmp_path, **kwargs):
    return CodexGateway(executable="codex-native", **kwargs).run(
        prompt="Research only this synthetic input", schema={"type": "object"},
        workdir=tmp_path, on_event=lambda event: None, cancelled=lambda: False,
    )


def test_startup_diagnostic_is_not_a_tool_execution():
    emitted = []
    parser = _EventParser(emitted.append)
    parser.feed({'type': 'item.completed', 'item': {'type': 'error', 'message': 'Tool host disabled; failing closed.'}})
    parser.feed({'type': 'turn.completed', 'usage': {'input_tokens': 10, 'output_tokens': 2}})
    assert parser.turn_completed
    assert parser.failed is None
    assert emitted[0]['kind'] == 'error'
    assert not any(event['kind'] == 'tool' for event in emitted)


def test_streams_only_reported_reasoning_and_locks_configuration(tmp_path, monkeypatch):
    events = [
        {"type": "thread.started", "thread_id": "synthetic"},
        {"type": "session.started", "session": {"model": "gpt-6-astra", "reasoning_effort": "xhigh"}},
        {"type": "item.completed", "item": {"type": "reasoning", "text": "Compare conditional samples."}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "{\"ok\":true}"}},
        {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 30, "output_tokens": 50}},
    ]
    captured = _install_process(monkeypatch, events, {"ok": True})
    monkeypatch.setenv("CODEX_EXEC_MODEL", "wrong-model")
    monkeypatch.setenv("OPENAI_MODEL", "wrong-model")
    emitted = []
    result = CodexGateway(executable="codex-native").run(
        prompt="a $prompt with `literal` syntax", schema={"type": "object"},
        workdir=tmp_path, on_event=emitted.append, cancelled=lambda: False,
    )
    assert result["response"] == {"ok": True}
    assert result["model"] == "gpt-6-astra"
    assert result["effort"] == "xhigh"
    assert result["model_verified"] is True
    assert result["usage"] == {"input_tokens": 100, "cached_input_tokens": 30,
                               "output_tokens": 50, "reasoning_output_tokens": None}
    command = captured["command"]
    assert command[command.index("-m") + 1] == "gpt-6-astra"
    assert 'model_reasoning_effort="xhigh"' in command
    for option in ("--json", "--ignore-user-config", "--ignore-rules", "--strict-config", "--ephemeral", "--skip-git-repo-check"):
        assert option in command
    assert command[command.index("--sandbox") + 1] == "read-only"
    for feature in ("multi_agent", "shell_tool", "apps", "plugins", "browser_use", "computer_use", "code_mode_host"):
        assert any(command[i:i + 2] == ["--disable", feature] for i in range(len(command)))
    assert 'web_search="disabled"' in command
    # Recent Codex rejects overrides of reserved built-in providers.
    assert not any('model_providers.openai.' in argument for argument in command)
    assert captured["process"].stdin.saved == "a $prompt with `literal` syntax"
    assert "OPENAI_MODEL" not in captured["kwargs"]["env"]
    assert "CODEX_EXEC_MODEL" not in captured["kwargs"]["env"]
    assert Path(captured["kwargs"]["cwd"]) != tmp_path
    assert not captured["kwargs"].get("shell", False)
    assert [e["text"] for e in emitted if e["kind"] == "reasoning"] == ["Compare conditional samples."]
    assert all(set(e) == {"kind", "text", "data"} for e in emitted)
    assert len((tmp_path / "codex_events.jsonl").read_text(encoding="utf-8").splitlines()) == len(events)
    assert "provider diagnostic" in (tmp_path / "codex_stderr.log").read_text(encoding="utf-8")


def test_unknown_usage_and_unconfirmed_identity_are_not_fabricated(tmp_path, monkeypatch):
    _install_process(monkeypatch, [{"type": "turn.completed"}], {"model": "gpt-6-astra", "effort": "xhigh"})
    result = _run(tmp_path)
    assert result["model_verified"] is False
    assert all(value is None for value in result["usage"].values())
    assert "did not confirm" in result["verification"]


def test_cumulative_usage_keeps_reasoning_separate_without_double_counting():
    parser = _EventParser(lambda event: None)
    raw = {"type": "turn.completed", "usage": {"input_tokens": 120,
        "input_tokens_details": {"cached_tokens": 80}, "output_tokens": 60,
        "output_tokens_details": {"reasoning_tokens": 45}}}
    parser.feed(raw)
    parser.feed(raw)
    assert parser.usage == {"input_tokens": 120, "cached_input_tokens": 80,
                            "output_tokens": 60, "reasoning_output_tokens": 45}
    parser.feed({"type": "token_count", "info": {"total_token_usage": {"output_tokens": 65}}})
    assert parser.usage["output_tokens"] == 65
    assert parser.usage["input_tokens"] == 120


@pytest.mark.parametrize("item_kind", ["command_execution", "mcp_tool_call", "file_change", "collab_tool_call", "unknown_new_tool"])
def test_any_tool_item_aborts_and_cleans_up(tmp_path, monkeypatch, item_kind):
    captured = _install_process(monkeypatch, [{"type": "item.started", "item": {"type": item_kind}}], hanging=True)
    with pytest.raises(ToolPolicyViolation, match="tool_policy_violation"):
        _run(tmp_path)
    assert captured["process"].killed


@pytest.mark.parametrize("identity", [
    {"model": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
    {"model": "gpt-6-astra", "reasoning_effort": "ultra"},
])
def test_runtime_model_mismatch_aborts(tmp_path, monkeypatch, identity):
    captured = _install_process(monkeypatch, [{"type": "session.started", "session": identity}], hanging=True)
    with pytest.raises(ModelPolicyViolation):
        _run(tmp_path)
    assert captured["process"].killed


def test_cancellation_terminates_owned_process(tmp_path, monkeypatch):
    captured = _install_process(monkeypatch, [], hanging=True)
    checks = iter([False, False, False, True])
    with pytest.raises(GatewayCancelled):
        CodexGateway(executable="codex-native").run(prompt="test", schema={}, workdir=tmp_path,
            on_event=lambda event: None, cancelled=lambda: next(checks, True))
    assert captured["process"].killed


def test_timeout_terminates_owned_process_without_retry(tmp_path, monkeypatch):
    captured = _install_process(monkeypatch, [], hanging=True)
    with pytest.raises(GatewayTimeout):
        _run(tmp_path, timeout_seconds=0.01)
    assert captured["process"].killed


def test_failed_turn_cannot_be_accepted_even_with_response_file(tmp_path, monkeypatch):
    _install_process(monkeypatch, [{"type": "turn.failed", "error": {"message": "provider failure"}}], {"ok": True})
    with pytest.raises(GatewayError, match="provider failure"):
        _run(tmp_path)


def test_nonzero_exit_is_failure(tmp_path, monkeypatch):
    _install_process(monkeypatch, [{"type": "turn.completed"}], {"ok": True}, returncode=7)
    with pytest.raises(GatewayError, match="status 7"):
        _run(tmp_path)


def test_preflight_fails_closed_when_required_features_missing(monkeypatch):
    help_text = "--json --output-schema --output-last-message --strict-config --ignore-user-config --ignore-rules --ephemeral --sandbox"
    results = iter([SimpleNamespace(returncode=0, stdout=help_text), SimpleNamespace(returncode=0, stdout="shell_tool stable true")])
    monkeypatch.setattr(gateway_module.subprocess, "run", lambda *a, **kw: next(results))
    with pytest.raises(GatewayError, match="cannot disable"):
        CodexGateway(executable="codex-native")._preflight()


def test_preflight_selects_only_features_supported_by_installed_cli(monkeypatch):
    help_text = "--json --output-schema --output-last-message --strict-config --ignore-user-config --ignore-rules --ephemeral --sandbox"
    available = "\n".join(f"{name} stable true" for name in gateway_module._REQUIRED_FEATURES)
    results = iter([SimpleNamespace(returncode=0, stdout=help_text), SimpleNamespace(returncode=0, stdout=available)])
    monkeypatch.setattr(gateway_module.subprocess, "run", lambda *a, **kw: next(results))
    assert set(CodexGateway(executable="codex-native")._preflight()) == gateway_module._REQUIRED_FEATURES


def test_existing_attempt_directory_cannot_overwrite_prior_response(tmp_path, monkeypatch):
    _install_process(monkeypatch, [{"type": "turn.completed"}], {"ok": True})
    _run(tmp_path)
    with pytest.raises(GatewayError, match="already exist"):
        _run(tmp_path)
