"""Same public tools and controlled program, using labelled engineering inputs."""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3.l2_cash_account import KINDS
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from test_meta_v3_l2_corporate_actions import dynamic_plan
from test_meta_v3_l2_cash_account import quote


def case():
    p=dynamic_plan();days=['2026-01-06','2026-01-07','2026-01-08','2026-01-09','2026-01-12']
    p.update(calendar=days,initial_time=days[0]+'T00:00:00+08:00',mode='real_development')
    p['policy'].update(assumed_feed_delay_ms=1000,max_decision_quote_source_age_ms=4000,
        buy_limit_vs_decision_ask_fraction='0.001',sell_limit_vs_decision_bid_fraction='0.001')
    p['obligations']=[{'code':'600006.SH','date':d,'kind':k,'status':'documented_scope' if k=='corporate_actions' else 'declared_simulation',
        'evidence_sha256':'a'*64,'note':'Generated engineering stand-in; no market or source claim'} for d in days for k in KINDS]
    fields=[];eligibility=[];obs=[];marks=[]
    for i,day in enumerate(days):
        metadata={'session':day,'symbol':'sh600006','effective_at':day+'T15:05:00+08:00','available_at':day+'T15:05:00+08:00','source_evidence_id':'a'*64}
        fields.append({**metadata,'field':'close','value':[2.,1.,0.,0.,0.][i]})
        eligibility.append({**metadata,'eligible':True})
        execution=quote(day);reference=deepcopy(execution)
        reference.update(event_ts=day+'T09:34:59+08:00',time_raw=93459000,source_row_no=1)
        obs.append({'code':'600006.SH','date':day,'decision':reference,'execution':execution,'source_selection_sha256':'a'*64})
        marks.append({'code':'600006.SH','date':day,'raw_price':'10.00','effective_at':day+'T15:05:00+08:00',
            'available_at':day+'T15:05:00+08:00','source_sha256':'a'*64})
    return {'research_class':'real_saved_development','description':'Generated engineering stand-in for L2 entry; not actual market evidence',
        'initial_cash':p['initial_cash'],'execution_backend':'v3_l2_cash_001',
        'decision_fixture':{'kind':'exposed_l2_decision_table','codes':['sh600006'],'calendar':days,
            'fields':[{'name':'close','unit':'fixture_value'}],'field_rows':fields,'eligibility_rows':eligibility},
        'raw_source_bindings':{'obligations':p['obligations'],'source_artifacts':[]},
        'l2_execution':{'account_plan':p,'observations':obs,'marks':marks}}


def program():
    return {'version':'factor_strategy_program_v1','factors':[],
        'target_weight_expression':'where(close > 1, 0.05, where(close > 0, 0.025, 0))',
        'hypothesis':'Engineering sequence, no alpha claim','applicability':['Generated data only'],
        'invalidation_conditions':['Cash or share identity differs']}


def run(tmp_path,data):
    tools=ResearchTools(tmp_path,'unit',data,[])
    result=tools.execute('run','develop_strategy',{'program':program()})
    artifact=json.loads((tmp_path/'tools/unit/run/artifact.json').read_text(encoding='utf-8'))
    return tools,result,artifact


def test_public_program_reaches_funded_l2_and_dynamic_rights(tmp_path):
    tools,result,artifact=run(tmp_path,case())
    assert 'diagnose_horizons' not in tools.menu()
    assert result['public']['raw_status']=='completed_mechanical',artifact['raw']
    raw=artifact['raw']['result'];snap=raw['final_snapshot']
    assert len(raw['daily'])==5 and raw['filled_order_count']==3
    assert snap['external_cash_flow']=='100000.00'
    assert snap['actions']['cash-fixture']['entitled_shares']==400
    assert snap['actions']['cash-fixture']['tax_due']==snap['actions']['cash-fixture']['tax_paid']=='11.60'
    assert snap['cash']=='100022.42' and raw['portfolio_pnl']=='22.42'
    assert result['public']['costs_applied'] and not result['formal_target_success']
    targets=json.loads((tmp_path/'tools/unit/run/workbench/targets.json').read_text(encoding='utf-8'))
    assert targets['targets'][0]['signal_date']=='2026-01-06' and targets['targets'][0]['trade_date']=='2026-01-07'
    tools.history=[{'id':'run','result':result,'response':{'action':'develop_strategy'}}]
    page=tools.execute('inspect','inspect_execution',{'evidence_id':'run','table':'trades','offset':0,'limit':2})
    assert page['public']['returned_rows']>0
    compact=tools.execute('compact','inspect_execution',{'evidence_id':'run','table':'daily_compact','offset':0,'limit':32})
    assert compact['public']['returned_rows']==5 and compact['public']['next_offset'] is None


