"""Generated accounting equivalence and durable-checkpoint failure cases only."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from time import perf_counter

import pandas as pd
import pytest

from quanta_agents.meta_v6 import legacy_account as legacy


def payload():
    days = pd.bdate_range("2018-12-17", "2019-01-21").strftime("%Y-%m-%d").tolist()
    symbols = ["sz000001", "sh600006"]
    rows = [{"date": day, "code": code, "raw_open": "10.00", "raw_close": "10.00",
             "raw_prev_close": "10.00", "raw_high": "10.00", "raw_low": "10.00",
             "volume": 1000000, "amount": 10000000, "stock_name": "合成测试公司", "accepted": True}
            for day in days for code in symbols]
    targets = [{"symbol": code, "signal_date": days[i-1], "trade_date": day,
                "available_at": day + "T09:00:00+08:00",
                "target_weight": ("0.30" if i % 2 else "0.15") if code == symbols[0] else "0.20"}
               for i, day in enumerate(days) if i for code in symbols]
    adapter = legacy.legacy_modules(optimized=False).adapter
    actions = []
    for code, record, ex in [(symbols[0], "2018-12-25", "2018-12-26"),
                             (symbols[1], "2019-01-03", "2019-01-04")]:
        actions.append(dict(action_id="fixture-"+code, symbol=code, announcement_date="2018-12-17",
            record_date=record, ex_date=ex, cash_payment_date=ex, gross_cash_per_share="0.145",
            short_holding_tax_rate="0.20", tax_rule=adapter.SUPPORTED_TAX_RULE, account_type=adapter.ACCOUNT_TYPE,
            stock_distribution_per_share="0", stock_distribution_kind="none", rights_issue=False,
            implementation_status="implementation_notice", source_url="https://example.org/synthetic.pdf",
            source_sha256="a"*64, source_fetched_at="2026-09-05T00:00:00+00:00", facts_verified=True))
    return dict(daily_data=rows, calendar=days, targets=targets, initial_cash="100000",
                corporate_actions=actions, allow_incomplete_for_integration=True, slippage_fraction="0")


def native_inputs(value):
    result = deepcopy(value)
    result["daily_data"] = pd.DataFrame(result["daily_data"])
    result["targets"] = pd.DataFrame(result["targets"])
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def events(folder):
    return [json.loads(line) for line in (folder / "account_progress.jsonl").read_text(encoding="utf-8").splitlines()]


def request(folder, value):
    folder.mkdir()
    legacy._write(folder / "account_input.json", {"version": legacy.VERSION, "payload": value,
        "payload_hash": legacy._hash(value), "source_manifest": legacy.source_manifest()}, exclusive=True)


def test_result_journal_tax_nav_equal_and_actual_output_volume_reduced(tmp_path, record_property):
    inputs = native_inputs(payload())
    originals = {path: path.read_bytes() for path in legacy.LEGACY.glob("*.py")}
    results, measured = {}, {}
    for optimized, label in [(False, "original"), (True, "daily")]:
        folder = tmp_path / label
        folder.mkdir()
        sink = legacy._CheckpointSink(folder, "synthetic-request")
        start = perf_counter()
        try:
            results[label] = legacy.simulate_legacy_account(optimized=optimized, checkpoint=sink, **inputs)
        finally:
            sink.close()
        measured[label] = {**sink.metrics(), "wall_seconds": perf_counter()-start}
    assert results["daily"] == results["original"]
    assert legacy._hash(results["daily"]) == legacy._hash(results["original"])
    result = results["daily"]
    assert any(row["event"]["kind"] == "tax_assessed" for row in result["journal"])
    assert any(row["event"]["kind"] == "cash_dividend_paid" for row in result["journal"])
    assert any(row["event"]["kind"] == "tax_paid" for row in result["journal"])
    assert legacy.legacy_modules().ledger.RawShareLedger.replay(result["genesis"], result["journal"]).snapshot() == result["final_snapshot"]
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert measured["daily"]["callback_count"] == measured["original"]["callback_count"]
    assert measured["daily"]["full_checkpoint_writes"] == len(result["daily"]) // legacy.FULL_CHECKPOINT_INTERVAL_DAYS + 2
    assert measured["daily"]["full_checkpoint_writes"] < measured["original"]["full_checkpoint_writes"] / 2
    assert measured["daily"]["total_payload_bytes_written"] < measured["original"]["total_payload_bytes_written"] * .6
    checkpoint = load(tmp_path / "daily/account_checkpoint.json")
    assert checkpoint["native_checkpoint"]["result"] == result
    assert checkpoint["persistence"]["last_complete_day"] == result["replay_dates"][-1]
    assert checkpoint["persistence"]["unfinished_current_day"] is None
    log = events(tmp_path / "daily")
    assert [row["sequence"] for row in log] == list(range(1, len(log)+1))
    previous_hash = "0"*64
    for row in log:
        assert row["previous_log_hash"] == previous_hash
        assert row["record_hash"] == legacy._hash({k:v for k,v in row.items() if k != "record_hash"})
        previous_hash = row["record_hash"]
        assert not {"journal", "snapshot", "genesis", "progress", "result"} & set(row)
    applied = [row for row in log if row["phase"] == "event_applied" and row["application"]["status"] == "applied"]
    assert len(applied) == len(result["journal"])
    for row, entry in zip(applied, result["journal"]):
        assert row["journal_entry"] == entry
        assert "event" not in row  # applied entry already contains the exact event
        assert row["application"]["entry_hash"] == entry["entry_hash"]
        assert row["application"]["event_hash"] == entry["event_hash"]
        assert row["event_payload_sha256"] == legacy._hash(entry["event"])
    benchmark = {label: {key: value[key] for key in (
        "callback_count", "full_checkpoint_writes", "total_payload_bytes_written", "wall_seconds")}
        for label, value in measured.items()}
    record_property("synthetic_checkpoint_comparison", json.dumps(benchmark))
    print("SYNTHETIC_CHECKPOINT_COMPARISON=" + json.dumps(benchmark))
    verified = legacy.verify_checkpoint_evidence(tmp_path / "daily", request_hash="synthetic-request")
    assert verified["simulation_completed"] is True
    assert verified["journal"] == result["journal"]
    assert verified["snapshot"] == result["final_snapshot"]
    assert all(verified["progress"][name] == result[name] for name in legacy.PROGRESS_TABLES)


def test_light_observer_never_reads_full_history_and_callback_cannot_mutate_inputs():
    module = legacy.legacy_modules().portfolio
    collected = []
    observer = module._CheckpointState(collected.append)
    class HistoryMustNotBeRead:
        @property
        def journal(self):
            raise AssertionError("light observer copied journal")
        def snapshot(self):
            raise AssertionError("light observer copied snapshot")
        @property
        def genesis(self):
            raise AssertionError("light observer copied genesis")
    observer.ledger = HistoryMustNotBeRead()
    observer._genesis_persisted = True
    observer.progress = {"current_date": "2019-01-01", "daily": [object()] * 1000,
                         "orders": [object()] * 1000, "trades": [], "skipped_actions": []}
    event = {"event_id": "fixture", "kind": "buy_fill", "data": {"quantity": 100}}
    observer.emit("event_intent", event=event, as_of="2019-01-01T09:30:00+08:00")
    collected[0]["event"]["data"]["quantity"] = 999
    assert event["data"]["quantity"] == 100
    assert collected[0]["persistence"]["counts"]["daily"] == 1000
    assert collected[0]["checkpoint_kind"] == "light"
    assert not {"journal", "snapshot", "progress"} & set(collected[0])


def test_financial_failure_keeps_complete_day_frontier_and_same_partial_native_state(tmp_path):
    value = payload()
    failed_day = value["calendar"][5]
    for row in value["daily_data"]:
        if row["date"] == failed_day and row["code"] == "sz000001":
            row["raw_close"] = None
    old_checkpoints = []
    with pytest.raises(ValueError, match="held-stock close unavailable"):
        legacy.simulate_legacy_account(optimized=False, checkpoint=old_checkpoints.append, **native_inputs(value))
    folder = tmp_path / "failure"
    request(folder, value)
    with pytest.raises(ValueError, match="held-stock close unavailable"):
        legacy._worker(folder)
    assert not (folder / "account_result.json").exists()
    checkpoint = load(folder / "account_checkpoint.json")
    assert checkpoint["native_checkpoint"]["phase"] == "simulation_failed"
    for key in ("journal", "snapshot", "genesis", "progress"):
        assert checkpoint["native_checkpoint"][key] == old_checkpoints[-1][key]
    assert checkpoint["persistence"]["last_complete_day"] == value["calendar"][4]
    assert checkpoint["persistence"]["unfinished_current_day"] == failed_day
    assert load(folder / "account_error.json")["financial_validation_claimed"] is False
    assert events(folder)[-1]["phase"] == "simulation_failed"
    assert load(folder / "account_checkpoint_metrics.json")["last_complete_day"] == value["calendar"][4]


def test_light_log_failure_stops_after_intent_and_keeps_last_complete_checkpoint(tmp_path, monkeypatch):
    value = payload()
    folder = tmp_path / "log_failure"
    request(folder, value)
    original_append = legacy._CheckpointSink._append_progress
    def fail_after_buy(self, record):
        if record["phase"] == "event_applied" and record["journal_entry"]["event"]["kind"] == "buy_fill":
            raise OSError("synthetic event-log write failure")
        return original_append(self, record)
    monkeypatch.setattr(legacy._CheckpointSink, "_append_progress", fail_after_buy)
    with pytest.raises(legacy.legacy_modules().portfolio.CheckpointPersistenceError, match="event-log write failure"):
        legacy._worker(folder)
    checkpoint = load(folder / "account_checkpoint.json")
    assert checkpoint["native_checkpoint"]["phase"] == "event_intent"
    verified = legacy.verify_checkpoint_evidence(folder)
    assert verified["last_complete_day"] == value["calendar"][0]
    assert verified["unfinished_current_day"] == value["calendar"][1]
    log = events(folder)
    assert log[-1]["phase"] == "event_intent"
    assert log[-1]["event"]["kind"] == "buy_fill"
    assert not any(row["phase"] == "simulation_completed" for row in log)
    assert not (folder / "account_result.json").exists()
    metrics = load(folder / "account_checkpoint_metrics.json")
    assert metrics["last_complete_day"] == value["calendar"][0]
    assert metrics["unfinished_current_day"] == value["calendar"][1]


def test_eod_checkpoint_failure_does_not_advance_durable_frontier(tmp_path, monkeypatch):
    value = payload()
    folder = tmp_path / "eod_failure"
    request(folder, value)
    def fail_eod(self, content):
        raise OSError("synthetic EOD commit failure")
    monkeypatch.setattr(legacy._CheckpointSink, "_append_day", fail_eod)
    with pytest.raises(legacy.legacy_modules().portfolio.CheckpointPersistenceError, match="EOD commit failure"):
        legacy._worker(folder)
    checkpoint = load(folder / "account_checkpoint.json")
    assert checkpoint["native_checkpoint"]["phase"] == "event_intent"  # initial genesis checkpoint
    assert checkpoint["persistence"]["last_complete_day"] is None
    metrics = load(folder / "account_checkpoint_metrics.json")
    assert metrics["last_complete_day"] is None
    assert metrics["unfinished_current_day"] == value["calendar"][0]
    assert not (folder / "account_result.json").exists()
    assert not any(row["phase"] == "simulation_completed" for row in events(folder))
    verified = legacy.verify_checkpoint_evidence(folder)
    assert verified["complete_days"] == 0
    assert verified["last_complete_day"] is None
    assert verified["unfinished_current_day"] == value["calendar"][0]
    # The initial cash application is still present with its original event/hash.
    assert any(row["phase"] == "event_applied" and row["journal_entry"]["event"]["kind"] == "cash_deposit" for row in events(folder))


def windows_error(code):
    error = PermissionError("synthetic Windows replacement conflict")
    error.winerror = code
    return error


@pytest.mark.parametrize("code", [5, 32])
def test_transient_windows_replace_conflict_is_bounded_without_rewriting_payload(tmp_path, monkeypatch, code):
    path = tmp_path / "checkpoint.json"
    path.write_text('"prior"', encoding="utf-8")
    original_replace = legacy.os.replace
    calls, waits = [], []
    def replace(source, destination):
        calls.append((source, destination))
        if len(calls) <= 2:
            raise windows_error(code)
        return original_replace(source, destination)
    monkeypatch.setattr(legacy.os, "replace", replace)
    monkeypatch.setattr(legacy.time, "sleep", waits.append)
    written = legacy._write(path, {"value": "new"})
    assert load(path) == {"value": "new"}
    assert written == path.stat().st_size
    assert len(calls) == 3
    assert waits == list(legacy.REPLACE_RETRY_DELAYS[:2])


def test_exhausted_or_unrelated_replace_failure_is_not_hidden(tmp_path, monkeypatch):
    path = tmp_path / "checkpoint.json"
    prior = b'{"prior":true}'
    path.write_bytes(prior)
    calls, waits = [], []
    def replace(source, destination):
        calls.append((source, destination))
        raise windows_error(5)
    monkeypatch.setattr(legacy.os, "replace", replace)
    monkeypatch.setattr(legacy.time, "sleep", waits.append)
    with pytest.raises(PermissionError):
        legacy._write(path, {"value": "not_committed"})
    assert path.read_bytes() == prior
    assert path.with_name(path.name + ".tmp").exists()
    assert len(calls) == len(legacy.REPLACE_RETRY_DELAYS) + 1
    assert waits == list(legacy.REPLACE_RETRY_DELAYS)
    def unrelated(source, destination):
        raise windows_error(123)
    monkeypatch.setattr(legacy.os, "replace", unrelated)
    waits.clear()
    with pytest.raises(PermissionError):
        legacy._write(path, {"value": "still_not_committed"})
    assert waits == []
    assert path.read_bytes() == prior


def test_private_original_observer_is_not_changed():
    original = legacy.legacy_modules(optimized=False).portfolio
    optimized = legacy.legacy_modules().portfolio
    assert original._CheckpointState.__name__ == "_CheckpointState"
    assert optimized._CheckpointState is not original._CheckpointState
    assert optimized._CheckpointState.__name__ == "IncrementalCheckpointState"


def test_daily_delta_observer_avoids_history_and_advances_only_after_callback():
    class Sink:
        checkpoint_interval_days = 64
        def __init__(self):
            self.rows = []
            self.reject = False
        def __call__(self, value):
            self.rows.append(value)
            if self.reject:
                raise OSError("synthetic daily callback failure")
    class Ledger:
        @property
        def journal(self):
            raise AssertionError("daily observer read full journal")
        @property
        def genesis(self):
            raise AssertionError("daily observer read genesis")
        def snapshot(self):
            raise AssertionError("daily observer read snapshot")
    sink = Sink()
    observer = legacy.legacy_modules().portfolio._CheckpointState(sink)
    observer.ledger = Ledger()
    observer._genesis_persisted = True
    # Historical elements deliberately cannot be JSON serialized.
    observer.progress = {"current_date": "2019-01-03", "daily": [object()] * 62 + [{"date": "2019-01-03"}],
                         "orders": [object()] * 1000 + [{"new": [1]}], "trades": [], "skipped_actions": []}
    observer._committed_counts = {"daily": 62, "orders": 1000, "trades": 0, "skipped_actions": 0}
    observer.emit("day_completed", date="2019-01-03")
    assert sink.rows[0]["progress_delta"] == {"daily": [{"date": "2019-01-03"}], "orders": [{"new": [1]}], "trades": [], "skipped_actions": []}
    sink.rows[0]["progress_delta"]["orders"][0]["new"].append(2)
    assert observer.progress["orders"][-1]["new"] == [1]
    assert observer._last_complete_day == "2019-01-03"
    # Skip the periodic boundary to exercise failure of another incremental day.
    observer._interval = 128
    observer.progress["current_date"] = "2019-01-04"
    observer.progress["daily"].append({"date": "2019-01-04"})
    sink.reject = True
    with pytest.raises(legacy.legacy_modules().portfolio.CheckpointPersistenceError):
        observer.emit("day_completed", date="2019-01-04")
    assert observer._last_complete_day == "2019-01-03"
    assert observer._committed_counts["daily"] == 63


def short_payload(count=5):
    value = payload()
    value["calendar"] = value["calendar"][:count]
    value["daily_data"] = [row for row in value["daily_data"] if row["date"] in value["calendar"]]
    value["targets"] = [row for row in value["targets"] if row["trade_date"] in value["calendar"]]
    value["corporate_actions"] = []
    return value


def test_periodic_anchors_preserve_exact_native_result_and_delta_reconstruction(tmp_path):
    value = payload()
    results, metrics = {}, {}
    for interval in (1, 7, 64):
        folder = tmp_path / str(interval)
        folder.mkdir()
        sink = legacy._CheckpointSink(folder, "same-input", checkpoint_interval_days=interval)
        try:
            results[interval] = legacy.simulate_legacy_account(checkpoint=sink, **native_inputs(value))
        finally:
            sink.close()
        metrics[interval] = sink.metrics()
        verified = legacy.verify_checkpoint_evidence(folder)
        assert verified["progress"]["daily"] == results[interval]["daily"]
        assert verified["journal"] == results[interval]["journal"]
        assert verified["snapshot"] == results[interval]["final_snapshot"]
        assert sink.full_count == len(value["calendar"]) // interval + 2
        assert sink.day_count == len(value["calendar"])
    assert results[1] == results[7] == results[64]
    assert metrics[64]["total_payload_bytes_written"] < .35 * metrics[1]["total_payload_bytes_written"]
    print("SYNTHETIC_INTERVAL_COMPARISON=" + json.dumps({str(key): {
        "full_writes": item["full_checkpoint_writes"], "bytes": item["total_payload_bytes_written"]}
        for key, item in metrics.items()}))


@pytest.fixture
def finished_folder(tmp_path):
    folder = tmp_path / "finished"
    request(folder, short_payload())
    legacy._worker(folder)
    assert legacy.verify_checkpoint_evidence(folder)["simulation_completed"]
    return folder


def rewrite_chain(path, rows, *, daily=False):
    hash_key = "commit_hash" if daily else "record_hash"
    previous_key = "previous_commit_hash" if daily else "previous_log_hash"
    sequence_key = "day_sequence" if daily else "sequence"
    head = "0" * 64
    with path.open("wb") as stream:
        for i, row in enumerate(rows, 1):
            row = {key: value for key, value in row.items() if key != hash_key}
            row[previous_key], row[sequence_key] = head, i
            row[hash_key] = legacy._hash(row)
            head = row[hash_key]
            stream.write((legacy._serial(row) + "\n").encode("utf-8"))


@pytest.mark.parametrize("mutation", ["byte_corruption", "missing_day", "wrong_starts", "wrong_progress_head", "wrong_journal_state", "wrong_request", "application_id", "application_time", "fake_duplicate", "input_bytes", "ahead_hint", "wrong_hint_head", "wrong_hint_date", "result_hash"])
def test_verifier_rejects_corrupted_incremental_evidence(finished_folder, mutation):
    folder = finished_folder
    days_path = folder / "account_days.jsonl"
    if mutation == "byte_corruption":
        with days_path.open("ab") as stream:
            stream.write(b'{"broken":\n')
    elif mutation in {"missing_day", "wrong_starts", "wrong_progress_head"}:
        days = [json.loads(line) for line in days_path.read_bytes().splitlines()]
        if mutation == "missing_day":
            del days[1]
        elif mutation == "wrong_starts":
            days[1]["starts"]["orders"] += 1
        else:
            days[1]["progress_log_head"] = "f" * 64
        rewrite_chain(days_path, days, daily=True)
    elif mutation in {"wrong_request", "wrong_journal_state", "application_id", "application_time", "fake_duplicate"}:
        rows = events(folder)
        if mutation == "wrong_request":
            rows[0]["request_hash"] = "different-input"
        elif mutation == "wrong_journal_state":
            applied = next(row for row in rows if "journal_entry" in row)
            applied["journal_entry"]["state_hash"] = "f" * 64
        elif mutation == "application_id":
            applied = next(row for row in rows if "journal_entry" in row)
            applied["application"]["event_id"] = "different-event"
        elif mutation == "application_time":
            # Keep the native entry intact, alter both intent/application log
            # clocks. Native replay alone cannot detect this mismatch.
            for row in rows[:2]:
                row["as_of"] = "2018-12-17T08:01:00+08:00"
        else:
            applied = next(row for row in rows if "journal_entry" in row)
            applied["application"]["status"] = "duplicate"
            applied["event"] = applied.pop("journal_entry")["event"]
        rewrite_chain(folder / "account_progress.jsonl", rows)
    elif mutation == "input_bytes":
        with (folder / "account_input.json").open("ab") as stream:
            stream.write(b"\n")
    elif mutation in {"ahead_hint", "wrong_hint_head", "wrong_hint_date"}:
        hint = load(folder / "account_frontier.json")
        if mutation == "ahead_hint":
            hint["complete_days"] += 1
        elif mutation == "wrong_hint_head":
            hint["progress_log_head"] = "e" * 64
        else:
            hint["current_date"] = "2099-01-01"
        legacy._write(folder / "account_frontier.json", hint)
    else:
        result = load(folder / "account_result.json")
        result["native_result_hash"] = "e" * 64
        legacy._write(folder / "account_result.json", result)
    with pytest.raises(ValueError):
        legacy.verify_checkpoint_evidence(folder)


@pytest.mark.parametrize("failure_point", ["partial_commit", "frontier_after_commit", "periodic_before_progress"])
def test_interrupted_commit_authority_ignores_temporary_files_and_partial_days(tmp_path, monkeypatch, failure_point):
    value = short_payload()
    folder = tmp_path / failure_point
    request(folder, value)
    if failure_point == "partial_commit":
        original_append = legacy._CheckpointSink._append_day
        def append_day(self, row):
            if self.day_count == 1:
                self._days.write(b'{"day_sequence":2,"delta":')
                self._days.flush()
                legacy.os.fsync(self._days.fileno())
                raise OSError("interrupted daily commit")
            return original_append(self, row)
        monkeypatch.setattr(legacy._CheckpointSink, "_append_day", append_day)
    elif failure_point == "frontier_after_commit":
        original_write = legacy._write
        def write(path, content, **kwargs):
            if Path(path).name == "account_frontier.json" and content["complete_days"] == 2:
                Path(str(path) + ".tmp").write_text(legacy._serial(content), encoding="utf-8")
                raise OSError("interrupted frontier replacement")
            return original_write(path, content, **kwargs)
        monkeypatch.setattr(legacy, "_write", write)
    else:
        # A complete full anchor persisted before its day_completed log is an
        # uncommitted candidate, never a substitute for the daily commit.
        original_init = legacy._CheckpointSink.__init__
        def init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.checkpoint_interval_days = 2
        monkeypatch.setattr(legacy._CheckpointSink, "__init__", init)
        original_append = legacy._CheckpointSink._append_progress
        def append_progress(self, row):
            if row["phase"] == "day_completed" and row["date"] == value["calendar"][1]:
                self._stream.write(b'{"phase":"day_completed"')
                self._stream.flush()
                legacy.os.fsync(self._stream.fileno())
                raise OSError("interrupted progress append")
            return original_append(self, row)
        monkeypatch.setattr(legacy._CheckpointSink, "_append_progress", append_progress)
    with pytest.raises(legacy.legacy_modules().portfolio.CheckpointPersistenceError, match="interrupted"):
        legacy._worker(folder)
    # Deliberately bogus temp file is never opened by the verifier.
    (folder / "account_checkpoint.json.tmp").write_bytes(b"not valid JSON; not committed")
    verified = legacy.verify_checkpoint_evidence(folder)
    expected = 2 if failure_point == "frontier_after_commit" else 1
    assert verified["complete_days"] == expected
    assert verified["last_complete_day"] == value["calendar"][expected-1]
    assert verified["simulation_completed"] is False
    assert verified["ignored_temporary_files"]
    assert verified["unfinished_current_day"] == (None if expected == 2 else value["calendar"][1])
    if failure_point == "partial_commit":
        assert verified["ignored_unterminated_bytes"]["days"] > 0
        assert verified["uncommitted_events"] > 0
    elif failure_point == "frontier_after_commit":
        assert verified["frontier_hint_stale"] is True
    else:
        assert verified["full_anchor_uncommitted"] is True
        assert verified["ignored_unterminated_bytes"]["progress"] > 0
    assert not (folder / "account_result.json").exists()


def test_dropped_final_newline_is_not_a_committed_event(tmp_path, monkeypatch):
    value = short_payload()
    folder = tmp_path / "event_tail"
    request(folder, value)
    original = legacy._CheckpointSink._append_progress
    def append(self, row):
        if row["phase"] == "event_applied" and row["journal_entry"]["event"]["kind"] == "buy_fill":
            row = {**row, "previous_log_hash": self.previous_log_hash}
            row["record_hash"] = legacy._hash(row)
            self._stream.write(legacy._serial(row).encode("utf-8"))  # Valid JSON, missing commit delimiter.
            self._stream.flush()
            legacy.os.fsync(self._stream.fileno())
            raise OSError("missing final newline")
        return original(self, row)
    monkeypatch.setattr(legacy._CheckpointSink, "_append_progress", append)
    with pytest.raises(legacy.legacy_modules().portfolio.CheckpointPersistenceError):
        legacy._worker(folder)
    verified = legacy.verify_checkpoint_evidence(folder)
    assert verified["complete_days"] == 1
    assert verified["observed_events"] == 1  # deposit only; attempted buy is not durable application evidence
    assert verified["ignored_unterminated_bytes"]["progress"] > 0
    assert verified["simulation_completed"] is False
