"""Finite engineering fixtures. No supplier requests and no market results."""
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import json
import multiprocessing
import time

import pytest

from quanta_agents.meta_v3.closing import ClosingPolicy, FINAL_ACTION
from quanta_agents.meta_v3.ledger import Ledger, AdmissionBlocked, worker_lease


P = ClosingPolicy(task_tokens=400, stage_tokens=400, task_calls=4, stage_calls=4,
                  call_reserve=80, closing_reserve=80, closing_seconds=60)
A = ("inspect_inputs", FINAL_ACTION)


def request(menu, state, decision):
    return "engineering fixture", {"type": "object", "properties": {"action": {"enum": list(menu)}}}


def new(tmp_path, policy=P, tasks=None):
    return Ledger.create(tmp_path / "stage", policy=policy, tasks=tasks or {"one": {}},
                         deadline_epoch=time.time() + 7200, provenance={"engineering_fixture": True})


def settle(job, intent, *, cost=10, action="inspect_inputs", final=False):
    receipt = {"request_identity": {"intent_id": intent["intent_id"]},
        "usage": {"input_tokens": cost, "output_tokens": 0}, "artifact_sha256": {},
        "response": {"action": action}}
    job.receive_saved(intent["intent_id"], lambda *a, **k: receipt)
    job.begin_apply(intent["intent_id"])
    job.finish_apply(intent["intent_id"], {"fixture": True}, final=final)


def test_closing_mode_and_one_last_slot_survive_restart(tmp_path):
    job = new(tmp_path, replace(P, task_calls=2, stage_calls=2))
    a = job.reserve("one", A, request)
    settle(job, a)
    job = Ledger(job.root)
    b = job.reserve("one", A, request)
    assert b["mode"] == "close_only" and b["actions"] == [FINAL_ACTION]
    assert Ledger(job.root).status("one")["persisted_mode"] == "close_only"
    settle(job, b, action=FINAL_ACTION, final=True)
    assert job.status("one")["terminal"] == "submitted"
    with pytest.raises(AdmissionBlocked):
        job.reserve("one", A, request)
    assert len(job.history("one")) == 2


def test_siblings_keep_stage_final_reserves(tmp_path):
    job = new(tmp_path, replace(P, task_tokens=160, stage_tokens=160), {"one": {}, "two": {}})
    a = job.reserve("one", A, request)
    assert a["mode"] == "close_only"
    settle(job, a, cost=80, action=FINAL_ACTION, final=True)
    b = job.reserve("two", A, request)
    assert b["mode"] == "close_only"
    settle(job, b, cost=80, action=FINAL_ACTION, final=True)
    assert job.status("two")["known_tokens"] == 160


def test_unknown_and_unapplied_block_whole_stage(tmp_path):
    job = new(tmp_path, tasks={"one": {}, "two": {}})
    a = job.reserve("one", A, request)
    job.unknown(a["intent_id"], "connection lost")
    for task in ("one", "two"):
        with pytest.raises(AdmissionBlocked):
            Ledger(job.root).reserve(task, A, request)
    assert job.status("two")["unknown_or_pending_reserve"] == 80
    assert job.status("two")["old_v2_unknown_reserve"] == 80000
    settle(job, a)
    assert job.reserve("two", A, request)["ordinal"] == 1


def test_crash_before_commit_rolls_back_and_after_commit_never_redispatches(tmp_path):
    job = new(tmp_path)
    with pytest.raises(RuntimeError):
        job.reserve("one", A, lambda *a: (_ for _ in ()).throw(RuntimeError("power loss")))
    assert job.status("one")["calls"] == []
    intent = job.reserve("one", A, request)
    with pytest.raises(AdmissionBlocked):
        Ledger(job.root).reserve("one", A, request)
    assert len(job.status("one")["calls"]) == 1
    assert job.call(intent["intent_id"])["status"] == "pending"


def test_nonfinal_in_closing_is_paid_failure_never_controller_final(tmp_path):
    job = new(tmp_path, replace(P, task_calls=1, stage_calls=1))
    intent = job.reserve("one", A, request)
    receipt = {"request_identity": {"intent_id": intent["intent_id"]},
        "usage": {"input_tokens": 12, "output_tokens": 3}, "artifact_sha256": {},
        "response": {"action": "inspect_inputs"}}
    job.receive_saved(intent["intent_id"], lambda *a, **k: receipt)
    with pytest.raises(AdmissionBlocked):
        job.begin_apply(intent["intent_id"])
    state = job.status("one")
    assert state["known_tokens"] == 15 and state["final_call"] is None
    assert state["terminal"] == "invalid_action"


def test_actual_overrun_preserved_and_no_money_created(tmp_path):
    job = new(tmp_path)
    settle(job, job.reserve("one", A, request), cost=401)
    with pytest.raises(AdmissionBlocked):
        job.reserve("one", A, request)
    state = job.status("one")
    assert state["known_tokens"] == 401 and state["terminal"] == "terminal_without_submission"
    assert state["final_call"] is None


def _compete(root, task, barrier, output):
    job = Ledger(root)
    barrier.wait()
    try:
        job.reserve(task, A, request)
        output.put("reserved")
    except AdmissionBlocked:
        output.put("blocked")


def test_real_processes_compete_on_one_shared_ledger(tmp_path):
    job = new(tmp_path, tasks={"one": {}, "two": {}})
    ctx = multiprocessing.get_context("spawn")
    barrier, output = ctx.Barrier(2), ctx.Queue()
    workers = [ctx.Process(target=_compete, args=(str(job.root), task, barrier, output)) for task in ("one", "two")]
    for p in workers:
        p.start()
    for p in workers:
        p.join(40)
        assert p.exitcode == 0
    assert sorted(output.get(timeout=2) for _ in workers) == ["blocked", "reserved"]
    assert len(job.status("one")["calls"]) == 1


def test_receipt_and_apply_recovery_is_idempotent_and_does_not_rerun_tool(tmp_path):
    job = new(tmp_path)
    a = job.reserve("one", A, request)
    settle(job, a)
    assert job.begin_apply(a["intent_id"]) is None
    b = job.reserve("one", A, request)
    receipt = {"request_identity": {"intent_id": b["intent_id"]},
        "usage": {"input_tokens": 10, "output_tokens": 0}, "artifact_sha256": {},
        "response": {"action": "inspect_inputs"}}
    job.receive_saved(b["intent_id"], lambda *a, **k: receipt)
    job.begin_apply(b["intent_id"])
    with pytest.raises(AdmissionBlocked):
        Ledger(job.root).begin_apply(b["intent_id"])
    with pytest.raises(AdmissionBlocked):
        Ledger(job.root).reserve("one", A, request)
    job.finish_apply(b["intent_id"], {"recovered_saved_evidence": True})
    assert len(job.history("one")) == 2


def test_worker_os_lease_and_plan_drift(tmp_path):
    job = new(tmp_path)
    with worker_lease(job.root):
        with pytest.raises(AdmissionBlocked):
            with worker_lease(job.root):
                pass
    with worker_lease(job.root):
        pass
    plan = json.loads((job.root / "plan.json").read_text(encoding="utf-8"))
    plan["policy"]["task_tokens"] += 1
    (job.root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(AdmissionBlocked, match="drift"):
        job.reserve("one", A, request)
