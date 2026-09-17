"""Canonical fixed/random generators: generated prices, native jobs, zero models."""
from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time

import pytest

from quanta_agents.meta_v3 import generator_controls as gc, process_envelope as pe
from quanta_agents.meta_v3 import registered_producer as rp, study_registry as sr, study_allocation as sa
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest,serial
from quanta_agents.meta_v3.runtime import source_pins
from test_meta_v3_generator_controls import inputs,SEED


@pytest.fixture
def setup_producer(tmp_path,monkeypatch):
    monkeypatch.setattr(sr,'REGISTRY',tmp_path/'canonical.sqlite3')
    def create(arms=('fixed',),*,mode='full',count=2,freeze=True):
        case,space=inputs(tmp_path/'generated',(.2,.4))
        tasks={'producer':{'case':case,'case_hash':digest(case),'idea':'Generated producer accounting calibration','documents':[]}}
        policy=ClosingPolicy(task_calls=7,stage_calls=7)
        entry=Path(__file__).parent/'helpers/meta_v3_producer_fixture.py'
        budget={'launches':2,'cpu_ms':60000,'io_transfer_bytes':1073741824,'closing_cpu_ms':1000,'closing_io_transfer_bytes':1048576}
        if mode=='closing':budget['closing_io_transfer_bytes']=budget['io_transfer_bytes']-1
        tool={'actions':1,'candidates':count,'scan_cells':count*48,'comparisons':0,'wall_ms':120000,'controller_cpu_ms':60000,'retained_output_bytes':268435456}
        trials=[]
        for arm in arms:
            root=tmp_path/arm
            envelope={'version':pe.VERSION,'entrypoint':str(entry.resolve()),'entrypoint_sha256':hashlib.sha256(entry.read_bytes()).hexdigest(),
                'arguments':['--root',str(root),'--registry',str(sr.REGISTRY),'--mode',mode],'budget':deepcopy(budget)}
            trials.append({'id':arm,'root':str(root),'case_hash':digest(case),'architecture_hash':digest({'arm':arm}),'repeat':1,
                'tasks_hash':digest(tasks),'source_pins_hash':digest(source_pins()),'policy':asdict(policy),'duration_seconds':7200,
                'tool_budget':deepcopy(tool),'process_envelope':envelope,
                'producer_contract':{'kind':rp.VERSION,'arm':arm,'space':space,'count':count,'seed':SEED}})
        n=len(trials)
        plan={'study_id':'producer','trials':trials,'allocation':{'version':sa.VERSION,'model_tokens':n*policy.stage_tokens,'model_calls':n*policy.stage_calls,
            'tool_resources':{k:n*v for k,v in tool.items()},'process_resources':{k:n*budget[k] for k in pe.LIMITS}}}
        if not freeze:return plan,tasks,policy
        sr.freeze(plan)
        return [sr.create_stage(t['root'],'producer',t['id'],policy=policy,tasks=tasks,duration_seconds=7200,
            provenance={'source_pins':source_pins()}) for t in trials]
    return create


def test_both_registered_arms_use_public_cli_native_child_cost_and_full_cash(setup_producer,monkeypatch):
    stages=setup_producer(('fixed','random'))
    receipts=[]
    for ledger in stages:
        process=rp.dispatch(ledger.root);receipts.append(process)
        assert process['exit_code']==0,(ledger.root/'process_runs/1/worker.log').read_text(encoding='utf-8',errors='replace')
        assert process['metrics']['cpu_ms']>0 and process['metrics']['total_processes']>=3 and process['metrics']['active_processes']==0
        state=rp.status(ledger.root);result=state['record']['receipt']['result'];arm=ledger.root.name
        assert state['completed'] and not state['unknown_work']
        assert result['control_arm']==arm and result['reserved_candidates']==2 and result['reserved_scan_cells']==96
        assert result['started_candidates']==2 and all(r['status']=='completed' for r in result['candidates'])
        assert all(r['account']['initial_cash']=='1000000.00' and r['account']['complete_account'] is True for r in result['candidates'])
        assert state['record']['receipt']['model_final'] is False and result['formal_target_success'] is False
        controls=json.loads((ledger.root/'control/controls.json').read_text(encoding='utf-8'))
        assert set(controls['arms'])=={arm} and controls['reserved_candidates_total']==2
        assert len(json.loads((ledger.root/'admission_probes.json').read_text(encoding='utf-8'))['checks'])==3
        local=ledger.root/'producer_receipt.json';local.rename(local.with_suffix('.preserved'))
        local.write_text('{"result":"invented"}',encoding='utf-8')
        assert rp.status(ledger.root)==state
    state=sr.snapshot('producer');allocation=state['study_allocation']
    assert state['calls']==[] and state['known_tokens']==0
    assert all(g['tool_used']['actions']==1 and g['tool_used']['candidates']==2 and g['tool_used']['scan_cells']==96 for g in allocation['grants'])
    assert allocation['grant_transfer_allowed'] is False and allocation['full_stack_comparison_admitted'] is False
    assert all(g['calls_used']==0 and g['model_call_grant']==7 for g in allocation['grants'])
    monkeypatch.setattr(pe,'supervise',lambda *a:pytest.fail('replacement process'))
    for ledger in stages:
        with pytest.raises(AdmissionBlocked,match='never regenerate'):rp.dispatch(ledger.root)
    (stages[0].root.parent/'final_allocation.json').write_text(serial(state),encoding='utf-8')


