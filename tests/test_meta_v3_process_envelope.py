"""Actual Windows jobs; generated bounded workloads and no supplier calls."""
from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import pytest

from quanta_agents.meta_v3 import process_envelope as pe, study_registry as sr
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest
from quanta_agents.meta_v3.runtime import source_pins
from test_meta_v3_batch_research import configured


@pytest.fixture
def setup_process(tmp_path,monkeypatch):
    monkeypatch.setattr(sr,'REGISTRY',tmp_path/'canonical.sqlite3')
    def create(mode='child',*,freeze=True,**overrides):
        case=configured(tmp_path/'generated')
        task={'case':case,'case_hash':digest(case),'idea':'Generated process/accounting validation only','documents':[]}
        tasks={'test':task};root=tmp_path/'stage';policy=ClosingPolicy(task_calls=7,stage_calls=7)
        entry=Path(__file__).parent/'helpers/meta_v3_process_fixture.py'
        budget={'launches':2,'cpu_ms':60000,'io_transfer_bytes':1073741824,'closing_cpu_ms':1000,'closing_io_transfer_bytes':1048576}
        budget.update(overrides)
        envelope={'version':pe.VERSION,'entrypoint':str(entry.resolve()),'entrypoint_sha256':hashlib.sha256(entry.read_bytes()).hexdigest(),
            'arguments':['--root',str(root),'--registry',str(sr.REGISTRY),'--mode',mode],'budget':budget}
        tool_budget={'actions':20,'candidates':8,'scan_cells':20000,'comparisons':64,'wall_ms':60000,'controller_cpu_ms':60000,'retained_output_bytes':20000000}
        trial={'id':'one','root':str(root),'case_hash':digest(case),'architecture_hash':'a'*64,'repeat':1,
            'tasks_hash':digest(tasks),'source_pins_hash':digest(source_pins()),'policy':asdict(policy),'duration_seconds':7200,
            'tool_budget':tool_budget,'process_envelope':envelope}
        plan={'study_id':'process','trials':[trial]}
        if not freeze:return plan,tasks,policy
        sr.freeze(plan)
        ledger=sr.create_stage(root,'process','one',policy=policy,tasks=tasks,duration_seconds=7200,provenance={'source_pins':source_pins()})
        return ledger
    return create


def test_exited_child_and_startup_io_remain_in_original_job_cost(setup_process):
    ledger=setup_process();receipt=pe.supervise(ledger.root)
    probe=json.loads((ledger.root/'child_probe.json').read_text(encoding='utf-8'))
    m=receipt['metrics']
    # Windows interpreter launchers may create additional startup processes.
    assert receipt['exit_code']==0 and m['active_processes']==0 and m['total_processes']>=2
    assert m['cpu_ms']>=probe['primary_cpu_ms']+200
    assert m['read_bytes']>=1048576 and m['write_bytes']>=1048576
    assert pe.status(ledger.root)['known_finished']['cpu_ms']==m['cpu_ms']
    assert pe.status(ledger.root)['unfinished_slots']==[]


def test_cpu_ceiling_stops_owned_job_and_retains_overrun(setup_process):
    ledger=setup_process('burn',cpu_ms=350,closing_cpu_ms=100)
    receipt=pe.supervise(ledger.root)
    assert receipt['stop_reason']=='process_resource_ceiling' and receipt['exit_code']!=0
    assert receipt['metrics']['cpu_ms']>=350 and receipt['metrics']['active_processes']==0
    with pytest.raises(AdmissionBlocked,match='resources exhausted'):pe.reserve(ledger.root)


def test_nonzero_exit_has_known_cost_and_local_copy_cannot_erase_it(setup_process):
    ledger=setup_process('crash');receipt=pe.supervise(ledger.root)
    assert receipt['exit_code']==7 and receipt['metrics']['cpu_ms']>0
    local=ledger.root/'process_runs/1/receipt.json';local.rename(local.with_suffix('.preserved'))
    local.write_text('{"cpu_ms":0}',encoding='utf-8')
    state=pe.status(ledger.root)
    assert state['known_finished']['cpu_ms']==receipt['metrics']['cpu_ms'] and not state['unfinished_slots']


