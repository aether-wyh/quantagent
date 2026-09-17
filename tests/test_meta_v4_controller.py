"""Black-box scheduling counterexamples. Scripted gateway, actual tools/ledger.

All generated receipts and token numbers are fixtures, never supplier evidence.
"""
import json
import sqlite3
import time
from pathlib import Path

import pytest

from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.controller_plan import VERSION, validate
from quanta_agents.meta_v3.ledger import AdmissionBlocked, Ledger, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime, action_schema, source_pins
from test_meta_v3_research_entry import fixture


def contracts(ids):
    return {'version': VERSION, 'work': {k: {
        'question': 'Does this supplied input support a research conclusion?',
        'necessary_evidence': ['Full declared input coverage and its limitations'],
        'depends_on': [], 'unlocks': 'Decide whether additional source work is useful',
        'stop_condition': 'Inspect coverage once, then report insufficient market evidence'
    } for k in ids}}


def stage(tmp_path, *, scoped=True, missing=True, dependencies=False):
    tasks = {}
    for name in ('unavailable', 'independent'):
        case = fixture.prepare(tmp_path / name, flat=True)
        tasks[name] = {'idea': 'Evaluate the supplied information.', 'documents': [],
                       'case': case, 'case_hash': digest(case)}
    provenance = {'source_pins': source_pins()}
    if scoped:
        policy = contracts(tasks)
        if dependencies:
            policy['work']['independent']['depends_on'] = ['unavailable']
        provenance['controller_policy'] = policy
    ledger = Ledger.create(tmp_path / 'stage', tasks=tasks,
        policy=ClosingPolicy(task_calls=3, stage_calls=6),
        deadline_epoch=time.time() + 7200, provenance=provenance)
    if missing:
        artifact = tasks['unavailable']['case']['raw_source_bindings']['source_artifacts'][0]
        (Path(artifact['root']) / artifact['rows_file']).unlink()
    return ResearchRuntime(ledger.root)


def scripted_gateway(runtime, monkeypatch, *, verified=True, verbose=False):
    calls = []
    receipts = {}
    monkeypatch.setattr(runtime, 'verify_identity_route', lambda: {
        'status': 'available', 'engineering_fixture': True, 'provider_binding_verified': False})

    def run(self, *, prompt, schema, workdir, **kwargs):
        body = json.loads(prompt)
        intent = json.loads((Path(workdir) / 'intent.json').read_text(encoding='utf-8'))
        task_id = intent['task_id']
        calls.append(task_id)
        history = body['own_complete_action_history']
        if not history:
            action, args = 'inspect_inputs', {'table': 'coverage', 'offset': 0, 'limit': 32}
        else:
            action = 'submit_research_report'
            args = {'outcome': 'abstain', 'conclusion': 'Generated input cannot establish a real-market edge.',
                'evidence_ids': [history[0]['id']], 'program_evidence_id': None,
                'limitations': ['Scripted engineering fixture, no model research'],
                'next_step': 'Obtain admissible real evidence', 'falsifiers': ['Independent real evidence is available']}
        response = {'action': action, 'arguments_json': json.dumps(args),
            'public_summary': 'Scripted test response, not a model observation',
            'self_review': dict.fromkeys(('assessment', 'uncertainty', 'next_step', 'falsifier'), 'Generated fixture only')}
        if verbose:
            response['public_summary'] = 'Explicit engineering source. ' + 'x' * 3900
            response['self_review'] = {key: key + ': ' + 'y' * 1900 for key in response['self_review']}
        runtime.gateway_module._validate_output(response, schema)
        receipt = {'response': response, 'usage': {'input_tokens': 10, 'output_tokens': 10},
            'request_identity': {'intent_id': intent['intent_id']}, 'artifact_sha256': {},
            'model_verified': verified, 'engineering_fixture': True}
        receipts[intent['intent_id']] = receipt
        (Path(workdir) / 'scripted_receipt.json').write_text(json.dumps(receipt), encoding='utf-8')

    monkeypatch.setattr(runtime.gateway_module.CodexGateway, 'run', run)
    monkeypatch.setattr(runtime.gateway_module, 'verify_saved_completion',
        lambda folder, **kwargs: receipts[Path(folder).name])
    return calls


def test_same_missing_file_blocks_legacy_but_scoped_entry_executes_independent_tools(tmp_path, monkeypatch):
    old = stage(tmp_path / 'legacy', scoped=False)
    old_calls = scripted_gateway(old, monkeypatch)
    with pytest.raises(FileNotFoundError):
        old.run()
    assert old_calls == []
    new = stage(tmp_path / 'v4')
    new_calls = scripted_gateway(new, monkeypatch)
    status = new.run()
    assert new_calls == ['independent', 'independent']
    assert status['tasks']['independent']['terminal'] == 'submitted'
    assert status['tasks']['unavailable']['terminal'] is None
    assert status['work_schedule']['stage_disposition'] == 'blocked_partial'
    assert status['work_schedule']['tasks']['unavailable']['status'] == 'blocked_task_source'
    rows = new.ledger.history('independent')
    assert rows[0]['result']['action'] == 'inspect_inputs'
    assert (new.root / 'tools' / 'independent' / rows[0]['id'] / 'artifact.json').is_file()
    assert rows[1]['result']['legal_submission'] and not rows[1]['result']['formal_target_success']
    with sqlite3.connect(new.ledger.path) as db:
        assert db.execute("SELECT count(*) FROM events WHERE kind='work_selection'").fetchone()[0] >= 2
    assert new.run()['tasks']['independent']['terminal'] == 'submitted'
    assert len(new_calls) == 2, 'Returning to a partially blocked stage must not repeat finished work'


