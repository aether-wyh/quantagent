"""Generated model receipts with actual admission, account tools and shared costs."""
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

import pytest

from quanta_agents.meta_v3 import research_extension as extension
from quanta_agents.meta_v3 import study_registry as sr, tool_resources as tr
from quanta_agents.meta_v3.ledger import AdmissionBlocked, Ledger, digest, serial
from quanta_agents.meta_v3.runtime import ResearchRuntime, action_schema
from test_meta_v4_parent_program_context import prepare as base_prepare
from test_meta_v3_l2_research_entry import program


@pytest.fixture
def prepared(tmp_path, monkeypatch, request):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path/'registry.sqlite3')
    original = Ledger.create
    def registered(root, **kwargs):
        if Path(root).name == 'p':
            policy=kwargs['policy'];tasks=kwargs['tasks'];provenance=kwargs['provenance']
            trial={'id':'one','root':str(Path(root).resolve()),'case_hash':next(iter(tasks.values()))['case_hash'],
                   'architecture_hash':'b'*64,'repeat':1,'tasks_hash':digest(tasks),
                   'source_pins_hash':digest(provenance['source_pins']),'policy':asdict(policy),'duration_seconds':7200,
                   'tool_budget':{'actions':20,'candidates':4,'scan_cells':100000,'comparisons':64,
                                  'wall_ms':60000,'controller_cpu_ms':60000,'retained_output_bytes':50000000}}
            trial['tool_budget'].update(getattr(request,'param',{}))
            sr.freeze({'study_id':'descendants','trials':[trial]})
            binding=sr.claim('descendants','one')
            kwargs={**kwargs,'deadline_epoch':binding['deadline_epoch'],
                    'provenance':{**provenance,'study_trial':binding}}
        return original(root,**kwargs)
    monkeypatch.setattr(Ledger,'create',staticmethod(registered))
    return base_prepare.__wrapped__(tmp_path,monkeypatch)()


def child(f):
    result=extension.decide_extension(f.parent.root,'test',f.request_id,**f.kwargs)
    return ResearchRuntime(result['child_root'])


def reply(f,runtime,task_id,action,args,*,cost=20):
    tools=runtime._tools(task_id)
    intent=runtime.ledger.reserve(task_id,tools.menu(),lambda menu,*a:('Generated only',action_schema(menu)))
    response={'action':action,'arguments_json':json.dumps(args),'public_summary':'Generated fixture, no provider call',
              'self_review':dict.fromkeys(('assessment','uncertainty','next_step','falsifier'),'Fixture')}
    receipt={'response':response,'usage':{'input_tokens':cost-1,'output_tokens':1},
             'request_identity':{'intent_id':intent['intent_id']},'artifact_sha256':{'runtime_session.jsonl':'a'*64},
             'model_verified':False,'runtime_identity':{'verified':True,'level':'generated_fixture'}}
    f.receipts[intent['intent_id']]=receipt
    runtime.ledger.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    runtime._apply(intent['intent_id'])
    return runtime.ledger.call(intent['intent_id'])


def report(runtime,task_id):
    case=runtime.plan['tasks'][task_id]['case']
    return {'outcome':'abstain','conclusion':'Generated fixtures do not establish market validity.',
            'evidence_ids':['input:'+digest(case)],'program_evidence_id':None,
            'limitations':['Generated only'],'next_step':'Inspect real evidence','falsifiers':['Real evidence differs'],
            'claims':[{'claim_id':'scope','kind':'descriptive','evidence_id':'input:'+digest(case),
                       'research_class':case['research_class'],'text':'Generated scope only.'}]}


def test_child_actual_account_and_measurement_use_original_trial(prepared):
    f=prepared;runtime=child(f)
    p=program();p['target_weight_expression']='where(volume > 0, 0.05, 0)'
    result=reply(f,runtime,'extension','develop_strategy',{'program':p})
    assert result['status']=='applied',result
    assert result['result']['public']['raw_status']=='completed_mechanical'
    totals=sr.snapshot('descendants')
    assert len(totals['trials'])==1 and len(totals['calls'])==3 and totals['known_tokens']==60
    shared=tr.status(runtime.root)
    assert shared['used']==tr.status(f.parent.root)['used']
    assert shared['used']['candidates']==2 and shared['used']['actions']==3
    body=json.loads((runtime.root/'calls'/result['id']/'tool_measurement.json').read_text(encoding='utf-8'))
    assert body['tool_intent']['stage_plan_hash']==digest(runtime.plan)
    parent_plan=json.loads((f.parent.root/'plan.json').read_text(encoding='utf-8'))
    parent_measurement=json.loads((f.parent.root/'calls'/f.source_id/'tool_measurement.json').read_text(encoding='utf-8'))
    assert parent_measurement['tool_intent']['stage_plan_hash']==digest(parent_plan)
    assert runtime.plan['tasks']['extension']['case_hash']!=parent_plan['tasks']['test']['case_hash']
    assert runtime.plan['provenance']['study_trial']==parent_plan['provenance']['study_trial']
    assert totals['descendant_stages'][0]['trial_case_hash']==parent_plan['tasks']['test']['case_hash']
    assert totals['descendant_stages'][0]['child_case_hashes']=={'extension':runtime.plan['tasks']['extension']['case_hash']}
    assert next(x for x in totals['call_stage_bindings'] if x['id']==result['id'])['root']==sr._root(runtime.root)


