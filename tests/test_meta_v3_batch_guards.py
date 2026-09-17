"""Batch budget, precision, recovery and source guards; generated inputs only."""
from copy import deepcopy
import json
import time

import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest,Ledger
from quanta_agents.meta_v3.research_tools import ResearchTools,save_once
from quanta_agents.meta_v3 import research_tools,research_batch
from quanta_agents.meta_v3.discrete_fields import derive
from quanta_agents.meta_v3.runtime import ResearchRuntime,source_pins
from quanta_agents.meta_v3.closing import ClosingPolicy
from test_meta_v3_research_entry import action,program
from test_meta_v3_batch_research import configured,declaration,execute


def test_digits_use_exact_units_and_original_text_keep_missing_and_timing():
    rows=[]
    for i,(value,unit) in enumerate([('10.99','CNY'),('10.991','CNY'),(10.99,'CNY'),(None,'CNY'),('10.00','shares')]):
        rows.append({'session':f'2019-03-0{i+4}','symbol':'sh600001','value_text':value,'unit':unit,
            'effective_at':'2019-03-04T15:00:00+08:00','available_at':'2019-03-04T16:00:00+08:00','source_sha256':'a'*64})
    result=derive(rows,name='last_two_ticks',source_unit='CNY',minimum_increment='0.01',width=2)
    assert [r['value'] for r in result['field_rows']]==[99,None,None,None,None]
    assert result['evidence']['retained_rows']==5 and result['evidence']['usable_rows']==1
    assert result['field_rows'][0]['available_at']==rows[0]['available_at']
    assert result['field_semantics']['digit_derivation']['source_evidence_sha256']==digest(result['evidence'])
    huge={**rows[0],'value_text':'123456789012345678901234567890.99'}
    assert derive([huge],name='precise',source_unit='CNY',minimum_increment='.01',width=2)['field_rows'][0]['value']==99
    huge['value_text']='1e999999999'
    bounded=derive([huge],name='bounded',source_unit='CNY',minimum_increment='.01')
    assert bounded['field_rows'][0]['value'] is None and 'magnitude' in bounded['evidence']['trace'][0]['reason']
    with pytest.raises(AdmissionBlocked,match='magnitude'):derive(rows,name='bad',source_unit='CNY',minimum_increment='1e-999999999')


def digit_case(tmp_path):
    case=configured(tmp_path);raw=[{'session':r['session'],'symbol':r['symbol'],'value_text':str(r['value']),'unit':'CNY',
        'effective_at':r['effective_at'],'available_at':r['available_at'],'source_sha256':r['source_evidence_id']} for r in case['decision_fixture']['field_rows'] if r['field']=='close']
    d=derive(raw,name='last_tick',source_unit='CNY',minimum_increment='.01')
    path=tmp_path/'digit_trace.json';save_once(path,d['evidence'])
    case['evidence_sources']=[{'path':str(path),'sha256':digest(d['evidence'])}]
    case['decision_fixture']['fields'].append(d['field']);case['decision_fixture']['field_rows'].extend(d['field_rows'])
    case['batch_policy']['field_semantics']['last_tick']=d['field_semantics'];return case


def test_digit_batch_requires_actual_precision_contract_and_alternative_controls(tmp_path):
    case=digit_case(tmp_path);tools=ResearchTools(tmp_path/'stage','test',case,[])
    args=declaration((0,1));f=args['families'][0];f['program_template']['target_weight_expression']='where(last_tick == {{weight}}, 0.2, 0)';f['digit_fields']=['last_tick']
    fail=execute(tools,'uncorroborated','register_batch',args)
    assert fail['public']['validation_failures']==2
    args['comparisons']=[{'kind':kind,'families':['simple'],'prediction':'Explicit generated alternative; not market proof'} for kind in ('alternative_digits','alternative_explanation')]
    good=execute(tools,'controlled','register_batch',args)
    assert good['public']['validation_failures']==0
    case['batch_policy']['field_semantics']['last_tick']['digit_derivation']['integer_conversion']='rounded'
    with pytest.raises(AdmissionBlocked,match='cannot infer lost precision'):ResearchTools(tmp_path/'bad','test',case,[])


def test_horizon_and_ordinary_work_share_scan_budget_with_batches(tmp_path):
    case=configured(tmp_path);case['batch_policy']['max_scan_cells_total']=200
    tools=ResearchTools(tmp_path/'stage','test',case,[])
    # No numeric work needed: preserved prior request still reserves its scan.
    tools.history=[{'id':'h','response':{'action':'diagnose_horizons','arguments_json':json.dumps({'horizons':[1]})},'result':None}]
    assert tools._diagnostic_reservations()['scan_cells']==192
    with pytest.raises(AdmissionBlocked,match='scan-cell'):tools.execute('over','register_batch',declaration((.2,)))
    tools.history=[{'id':'ordinary','response':{'action':'develop_strategy'},'result':None}]
    assert tools._ordinary_candidates()==1
    with pytest.raises(AdmissionBlocked,match='scan-cell'):tools.execute('over2','register_batch',declaration((.1,.2)))


def test_invalid_code_cannot_execute_and_stop_rule_retains_unstarted_candidates(tmp_path,monkeypatch):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    args=declaration((.1,.2));args['families'][0]['program_template']['target_weight_expression']='__import__("os").system({{weight}})'
    args['stop_rule']='stop_on_first_failure'
    execute(tools,'registration','register_batch',args)
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('invalid DSL worker'))
    r=execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    assert r['public']['status_counts']=={'invalid':1,'not_started':1} and r['public']['started_candidates']==0


def test_real_runtime_application_recovers_saved_batch_without_new_gateway_or_dispatch(tmp_path,monkeypatch):
    case=configured(tmp_path);task={'case':case,'case_hash':digest(case),'idea':'Engineering batch recovery','documents':[]}
    ledger=Ledger.create(tmp_path/'stage',policy=ClosingPolicy(task_calls=6,stage_calls=6),tasks={'test':task},
        deadline_epoch=time.time()+7200,provenance={'source_pins':source_pins(),'fixture_only':True})
    runtime=ResearchRuntime(ledger.root)
    registered=action(runtime,task,'register_batch',declaration((.2,)))
    before_calls=len(ledger.status('test')['calls']);original=research_tools.save_once
    def interrupted(path,value):
        if path.name=='artifact.json' and value.get('kind')=='batch_execution_evidence_v1':raise OSError('parent lost result commit')
        original(path,value)
    monkeypatch.setattr(research_tools,'save_once',interrupted)
    with pytest.raises(OSError):action(runtime,task,'execute_batch',{'registration_evidence_id':registered['id']})
    call=ledger.history('test')[-1];assert call['status']=='applying'
    monkeypatch.setattr(research_tools,'save_once',original)
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('cached call dispatched again'))
    runtime._apply(call['id'])
    assert ledger.history('test')[-1]['status']=='applied'
    assert ledger.history('test')[-1]['result']['public']['status_counts']=={'completed':1}
    assert len(ledger.status('test')['calls'])==before_calls+1
