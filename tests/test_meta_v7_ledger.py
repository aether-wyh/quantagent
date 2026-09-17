import sqlite3

import pytest

from quanta_agents.meta_v7.ledger import ProjectLedger


def ledger(tmp_path):
    value = ProjectLedger(tmp_path / "shared_project")
    value.register_study("first", {"split_plan": {"train_start": "2016-01-01", "train_end": "2020-12-31"}})
    return value


def test_restart_and_identical_event_are_idempotent_but_changed_content_refused(tmp_path):
    value = ledger(tmp_path)
    spec = {"attempt_id": "a", "strategy": {"score": "F1", "top_n": 20}}
    old = value.record_trial("first", "a_registered", "strategy", spec)
    spec["strategy"]["top_n"] = 999
    reopened = ProjectLedger(value.root)
    assert reopened.list_trials()[0]["spec"]["strategy"]["top_n"] == 20
    assert reopened.record_trial("first", "a_registered", "strategy", old["spec"]) == old
    with pytest.raises(ValueError, match="immutable"):
        reopened.record_trial("first", "a_registered", "strategy", spec)
    with pytest.raises(ValueError, match="immutable"):
        reopened.record_trial("first", "a_registered", "strategy", old["spec"], status="completed")
    with pytest.raises(ValueError, match="immutable"):
        reopened.register_study("first", {"changed": True})


def test_cross_study_rename_retry_transitions_and_failed_history_are_not_independent(tmp_path):
    value = ledger(tmp_path)
    value.register_study("second", {"seed": 456})
    spec = {"attempt_id": "a", "strategy": {"name": "original", "top_n": 20, "score": {"id": "F1"}}}
    value.record_trial("first", "a_register", "account", spec)
    value.record_trial("first", "a_fail", "account", {**spec, "event": "finished", "status": "failed", "evidence": "ev1"}, status="failed", evidence={"error": "observed"})
    retry = {"attempt_id": "b", "retry_of": "first/a", "strategy": {"name": "renamed", "top_n": 20, "score": {"id": "F1"}}}
    value.record_trial("second", "b_reuse", "account", retry, status="reused", evidence="original bytes")
    state = value.summary()
    assert (state["trial_events"], state["total_attempts"], state["unique_economic_trials"]) == (3, 2, 1)
    assert state["failed_attempts"] == state["reuse_attempts"] == state["explicit_reuse_attempts"] == 1
    assert state["dsr_independent_n"] is None and state["independent_sample_count"] is None
    assert value.list_trials()[1]["evidence"] == {"error": "observed"}
    changed = {**retry, "attempt_id": "c", "strategy": {"top_n": 21, "score": {"id": "F1"}}}
    value.record_trial("second", "c", "account", changed)
    assert value.summary()["unique_economic_trials"] == 2


def test_same_attempt_cannot_silently_change_economics(tmp_path):
    value = ledger(tmp_path)
    value.record_trial("first", "event1", "factor", {"attempt_id": "a", "expression": "close"})
    with pytest.raises(ValueError, match="logical attempt"):
        value.record_trial("first", "event2", "factor", {"attempt_id": "a", "expression": "volume"})
    assert value.summary()["trial_events"] == 1


def test_scope_and_source_are_economic_identity_not_prose(tmp_path):
    value = ledger(tmp_path)
    for i, (source, end) in enumerate((("hash1", "2020-12-31"), ("hash2", "2020-12-31"), ("hash1", "2019-12-31"))):
        value.record_trial("first", f"trial{i}", "account", {"source_sha256": source, "end": end, "strategy": {"top_n": 20}})
    assert value.summary()["unique_economic_trials"] == 3


def test_registered_training_and_actual_exposure_block_inclusive_overlap_across_studies(tmp_path):
    value = ledger(tmp_path)
    value.register_study("second", {})
    assert not value.can_validate("first", start="2020-12-31", end="2021-01-02")["allowed"]
    # V7 initialization has already loaded training values before registering.
    prior_training = value.can_validate("second", start="2019-01-01", end="2019-12-31")
    assert not prior_training["allowed"]
    assert prior_training["prior_exposures"][0]["study_id"] == "first"
    item = value.record_exposure("first", start="2021-01-01", end="2024-12-31", role="development", evidence_id="EV1", reason="prior diagnostic read")
    assert value.record_exposure("first", start="2021-01-01", end="2024-12-31", role="development", evidence_id="EV1", reason="prior diagnostic read") == item
    for study in ("first", "second"):
        denied = value.can_validate(study, start="2024-12-31", end="2025-12-31")
        assert not denied["allowed"] and len(denied["prior_exposures"]) == 1
    permitted = value.can_validate("second", start="2025-01-01", end="2025-12-31")
    assert permitted["allowed"] and not permitted["formal_validation_certified"]
    assert "unrecorded" in permitted["reason"]
    assert value.summary()["exposures"] == 1


