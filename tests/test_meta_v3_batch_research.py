"""Real subprocess mechanics on generated fixtures; no research model calls."""
from copy import deepcopy
import json
import time

import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest,Ledger
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3 import research_tools,research_batch
from quanta_agents.meta_v3.runtime import ResearchRuntime,source_pins
from quanta_agents.meta_v3.closing import ClosingPolicy
from test_meta_v3_research_entry import fixture,program,action


def configured(tmp_path):
    case=fixture.prepare(tmp_path/'case',flat=True)
    case['research_policy']={'version':'structural_research_v1','action_limits':{
        'register_batch':4,'execute_batch':4,'inspect_batch':16,'develop_strategy':5,'diagnose_execution':3,'register_experiment':3}}
    case['batch_policy']={'version':'bounded_batch_v1','max_candidates_total':64,'max_scan_cells_total':2097152,
        'max_wall_seconds':120,'output_stop_threshold_bytes':268435456,
        'field_semantics':{f['name']:{'unit':f['unit'],'raw_precision':'generated deterministic fixture','digit_derivation':None} for f in case['decision_fixture']['fields']}}
    return case


def declaration(values=(.1,.2)):
    p=program();p['target_weight_expression']='{{weight}}'
    family={'id':'simple','priority':1,'origin':'model_intuition','mechanism_status':'unknown_anomaly',
        'mechanism':'Generated unknown anomaly for engineering; no fabricated market explanation','role':'original',
        'program_template':p,'parameters':{'weight':list(values)},'digit_fields':[]}
    return {'families':[family],'comparisons':[{'kind':'parameter_neighborhood','families':['simple'],'prediction':'Constant prices should lose declared costs'}],
        'selection_rule':'Compare every full-capital net outcome and failure; no OOS claim','stop_rule':'continue_settled_failures'}


def execute(tools,eid,name,args):
    result=tools.execute(eid,name,args)
    tools.history.append({'id':eid,'response':{'action':name,'arguments_json':json.dumps(args)},'result':result})
    return result


def report(batch='run',candidate='c001'):
    return {'outcome':'strategy_for_development','conclusion':'Generated accounting demonstration only','evidence_ids':['registration',batch],
        'program_evidence_id':batch,'batch_candidate_id':candidate,'limitations':['Generated prices; no alpha or independent OOS'],
        'next_step':'Obtain admitted evidence','falsifiers':['Accounting differs']}


def read_results(tools):
    offset=0;rows=[]
    while offset is not None:
        r=execute(tools,'page'+str(offset),'inspect_batch',{'registration_evidence_id':'registration','candidate_id':None,'table':'results','offset':offset,'limit':32})
        rows.extend(r['public']['rows']);offset=r['public']['next_offset']
    return rows


def test_batch_expands_executes_all_variants_and_final_reuses_without_model_or_rerun(tmp_path,monkeypatch):
    case=configured(tmp_path);tools=ResearchTools(tmp_path/'stage','test',case,[])
    assert {'register_batch','execute_batch','inspect_batch'}<=set(tools.menu())
    assert tools.contract()['actions']['register_batch']['family_fields']['mechanism_status']=='hypothesis|unknown_anomaly'
    r=execute(tools,'registration','register_batch',declaration((.1,.2,2)))
    assert r['public']['reserved_candidates']==3 and r['public']['reserved_scan_cells']==144
    assert not list(tools.batch_folder.rglob('intent.json'))
    result=execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    assert result['public']['status_counts']=={'completed':2,'failed':1},read_results(tools)
    assert result['public']['new_model_calls_inside_batch']==0 and result['public']['started_candidates']==3
    with pytest.raises(AdmissionBlocked,match='all batch result rows'):tools.final(report())
    rows=read_results(tools)
    assert [r['status'] for r in rows]==['completed','completed','failed']
    assert all(r['account']['initial_cash']=='10000.00' for r in rows[:2])
    assert rows[0]['account']['net_pnl']=='0.00' and rows[0]['account']['trade_count']==0
    assert float(rows[1]['account']['net_pnl'])<0 and rows[1]['account']['trade_count']>0
    before={str(p):p.read_bytes() for p in tools.batch_folder.rglob('worker_result.json')}
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('completed candidate rerun'))
    with pytest.raises(AdmissionBlocked,match='no funded fills'):tools.final(report())
    assert tools.final(report(candidate='c002'))['legal_submission']
    again=execute(tools,'again','execute_batch',{'registration_evidence_id':'registration'})
    assert again['public']['started_candidates']==3
    assert {str(p):p.read_bytes() for p in tools.batch_folder.rglob('worker_result.json')}==before


def test_duplicate_grid_and_cross_batch_use_original_funded_result(tmp_path,monkeypatch):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    execute(tools,'registration','register_batch',declaration((.2,.2)))
    one=execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    assert one['public']['started_candidates']==1 and one['public']['status_counts']=={'completed':1,'reused':1}
    read_results(tools);assert tools.final(report(candidate='c002'))['legal_submission']
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('duplicate scan'))
    second=declaration((.2,));second['families'][0]['program_template']['hypothesis']='Different prose'
    execute(tools,'second','register_batch',second)
    two=execute(tools,'second_run','execute_batch',{'registration_evidence_id':'second'})
    assert two['public']['started_candidates']==0 and two['public']['status_counts']=={'reused':1}
    with pytest.raises(AdmissionBlocked,match='recorded in batch'):
        p=program();p['target_weight_expression']='(0.2)';tools.execute('ordinary_duplicate','develop_strategy',{'program':p})


