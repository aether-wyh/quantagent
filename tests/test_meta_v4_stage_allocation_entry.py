"""Generated receipts and actual admission tools; no model/account/process run."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import time

import pytest

from quanta_agents.meta_v3 import study_registry as sr, study_allocation as sa
from quanta_agents.meta_v3 import process_envelope as pe, research_batch
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime
from test_meta_v3_study_allocation import proposal, create
from test_meta_v3_ledger import P, A, request, settle
from test_meta_v3_tool_resources import reply


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path / 'canonical.sqlite3')
    def forbidden(*args, **kwargs):
        pytest.fail('No model, native process, or strategy worker in entry checks')
    monkeypatch.setattr(research_batch.subprocess, 'Popen', forbidden)
    monkeypatch.setattr(research_batch, 'run', forbidden)
    monkeypatch.setattr(module('meta.codex_gateway').CodexGateway, 'run', forbidden)


def setup_debt(tmp_path, resource):
    plan, tasks, pins = proposal(tmp_path, output_bytes=1 if resource == 'tool' else 5000000)
    if resource == 'process':
        entry = Path(__file__).parent / 'helpers/meta_v3_process_fixture.py'
        budget = {'launches':1, 'cpu_ms':1000, 'io_transfer_bytes':1000000,
                  'closing_cpu_ms':100, 'closing_io_transfer_bytes':1000}
        for trial in plan['trials']:
            trial['process_envelope'] = {'version':pe.VERSION, 'entrypoint':str(entry.resolve()),
                'entrypoint_sha256':hashlib.sha256(entry.read_bytes()).hexdigest(),
                'arguments':['--root',trial['root'],'--registry',str(sr.REGISTRY),'--mode','crash'],
                'budget':deepcopy(budget)}
        plan['allocation']['process_resources'] = {k:2*budget[k] for k in pe.LIMITS}
    sr.freeze(plan)
    one = create(plan,tasks,pins,0)
    if resource == 'model':
        settle(one,one.reserve('one',A,request),cost=450)
    elif resource == 'tool':
        runtime = ResearchRuntime(one.root)
        runtime.verify_inputs()
        result = reply(runtime,tasks['one'],'inspect_inputs',
            {'table':'fields','offset':0,'limit':32},task_id='one')
        assert result['status'] == 'applied'
    else:
        # An explicitly scripted native receipt validates canonical aggregation
        # without launching the fixture or measuring an invented real workload.
        intent, _ = pe.reserve(one.root)
        dispatch = {'job_name':intent['job_name'],'assigned_before_resume':True}
        pe._write(one.root,intent,'dispatch',dispatch)
        metrics = dict.fromkeys(('user_cpu_100ns','kernel_cpu_100ns','cpu_ms','read_ops',
            'write_ops','other_ops','read_bytes','write_bytes','other_bytes','io_transfer_bytes',
            'total_processes','active_processes','processes_terminated_by_limit'),0)
        metrics.update(cpu_ms=1001,user_cpu_100ns=10010000,total_processes=1)
        receipt = {'kind':pe.VERSION,'intent_hash':digest(intent),'dispatch_hash':digest(dispatch),
            'metrics':metrics,'exit_code':0,'stop_reason':None,'ended_at':time.time(),'wall_ms':1,
            'supervisor_outside_measured_experiment':True,'io_is_physical_disk_bytes':False,
            'formal_target_success':False}
        pe._write(one.root,intent,'receipt',receipt)
    return plan,tasks,pins,one


def canonical_state():
    with sqlite3.connect(sr.REGISTRY) as db:
        return {name:db.execute('SELECT * FROM '+name+' ORDER BY 1,2').fetchall()
                for name in ['studies','trials','calls','tool_actions','process_runs','producer_runs']}


@pytest.mark.parametrize('resource',['model','tool','process'])
def test_exhaustion_rejects_before_stage_claim_directory_or_new_process(tmp_path,resource):
    plan,tasks,pins,one = setup_debt(tmp_path,resource)
    before = canonical_state()
    saved_plan = (one.root/'plan.json').read_bytes()
    allocation = sr.snapshot('allocated')['study_allocation']
    assert allocation[resource+'_allocation_exhausted'] is True
    with pytest.raises(AdmissionBlocked,match='study '+resource+' headroom exhausted; no new stage claim'):
        create(plan,tasks,pins,1)
    # Direct low-level claim shares the gate instead of bypassing the CLI.
    with pytest.raises(AdmissionBlocked,match='no new stage claim'):
        sr.claim('allocated','t1')
    assert canonical_state() == before
    assert not Path(plan['trials'][1]['root']).exists()
    assert (one.root/'plan.json').read_bytes() == saved_plan
    assert not list(tmp_path.rglob('worker_result.json'))


@pytest.mark.parametrize('mismatch',['source','inputs'])
def test_source_or_input_mismatch_precedes_allocation_and_consumes_nothing(tmp_path,monkeypatch,mismatch):
    plan,tasks,pins,_ = setup_debt(tmp_path,'model')
    before = canonical_state()
    if mismatch == 'source':
        pins = {'generated_mismatch':'f'*64}
        message = 'study source identity changed'
    else:
        tasks = deepcopy(tasks)
        tasks['one']['idea'] = 'Changed generated input'
        message = 'study inputs or policy changed'
    def not_reached(*args):
        pytest.fail('Allocation must not run before frozen input and source validation')
    monkeypatch.setattr(sa,'status',not_reached)
    with pytest.raises(AdmissionBlocked,match=message):
        create(plan,tasks,pins,1)
    assert canonical_state() == before
    assert not Path(plan['trials'][1]['root']).exists()


def test_healthy_allocation_creates_exact_frozen_grant_without_process_or_model(tmp_path):
    plan,tasks,pins = proposal(tmp_path)
    sr.freeze(plan)
    stages = [create(plan,tasks,pins,i) for i in range(2)]
    state = sr.snapshot('allocated')
    assert state['calls'] == [] and state['known_tokens'] == 0
    assert not any(state['study_allocation'][r+'_allocation_exhausted'] for r in ['model','tool','process'])
    for stage, trial in zip(stages,state['trials']):
        saved = json.loads((stage.root/'plan.json').read_text(encoding='utf-8'))
        assert saved['policy'] == plan['trials'][0]['policy']
        assert saved['deadline_epoch'] == trial['claimed_at'] + 7200
        assert saved['provenance']['study_trial']['deadline_epoch'] == saved['deadline_epoch']
        assert not (stage.root/'process_runs').exists()
        assert not (stage.root/'calls').exists()
