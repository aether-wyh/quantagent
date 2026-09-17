"""Generated million-CNY physical accounts; no strategy or tax-age proof."""
from dataclasses import replace
from decimal import Decimal as D
import hashlib

import pytest

from quanta_agents.meta_v3.stock_distribution import (
    AdapterError, LedgerError, RawShareLedger, StockDistributionAnnouncement as Notice,
    StockDistributionRightsAdapter as Adapter, UnsupportedCorporateAction,
    economic_share_positions, physical_sale_allocations,
)

DAYS = ['2018-05-10', '2018-05-11', '2018-05-14', '2018-05-15',
        '2018-05-16', '2018-05-17', '2018-05-18', '2018-05-21']
SYMBOL = 'sh600064'
SOURCE = {'ref': 'generated-engineering://physical-rights-only', 'sha256': 'a'*64,
          'verified': True, 'evidence_type': 'simulated',
          'assumption_ref': 'generated-full-capital-account', 'assumption_sha256': 'b'*64}


def at(day, clock='09:30:00'):
    return day + 'T' + clock + '+08:00'


def fixture(tmp_path, **updates):
    doc = tmp_path/'generated_fixture.pdf'
    doc.write_bytes(b'%PDF-generated engineering source; no historical verification claim')
    spec = Notice('generated-mixed', SYMBOL, '2018-05-10', '2018-05-16', '2018-05-17',
                  '2018-05-17', '2018-05-18', '0.1', '0.2', '0.4', '1',
                  'share_premium_verified', 'https://example.invalid/generated.pdf',
                  hashlib.sha256(doc.read_bytes()).hexdigest(), '2026-09-07T16:00:00+00:00', True)
    return Adapter(replace(spec, **updates), DAYS, source_document=doc), doc


def apply(ledger, event):
    return ledger.apply(event, as_of=event['available_at'])


def account(quantity=1000):
    ledger = RawShareLedger(DAYS, calendar_source=SOURCE, calendar_available_at=at(DAYS[0], '00:00:00'))
    apply(ledger, event('deposit', 'cash_deposit', DAYS[0], {'amount': '1000000.00'}))
    apply(ledger, event('old-buy', 'buy_fill', DAYS[1],
                       {'symbol': SYMBOL, 'quantity': quantity, 'raw_price': '16.00', 'fees': '5.00'}))
    return ledger


def event(identity, kind, day, data, clock='09:30:00'):
    return {'event_id': identity, 'kind': kind, 'effective_at': at(day, clock),
            'available_at': at(day, clock), 'source': SOURCE, 'data': data}


def activated(adapter, ledger):
    apply(ledger, adapter.record_event(ledger))
    apply(ledger, adapter.activation_event(ledger))


def sell(ledger, quantity, day, identity, fees='15.00'):
    allocation = physical_sale_allocations(ledger, SYMBOL, quantity, as_of=at(day))
    apply(ledger, event(identity, 'sell_fill', day, {'symbol': SYMBOL, 'quantity': quantity,
        'raw_price': '9.90', 'fees': fees, 'lot_allocations': allocation}))


def value(ledger, day, clock='15:05:00'):
    positions = economic_share_positions(ledger.snapshot())
    marks = {symbol: {'raw_price': '9.90', 'effective_at': at(day, clock),
             'available_at': at(day, clock), 'source': SOURCE} for symbol in positions}
    return ledger.valuation(marks, as_of=at(day, clock))


