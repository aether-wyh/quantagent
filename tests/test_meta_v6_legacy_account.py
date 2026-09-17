"""Generated accounting/performance fixtures; no model or historical study runs."""
from copy import deepcopy
from datetime import date, timedelta
import json
from time import perf_counter
from types import SimpleNamespace

import pandas as pd
import pytest

from quanta_agents.meta_v6.legacy_account import (
    _hash, legacy_modules, run_legacy_account, simulate_legacy_account, source_manifest,
)


def announcement(symbol="sz000001", *, action_id="fixture-cash", record="2018-12-25", ex="2018-12-26"):
    module = legacy_modules(optimized=False).adapter
    return dict(action_id=action_id, symbol=symbol, announcement_date="2018-12-17",
                record_date=record, ex_date=ex, cash_payment_date=ex,
                gross_cash_per_share="0.145", short_holding_tax_rate="0.20",
                tax_rule=module.SUPPORTED_TAX_RULE, account_type=module.ACCOUNT_TYPE,
                stock_distribution_per_share="0", stock_distribution_kind="none", rights_issue=False,
                implementation_status="implementation_notice", source_url="https://example.org/fixture.pdf",
                source_sha256="a" * 64, source_fetched_at="2026-09-05T00:00:00+00:00", facts_verified=True)


def generated_payload(*, second_action=True):
    # Synthetic weekdays including Jan 1; deliberately not an exchange calendar.
    days = pd.bdate_range("2018-12-17", "2019-01-11").strftime("%Y-%m-%d").tolist()
    rows = [{"date": day, "code": symbol, "raw_open": "10.00", "raw_close": "10.00",
             "raw_prev_close": "10.00", "raw_high": "10.00", "raw_low": "10.00",
             "volume": 1000000, "amount": 10000000, "stock_name": "合成测试公司", "accepted": True}
            for day in days for symbol in ("sz000001", "sh600006")]
    targets = [{"symbol": symbol, "signal_date": days[index - 1], "trade_date": day,
                "available_at": day + "T09:00:00+08:00",
                "target_weight": ("0.30" if index % 2 else "0.15") if symbol == "sz000001" else "0.20"}
               for index, day in enumerate(days) if index
               for symbol in ("sz000001", "sh600006")]
    actions = [announcement()]
    if second_action:
        actions.append(announcement("sh600006", action_id="second-cash", record="2019-01-03", ex="2019-01-04"))
    return dict(daily_data=rows, calendar=days, targets=targets, initial_cash="100000",
                corporate_actions=actions, allow_incomplete_for_integration=True, slippage_fraction="0")


@pytest.mark.parametrize("second_action", [False, True])
def test_native_account_all_fields_and_record_hashes_equal_across_year_boundary(second_action, record_property):
    payload = generated_payload(second_action=second_action)
    payload["daily_data"] = pd.DataFrame(payload["daily_data"])
    payload["targets"] = pd.DataFrame(payload["targets"])
    before = source_manifest()
    started = perf_counter()
    original = simulate_legacy_account(optimized=False, **payload)
    original_seconds = perf_counter() - started
    started = perf_counter()
    optimized = simulate_legacy_account(optimized=True, **payload)
    optimized_seconds = perf_counter() - started
    assert optimized == original
    assert source_manifest() == before
    assert len(original["daily"]) == len(payload["calendar"])
    assert original["daily"][0]["date"].startswith("2018")
    assert original["daily"][-1]["date"].startswith("2019")
    assert any(row["event"]["kind"] == "tax_assessed" for row in original["journal"])
    assert original["execution_valid"] is False
    assert legacy_modules().ledger.RawShareLedger.replay(original["genesis"], original["journal"]).snapshot() == original["final_snapshot"]
    record_property("synthetic_original_seconds", original_seconds)
    record_property("synthetic_optimized_seconds", optimized_seconds)
    record_property("native_output_hash", _hash(original))


def test_private_namespaces_do_not_modify_original_adapter():
    original = legacy_modules(optimized=False)
    method = original.adapter.CashDividendAdapter.validate_eod_integrity
    optimized = legacy_modules()
    assert original.adapter is not optimized.adapter
    assert original.ledger is not optimized.ledger
    assert original.adapter.CashDividendAdapter.validate_eod_integrity is method
    assert optimized.adapter.CashDividendAdapter.validate_eod_integrity is not method
    assert optimized.portfolio.CashDividendAdapter is optimized.adapter.CashDividendAdapter
    assert original.portfolio.CashDividendAdapter is original.adapter.CashDividendAdapter


class CountingLedger:
    def __init__(self, events):
        self.entries = [{"event": event} for event in events]
        self.reads = 0

    @property
    def journal(self):
        self.reads += 1
        return deepcopy(self.entries)


def integrity_fixture(module, *, count=120, nonmonotone=False):
    adapter = module.CashDividendAdapter.__new__(module.CashDividendAdapter)
    adapter._spec = SimpleNamespace(action_id="fixture", symbol="sz000001")
    dates = [(date(2019, 1, 1) + timedelta(days=index)).isoformat() for index in range(count)]
    trades = [dict(kind="buy_fill", event_id="trade-" + str(index), effective_at=day + "T09:30:00+08:00",
                   data={"symbol": "sz000001", "quantity": 100, "raw_price": "10.00", "fees": "5.00"},
                   source={"label": "合成unicode", "tags": [True, None, {"fraction": "0.1"}]})
              for index, day in enumerate(dates)]
    if nonmonotone:
        trades = trades[::2] + trades[1::2]
    finalized = [dict(kind="tax_assessed", event_id="fixture:tax-eod-" + day + "-" + module._hash(
        [trade for trade in trades if trade["effective_at"][:10] <= day])) for day in dates]
    return adapter, CountingLedger(trades + finalized)


