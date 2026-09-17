"""Generated gateway receipts only; actual ledger/admission/read-only handoff."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

import pytest

from quanta_agents.meta_v3 import codex_session_gateway as capture
from quanta_agents.meta_v3 import research_extension as extension
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.extension_handoff import inspect_handoff,validate_policy
from quanta_agents.meta_v3.ledger import AdmissionBlocked,Ledger,digest,serial
from quanta_agents.meta_v3.runtime import ResearchRuntime,action_schema,source_pins
from test_meta_v3_research_iteration import configured
from test_meta_v4_controller import contracts


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    case=configured()
    case['report_policy']={'version':'claim_support_v1'}
    case['experiment_design_policy']={'version':'scalar_conjunction_design_review_v1'}
    task={'case':case,'case_hash':digest(case),'idea':'Generated extension question','documents':[]}
    ledger=Ledger.create(tmp_path/'parent',policy=ClosingPolicy(task_calls=6,stage_calls=6),
        tasks={'test':task},deadline_epoch=time.time()+7200,provenance={
            'source_pins':source_pins(),'fixture_only':True,
            'controller_policy':contracts(['test']),'harness_version':'4.0.0-dev',
            'runtime_identity_route':{'version':'codex_session_v1'},
            'extension_handoff_policy':{'version':'yield_to_controller_v1'}})
    receipts={};verified=[]
    def verifier(folder,**kwargs):
        verified.append((Path(folder).name,kwargs))
        return receipts[Path(folder).name]
    monkeypatch.setattr(capture,'verify_saved_completion',verifier)
    monkeypatch.setattr(extension.module('meta.codex_gateway'),'verify_saved_completion',
        lambda *a,**k:pytest.fail('V4 session receipt sent to legacy verifier'))
    def action(runtime,task_id,name,args):
        tools=runtime._tools(task_id)
        intent=runtime.ledger.reserve(task_id,tools.menu(),lambda menu,*a:('Generated engineering prompt',action_schema(menu)))
        response={'action':name,'arguments_json':json.dumps(args),
            'public_summary':'Generated engineering response, no provider call',
            'self_review':dict.fromkeys(('assessment','uncertainty','next_step','falsifier'),'Generated fixture')}
        receipt={'response':response,'usage':{'input_tokens':10,'output_tokens':10},
            'request_identity':{'intent_id':intent['intent_id']},
            'artifact_sha256':{capture.SESSION:'a'*64},'model_verified':False,
            'runtime_identity':{'verified':True,'level':'generated_engineering_fixture'}}
        receipts[intent['intent_id']]=receipt
        runtime.ledger.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
        runtime._apply(intent['intent_id'])
        return runtime.ledger.history(task_id)[-1]
    runtime=ResearchRuntime(ledger.root)
    first=action(runtime,'test','inspect_inputs',{'table':'coverage','offset':0,'limit':32})
    request=action(runtime,'test','request_research_extension',{
        'evidence_ids':[first['id']],'problem':'Need volume to distinguish the stated explanations.',
        'request_kind':'data','requested_fields':['volume'],'specification':'Generated volume field on the same axes',
        'expected_information_gain':'Evaluate the availability of a new field without a strategy claim.',
        'requested_resource_bounds':{'symbols':1,'sessions':5,'model_calls':4,'download_bytes':0,'wall_seconds':7200}})
    child=deepcopy(case)
    child['decision_fixture']['fields'].append({'name':'volume','unit':'engineering shares'})
    added=deepcopy(child['decision_fixture']['field_rows'])
    for row in added:row.update(field='volume',value=100)
    child['decision_fixture']['field_rows'].extend(added)
    source=tmp_path/'generated_source.json';source.write_text(serial(child),encoding='utf-8')
    child['evidence_sources']=[{'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]
    decision={'status':'ready','reason':'Generated additive field is implemented; no financial evidence.',
        'asset_contract':'a_share_cash_equity','resource_bounds':{
            'symbols':1,'sessions':5,'model_calls':4,'download_bytes':0,'wall_seconds':7200},
        'exposure_statement':'Generated fixture; parent evidence exposed; no OOS.',
        'source_admissions':[{'path':str(source),'role':'engineering','partition':'generated_fixture','content_date_range':None}]}
    kwargs={'decision':decision,'child_case':child,
        'policy':ClosingPolicy(task_calls=4,stage_calls=4,stage_tokens=600000),
        'deadline_epoch':time.time()+7000}
    return ledger,request['id'],kwargs,action,receipts,verified


def files(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def test_pending_handoff_is_read_only_and_admission_inherits_v4_contract(prepared):
    parent,eid,kwargs,_,_,verified=prepared
    original=files(parent.root)
    handoff=inspect_handoff(parent.root,'test')
    assert handoff['status']=='pending_controller' and handoff['blocks_parent_dispatch']
    assert handoff['requests'][0]['request_id']==eid
    assert files(parent.root)==original
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    plan=json.loads((Path(result['child_root'])/'plan.json').read_text(encoding='utf-8'))
    assert plan['provenance']['runtime_identity_route']=={'version':'codex_session_v1'}
    work=plan['provenance']['controller_policy']['work']['extension']
    assert 'Need volume' in work['question'] and work['depends_on']==[]
    assert plan['tasks']['extension']['case']==kwargs['child_case']
    assert 'extension_handoff_policy' not in plan['provenance']
    assert verified[-1][1]['expected_artifact_sha256']=={capture.SESSION:'a'*64}
    before=files(parent.root)
    assert inspect_handoff(parent.root,'test')['status']=='child_running'
    assert files(parent.root)==before
    assert all(files(parent.root)[p]==sha for p,sha in original.items())


def test_v4_session_request_needs_newly_verified_runtime_identity(prepared):
    parent,eid,kwargs,_,receipts,_=prepared
    receipts[eid]['runtime_identity']['verified']=False
    with pytest.raises(AdmissionBlocked,match='runtime session identity unverified'):
        extension.decide_extension(parent.root,'test',eid,**kwargs)
    assert not (parent.root/'controller_extensions').exists()


def test_completed_child_report_is_bounded_cross_scope_context_and_parent_unchanged(prepared):
    parent,eid,kwargs,action,_,_=prepared
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    child=ResearchRuntime(result['child_root']);case=child.plan['tasks']['extension']['case']
    report={'outcome':'abstain','conclusion':'Generated fixture cannot establish market validity. '+('界'*7600),
        'evidence_ids':['input:'+digest(case)],'program_evidence_id':None,
        'limitations':['Generated sources only'],'next_step':'Inspect admissible sources',
        'falsifiers':['The original evidence changes'],
        'claims':[{'claim_id':'scope','kind':'descriptive','evidence_id':'input:'+digest(case),
                   'research_class':case['research_class'],'statement':'Only a generated fixture is supplied.'}]}
    final=action(child,'extension','submit_research_report',report)
    assert final['status']=='applied',final
    before=files(parent.root);history=parent.history('test')
    projection=inspect_handoff(parent.root,'test',max_bytes=4000)
    assert projection['status']=='ready_followup' and not projection['blocks_parent_dispatch']
    assert projection['requests'][0]['child_terminal']=='submitted'
    assert len(serial(projection).encode())<=4000
    assert files(parent.root)==before and parent.history('test')==history
    assert len(history)==2 and parent.status('test')['terminal'] is None
    full=inspect_handoff(parent.root,'test',max_bytes=64000)['requests'][0]['detail']['child_report']
    assert full['child_call_id']==final['id'] and full['public_result']==final['result']
    assert not full['public_result']['formal_target_success']


def test_child_invalid_final_returns_failure_instead_of_waiting_forever(prepared):
    parent,eid,kwargs,action,_,_=prepared
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    child=ResearchRuntime(result['child_root'])
    failed=action(child,'extension','submit_research_report',{'bad':'generated invalid final'})
    assert failed['status']=='failed'
    projection=inspect_handoff(parent.root,'test')
    row=projection['requests'][0]
    assert row['status']=='ready_followup' and row['child_terminal']=='invalid_final'
    assert row['detail']['child_report'] is None and not projection['blocks_parent_dispatch']


def test_derived_child_deadline_exhaustion_returns_without_ledger_write(prepared,monkeypatch):
    parent,eid,kwargs,_,_,_=prepared
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    before=files(parent.root)
    monkeypatch.setattr('quanta_agents.meta_v3.ledger.time.time',lambda:kwargs['deadline_epoch']+1)
    row=inspect_handoff(parent.root,'test')['requests'][0]
    assert row['status']=='ready_followup' and row['child_terminal'] is None
    assert row['child_mode']=='terminal_without_submission'
    assert files(parent.root)==before


@pytest.mark.parametrize('target,field,value',[
    ('intent','parent_task','foreign'),('intent','request_hash','b'*64),
    ('intent','parent_plan_hash','b'*64),('decision','child_root','C:/foreign/child')])
def test_foreign_intent_or_child_binding_is_rejected(prepared,target,field,value):
    parent,eid,kwargs,_,_,_=prepared
    extension.decide_extension(parent.root,'test',eid,**kwargs)
    path=parent.root/'controller_extensions'/eid/(target+'.json')
    body=json.loads(path.read_text(encoding='utf-8'));body[field]=value;path.write_text(serial(body),encoding='utf-8')
    with pytest.raises(AdmissionBlocked,match='binding drift'):
        inspect_handoff(parent.root,'test')


def test_unimplemented_decision_returns_to_parent_without_child(prepared):
    parent,eid,kwargs,_,_,_=prepared
    decision={**kwargs['decision'],'status':'needs_implementation','resource_bounds':None,
        'reason':'Generated unsupported field'}
    extension.decide_extension(parent.root,'test',eid,decision=decision)
    before=files(parent.root);projection=inspect_handoff(parent.root,'test')
    assert projection['status']=='needs_implementation' and not projection['blocks_parent_dispatch']
    assert files(parent.root)==before and not (parent.root/'controller_extensions'/eid/'stage').exists()


def test_unfinished_controller_intent_stays_pending_and_read_only(prepared,monkeypatch):
    parent,eid,kwargs,_,_,_=prepared
    original=extension.save_once
    def interrupted(path,value):
        if path.name=='decision.json':raise OSError('Generated interruption before committed decision')
        return original(path,value)
    monkeypatch.setattr(extension,'save_once',interrupted)
    with pytest.raises(OSError):extension.decide_extension(parent.root,'test',eid,**kwargs)
    before=files(parent.root)
    assert inspect_handoff(parent.root,'test')['status']=='pending_controller'
    assert files(parent.root)==before


def test_unknown_handoff_policy_rejected():
    assert validate_policy(None) is None
    with pytest.raises(AdmissionBlocked):validate_policy({'version':'unregistered'})
