"""Offline recovery tests. Every model gateway and session capture is mocked."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from quanta_agents.meta_v6 import gateway, research


PROMPT = "合成恢复测试，不调用模型。"
SCHEMA = research.object_schema({"answer": research.TEXT})
USAGE = {"input_tokens": 101, "output_tokens": 23, "cached_input_tokens": 17}


def prompt_hash(prompt=PROMPT):
    return hashlib.sha256(json.dumps(prompt, ensure_ascii=False, allow_nan=False,
                                    default=str).encode()).hexdigest()


def receipt(*, verified=True):
    return {"response": {"answer": "synthetic mock output"}, "usage": deepcopy(USAGE),
            "model": "gpt-6-astra", "effort": "xhigh",
            "runtime_identity": {"verified": verified}, "artifact_sha256": {"response.json": "a" * 64}}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def forbid_unmocked_live_or_capture(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("test attempted an unmocked model gateway or session capture")
    monkeypatch.setattr(gateway, "CodexGateway", forbidden)
    monkeypatch.setattr(gateway, "verify_saved_completion", forbidden)
    monkeypatch.setattr(gateway, "capture_saved_session", forbidden)


def saved_stage(tmp_path):
    root = tmp_path / "research"
    folder = root / "model_calls" / "stage"
    folder.mkdir(parents=True)
    # Deliberately synthetic files; the real verifier is never invoked on them.
    (folder / "codex_request.json").write_text('{"test_fixture":true}', encoding="utf-8")
    (folder / "response.json").write_text('{"answer":"synthetic mock output"}', encoding="utf-8")
    return root, folder


def test_existing_completion_binds_current_prompt_and_schema_without_dispatch(tmp_path, monkeypatch):
    root, folder = saved_stage(tmp_path)
    seen = []
    expected = receipt()

    def verify(path, **kwargs):
        seen.append((path, kwargs))
        assert kwargs == {"expected_prompt_hash": prompt_hash(), "expected_schema": SCHEMA}
        return deepcopy(expected)

    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    assert research.call_researcher(root, "stage", PROMPT, SCHEMA) == expected
    assert seen == [(folder, {"expected_prompt_hash": prompt_hash(), "expected_schema": SCHEMA})]
    assert read(folder / "admitted_receipt.json") == expected


@pytest.mark.parametrize("changed", ["prompt", "schema"])
def test_changed_request_rejects_old_response_instead_of_reusing_it(tmp_path, monkeypatch, changed):
    root, folder = saved_stage(tmp_path)
    original_response = (folder / "response.json").read_bytes()

    def verify(path, *, expected_prompt_hash, expected_schema):
        if expected_prompt_hash != prompt_hash() or expected_schema != SCHEMA:
            raise ValueError("Saved prompt or schema does not match expected request")
        return receipt()

    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    prompt = PROMPT + " changed" if changed == "prompt" else PROMPT
    schema = research.object_schema({"different": research.TEXT}) if changed == "schema" else SCHEMA
    with pytest.raises(ValueError, match="does not match"):
        research.call_researcher(root, "stage", prompt, schema)
    assert not (folder / "admitted_receipt.json").exists()
    assert (folder / "response.json").read_bytes() == original_response


def test_missing_identity_recovers_exact_saved_session_offline(tmp_path, monkeypatch):
    root, folder = saved_stage(tmp_path)
    captures, verifies = [], []

    def verify(path, **kwargs):
        verifies.append(kwargs)
        return receipt(verified=(folder / "mock_session_captured").exists())

    def capture(path, saved):
        captures.append((path, deepcopy(saved)))
        assert read(folder / "completion_before_identity_recovery.json")["usage"] == USAGE
        (folder / "mock_session_captured").touch()

    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    monkeypatch.setattr(gateway, "capture_saved_session", capture)
    result = research.call_researcher(root, "stage", PROMPT, SCHEMA)
    assert result["runtime_identity"]["verified"] is True
    assert len(captures) == 1 and len(verifies) == 2
    assert all(value == {"expected_prompt_hash": prompt_hash(), "expected_schema": SCHEMA} for value in verifies)
    assert captures[0] == (folder, receipt(verified=False))
    assert read(folder / "completion_before_identity_recovery.json") == receipt(verified=False)


@pytest.mark.parametrize("identity_value", [False, None, "true", 1])
def test_unverified_or_nonboolean_identity_never_admitted(tmp_path, monkeypatch, identity_value):
    root, folder = saved_stage(tmp_path)
    expected = receipt(verified=identity_value)
    captures = []
    monkeypatch.setattr(gateway, "verify_saved_completion", lambda *args, **kwargs: deepcopy(expected))
    monkeypatch.setattr(gateway, "capture_saved_session", lambda *args: captures.append(args))
    with pytest.raises(ValueError, match="identity is not verified"):
        research.call_researcher(root, "stage", PROMPT, SCHEMA)
    assert len(captures) == 1
    assert not (folder / "admitted_receipt.json").exists()
    assert read(folder / "completion_before_identity_recovery.json") == expected


def test_capture_failure_retains_billable_completion_and_next_attempt_is_offline(tmp_path, monkeypatch):
    root = tmp_path / "research"
    folder = root / "model_calls" / "stage"
    calls, captures = [], []
    recovered = False

    class MockGateway:
        def __init__(self, *, timeout_seconds):
            assert timeout_seconds == 42

        def run(self, **kwargs):
            calls.append(kwargs)
            assert kwargs["prompt"] == PROMPT and kwargs["schema"] == SCHEMA
            assert kwargs["cancelled"]() is False
            (folder / "codex_request.json").write_text('{"test_fixture":true}', encoding="utf-8")
            (folder / "response.json").write_text('{"answer":"synthetic mock output"}', encoding="utf-8")
            kwargs["on_event"]({"kind": "usage", "data": USAGE})
            return receipt(verified=False)

    def capture(path, saved):
        nonlocal recovered
        captures.append(path)
        if len(captures) == 1:
            raise ValueError("original runtime session capture temporarily unavailable")
        recovered = True

    def verify(path, **kwargs):
        assert kwargs == {"expected_prompt_hash": prompt_hash(), "expected_schema": SCHEMA}
        return receipt(verified=recovered)

    monkeypatch.setattr(gateway, "CodexGateway", MockGateway)
    monkeypatch.setattr(gateway, "capture_saved_session", capture)
    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    with pytest.raises(ValueError, match="temporarily unavailable"):
        research.call_researcher(root, "stage", PROMPT, SCHEMA, timeout_seconds=42)
    assert read(folder / "completion_before_identity_recovery.json")["usage"] == USAGE
    assert not (folder / "admitted_receipt.json").exists()
    original = {name: (folder / name).read_bytes() for name in (
        "codex_request.json", "response.json", "intent.json", "stage_failure.json",
        "completion_before_identity_recovery.json", "gateway_events.jsonl")}
    result = research.call_researcher(root, "stage", PROMPT, SCHEMA, timeout_seconds=42)
    assert result == receipt(verified=True)
    assert len(calls) == 1 and len(captures) == 2
    assert all((folder / name).read_bytes() == raw for name, raw in original.items())
    assert read(folder / "stage_failure.json")["saved_response_must_be_recovered_before_new_paid_call"] is True


def test_partial_invocation_retains_observed_usage_and_cannot_be_paid_retried(tmp_path, monkeypatch):
    root = tmp_path / "research"
    folder = root / "model_calls" / "stage"
    calls = []

    class MockGateway:
        def __init__(self, **kwargs):
            pass

        def run(self, **kwargs):
            calls.append(kwargs)
            (folder / "codex_request.json").write_text('{"test_fixture":true}', encoding="utf-8")
            error = RuntimeError("simulated unknown response, original invocation retained")
            error.usage = {"input_tokens": 101, "output_tokens": None}
            raise error

    def verify(*args, **kwargs):
        raise ValueError("original completion not yet available")

    monkeypatch.setattr(gateway, "CodexGateway", MockGateway)
    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    with pytest.raises(RuntimeError, match="unknown response"):
        research.call_researcher(root, "stage", PROMPT, SCHEMA)
    failure_before = (folder / "stage_failure.json").read_bytes()
    assert read(folder / "stage_failure.json")["usage"] == {"input_tokens": 101, "output_tokens": None}
    with pytest.raises(ValueError, match="not yet available"):
        research.call_researcher(root, "stage", PROMPT, SCHEMA)
    assert len(calls) == 1
    assert not (folder / "admitted_receipt.json").exists()
    assert (folder / "stage_failure.json").read_bytes() == failure_before


def test_intent_without_request_refuses_automatic_retry(tmp_path):
    root = tmp_path / "research"
    folder = root / "model_calls" / "stage"
    folder.mkdir(parents=True)
    (folder / "intent.json").write_text('{"test_fixture":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="intent already exists"):
        research.call_researcher(root, "stage", PROMPT, SCHEMA)
    assert not (folder / "codex_request.json").exists()
