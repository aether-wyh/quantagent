"""Generated custody adversaries only; no old accounts or research are read."""
from copy import deepcopy
import json
import sqlite3
from types import SimpleNamespace

import pytest

from quanta_agents.meta_v3 import evaluation_custody as custody
from quanta_agents.meta_v3.ledger import digest, serial


@pytest.fixture
def generated_book(tmp_path, monkeypatch):
    registry = tmp_path / 'new_custody' / 'evaluations.sqlite3'
    snapshot = {
        'study_id': 'v4s1', 'closed': True, 'formal_acceptance': False,
        'trials': [
            {'id': name, 'status': 'not_started' if name in ('v3', 's3') else 'closed',
             'selection': None, 'original_final_outcome': 'abstain'}
            for name in ('v1', 's1', 'f1', 's2', 'f2', 'v2', 'f3', 'v3', 's3')],
    }
    spec = {
        'version': 'v4s1_v1_frozen_account_terms_spec_v1',
        'study_id': 'v4s1', 'trial_id': 'v1', 'task_id': 'research',
        'call_id': 'research_011_c7700a001b27',
        'original_final_call_id': 'research_014_c8a281224dcf',
        'original_final_outcome': 'abstain',
        'selection_scope': 'explicit_old_candidate_audit_not_final_selection',
        'formal_target_success': False,
        'input_file_sha256': {'generated_only.json': digest('original input')},
        'policy_sha256': digest('generated policy'),
    }
    state = SimpleNamespace(
        registry=registry, snapshot=snapshot, spec=spec,
        pins={'generated_backend.py': digest('generated implementation')},
        calls=0, before_callback=None, effect=None,
        result={'formal_target_success': False, 'financial_accepted': False,
                'original_final_outcome': 'abstain', 'selected_program': None},
    )

    def audit(bound_spec):
        state.calls += 1
        assert bound_spec == state.spec
        if state.before_callback is not None:
            state.before_callback()
        if state.effect is not None:
            state.effect()
        return deepcopy(state.result)

    backend = SimpleNamespace(build_spec=lambda: deepcopy(state.spec), audit_saved_candidate=audit)
    monkeypatch.setattr(custody, 'REGISTRY', registry)
    monkeypatch.setattr(custody, '_backend', lambda: backend)
    monkeypatch.setattr(custody, '_code_pins', lambda: deepcopy(state.pins))
    monkeypatch.setattr(custody, 'closed_study_snapshot', lambda study_id: deepcopy(state.snapshot))
    return state


def mutate_sql(state, sql, args=()):
    with sqlite3.connect(state.registry) as db:
        db.execute(sql, args)


def test_consumption_is_committed_before_backend_and_result_preserves_originals(generated_book):
    state = generated_book
    before = deepcopy(state.snapshot)
    frozen = custody.freeze('generated_audit')

    def observe_from_second_readonly_connection():
        with sqlite3.connect(state.registry.resolve().as_uri() + '?mode=ro', uri=True) as reader:
            reader.execute('PRAGMA query_only=ON')
            row = reader.execute('SELECT state,token,consumed_at,receipt FROM evaluations').fetchone()
            assert row[0] == 'CONSUMED' and row[1] and row[2] is not None and row[3] is None
            assert reader.execute('SELECT COUNT(*) FROM evaluation_events').fetchone()[0] == 2

    state.before_callback = observe_from_second_readonly_connection
    result = custody.run('generated_audit')
    assert result['state'] == 'COMPLETE' and state.calls == 1
    assert result['manifest_hash'] == frozen['manifest_hash']
    assert state.snapshot == before == result['manifest']['study_snapshot']
    assert len(result['manifest']['study_snapshot']['trials']) == 9
    assert all(row['selection'] is None for row in result['manifest']['study_snapshot']['trials'])
    receipt = result['receipt']
    assert receipt['original_selections_changed'] is False
    assert receipt['new_research_opportunities'] == 0
    assert receipt['formal_target_success'] is False and receipt['financial_accepted'] is False
    assert result['manifest']['audit_inputs']['original_final_outcome'] == 'abstain'
    assert result['formal_target_success'] is False


