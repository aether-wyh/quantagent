"""Fixed study allocation and ordinary final delivery on generated inputs only."""
from copy import deepcopy
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from quanta_agents.meta_v3 import study_registry as sr, study_allocation as sa, tool_resources as tr, research_batch
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import Ledger, AdmissionBlocked, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime, source_pins
from test_meta_v3_ledger import P, A, request, settle
from test_meta_v3_batch_research import configured
from test_meta_v3_tool_resources import reply


@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(sr,'REGISTRY',tmp_path/'canonical.sqlite3')
    def forbidden(*args,**kwargs):pytest.fail('No model, subprocess or account worker')
    monkeypatch.setattr(research_batch.subprocess,'Popen',forbidden)
    monkeypatch.setattr(module('meta.codex_gateway').CodexGateway,'run',forbidden)


def proposal(tmp_path, *, headroom=0, output_bytes=5000000):
    case=configured(tmp_path/'case')
    task={'case':case,'case_hash':digest(case),'idea':'Generated allocation evidence; permit abstention.','documents':[]}
    tasks={'one':task};pins=source_pins()
    budget={'actions':20,'candidates':8,'scan_cells':20000,'comparisons':64,
        'wall_ms':60000,'controller_cpu_ms':60000,'retained_output_bytes':output_bytes}
    trials=[{'id':f't{i}','root':str(tmp_path/f'stage{i}'),'case_hash':digest(case),'architecture_hash':'2'*64,
        'repeat':i+1,'tasks_hash':digest(tasks),'source_pins_hash':digest(pins),'policy':asdict(P),
        'duration_seconds':7200,'tool_budget':deepcopy(budget)} for i in range(2)]
    allocation={'version':sa.VERSION,'model_tokens':800+headroom,'model_calls':8,
        'tool_resources':{k:v*2 for k,v in budget.items()}}
    return {'study_id':'allocated','trials':trials,'allocation':allocation},tasks,pins


def create(plan,tasks,pins,index):
    t=plan['trials'][index]
    return sr.create_stage(t['root'],plan['study_id'],t['id'],policy=P,tasks=tasks,
        duration_seconds=t['duration_seconds'],provenance={'source_pins':pins})


def test_insufficient_total_cannot_promise_both_trial_grants(tmp_path):
    plan,_,_=proposal(tmp_path);plan['allocation']['model_tokens']=799
    with pytest.raises(AdmissionBlocked,match='fund all model grants'):sr.freeze(plan)
    assert not sr.REGISTRY.exists()


def test_allocation_requires_every_tool_grant_and_exact_shape(tmp_path):
    plan,_,_=proposal(tmp_path);plan['trials'][1].pop('tool_budget')
    with pytest.raises(AdmissionBlocked,match='every trial tool grant'):sr.freeze(plan)
    plan['allocation']=None
    with pytest.raises(AdmissionBlocked,match='exact study allocation'):sr.freeze(plan)
    assert not sr.REGISTRY.exists()


def test_same_case_repeat_architectures_need_equal_whole_trial_ceilings(tmp_path):
    plan,_,_=proposal(tmp_path)
    plan['trials'][1].update(repeat=1,architecture_hash='3'*64)
    plan['trials'][1]['policy']['stage_tokens']=500
    plan['allocation']['model_tokens']=900
    with pytest.raises(AdmissionBlocked,match='equal resource ceilings'):sr.freeze(plan)
    # Different internal task caps are allowed within identical trial ceilings.
    plan['trials'][1]['policy']['stage_tokens']=400
    plan['trials'][1]['policy']['task_calls']=2
    sr.freeze(plan)
    assert sr.snapshot('allocated')['study_allocation']['model_headroom']==100


def test_unknown_trial_keeps_its_full_grant_and_cannot_reset_sibling(tmp_path):
    plan,tasks,pins=proposal(tmp_path);sr.freeze(plan)
    one=create(plan,tasks,pins,0);intent=one.reserve('one',A,request);one.unknown(intent['intent_id'],'Generated unknown')
    before=sr.snapshot('allocated')['study_allocation']
    assert before['grants'][0]['unknown_model_reserve']==80 and before['grants'][0]['model_token_grant']==400
    assert not before['grants'][1]['claimed'] and before['grants'][1]['model_token_grant']==400
    two=create(plan,tasks,pins,1);settle(two,two.reserve('one',A,request),cost=20)
    after=sr.snapshot('allocated')['study_allocation']
    assert after['grants'][0]['unknown_model_reserve']==80 and after['grants'][1]['known_tokens']==20
    assert not after['grant_transfer_allowed']


def test_paid_overrun_consumes_explicit_headroom_without_shrinking_other_grant(tmp_path):
    plan,tasks,pins=proposal(tmp_path,headroom=100);sr.freeze(plan)
    one=create(plan,tasks,pins,0);settle(one,one.reserve('one',A,request),cost=450)
    two=create(plan,tasks,pins,1);second=two.reserve('one',A,request)
    state=sr.snapshot('allocated')['study_allocation']
    assert state['model_overrun']==50 and state['model_headroom']==100
    assert state['grants'][1]['model_token_grant']==400 and state['grants'][1]['unknown_model_reserve']==80
    assert not state['model_allocation_exhausted']
    settle(two,second,cost=20)