def test_dependency_blocks_only_its_consumer_and_no_gateway_is_needed(tmp_path, monkeypatch):
    runtime = stage(tmp_path, dependencies=True)
    calls = scripted_gateway(runtime, monkeypatch)
    state = runtime.run()
    assert calls == []
    assert state['work_schedule']['tasks']['independent']['status'] == 'blocked_dependency'
    assert all(not s['calls'] for s in state['tasks'].values())


def test_v4_prompt_adds_bounded_index_for_actual_omitted_history(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    scripted_gateway(runtime, monkeypatch, verbose=True)
    runtime.run()
    calls = runtime.ledger.status('independent')['calls']
    prompt = json.loads(runtime.ledger.call(calls[-1]['id'])['intent']['prompt'])
    index = prompt['working_evidence_index']
    assert index['projection'] == 'omitted_only' and index['rows']
    assert len(json.dumps(index, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) <= 12000
    assert 'context_projection' in prompt['own_complete_action_history'][0]['response']
    original = runtime.ledger.history('independent')[0]['response']
    assert original['self_review']['falsifier'].endswith('y' * 1900)


def test_shared_pause_is_not_misreported_as_local_source_issue(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    runtime.ledger.pause('Unresolved shared execution evidence')
    calls = scripted_gateway(runtime, monkeypatch)
    state = runtime.run()
    assert calls == []
    assert all(row['status'] == 'blocked_shared_gate' for row in state['work_schedule']['tasks'].values())


def test_unresolved_call_on_unavailable_task_keeps_shared_reservation(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    intent = runtime.ledger.reserve('unavailable', ('submit_research_report',),
        lambda menu, state, decision: ('Explicit pending-call fixture', action_schema(menu)))
    calls = scripted_gateway(runtime, monkeypatch)
    with pytest.raises(FileNotFoundError):
        runtime.run()
    assert calls == []
    assert runtime.ledger.call(intent['intent_id'])['status'] == 'pending'
    assert runtime.ledger.status('independent')['unknown_or_pending_reserve'] == 80000


def test_v4_unverified_runtime_identity_cannot_execute_tools_or_buy_a_retry(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    calls = scripted_gateway(runtime, monkeypatch, verified=False)
    for _ in range(2):
        with pytest.raises(AdmissionBlocked, match='runtime model/effort identity unverified'):
            runtime.run()
    assert calls == ['independent']
    assert not list((runtime.root / 'tools').rglob('artifact.json'))
    state = runtime.ledger.status('independent')
    assert state['calls'][0]['status'] == 'received' and state['known_tokens'] == 20


def test_code_drift_remains_global_and_does_not_dispatch(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    calls = scripted_gateway(runtime, monkeypatch)
    import quanta_agents.meta_v3.runtime as runtime_module
    monkeypatch.setattr(runtime_module, 'source_pins', lambda: {'different': 'hash'})
    with pytest.raises(AdmissionBlocked, match='research source drift'):
        runtime.run()
    assert calls == []


def test_missing_capture_route_blocks_before_any_new_model_reservation(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail('Known missing identity cannot justify a paid probe')
    monkeypatch.setattr(runtime.gateway_module.CodexGateway, 'run', forbidden)
    result = runtime.run()
    assert result['work_schedule']['tasks']['independent']['status'] == 'blocked_runtime_identity'
    assert result['tasks']['independent']['calls'] == []
    assert result['tasks']['independent']['known_tokens'] == 0


def test_missing_sources_cannot_keep_expired_task_open(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    calls = scripted_gateway(runtime, monkeypatch)
    frozen_time = runtime.plan['deadline_epoch'] + 1
    monkeypatch.setattr(time, 'time', lambda: frozen_time)
    state = runtime.run()
    assert calls == []
    assert all(s['terminal'] == 'terminal_without_submission' for s in state['tasks'].values())
    assert state['work_schedule']['stage_disposition'] == 'all_tasks_terminal'


def test_cycles_and_empty_information_contracts_rejected():
    policy = contracts(('a', 'b'))
    policy['work']['a']['depends_on'] = ['b']
    policy['work']['b']['depends_on'] = ['a']
    with pytest.raises(AdmissionBlocked, match='cyclic'):
        validate(policy, {'a': {}, 'b': {}})
    policy = contracts(('a',))
    policy['work']['a']['question'] = ' '
    with pytest.raises(AdmissionBlocked, match='substantive'):
        validate(policy, {'a': {}})