def test_fully_rejected_execution_cannot_be_selected_as_funded_strategy(tmp_path):
    data=case();data['l2_execution']['account_plan']['fees']=None
    for row in data['raw_source_bindings']['obligations']:
        if row['kind']=='fee_policy':row['status']='pending'
    tools,result,artifact=run(tmp_path,data)
    assert result['public']['raw_status']=='completed_execution_evidence'
    assert result['public']['final_snapshot']['cash']=='100000.00'
    assert not result['public']['costs_applied'] and result['public']['portfolio_pnl'] is None
    tools.history=[{'id':'run','result':result,'response':{'action':'develop_strategy'}}]
    final={'outcome':'strategy_for_development','conclusion':'Fixture report','evidence_ids':['run'],'program_evidence_id':'run',
        'limitations':['All orders rejected'],'next_step':'Read missing source evidence','falsifiers':['Source gap resolved']}
    with pytest.raises(AdmissionBlocked,match='no completed funded execution'):tools.final(final)
    final.update(outcome='abstain',program_evidence_id=None)
    assert tools.final(final)['legal_submission']


def test_missing_held_mark_preserves_actual_fills_and_failed_day(tmp_path):
    data=case();data['l2_execution']['marks']=[x for x in data['l2_execution']['marks'] if x['date']!='2026-01-07']
    tools,result,artifact=run(tmp_path,data)
    assert result['public']['raw_status']=='failed' and 'missing held mark' in result['public']['error']['message']
    partial=artifact['raw']['partial'];assert len(partial['trades'])==1 and len(partial['daily'])==1
    assert partial['final_snapshot']['cash']=='95992.66'
    assert sum(x['quantity'] for x in partial['final_snapshot']['lots'].values())==400
    assert partial['final_snapshot']['actions']['cash-fixture']['entitled_shares']==400
    assert result['public']['portfolio_pnl'] is None
    tools.history=[{'id':'run','result':result,'response':{'action':'develop_strategy'}}]
    page=tools.execute('inspect','inspect_execution',{'evidence_id':'run','table':'trades','offset':0,'limit':2})
    assert page['public']['total_rows']==1 and page['public']['returned_rows']==1


def test_execution_depth_does_not_rewrite_saved_order_quantity(tmp_path):
    data=case();_,_,original=run(tmp_path/'a',data)
    changed=deepcopy(data)
    for row in changed['l2_execution']['observations']:
        if row['date']=='2026-01-07':
            row['execution']['ask_volume_1']=100
            row['execution']['ask_volume_2']=100
    _,_,modified=run(tmp_path/'b',changed)
    a=original['raw']['result']['trades'][0]['order']
    b=modified['raw']['result']['trades'][0]['order']
    assert a==b and a['quantity']==400
    assert modified['raw']['result']['trades'][0]['receipt']['filled_quantity']==0


def test_runtime_saved_fixture_can_close_after_l2_evidence(tmp_path):
    import time
    from quanta_agents.meta_v3.closing import ClosingPolicy
    from quanta_agents.meta_v3.ledger import Ledger,digest
    from quanta_agents.meta_v3.runtime import ResearchRuntime,source_pins
    from test_meta_v3_research_entry import action
    data=case();task={'case':data,'case_hash':digest(data),'idea':'Engineering only: evaluate the supplied program and account evidence.','documents':[]}
    ledger=Ledger.create(tmp_path/'runtime',policy=ClosingPolicy(task_calls=4,stage_calls=4),
        tasks={'test':task},deadline_epoch=time.time()+7200,provenance={'source_pins':source_pins(),'fixture_only':True})
    runtime=ResearchRuntime(ledger.root)
    one=action(runtime,task,'develop_strategy',{'program':program()})
    assert one['result']['public']['raw_status']=='completed_mechanical'
    report={'outcome':'abstain','conclusion':'Generated engineering inputs verify wiring only.',
        'evidence_ids':[one['id']],'program_evidence_id':None,'limitations':['No actual model or market research'],
        'next_step':'Obtain bounded real execution sources','falsifiers':['Accounting mismatch']}
    two=action(runtime,task,'submit_research_report',report)
    assert runtime.ledger.status('test')['terminal']=='submitted' and two['result']['legal_submission']
    assert two['result']['target_achieved'] is False


def test_payment_day_source_gap_survives_full_sale_and_settlement(tmp_path):
    data=case()
    for row in data['raw_source_bindings']['obligations']:
        if row['date']=='2026-01-09' and row['kind']=='corporate_actions':row['status']='unknown'
    spec=program();spec['target_weight_expression']='where(close > 1, 0.05, 0)'
    tools=ResearchTools(tmp_path,'unit',data,[])
    result=tools.execute('run','develop_strategy',{'program':spec})
    artifact=json.loads((tmp_path/'tools/unit/run/artifact.json').read_text(encoding='utf-8'))
    assert result['public']['raw_status']=='failed' and result['public']['valuation_complete_through']=='2026-01-08'
    snap=artifact['raw']['partial']['final_snapshot']
    assert snap['cash']=='100025.72' and snap['actions']['cash-fixture']['cash_paid']
    assert not any(x['quantity'] for x in snap['lots'].values())
    assert 'unknown held economic exposure' in result['public']['error']['message']
