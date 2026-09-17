"""Same-entry saved-result visibility; generated receipts, never model dispatch."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from quanta_agents.meta_v3 import tool_resources as tr, tool_measurements as tm
from quanta_agents.meta_v3 import program_execution, study_registry as sr
from quanta_agents.meta_v3.context import history_context
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest, serial
from quanta_agents.meta_v3.research_tools import ResearchTools
from test_meta_v3_tool_resources import setup, reply
from test_meta_v3_research_entry import program


def interrupted(*args):
    raise RuntimeError('Generated projection interruption after original returned result')


def seed(setup, monkeypatch, action='inspect_inputs', args=None):
    runtime, task = setup()
    with monkeypatch.context() as patch:
        patch.setattr(tr, '_settle', interrupted)
        call = reply(runtime, task, action, args or {'table':'fields','offset':0,'limit':32})
    assert call['status'] == 'failed'
    return runtime, task, call


def test_failed_result_visible_without_rewriting_failure_or_cost(setup, monkeypatch):
    runtime, _, call = seed(setup, monkeypatch)
    application = runtime.root/'calls'/call['id']/'application.json'
    original = application.read_bytes()
    before = tr.status(runtime.root)
    def forbidden(*a, **k): pytest.fail('Saved view must not execute or inventory a producer')
    monkeypatch.setattr(ResearchTools, '_execute', forbidden)
    monkeypatch.setattr(tm, 'inventory', forbidden)
    view = runtime._history('test')[0]
    assert view['status'] == 'failed' and view['result'].get('artifact_hash'), view
    assert view['original_application_result'] == call['result']
    assert view['saved_result_recovery']['producer_reexecuted'] is False
    assert history_context([view])[0]['original_application_result'] == call['result']
    assert history_context([view])[0]['saved_result_recovery'] == view['saved_result_recovery']
    assert runtime._tools('test')._prior(call['id'], 'inspect_inputs')
    with pytest.raises(AdmissionBlocked, match='this task/action'):
        runtime._tools('other')._prior(call['id'], 'inspect_inputs')
    assert runtime.ledger.call(call['id']) == call and application.read_bytes() == original
    assert tr.status(runtime.root) == before
    assert sr.snapshot('tools')['known_tokens'] == 20


def test_funded_result_survives_projection_failure_without_account_replay(tmp_path, monkeypatch):
    # This test alone permits one new generated account execution per version.
    native_popen = subprocess.Popen
    create = setup.__wrapped__(tmp_path, monkeypatch)
    monkeypatch.setattr(subprocess, 'Popen', native_popen)
    runtime, task = create()
    intent = reply(runtime, task, 'develop_strategy', {'program':program()}, apply=False)
    error = None
    with monkeypatch.context() as patch:
        patch.setattr(tr, '_settle', interrupted)
        try: runtime._apply(intent['id'])
        except RuntimeError as exc: error = str(exc)
    call = runtime.ledger.call(intent['id'])
    state = runtime.ledger.status('test')
    (tmp_path/'funded_interruption_observation.json').write_text(serial({
        'call_id':call['id'],'status':call['status'],'runtime_exception':error,
        'state':state,'generated_model_receipts':1,'actual_model_calls':0,
        'account_seeds':1}), encoding='utf-8')
    assert call['status'] == 'failed' and error is None, (call['status'], error)
    assert state['terminal'] is None
    saved_files = {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (runtime.root/'tools/test'/call['id']).rglob('*') if p.is_file()}
    def forbidden(*a, **k): pytest.fail('Completed account must never replay')
    monkeypatch.setattr(program_execution, 'develop', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    tm.reconcile_available(runtime.root)
    view = runtime._history('test')[0]
    assert view['status']=='failed' and view['result']['public']['raw_status']=='completed_mechanical'
    assert view['result']['public']['costs_applied'] is True
    assert float(view['result']['public']['final_snapshot']['cash']) < 10000
    page = reply(runtime,task,'inspect_execution',{'evidence_id':call['id'],'table':'trades_compact','offset':0,'limit':32})
    assert page['status']=='applied' and page['result']['public']['returned_rows'] > 0
    report = reply(runtime,task,'submit_research_report',{'outcome':'strategy_for_development',
        'conclusion':'Generated full-cash accounting demonstration loses declared costs; no alpha claim.',
        'evidence_ids':[call['id'],page['id']],'program_evidence_id':call['id'],
        'limitations':['Generated 12-day prices and generated model receipts; no formal evidence.'],
        'next_step':'Obtain admissible real evidence.','falsifiers':['Saved accounting differs.']})
    assert report['status']=='applied' and report['result']['legal_submission']
    assert not report['result']['execution_valid'] and not report['result']['formal_target_success']
    assert runtime.ledger.call(call['id']) == call
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in saved_files.items())
    assert tr.status(runtime.root)['used']['candidates']==1
    (tmp_path/'funded_saved_result_validation.json').write_text(serial({
        'history_view':view,'page':page,'final':report,'original_call':call,
        'tool_state':tr.status(runtime.root),'known_generated_tokens':sr.snapshot('tools')['known_tokens'],
        'account_seeds':1,'account_replays':0,'actual_model_calls':0}),encoding='utf-8')


@pytest.mark.parametrize('name', ['request.json','result.json','artifact.json'])
def test_drifted_output_cannot_be_recovered_as_evidence_but_cost_survives(setup, monkeypatch, name):
    runtime, _, call = seed(setup, monkeypatch)
    path = runtime.root/'tools/test'/call['id']/name
    path.rename(path.with_suffix('.preserved'))
    path.write_text('{}',encoding='utf-8')
    def forbidden(*a, **k): pytest.fail('Corrupt evidence must not trigger a rerun')
    monkeypatch.setattr(ResearchTools,'_execute',forbidden)
    assert tm.reconcile(runtime.root,call['id'])['projection_updated']
    with pytest.raises(AdmissionBlocked,match='original returned output changed'):
        runtime._history('test')
    assert runtime.ledger.call(call['id']) == call
    assert tr.status(runtime.root)['used']['retained_output_bytes'] > 0


def test_rewritten_local_model_receipt_cannot_bind_saved_result(setup, monkeypatch):
    runtime, _, call = seed(setup, monkeypatch)
    receipt = json.loads(serial(call['receipt']))
    receipt['response']['arguments_json'] = json.dumps({'table':'coverage','offset':0,'limit':32})
    with sqlite3.connect(runtime.ledger.path) as db:
        db.execute('UPDATE calls SET receipt=? WHERE id=?',(serial(receipt),call['id']))
    with pytest.raises(AdmissionBlocked,match='canonical model receipt changed'):
        runtime._history('test')
    assert sr.snapshot('tools')['known_tokens'] == 20


def test_local_outputs_without_canonical_anchor_remain_unknown(setup, monkeypatch):
    runtime, _, call = seed(setup, monkeypatch)
    with sqlite3.connect(sr.REGISTRY) as db:
        db.execute('CREATE TABLE preserved_measurement AS SELECT * FROM tool_measurements')
        db.execute('DELETE FROM tool_measurements WHERE id=?',(call['id'],))
    assert runtime._history('test') == runtime.ledger.history('test')
    assert 'artifact_hash' not in runtime._history('test')[0]['result']
    assert tr.status(runtime.root)['unknown_measurements'] == 1


def test_raised_producer_cannot_promote_partial_saved_files(setup, monkeypatch):
    runtime, task = setup()
    original = ResearchTools._execute
    def partial(tools, *args):
        original(tools, *args)
        raise ValueError('Generated producer failure after saving partial outputs')
    monkeypatch.setattr(ResearchTools,'_execute',partial)
    call = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    assert call['status']=='failed'
    assert tr.status(runtime.root)['entries'][0]['outcome']=='raised'
    assert runtime._history('test')==runtime.ledger.history('test')


def test_unknown_child_does_not_clear_pause_or_invent_return(setup, monkeypatch):
    runtime, task = setup()
    def partial(tools, call_id, *args):
        (tools.folder/call_id/'workbench').mkdir(parents=True)
        raise OSError('Generated unresolved child intent; no account executed')
    monkeypatch.setattr(ResearchTools,'_execute',partial)
    call = reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    with pytest.raises(OSError,match='unresolved child intent'): runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])['status']=='applying'
    state=runtime.ledger.status('test')
    assert state['mode']=='blocked'
    assert runtime._history('test')==runtime.ledger.history('test')
    later=runtime.ledger.status('test')
    assert later['mode']==state['mode'] and later['calls']==state['calls']
    with sqlite3.connect(runtime.ledger.path) as db:
        assert db.execute('SELECT paused FROM stage').fetchone()==(1,)


def test_existing_pause_is_preserved_by_read_only_result_view(setup, monkeypatch):
    runtime, _, call = seed(setup, monkeypatch)
    runtime.ledger.pause('Generated independent manual pause')
    view=runtime._history('test')[0]
    assert view['result']['artifact_hash'] and view['status']=='failed'
    state=runtime.ledger.status('test')
    assert state['mode']=='blocked'
    with sqlite3.connect(runtime.ledger.path) as db:
        assert db.execute('SELECT paused,reason FROM stage').fetchone()==(1,'Generated independent manual pause')


def test_changed_original_failure_receipt_cannot_be_hidden_by_view(setup, monkeypatch):
    runtime, _, call = seed(setup, monkeypatch)
    path=runtime.root/'calls'/call['id']/'application.json'
    path.rename(path.with_suffix('.preserved'))
    path.write_text(serial({'model_response_hash':digest(call['receipt']['response']),
                           'failed':True,'result':{'error':'Rewritten generated failure'}}),encoding='utf-8')
    with pytest.raises(AdmissionBlocked,match='original failed application changed'):
        runtime._history('test')
    assert runtime.ledger.call(call['id'])==call


def test_child_output_drift_at_projection_error_keeps_stage_paused(setup, monkeypatch):
    runtime, task = setup();original=ResearchTools._execute
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def produced(tools, call_id, *args):
        result=original(tools,call_id,*args)
        child=tools.folder/call_id/'workbench';child.mkdir()
        (child/'generated_placeholder.txt').write_text('No account worker executed',encoding='utf-8')
        return result
    def corrupt(*args):
        path=runtime.root/'tools/test'/call['id']/'artifact.json'
        path.rename(path.with_suffix('.preserved'))
        path.write_text('{}',encoding='utf-8')
        raise OSError('Generated projection error with output drift')
    monkeypatch.setattr(ResearchTools,'_execute',produced)
    monkeypatch.setattr(tr,'_settle',corrupt)
    with pytest.raises(AdmissionBlocked,match='original returned output changed'):
        runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])['status']=='applying'
    with sqlite3.connect(runtime.ledger.path) as db:
        paused,reason=db.execute('SELECT paused,reason FROM stage').fetchone()
    assert paused==1 and 'output drift' in reason and 'saved result rejected' in reason


def test_applying_call_with_original_return_recovers_without_reexecution(setup, monkeypatch):
    runtime,task=setup()
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def interrupted_projection(*args): raise KeyboardInterrupt('Generated process interruption after original capture')
    with monkeypatch.context() as patch:
        patch.setattr(tr,'_settle',interrupted_projection)
        with pytest.raises(KeyboardInterrupt): runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])['status']=='applying'
    application=runtime.root/'calls'/call['id']/'application.json'
    assert not application.exists()
    tm.reconcile_available(runtime.root)
    before=tr.status(runtime.root)
    def forbidden(*a,**k): pytest.fail('Interrupted application must use its original return')
    monkeypatch.setattr(ResearchTools,'execute',forbidden)
    runtime._apply(call['id'])
    after=runtime.ledger.call(call['id'])
    assert after['status']=='applied' and after['result']['artifact_hash']
    receipt=json.loads(application.read_text(encoding='utf-8'))
    assert receipt['saved_result_recovery']['producer_reexecuted'] is False
    assert receipt['saved_result_recovery']['original_failure_preserved'] is False
    assert tr.status(runtime.root)==before
    assert sr.snapshot('tools')['known_tokens']==20


def test_applying_unmeasured_interruption_cannot_adopt_local_outputs(setup, monkeypatch):
    runtime,task=setup();original=ResearchTools._execute
    call=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32},apply=False)
    def unfinished(tools,*args):
        original(tools,*args)
        raise KeyboardInterrupt('Generated interruption without measurement capture')
    with monkeypatch.context() as patch:
        patch.setattr(ResearchTools,'_execute',unfinished)
        with pytest.raises(KeyboardInterrupt): runtime._apply(call['id'])
    def forbidden(*a,**k): pytest.fail('Unmeasured local output must not cause execution')
    monkeypatch.setattr(ResearchTools,'execute',forbidden)
    with pytest.raises(AdmissionBlocked,match='saved evidence reconciliation required'):
        runtime._apply(call['id'])
    assert runtime.ledger.call(call['id'])['status']=='applying'
    assert tr.status(runtime.root)['unknown_measurements']==1
    assert not (runtime.root/'calls'/call['id']/'application.json').exists()
