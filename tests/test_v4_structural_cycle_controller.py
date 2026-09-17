"""Controller admission/accounting counterexamples; no supplier or strategy run."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import serial
from quanta_agents.meta_v3.source_admission import admit_paths, source_paths


@pytest.fixture
def governor(tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('v4_cycle_governor',ROOT/'scripts/run_v4_structural_cycle.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=tmp_path/'r';root.mkdir()
    monkeypatch.setattr(module,'SCOPE',root)
    monkeypatch.setattr(module,'event',lambda *a,**k:None)
    monkeypatch.setattr(module,'update_gui',lambda *a,**k:None)
    return module


def test_preserved_source_admissions_cover_every_path_without_broadening_raw_dates(governor,tmp_path):
    case=json.loads((ROOT/'experiment_traces/meta_framework_v3/year_inputs_001/case.json').read_text(encoding='utf-8'))
    manifest=tmp_path/'derivation_manifest.json';manifest.write_text('{}',encoding='utf-8')
    prepared={'source_admissions':[{'path':str(manifest),'role':'development_market_data',
        'partition':'exposed_2017_2021','content_date_range':['2019-01-02','2019-12-31']}]}
    child=deepcopy(case);child['evidence_sources'].append({'path':str(manifest),'sha256':'a'*64})
    declarations=governor.admissions(case,prepared)
    result=admit_paths(child,declarations)
    assert not result['content_verified']
    assert len(declarations)==len(source_paths(child))
    assert {str(Path(x['path']).resolve()) for x in declarations}==set(source_paths(child))
    for row in declarations:
        if source_paths(child)[str(Path(row['path']).resolve())]=='market':
            assert row['role']=='development_market_data'
            assert row['content_date_range']==['2017-01-01','2021-12-31']


@pytest.mark.parametrize('change',[
    {'requested_fields':['vwap']},{'request_kind':'benchmark','requested_fields':None},
    {'symbols':0},{'sessions':243},{'model_calls':0},{'wall_seconds':119}])
def test_out_of_service_request_records_denial_without_preparation_or_child_budget(governor,monkeypatch,change):
    body={'request_kind':'data','requested_fields':['open'],
        'requested_resource_bounds':{'symbols':1,'sessions':244,'model_calls':10,'wall_seconds':3600,'download_bytes':0}}
    for key,value in change.items():
        if key in body['requested_resource_bounds']:body['requested_resource_bounds'][key]=value
        else:body[key]=value
    plan={'deadline_epoch':governor.time.time()+7200,'policy':{'closing_seconds':600},
        'provenance':{'extension_service_policy':{'maximum_child_wall_seconds':3600,
            'maximum_child_model_calls':10,'maximum_child_tokens':600000,'fields':['open','high','low']}}}
    monkeypatch.setattr(governor,'Ledger',lambda *a:object())
    monkeypatch.setattr(governor,'_parent_request',lambda *a:(plan,{'case':{}},{'request':body},[],[]))
    monkeypatch.setattr(governor,'prepare',lambda *a:pytest.fail('Denied request cannot prepare new material'))
    decisions=[]
    def decide(*args,**kwargs):
        decisions.append(kwargs)
        return {'child_root':None,**kwargs['decision']}
    monkeypatch.setattr(governor,'decide_extension',decide)
    result=governor.grant_request(plan,'ap_001_generated')
    assert result['status']=='needs_implementation' and result['resource_bounds'] is None
    assert len(decisions)==1 and set(decisions[0])=={'decision'}


def test_completed_child_is_included_when_controller_reenters_and_parent_finishes(governor,monkeypatch):
    """A fresh controller process must not forget paid child work in memory."""
    plan={'provenance':{'controller_scripts':{},'extension_service_policy':{
        'version':'saved_ohlc_service_v1','maximum_extensions':1,'maximum_total_model_calls':24}}}
    (governor.SCOPE/'plan.json').write_text(serial(plan),encoding='utf-8')
    request_id='ap_002_generated';folder=governor.SCOPE/'controller_extensions'/request_id
    child=folder/'stage';child.mkdir(parents=True)
    decision={'status':'ready','child_root':str(child)}
    (folder/'decision.json').write_text(serial(decision),encoding='utf-8')
    handoff={'status':'ready_followup','blocks_parent_dispatch':False,'requests':[{
        'request_id':request_id,'status':'ready_followup','detail':{'child_root':str(child)}}]}
    monkeypatch.setattr(governor,'inspect_handoff',lambda *a,**k:handoff)
    monkeypatch.setattr(governor,'Ledger',lambda *a:SimpleNamespace(status=lambda *a:{'terminal':'submitted'}))
    monkeypatch.setattr(governor,'ResearchRuntime',lambda *a:SimpleNamespace(run=lambda:None))
    audited=[]
    def audit(stages):
        audited.extend(stages)
        return {'research_model_calls':12,'research_known_tokens':120}
    monkeypatch.setattr(governor,'audit',audit)
    governor.main()
    assert (child,'extension') in audited,'Previously completed child calls and costs were omitted at controller reentry'


def test_large_request_is_capped_by_service_and_parent_closing_time(governor,monkeypatch):
    case=json.loads((ROOT/'experiment_traces/meta_framework_v3/year_inputs_001/case.json').read_text(encoding='utf-8'))
    case['research_policy']={'version':'structural_research_v1','action_limits':{'request_research_extension':1}}
    original=deepcopy(case)
    body={'request_kind':'data','requested_fields':['open','high'],
        'requested_resource_bounds':{'symbols':99,'sessions':9999,'model_calls':500,'wall_seconds':10000,'download_bytes':1000000}}
    service={'maximum_child_wall_seconds':3600,'maximum_child_model_calls':10,
        'maximum_child_tokens':600000,'fields':['open','high','low']}
    plan={'deadline_epoch':2500,'policy':{'closing_seconds':600},
        'provenance':{'extension_service_policy':service}}
    monkeypatch.setattr(governor.time,'time',lambda:1000)
    monkeypatch.setattr(governor,'Ledger',lambda *a:object())
    monkeypatch.setattr(governor,'_parent_request',lambda *a:(plan,{'case':case},{'request':body},[],[]))
    monkeypatch.setattr(governor,'prepare',lambda *a:{'child_case':deepcopy(case),'source_admissions':[]})
    captured=[]
    def decide(*args,**kwargs):
        captured.append(kwargs)
        return kwargs['decision']
    monkeypatch.setattr(governor,'decide_extension',decide)
    result=governor.grant_request(plan,'ap_002_generated')
    assert result['status']=='ready' and result['resource_bounds']=={
        'symbols':1,'sessions':244,'model_calls':10,'download_bytes':0,'wall_seconds':900}
    grant=captured[0]
    assert grant['policy'].stage_calls==grant['policy'].task_calls==10
    assert grant['policy'].stage_tokens==grant['policy'].task_tokens==600000
    assert grant['deadline_epoch']==1898 and grant['deadline_epoch']<=plan['deadline_epoch']-600
    assert grant['child_case']['research_policy']['action_limits']['request_research_extension']==0
    assert case==original,'Child grant must not change the original parent case'


def test_audit_accepts_failed_application_shape_and_keeps_its_cost(governor,monkeypatch):
    root=governor.SCOPE
    receipt={'response':{'action':'develop_strategy'},'usage':{'input_tokens':13,'output_tokens':7},
        'artifact_sha256':{},'runtime_identity':{'verified':True,'level':'generated_engineering_fixture'}}
    call={'id':'ap_001_generated','status':'failed','known_tokens':20,'receipt':receipt,
        'intent':{'prompt_hash':'a'*64,'schema':{}},
        'result':{'error':'Generated application failure after a settled response','formal_target_success':False}}
    state={'terminal':'invalid_final','calls':[{'id':call['id']}],
        'known_tokens':20,'unknown_or_pending_reserve':0}
    runtime=SimpleNamespace(verify_inputs=lambda:None,
        ledger=SimpleNamespace(status=lambda *a:state,call=lambda *a:call),
        gateway_module=SimpleNamespace(verify_saved_completion=lambda *a,**k:receipt))
    monkeypatch.setattr(governor,'ResearchRuntime',lambda *a:runtime)
    saved=[];monkeypatch.setattr(governor,'save_once',lambda path,value:saved.append((path,value)))
    result=governor.audit([(root,governor.TASK)])
    assert result['research_model_calls']==1 and result['research_known_tokens']==20
    assert result['stages'][0]['calls'][0]['result']==call['result']
    assert result['stages'][0]['calls'][0]['status']=='failed' and len(saved)==1
