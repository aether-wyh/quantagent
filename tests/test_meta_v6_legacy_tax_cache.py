"""Synthetic immutable operation snapshots and exact historical tax boundaries."""
from datetime import date

import pandas as pd
import pytest

from quanta_agents.meta_v6 import legacy_account as legacy
from quanta_agents.meta_v6 import legacy_tax_cache as cache


def account(optimized=True, *, finalized=True):
    modules = legacy.legacy_modules(optimized=optimized)
    source = {"ref": "synthetic://history-cache", "sha256": "a"*64, "verified": True,
              "evidence_type": "simulated", "assumption_ref": "synthetic://calendar", "assumption_sha256": "b"*64}
    days = pd.bdate_range("2018-12-17", periods=100).strftime("%Y-%m-%d").tolist()
    class CountingLedger(modules.ledger.RawShareLedger):
        journal_reads = snapshot_reads = 0
        @property
        def journal(self):
            self.journal_reads += 1
            return super().journal
        def snapshot(self):
            self.snapshot_reads += 1
            return super().snapshot()
    ledger = CountingLedger(days, calendar_source=source, calendar_available_at=days[0]+"T00:00:00+08:00")
    announcement = modules.adapter.CashDividendAnnouncement(action_id="synthetic-action", symbol="sz000001",
        announcement_date=days[0], record_date="2018-12-25", ex_date="2018-12-26", cash_payment_date="2018-12-26",
        gross_cash_per_share="0.145", short_holding_tax_rate="0.20", tax_rule=modules.adapter.SUPPORTED_TAX_RULE,
        account_type=modules.adapter.ACCOUNT_TYPE, stock_distribution_per_share="0", stock_distribution_kind="none",
        rights_issue=False, implementation_status="implementation_notice", source_url="https://example.org/synthetic",
        source_sha256="a"*64, source_fetched_at="2026-09-09T00:00:00+00:00", facts_verified=True)
    adapter = modules.adapter.CashDividendAdapter(announcement, days)
    def push(identity, kind, when, data):
        ledger.apply(dict(event_id=identity, kind=kind, effective_at=when, available_at=when, source=source, data=data), as_of=when)
    push("capital", "cash_deposit", days[0]+"T08:00:00+08:00", {"amount": "100000"})
    push("buy", "buy_fill", days[1]+"T09:30:00+08:00", {"symbol":"sz000001", "quantity":1000, "raw_price":"10.00", "fees":"0.00"})
    for event in (adapter.record_event(ledger),):
        ledger.apply(event, as_of=event["available_at"])
    event = adapter.activation_event(ledger)
    ledger.apply(event, as_of=event["available_at"])
    if finalized:
        event = adapter.tax_assessment_event(ledger, as_of="2018-12-26T15:05:00+08:00")
        ledger.apply(event, as_of=event["available_at"])
    return modules, ledger, adapter, days, push


def test_one_capture_per_outer_operation_and_fresh_next_operation():
    _, ledger, adapter, _, _ = account()
    ledger.journal_reads = ledger.snapshot_reads = 0
    first = adapter.tax_reserve(ledger, as_of="2018-12-26T15:05:00+08:00")
    assert ledger.journal_reads == ledger.snapshot_reads == 1
    first["realized_evidence"]["daily_net_changes"].clear()
    second = adapter.tax_reserve(ledger, as_of="2018-12-26T15:05:00+08:00")
    assert ledger.journal_reads == ledger.snapshot_reads == 2
    assert second["realized_evidence"]["daily_net_changes"]
    assert adapter._v4_history_stats["hits"] > 0


