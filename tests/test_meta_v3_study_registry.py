"""Cross-directory admission and generated cost receipts; no model or account."""
from copy import deepcopy
from dataclasses import asdict
import json
import shutil
import sqlite3

import pytest

from quanta_agents.meta_v3 import study_registry as sr
from quanta_agents.meta_v3.ledger import Ledger, AdmissionBlocked, digest, serial
from test_meta_v3_ledger import P, A, request, settle


@pytest.fixture(autouse=True)
def isolate_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path/'canonical/studies.sqlite3')


def prepared(tmp_path, *, trial_count=1):
    tasks={'one':{'idea':'Generated ordinary input'}}; pins={'generated':'a'*64}
    trials=[{'id':f't{i}', 'root':str((tmp_path/f'stage{i}').resolve()), 'case_hash':'1'*64,
        'architecture_hash':'2'*64, 'repeat':i+1, 'tasks_hash':digest(tasks),
        'source_pins_hash':digest(pins), 'policy':asdict(P), 'duration_seconds':7200} for i in range(trial_count)]
    plan={'study_id':'study', 'trials':trials}; sr.freeze(plan)
    return plan,tasks,pins


def create(plan,tasks,pins,index=0):
    t=plan['trials'][index];binding=sr.claim(plan['study_id'],t['id'])
    return Ledger.create(t['root'],policy=P,tasks=tasks,deadline_epoch=binding['deadline_epoch'],
        provenance={'source_pins':pins,'study_trial':binding})


def test_renaming_study_and_directory_does_not_restore_opportunities(tmp_path):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins)
    copied=deepcopy(plan);copied['study_id']='another';copied['trials'][0]['root']=str(tmp_path/'another')
    copied['trials'][0]['id']='renamed'
    with pytest.raises(AdmissionBlocked,match='equivalent opportunities'):sr.freeze(copied)
    with pytest.raises(AdmissionBlocked,match='already claimed'):sr.claim('study','t0')
    assert sr.snapshot('study')['trials'][0]['claimed_at'] is not None


def test_copied_stage_cannot_dispatch_from_new_directory(tmp_path):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins)
    target=tmp_path/'copied';shutil.copytree(job.root,target)
    with pytest.raises(AdmissionBlocked,match='copied outside'):Ledger(target).reserve('one',A,request)
    assert sr.snapshot('study')['calls']==[]


def test_deleted_binding_cannot_downgrade_registered_root(tmp_path):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins)
    p=job.root/'plan.json';x=json.loads(p.read_text(encoding='utf-8'));x['provenance'].pop('study_trial')
    p.write_text(serial(x),encoding='utf-8')
    with sqlite3.connect(job.path) as db:db.execute('update stage set plan=?,plan_hash=?',(serial(x),digest(x)))
    with pytest.raises(AdmissionBlocked,match='binding missing'):job.reserve('one',A,request)
    assert sr.snapshot('study')['calls']==[]


def test_input_policy_and_clock_cannot_change_after_claim(tmp_path):
    plan,tasks,pins=prepared(tmp_path);binding=sr.claim('study','t0')
    bad=deepcopy(tasks);bad['one']['idea']='Later retuned input'
    with pytest.raises(AdmissionBlocked,match='inputs or policy'):Ledger.create(plan['trials'][0]['root'],policy=P,tasks=bad,
        deadline_epoch=binding['deadline_epoch'],provenance={'source_pins':pins,'study_trial':binding})
    with pytest.raises(AdmissionBlocked,match='already claimed'):sr.claim('study','t0')


def test_claimed_clock_is_not_renewed_on_restart(tmp_path):
    plan,tasks,pins=prepared(tmp_path);binding=sr.claim('study','t0')
    with pytest.raises(AdmissionBlocked,match='clock cannot'):Ledger.create(plan['trials'][0]['root'],policy=P,tasks=tasks,
        deadline_epoch=binding['deadline_epoch']+1,provenance={'source_pins':pins,'study_trial':binding})


def test_shared_reservation_precedes_local_commit_and_blocks_crash_replacement(tmp_path,monkeypatch):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins)
    original=Ledger.event
    def crash(db,kind,body):
        if kind=='call_reserved':raise RuntimeError('generated local commit interruption')
        return original(db,kind,body)
    with monkeypatch.context() as patch:
        patch.setattr(Ledger,'event',staticmethod(crash))
        with pytest.raises(RuntimeError):job.reserve('one',A,request)
    assert job.status('one')['calls']==[]
    saved=sr.snapshot('study');assert len(saved['calls'])==1 and saved['unresolved_reserve']==80
    with pytest.raises(AdmissionBlocked,match='unresolved shared'):job.reserve('one',A,request)
    assert sr.snapshot('study')['unresolved_reserve']==80