def test_unknown_child_model_reserve_blocks_parent_and_other_scopes(prepared):
    f=prepared;runtime=child(f)
    intent=runtime.ledger.reserve('extension',runtime._tools('extension').menu(),lambda menu,*a:('Fixture',action_schema(menu)))
    runtime.ledger.unknown(intent['intent_id'],'Generated uncertain dispatch')
    assert sr.snapshot('descendants')['unresolved_reserve']==80000
    assert f.parent.status('test')['mode']=='blocked'
    with pytest.raises(AdmissionBlocked):
        f.parent.reserve('test',('inspect_inputs','submit_research_report'),lambda *a:pytest.fail('Cannot construct another request'))


@pytest.mark.parametrize('prepared',[{'candidates':2}],indirect=True)
def test_parent_and_child_cannot_refresh_candidate_quota(prepared):
    f=prepared;runtime=child(f)
    p=program();p['target_weight_expression']='where(volume > 0, 0.05, 0)'
    assert reply(f,runtime,'extension','develop_strategy',{'program':p})['status']=='applied'
    assert tr.status(runtime.root)['used']['candidates']==2
    assert 'develop_strategy' not in runtime._tools('extension').menu()
    assert 'develop_strategy' not in ResearchRuntime(f.parent.root)._tools('test').menu()


def test_shared_call_ceiling_keeps_a_final_for_parent_and_child(prepared):
    f=prepared;runtime=child(f)
    for _ in range(2):
        assert reply(f,runtime,'extension','inspect_inputs',{'table':'fields','offset':0,'limit':32})['status']=='applied'
    assert runtime.ledger.status('extension')['mode']=='close_only'
    assert f.parent.status('test')['mode']=='close_only'
    assert reply(f,runtime,'extension','submit_research_report',report(runtime,'extension'))['status']=='applied'
    parent=ResearchRuntime(f.parent.root)
    assert reply(f,parent,'test','submit_research_report',report(parent,'test'))['status']=='applied'
    assert len(sr.snapshot('descendants')['calls'])==6
    assert f.parent.status('test')['terminal']=='submitted'
    assert runtime.ledger.status('extension')['terminal']=='submitted'


def test_actual_child_token_overrun_is_retained_and_blocks_parent(prepared):
    f=prepared;runtime=child(f)
    reply(f,runtime,'extension','inspect_inputs',{'table':'fields','offset':0,'limit':32},cost=2500000)
    assert sr.snapshot('descendants')['known_tokens']==2500040
    assert f.parent.status('test')['mode']=='blocked'


def test_shorter_child_clock_also_protects_tool_closing_reserve(prepared,monkeypatch):
    f=prepared
    f.kwargs['deadline_epoch']=extension.time.time()+5000
    runtime=child(f)
    monkeypatch.setattr(extension.time,'time',lambda:f.kwargs['deadline_epoch']-3599)
    assert tr.status(runtime.root)['closing_time_reached']
    assert not tr.status(f.parent.root)['closing_time_reached']
    assert runtime._tools('extension').menu()==('submit_research_report',)


@pytest.mark.parametrize('fault',['binding','case','clock'])
def test_descendant_cannot_downgrade_or_change_its_registered_scope(prepared,fault):
    f=prepared;runtime=child(f);plan=runtime.plan
    if fault=='binding':
        plan['provenance'].pop('study_trial');plan['provenance'].pop('study_descendant')
    elif fault=='case':
        plan['tasks']['extension']['case']['initial_cash']='1.00'
        plan['tasks']['extension']['case_hash']=digest(plan['tasks']['extension']['case'])
    else:plan['deadline_epoch']+=100
    (runtime.root/'plan.json').write_text(serial(plan),encoding='utf-8')
    with sqlite3.connect(runtime.ledger.path) as db:
        db.execute('UPDATE stage SET plan=?,plan_hash=?',(serial(plan),digest(plan)))
    with pytest.raises(AdmissionBlocked,match='descendant'):
        runtime.ledger.status('extension')


@pytest.mark.parametrize('fault',['clock','reserve'])
def test_extension_cannot_renew_trial_deadline_or_weaken_reserves(prepared,monkeypatch,fault):
    f=prepared
    parent_plan=json.loads((f.parent.root/'plan.json').read_text(encoding='utf-8'))
    if fault=='clock':
        current=extension.time.time
        monkeypatch.setattr(extension.time,'time',lambda:current()+2)
        f.kwargs['deadline_epoch']=parent_plan['deadline_epoch']+1
        reason='clock cannot be renewed'
    else:
        from dataclasses import replace
        f.kwargs['policy']=replace(f.kwargs['policy'],closing_seconds=1800)
        reason='cannot exceed or weaken'
    with pytest.raises(AdmissionBlocked,match=reason):
        child(f)
    with sr._db() as db:
        assert db.execute('SELECT count(*) FROM trials').fetchone()[0]==1
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='trial_descendants'").fetchone():
            assert db.execute('SELECT count(*) FROM trial_descendants').fetchone()[0]==0