def test_overrun_beyond_headroom_blocks_new_calls_and_retains_all_cost(tmp_path):
    plan,tasks,pins=proposal(tmp_path);sr.freeze(plan)
    one=create(plan,tasks,pins,0);settle(one,one.reserve('one',A,request),cost=450)
    with pytest.raises(AdmissionBlocked,match='study model headroom exhausted; no new stage claim'):
        create(plan,tasks,pins,1)
    assert sr.snapshot('allocated')['known_tokens']==450
    assert sr.snapshot('allocated')['study_allocation']['grants'][1]['model_token_grant']==400
    assert sr.snapshot('allocated')['trials'][1]['claimed_at'] is None
    assert not (tmp_path/'stage1').exists()


def test_completed_final_does_not_transfer_unused_grant(tmp_path):
    plan,tasks,pins=proposal(tmp_path);sr.freeze(plan)
    one=create(plan,tasks,pins,0)
    settle(one,one.reserve('one',A,request),cost=10,action='submit_research_report',final=True)
    two=create(plan,tasks,pins,1)
    for _ in range(3):settle(two,two.reserve('one',A,request),cost=10)
    closing=two.reserve('one',A,request)
    assert closing['actions']==['submit_research_report'] and closing['mode']=='close_only'
    settle(two,closing,cost=10,action='submit_research_report',final=True)
    with pytest.raises(AdmissionBlocked):two.reserve('one',A,request)
    result=sr.snapshot('allocated')['study_allocation']
    assert [g['model_token_grant'] for g in result['grants']]==[400,400]
    assert [g['calls_used'] for g in result['grants']]==[1,4]


def test_concurrent_trials_keep_separate_preallocated_grants(tmp_path):
    plan,tasks,pins=proposal(tmp_path);sr.freeze(plan)
    jobs=[create(plan,tasks,pins,i) for i in range(2)];barrier=Barrier(2)
    def reserve(job):
        barrier.wait(timeout=5)
        return job.reserve('one',A,request)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,jobs))
    assert len({x['intent_id'] for x in results})==2
    state=sr.snapshot('allocated')['study_allocation']
    assert [g['unknown_model_reserve'] for g in state['grants']]==[80,80]
    assert not state['model_allocation_exhausted']


def test_tool_overrun_forces_untouched_trial_to_legal_input_based_final(tmp_path):
    plan,tasks,pins=proposal(tmp_path,output_bytes=1);sr.freeze(plan)
    one,two=[create(plan,tasks,pins,i) for i in range(2)]
    runtime1,runtime2=ResearchRuntime(one.root),ResearchRuntime(two.root)
    runtime1.verify_inputs();runtime2.verify_inputs()
    result=reply(runtime1,tasks['one'],'inspect_inputs',{'table':'fields','offset':0,'limit':32},task_id='one')
    assert result['status']=='applied' and tr.status(one.root)['used']['retained_output_bytes']>1
    state=two.status('one')
    assert state['mode']=='close_only' and state['reasons']==['study_tool_headroom_exhausted']
    assert two.history('one')==[]
    tools=runtime2._tools('one');input_id=tools.contract()['input_evidence_id']
    report={'outcome':'abstain','conclusion':'Resource admission stopped before research; the supplied generated input does not prove an edge.',
        'evidence_ids':[input_id],'program_evidence_id':None,'limitations':['No tool evaluation in this trial.'],
        'next_step':'Keep this incomplete attempt and obtain new predeclared evidence.','falsifiers':['Valid executable evidence supports a different conclusion.']}
    final=reply(runtime2,tasks['one'],'submit_research_report',report,task_id='one')
    assert final['status']=='applied' and final['result']['legal_submission']
    assert two.status('one')['terminal']=='submitted' and tr.status(two.root)['entries']==[]
    assert not final['result']['formal_target_success']
    # The same input ID cannot stand in for an evaluated strategy.
    bad=deepcopy(report);bad.update(outcome='strategy_for_development',program_evidence_id=input_id)
    with pytest.raises(AdmissionBlocked,match='foreign or unknown'):tools.final(bad)


def test_model_reservation_rechecks_study_after_status_race(tmp_path,monkeypatch):
    plan,tasks,pins=proposal(tmp_path);sr.freeze(plan)
    one,two=[create(plan,tasks,pins,i) for i in range(2)]
    pending=one.reserve('one',A,request)
    original=sr.reserve_model;triggered=[]
    def race(root,intent,reserve):
        if root==two.root and not triggered:
            triggered.append(True);settle(one,pending,cost=450)
        return original(root,intent,reserve)
    monkeypatch.setattr(sr,'reserve_model',race)
    with pytest.raises(AdmissionBlocked,match='headroom exhausted'):two.reserve('one',A,request)
    assert two.status('one')['calls']==[] and sr.snapshot('allocated')['known_tokens']==450
