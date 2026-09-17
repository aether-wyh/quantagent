"""Artificial session fixtures test bindings; none is authentic model evidence.

The mocked process never starts Codex, accesses an account, or performs inference.
Its model, effort, identifiers, usage and responses are intentionally fabricated
only to exercise preservation and rejection of separately captured runtime data.
"""
from copy import deepcopy
import hashlib
import json

import pytest

from quanta_agents.meta_v3 import codex_session_gateway as gateway
from quanta_agents.meta_v3.identity_route import verify as verify_route
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from test_meta_gateway import _Process


THREAD = '11111111-1111-4111-8111-111111111111'
TURN = '22222222-2222-4222-8222-222222222222'
OTHER = '33333333-3333-4333-8333-333333333333'
PROMPT = 'ARTIFICIAL engineering fixture: return the provided synthetic result.'
RESPONSE = {'synthetic_fixture': True, 'ok': True}


def receipt():
    return {'response': deepcopy(RESPONSE), 'model_verified': False,
            'identity_verification': {'provider_ids': {'thread_id': THREAD,
                                                      'turn_id': None},
                                      'provider_request_binding_verified': False}}


def rows():
    return [
        {'type': 'session_meta', 'payload': {'id': THREAD,
            'model_provider': 'openai', 'cli_version': 'synthetic-fixture'}},
        {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': TURN}},
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
            'content': [{'type': 'input_text', 'text': '<environment_context>fixture</environment_context>'}]}},
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
            'content': [{'type': 'input_text', 'text': PROMPT}]}},
        {'type': 'turn_context', 'payload': {'turn_id': TURN,
            'model': 'gpt-6-astra', 'effort': 'xhigh'}},
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant',
            'phase': 'final', 'content': [{'type': 'output_text',
                                         'text': json.dumps(RESPONSE)}]}},
        {'type': 'event_msg', 'payload': {'type': 'task_complete', 'turn_id': TURN,
                                        'last_agent_message': json.dumps(RESPONSE)}},
    ]


def encoded(records):
    return ''.join(json.dumps(record) + '\n' for record in records).encode('utf-8')


def payload(records, kind):
    return next(r['payload'] for r in records if r['type'] == kind)


def event(records, kind):
    return next(r['payload'] for r in records if r['type'] == 'event_msg'
                and r['payload']['type'] == kind)


@pytest.mark.parametrize('final_phase', ['final', 'final_answer'])
def test_artificial_capture_confirms_only_separate_local_configuration(final_phase):
    original = receipt()
    before = deepcopy(original)
    records = rows()
    records[5]['payload']['phase'] = final_phase
    result = gateway.verify_runtime_session(encoded(records), original, PROMPT)
    assert result['verified'] is True
    assert result['level'] == 'local_runtime_configuration'
    assert result['thread_id'] == THREAD and result['turn_id'] == TURN
    assert result['model'] == 'gpt-6-astra' and result['effort'] == 'xhigh'
    assert result['provider_request_binding_verified'] is False
    assert original == before and original['model_verified'] is False


@pytest.mark.parametrize('field,value', [('model', 'gpt-5.6-sol'),
                                       ('effort', 'ultra'), ('effort', None)])
