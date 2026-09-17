"""Synthetic local-session proof tests; no account access or model invocation."""
from copy import deepcopy
import hashlib
import json

import pytest

from quanta_agents.meta_v6 import gateway


THREAD = "11111111-1111-4111-8111-111111111111"
TURN = "22222222-2222-4222-8222-222222222222"
PROMPT = "合成测试第一行\nDo not invoke a model.\n最后一行"
RESPONSE = {"synthetic_fixture": True, "answer": "retained"}


def receipt():
    return {"response": deepcopy(RESPONSE), "model_verified": False,
            "identity_verification": {"provider_ids": {"thread_id": THREAD, "turn_id": None}}}


def rows(observed=None):
    return [
        {"type": "session_meta", "payload": {"id": THREAD, "model_provider": "openai", "cli_version": "synthetic"}},
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": TURN}},
        {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "<environment_context>synthetic</environment_context>"}]}},
        {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": PROMPT if observed is None else observed}]}},
        {"type": "turn_context", "payload": {"turn_id": TURN, "model": "gpt-6-astra", "effort": "xhigh"}},
        {"type": "response_item", "payload": {"type": "message", "role": "assistant", "phase": "final", "content": [
            {"type": "output_text", "text": json.dumps(RESPONSE)}]}},
        {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": TURN,
                                          "last_agent_message": json.dumps(RESPONSE)}},
    ]


def encoded(records):
    return ("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n").encode("utf-8")


@pytest.mark.parametrize("transported", [False, True])
def test_exact_or_uniform_windows_transport_records_binding_without_edit(transported):
    observed = PROMPT.replace("\n", "\r\n") if transported else PROMPT
    original = encoded(rows(observed))
    saved = receipt()
    before = deepcopy(saved)
    identity = gateway.verify_runtime_session(original, saved, PROMPT)
    assert saved == before
    assert original == encoded(rows(observed))
    assert identity["verified"] is True and identity["provider_request_binding_verified"] is False
    binding = identity["prompt_transport"]
    assert binding["mode"] == ("windows_text_stdin_lf_to_crlf" if transported else "exact")
    assert binding["logical_prompt_utf8_sha256"] == hashlib.sha256(PROMPT.encode()).hexdigest()
    assert binding["observed_prompt_utf8_sha256"] == hashlib.sha256(observed.encode()).hexdigest()
    assert binding["original_session_sha256"] == hashlib.sha256(original).hexdigest()
    assert binding["original_session_bytes_preserved"] is True


@pytest.mark.parametrize("altered", [
    PROMPT.replace("\n", "\r\n", 1),  # Mixed newline styles are not normalized.
    PROMPT.replace("\n", "\r"),
    PROMPT + "\n",
    PROMPT.replace("\n", "\r\n") + " ",
    PROMPT.replace("Do not", "Do"),
    PROMPT.replace("第一", "第ー"),
])
def test_any_other_text_change_is_rejected(altered):
    with pytest.raises(gateway.GatewayError, match="prompt"):
        gateway.verify_runtime_session(encoded(rows(altered)), receipt(), PROMPT)


@pytest.mark.parametrize("mutation", ["wrong_model", "wrong_effort", "wrong_provider", "wrong_thread",
                                     "wrong_turn", "wrong_final", "wrong_completed", "reroute", "extra_user", "duplicate_input"])
