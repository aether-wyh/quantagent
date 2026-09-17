"""End-to-end acceptance using generated prices and the actual numerical engines."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.research_kernel.controller import ResearchKernel
from quanta_agents.research_kernel.evidence import factor_report
from quanta_agents.research_kernel.store import Store, exclusive_lock, serial


def synthetic_panel():
    dates = pd.bdate_range("2019-01-02", periods=190, name="date")
    codes = pd.Index([f"sh{600000 + i}" for i in range(8)], name="stock")
    t, j = np.arange(len(dates))[:, None], np.arange(len(codes))[None, :]
    daily = .0002 + .003 * np.sin(t / 9 + j / 2) + .0002 * j
    close = pd.DataFrame((10 + j) * np.exp(np.cumsum(daily, axis=0)), index=dates, columns=codes)
    previous = close.shift(1).fillna(close.iloc[0])
    opening = previous * (1 + .0005 * np.cos(t / 7 + j))
    fields = {"open": opening, "close": close, "high": np.maximum(close, opening) * 1.005,
              "low": np.minimum(close, opening) * .995, "raw_open": opening.copy(),
              "raw_close": close.copy(), "raw_prev_close": previous, "volume": close * 0 + 1e6,
              "amount": close * 0 + 1e8, "adjustment_factor": close * 0 + 1,
              "is_st": close * 0, "is_delisting": close * 0, "open_observed": close * 0 + 1}
    return MarketPanel(fields, close.notna(), {"source": "synthetic_acceptance_only"})


def factor(key):
    return {"op": "factor", "id": key}


def op(name, *args, **params):
    return {"op": name, "args": list(args), **params}


def constant(value):
    return {"op": "constant", "value": value}


def strategy(name="baseline", score=None, **changes):
    return {"name": name, "score": score or factor("F1"),
            "allocation": {"top_n": 3, "max_stock_weight": .3, "rebalance_sessions": 5}, **changes}


def initialize(tmp_path, *, budget=None):
    panel = synthetic_panel()
    kernel = ResearchKernel(tmp_path / "study")
    config = {"start": str(panel.dates[125].date()), "end": str(panel.dates[164].date()),
              "budget": {"max_context_bytes": 6000, **(budget or {})},
              "account_policy": {"capital": 100_000., "lot_size": 1}}
    kernel.initialize(config, panel)
    expressions = {"F1": "close", "F2": "pct_change(close,3)",
                   "F3": "rolling_std(pct_change(close,1),10)", "alias": "((close))",
                   "unavailable": "unknown_signal_input"}
    for key, expression in expressions.items():
        kernel.assets.register({"id": key, "name": key, "expression": expression,
                                "roles": ["return"], "source": {"kind": "generated_test"}})
    return kernel, panel, config


def run_rows(kernel):
    return kernel.store.rows("SELECT * FROM runs ORDER BY updated,id")


def event_rows(kernel, kind):
    return kernel.store.rows("SELECT * FROM events WHERE kind=? ORDER BY seq", (kind,))


def test_initialize_freezes_scope_policy_budget_and_actual_panel(tmp_path):
    kernel, panel, config = initialize(tmp_path)
    original = (kernel.root / "config.json").read_bytes()
    reopened = ResearchKernel(kernel.root)
    reopened.initialize(config, panel)
    assert (kernel.root / "config.json").read_bytes() == original
    assert len(event_rows(kernel, "initialized")) == 1
    for changed in ({**config, "end": str(panel.dates[165].date())},
                    {**config, "budget": {"max_executions": 99}},
                    {**config, "account_policy": {"capital": 1_000_000.}}):
        with pytest.raises(ValueError, match="frozen"):
            reopened.initialize(changed, panel)
    altered = deepcopy(panel)
    altered.fields["close"].iloc[130, 0] *= 1.01
    with pytest.raises(ValueError, match="snapshot"):
        reopened.execute_pending(altered)
    assert kernel.status()["executions"] == 0
    assert (kernel.root / "config.json").read_bytes() == original


def test_batch_keeps_original_three_ablation_arms_and_generic_gate_control(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    score = op("weighted_sum", *[op("rank", factor(f"F{i}")) for i in range(1, 4)], weights=[.2, .3, .5])
    gate = op("where", op("gt", op("rank", factor("F2")), constant(.5)), constant(.4), constant(.8))
    result = kernel.submit_batch([strategy(score=score, gate=gate)], controls=["leave_one_out", "without_gate"])
    attempts = result["attempts"]
    assert {row["role"] for row in attempts} == {"proposal", "without_gate", "omit_1", "omit_2", "omit_3"}
    assert len({row["run_id"] for row in attempts}) == 5
    executed = kernel.execute_pending(panel)
    assert len(executed["runs"]) == 5
    assert {row["status"] for row in executed["runs"]} == {"completed"}, executed["runs"]
    specs = {row["id"]: json.loads(row["spec"])["strategy"] for row in run_rows(kernel)}
    for attempt in attempts:
        spec = specs[attempt["run_id"]]
        if attempt["role"] == "proposal":
            assert spec["score"] == score and spec["gate"] == gate
        elif attempt["role"] == "without_gate":
            assert spec["score"] == score and spec["gate"] is None
        else:
            omitted = int(attempt["role"].split("_")[1]) - 1
            assert spec["score"]["args"] == score["args"][:omitted] + score["args"][omitted + 1:]
            assert spec["score"]["weights"] == score["weights"][:omitted] + score["weights"][omitted + 1:]
    paired = kernel.store.evidence(kernel.store.meta("batch_evidence:" + result["batch_id"]), pointer="/arms", limit=100)["value"]
    assert len(paired) == 5 and all(row["status"] == "completed" for row in paired)
    assert kernel.status()["attempts"] == kernel.status()["executions"] == 5


def test_aliases_share_exactly_one_execution_but_each_attempt_is_retained(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    first = kernel.submit_batch([strategy("original"), strategy("alias", factor("alias"))], action_id="same_request")
    assert first["attempts"][0]["run_id"] == first["attempts"][1]["run_id"]
    assert first["attempts"][1]["reused"] is True
    assert kernel.submit_batch([strategy("original"), strategy("alias", factor("alias"))], action_id="same_request") == first
    assert kernel.status()["attempts"] == 2
    kernel.execute_pending(panel)
    third = kernel.submit_batch([strategy("third retained attempt", factor("alias"))])
    assert third["attempts"][0]["reused"] is True
    assert third["attempts"][0]["status"] == "completed", run_rows(kernel)
    assert kernel.execute_pending(panel)["runs"] == []
    assert kernel.status()["executions"] == 1 and kernel.status()["attempts"] == 3


def test_rejected_and_numerically_failed_branches_do_not_block_valid_account(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    batch = kernel.submit_batch([strategy("unsupported", {"op": "python", "code": "bad"}),
                                 strategy("missing", factor("not_registered")),
                                 strategy("bad gate", gate=constant(2)),
                                 strategy("missing field", factor("unavailable")), strategy("valid")])
    assert [row["status"] for row in batch["attempts"][:2]] == ["rejected", "rejected"]
    result = kernel.execute_pending(panel)
    assert sorted(row["status"] for row in result["runs"]) == ["completed", "failed", "failed"]
    assert kernel.status()["attempts"] == 5 and kernel.status()["executions"] == 3
    failed = [row for row in run_rows(kernel) if row["status"] == "failed"]
    assert len(failed) == 2 and all(row["error"] and row["evidence_id"] is None for row in failed)
    paired = kernel.store.evidence(kernel.store.meta("batch_evidence:" + batch["batch_id"]), pointer="/arms", limit=100)["value"]
    assert len(paired) == 5 and {row["status"] for row in paired} == {"completed", "failed", "rejected"}


@pytest.mark.parametrize("limit,expected", [(2, "completed"), (1, "queued")])
def test_abandoned_running_entry_recovers_only_under_os_lock_and_consumes_old_attempt(tmp_path, limit, expected):
    kernel, panel, _ = initialize(tmp_path, budget={"max_executions": limit})
    run_id = kernel.submit_batch([strategy()])["attempts"][0]["run_id"]
    orphan = kernel.root / "accounts" / "abandoned_partial"
    orphan.mkdir(parents=True)
    (orphan / "daily.parquet.tmp").write_bytes(b"unfinished account, never committed")
    # Simulate a process which exited after the durable execution-start commit.
    with kernel.store.transaction() as db:
        db.execute("UPDATE runs SET status='running',executions=1 WHERE id=?", (run_id,))
        db.execute("UPDATE attempts SET status='running' WHERE run_id=?", (run_id,))
    with exclusive_lock(kernel.root / "executor.lock"):
        with pytest.raises(RuntimeError, match="live owner"):
            kernel.execute_pending(panel)
    assert run_rows(kernel)[0]["status"] == "running"
    result = ResearchKernel(kernel.root).execute_pending(panel)
    row = run_rows(kernel)[0]
    assert row["status"] == expected, row["error"]
    assert row["executions"] == limit
    assert len(event_rows(kernel, "interrupted_execution_recovered")) == 1
    assert (orphan / "daily.parquet.tmp").read_bytes() == b"unfinished account, never committed"
    if expected == "completed":
        assert len(result["runs"]) == 1
        assert row["artifact_dir"] != str(orphan.relative_to(kernel.root))
        assert len(pd.read_parquet(kernel.root / row["artifact_dir"] / "daily.parquet")) == 40
    else:
        assert result["runs"] == [] and row["evidence_id"] is None


def test_failed_execution_and_rejected_or_reused_attempts_consume_limits(tmp_path, monkeypatch):
    import quanta_agents.research_kernel.controller as controller
    monkeypatch.setattr(controller.time, "time", lambda: 1234567.0)
    kernel, panel, _ = initialize(tmp_path, budget={"max_attempts": 4, "max_executions": 1})
    kernel.submit_batch([strategy("fails", gate=constant(2)), strategy("later")])
    result = kernel.execute_pending(panel)
    assert [row["status"] for row in result["runs"]] == ["failed"]
    assert kernel.status()["runs"] == {"failed": 1, "queued": 1}
    kernel.submit_batch([strategy("bad definition", {"op": "unknown"}), strategy("same queued")])
    assert kernel.status()["attempts"] == 4
    with pytest.raises(ValueError, match="Attempt budget"):
        kernel.submit_batch([strategy("even alias counts", factor("alias"))])
    assert kernel.execute_pending(panel)["runs"] == []
    assert kernel.status()["executions"] == 1


@pytest.mark.parametrize("rewrite_manifest", [False, True])
def test_completed_artifact_pollution_is_rejected_even_if_local_manifest_is_rewritten(tmp_path, rewrite_manifest):
    kernel, panel, _ = initialize(tmp_path)
    kernel.submit_batch([strategy()])
    kernel.execute_pending(panel)
    row = run_rows(kernel)[0]
    assert row["status"] == "completed", row["error"]
    folder = kernel.root / row["artifact_dir"]
    result_path = folder / "result.json"
    value = json.loads(result_path.read_text(encoding="utf-8"))
    value["summary"]["forged_success"] = True
    result_path.write_text(serial(value), encoding="utf-8")
    if rewrite_manifest:
        path = folder / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["result.json"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        path.write_text(serial(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="digest|manifest|artifact"):
        kernel.execute_pending(panel)
    assert kernel.status()["executions"] == 1


def test_evidence_pagination_pointer_escaping_and_byte_budget(tmp_path):
    store = Store(tmp_path)
    payload = {"rows": [{"row": i, "text": "边界" * 100} for i in range(9)],
               "a/b": {"~key": "resolved"}}
    identity = store.put_evidence("test", payload)
    assert store.put_evidence("test", payload) == identity
    first = store.evidence(identity, pointer="/rows", offset=0, limit=4, max_bytes=6000)
    second = store.evidence(identity, pointer="/rows", offset=4, limit=4, max_bytes=6000)
    assert first["total"] == 9 and [v["row"] for v in first["value"]] == [0, 1, 2, 3]
    assert [v["row"] for v in second["value"]] == [4, 5, 6, 7]
    assert store.evidence(identity, pointer="/a~1b/~0key")["value"] == "resolved"
    oversized = store.evidence(identity, pointer="/rows", limit=9, max_bytes=600)
    assert oversized["status"] == "narrow_query_required"
    assert len(serial(oversized).encode("utf-8")) <= 600
    long_key_id = store.put_evidence("long_names", {"很长的键" * 2000: "value"})
    narrowed = store.evidence(long_key_id, max_bytes=600)
    assert narrowed["status"] == "narrow_query_required"
    assert len(serial(narrowed).encode("utf-8")) <= 600


def test_evidence_content_hash_is_verified_on_every_read(tmp_path):
    store = Store(tmp_path)
    identity = store.put_evidence("test", {"answer": "original"})
    row = store.rows("SELECT * FROM evidence WHERE id=?", (identity,))[0]
    (store.root / row["path"]).write_text('{"answer":"forged"}', encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        store.evidence(identity)
    with pytest.raises(ValueError, match="changed"):
        store.put_evidence("test", {"answer": "original"})


def test_factor_diagnostics_purge_terminal_labels_and_ignore_prices_after_frozen_end():
    panel = synthetic_panel()
    dates = panel.dates[125:165]
    start, end = str(dates[0].date()), str(dates[-1].date())
    scores = {"F1": panel.fields["close"].copy()}
    before = scores["F1"].copy(deep=True)
    observed = factor_report(panel, scores, start=start, end=end)
    for horizon in (5, 20):
        opening = panel.fields["open"]
        label = (opening.shift(-horizon - 1) / opening.shift(-1) - 1).loc[dates]
        label.iloc[-horizon - 1:] = np.nan
        manual = scores["F1"].loc[dates].rank(axis=1).corrwith(label.rank(axis=1), axis=1)
        found = observed["factors"]["F1"]["horizons"][str(horizon)]
        assert found["days"] == len(dates) - horizon - 1
        assert found["mean_ic"] == pytest.approx(manual.mean(), abs=1e-14)
        assert found["annual"][0]["days"] == found["days"]
    changed = deepcopy(panel)
    changed.fields["open"].iloc[165:] *= np.arange(1, 9)
    assert factor_report(changed, scores, start=start, end=end) == observed
    assert_frame_equal(scores["F1"], before, check_exact=True)
    assert not any("label" in key for key in panel.fields)


def test_action_id_is_idempotent_and_extension_does_not_execute_new_capability(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    response = {"action": "propose_batch", "reason": "generated test", "payload_json": serial({"specs": [strategy()]})}
    first = kernel.apply_action(response, action_id="response_once")
    revision = kernel.status()["revision"]
    assert kernel.apply_action(response, action_id="response_once") == first
    assert kernel.status()["attempts"] == 1 and kernel.status()["revision"] == revision
    extension = {"action": "request_extension", "reason": "missing operator",
                 "payload_json": serial({"capability": "synthetic_missing", "reason": "causal test extension",
                                         "acceptance_tests": ["future data does not alter prior scores"]})}
    outcome = kernel.apply_action(extension, action_id="extension_once")
    assert outcome["executable"] is False
    assert kernel.status()["executions"] == 0
    assert kernel.execute_pending(panel)["runs"][0]["status"] == "completed"


def test_explicit_failed_retry_retains_prior_failure_and_consumes_execution_budget(tmp_path):
    kernel, panel, _ = initialize(tmp_path, budget={"max_executions": 2})
    run_id = kernel.submit_batch([strategy("fails", gate=constant(2))])["attempts"][0]["run_id"]
    assert kernel.execute_pending(panel)["runs"][0]["status"] == "failed"
    assert kernel.execute_pending(panel)["runs"] == []  # no automatic retry
    kernel.retry_run(run_id)
    assert run_rows(kernel)[0]["status"] == "queued"
    assert kernel.execute_pending(panel)["runs"][0]["status"] == "failed"
    assert run_rows(kernel)[0]["executions"] == 2
    assert len(event_rows(kernel, "execution_failed")) == 2
    with pytest.raises(ValueError, match="budget"):
        kernel.retry_run(run_id)
    assert kernel.status()["executions"] == 2


def model_receipt(response, *, model="gpt-6-astra", effort="xhigh", verified=True):
    return {"model": model, "effort": effort, "runtime_identity": {"verified": verified},
            "response": response, "usage": {"test_only": True}}


class SavedFakeGateway:
    """A deterministic transport stub; never calls any model or alters numerical work."""
    def __init__(self, receipt):
        self.receipt = receipt
        self.calls = 0

    def run(self, **kwargs):
        self.calls += 1
        assert kwargs["schema"]["additionalProperties"] is False
        assert "RESEARCH_STATE_JSON" in kwargs["prompt"]
        return deepcopy(self.receipt)


def test_model_step_persists_one_short_action_and_retains_model_budget(tmp_path):
    from quanta_agents.research_kernel.model import model_step
    kernel, panel, _ = initialize(tmp_path, budget={"max_model_calls": 1, "max_context_bytes": 10000})
    action = {"action": "propose_batch", "reason": "synthetic mechanism and falsifier",
              "payload_json": serial({"specs": [strategy()]})}
    gateway = SavedFakeGateway(model_receipt(action))
    outcome = model_step(kernel, gateway=gateway)
    assert outcome["status"] == "applied"
    assert gateway.calls == 1 and kernel.status()["model_calls"] == 1
    assert kernel.status()["attempts"] == 1 and kernel.status()["executions"] == 0
    assert model_step(kernel, gateway=gateway)["status"] == "model_budget_exhausted"
    assert gateway.calls == 1
    assert kernel.store.meta("model_stopped") is True
    assert kernel.store.meta("stopped") is False  # already registered work remains authorized
    assert kernel.execute_pending(panel)["runs"][0]["status"] == "completed"
    assert kernel.store.meta("stopped") is True


@pytest.mark.parametrize("model,effort,verified", [("other", "xhigh", True),
    ("gpt-6-astra", "low", True), ("gpt-6-astra", "xhigh", False)])
def test_model_identity_mismatch_retains_completion_without_admitting_action(tmp_path, model, effort, verified):
    from quanta_agents.research_kernel.model import model_step
    kernel, _, _ = initialize(tmp_path, budget={"max_context_bytes": 10000})
    action = {"action": "propose_batch", "reason": "generated", "payload_json": serial({"specs": [strategy()]})}
    gateway = SavedFakeGateway(model_receipt(action, model=model, effort=effort, verified=verified))
    with pytest.raises(ValueError):
        model_step(kernel, gateway=gateway)
    assert gateway.calls == 1
    assert kernel.status()["attempts"] == kernel.status()["executions"] == 0
    row = kernel.store.rows("SELECT * FROM model_calls")[0]
    assert row["status"] == "needs_recovery" and row["error"]


def test_saved_unresolved_model_completion_is_recovered_without_new_call(tmp_path, monkeypatch):
    from quanta_agents.meta_v6 import gateway as transport
    from quanta_agents.research_kernel.model import model_step, recover_model_call
    kernel, _, _ = initialize(tmp_path, budget={"max_model_calls": 1})
    action = {"action": "propose_batch", "reason": "recovered saved test", "payload_json": serial({"specs": [strategy()]})}
    receipt = model_receipt(action)
    folder = kernel.root / "model_calls" / "saved"
    folder.mkdir(parents=True)
    original = serial(receipt).encode("utf-8")
    (folder / "receipt.json").write_bytes(original)
    with kernel.store.transaction() as db:
        db.execute("INSERT INTO model_calls VALUES (?,?,?,?,?,?,?)",
                   ("saved", "needs_recovery", str(folder), None, None, "previous interruption", time.time()))
    verified_paths = []
    def saved_verifier(path):
        verified_paths.append(Path(path))
        assert Path(path) == folder
        return json.loads((folder / "receipt.json").read_bytes())
    monkeypatch.setattr(transport, "verify_saved_completion", saved_verifier)
    gateway = SavedFakeGateway(receipt)
    assert model_step(kernel, gateway=gateway)["status"] == "applied"
    assert gateway.calls == 0 and verified_paths == [folder]
    assert kernel.status()["model_calls"] == kernel.status()["attempts"] == 1
    recover_model_call(kernel, "saved")
    assert kernel.status()["attempts"] == 1  # the saved action ID is idempotent
    assert (folder / "receipt.json").read_bytes() == original


def test_protocol_response_boundaries_and_context_size_are_explicit(tmp_path):
    from quanta_agents.research_kernel.protocol import build_context, validate_action
    kernel, _, _ = initialize(tmp_path)
    context = build_context(kernel)
    assert context["utf8_bytes"] == len(context["prompt"].encode("utf-8")) <= 6000
    assert context["packet"]["state"]["scope"]["scope_role"] == "exposed_development"
    for raw in ['{"query":"a","query":"b"}', '{"limit":NaN}', '[1,2]', '{"python":"code"}']:
        with pytest.raises(ValueError):
            validate_action({"action": "query_assets", "reason": "boundary", "payload_json": raw})
    with pytest.raises(ValueError, match="byte"):
        validate_action({"action": "query_assets", "reason": "boundary", "payload_json": serial({"query": "大" * 200})}, max_bytes=100)
    kernel.submit_batch([strategy("future forbidden", factor("future_returns"))])
    next_context = build_context(kernel)
    assert next_context["packet"]["recent_rejections"]
    assert next_context["utf8_bytes"] <= 6000


def test_large_legal_evidence_query_yields_addressable_narrowing_in_next_context(tmp_path):
    from quanta_agents.research_kernel.protocol import build_context
    kernel, _, _ = initialize(tmp_path)
    payload = {"rows": [{"record": i, "detail": "合成证据" * 140} for i in range(4)]}
    identity = kernel.store.put_evidence("verbose_generated", payload)
    action = {"action": "get_evidence", "reason": "inspect saved evidence",
              "payload_json": serial({"evidence_id": identity, "pointer": "/rows", "limit": 4})}
    kernel.apply_action(action, action_id="verbose_query")
    context = build_context(kernel)
    assert context["utf8_bytes"] <= 6000
    assert identity in context["prompt"]
    assert "narrow" in context["prompt"].lower()
    text = payload["rows"][0]["detail"]
    pages = [kernel.store.evidence(identity, pointer="/rows/0/detail", offset=i, limit=100, max_bytes=6000)
             for i in range(0, len(text), 100)]
    assert all(page["total"] == len(text) for page in pages)
    assert "".join(page["value"] for page in pages) == text