def test_pending_only_after_old_sale_preserves_all_rights_loss_and_cash(tmp_path):
    adapter, _ = fixture(tmp_path)
    ledger = account()
    activated(adapter, ledger)
    assert ledger.sellable_quantity(SYMBOL, as_of=at(DAYS[5])) == 1000
    assert value(ledger, DAYS[5])['gross_asset_value'] == '999935.00'
    sell(ledger, 1000, DAYS[5], 'old-sale')
    assert economic_share_positions(ledger.snapshot()) == {SYMBOL: {'listed': 0, 'pending': 600, 'economic': 600}}
    assert ledger.sellable_quantity(SYMBOL, as_of=at(DAYS[5])) == 0
    before = ledger.snapshot()
    with pytest.raises(AdapterError, match='sellable'):
        physical_sale_allocations(ledger, SYMBOL, 100, as_of=at(DAYS[5]))
    assert ledger.snapshot() == before
    pending = value(ledger, DAYS[5])
    assert pending['cash_available'] == '993880.00'
    assert pending['cash_receivable_gross'] == '100.00'
    assert pending['share_value_including_pending'] == '5940.00'
    assert pending['gross_asset_value'] == '999920.00'
    assert pending['net_asset_value'] is None
    assert pending['unresolved_tax_actions'] == ['generated-mixed']
    # The missing pending-only mark cannot silently erase the remaining rights.
    with pytest.raises(LedgerError):
        ledger.valuation({}, as_of=at(DAYS[5], '15:05:00'))
    apply(ledger, adapter.cash_payment_event(ledger))
    before_listing = value(ledger, DAYS[6], '08:00:00')
    listed = adapter.listing_event(ledger)
    apply(ledger, listed)
    assert value(ledger, DAYS[6])['gross_asset_value'] == before_listing['gross_asset_value']
    assert economic_share_positions(ledger.snapshot())[SYMBOL] == {'listed': 600, 'pending': 0, 'economic': 600}
    assert ledger.snapshot()['lots'][listed['event_id']]['acquired_at'] is None
    sell(ledger, 600, DAYS[6], 'new-sale', '10.00')
    assert ledger.snapshot()['cash'] == '999910.00'
    assert ledger.snapshot()['external_cash_flow'] == '1000000.00'
    assert ledger.snapshot()['fees_paid'] == '30.00'
    assert economic_share_positions(ledger.snapshot()) == {}
    assert value(ledger, DAYS[6])['net_asset_value'] is None
    assert ledger.verify_state_commitment()


def test_taxable_bonus_and_non_taxable_capital_are_distinct_and_not_cash(tmp_path):
    adapter, _ = fixture(tmp_path)
    e = adapter.entitlements(1000)
    assert (e['bonus_shares'], e['capitalization_shares'], e['new_shares']) == (200, 400, 600)
    assert D(e['total_taxable_income_cny_exact']) == D('300')
    assert D(e['maximum_tax_exposure_cny_exact']) == D('60')
    assert e['cash_gross_due'] == '100.00'
    assert e['capitalization_taxable_income_cny_exact'] == '0'
    with pytest.raises(UnsupportedCorporateAction, match='unimplemented'):
        adapter.require_tax_execution_ready()


def test_negative_cash_dividend_tax_exposure_can_exceed_cash_not_clipped(tmp_path):
    adapter, _ = fixture(tmp_path, bonus_per_share='0.8', capitalization_per_share='0', capitalization_source='none')
    e = adapter.entitlements(40000)
    assert e['cash_gross_due'] == '4000.00'
    assert D(e['maximum_tax_exposure_cny_exact']) == D('7200')
    assert D(e['maximum_tax_exposure_cny_exact']) - D(e['cash_gross_due']) == D('3200')
    assert e['maximum_is_exposure_only_not_assessed_or_paid_tax']


@pytest.mark.parametrize('bonus,capital,quantity', [('0.2','0.4',101), ('0.2','0.8',1)])
def test_fractional_components_reject_before_any_record_not_net_or_floor(tmp_path, bonus, capital, quantity):
    adapter, _ = fixture(tmp_path, bonus_per_share=bonus, capitalization_per_share=capital)
    ledger = account(quantity)
    before = ledger.snapshot()
    with pytest.raises(UnsupportedCorporateAction, match='fractional'):
        adapter.record_event(ledger)
    assert ledger.snapshot() == before


def test_total_account_integer_allocation_not_per_purchase_lot_rounding(tmp_path):
    adapter, _ = fixture(tmp_path)
    ledger = account(101)
    apply(ledger, event('second-buy', 'buy_fill', DAYS[2],
        {'symbol': SYMBOL, 'quantity': 99, 'raw_price': '16.00', 'fees': '5.00'}))
    activated(adapter, ledger)
    assert ledger.snapshot()['actions']['generated-mixed']['bonus_pending'] == 120


def test_non_cent_cash_rejects_before_registration(tmp_path):
    adapter, _ = fixture(tmp_path, gross_cash_per_share='0.097')
    ledger = account(105)
    before = ledger.snapshot()
    with pytest.raises(UnsupportedCorporateAction, match='cent'):
        adapter.record_event(ledger)
    assert ledger.snapshot() == before


def test_cash_amount_above_ledger_limit_rejects_before_recording(tmp_path):
    adapter, _ = fixture(tmp_path, gross_cash_per_share='999999999999')
    ledger = account(2000)
    before = ledger.snapshot()
    with pytest.raises(AdapterError, match='raw ledger bounds'):
        adapter.record_event(ledger)
    assert ledger.snapshot() == before