def test_newline_rule_does_not_relax_other_original_checks(mutation):
    records = rows(PROMPT.replace("\n", "\r\n"))
    if mutation == "wrong_model":
        records[4]["payload"]["model"] = "other-model"
    elif mutation == "wrong_effort":
        records[4]["payload"]["effort"] = "high"
    elif mutation == "wrong_provider":
        records[0]["payload"]["model_provider"] = "other-provider"
    elif mutation == "wrong_thread":
        records[0]["payload"]["id"] = TURN
    elif mutation == "wrong_turn":
        records[4]["payload"]["turn_id"] = THREAD
    elif mutation == "wrong_final":
        records[5]["payload"]["content"][0]["text"] = '{"changed":true}'
    elif mutation == "wrong_completed":
        records[6]["payload"]["last_agent_message"] = '{"changed":true}'
    elif mutation == "reroute":
        records.insert(-1, {"type": "event_msg", "payload": {"type": "model_rerouted"}})
    elif mutation == "extra_user":
        other = deepcopy(records[3])
        other["payload"]["content"][0]["text"] = "Additional instruction"
        records.insert(4, other)
    else:
        records.insert(4, deepcopy(records[3]))
    with pytest.raises(gateway.GatewayError):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


def test_capture_copies_exact_raw_bytes_without_modifying_prompt_or_source(tmp_path, monkeypatch):
    home = tmp_path / "synthetic_codex_home"
    session_dir = home / "sessions/2000/01/01"
    session_dir.mkdir(parents=True)
    source = session_dir / ("rollout-synthetic-" + THREAD + ".jsonl")
    raw = encoded(rows(PROMPT.replace("\n", "\r\n")))
    source.write_bytes(raw)
    folder = tmp_path / "call"
    folder.mkdir()
    (folder / "prompt.txt").write_bytes(PROMPT.encode())
    monkeypatch.setenv("CODEX_HOME", str(home))
    gateway.capture_saved_session(folder, receipt())
    assert (folder / gateway.SESSION).read_bytes() == raw
    assert source.read_bytes() == raw
    assert (folder / "prompt.txt").read_bytes() == PROMPT.encode()
    gateway.capture_saved_session(folder, receipt())
    assert (folder / gateway.SESSION).read_bytes() == raw


def test_bad_capture_does_not_create_session_file(tmp_path, monkeypatch):
    home = tmp_path / "synthetic_codex_home"
    session_dir = home / "sessions/2000/01/01"
    session_dir.mkdir(parents=True)
    (session_dir / ("rollout-synthetic-" + THREAD + ".jsonl")).write_bytes(encoded(rows(PROMPT + "changed")))
    folder = tmp_path / "call"
    folder.mkdir()
    (folder / "prompt.txt").write_bytes(PROMPT.encode())
    monkeypatch.setenv("CODEX_HOME", str(home))
    with pytest.raises(gateway.GatewayError, match="prompt"):
        gateway.capture_saved_session(folder, receipt())
    assert not (folder / gateway.SESSION).exists()


def test_saved_verification_keeps_hash_binding_and_passes_expected_request(tmp_path, monkeypatch):
    saved = {**receipt(), "artifact_sha256": {}, "verification": "synthetic base verifier"}
    seen = []

    def verify(path, **kwargs):
        seen.append(kwargs)
        return deepcopy(saved)

    monkeypatch.setattr(gateway.base, "verify_saved_completion", verify)
    (tmp_path / "prompt.txt").write_bytes(PROMPT.encode())
    raw = encoded(rows(PROMPT.replace("\n", "\r\n")))
    (tmp_path / gateway.SESSION).write_bytes(raw)
    expected = {gateway.SESSION: hashlib.sha256(raw).hexdigest(), "response.json": "b" * 64}
    result = gateway.verify_saved_completion(tmp_path, expected_artifact_sha256=expected,
                                              expected_prompt_hash="logical-hash", expected_schema={"type": "object"})
    assert result["runtime_identity"]["verified"] is True
    assert result["artifact_sha256"][gateway.SESSION] == expected[gateway.SESSION]
    assert seen[0] == {"expected_artifact_sha256": {"response.json": "b" * 64},
                       "expected_prompt_hash": "logical-hash", "expected_schema": {"type": "object"}}
    with pytest.raises(gateway.GatewayError, match="hash mismatch"):
        gateway.verify_saved_completion(tmp_path, expected_artifact_sha256={gateway.SESSION: "0" * 64})