def test_missing_run_slot_cannot_reset_launch_opportunity(setup_process):
    ledger=setup_process()
    with sqlite3.connect(sr.REGISTRY) as db:
        db.execute('CREATE TABLE preserved_runs AS SELECT * FROM process_runs')
        db.execute('DELETE FROM process_runs WHERE slot=1')
    with pytest.raises(AdmissionBlocked,match='slots missing'):pe.reserve(ledger.root)


def test_reserved_unobserved_run_cannot_be_replaced_or_used_outside_job(setup_process):
    ledger=setup_process();intent,_=pe.reserve(ledger.root)
    assert intent['slot']==1
    with pytest.raises(AdmissionBlocked,match='unresolved process run'):pe.reserve(ledger.root)
    with pytest.raises(AdmissionBlocked):
        ledger.reserve('test',('inspect_inputs','submit_research_report'),lambda *a:pytest.fail('No unmetered prompt'))
    assert sr.snapshot('process')['calls']==[]


def test_same_ordinary_runtime_and_batch_account_complete_inside_job(setup_process):
    ledger=setup_process('full');receipt=pe.supervise(ledger.root)
    assert receipt['exit_code']==0,(ledger.root/'process_runs/1/worker.log').read_text(encoding='utf-8',errors='replace')
    v=json.loads((ledger.root/'generated_runtime_validation.json').read_text(encoding='utf-8'))
    assert v['status']['tasks']['test']['terminal']=='submitted'
    assert len(v['history'])==5 and all(r['status']=='applied' for r in v['history'])
    assert v['history'][-1]['result']['legal_submission'] and not v['history'][-1]['result']['formal_target_success']
    assert receipt['metrics']['total_processes']>=2 and receipt['metrics']['active_processes']==0
    assert sr.snapshot('process')['known_tokens']==100
    assert v['actual_model_calls']==0


def test_process_closing_reserve_reaches_input_abstention(setup_process):
    ledger=setup_process('closing',cpu_ms=10000,closing_cpu_ms=8500)
    receipt=pe.supervise(ledger.root)
    assert receipt['exit_code']==0,(ledger.root/'process_runs/1/worker.log').read_text(encoding='utf-8',errors='replace')
    v=json.loads((ledger.root/'generated_runtime_validation.json').read_text(encoding='utf-8'))
    assert len(v['history'])==1 and v['history'][0]['response']['action']=='submit_research_report'
    assert v['history'][0]['result']['model_report']['outcome']=='abstain'
    assert v['status']['tasks']['test']['calls'][0]['mode']=='close_only'
    assert sr.snapshot('process')['known_tokens']==20


def paired(setup_process,*,headroom=0):
    from quanta_agents.meta_v3 import study_allocation as sa
    plan,tasks,policy=setup_process('burn',freeze=False,cpu_ms=350,closing_cpu_ms=100)
    one=plan['trials'][0];two=deepcopy(one)
    two.update(id='two',root=one['root']+'_two',architecture_hash='b'*64)
    two['process_envelope']['arguments'][1]=two['root']
    plan['trials'].append(two)
    plan['allocation']={'version':sa.VERSION,'model_tokens':2*policy.stage_tokens,'model_calls':2*policy.stage_calls,
        'tool_resources':{k:2*v for k,v in one['tool_budget'].items()},
        'process_resources':{k:2*one['process_envelope']['budget'][k] for k in pe.LIMITS}}
    plan['allocation']['process_resources']['cpu_ms']+=headroom
    return plan,tasks,policy


