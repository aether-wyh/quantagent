"""Saved measurement recovery; original producer never reruns to infer costs."""
from copy import deepcopy
import importlib.util
import json
import sqlite3
import sys

import pytest

from quanta_agents.meta_v3 import study_registry as sr, tool_resources as tr, tool_measurements as tm
from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest, serial
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3.runtime import ResearchRuntime
from test_meta_v3_tool_resources import setup, reply
from test_meta_v3_study_allocation import proposal, create


def pending_projection(setup,monkeypatch):
    runtime,task=setup()
    def interrupted(*args):raise RuntimeError('Generated projection interruption after original capture')
    with monkeypatch.context() as patch:
        patch.setattr(tr,'_settle',interrupted)
        call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    assert call['status']=='failed'
    state=tr.status(runtime.root)
    assert state['unresolved']==1 and state['unknown_measurements']==0
    return runtime,task,call,state


def no_producer(monkeypatch):
    def forbidden(*args,**kwargs):pytest.fail('Recovery must not execute a tool or rescan current outputs')
    monkeypatch.setattr(ResearchTools,'_execute',forbidden)
    monkeypatch.setattr(tm,'inventory',forbidden)


def test_saved_projection_recovers_idempotently_without_rerun_or_status_rewrite(setup,monkeypatch):
    runtime,_,call,before=pending_projection(setup,monkeypatch)
    no_producer(monkeypatch)
    first=tm.reconcile(runtime.root,call['id'])
    second=tm.reconcile(runtime.root,call['id'])
    assert first['projection_updated'] is True and second['projection_updated'] is False
    assert first['receipt_hash']==second['receipt_hash'] and first['local_copy']=='matching'
    after=tr.status(runtime.root)
    assert after['unresolved']==0 and after['used']==before['used']
    assert runtime.ledger.call(call['id'])['status']=='failed'
    assert sr.snapshot('tools')['known_tokens']==20 and len(sr.snapshot('tools')['calls'])==1


def test_changed_local_copy_and_output_cannot_erase_original_cost(setup,monkeypatch):
    runtime,_,call,before=pending_projection(setup,monkeypatch)
    local=runtime.root/'calls'/call['id']/'tool_measurement.json'
    local.write_text('{"metrics":{"retained_output_bytes":0}}',encoding='utf-8')
    artifact=runtime.root/'tools/test'/call['id']/'artifact.json'
    artifact.rename(artifact.with_suffix('.preserved'))
    no_producer(monkeypatch)
    result=tm.reconcile(runtime.root,call['id'])
    assert result['local_copy']=='drifted' and result['metrics']['retained_output_bytes']>0
    assert not result['financial_evidence_certified']
    assert tr.status(runtime.root)['used']==before['used'] and not artifact.exists()


def test_missing_local_copy_recovers_from_original_canonical_receipt(setup,monkeypatch):
    runtime,_,call,_=pending_projection(setup,monkeypatch)
    local=runtime.root/'calls'/call['id']/'tool_measurement.json';local.rename(local.with_suffix('.preserved'))
    no_producer(monkeypatch)
    result=tm.reconcile_available(runtime.root)
    assert result['reconciled'][0]['local_copy']=='missing' and not local.exists()
    assert result['unknown_without_receipt']==[]


def test_interrupted_producer_without_measurement_stays_unknown(setup,monkeypatch):
    runtime,task=setup()
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def interrupted(*args):raise KeyboardInterrupt('Generated interruption in original producer')
    monkeypatch.setattr(ResearchTools,'_execute',interrupted)
    with pytest.raises(KeyboardInterrupt):runtime._apply(call['id'])
    no_producer(monkeypatch)
    result=tm.reconcile_available(runtime.root)
    assert result=={'reconciled':[],'unknown_without_receipt':[call['id']]}
    with pytest.raises(AdmissionBlocked,match='no anchored original'):tm.reconcile(runtime.root,call['id'])
    assert tr.status(runtime.root)['unknown_measurements']==1
    assert runtime.ledger.call(call['id'])['status']=='applying'


def test_local_measurement_without_canonical_anchor_is_not_guessed(setup,monkeypatch):
    runtime,task=setup();original=tm.capture
    def interrupted_capture(*args):
        with monkeypatch.context() as patch:
            def unavailable(*a,**k):raise RuntimeError('Generated canonical anchor write interruption')
            patch.setattr(sr,'_db',unavailable)
            return original(*args)
    with monkeypatch.context() as patch:
        patch.setattr(tm,'capture',interrupted_capture)
        call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    assert call['status']=='failed' and (runtime.root/'calls'/call['id']/'tool_measurement.json').is_file()
    no_producer(monkeypatch)
    with pytest.raises(AdmissionBlocked,match='no anchored original'):tm.reconcile(runtime.root,call['id'])
    assert tr.status(runtime.root)['unknown_measurements']==1


