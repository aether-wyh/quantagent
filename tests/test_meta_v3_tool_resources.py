"""Generated registered tool producer checks, with model/account dispatch forbidden."""
from copy import deepcopy
from dataclasses import asdict
import json
import shutil
import sqlite3

import pytest

from quanta_agents.meta_v3 import study_registry as sr, tool_resources as tr, research_batch
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import Ledger, AdmissionBlocked, digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3.runtime import ResearchRuntime, action_schema, make_prompt, source_pins
from test_meta_v3_batch_research import configured, declaration


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path/'canonical.sqlite3')
    def forbidden(*args, **kwargs): pytest.fail('No actual model or account worker permitted')
    monkeypatch.setattr(research_batch.subprocess, 'Popen', forbidden)
    monkeypatch.setattr(module('meta.codex_gateway').CodexGateway, 'run', forbidden)
    def create(**overrides):
        case = configured(tmp_path/'case')
        task = {'case':case,'case_hash':digest(case),'idea':'Generated resource check; abstain unless supported.','documents':[]}
        tasks = {'test':task, 'other':deepcopy(task)}
        budget = {'actions':20,'candidates':8,'scan_cells':20000,'comparisons':64,
                  'wall_ms':60000,'controller_cpu_ms':60000,'retained_output_bytes':5000000}
        budget.update(overrides)
        policy = ClosingPolicy(task_calls=10,stage_calls=20)
        trial = {'id':'one','root':str(tmp_path/'stage'),'case_hash':digest(case),'architecture_hash':'b'*64,
            'repeat':1,'tasks_hash':digest(tasks),'source_pins_hash':digest(source_pins()),
            'policy':asdict(policy),'duration_seconds':7200,'tool_budget':budget}
        sr.freeze({'study_id':'tools','trials':[trial]})
        job = sr.create_stage(tmp_path/'stage','tools','one',policy=policy,tasks=tasks,
            duration_seconds=7200,provenance={'source_pins':source_pins()})
        return ResearchRuntime(job.root), task
    return create


def reply(runtime, task, name, args, *, task_id='test', apply=True, stale_menu=False):
    tools = runtime._tools(task_id)
    menu = ('inspect_inputs','develop_strategy','submit_research_report') if stale_menu else tools.menu()
    history = runtime.ledger.history(task_id)
    build = lambda actions,state,decision: (make_prompt(task,tools,history,actions,state,decision,runtime.plan['policy']),action_schema(actions))
    intent = runtime.ledger.reserve(task_id,menu,build)
    response = {'action':name,'arguments_json':json.dumps(args),'public_summary':'Explicit generated resource fixture',
                'self_review':dict.fromkeys(('assessment','uncertainty','next_step','falsifier'),'Generated only')}
    module('meta.codex_gateway')._validate_output(response,intent['schema'])
    receipt = {'response':response,'usage':{'input_tokens':10,'output_tokens':10},
               'request_identity':{'intent_id':intent['intent_id']},'artifact_sha256':{}}
    runtime.ledger.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    if apply: runtime._apply(intent['intent_id'])
    return runtime.ledger.call(intent['intent_id'])


def test_failed_ordinary_attempt_and_second_task_share_candidate_gate(setup):
    runtime, task = setup(candidates=1)
    failed = reply(runtime,task,'develop_strategy',{'program':{}})
    assert failed['status']=='failed'
    state = tr.status(runtime.root)
    assert state['used']['candidates']==1 and state['used']['scan_cells']==144
    assert state['entries'][0]['outcome']=='raised'
    assert 'develop_strategy' not in runtime._tools('other').menu()
    second = reply(runtime,task,'develop_strategy',{'program':{}},task_id='other',stale_menu=True)
    assert second['status']=='failed' and 'resource budget exhausted' in second['result']['error']
    assert len(tr.status(runtime.root)['entries'])==1
    assert sr.snapshot('tools')['known_tokens']==40  # Rejected tool still paid its generated model receipt.


def test_horizon_producer_reserves_before_numeric_work_and_records_measurements(setup,monkeypatch):
    runtime, task = setup()
    original = ResearchTools._frames
    def observe(tools):
        current = tr.status(tools.root)
        assert current['unresolved']==1
        assert current['used']['comparisons']==8 and current['used']['scan_cells']==336
        return original(tools)
    monkeypatch.setattr(ResearchTools,'_frames',observe)
    result = reply(runtime,task,'diagnose_horizons',{'filter_expression':'close > 0','feature_expression':'close','horizons':[1,2]})
    assert result['status']=='applied'
    state = tr.status(runtime.root)
    assert state['unresolved']==0 and state['used']['wall_ms']>0 and state['used']['retained_output_bytes']>0
    assert runtime._tools('test').contract()['trial_tool_resources']['used']==state['used']