def test_repeat_run_returns_identical_receipt_without_backend(generated_book):
    state = generated_book
    custody.freeze('original')
    first = custody.run('original')
    second = custody.run('original')
    assert first == second and state.calls == 1


def test_repeat_while_first_backend_is_active_only_observes_consumption(generated_book):
    state = generated_book
    custody.freeze('in_flight')
    observations = []
    state.before_callback = lambda: observations.append(custody.run('in_flight'))
    result = custody.run('in_flight')
    assert result['state'] == 'COMPLETE' and state.calls == 1
    assert len(observations) == 1
    assert observations[0]['state'] == 'CONSUMED' and observations[0]['receipt'] is None
    assert observations[0]['token'] == result['token']


@pytest.mark.parametrize('consume', [False, True])
def test_same_subject_cannot_get_another_freeze_by_changing_display_id(generated_book, consume):
    state = generated_book
    custody.freeze('original')
    if consume:
        custody.run('original')
    for alias in ('original', 'replacement'):
        with pytest.raises(ValueError, match='already registered'):
            custody.freeze(alias)
    with sqlite3.connect(state.registry) as db:
        assert db.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0] == 1


def test_keyboard_interrupt_stays_consumed_and_never_redispatches(generated_book):
    state = generated_book
    custody.freeze('interrupted')

    def interrupt():
        raise KeyboardInterrupt('generated abrupt stop')

    state.effect = interrupt
    with pytest.raises(KeyboardInterrupt):
        custody.run('interrupted')
    observed = custody.inspect('interrupted')
    assert observed['state'] == 'CONSUMED' and observed['receipt'] is None
    assert custody.run('interrupted') == observed and state.calls == 1


def test_ordinary_backend_failure_is_terminal_and_never_redispatches(generated_book):
    state = generated_book
    custody.freeze('failed')

    def fail():
        raise ValueError('generated unverifiable account')

    state.effect = fail
    result = custody.run('failed')
    assert result['state'] == 'INCOMPLETE_TERMINAL'
    assert result['receipt']['backend_result'] is None
    assert result['receipt']['error'] == {'type': 'ValueError', 'message': 'generated unverifiable account'}
    assert custody.run('failed') == result and state.calls == 1


@pytest.mark.parametrize('drift', ['code', 'snapshot', 'inputs'])
def test_pre_dispatch_drift_rejects_without_consumption(generated_book, drift):
    state = generated_book
    custody.freeze('drift')
    if drift == 'code':
        state.pins['generated_backend.py'] = digest('changed implementation')
    elif drift == 'snapshot':
        state.snapshot['trials'].pop()
    else:
        state.spec['input_file_sha256']['generated_only.json'] = digest('changed input')
    with pytest.raises(ValueError, match='changed|drift'):
        custody.run('drift')
    assert custody.inspect('drift')['state'] == 'FROZEN' and state.calls == 0


@pytest.mark.parametrize('drift', ['code', 'snapshot'])
def test_drift_during_backend_consumes_opportunity_with_terminal_error(generated_book, drift):
    state = generated_book
    custody.freeze('during')

    def change():
        if drift == 'code':
            state.pins['generated_backend.py'] = digest('changed while executing')
        else:
            state.snapshot['trials'][0]['selection'] = {'replacement': 'unapproved'}

    state.effect = change
    result = custody.run('during')
    assert result['state'] == 'INCOMPLETE_TERMINAL'
    assert 'changed during audit' in result['receipt']['error']['message']
    assert custody.run('during') == result and state.calls == 1


@pytest.mark.parametrize('target', ['manifest', 'event', 'exposure', 'token', 'state'])
def test_custody_tampering_is_rejected_before_dispatch(generated_book, target):
    state = generated_book
    custody.freeze('tamper')
    if target == 'manifest':
        mutate_sql(state, 'UPDATE evaluations SET manifest=?', (serial({'rewritten': True}),))
    elif target == 'event':
        mutate_sql(state, 'UPDATE evaluation_events SET body=?', (serial({'action': 'rewritten'}),))
    elif target == 'exposure':
        mutate_sql(state, 'UPDATE evaluations SET exposure_key=?', (digest('a different opportunity'),))
    elif target == 'token':
        mutate_sql(state, 'UPDATE evaluations SET token=?', ('unexpected dispatch',))
    else:
        mutate_sql(state, "UPDATE evaluations SET state='COMPLETE'")
    with pytest.raises(ValueError):
        custody.inspect('tamper')
    with pytest.raises(ValueError):
        custody.run('tamper')
    assert state.calls == 0