def test_process_comparison_grants_and_total_are_frozen_before_any_launch(setup_process):
    plan,_,_=paired(setup_process)
    plan['allocation']['process_resources']['cpu_ms']-=1
    with pytest.raises(AdmissionBlocked,match='fund all process grants'):sr.freeze(plan)
    plan['allocation']['process_resources']['cpu_ms']+=2
    plan['trials'][1]['process_envelope']['budget']['cpu_ms']+=1
    with pytest.raises(AdmissionBlocked,match='equal resource ceilings'):sr.freeze(plan)
    assert not sr.REGISTRY.exists()


@pytest.mark.parametrize('headroom',[0,1000])
def test_measured_overrun_uses_only_declared_study_headroom(setup_process,headroom):
    plan,tasks,policy=paired(setup_process,headroom=headroom);sr.freeze(plan)
    stages=[sr.create_stage(t['root'],'process',t['id'],policy=policy,tasks=tasks,duration_seconds=7200,
        provenance={'source_pins':source_pins()}) for t in plan['trials']]
    receipt=pe.supervise(stages[0].root)
    assert receipt['stop_reason']=='process_resource_ceiling'
    state=sr.snapshot('process')['study_allocation']
    assert state['process_overrun']['cpu_ms']==receipt['metrics']['cpu_ms']-350>0
    assert state['process_headroom']['cpu_ms']==headroom
    assert state['process_allocation_exhausted']==(headroom==0)
    if headroom==0:
        with pytest.raises(AdmissionBlocked,match='study process headroom'):pe.reserve(stages[1].root)
    else:
        intent,_=pe.reserve(stages[1].root)
        assert intent['slot']==1
    assert pe.status(stages[1].root)['budget']['cpu_ms']==350
    (stages[0].root/'allocation_observation.json').write_text(json.dumps(state,ensure_ascii=True,indent=2),encoding='utf-8')


