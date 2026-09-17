from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.l2_cash_account import L2CashAccount
from test_meta_v3_l2_cash_account import plan, order, quote

CA=module('corporate_action_adapter')


def dynamic_plan():
    p=plan()
    p['corporate_announcements']=[{
        'action_id':'cash-fixture','symbol':'600006.SH','announcement_date':'2026-01-06',
        'record_date':'2026-01-07','ex_date':'2026-01-08','cash_payment_date':'2026-01-08',
        'gross_cash_per_share':'0.145','short_holding_tax_rate':'0.20',
        'tax_rule':CA.SUPPORTED_TAX_RULE,'account_type':CA.ACCOUNT_TYPE,
        'stock_distribution_per_share':'0','stock_distribution_kind':'none','rights_issue':False,
        'implementation_status':'implementation_notice','source_url':'fixture://cash-only-notice',
        'source_sha256':'a'*64,'source_fetched_at':'2026-01-06T20:00:00+08:00','facts_verified':True}]
    p['corporate_policy']={'rounding_policy':'aggregate_half_up_simulated',
        'boundary_policy':'calendar_clamp_simulated','cash_reserve':'maximum_registered_tax_until_final'}
    return p


def test_actual_filled_lots_drive_rights_partial_disposals_and_payment(tmp_path):
    path=tmp_path/'dynamic.sqlite';a=L2CashAccount(path,dynamic_plan())
    assert a.submit(order('buy'),quote())['filled_quantity']==400
    a.submit(order('sell_half','2026-01-08','sell',200),quote('2026-01-08'))
    state=a.advance('2026-01-08T15:05:00+08:00')
    right=state['actions']['cash-fixture']
    assert right['entitled_shares']==400 and len(right['registered_lots'])==2
    assert right['cash_gross_due']=='58.00' and not right['cash_paid']
    assert right['tax_due']=='5.80' and not right['tax_final']
    assert str(a._tax_reserve_for(a.ledger))=='11.60'
    assert state['cash']=='97984.34'
    a.close();a=L2CashAccount(path)
    paid=a.advance('2026-01-09T08:00:00+08:00')
    assert paid['cash']=='98036.54' and paid['actions']['cash-fixture']['tax_paid']=='5.80'
    assert a.advance('2026-01-09T08:00:00+08:00')['events_applied']==0
    assert str(a._tax_reserve_for(a.ledger))=='5.80'
    a.submit(order('sell_rest','2026-01-09','sell',200),quote('2026-01-09'))
    final=a.advance('2026-01-09T15:05:00+08:00')
    right=final['actions']['cash-fixture']
    assert right['entitled_shares']==400 and right['tax_due']==right['tax_paid']=='11.60'
    assert right['tax_final'] and final['cash']=='100022.42'
    assert final['external_cash_flow']=='100000.00' and not a._held()
    assert final['portfolio_pnl'] is None and not final['formal_target_success']
    a.close();b=L2CashAccount(path)
    assert b.snapshot()['cash']=='100022.42' and b.ledger.verify_state_commitment()


@pytest.mark.parametrize('phase',['corporate_before_receipt','before_commit','after_commit'])
def test_corporate_stage_transaction_recovery_has_one_entitlement(tmp_path,phase):
    path=tmp_path/'interrupt.sqlite';a=L2CashAccount(path,dynamic_plan())
    a.submit(order('buy'),quote())
    def crash(here):
        if here==phase:raise RuntimeError('simulated interruption')
    with pytest.raises(RuntimeError):a.advance('2026-01-07T15:00:00+08:00',fault=crash)
    a.close();b=L2CashAccount(path)
    before=b.snapshot()
    assert len(before['actions'])==(1 if phase=='after_commit' else 0)
    b.advance('2026-01-07T15:00:00+08:00')
    assert b.snapshot()['actions']['cash-fixture']['entitled_shares']==400
    assert b.db.execute('SELECT count(*) FROM corporate_stages').fetchone()[0]==1
    assert sum(e['event']['kind']=='record_entitlement' for e in b.ledger.journal)==1


def test_empty_registration_is_final_and_late_orders_cannot_change_it(tmp_path):
    a=L2CashAccount(tmp_path/'empty.sqlite',dynamic_plan())
    a.advance('2026-01-07T15:00:00+08:00')
    r=a.submit(order('late'),quote())
    assert r['status']=='rejected_order' and 'completed corporate stage' in r['reason']
    assert a.submit(order('new','2026-01-08'),quote('2026-01-08'))['filled_quantity']==400
    a.advance('2026-01-09T15:05:00+08:00')
    assert a.snapshot()['actions']=={} and a.snapshot()['cash']=='95992.66'
    rows=[json.loads(x[0]) for x in a.db.execute('SELECT payload FROM corporate_stages')]
    assert rows[0]['skipped']=='no_shares_at_registration'
    assert all(not x['event_ids'] for x in rows)


def test_unpaid_rights_keep_exposure_after_all_shares_sold(tmp_path):
    p=dynamic_plan()
    for row in p['obligations']:
        if row['date']=='2026-01-09' and row['kind']=='corporate_actions':row['status']='unknown'
    a=L2CashAccount(tmp_path/'rights.sqlite',p)
    a.submit(order('buy'),quote());a.submit(order('exit','2026-01-08','sell',400),quote('2026-01-08'))
    assert not a._held() and a._exposed()=={'600006.SH'}
    # Even if today's known payment settles the last right, that day was
    # actually exposed and its unresolved source coverage cannot disappear.
    result=a.submit(order('after_payment','2026-01-09'),quote('2026-01-09'))
    assert result['status']=='halted_account' and a.snapshot()['actions']['cash-fixture']['cash_paid']
    assert a.snapshot()['cash']=='100025.72'
    # Inspect the same covered execution time before payment, with the next
    # day's source gap made visible for an already registered economic right.
    p2=deepcopy(p);p2['corporate_announcements'][0]['cash_payment_date']='2026-01-09'
    p2['calendar'].append('2026-01-12')
    p2['obligations'] += [{**x,'date':'2026-01-12','status':'fixture_complete'}
                         for x in p['obligations'] if x['date']=='2026-01-08']
    b=L2CashAccount(tmp_path/'later_payment.sqlite',p2)
    b.submit(order('buy'),quote());b.submit(order('exit','2026-01-08','sell',400),quote('2026-01-08'))
    result=b.submit(order('next','2026-01-09'),quote('2026-01-09'))
    assert result['status']=='halted_account' and not b._held()
    assert b.snapshot()['actions']['cash-fixture']['cash_gross_due']=='58.00'
    assert not b.snapshot()['actions']['cash-fixture']['cash_paid']


def test_unsupported_stock_component_and_duplicate_event_are_not_dropped(tmp_path):
    p=dynamic_plan();p['corporate_announcements'][0]['stock_distribution_kind']='bonus'
    with pytest.raises(CA.UnsupportedCorporateAction):L2CashAccount(tmp_path/'unsupported.sqlite',p)
    assert not (tmp_path/'unsupported.sqlite').exists()
    p=dynamic_plan();p['corporate_announcements'].append(deepcopy(p['corporate_announcements'][0]))
    with pytest.raises(ValueError,match='duplicate economic action'):L2CashAccount(tmp_path/'duplicate.sqlite',p)