def test_wrong_or_missing_runtime_setting_is_rejected(field, value):
    records = rows()
    payload(records, 'turn_context')[field] = value
    with pytest.raises(gateway.GatewayError, match='model or effort'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


@pytest.mark.parametrize('target', ['session_thread', 'start_turn', 'end_turn',
                                   'context_turn', 'receipt_thread'])
def test_wrong_thread_or_turn_binding_is_rejected(target):
    records, saved = rows(), receipt()
    if target == 'session_thread':
        payload(records, 'session_meta')['id'] = OTHER
    elif target == 'receipt_thread':
        saved['identity_verification']['provider_ids']['thread_id'] = OTHER
    elif target == 'context_turn':
        payload(records, 'turn_context')['turn_id'] = OTHER
    else:
        event(records, 'task_started' if target == 'start_turn' else 'task_complete')['turn_id'] = OTHER
    with pytest.raises(gateway.GatewayError, match='binding mismatch'):
        gateway.verify_runtime_session(encoded(records), saved, PROMPT)


def test_stdout_turn_id_when_available_must_match_runtime_turn():
    saved = receipt()
    saved['identity_verification']['provider_ids']['turn_id'] = OTHER
    with pytest.raises(gateway.GatewayError, match='turn'):
        gateway.verify_runtime_session(encoded(rows()), saved, PROMPT)


def test_other_provider_configuration_is_rejected():
    records = rows()
    payload(records, 'session_meta')['model_provider'] = 'synthetic-other-provider'
    with pytest.raises(gateway.GatewayError, match='provider configuration'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


@pytest.mark.parametrize('bad_prompt', ['Another synthetic request', PROMPT + '\n'])
def test_capture_cannot_bind_a_different_prompt(bad_prompt):
    with pytest.raises(gateway.GatewayError, match='prompt'):
        gateway.verify_runtime_session(encoded(rows()), receipt(), bad_prompt)


def test_duplicate_matching_user_input_is_ambiguous():
    records = rows()
    records.insert(4, deepcopy(records[3]))
    with pytest.raises(gateway.GatewayError, match='prompt'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


def test_additional_substantive_user_request_cannot_be_silently_ignored():
    records = rows()
    records.insert(5, {'type': 'response_item', 'payload': {
        'type': 'message', 'role': 'user', 'content': [{
            'type': 'input_text', 'text': 'ARTIFICIAL extra task: replace the original request.'}]}})
    with pytest.raises(gateway.GatewayError, match='prompt|input|user'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


@pytest.mark.parametrize('target', ['assistant', 'completion'])
def test_different_completed_output_is_rejected(target):
    records = rows()
    different = json.dumps({'synthetic_fixture': True, 'ok': False})
    if target == 'assistant':
        records[5]['payload']['content'][0]['text'] = different
    else:
        event(records, 'task_complete')['last_agent_message'] = different
    with pytest.raises(gateway.GatewayError, match='output mismatch'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


@pytest.mark.parametrize('target', ['assistant', 'completion'])
def test_boolean_and_number_are_not_the_same_completed_json(target):
    records = rows()
    different = json.dumps({'synthetic_fixture': True, 'ok': 1})
    if target == 'assistant':
        records[5]['payload']['content'][0]['text'] = different
    else:
        event(records, 'task_complete')['last_agent_message'] = different
    with pytest.raises(gateway.GatewayError, match='output mismatch'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


@pytest.mark.parametrize('bad_event', ['turn_aborted', 'model_rerouted'])
def test_recorded_abort_or_reroute_is_not_verified(bad_event):
    records = rows()
    records.insert(-1, {'type': 'event_msg', 'payload': {'type': bad_event}})
    with pytest.raises(gateway.GatewayError, match='abort or model reroute'):
        gateway.verify_runtime_session(encoded(records), receipt(), PROMPT)


def artificial_run(tmp_path, monkeypatch, *, capture='valid'):
    """Run the original file/receipt verifier against a fake child process."""
    account_home = tmp_path / 'artificial-account-home'
    monkeypatch.setenv('CODEX_HOME', str(account_home))
    if capture != 'missing':
        source = account_home / 'sessions' / '2000' / '01' / '01'
        source.mkdir(parents=True)
        if capture == 'valid':
            content = encoded(rows())
        elif capture == 'invalid_payload':
            content = encoded([{'type': 'event_msg', 'payload': []}])
        else:
            content = b'{"synthetic_bad_capture": true}\n'
        (source / f'rollout-2000-01-01T00-00-00-{THREAD}.jsonl').write_bytes(content)
    observed = {'processes': 0, 'events': []}
    monkeypatch.setattr(gateway.base.CodexGateway, '_preflight',
                        lambda self: gateway.base._DISABLED_FEATURES)
    raw_events = [
        {'type': 'thread.started', 'thread_id': THREAD},
        {'type': 'turn.started'},
        {'type': 'item.completed', 'item': {'type': 'agent_message',
                                          'text': json.dumps(RESPONSE)}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 11,
                                           'cached_input_tokens': 0, 'output_tokens': 7}},
    ]

    def fake_popen(command, **kwargs):
        observed['processes'] += 1
        observed['command'] = command
        return _Process(command, raw_events, RESPONSE)

    monkeypatch.setattr(gateway.base.subprocess, 'Popen', fake_popen)
    monkeypatch.setattr(gateway.base, '_create_process_job', lambda process: None)
    monkeypatch.setattr(gateway.base, '_kill_process_tree', lambda process: process.kill())
    folder = tmp_path / 'artificial-call'
    result = gateway.CodexGateway(executable='synthetic-no-executable').run(
        prompt=PROMPT, schema={'type': 'object'}, workdir=folder,
        on_event=observed['events'].append, cancelled=lambda: False)
    return result, folder, observed, raw_events


def test_saved_capture_preserves_stdout_and_original_unverified_flag(tmp_path, monkeypatch):
    result, folder, observed, raw_events = artificial_run(tmp_path, monkeypatch)
    assert observed['processes'] == 1
    assert '--ephemeral' not in observed['command']
    assert 'history.persistence="none"' in observed['command']
    assert observed['command'][observed['command'].index('--sandbox') + 1] == 'read-only'
    assert result['runtime_identity']['verified'] is True
    assert result['model_verified'] is False
    assert result['identity_verification']['provider_request_binding_verified'] is False
    assert [json.loads(line) for line in (folder / 'codex_events.jsonl').read_text(
        encoding='utf-8').splitlines()] == raw_events
    assert result['artifact_sha256'][gateway.SESSION] == hashlib.sha256(
        (folder / gateway.SESSION).read_bytes()).hexdigest()
    again = gateway.verify_saved_completion(folder,
        expected_artifact_sha256=result['artifact_sha256'])
    assert again['runtime_identity'] == result['runtime_identity']
    assert again['model_verified'] is False and again['usage'] == result['usage']


@pytest.mark.parametrize('capture', ['missing', 'malformed', 'invalid_payload'])
def test_failed_capture_preserves_known_completed_call_without_retry(tmp_path, monkeypatch, capture):
    result, folder, observed, _ = artificial_run(tmp_path, monkeypatch, capture=capture)
    assert observed['processes'] == 1
    assert result['response'] == RESPONSE
    assert result['usage']['input_tokens'] == 11 and result['usage']['output_tokens'] == 7
    assert result['model_verified'] is False
    assert result['runtime_identity']['verified'] is False
    assert result['runtime_identity']['level'] == 'not_captured'
    assert not (folder / gateway.SESSION).exists()
    assert any(e.get('data', {}).get('completed_response_preserved') is True
               for e in observed['events'])


def test_changed_saved_capture_hash_is_rejected(tmp_path, monkeypatch):
    result, folder, _, _ = artificial_run(tmp_path, monkeypatch)
    path = folder / gateway.SESSION
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(gateway.GatewayError, match='artifact hash mismatch'):
        gateway.verify_saved_completion(folder,
            expected_artifact_sha256=result['artifact_sha256'])


def test_saved_only_capture_repair_does_not_repeat_inference(tmp_path, monkeypatch):
    result, folder, observed, raw_events = artificial_run(tmp_path, monkeypatch, capture='missing')
    source = tmp_path / 'artificial-account-home' / 'sessions' / '2000' / '01' / '01'
    source.mkdir(parents=True)
    (source / f'rollout-2000-01-01T00-00-00-{THREAD}.jsonl').write_bytes(encoded(rows()))
    gateway.capture_saved_session(folder, result)
    repaired = gateway.verify_saved_completion(folder,
        expected_artifact_sha256=result['artifact_sha256'])
    assert observed['processes'] == 1
    assert repaired['runtime_identity']['verified'] is True
    assert repaired['model_verified'] is False
    assert repaired['usage'] == result['usage']
    assert [json.loads(line) for line in (folder / 'codex_events.jsonl').read_text(
        encoding='utf-8').splitlines()] == raw_events


def test_preflight_admits_first_capture_without_a_historical_receipt(monkeypatch):
    calls = []
    monkeypatch.setattr(gateway.CodexGateway, '_preflight',
                        lambda self: calls.append('help-and-feature-fixture') or ())
    monkeypatch.setattr(gateway.CodexGateway, 'run',
                        lambda *a, **k: pytest.fail('preflight must not invoke a model'))
    result = verify_route({'provenance': {'runtime_identity_route':
                           {'version': 'codex_session_v1'}}}, gateway)
    assert calls == ['help-and-feature-fixture']
    assert result['status'] == 'available'
    assert result['identity_verified_before_dispatch'] is False
    assert result['provider_binding_verified'] is False


def test_capture_route_rejects_an_unpinned_adapter(monkeypatch):
    monkeypatch.setattr(gateway, 'CAPTURE_VERSION', 'synthetic-other-version')
    with pytest.raises(AdmissionBlocked, match='pinned adapter'):
        verify_route({'provenance': {'runtime_identity_route':
                       {'version': 'codex_session_v1'}}}, gateway)