def test_canonical_receipt_corruption_cannot_rewrite_projection(setup,monkeypatch):
    runtime,_,call,_=pending_projection(setup,monkeypatch)
    with sqlite3.connect(sr.REGISTRY) as db:
        row=db.execute('SELECT body FROM tool_measurements WHERE id=?',(call['id'],)).fetchone()
        body=json.loads(row[0]);body['metrics']['wall_ms']+=100
        db.execute('UPDATE tool_measurements SET body=? WHERE id=?',(serial(body),call['id']))
    no_producer(monkeypatch)
    with pytest.raises(AdmissionBlocked,match='canonical measurement receipt drift'):tm.reconcile(runtime.root,call['id'])
    with sqlite3.connect(sr.REGISTRY) as db:
        assert db.execute('SELECT metrics FROM tool_actions WHERE id=?',(call['id'],)).fetchone()[0] is None


def test_rehashed_foreign_intent_still_cannot_be_adopted(setup,monkeypatch):
    runtime,_,call,_=pending_projection(setup,monkeypatch)
    with sqlite3.connect(sr.REGISTRY) as db:
        body=json.loads(db.execute('SELECT body FROM tool_measurements WHERE id=?',(call['id'],)).fetchone()[0])
        body['tool_intent']['task_id']='another_task'
        db.execute('UPDATE tool_measurements SET body=?,receipt_hash=? WHERE id=?',(serial(body),digest(body),call['id']))
    no_producer(monkeypatch)
    with pytest.raises(AdmissionBlocked,match='another tool intent'):tm.reconcile(runtime.root,call['id'])


def test_study_accounts_anchored_overrun_before_projection_recovery(setup,tmp_path,monkeypatch):
    plan,tasks,pins=proposal(tmp_path,output_bytes=1);sr.freeze(plan)
    one,two=[create(plan,tasks,pins,i) for i in range(2)]
    runtime=ResearchRuntime(one.root)
    def interrupted(*args):raise RuntimeError('Generated projection interruption')
    with monkeypatch.context() as patch:
        patch.setattr(tr,'_settle',interrupted)
        call=reply(runtime,tasks['one'],'inspect_inputs',{'table':'fields','offset':0,'limit':32},task_id='one')
    before=sr.snapshot('allocated')['study_allocation']
    assert before['tool_allocation_exhausted'] and before['tool_overrun']['retained_output_bytes']>0
    assert two.status('one')['mode']=='close_only'
    no_producer(monkeypatch)
    tm.reconcile(one.root,call['id'])
    after=sr.snapshot('allocated')['study_allocation']
    assert after['tool_overrun']==before['tool_overrun']


def test_runtime_recovers_saved_projection_before_next_model_admission(setup,monkeypatch):
    runtime,_,call,_=pending_projection(setup,monkeypatch)
    no_producer(monkeypatch)
    class StopBeforeNextModel(Exception):pass
    def inspected(task_id):
        assert tr.status(runtime.root)['unresolved']==0
        assert runtime.ledger.call(call['id'])['status']=='failed'
        raise StopBeforeNextModel('Generated stop after actual startup recovery, before model dispatch')
    monkeypatch.setattr(runtime.ledger,'status',inspected)
    with pytest.raises(StopBeforeNextModel):runtime.run()
    assert sr.snapshot('tools')['known_tokens']==20 and len(sr.snapshot('tools')['calls'])==1


def test_public_cli_reconciles_only_original_saved_measurement(setup,monkeypatch,capsys):
    runtime,_,call,_=pending_projection(setup,monkeypatch)
    no_producer(monkeypatch)
    spec=importlib.util.spec_from_file_location('measurement_cli',ROOT/'scripts/run_research_v3.py')
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    monkeypatch.setattr(sys,'argv',['run_research_v3.py','reconcile-tool-measurements','--root',str(runtime.root),'--call-id',call['id']])
    cli.main();result=json.loads(capsys.readouterr().out)
    assert result['projection_updated'] and not result['producer_reexecuted']
    monkeypatch.setattr(sys,'argv',['run_research_v3.py','reconcile-tool-measurements','--root',str(runtime.root)])
    cli.main();assert json.loads(capsys.readouterr().out)=={'reconciled':[],'unknown_without_receipt':[]}