def test_invalid_duplicate_batch_slots_reserved_once_through_execute_and_inspect(setup):
    runtime, task = setup()
    args = declaration((.1,.1))
    args['families'][0]['program_template']['factors']=[{'name':'bad','expression':'missing_field'}]
    reg = reply(runtime,task,'register_batch',args)
    assert reg['status']=='applied' and reg['result']['public']['validation_failures']==2
    state = tr.status(runtime.root)
    assert state['used']['candidates']==2 and state['used']['scan_cells']==144 and state['used']['comparisons']==1
    executed = reply(runtime,task,'execute_batch',{'registration_evidence_id':reg['id']})
    assert executed['status']=='applied'
    inspected = reply(runtime,task,'inspect_batch',{'registration_evidence_id':reg['id'],'candidate_id':None,'table':'candidates','offset':0,'limit':32})
    assert inspected['status']=='applied'
    after = tr.status(runtime.root)
    assert after['used']['actions']==3 and after['used']['candidates']==2 and after['used']['scan_cells']==144
    assert not list(runtime.root.rglob('worker_result.json'))


def test_output_overrun_is_retained_and_final_remains_available(setup):
    runtime, task = setup(retained_output_bytes=1)
    one = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    state = tr.status(runtime.root)
    assert state['used']['retained_output_bytes']>1
    assert runtime._tools('test').menu()==('submit_research_report',)
    final = reply(runtime,task,'submit_research_report',{'outcome':'abstain','conclusion':'Generated input cannot establish an edge.',
        'evidence_ids':[one['id']],'program_evidence_id':None,'limitations':['Generated resource admission check.'],
        'next_step':'Complete real evidence.','falsifiers':['New valid evidence differs.']})
    assert final['status']=='applied' and runtime.ledger.status('test')['terminal']=='submitted'
    assert tr.status(runtime.root)['used']==state['used']


def test_interrupted_application_keeps_unknown_and_forbids_replay(setup,monkeypatch):
    runtime, task = setup()
    call = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def interrupted(*args): raise KeyboardInterrupt('Generated interruption before measurement commit')
    monkeypatch.setattr(ResearchTools,'_execute',interrupted)
    with pytest.raises(KeyboardInterrupt): runtime._apply(call['id'])
    assert tr.status(runtime.root)['unresolved']==1
    with pytest.raises(AdmissionBlocked,match='unresolved tool'):
        runtime._tools('test').execute(call['id'],'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    assert len(tr.status(runtime.root)['entries'])==1


def test_settlement_interruption_retains_output_and_unknown_without_reexecution(setup,monkeypatch):
    runtime, task = setup()
    def interrupted(*args): raise RuntimeError('Generated measurement commit interruption')
    monkeypatch.setattr(tr,'_settle',interrupted)
    one = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    assert one['status']=='failed' and tr.status(runtime.root)['unresolved']==1
    artifact = runtime.root/'tools/test'/one['id']/'artifact.json'
    original = artifact.read_bytes()
    runtime._apply(one['id'])
    assert artifact.read_bytes()==original and len(tr.status(runtime.root)['entries'])==1


def test_registry_loss_between_tool_check_and_reserve_cannot_skip_meter(setup,monkeypatch):
    runtime, task = setup()
    one = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    original = tr._reserve
    preserved = sr.REGISTRY.with_suffix('.preserved')
    def lose(*args):
        sr.REGISTRY.rename(preserved)
        return original(*args)
    monkeypatch.setattr(tr,'_reserve',lose)
    runtime._apply(one['id'])
    failed = runtime.ledger.call(one['id'])
    assert failed['status']=='failed' and 'registry missing' in failed['result']['error']
    with sqlite3.connect(preserved.as_uri()+'?mode=ro',uri=True) as db:
        assert db.execute('SELECT count(*) FROM tool_actions').fetchone()[0]==0
    assert not (runtime.root/'tools/test'/one['id']).exists()


def test_copied_stage_cannot_use_tool_budget_at_new_root(setup,tmp_path):
    runtime, _ = setup()
    copied = tmp_path/'copied';shutil.copytree(runtime.root,copied)
    with pytest.raises(AdmissionBlocked,match='copied outside'): tr.status(copied)
    assert tr.status(runtime.root)['used']['actions']==0


def test_trial_deadline_protects_existing_closing_time(setup,monkeypatch):
    runtime, _ = setup()
    monkeypatch.setattr(tr.time,'time',lambda:runtime.plan['deadline_epoch']-100)
    assert tr.status(runtime.root)['closing_time_reached']
    assert runtime._tools('test').menu()==('submit_research_report',)


def test_invalid_budget_rejected_before_creating_registry(setup):
    with pytest.raises(AdmissionBlocked,match='bounded tool resource'): setup(candidates=True)
    assert not sr.REGISTRY.exists()


def test_locally_rewritten_response_cannot_spend_canonical_tool_budget(setup):
    runtime, task = setup()
    call = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    changed = deepcopy(call['receipt'])
    changed['response']['arguments_json'] = json.dumps({'table':'coverage','offset':0,'limit':32})
    with sqlite3.connect(runtime.ledger.path) as db:
        db.execute('UPDATE calls SET receipt=? WHERE id=?',(json.dumps(changed),call['id']))
    runtime._apply(call['id'])
    failed = runtime.ledger.call(call['id'])
    assert failed['status']=='failed' and 'canonical receipt' in failed['result']['error']
    assert tr.status(runtime.root)['entries']==[]
    assert not (runtime.root/'tools/test'/call['id']).exists()
