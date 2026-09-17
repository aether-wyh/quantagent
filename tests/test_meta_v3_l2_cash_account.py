from copy import deepcopy
from decimal import Decimal

import pytest

from quanta_agents.meta_v3.l2_cash_account import L2CashAccount, KINDS


def plan(cash='100000.00'):
    days=['2026-01-07','2026-01-08','2026-01-09']
    return {'mode':'fixture','codes':['600006.SH'],'calendar':days,'initial_time':'2026-01-07T00:00:00+08:00','initial_cash':cash,
        'policy':{'price_scale':10000,'tick_scaled':100,'unit_lot':100,'per_level_displayed_depth_fraction':'0.10',
            'max_execution_snapshot_delay_ms':4000,'decision_local_time':'09:35:00','assumed_order_latency_ms':1000},
        'fees':{'commission_rate':'0.0003','minimum_commission':'5.00','transfer_rate':'0.00001','sell_stamp_rate':'0.0005'},
        'corporate_events':[],
        'obligations':[{'code':'600006.SH','date':d,'kind':k,'status':'fixture_complete','evidence_sha256':'1'*64} for d in days for k in KINDS]}


def order(oid,day='2026-01-07',side='buy',quantity=1000):
    return {'id':oid,'code':'600006.SH','date':day,'side':side,'quantity':quantity,
        'limit_price_scaled':100200 if side=='buy' else 99800,'decision_time':day+'T09:35:00+08:00','arrival_time':day+'T09:35:01+08:00'}


def quote(day='2026-01-07'):
    row={'wind_code':'600006.SH','date':day,'event_ts':day+'T09:35:01+08:00','source_row_no':2,'time_raw':93501000}
    for side in ('ask','bid'):
        for n in range(1,11):
            row[f'{side}_price_{n}_x1e4']=(100000+(n-1)*100 if side=='ask' else 99900-(n-1)*100) if n<=2 else 0
            row[f'{side}_volume_{n}']=(1700 if n==1 else 2700) if n<=2 else 0
    return row


def test_multilevel_minimum_fee_depth_reuse_t1_cash_and_idempotency(tmp_path):
    path=tmp_path/'cash.sqlite';a=L2CashAccount(path,plan())
    bought=a.submit(order('buy'),quote())
    assert bought['filled_quantity']==400 and bought['remaining_quantity']==600
    assert [x['quantity'] for x in bought['allocations']]==[170,230]
    assert bought['fees']=={'commission':'5.00','transfer':'0.04','stamp':'0.00','total':'5.04'}
    assert bought['cash_after']=='95992.66'
    duplicate=a.submit(order('buy'),quote());assert duplicate==bought
    assert a.submit(order('reuse'),quote())['filled_quantity']==0
    blocked=a.submit(order('same_day_sell',side='sell',quantity=400),quote())
    assert blocked['status']=='rejected_order' and 'T+1' in blocked['reason']
    sold=a.submit(order('sell','2026-01-08','sell',400),quote('2026-01-08'))
    assert sold['fees']['total']=='7.04' and sold['notional']=='3993.70'
    assert sold['cash_after']=='99979.32' and sold['holdings_after']=={}
    a.close();recovered=L2CashAccount(path)
    assert recovered.snapshot()['cash']=='99979.32'
    assert recovered.snapshot()['external_cash_flow']=='100000.00'
    assert recovered.ledger.verify_state_commitment()


def test_full_order_cash_reservation_precedes_future_partial_fill_and_unknowns_stop(tmp_path):
    a=L2CashAccount(tmp_path/'short.sqlite',plan('10024.90'))
    r=a.submit(order('insufficient'),quote())
    assert r['status']=='rejected_order' and 'pre-dispatch' in r['reason']
    assert a.snapshot()['cash']=='10024.90' and a.snapshot()['event_count']==1
    simultaneous=L2CashAccount(tmp_path/'simultaneous.sqlite',plan('15000.00'))
    assert simultaneous.submit(order('first'),quote())['filled_quantity']==400
    later=quote();later.update(event_ts='2026-01-07T09:35:02+08:00',time_raw=93502000,source_row_no=3)
    second=simultaneous.submit(order('same_decision'),later)
    assert second['status']=='rejected_order' and 'pre-dispatch' in second['reason']
    assert simultaneous.snapshot()['cash']=='10992.66'
    p=plan()
    for x in p['obligations']:
        if x['date']=='2026-01-08' and x['kind']=='corporate_actions':x['status']='unknown'
    b=L2CashAccount(tmp_path/'unknown.sqlite',p);b.submit(order('buy'),quote())
    before=b.snapshot()
    r=b.submit(order('next','2026-01-08','sell',400),quote('2026-01-08'))
    assert r['status']=='halted_account' and r['holdings_after']=={'600006.SH':400}
    assert b.snapshot()['cash']==before['cash'] and b.snapshot()['lots']==before['lots']
    assert b.snapshot()['portfolio_pnl'] is None


