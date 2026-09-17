"""Admission/recovery tests use labelled saved responses, never a paid model."""
from copy import deepcopy
import hashlib
import json
import time

import pytest

from quanta_agents.meta_v3 import research_extension as extension
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import AdmissionBlocked,Ledger,digest
from quanta_agents.meta_v3.runtime import ResearchRuntime,source_pins
from test_meta_v3_research_entry import action
from test_meta_v3_research_iteration import configured
from test_meta_v3_l2_research_entry import program


def prepared(tmp_path,monkeypatch):
    data=configured();task={'case':data,'case_hash':digest(data),'idea':'Diagnose using available evidence','documents':[]}
    ledger=Ledger.create(tmp_path/'parent',policy=ClosingPolicy(task_calls=6,stage_calls=6),tasks={'test':task},
        deadline_epoch=time.time()+7200,provenance={'source_pins':source_pins(),'fixture_only':True})
    runtime=ResearchRuntime(ledger.root)
    first=action(runtime,task,'inspect_inputs',{'table':'coverage','offset':0,'limit':32})
    request=action(runtime,task,'request_research_extension',{'evidence_ids':[first['id']],
        'problem':'Need a new causal field to distinguish price level from volume effects','request_kind':'data',
        'requested_fields':['volume'],
        'specification':'Generated engineering volume field','expected_information_gain':'Test capability path, no alpha',
        'requested_resource_bounds':{'symbols':1,'sessions':5,'model_calls':4,'download_bytes':0,'wall_seconds':7200}})
    receipt=ledger.call(request['id'])['receipt']
    monkeypatch.setattr(module('meta.codex_gateway'),'verify_saved_completion',lambda *a,**k:receipt)
    child=deepcopy(data)
    child['decision_fixture']['fields'].append({'name':'volume','unit':'engineering shares'})
    rows=deepcopy(child['decision_fixture']['field_rows'])
    for row in rows:row.update(field='volume',value=100)
    child['decision_fixture']['field_rows'].extend(rows)
    proof=tmp_path/'generated_source.json';proof.write_text(json.dumps(child),encoding='utf-8')
    child['evidence_sources']=[{'path':str(proof),'sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}]
    decision={'status':'ready','reason':'Generated engineering data are already implemented; no market claim',
        'asset_contract':'a_share_cash_equity','resource_bounds':{
            'symbols':1,'sessions':5,'model_calls':4,'download_bytes':0,'wall_seconds':7200},
        'exposure_statement':'Generated engineering example only; parent evidence exposed; no OOS.',
        'source_admissions':[{'path':str(proof),'role':'engineering','partition':'generated_fixture','content_date_range':None}]}
    kwargs={'decision':decision,'child_case':child,'policy':ClosingPolicy(task_calls=4,stage_calls=4,stage_tokens=600000),
        'deadline_epoch':time.time()+7000}
    return ledger,request['id'],kwargs


def test_ready_child_executes_new_field_and_preserves_parent_and_final_budget(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    original=(parent.root/'plan.json').read_bytes();history=parent.history('test')
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    runtime=ResearchRuntime(result['child_root']);runtime.verify_inputs()
    assert result['child_budget_registered'] and result['model_calls_executed_by_admission']==0
    assert not result['genuine_model_extension_use_verified']
    assert runtime.ledger.status('extension')['known_tokens']==0
    task=runtime.plan['tasks']['extension'];tools=runtime._tools('extension')
    p=program();p['target_weight_expression']='where(volume > 0, 0.05, 0)'
    evaluated=tools.execute('engineering','develop_strategy',{'program':p})
    assert evaluated['public']['raw_status']=='completed_mechanical'
    assert runtime.plan['model']=='gpt-6-astra' and runtime.plan['effort']=='xhigh'
    assert task['case_hash']!=json.loads(original)['tasks']['test']['case_hash']
    assert parent.history('test')==history and (parent.root/'plan.json').read_bytes()==original
    assert extension.decide_extension(parent.root,'test',eid,**kwargs)==result
    assert not runtime.ledger.history('extension') # Direct engineering tool use, no forged model receipt.


def test_crash_after_child_creation_blocks_runtime_and_reconciles_without_recreation(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch);original_save=extension.save_once
    def interrupted(path,value):
        if path.name=='decision.json':raise OSError('engineering injected interruption')
        return original_save(path,value)
    monkeypatch.setattr(extension,'save_once',interrupted)
    with pytest.raises(OSError):extension.decide_extension(parent.root,'test',eid,**kwargs)
    child=parent.root/'controller_extensions'/eid/'stage'
    before=(child/'plan.json').read_bytes()
    with pytest.raises(AdmissionBlocked,match='admission incomplete'):ResearchRuntime(child).verify_inputs()
    monkeypatch.setattr(extension,'save_once',original_save)
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    assert result['status']=='ready' and (child/'plan.json').read_bytes()==before
    ResearchRuntime(child).verify_inputs()
    assert Ledger(child).history('extension')==[]


@pytest.mark.parametrize('change,reason',[
    ('capital','capital or execution contract'),('fees','capital or execution contract'),
    ('calls','model calls exceed'),('assets','unsupported asset'),('raw','case source drift')])
def test_scope_grant_cannot_cheapen_execution_or_invent_resources(tmp_path,monkeypatch,change,reason):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    if change=='capital':kwargs['child_case']['initial_cash']='10000.00'
    if change=='fees':kwargs['child_case']['l2_execution']['account_plan']['fees']['commission_rate']='0'
    if change=='calls':kwargs['policy']=ClosingPolicy(task_calls=5,stage_calls=5,stage_tokens=600000)
    if change=='assets':kwargs['decision']['asset_contract']='futures'
    if change=='raw':
        raw=tmp_path/'raw.json';raw.write_text('[]')
        kwargs['child_case']['raw_source_bindings']['source_artifacts']=[{'root':str(tmp_path),
            'rows_file':raw.name,'rows_sha256':'f'*64,'manifest_file':raw.name,'manifest_sha256':'f'*64}]
        kwargs['decision']['source_admissions'].append({'path':str(raw),'role':'engineering','partition':'generated_fixture','content_date_range':None})
    with pytest.raises(AdmissionBlocked,match=reason):extension.decide_extension(parent.root,'test',eid,**kwargs)
    assert not (parent.root/'controller_extensions'/eid/'stage').exists()


def test_unavailable_capability_is_recorded_without_child_or_budget(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    decision={**kwargs['decision'],'status':'needs_implementation','asset_contract':'futures',
        'resource_bounds':None,'reason':'No contract multiplier, margin, roll or settlement implementation'}
    result=extension.decide_extension(parent.root,'test',eid,decision=decision)
    assert result['child_root'] is None and not result['child_budget_registered']
    assert result['model_calls_executed_by_admission']==0
    with pytest.raises(AdmissionBlocked,match='previous admission intent differs'):
        extension.decide_extension(parent.root,'test',eid,**kwargs)


def test_changed_parent_evidence_and_unresolved_calls_block_admission(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    result=extension.decide_extension(parent.root,'test',eid,**kwargs)
    first=parent.history('test')[0]['id'];path=parent.root/'tools/test'/first/'artifact.json'
    old=path.read_bytes();path.write_text('{}')
    with pytest.raises(AdmissionBlocked,match='parent evidence drift'):ResearchRuntime(result['child_root']).verify_inputs()
    path.write_bytes(old)
    parent.reserve('test',('inspect_inputs','submit_research_report'),lambda *a:('fixture',{}))
    with pytest.raises(AdmissionBlocked,match='unresolved parent exposure'):
        extension.decide_extension(parent.root,'test',eid,**kwargs)