def test_tampered_exposure_cannot_create_alias_registration(generated_book):
    state = generated_book
    custody.freeze('original')
    mutate_sql(state, 'UPDATE evaluations SET exposure_key=?', (digest('forged alias key'),))
    with pytest.raises(ValueError):
        custody.freeze('replacement')
    with sqlite3.connect(state.registry) as db:
        assert db.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0] == 1


@pytest.mark.parametrize('rewrite', ['formal_route', 'audit_subject', 'abstention'])
def test_locally_rehashed_manifest_still_cannot_change_fixed_scope(generated_book, rewrite):
    state = generated_book
    frozen = custody.freeze('local_rehash')
    manifest = deepcopy(frozen['manifest'])
    if rewrite == 'formal_route':
        manifest['kind'] = 'formal_final_release'
    elif rewrite == 'audit_subject':
        manifest['audit_subject'] = 'v4s1/v1/replacement_selected_candidate'
    else:
        manifest['audit_inputs']['original_final_outcome'] = 'strategy_for_development'
        manifest['audit_inputs_hash'] = digest(manifest['audit_inputs'])
    manifest_hash = digest(manifest)
    exposure_key = digest({'kind': manifest['kind'], 'study_id': manifest['study_id'],
                           'subject': manifest['audit_subject']})
    event_body = {'action': 'freeze', 'manifest_hash': manifest_hash}
    event_hash = digest({'ordinal': 1, 'previous_hash': None, 'body': event_body})
    with sqlite3.connect(state.registry) as db:
        db.execute('UPDATE evaluations SET manifest=?,manifest_hash=?,exposure_key=?',
                   (serial(manifest), manifest_hash, exposure_key))
        db.execute('UPDATE evaluation_events SET body=?,event_hash=?', (serial(event_body), event_hash))
    with pytest.raises(ValueError, match='route drift|input scope drift'):
        custody.run('local_rehash')
    assert state.calls == 0


def test_saved_receipt_tamper_is_detected_without_new_dispatch(generated_book):
    state = generated_book
    custody.freeze('receipt')
    custody.run('receipt')
    mutate_sql(state, 'UPDATE evaluations SET receipt=?', (serial({'invented': 'result'}),))
    with pytest.raises(ValueError):
        custody.run('receipt')
    assert state.calls == 1


def test_formal_release_rejects_before_source_backend_or_book_access(generated_book, monkeypatch):
    state = generated_book

    def forbidden(*args, **kwargs):
        raise AssertionError('formal refusal attempted a source or book read')

    for name in ('closed_study_snapshot', '_backend', '_code_pins', '_db'):
        monkeypatch.setattr(custody, name, forbidden)
    with pytest.raises(ValueError, match='formal_final_release unavailable'):
        custody.freeze('formal_attempt', kind='formal_final_release')
    assert not state.registry.exists() and not state.registry.parent.exists()


def test_inspection_and_repeat_terminal_run_do_not_reenter_sources(generated_book, monkeypatch):
    custody.freeze('read_only')
    expected = custody.run('read_only')

    def forbidden(*args, **kwargs):
        raise AssertionError('saved inspection attempted source access')

    for name in ('closed_study_snapshot', '_backend', '_code_pins'):
        monkeypatch.setattr(custody, name, forbidden)
    assert custody.inspect('read_only') == expected
    assert custody.run('read_only') == expected


@pytest.mark.parametrize('invalid', [None, [], {'formal_target_success': True}])
def test_backend_cannot_supply_formal_acceptance_or_invalid_result(generated_book, invalid):
    state = generated_book
    custody.freeze('invalid_result')
    state.result = invalid
    result = custody.run('invalid_result')
    assert result['state'] == 'INCOMPLETE_TERMINAL'
    assert result['receipt']['backend_result'] is None
    assert result['receipt']['formal_target_success'] is False
    assert state.calls == 1
