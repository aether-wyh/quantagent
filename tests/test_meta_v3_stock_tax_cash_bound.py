"""Full-capital generated cash-protection counterexamples, not tax validation."""
from dataclasses import replace
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

import pytest

from quanta_agents.meta_v3.stock_tax_cash_bound import stock_tax_cash_bound
from quanta_agents.meta_v3.stock_distribution import AdapterError, StockDistributionRightsAdapter as Adapter
from test_meta_v3_stock_distribution import (
    DAYS, SOURCE, SYMBOL, RawShareLedger, apply, at, event, fixture, activated, sell,
)


def prepared(tmp_path, **updates):
    adapter, doc = fixture(tmp_path, **updates)
    ledger = RawShareLedger(DAYS, calendar_source=SOURCE, calendar_available_at=at(DAYS[0], '00:00:00'))
    apply(ledger, event('deposit', 'cash_deposit', DAYS[0], {'amount': '1000000.00'}))
    apply(ledger, event('buy', 'buy_fill', DAYS[1],
        {'symbol': SYMBOL, 'quantity': 1000, 'raw_price': '999.00', 'fees': '0.00'}))
    activated(adapter, ledger)
    apply(ledger, adapter.cash_payment_event(ledger))
    return adapter, ledger, doc


def bound(ledger, adapters):
    return stock_tax_cash_bound(ledger, adapters, as_of=at(DAYS[6], '15:05:00'))


def tax(ledger, amount, *, final=False, paid=False):
    apply(ledger, event('generated-tax', 'tax_assessed', DAYS[6],
        {'action_id': 'generated-mixed', 'total_tax_due': amount, 'tax_final': final}, '15:05:00'))
    if paid:
        apply(ledger, event('generated-tax-cash', 'tax_paid', DAYS[6],
            {'action_id': 'generated-mixed', 'amount': amount}, '15:05:00'))


def test_paid_tax_reduces_cash_and_reserve_equally_without_unlocking_money(tmp_path):
    adapter, ledger, _ = prepared(tmp_path)
    before = bound(ledger, [adapter])
    assert before['cash_available'] == '1100.00'
    assert before['total_stock_tax_cash_reserve'] == '60.00'
    assert before['spendable_cash_after_all_tax_reserves'] == '1040.00'
    tax(ledger, '10.00', paid=True)
    after = bound(ledger, [adapter])
    assert after['cash_available'] == '1090.00'
    assert after['total_stock_tax_cash_reserve'] == '50.00'
    assert after['spendable_cash_after_all_tax_reserves'] == '1040.00'
    assert ledger.snapshot()['external_cash_flow'] == '1000000.00'
    assert after['net_asset_value'] is None and not after['research_execution_ready']


def test_unverified_final_zero_tax_cannot_release_registered_liability(tmp_path):
    adapter, ledger, _ = prepared(tmp_path)
    tax(ledger, '0.00', final=True)
    assert bound(ledger, [adapter])['total_stock_tax_cash_reserve'] == '60.00'


def test_pending_only_and_selling_every_new_share_do_not_erase_tax_bound(tmp_path):
    adapter, ledger, _ = prepared(tmp_path)
    # Cash has arrived; listing remains pending at09:30 on this generated day.
    sell(ledger, 1000, DAYS[6], 'old-sale', '0.00')
    assert bound(ledger, [adapter])['total_stock_tax_cash_reserve'] == '60.00'
    apply(ledger, adapter.listing_event(ledger))
    sell(ledger, 600, DAYS[6], 'new-sale', '0.00')
    assert bound(ledger, [adapter])['total_stock_tax_cash_reserve'] == '60.00'


def test_cash_and_bonus_rounding_cannot_cancel_half_cents(tmp_path):
    adapter, ledger, _ = prepared(tmp_path, gross_cash_per_share='0.025', bonus_per_share='0.025',
                                     capitalization_per_share='0', capitalization_source='none')
    r = bound(ledger, [adapter])
    # A per-share disposal has0.005cash tax and0.005bonus tax. Separate
    # half-up yields0.02, exceeding the0.01ceiling of their combined amount.
    assert D('0.005').quantize(D('.01'), rounding=ROUND_HALF_UP) * 2 == D('.02')
    assert r['total_stock_tax_cash_reserve'] == '20.00'
    assert r['actions'][0]['cash_tax_per_original_share_ceiling'] == '0.01'
    assert r['actions'][0]['bonus_tax_per_original_share_ceiling'] == '0.01'


