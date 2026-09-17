"""Independent harness control tests; fake transport is not research evidence.

No real model, account, factor computation or market-data loader is called.
Generated summaries only test lossless state/context handling.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import time

import pandas as pd
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.research_kernel.controller import ResearchKernel
from quanta_agents.research_kernel.model import model_step, recover_model_call
from quanta_agents.research_kernel.protocol import build_context, validate_action
from quanta_agents.research_kernel.store import serial, write_json


def action(kind="query_assets", payload=None, reason="合成控制流程测试，不代表研究能力"):
    return {"action": kind, "reason": reason,
            "payload_json": json.dumps(payload or {}, ensure_ascii=False)}


def make_kernel(tmp_path, **budget):
    dates = pd.bdate_range("2019-01-01", "2019-12-31")
    opening = pd.DataFrame(10., index=dates, columns=["synthetic_only"])
    panel = MarketPanel({"open": opening, "close": opening.copy()}, opening.notna(),
                        {"fixture_only": True, "market_data": False})
    kernel = ResearchKernel(tmp_path)
    kernel.initialize({"start": "2019-02-01", "end": "2019-12-31", "budget": budget}, panel)
    kernel.assets.register({"id": "weak", "name": "Weak metadata fixture",
        "expression": "close", "roles": ["condition", "interaction"],
        "source": {"fixture_only": True}, "metadata": {"prior_ic": 0., "independent_validation": False}})
    return kernel


def strategy(name="synthetic declaration"):
    return {"version": 1, "name": name, "score": {"op": "factor", "id": "weak"},
            "allocation": {"top_n": 1, "max_stock_weight": 1.}}


def add_run(kernel, identity, status, *, updated, error=None, summary=None):
    eid = None
    if summary is not None:
        eid = kernel.store.put_evidence("synthetic_context_fixture", {
            "summary": summary, "fixture_only": True, "financial_execution": False})
    with kernel.store.transaction() as db:
        db.execute("INSERT INTO runs(id,spec,status,evidence_id,error,updated) VALUES (?,?,?,?,?,?)",
                   (identity, serial({"strategy": {**strategy(identity), "metadata": {}}}),
                    status, eid, error, updated))
        kernel.store.event(db, "fixture_state", {"run_id": identity, "status": status})
    return eid


class FakeGateway:
    """Transport fixture with explicitly fake runtime metadata and saved output.

    The production verifier is replaced only in recovery tests below. This does
    not test provider/runtime authenticity, which remains the gateway's duty.
    """
    def __init__(self, response=None, *, verified=True, error=None, usage=None):
        self.response = action() if response is None else response
        self.verified, self.error = verified, error
        self.usage = {"input_tokens": 111, "output_tokens": 23, "total_tokens": 134,
                      "cached_input_tokens": 7} if usage is None else usage
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        folder = Path(kwargs["workdir"])
        receipt = {"model": "gpt-6-astra", "effort": "xhigh", "response": deepcopy(self.response),
            "usage": deepcopy(self.usage), "runtime_identity": {"verified": self.verified,
                "level": "synthetic_transport_fixture_not_real_identity_verification"},
            "fixture_only": True}
        write_json(folder / "fixture_original_receipt.json", receipt)
        write_json(folder / "fixture_original_response.json", self.response)
        (folder / "fixture_prompt.txt").write_text(kwargs["prompt"], encoding="utf-8")
        if self.error:
            raise self.error
        return receipt


def install_fake_saved_verifier(monkeypatch, *, force_verified=None, fail=None):
    from quanta_agents.meta_v6 import gateway
    checks, captures = [], []
    def verify(folder, **kwargs):
        checks.append(Path(folder))
        if fail:
            raise fail
        receipt = json.loads((Path(folder) / "fixture_original_receipt.json").read_text(encoding="utf-8"))
        if force_verified is not None:
            receipt["runtime_identity"]["verified"] = force_verified
        return receipt
    monkeypatch.setattr(gateway, "verify_saved_completion", verify)
    monkeypatch.setattr(gateway, "capture_saved_session", lambda *args: captures.append(args))
    return checks, captures


@pytest.mark.parametrize("bad", [
    {"action": "query_assets", "reason": "x", "payload_json": "{}", "replacement": "fake"},
    {"action": "invent_result", "reason": "x", "payload_json": "{}"},
    action(payload={"limit": 0}), action(payload={"limit": True}),
    action(payload={"cache_path": "untrusted"}), action("stop", {"success": True}),
    action("request_extension", {"capability": "exit", "reason": "x", "acceptance_tests": []}),
    {"action": "query_assets", "reason": "x", "payload_json": '{"limit":2,"limit":3}'},
    {"action": "query_assets", "reason": "x", "payload_json": '{"limit":NaN}'},
    {"action": "query_assets", "reason": "x", "payload_json": "[]"},
])
def test_short_action_invalid_data_rejected_without_repair(bad):
    original = deepcopy(bad)
    with pytest.raises((ValueError, TypeError)):
        validate_action(bad)
    assert bad == original


def test_response_limit_counts_utf8_bytes_not_characters():
    response = action(reason="汉" * 100)
    encoded = len(serial(response).encode("utf-8"))
    with pytest.raises(ValueError, match="byte budget"):
        validate_action(response, max_bytes=encoded - 1)
    assert validate_action(response, max_bytes=encoded)[0] == "query_assets"


def test_low_ic_does_not_gate_admission_and_unsupported_branch_does_not_stop(tmp_path):
    kernel = make_kernel(tmp_path)
    unsupported = strategy("unsupported operator")
    unsupported["score"] = {"op": "unimplemented_custom_residual", "args": []}
    result = kernel.apply_action(action("propose_batch", {"specs": [unsupported, strategy()], "controls": []}))
    assert [row["status"] for row in result["attempts"]] == ["rejected", "queued"]
    assert kernel.status()["attempts"] == 2 and kernel.status()["executions"] == 0
    assert kernel.status()["stopped"] is False
    request = {"capability": "custom residual operator", "reason": "new primitive required",
               "acceptance_tests": ["known generated matrix coefficients", "future perturbation invariance"]}
    extension = kernel.apply_action(action("request_extension", request))
    assert extension["status"] == "capability_request_recorded" and extension["executable"] is False
    assert kernel.status()["stopped"] is False
    packet = build_context(kernel)["packet"]
    assert packet["recent_rejections"][0]["name"] == "unsupported operator"
    assert "weak" in serial(packet)


def test_context_delta_has_requested_evidence_and_excludes_old_query(tmp_path):
    kernel = make_kernel(tmp_path)
    kernel.apply_action(action("query_assets", {"query": "weak", "limit": 1}), action_id="query_1")
    revision = kernel.status()["revision"]
    eid = kernel.store.put_evidence("synthetic_context", {"items": [{"marker": "new_required_detail"}]})
    kernel.apply_action(action("get_evidence", {"evidence_id": eid, "pointer": "/items", "limit": 1}), action_id="query_2")
    context = build_context(kernel, after_revision=revision)
    delta = context["packet"]["requested_evidence_delta"]
    assert len(delta) == 1 and delta[0]["kind"] == "action_get_evidence"
    assert delta[0]["revision"] > revision
    assert "new_required_detail" in serial(delta)
    assert context["utf8_bytes"] == len(context["prompt"].encode("utf-8"))
    assert context["revision"] == kernel.status()["revision"]


def test_recent_runs_expose_names_roles_and_correct_paired_parent_without_extra_query(tmp_path):
    from quanta_agents.research_kernel.compiler import strategy_id
    kernel = make_kernel(tmp_path)
    first = strategy("First declared mechanism")
    first["gate"] = {"op": "constant", "value": .5}
    second = strategy("Second distinct mechanism")
    second["score"] = {"op": "negate", "args": [{"op": "factor", "id": "weak"}]}
    second["gate"] = {"op": "constant", "value": .25}
    batch = kernel.apply_action(action("propose_batch", {
        "specs": [first, second], "controls": ["without_gate"]}))
    assert len(batch["attempts"]) == 4
    expected = {}
    for parent, members in ((first, batch["attempts"][:2]), (second, batch["attempts"][2:])):
        for attempt in members:
            marker = "synthetic summary for " + attempt["name"]
            eid = kernel.store.put_evidence("synthetic_context_fixture", {
                "summary": {"metric_marker": marker, "fixture_only": True},
                "financial_execution": False})
            with kernel.store.transaction() as db:
                db.execute("UPDATE runs SET status='completed',evidence_id=? WHERE id=?",
                           (eid, attempt["run_id"]))
            expected[attempt["run_id"]] = {"name": attempt["name"], "role": attempt["role"],
                "control_parent": strategy_id(parent), "evidence_id": eid, "marker": marker}
    context = build_context(kernel)
    rows = {row["id"]: row for row in context["packet"]["recent_runs"]}
    assert set(rows) == set(expected)
    for identity, wanted in expected.items():
        row = rows[identity]
        assert {key: row[key] for key in ("name", "role", "control_parent", "evidence_id")} == {
            key: wanted[key] for key in ("name", "role", "control_parent", "evidence_id")}
        assert row["summary"]["metric_marker"] == wanted["marker"]
        assert row["name"] in context["prompt"]
    assert rows[batch["attempts"][0]["run_id"]]["control_parent"] != rows[batch["attempts"][2]["run_id"]]["control_parent"]
    assert kernel.store.rows("SELECT * FROM events WHERE kind='action_get_evidence'") == []
    assert kernel.status()["executions"] == 0 and kernel.status()["model_calls"] == 0


def test_context_shrinks_catalogue_but_keeps_failure_and_scope(tmp_path):
    kernel = make_kernel(tmp_path, max_context_bytes=8000)
    for number in range(24):
        kernel.assets.register({"id": f"long_{number:02d}", "name": "名称" * 100,
            "expression": "close", "roles": ["return"], "metadata": {}, "source": {}})
    add_run(kernel, "failed_run", "failed", updated=1., error="preserve_failure_reason")
    context = build_context(kernel)
    assert context["utf8_bytes"] <= 8000
    assert len(context["packet"]["catalogue_page"]) < 16
    assert context["packet"]["catalogue_more_available"] is True
    assert "preserve_failure_reason" in context["prompt"]
    assert context["packet"]["state"]["scope"]["scope_role"] == "exposed_development"


def test_older_failure_remains_addressable_after_many_new_successes(tmp_path):
    kernel = make_kernel(tmp_path)
    eid = add_run(kernel, "older_failure_must_remain_addressable", "failed", updated=1.,
                  error="missing_open_is_not_zero_return", summary={"status": "failed", "sharpe": None})
    for number in range(12):
        add_run(kernel, f"newer_completed_{number}", "completed", updated=10. + number,
                summary={"fixture_only": True, "sharpe": .01})
    context = build_context(kernel)
    assert context["packet"]["state"]["runs"]["failed"] == 1
    # Old failure detail need not inflate every prompt, but the packet must give
    # a working reference through which the model's existing action can fetch it.
    ledger = context["packet"]["full_ledger_evidence_id"]
    fetched = kernel.apply_action(action("get_evidence", {
        "evidence_id": ledger, "pointer": "/runs", "limit": 20, "offset": 0}))
    failure = next(row for row in fetched["value"] if row["id"] == "older_failure_must_remain_addressable")
    assert failure["evidence_id"] == eid and failure["error"] == "missing_open_is_not_zero_return"
    assert failure["status"] == "failed"
    assert kernel.store.evidence(eid, pointer="/summary")["value"]["sharpe"] is None


def test_oversized_query_delta_returns_working_narrow_evidence_reference(tmp_path):
    kernel = make_kernel(tmp_path, max_context_bytes=10000)
    eid = kernel.store.put_evidence("large_query_fixture", {"items": [
        {"mechanism": "retained detail " * 200, "fixture_only": True, "number": number}
        for number in range(3)]})
    revision = kernel.status()["revision"]
    original = kernel.apply_action(action("get_evidence", {"evidence_id": eid, "pointer": "/items", "limit": 3}))
    context = build_context(kernel, after_revision=revision)
    delta = context["packet"]["requested_evidence_delta"][0]["data"]
    assert delta["status"] == "narrow_query_required"
    assert context["utf8_bytes"] <= 10000
    restored = kernel.apply_action(action("get_evidence", {"evidence_id": delta["full_evidence_id"],
        "pointer": "/result/value", "limit": 1, "offset": 0}))
    assert restored["value"] == original["value"][:1]
    assert restored["total"] == 3


def test_mandatory_context_over_budget_refuses_instead_of_erasing_failures(tmp_path):
    kernel = make_kernel(tmp_path, max_context_bytes=6000)
    for number in range(10):
        add_run(kernel, f"failure_{number}", "failed", updated=number,
                error="失败证据不可删除" * 70)
    with pytest.raises(ValueError, match="Mandatory evidence"):
        build_context(kernel)
    assert kernel.status()["runs"]["failed"] == 10


def test_verified_transport_action_usage_and_real_context_statistics(tmp_path):
    kernel = make_kernel(tmp_path)
    fake = FakeGateway()
    result = model_step(kernel, gateway=fake)
    assert result["status"] == "applied" and result["usage"] == fake.usage
    assert len(fake.calls) == 1
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    assert row["status"] == "applied"
    assert json.loads(row["response"]) == fake.response
    assert json.loads(row["usage"]) == fake.usage
    manifest = json.loads((Path(row["directory"]) / "context_manifest.json").read_text())
    assert manifest["utf8_bytes"] == len(fake.calls[0]["prompt"].encode("utf-8"))
    assert manifest["model"] == "gpt-6-astra" and manifest["effort"] == "xhigh"
    assert "not a provider token cap" in manifest["output_limit_enforcement"]
    assert kernel.status()["model_calls"] == 1 and kernel.status()["executions"] == 0


@pytest.mark.parametrize("verified", [False, None, 1, "true"])
def test_unverified_runtime_cannot_admit_or_dispatch_action(tmp_path, verified):
    kernel = make_kernel(tmp_path)
    fake = FakeGateway(action("propose_batch", {"specs": [strategy()]}), verified=verified)
    with pytest.raises(ValueError, match="identity"):
        model_step(kernel, gateway=fake)
    assert kernel.status()["attempts"] == 0
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    assert row["status"] == "needs_recovery" and kernel.status()["model_calls"] == 1
    assert json.loads((Path(row["directory"]) / "fixture_original_response.json").read_text(encoding="utf-8")) == fake.response


def test_illegal_model_action_is_retained_and_feedback_does_not_forge_correction(tmp_path):
    kernel = make_kernel(tmp_path)
    invalid = {"action": "fake_complete_account", "reason": "invalid fixture", "payload_json": "{}"}
    fake = FakeGateway(invalid)
    result = model_step(kernel, gateway=fake)
    assert result["status"] == "action_rejected"
    assert result["result"]["status"] == "action_rejected"
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    assert json.loads(row["response"]) == invalid
    assert kernel.store.rows("SELECT * FROM actions") == []
    assert kernel.status()["attempts"] == 0 and kernel.status()["executions"] == 0
    assert kernel.status()["stopped"] is False
    assert kernel.store.rows("SELECT * FROM events WHERE kind='action_rejected'")


def test_model_call_budget_counts_rejected_calls_and_blocks_new_transport(tmp_path):
    kernel = make_kernel(tmp_path, max_model_calls=1)
    fake = FakeGateway({"action": "invalid", "reason": "x", "payload_json": "{}"})
    assert model_step(kernel, gateway=fake)["status"] == "action_rejected"
    assert model_step(kernel, gateway=fake)["status"] == "model_budget_exhausted"
    assert len(fake.calls) == 1 and kernel.status()["model_calls"] == 1
    assert kernel.status()["stopped"] is True
    assert len(kernel.store.rows("SELECT * FROM events WHERE kind='model_budget_exhausted'")) == 1


def test_four_call_limit_persists_stop_before_context_or_gateway_and_only_once(tmp_path, monkeypatch):
    from quanta_agents.research_kernel import model
    kernel = make_kernel(tmp_path, max_model_calls=4)
    with kernel.store.transaction() as db:
        for number in range(4):
            db.execute("INSERT INTO model_calls VALUES (?,?,?,?,?,?,?)", (
                f"fixture_call_{number}", "applied", str(tmp_path / f"fixture_only_{number}"),
                serial(action()), serial({"fixture_only": True}), None, time.time()))
    # These are terminal ledger fixtures, not four paid calls. The next transport
    # must never be reached, even if building context itself would fail.
    monkeypatch.setattr(model, "build_context", lambda *a, **kw: pytest.fail("budget check must precede context"))
    fake = FakeGateway()
    result = model_step(kernel, gateway=fake)
    assert result == {"status": "model_budget_exhausted"}
    assert not fake.calls
    assert kernel.status()["model_calls"] == 4 and kernel.status()["stopped"] is True
    events = kernel.store.rows("SELECT * FROM events WHERE kind='model_budget_exhausted'")
    assert len(events) == 1 and json.loads(events[0]["payload"])["reason"]
    fresh = ResearchKernel(tmp_path)
    assert fresh.store.meta("stopped") is True
    assert model_step(fresh, gateway=fake) == {"status": "stopped"}
    assert not fake.calls and fresh.status()["model_calls"] == 4
    assert len(fresh.store.rows("SELECT * FROM events WHERE kind='model_budget_exhausted'")) == 1


def test_saved_completion_recovers_without_second_paid_dispatch(tmp_path, monkeypatch):
    kernel = make_kernel(tmp_path, max_model_calls=1)
    response = action("propose_batch", {"specs": [strategy()], "controls": []})
    fake = FakeGateway(response, error=TimeoutError("saved output, transport interrupted"))
    with pytest.raises(TimeoutError):
        model_step(kernel, gateway=fake)
    original = kernel.store.rows("SELECT * FROM model_calls")[0]
    original_response = (Path(original["directory"]) / "fixture_original_response.json").read_bytes()
    checks, captures = install_fake_saved_verifier(monkeypatch)
    result = model_step(kernel, gateway=fake)
    assert result["call_id"] == original["id"] and result["status"] == "applied"
    assert len(fake.calls) == 1 and len(checks) == 1 and not captures
    assert kernel.status()["model_calls"] == 1 and kernel.status()["attempts"] == 1
    assert kernel.status()["executions"] == 0
    # Re-admission is action-idempotent even after a parent lost the return value.
    repeated = recover_model_call(kernel, original["id"])
    assert repeated["result"] == result["result"] and kernel.status()["attempts"] == 1
    assert (Path(original["directory"]) / "fixture_original_response.json").read_bytes() == original_response


def test_unrecoverable_call_never_silently_pays_again(tmp_path, monkeypatch):
    kernel = make_kernel(tmp_path, max_model_calls=3)
    fake = FakeGateway(error=TimeoutError("no complete transport receipt"))
    with pytest.raises(TimeoutError):
        model_step(kernel, gateway=fake)
    checks, _ = install_fake_saved_verifier(monkeypatch, fail=ValueError("saved identity unavailable"))
    for _ in range(2):
        with pytest.raises(ValueError, match="saved identity"):
            model_step(kernel, gateway=fake)
    assert len(fake.calls) == 1 and len(checks) == 2
    assert kernel.status()["model_calls"] == 1


def test_offline_runtime_capture_must_be_verified_before_recovery_admission(tmp_path, monkeypatch):
    kernel = make_kernel(tmp_path)
    fake = FakeGateway(verified=False)
    with pytest.raises(ValueError):
        model_step(kernel, gateway=fake)
    checks, captures = install_fake_saved_verifier(monkeypatch, force_verified=False)
    with pytest.raises(ValueError, match="identity"):
        model_step(kernel, gateway=fake)
    assert len(checks) == 2 and len(captures) == 1 and len(fake.calls) == 1
    assert kernel.store.rows("SELECT * FROM actions") == []


def test_missing_usage_stays_unknown_not_synthesized_zero(tmp_path):
    kernel = make_kernel(tmp_path)
    fake = FakeGateway(usage={})
    result = model_step(kernel, gateway=fake)
    assert result["usage"] == {}
    assert json.loads(kernel.store.rows("SELECT usage FROM model_calls")[0]["usage"]) == {}


def test_stop_prevents_transport_and_retains_scope_and_history(tmp_path):
    kernel = make_kernel(tmp_path)
    kernel.apply_action(action("stop", reason="explicit stop fixture"), action_id="stop_once")
    fake = FakeGateway()
    assert model_step(kernel, gateway=fake) == {"status": "stopped"}
    assert not fake.calls and kernel.status()["model_calls"] == 0
    assert kernel.store.rows("SELECT * FROM events WHERE kind='action_stop'")