def test_pagination_and_exposure_filters_preserve_every_record(tmp_path):
    value = ledger(tmp_path)
    for i in range(7):
        value.record_trial("first", f"t{i}", "factor", {"expression": str(i)})
        value.record_exposure("first", start=f"201{i}-01-01", end=f"201{i}-12-31", role="validation", evidence_id=f"EV{i}", reason="observed")
    pages = [*value.list_trials(limit=3), *value.list_trials(limit=3, offset=3), *value.list_trials(limit=3, offset=6)]
    assert [r["trial_id"] for r in pages] == [f"t{i}" for i in range(7)]
    assert len(value.list_exposures(start="2012-01-01", end="2013-12-31")) == 2
    assert value.list_trials(offset=99) == []
    for kwargs in ({"limit": 0}, {"limit": True}, {"offset": -1}, {"limit": 10001}):
        with pytest.raises(ValueError):
            value.list_trials(**kwargs)


@pytest.mark.parametrize("tamper", ["payload", "deleted_tail", "sequence", "head"])
def test_corruption_or_truncated_history_is_detected(tmp_path, tamper):
    value = ledger(tmp_path)
    value.record_trial("first", "t", "factor", {"expression": "close"})
    with sqlite3.connect(value.db_path) as db:
        if tamper == "payload":
            db.execute("UPDATE events SET payload='{}' WHERE seq=2")
        elif tamper == "deleted_tail":
            db.execute("DELETE FROM events WHERE seq=2")
        elif tamper == "sequence":
            db.execute("UPDATE events SET seq=3 WHERE seq=2")
        else:
            db.execute("UPDATE head SET sha256='bad'")
    with pytest.raises(ValueError, match="integrity"):
        value.summary()
    with pytest.raises(ValueError, match="integrity"):
        ProjectLedger(value.root)


@pytest.mark.parametrize("start,end", [("2020-01-02", "2020-01-01"), ("2020-1-1", "2020-12-31"), ("2020-01-01T00:00:00", "2020-12-31")])
def test_invalid_dates_refused(tmp_path, start, end):
    value = ledger(tmp_path)
    with pytest.raises(ValueError):
        value.can_validate("first", start=start, end=end)


def test_unknown_study_never_appends_or_authorizes(tmp_path):
    value = ProjectLedger(tmp_path)
    with pytest.raises(KeyError):
        value.record_trial("missing", "t", "factor", {})
    with pytest.raises(KeyError):
        value.record_exposure("missing", start="2020-01-01", end="2020-12-31", role="train", evidence_id="e", reason="r")
    with pytest.raises(KeyError):
        value.can_validate("missing", start="2020-01-01", end="2020-12-31")
    assert value.summary()["trial_events"] == 0


def test_validation_admission_records_before_read_and_retries_are_exposed(tmp_path):
    value = ledger(tmp_path)
    request = dict(start="2025-01-01", end="2025-12-31", evidence_id="job", reason="before read")
    accepted = value.begin_validation("first", **request, require_independent=True)
    assert accepted["allowed"] and accepted["admission_recorded_before_read"]
    assert value.summary()["exposures"] == 1  # A subsequent caller crash cannot erase this.
    with pytest.raises(ValueError, match="Independent validation blocked"):
        value.begin_validation("first", **request, require_independent=True)
    repeated = value.begin_validation("first", **request, require_independent=False)
    assert not repeated["allowed"] and value.summary()["exposures"] == 1


def test_concurrent_validation_admission_does_not_allow_two_independent_reads(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    value = ledger(tmp_path)
    value.register_study("second", {})
    barrier = Barrier(2)
    def attempt(study):
        opened = ProjectLedger(value.root)
        barrier.wait(timeout=10)
        try:
            return opened.begin_validation(study, start="2025-01-01", end="2025-12-31",
                evidence_id=study, reason="test admission before data", require_independent=True)["allowed"]
        except ValueError as exc:
            assert "Independent validation blocked" in str(exc)
            return False
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ["first", "second"]))
    assert sorted(results) == [False, True]
    assert value.summary()["exposures"] == 1