def test_unknown_producer_result_keeps_original_reservations_and_cannot_relaunch(setup_producer,monkeypatch):
    ledger=setup_producer(mode='unknown',count=1)[0];process=rp.dispatch(ledger.root)
    assert process['exit_code']!=0 and process['metrics']['cpu_ms']>0
    state=rp.status(ledger.root)
    assert state['unknown_work'] and not state['completed'] and state['record']['intent']['reserved_candidates']==1
    assert (ledger.root/'generated_uncommitted_result.json').is_file()
    assert json.loads((ledger.root/'generated_uncommitted_result.json').read_text(encoding='utf-8'))['started_candidates']==1
    snapshot=sr.snapshot('producer');grant=snapshot['study_allocation']['grants'][0]
    assert grant['tool_used']['actions']==1 and grant['tool_used']['candidates']==1 and grant['tool_used']['scan_cells']==48
    assert snapshot['producer_resources']['fixed']['unknown_work'] and snapshot['calls']==[]
    assert pe.status(ledger.root)['unfinished_slots']==[] and pe.status(ledger.root)['launches_used']==1
    monkeypatch.setattr(pe,'supervise',lambda *a:pytest.fail('unknown replacement process'))
    with pytest.raises(AdmissionBlocked,match='never regenerate'):rp.dispatch(ledger.root)


def test_closing_reserve_records_no_generation_without_model_final(setup_producer):
    ledger=setup_producer(mode='closing')[0];process=rp.dispatch(ledger.root)
    assert process['exit_code']==0,(ledger.root/'process_runs/1/worker.log').read_text(encoding='utf-8',errors='replace')
    state=rp.status(ledger.root);receipt=state['record']['receipt']
    assert receipt['result']['status']=='closed_without_generation' and receipt['result']['started_candidates']==0
    assert receipt['model_final'] is False and receipt['actual_model_calls']==0 and not (ledger.root/'control').exists()
    assert sr.snapshot('producer')['study_allocation']['grants'][0]['tool_used']['candidates']==2


def test_legacy_direct_new_execution_is_rejected_before_any_account(setup_producer,tmp_path):
    setup_producer()
    case,space=inputs(tmp_path/'legacy_generated')
    root=tmp_path/'legacy'
    gc.freeze(root,case,space,count=1,seed=SEED,deadline_epoch=time.time()+300)
    with pytest.raises(AdmissionBlocked,match='registered standalone producer'):gc.run_control(root,'fixed')
    assert not (root/'arms').exists() and sr.snapshot('producer')['calls']==[]


@pytest.mark.parametrize('damage',['row','table'])
def test_missing_canonical_producer_slot_cannot_be_reset(setup_producer,damage):
    ledger=setup_producer()[0]
    with sqlite3.connect(sr.REGISTRY) as db:
        if damage=='row':
            db.execute('CREATE TABLE preserved_producer AS SELECT * FROM producer_runs');db.execute('DELETE FROM producer_runs')
        else:db.execute('ALTER TABLE producer_runs RENAME TO preserved_producer')
    with pytest.raises(AdmissionBlocked,match='producer (slot|journal) missing'):rp.dispatch(ledger.root)
    assert pe.status(ledger.root)['launches_used']==0


def test_producer_requires_envelope_before_study_is_frozen(setup_producer):
    plan,_,_=setup_producer(freeze=False);plan['trials'][0].pop('process_envelope')
    with pytest.raises(AdmissionBlocked,match='requires a process envelope'):sr.freeze(plan)
    assert not sr.REGISTRY.exists()


@pytest.mark.parametrize('field',['arm','count'])
def test_changed_canonical_contract_cannot_downgrade_or_expand_grant(setup_producer,field):
    ledger=setup_producer()[0]
    with sqlite3.connect(sr.REGISTRY) as db:
        spec=json.loads(db.execute('SELECT spec FROM trials').fetchone()[0])
        spec['producer_contract'][field]='random' if field=='arm' else 3
        db.execute('UPDATE trials SET spec=?',(serial(spec),))
    with pytest.raises(AdmissionBlocked,match='specification drift'):rp.dispatch(ledger.root)


def test_copied_stage_cannot_start_new_producer(setup_producer,tmp_path):
    ledger=setup_producer()[0];copy=tmp_path/'copied';shutil.copytree(ledger.root,copy)
    with pytest.raises(AdmissionBlocked,match='copied outside'):rp.dispatch(copy)
    assert pe.status(ledger.root)['launches_used']==0


def test_process_intent_without_producer_intent_cannot_get_replacement_launch(setup_producer,monkeypatch):
    ledger=setup_producer()[0];pe.reserve(ledger.root)
    monkeypatch.setattr(pe,'supervise',lambda *a:pytest.fail('replacement launch'))
    with pytest.raises(AdmissionBlocked,match='no replacement launch'):rp.dispatch(ledger.root)
    assert pe.status(ledger.root)['launches_used']==1 and not rp.status(ledger.root)['completed']