def test_verified_receipts_reconcile_after_interruption_without_double_cost(tmp_path,monkeypatch):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins);intent=job.reserve('one',A,request)
    receipt={'request_identity':{'intent_id':intent['intent_id']},'usage':{'input_tokens':17,'output_tokens':3},
        'artifact_sha256':{},'response':{'action':'inspect_inputs'}}
    with monkeypatch.context() as patch:
        patch.setattr(sr,'settle_model',lambda *a:(_ for _ in ()).throw(RuntimeError('generated shared receipt interruption')))
        with pytest.raises(RuntimeError):job.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    assert job.call(intent['intent_id'])['known_tokens']==20 and sr.snapshot('study')['unresolved_reserve']==80
    job.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    job.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    assert sr.snapshot('study')['known_tokens']==20 and sr.snapshot('study')['unresolved_reserve']==0


def test_actual_overrun_is_recorded_and_cannot_buy_another_trial_slot(tmp_path):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins);intent=job.reserve('one',A,request)
    settle(job,intent,cost=450)
    assert sr.snapshot('study')['known_tokens']==450
    with pytest.raises(AdmissionBlocked):job.reserve('one',A,request)
    with pytest.raises(AdmissionBlocked):sr.claim('study','t0')
    assert sr.snapshot('study')['full_stack_comparison_admitted'] is False


def test_declared_independent_repeats_keep_separate_costs_without_relabeling(tmp_path):
    plan,tasks,pins=prepared(tmp_path,trial_count=2)
    one=create(plan,tasks,pins,0);two=create(plan,tasks,pins,1)
    a=one.reserve('one',A,request);b=two.reserve('one',A,request)
    settle(one,a,cost=17);two.unknown(b['intent_id'],'generated unresolved')
    result=sr.snapshot('study');assert result['known_tokens']==17 and result['unresolved_reserve']==80
    assert {c['trial_id'] for c in result['calls']}=={'t0','t1'}


def test_registry_loss_blocks_registered_stage(tmp_path):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins)
    sr.REGISTRY.rename(sr.REGISTRY.with_suffix('.preserved'))
    with pytest.raises(AdmissionBlocked,match='registry missing'):job.reserve('one',A,request)


def test_duplicate_semantic_repeat_in_one_plan_is_rejected(tmp_path):
    plan,tasks,pins=prepared(tmp_path);other=deepcopy(plan);other['study_id']='bad'
    t=deepcopy(plan['trials'][0]);t['id']='dup';t['root']=str(tmp_path/'different');other['trials'].append(t)
    with pytest.raises(AdmissionBlocked,match='duplicate trial slot'):sr.freeze(other)


def test_two_controllers_cannot_claim_one_slot_twice(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    prepared(tmp_path);barrier=Barrier(2)
    def claimant():
        barrier.wait(timeout=5)
        try:return sr.claim('study','t0')
        except AdmissionBlocked:return 'blocked'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:claimant(),range(2)))
    assert sum(type(x) is dict for x in results)==1 and results.count('blocked')==1


def test_registry_loss_between_check_and_reservation_cannot_skip_charge(tmp_path,monkeypatch):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins)
    original=sr.reserve_model
    def remove_then_reserve(*args):
        sr.REGISTRY.rename(sr.REGISTRY.with_suffix('.preserved'))
        return original(*args)
    monkeypatch.setattr(sr,'reserve_model',remove_then_reserve)
    with pytest.raises(AdmissionBlocked,match='registry missing'):job.reserve('one',A,request)
    with sqlite3.connect(job.path) as db:assert db.execute('select count(*) from calls').fetchone()[0]==0


def test_registry_loss_at_receipt_keeps_known_local_cost_and_reconciles_later(tmp_path):
    plan,tasks,pins=prepared(tmp_path);job=create(plan,tasks,pins);intent=job.reserve('one',A,request)
    receipt={'request_identity':{'intent_id':intent['intent_id']},'usage':{'input_tokens':17,'output_tokens':3},
        'artifact_sha256':{},'response':{'action':'inspect_inputs'}}
    preserved=sr.REGISTRY.with_suffix('.preserved');sr.REGISTRY.rename(preserved)
    with pytest.raises(AdmissionBlocked,match='registry missing'):job.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    assert job.call(intent['intent_id'])['known_tokens']==20
    preserved.rename(sr.REGISTRY)
    job.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    assert sr.snapshot('study')['known_tokens']==20 and sr.snapshot('study')['unresolved_reserve']==0