def test_historical_through_inventory_is_not_current_inventory_and_brackets_are_exact():
    results = {}
    for optimized in (False, True):
        modules, ledger, adapter, days, push = account(optimized)
        through = date(2018, 12, 26)
        before = adapter._tax_history(ledger, through)
        push("later-sale", "sell_fill", days[20]+"T09:30:00+08:00", {
            "symbol":"sz000001", "quantity":400, "raw_price":"10.00", "fees":"0.00", "lot_allocations":{"buy":400}})
        prior = adapter._tax_history(ledger, through)
        present = adapter._tax_history(ledger, date.fromisoformat(days[20]))
        assert before == prior
        assert sum(prior["remaining"].values()) == 1000
        assert sum(present["remaining"].values()) == 600
        assert sum(lot["quantity"] for lot in ledger.snapshot()["lots"].values()) == 600
        with pytest.raises(modules.adapter.AdapterError, match="earlier stage"):
            adapter.tax_evidence(ledger, as_of="2018-12-26T15:05:00+08:00")
        evidence = adapter.tax_evidence(ledger, as_of=days[20]+"T15:05:00+08:00")
        reserves = [adapter.tax_reserve(ledger, as_of=days[i]+"T15:05:00+08:00") for i in (20, 25, 40, 80)]
        assert len({r["remaining_tax_reserve"] for r in reserves}) > 1
        results[optimized] = dict(before=before, prior=prior, present=present, evidence=evidence, reserves=reserves)
    assert results[False] == results[True]


@pytest.mark.parametrize("optimized", [False, True])
def test_private_historical_edit_with_unchanged_head_is_rechecked_after_cache_warmup(optimized):
    modules, ledger, adapter, _, _ = account(optimized)
    adapter._tax_history(ledger, date(2018, 12, 26))
    before_head = ledger._previous_hash
    ledger._journal[1]["event"]["data"]["raw_price"] = "9.99"
    assert ledger._previous_hash == before_head
    with pytest.raises(modules.adapter.AdapterError, match="post-finalization"):
        adapter._tax_history(ledger, date(2018, 12, 26))


def test_unfinalized_history_content_edit_changes_cache_key_instead_of_reusing_head():
    _, ledger, adapter, _, _ = account(finalized=False)
    before = adapter._tax_history(ledger, date(2018, 12, 26))
    head = ledger._previous_hash
    ledger._journal[1]["event"]["data"]["quantity"] = 900
    after = adapter._tax_history(ledger, date(2018, 12, 26))
    assert ledger._previous_hash == head
    assert sum(before["registered"].values()) == 1000
    assert sum(after["registered"].values()) == 900
    assert adapter._v4_history_stats["misses"] == 2


def test_cache_hit_still_checks_current_unsupported_bonus_lineage():
    modules, ledger, adapter, _, _ = account()
    adapter._tax_history(ledger, date(2018, 12, 26))
    ledger._state["actions"]["synthetic-action"]["bonus_entitled"] = 100
    with pytest.raises(modules.adapter.UnsupportedCorporateAction, match="lineage"):
        adapter._tax_history(ledger, date(2018, 12, 26))


def test_cache_is_bounded_and_returned_history_cannot_poison_it():
    _, ledger, adapter, days, _ = account()
    for day in days[7:27]:
        history = adapter._tax_history(ledger, date.fromisoformat(day))
        history["registered"].clear()
    assert len(adapter._v4_history_cache) <= cache.HISTORY_CACHE_ENTRIES
    assert adapter._v4_history_bytes <= cache.HISTORY_CACHE_BYTES
    again = adapter._tax_history(ledger, date.fromisoformat(days[26]))
    assert sum(again["registered"].values()) == 1000
    assert all(type(value) is bytes for value in adapter._v4_history_cache.values())


def test_operation_read_view_is_immutable_and_detects_commit_advance(monkeypatch):
    modules, ledger, adapter, _, push = account()
    trades = adapter._trade_events(ledger)
    with pytest.raises(TypeError, match="immutable"):
        trades[0]["data"]["quantity"] = 999
    with pytest.raises(TypeError, match="immutable"):
        trades.append({})
    original = ledger.snapshot
    def advancing_snapshot():
        result = original()
        push("concurrent-deposit", "cash_deposit", "2018-12-26T15:06:00+08:00", {"amount":"1.00"})
        return result
    monkeypatch.setattr(ledger, "snapshot", advancing_snapshot)
    with pytest.raises(modules.adapter.AdapterError, match="advanced during"):
        adapter._tax_history(ledger, date(2018, 12, 26))