def test_native_parent_and_descendant_share_one_frozen_process_job(tmp_path,monkeypatch):
    import hashlib
    from quanta_agents.meta_v3 import process_envelope as pe
    from quanta_agents.meta_v3.closing import ClosingPolicy
    from quanta_agents.meta_v3.runtime import source_pins
    from test_meta_v3_research_iteration import configured
    from test_meta_v4_controller import contracts
    monkeypatch.setattr(sr,'REGISTRY',tmp_path/'native_registry.sqlite3')
    case=configured();task={'case':case,'case_hash':digest(case),'idea':'Generated native inheritance','documents':[]}
    tasks={'test':task};root=tmp_path/'native';policy=ClosingPolicy(task_calls=8,stage_calls=8)
    entry=Path(__file__).parent/'helpers/meta_v4_descendant_fixture.py'
    envelope={'version':pe.VERSION,'entrypoint':str(entry.resolve()),
              'entrypoint_sha256':hashlib.sha256(entry.read_bytes()).hexdigest(),
              'arguments':['--root',str(root),'--registry',str(sr.REGISTRY)],
              'budget':{'launches':2,'cpu_ms':60000,'io_transfer_bytes':1073741824,
                        'closing_cpu_ms':1000,'closing_io_transfer_bytes':1048576}}
    trial={'id':'one','root':str(root),'case_hash':digest(case),'architecture_hash':'a'*64,'repeat':1,
           'tasks_hash':digest(tasks),'source_pins_hash':digest(source_pins()),'policy':asdict(policy),'duration_seconds':7200,
           'tool_budget':{'actions':20,'candidates':4,'scan_cells':100000,'comparisons':64,
                          'wall_ms':60000,'controller_cpu_ms':60000,'retained_output_bytes':50000000},
           'process_envelope':envelope}
    sr.freeze({'study_id':'native_descendants','trials':[trial]})
    ledger=sr.create_stage(root,'native_descendants','one',policy=policy,tasks=tasks,duration_seconds=7200,
                           provenance={'source_pins':source_pins(),'fixture_only':True,
                                       'controller_policy':contracts(['test']),
                                       'runtime_identity_route':{'version':'codex_session_v1'}})
    receipt=pe.supervise(ledger.root)
    assert receipt['exit_code']==0,(ledger.root/'process_runs/1/worker.log').read_text(encoding='utf-8',errors='replace')
    proof=json.loads((ledger.root/'native_descendant_validation.json').read_text(encoding='utf-8'))
    child_root=Path(proof['child_root'])
    child_probe=json.loads((child_root/'native_child_probe.json').read_text(encoding='utf-8'))
    assert proof['actual_model_calls']==child_probe['actual_model_calls']==0
    assert len(proof['study']['trials'])==1 and len(proof['study']['calls'])==5
    assert proof['study']['known_tokens']==100
    assert receipt['metrics']['active_processes']==0 and receipt['metrics']['total_processes']>=2
    assert child_probe['process']['launches_used']==1
    assert pe.status(child_root)['known_finished']==pe.status(ledger.root)['known_finished']
    assert pe.status(child_root)['launches_used']==1
    measurement=json.loads((child_root/'calls'/child_probe['call_id']/'tool_measurement.json').read_text(encoding='utf-8'))
    assert measurement['tool_intent']['stage_plan_hash']==digest(json.loads((child_root/'plan.json').read_text(encoding='utf-8')))
    with pytest.raises(AdmissionBlocked,match='single registered live process'):
        pe.public_status(child_root)
    launch,_=pe.reserve(child_root)
    assert launch['slot']==2 and sr._root(launch['root'])==sr._root(ledger.root)
    assert launch['envelope']==envelope
    assert pe.status(ledger.root)['launches_used']==pe.status(child_root)['launches_used']==2
    with pytest.raises(AdmissionBlocked,match='unresolved process run'):
        pe.reserve(ledger.root)


def test_uncommitted_descendant_decision_blocks_direct_reservation_and_reconciles(prepared,monkeypatch):
    f=prepared;original=extension.save_once
    def interrupted(path,value):
        if path.name=='decision.json':raise OSError('Generated interruption after child creation')
        return original(path,value)
    with monkeypatch.context() as patch:
        patch.setattr(extension,'save_once',interrupted)
        with pytest.raises(OSError):child(f)
    root=f.parent.root/'controller_extensions'/f.request_id/'stage'
    runtime=ResearchRuntime(root)
    with pytest.raises(AdmissionBlocked,match='decision incomplete'):
        runtime.ledger.reserve('extension',runtime._tools('extension').menu(),lambda menu,*a:('Fixture',action_schema(menu)))
    assert len(sr.snapshot('descendants')['calls'])==2
    assert child(f).root==root
    assert reply(f,runtime,'extension','inspect_inputs',{'table':'fields','offset':0,'limit':32})['status']=='applied'