def test_record_day_late_fill_rejected_and_no_activation_mutation(tmp_path):
    adapter, _ = fixture(tmp_path)
    ledger = account()
    apply(ledger, adapter.record_event(ledger))
    apply(ledger, event('late-buy', 'buy_fill', DAYS[4],
        {'symbol': SYMBOL, 'quantity': 100, 'raw_price': '16.00', 'fees': '5.00'}, '15:01:00'))
    before = ledger.snapshot()
    with pytest.raises(AdapterError, match='after registration'):
        adapter.activation_event(ledger)
    assert ledger.snapshot() == before


def test_unsupported_tax_assessment_cannot_be_smuggled_into_rights_stages(tmp_path):
    adapter, _ = fixture(tmp_path)
    ledger = account()
    activated(adapter, ledger)
    apply(ledger, event('invented-zero-tax', 'tax_assessed', DAYS[5],
        {'action_id': adapter.spec.action_id, 'total_tax_due': '0.00', 'tax_final': True}, '15:05:00'))
    with pytest.raises(AdapterError, match='tax mutations'):
        adapter.cash_payment_event(ledger)


def test_saved_event_replay_and_duplicate_listing_without_source_or_adapter(tmp_path, monkeypatch):
    adapter, doc = fixture(tmp_path)
    ledger = account()
    activated(adapter, ledger)
    apply(ledger, adapter.cash_payment_event(ledger))
    listed = adapter.listing_event(ledger)
    apply(ledger, listed)
    # Once receipts exist, recovering the raw ledger must not re-read sources.
    doc.write_bytes(b'changed after saved events; no new admission')
    monkeypatch.setattr(Adapter, '__init__', lambda *a, **k: (_ for _ in ()).throw(AssertionError('adapter reconstruction')))
    recovered = RawShareLedger.replay(ledger.genesis, ledger.journal)
    assert recovered.snapshot() == ledger.snapshot()
    assert apply(recovered, listed)['status'] == 'duplicate'
    assert recovered.snapshot()['actions']['generated-mixed']['bonus_entitled'] == 600


@pytest.mark.parametrize('updates', [
    {'capitalization_source': 'unspecified'}, {'stock_listing_date': '2018-05-16'},
    {'facts_verified': False}, {'rights_issue': True}, {'account_type': 'qfii'},
])
def test_bad_scope_and_dates_rejected(tmp_path, updates):
    with pytest.raises(AdapterError):
        fixture(tmp_path, **updates)


def test_document_drift_and_manifest_mutation_do_not_rebind_policy(tmp_path):
    adapter, doc = fixture(tmp_path)
    manifest = adapter.manifest()
    manifest['announcement']['bonus_per_share'] = '999'
    manifest['calendar'].clear()
    assert adapter.entitlements(1000)['new_shares'] == 600
    assert len(adapter.manifest()['calendar']) == len(DAYS)
    with pytest.raises(AttributeError):
        adapter.spec = replace(adapter.spec, bonus_per_share='999')
    doc.write_bytes(b'%PDF-changed')
    with pytest.raises(AdapterError, match='identity mismatch'):
        Adapter(adapter.spec, DAYS, source_document=doc)


def test_listed_new_shares_and_new_purchase_keep_distinct_sellability(tmp_path):
    adapter, _ = fixture(tmp_path)
    ledger = account()
    activated(adapter, ledger)
    apply(ledger, adapter.cash_payment_event(ledger))
    apply(ledger, adapter.listing_event(ledger))
    apply(ledger, event('listing-day-buy', 'buy_fill', DAYS[6],
        {'symbol': SYMBOL, 'quantity': 100, 'raw_price': '9.90', 'fees': '5.00'}))
    assert ledger.sellable_quantity(SYMBOL, as_of=at(DAYS[6])) == 1600
    allocation = physical_sale_allocations(ledger, SYMBOL, 1600, as_of=at(DAYS[6]))
    assert allocation == {'old-buy': 1000, 'generated-mixed:listed': 600}
    assert 'listing-day-buy' not in allocation


def test_unpaid_cash_does_not_block_listing_and_remains_receivable(tmp_path):
    adapter, _ = fixture(tmp_path, cash_payment_date='2018-05-18')
    ledger = account()
    activated(adapter, ledger)
    apply(ledger, adapter.listing_event(ledger))
    v = value(ledger, DAYS[6])
    assert v['cash_receivable_gross'] == '100.00'
    assert v['cash_available'] == '983995.00'
    apply(ledger, adapter.cash_payment_event(ledger))
    assert ledger.snapshot()['cash'] == '984095.00'