@pytest.mark.parametrize('phase',['before_commit','after_commit'])
def test_crash_commit_boundary_never_rematches_or_double_debits(tmp_path,phase):
    path=tmp_path/'crash.sqlite';a=L2CashAccount(path,plan())
    def crash(here):
        if here==phase:raise RuntimeError('simulated process interruption')
    with pytest.raises(RuntimeError):a.submit(order('once'),quote(),fault=crash)
    a.close();b=L2CashAccount(path)
    saved=b.submit(order('once'),quote())
    if phase=='before_commit':
        assert saved['status']=='pending_recovery_required'
        assert b.snapshot()['cash']=='100000.00' and b.snapshot()['event_count']==1
        with pytest.raises(ValueError,match='unresolved prior intent'):b.submit(order('new'),quote())
    else:
        assert saved['filled_quantity']==400 and b.snapshot()['cash']=='95992.66'
        assert b.snapshot()['event_count']==3 and b.snapshot()['pending_orders']==0


def test_known_entitlement_survives_sale_and_rejected_order_until_payment(tmp_path):
    p=plan();source={'ref':'fixture-events','sha256':'2'*64,'verified':True,'evidence_type':'simulated',
        'assumption_ref':'frozen-fixture','assumption_sha256':'3'*64}
    def event(name,kind,clock,data):return {'event_id':'action:'+name,'kind':kind,'effective_at':clock,'available_at':clock,'source':source,'data':data}
    p['corporate_events']=[
        event('record','record_entitlement','2026-01-07T15:00:00+08:00',{'action_id':'div','symbol':'600006.SH','entitled_shares':400}),
        event('activate','activate_entitlement','2026-01-08T08:00:00+08:00',{'action_id':'div','cash_gross_due':'68.00','tax_due':'0.00','tax_final':True,'bonus_shares':0,'share_kind':'none'}),
        event('pay','cash_dividend_paid','2026-01-09T09:00:00+08:00',{'action_id':'div','gross_amount':'68.00','net_cash_credit':'68.00','tax_withheld':'0.00'})]
    a=L2CashAccount(tmp_path/'actions.sqlite',p);a.submit(order('buy'),quote())
    rejected=a.submit(order('too_many','2026-01-08','sell',500),quote('2026-01-08'))
    assert rejected['status']=='rejected_order'
    assert a.snapshot()['actions']['div']['cash_gross_due']=='68.00'
    a.submit(order('sell','2026-01-08','sell',400),quote('2026-01-08'))
    assert a.snapshot()['actions']['div']['entitled_shares']==400
    before=Decimal(a.snapshot()['cash']);a.advance('2026-01-09T09:00:00+08:00')
    assert Decimal(a.snapshot()['cash'])==before+Decimal('68.00')
    assert a.advance('2026-01-09T09:00:00+08:00')['events_applied']==0