def test_expansion_invalid_branches_and_global_budget_are_visible(tmp_path):
    case=configured(tmp_path);case['batch_policy']['max_candidates_total']=3
    tools=ResearchTools(tmp_path/'stage','test',case,[])
    bad=declaration();bad['families'][0]['program_template']['target_weight_expression']='lag(close, -{{weight}})'
    r=execute(tools,'registration','register_batch',bad)
    assert r['public']['validation_failures']==2
    run=execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    assert run['public']['status_counts']=={'invalid':2} and run['public']['started_candidates']==0
    with pytest.raises(AdmissionBlocked,match='candidate budget'):
        tools.execute('over','register_batch',declaration())
    huge=declaration();f=huge['families'][0];f['parameters']={'x':list(range(8)),'y':list(range(8))};f['program_template']['target_weight_expression']='{{x}}+{{y}}'
    with pytest.raises(AdmissionBlocked,match='exceeds32'):tools.execute('huge','register_batch',huge)


def test_parent_interruption_recovers_only_committed_results(tmp_path,monkeypatch):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    execute(tools,'registration','register_batch',declaration((.1,)))
    original=research_tools.save_once
    def interrupted(path,value):
        if path==tools.folder/'run/artifact.json':raise OSError('parent interrupted after all worker results')
        original(path,value)
    monkeypatch.setattr(research_tools,'save_once',interrupted)
    with pytest.raises(OSError):tools.execute('run','execute_batch',{'registration_evidence_id':'registration'})
    monkeypatch.setattr(research_tools,'save_once',original)
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('recovery must not dispatch'))
    saved=tools.recover_batch_call('run',{'registration_evidence_id':'registration'})
    assert saved['public']['status_counts']=={'completed':1}


def test_unknown_dispatch_stops_later_candidates_and_all_new_scans(tmp_path,monkeypatch):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    execute(tools,'registration','register_batch',declaration())
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:(_ for _ in ()).throw(OSError('lost dispatch observation')))
    with pytest.raises(OSError):tools.execute('run','execute_batch',{'registration_evidence_id':'registration'})
    saved=tools.recover_batch_call('run',{'registration_evidence_id':'registration'})
    assert saved['public']['status_counts']=={'unknown':1,'not_started':1}
    assert saved['public']['started_candidates']==1 and 'develop_strategy' not in tools.menu() and 'register_batch' not in tools.menu()
    with pytest.raises(AdmissionBlocked,match='unresolved batch'):tools.execute('nope','develop_strategy',{'program':program()})


def test_batch_worker_cannot_spend_final_time_reserve(tmp_path,monkeypatch):
    case=configured(tmp_path);task={'case':case,'case_hash':digest(case),'idea':'Engineering batch','documents':[]}
    ledger=Ledger.create(tmp_path/'stage',policy=ClosingPolicy(task_calls=5,stage_calls=5),tasks={'test':task},
        deadline_epoch=time.time()+3590,provenance={'source_pins':source_pins(),'fixture_only':True})
    tools=ResearchTools(ledger.root,'test',case,[])
    execute(tools,'registration','register_batch',declaration((.1,)))
    # By dispatch time exploration is closed; final time is still available.
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('final reserve consumed'))
    value=execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    assert value['public']['started_candidates']==0 and value['public']['status_counts']=={'not_started':1}


def test_cross_batch_committed_result_without_receipt_is_reconciled_before_dispatch(tmp_path,monkeypatch):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    execute(tools,'registration','register_batch',declaration((.2,)))
    execute(tools,'second','register_batch',declaration((.2,)))
    execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    work=tools.batch_folder/'registration/candidates/c001';original=(work/'worker_result.json').read_bytes()
    (work/'receipt.json').unlink() # Explicit generated test crash window.
    assert research_batch.unresolved(tools.batch_folder)
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('cross-batch duplicate dispatch'))
    result=execute(tools,'second_run','execute_batch',{'registration_evidence_id':'second'})
    assert result['public']['status_counts']=={'reused':1} and result['public']['started_candidates']==0
    assert (work/'receipt.json').is_file() and (work/'worker_result.json').read_bytes()==original


def test_batch_candidate_can_be_diagnosed_and_bound_to_real_revision_without_reexecution(tmp_path,monkeypatch):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    execute(tools,'registration','register_batch',declaration((.2,)))
    execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('baseline rerun'))
    d=execute(tools,'diagnosis','diagnose_execution',{'evidence_ids':['run/c001']})
    assert d['public']['accounts'][0]['net_pnl']=='-28.28'
    p=program();p['target_weight_expression']='0.3'
    reg=execute(tools,'revision','register_experiment',{'baseline_evidence_id':'run/c001','diagnosis_evidence_id':'diagnosis',
        'mechanism_hypotheses':['Minimum fee and lot-size thresholds change turnover'],
        'distinguishing_prediction':'Same flat prices and raw execution; different share quantities/costs','structural_change':'Different allocation at a lot-size threshold',
        'revision_program':p,'success_rule':'Report full-capital difference including all fees and cash days','failure_rule':'Missing fees, capital changes or unvalued days'})
    assert not reg['public']['executed']
    result=execute(tools,'revised','develop_strategy',{'program':p,'experiment_evidence_id':'revision'})
    assert result['public']['experiment']['comparison']['pairs'][0]['same_cash_calendar_and_initial_capital']