def test_one_snapshot_prefix_hashes_replace_repeated_full_copies(record_property):
    old, new = legacy_modules(optimized=False).adapter, legacy_modules().adapter
    old_adapter, old_ledger = integrity_fixture(old, count=487)
    new_adapter, new_ledger = integrity_fixture(new, count=487)
    started = perf_counter()
    old_adapter.validate_eod_integrity(old_ledger)
    old_seconds = perf_counter() - started
    started = perf_counter()
    new_adapter.validate_eod_integrity(new_ledger)
    new_seconds = perf_counter() - started
    assert old_ledger.reads == 488
    assert new_ledger.reads == 1
    record_property("synthetic_tax_days", 487)
    record_property("old_journal_deepcopies", old_ledger.reads)
    record_property("new_journal_deepcopies", new_ledger.reads)
    record_property("old_integrity_seconds", old_seconds)
    record_property("new_integrity_seconds", new_seconds)


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("mutation", ["historical_price", "late_fill", "malformed_identity"])
def test_every_call_redetects_historical_or_late_mutations(optimized, mutation):
    module = legacy_modules(optimized=optimized).adapter
    adapter, ledger = integrity_fixture(module, count=5)
    adapter.validate_eod_integrity(ledger)
    if mutation == "historical_price":
        ledger.entries[0]["event"]["data"]["raw_price"] = "9.99"
    elif mutation == "late_fill":
        event = deepcopy(ledger.entries[0]["event"])
        event["event_id"] = "later-filled-after-close"
        event["effective_at"] = event["effective_at"].replace("09:30:00", "15:06:00")
        ledger.entries.append({"event": event})
    else:
        ledger.entries[-1]["event"]["event_id"] = "fixture:tax-eod-malformed"
    with pytest.raises(module.AdapterError, match="post-finalization|malformed"):
        adapter.validate_eod_integrity(ledger)


def test_nonmonotone_snapshot_keeps_original_filter_order_and_still_rejects_edit():
    for optimized in (False, True):
        module = legacy_modules(optimized=optimized).adapter
        adapter, ledger = integrity_fixture(module, count=8, nonmonotone=True)
        adapter.validate_eod_integrity(ledger)
        if optimized:
            assert ledger.reads == 1
        ledger.entries[1]["event"]["data"]["quantity"] += 100
        with pytest.raises(module.AdapterError, match="post-finalization"):
            adapter.validate_eod_integrity(ledger)


@pytest.mark.parametrize("optimized", [False, True])
def test_actual_ledger_accepts_late_fill_but_adapter_blocks_closed_day(optimized):
    modules = legacy_modules(optimized=optimized)
    module = modules.adapter
    days = pd.bdate_range("2018-12-17", "2019-01-11").strftime("%Y-%m-%d").tolist()
    source = {"ref": "synthetic://fixture", "sha256": "a" * 64, "verified": True,
              "evidence_type": "simulated", "assumption_ref": "synthetic://calendar-v1",
              "assumption_sha256": "b" * 64}
    ledger = modules.ledger.RawShareLedger(days, calendar_source=source,
                                          calendar_available_at="2018-01-01T00:00:00+08:00")
    adapter = module.CashDividendAdapter(module.CashDividendAnnouncement(**announcement()), days)

    def push(event_id, kind, when, data):
        ledger.apply(dict(event_id=event_id, kind=kind, effective_at=when, available_at=when,
                          source=source, data=data), as_of=when)

    push("capital", "cash_deposit", "2018-12-17T08:00:00+08:00", {"amount": "10000"})
    buy = {"symbol": "sz000001", "quantity": 100, "raw_price": "10.00", "fees": "0.00"}
    push("buy", "buy_fill", "2018-12-24T09:30:00+08:00", buy)
    for event in (adapter.record_event(ledger),):
        ledger.apply(event, as_of=event["available_at"])
    event = adapter.activation_event(ledger)
    ledger.apply(event, as_of=event["available_at"])
    event = adapter.tax_assessment_event(ledger, as_of="2018-12-26T15:05:00+08:00")
    ledger.apply(event, as_of=event["available_at"])
    adapter.validate_eod_integrity(ledger)
    push("late-buy", "buy_fill", "2018-12-26T15:06:00+08:00", buy)
    with pytest.raises(module.AdapterError, match="post-finalization"):
        adapter.tax_evidence(ledger, as_of="2018-12-26T15:07:00+08:00")


def test_supervised_new_generated_account_retains_native_result_and_checkpoint(tmp_path):
    payload = generated_payload(second_action=False)
    # Keep subprocess fixture small; no dividends activate in its five sessions.
    payload["calendar"] = payload["calendar"][:5]
    payload["daily_data"] = [row for row in payload["daily_data"] if row["date"] in payload["calendar"]]
    payload["targets"] = [row for row in payload["targets"] if row["trade_date"] in payload["calendar"]]
    payload["corporate_actions"] = []
    result = run_legacy_account(payload, output_dir=tmp_path / "job", timeout_seconds=30)
    assert result["status"] == "completed"
    account = json.loads((tmp_path / "job/account_result.json").read_text(encoding="utf-8"))
    checkpoint = json.loads((tmp_path / "job/account_checkpoint.json").read_text(encoding="utf-8"))
    assert account["native_result_hash"] == _hash(account["native_result"])
    assert account["source_manifest"] == source_manifest()
    assert account["native_result"]["execution_valid"] is False
    assert checkpoint["sequence"] > 0
    assert checkpoint["financial_validation_claimed"] is False
    assert checkpoint["request_hash"] == account["request_hash"]