def test_unlisted_share_right_survives_sale_and_odd_lot_exits_after_listing(tmp_path):
    p=plan();source={'ref':'fixture-share-right','sha256':'4'*64,'verified':True,'evidence_type':'simulated',
        'assumption_ref':'frozen-share-fixture','assumption_sha256':'5'*64}
    def e(name,kind,clock,data):return {'event_id':'action:'+name,'kind':kind,'effective_at':clock,'available_at':clock,'source':source,'data':data}
    p['corporate_events']=[
        e('record','record_entitlement','2026-01-07T15:00:00+08:00',{'action_id':'shares','symbol':'600006.SH','entitled_shares':400}),
        e('activate','activate_entitlement','2026-01-08T08:00:00+08:00',{'action_id':'shares','cash_gross_due':'0.00','tax_due':'0.00','tax_final':True,'bonus_shares':25,'share_kind':'capitalization'}),
        e('list','bonus_shares_listed','2026-01-09T09:00:00+08:00',{'action_id':'shares','quantity':25})]
    a=L2CashAccount(tmp_path/'unlisted.sqlite',p);a.submit(order('buy'),quote())
    assert a.submit(order('too_early','2026-01-08','sell',425),quote('2026-01-08'))['status']=='rejected_order'
    a.submit(order('sell_original','2026-01-08','sell',400),quote('2026-01-08'))
    assert a.snapshot()['actions']['shares']['bonus_pending']==25
    sold=a.submit(order('sell_listed_odd','2026-01-09','sell',25),quote('2026-01-09'))
    assert sold['filled_quantity']==25 and sold['remaining_quantity']==0 and sold['holdings_after']=={}
    assert a.snapshot()['actions']['shares']['bonus_pending']==0


@pytest.mark.parametrize('provisional_tax',[None,'0.00'])
def test_unknown_tax_after_cash_receipt_blocks_spending_without_erasing_cash(tmp_path,provisional_tax):
    p=plan();source={'ref':'fixture-unknown-tax','sha256':'6'*64,'verified':True,'evidence_type':'simulated',
        'assumption_ref':'frozen-tax-fixture','assumption_sha256':'7'*64}
    def e(name,kind,clock,data):return {'event_id':'action:'+name,'kind':kind,'effective_at':clock,'available_at':clock,'source':source,'data':data}
    p['corporate_events']=[
        e('record','record_entitlement','2026-01-07T15:00:00+08:00',{'action_id':'tax','symbol':'600006.SH','entitled_shares':400}),
        e('activate','activate_entitlement','2026-01-08T08:00:00+08:00',{'action_id':'tax','cash_gross_due':'68.00','tax_due':provisional_tax,'tax_final':False,'bonus_shares':0,'share_kind':'none'}),
        e('pay','cash_dividend_paid','2026-01-08T08:01:00+08:00',{'action_id':'tax','gross_amount':'68.00','net_cash_credit':'68.00','tax_withheld':'0.00'})]
    a=L2CashAccount(tmp_path/'tax.sqlite',p);a.submit(order('buy'),quote())
    rejected=a.submit(order('spend','2026-01-08'),quote('2026-01-08'))
    assert rejected['status']=='rejected_order' and 'unresolved tax' in rejected['reason']
    assert a.snapshot()['cash']=='96060.66' and a.snapshot()['actions']['tax']['tax_due']==provisional_tax


def test_cash_received_after_order_decision_cannot_retroactively_fund_order(tmp_path):
    p=plan('10032.44');source={'ref':'fixture-receipt-clock','sha256':'8'*64,'verified':True,'evidence_type':'simulated',
        'assumption_ref':'frozen-receipt-fixture','assumption_sha256':'9'*64}
    def e(name,kind,clock,data):return {'event_id':'action:'+name,'kind':kind,'effective_at':clock,'available_at':clock,'source':source,'data':data}
    p['corporate_events']=[
        e('record','record_entitlement','2026-01-07T15:00:00+08:00',{'action_id':'latecash','symbol':'600006.SH','entitled_shares':400}),
        e('activate','activate_entitlement','2026-01-08T08:00:00+08:00',{'action_id':'latecash','cash_gross_due':'5000.00','tax_due':'0.00','tax_final':True,'bonus_shares':0,'share_kind':'none'}),
        e('pay','cash_dividend_paid','2026-01-08T09:35:00.500000+08:00',{'action_id':'latecash','gross_amount':'5000.00','net_cash_credit':'5000.00','tax_withheld':'0.00'})]
    a=L2CashAccount(tmp_path/'latecash.sqlite',p)
    # Full initial order costs at most10025.10, so this first request is affordable.
    assert a.submit(order('buy'),quote())['filled_quantity']==400
    assert a.snapshot()['cash']=='6025.10'
    rejected=a.submit(order('too_early','2026-01-08'),quote('2026-01-08'))
    assert rejected['status']=='rejected_order' and 'pre-dispatch' in rejected['reason']
    assert a.snapshot()['cash']=='11025.10' and a.snapshot()['actions']['latecash']['cash_paid']