def test_bound_covers_different_integer_tax_lot_partitions_and_rates(tmp_path):
    adapter, ledger, _ = prepared(tmp_path, gross_cash_per_share='0.097')
    r = bound(ledger, [adapter]);ceiling=D(r['total_stock_tax_cash_reserve'])
    assert ceiling == D('60')  # unrounded whole-action maximum is59.40
    for partition in ([1000], [1]*1000, [333,333,334], [997,1,1,1]):
        assert sum(partition)==1000
        for rate in (D('0'),D('.10'),D('.20')):
            exact=sum(((D(q)*D('.097')*rate).quantize(D('.01'),rounding=ROUND_HALF_UP)
                       +(D(q)*D('.2')*rate).quantize(D('.01'),rounding=ROUND_HALF_UP) for q in partition),D('0'))
            assert exact <= ceiling


def test_shortfall_does_not_create_cash_or_spend_receivables(tmp_path):
    adapter, ledger, _ = prepared(tmp_path, bonus_per_share='8', capitalization_per_share='0', capitalization_source='none')
    r=bound(ledger,[adapter])
    assert r['cash_available']=='1100.00'
    assert r['total_stock_tax_cash_reserve']=='1620.00'
    assert r['cash_shortfall_to_stock_tax_bound']=='520.00'
    assert r['spendable_cash_after_all_tax_reserves']=='0.00'
    assert ledger.snapshot()['cash']=='1100.00'


def test_missing_or_duplicate_stock_adapter_rejected(tmp_path):
    adapter, ledger, _ = prepared(tmp_path)
    with pytest.raises(AdapterError,match='uncovered'):
        bound(ledger,[])
    with pytest.raises(AdapterError,match='duplicate'):
        bound(ledger,[adapter,adapter])


def test_cash_only_obligation_stays_uncovered_never_zero_by_omission(tmp_path):
    adapter, doc=fixture(tmp_path)
    ledger=RawShareLedger(DAYS,calendar_source=SOURCE,calendar_available_at=at(DAYS[0],'00:00:00'))
    apply(ledger,event('deposit','cash_deposit',DAYS[0],{'amount':'1000000.00'}))
    apply(ledger,event('buy','buy_fill',DAYS[1],{'symbol':SYMBOL,'quantity':1000,'raw_price':'999.00','fees':'0.00'}))
    apply(ledger,adapter.record_event(ledger))
    apply(ledger,event('other-record','record_entitlement',DAYS[4],
        {'action_id':'other-cash','symbol':SYMBOL,'entitled_shares':1000},'15:00:00'))
    apply(ledger,adapter.activation_event(ledger))
    apply(ledger,event('other-activate','activate_entitlement',DAYS[5],
        {'action_id':'other-cash','cash_gross_due':'50.00','tax_due':None,'tax_final':False,
         'bonus_shares':0,'share_kind':'none'},'08:00:00'))
    apply(ledger,adapter.cash_payment_event(ledger))
    r=bound(ledger,[adapter])
    assert r['uncovered_other_active_tax_actions']==['other-cash']
    assert r['spendable_cash_after_all_tax_reserves'] is None
    assert r['total_stock_tax_cash_reserve']=='60.00'


def test_paid_amount_above_bound_rejects_instead_of_releasing_cash(tmp_path):
    adapter, ledger, _=prepared(tmp_path)
    tax(ledger,'61.00',paid=True)
    with pytest.raises(AdapterError,match='contradicts'):
        bound(ledger,[adapter])


def test_mismatched_notice_cannot_reduce_existing_tax_reserve(tmp_path):
    adapter,ledger,doc=prepared(tmp_path)
    changed=Adapter(replace(adapter.spec,gross_cash_per_share='0.01'),DAYS,source_document=doc)
    with pytest.raises(AdapterError,match='disagrees'):
        bound(ledger,[changed])


def test_saved_replay_has_identical_cash_bound_and_no_new_payment(tmp_path):
    adapter,ledger,_=prepared(tmp_path)
    tax(ledger,'10.00',paid=True)
    expected=bound(ledger,[adapter]);head=ledger.snapshot()['journal_head']
    recovered=RawShareLedger.replay(ledger.genesis,ledger.journal)
    assert bound(recovered,[adapter])==expected
    assert recovered.snapshot()['journal_head']==head
    assert len([x for x in recovered.journal if x['event']['kind']=='tax_paid'])==1
