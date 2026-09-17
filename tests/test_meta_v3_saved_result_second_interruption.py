"""Original result authority survives repeated application interruptions."""
import json
import sqlite3

import pytest

from quanta_agents.meta_v3 import tool_resources as tr, tool_measurements as tm, study_registry as sr
from quanta_agents.meta_v3.ledger import AdmissionBlocked, serial
from quanta_agents.meta_v3.research_tools import ResearchTools
from test_meta_v3_tool_resources import setup, reply


def interrupted_application(setup,monkeypatch):
    runtime,task=setup()
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def stopped(*a):raise KeyboardInterrupt('Generated first interruption after original measurement')
    with monkeypatch.context() as patch:
        patch.setattr(tr,'_settle',stopped)
        with pytest.raises(KeyboardInterrupt):runtime._apply(call['id'])
    tm.reconcile_available(runtime.root)
    def stopped_commit(*a,**k):raise OSError('Generated second interruption after application receipt')
    with monkeypatch.context() as patch:
        patch.setattr(runtime.ledger,'finish_apply',stopped_commit)
        with pytest.raises(OSError,match='second interruption'):runtime._apply(call['id'])
    call=runtime.ledger.call(call['id']);assert call['status']=='applying'
    application=runtime.root/'calls'/call['id']/'application.json'
    assert json.loads(application.read_text(encoding='utf-8'))['saved_result_recovery']
    (runtime.root/'original_application_preserved.json').write_bytes(application.read_bytes())
    return runtime,task,call,application


@pytest.mark.parametrize('variant',['request_output','result_output','application_public','marker_removed_public'])
def test_second_interruption_revalidates_original_and_derived_results(setup,monkeypatch,variant):
    runtime,_,call,application=interrupted_application(setup,monkeypatch)
    path=(runtime.root/'tools/test'/call['id']/('request.json' if variant=='request_output' else 'result.json')
          if variant.endswith('_output') else application)
    value=json.loads(path.read_text(encoding='utf-8'));path.rename(path.with_suffix('.preserved'))
    if variant.endswith('_output'):value['generated_drift']='Changed after the first saved-only recovery'
    else:
        value['result']['public']={'generated_drift':'Arbitrary result while original artifact_hash is unchanged'}
        if variant=='marker_removed_public':value.pop('saved_result_recovery')
    path.write_text(serial(value),encoding='utf-8')
    before=tr.status(runtime.root)
    def forbidden(*a,**k):pytest.fail('Repeated recovery cannot reexecute a producer')
    monkeypatch.setattr(ResearchTools,'execute',forbidden)
    blocked=False;error=None
    try:runtime._apply(call['id'])
    except AdmissionBlocked as exc:blocked=True;error=str(exc)
    after=runtime.ledger.call(call['id'])
    (runtime.root/'second_recovery_probe.json').write_text(serial({'variant':variant,'blocked':blocked,
        'error':error,'after_status':after['status'],'before_tool_resources':before,'after_tool_resources':tr.status(runtime.root),
        'generated_model_receipt_tokens':sr.snapshot('tools')['known_tokens'],'actual_model_calls':0,'account_executions':0}),encoding='utf-8')
    assert blocked,(variant,after)
    assert after==call and tr.status(runtime.root)==before


@pytest.mark.parametrize('keep_marker',[True,False])
def test_unchanged_second_recovery_completes_once_and_keeps_original_cost(setup,monkeypatch,keep_marker):
    runtime,_,call,application=interrupted_application(setup,monkeypatch)
    if not keep_marker:
        value=json.loads(application.read_text(encoding='utf-8'));value.pop('saved_result_recovery')
        application.write_text(serial(value),encoding='utf-8')
    original=application.read_bytes();before=tr.status(runtime.root)
    def forbidden(*a,**k):pytest.fail('Unchanged recovery cannot rerun')
    monkeypatch.setattr(ResearchTools,'execute',forbidden)
    runtime._apply(call['id']);runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])['status']=='applied'
    assert application.read_bytes()==original and tr.status(runtime.root)==before
    assert sr.snapshot('tools')['known_tokens']==20
    with sqlite3.connect(runtime.ledger.path) as db:
        assert db.execute("SELECT count(*) FROM events WHERE kind='action_settled'").fetchone()[0]==1


def ordinary_interruption(setup,monkeypatch,*,raise_producer=False):
    runtime,task=setup()
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    original=ResearchTools._execute
    def partial(tools,*args):
        original(tools,*args)
        raise ValueError('Generated producer failure despite retained partial outputs')
    def stopped_commit(*a,**k):raise OSError('Generated ordinary application commit interruption')
    with monkeypatch.context() as patch:
        if raise_producer:patch.setattr(ResearchTools,'_execute',partial)
        patch.setattr(runtime.ledger,'finish_apply',stopped_commit)
        with pytest.raises(OSError,match='ordinary application'):runtime._apply(call['id'])
    application=runtime.root/'calls'/call['id']/'application.json'
    assert 'saved_result_recovery' not in json.loads(application.read_text(encoding='utf-8'))
    (runtime.root/'ordinary_application_preserved.json').write_bytes(application.read_bytes())
    return runtime,runtime.ledger.call(call['id']),application


def test_ordinary_application_without_marker_uses_same_original_authority(setup,monkeypatch):
    runtime,call,application=ordinary_interruption(setup,monkeypatch)
    value=json.loads(application.read_text(encoding='utf-8'))
    value['result']['public']={'changed':'Generated ordinary receipt drift'}
    application.write_text(serial(value),encoding='utf-8')
    with pytest.raises(AdmissionBlocked,match='differs from canonical original'):
        runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])==call


def test_raised_producer_cannot_be_promoted_by_forged_success_application(setup,monkeypatch):
    runtime,call,application=ordinary_interruption(setup,monkeypatch,raise_producer=True)
    value=json.loads(application.read_text(encoding='utf-8'));assert value['failed'] is True
    value['failed']=False
    value['result']=json.loads((runtime.root/'tools/test'/call['id']/'result.json').read_text(encoding='utf-8'))
    application.write_text(serial(value),encoding='utf-8')
    with pytest.raises(AdmissionBlocked,match='requires an anchored original returned result'):
        runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])==call
    assert tr.status(runtime.root)['entries'][0]['outcome']=='raised'


def test_absent_original_anchor_cannot_use_existing_application(setup,monkeypatch):
    runtime,_,call,application=interrupted_application(setup,monkeypatch)
    with sqlite3.connect(sr.REGISTRY) as db:
        db.execute('CREATE TABLE preserved_measurement AS SELECT * FROM tool_measurements')
        db.execute('DELETE FROM tool_measurements WHERE id=?',(call['id'],))
    with pytest.raises(AdmissionBlocked,match='required original measurement missing'):
        runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])==call and application.exists()


def test_unregistered_old_application_retains_existing_recovery(setup,tmp_path,monkeypatch):
    from test_meta_v3_research_entry import new
    runtime,task=new(tmp_path/'unregistered')
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def interrupted(*a,**k):raise OSError('Generated unregistered commit interruption')
    with monkeypatch.context() as patch:
        patch.setattr(runtime.ledger,'finish_apply',interrupted)
        with pytest.raises(OSError):runtime._apply(call['id'])
    def forbidden(*a,**k):pytest.fail('Old saved-only recovery cannot execute a producer')
    monkeypatch.setattr(ResearchTools,'execute',forbidden)
    runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])['status']=='applied'
    assert tr.status(runtime.root)['integrated'] is False