def test_original_process_receipt_failure_keeps_run_unknown_without_retry(setup_process,monkeypatch,tmp_path):
    ledger=setup_process('crash');write=pe._write
    def interrupted(root,intent,kind,value):
        if kind=='receipt':
            (tmp_path/'unanchored_original_observation.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
            raise OSError('Generated original canonical process receipt interruption')
        return write(root,intent,kind,value)
    monkeypatch.setattr(pe,'_write',interrupted)
    with pytest.raises(OSError,match='canonical process receipt'):pe.supervise(ledger.root)
    state=pe.status(ledger.root)
    assert state['unfinished_slots']==[1] and state['launches_used']==1
    with pytest.raises(AdmissionBlocked,match='unresolved process run'):pe.reserve(ledger.root)
    assert sr.snapshot('process')['process_resources']['one']['unfinished_slots']==[1]


def test_io_ceiling_counts_startup_and_stops_before_long_work(setup_process):
    ledger=setup_process('burn',io_transfer_bytes=100000,closing_io_transfer_bytes=0)
    receipt=pe.supervise(ledger.root)
    assert receipt['stop_reason']=='process_resource_ceiling' and receipt['metrics']['io_transfer_bytes']>=100000
    assert receipt['metrics']['active_processes']==0


def test_existing_process_schema_cannot_be_removed_from_snapshot(setup_process):
    ledger=setup_process()
    with sqlite3.connect(sr.REGISTRY) as db:db.execute('ALTER TABLE process_runs RENAME TO preserved_process_runs')
    with pytest.raises(AdmissionBlocked,match='canonical process journal missing'):sr.snapshot('process')
    with pytest.raises(AdmissionBlocked,match='canonical process journal missing'):pe.reserve(ledger.root)


def test_process_policy_deletion_cannot_downgrade_stage_binding(setup_process):
    ledger=setup_process()
    with sqlite3.connect(sr.REGISTRY) as db:
        spec=json.loads(db.execute('SELECT spec FROM trials').fetchone()[0]);spec.pop('process_envelope')
        db.execute('UPDATE trials SET spec=?',(json.dumps(spec),))
    with pytest.raises(AdmissionBlocked,match='specification drift'):pe.status(ledger.root)


def test_ordinary_cli_dispatches_envelope_and_direct_new_model_gate_stays_closed(setup_process,monkeypatch,capsys):
    import importlib.util
    from quanta_agents.meta_v3.kernel import ROOT
    ledger=setup_process('full')
    module_spec=importlib.util.spec_from_file_location('process_cli',ROOT/'scripts/run_research_v3.py')
    cli=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(cli)
    monkeypatch.setattr(sys,'argv',['run_research_v3.py','run','--root',str(ledger.root)])
    cli.main();receipt=json.loads(capsys.readouterr().out)
    assert receipt['exit_code']==0 and receipt['metrics']['active_processes']==0
    saved=ledger.call(ledger.history('test')[0]['id']);intent=deepcopy(saved['intent']);intent['intent_id']='outside_new_call'
    with pytest.raises(AdmissionBlocked,match='live process run'):sr.reserve_model(ledger.root,intent,80)
    with sr._db() as db:
        with pytest.raises(AdmissionBlocked,match='live process run'):pe.admit(db,ledger.root)
    assert sr.snapshot('process')['known_tokens']==100 and len(sr.snapshot('process')['calls'])==5


def test_original_cost_writer_is_independent_of_changed_local_stage_plan(setup_process):
    # Unit test of storage after a read: these counters are explicitly generated,
    # not observations of an OS process. Whole job acquisition is tested above.
    ledger=setup_process();intent,_=pe.reserve(ledger.root)
    dispatch={'pid':123,'job_name':intent['job_name'],'started_at':intent['reserved_at'],'assigned_before_resume':True}
    pe._write(ledger.root,intent,'dispatch',dispatch)
    metrics={'user_cpu_100ns':1000000,'kernel_cpu_100ns':0,'cpu_ms':100,'read_ops':1,'write_ops':1,'other_ops':0,
        'read_bytes':100,'write_bytes':200,'other_bytes':0,'io_transfer_bytes':300,'total_processes':1,'active_processes':0,'processes_terminated_by_limit':0}
    receipt={'kind':pe.VERSION,'intent_hash':digest(intent),'dispatch_hash':digest(dispatch),'metrics':metrics,'exit_code':7,
        'stop_reason':None,'ended_at':intent['reserved_at']+1,'wall_ms':1000,'supervisor_outside_measured_experiment':True,
        'io_is_physical_disk_bytes':False,'formal_target_success':False}
    p=ledger.root/'plan.json';value=json.loads(p.read_text(encoding='utf-8'));p.rename(p.with_suffix('.preserved'))
    value['provenance']['generated_plan_drift']=True;p.write_text(json.dumps(value),encoding='utf-8')
    assert pe._write(ledger.root,intent,'receipt',receipt)
    assert pe._write(ledger.root,intent,'receipt',receipt) is False
    assert pe.status(ledger.root)['known_finished']=={'cpu_ms':100,'io_transfer_bytes':300}
    with pytest.raises(AdmissionBlocked,match='stage plan changed'):pe.reserve(ledger.root)
    (ledger.root/'generated_counter_unit_only.json').write_text(json.dumps({'actual_process_launches':0,'actual_job_counters':False}),encoding='utf-8')


def test_unsupported_platform_cannot_consume_a_launch_slot(setup_process,monkeypatch):
    from types import SimpleNamespace
    ledger=setup_process();monkeypatch.setattr(pe,'os',SimpleNamespace(name='unsupported'))
    with pytest.raises(AdmissionBlocked,match='unavailable on this platform'):pe.supervise(ledger.root)
    with sqlite3.connect(sr.REGISTRY) as db:assert db.execute('SELECT count(*) FROM process_runs WHERE intent IS NOT NULL').fetchone()[0]==0
