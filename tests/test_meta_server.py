import json
from copy import deepcopy
import threading
import urllib.error
import urllib.request

import pytest

from quanta_agents.meta.runtime import Engine
from quanta_agents.meta.server import StateLock, make_server


@pytest.fixture
def service(tmp_path):
    engine = Engine(tmp_path)
    server = make_server(engine, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield engine, f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join(5)
    engine.close()


def request(url, body=None, headers=None):
    headers = headers or {}
    if body is not None:
        headers.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def test_api_create_list_events_artifacts(service):
    engine, url = service
    assert request(url + '/api/health')['effort'] == 'xhigh'
    run_id = request(url + '/api/runs', {'mode': 'fixture'})['run_id']
    engine.worker.join(10)
    run = request(url + '/api/runs/' + run_id)
    assert run['status'] == 'completed'
    assert request(url + '/api/runs')['runs'][0]['id'] == run_id
    page = request(url + '/api/runs/' + run_id + '/events?after=0')
    assert page['events']
    assert request(url + '/api/runs/' + run_id + '/events?after=' + str(page['last_id']))['events'] == []
    comparison = request(url + '/api/runs/' + run_id + '/artifacts/comparison.json')
    assert comparison['promotion'] is False
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/runs/' + run_id + '/artifacts/..%2Fledger.sqlite3')
    assert error.value.code == 404


def test_cross_origin_and_host_rebinding_are_rejected(service):
    _, url = service
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/runs', {'mode': 'fixture'}, {'Origin': 'https://example.invalid'})
    assert error.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/health', headers={'Host': 'attacker.invalid'})
    assert error.value.code == 403


def test_bad_modes_model_overrides_and_non_objects_are_rejected(service):
    _, url = service
    for body in [{'mode': 'unknown'}, {'mode': 'fixture', 'model': 'cheap'}, ['fixture']]:
        with pytest.raises(urllib.error.HTTPError) as error:
            request(url + '/api/runs', body)
        assert error.value.code == 400


def test_two_workers_cannot_own_one_state_directory(tmp_path):
    lock = StateLock(tmp_path)
    try:
        with pytest.raises(RuntimeError):
            StateLock(tmp_path)
    finally:
        lock.close()


@pytest.fixture
def recording_service(tmp_path):
    """Exercise the HTTP boundary without market loading or model calls."""
    class RecordingStore:
        def __init__(self):
            self.records = {'source-run': {'id': 'source-run', 'steps': {'meta_proposal': {
                'name': 'Frozen method', 'research_instructions': 'Inspect counter-evidence.',
                'source_run_id': 'old-origin', 'architecture_hash': 'frozen-hash',
            }}}}

        def get(self, run_id):
            return deepcopy(self.records[run_id])

        def runs(self):
            return [deepcopy(item) for item in self.records.values()]

    class RecordingEngine:
        active = None

        def __init__(self):
            self.root = tmp_path
            self.store = RecordingStore()
            self.requests = []
            self.source_hash = 'source-loaded-v1'

        def source_manifest(self):
            return {'hash': self.source_hash}

        def create(self, **options):
            self.requests.append(deepcopy(options))
            run_id = 'created-' + str(len(self.requests))
            config = options.get('research_config', {})
            self.store.records[run_id] = {'id': run_id, 'request_key': options.get('request_key'),
                'config': {'case_config': options.get('case_config', {}), 'research_config': config,
                           'evaluation_split': config.get('evaluation_split')},
                'steps': {}, 'research': {'baseline': []}, 'self_checks': [], 'calls': []}
            return run_id

        def get(self, run_id):
            return self.store.get(run_id)

    engine = RecordingEngine()
    server = make_server(engine, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield engine, f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_api_resolves_frozen_candidate_only_from_same_ledger(recording_service):
    engine, url = recording_service
    payload = {'mode': 'fixture', 'case': 'ashare', 'task': 'relative_strength',
               'research_calls': 12, 'frozen_candidate_run_id': 'source-run',
               'research_order': ['candidate', 'baseline'], 'evaluation_split': 'development',
               'only_architecture': 'candidate', 'request_key': 'batch_task_01-candidate'}
    result = request(url + '/api/runs', payload)
    options = engine.requests[-1]
    assert options['case_config'] == {'task': 'relative_strength'}
    assert options['request_key'] == 'batch_task_01-candidate'
    research = options['research_config']
    assert research['calls_per_architecture'] == 12
    assert research['research_order'] == ['candidate', 'baseline']
    assert research['evaluation_split'] == 'development'
    assert research['only_architecture'] == 'candidate'
    assert research['frozen_candidate']['source_run_id'] == 'source-run'
    assert research['frozen_candidate']['research_instructions'] == 'Inspect counter-evidence.'
    assert engine.store.get('source-run')['steps']['meta_proposal']['source_run_id'] == 'old-origin'
    listing = request(url + '/api/runs')['runs']
    summary = next(item for item in listing if item['id'] == result['run_id'])
    assert summary['task_key'] == 'relative_strength'
    assert summary['evaluation_split'] == 'development'
    assert summary['only_architecture'] == 'candidate'
    assert summary['request_key'] == 'batch_task_01-candidate'
    assert 'config' not in summary and 'research' not in summary


def test_api_defaults_preserve_synthetic_and_six_call_confirmation(recording_service):
    engine, url = recording_service
    request(url + '/api/runs', {'mode': 'fixture'})
    assert engine.requests[-1] == {'mode': 'fixture', 'case': 'synthetic'}
    request(url + '/api/runs', {'mode': 'fixture', 'case': 'ashare'})
    assert engine.requests[-1]['case_config'] == {'task': 'price_repair'}
    assert engine.requests[-1]['research_config'] == {
        'calls_per_architecture': 6, 'research_order': ['baseline', 'candidate'],
        'evaluation_split': 'confirmation', 'only_architecture': None}


def test_existing_frozen_wrapper_can_be_reused_without_execution_metadata(recording_service):
    engine, url = recording_service
    engine.store.records['source-run']['steps']['meta_proposal'].update(
        frozen=True, source_proposal={'name': 'earlier'}, source_proposal_hash='earlier-hash')
    request(url + '/api/runs', {'mode': 'fixture', 'case': 'ashare',
                              'frozen_candidate_run_id': 'source-run', 'only_architecture': 'candidate'})
    frozen = engine.requests[-1]['research_config']['frozen_candidate']
    assert frozen['source_run_id'] == 'source-run'
    assert frozen['research_instructions'] == 'Inspect counter-evidence.'
    assert 'frozen' not in frozen and 'source_proposal' not in frozen


@pytest.mark.parametrize('calls', [6, 7, 12, 18])
def test_api_accepts_integer_research_call_range(recording_service, calls):
    engine, url = recording_service
    request(url + '/api/runs', {'mode': 'fixture', 'case': 'ashare', 'research_calls': calls})
    assert engine.requests[-1]['research_config']['calls_per_architecture'] == calls


@pytest.mark.parametrize('controls', [
    {'task': 'unregistered'}, {'task': ['price_repair']}, {'research_calls': 5},
    {'research_calls': 19}, {'research_calls': True}, {'research_calls': 6.0},
    {'research_order': ['baseline', 'baseline']}, {'research_order': 'baseline'},
    {'research_order': ['candidate', 'baseline']}, {'evaluation_split': 'final'},
    {'only_architecture': 'both'}, {'only_architecture': 'candidate'},
    {'frozen_candidate_run_id': '../candidate.json'}, {'frozen_candidate_run_id': 'C:\\candidate.json'},
    {'frozen_candidate': {'research_instructions': 'override'}},
    {'case_config': {'data_root': 'elsewhere'}}, {'model': 'cheap'},
    {'request_key': ''}, {'request_key': 'has spaces'}, {'request_key': '../x'},
    {'request_key': True}, {'request_key': 'x' * 161},
])
def test_api_rejects_invalid_and_undeclared_research_controls(recording_service, controls):
    engine, url = recording_service
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/runs', {'mode': 'fixture', 'case': 'ashare', **controls})
    assert error.value.code == 400
    assert engine.requests == []


@pytest.mark.parametrize('field,value', [
    ('task', 'price_repair'), ('research_calls', 6), ('research_order', ['baseline', 'candidate']),
    ('evaluation_split', 'confirmation'), ('frozen_candidate_run_id', 'source-run'),
    ('only_architecture', None),
])
def test_synthetic_cannot_silently_accept_ashare_controls(recording_service, field, value):
    engine, url = recording_service
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/runs', {'mode': 'fixture', 'case': 'synthetic', field: value})
    assert error.value.code == 400
    assert engine.requests == []


def test_frozen_source_must_exist_and_contain_completed_proposal(recording_service):
    engine, url = recording_service
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/runs', {'case': 'ashare', 'frozen_candidate_run_id': 'unknown-run'})
    assert error.value.code == 404
    for proposal in [None, {}, {'name': 'bad', 'research_instructions': 1}]:
        engine.store.records['source-run']['steps']['meta_proposal'] = proposal
        with pytest.raises(urllib.error.HTTPError) as error:
            request(url + '/api/runs', {'case': 'ashare', 'frozen_candidate_run_id': 'source-run'})
        assert error.value.code == 400
    assert engine.requests == []


def test_loaded_source_identity_stays_fixed_and_blocks_creation_after_disk_change(recording_service):
    engine, url = recording_service
    assert request(url + '/api/health')['source_hash'] == 'source-loaded-v1'
    engine.source_hash = 'different-on-disk'
    assert request(url + '/api/health')['source_hash'] == 'source-loaded-v1'
    with pytest.raises(urllib.error.HTTPError) as error:
        request(url + '/api/runs', {'mode': 'fixture'})
    assert error.value.code == 409
    assert '重启服务' in json.load(error.value)['error']
    assert engine.requests == []


def test_batch_api_returns_compact_report_only_and_keeps_missing_usage_unknown(recording_service):
    engine, url = recording_service
    assert request(url + '/api/batches') == {'batches': []}
    folder = engine.root / 'batches' / 'batch-01'
    folder.mkdir(parents=True)
    report = {'batch_id': 'batch-01', 'status': 'waiting', 'scope': 'development_only',
              'updated_at': '2026-09-06T02:00:00Z', 'counts': {'planned': 8, 'completed': 2,
                  'failed': 1, 'not_started': 4, 'active': 1, 'cancelled': 0, 'attention': 0},
              'usage': {'known_tokens': 100_000, 'is_partial': True, 'unknown_entries': 1,
                        'reserved_tokens': 1_000_000, 'accident_token_limit': 8_000_000},
              'limits': {'hard_tokens': 8_000_000, 'max_wall_seconds': 86400},
              'elapsed_seconds': 91.5, 'current_entry_id': 'task_repeat_candidate',
              'current_run_id': 'created-1', 'promotion': False, 'formal_target_success': False,
              'entries': [{'prompt': 'PRIVATE_ENTRY_MUST_NOT_BE_EXPOSED'}]}
    (folder / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    (folder / 'plan.json').write_text('invalid plan is intentionally not read', encoding='utf-8')
    result = request(url + '/api/batches')['batches'][0]
    assert result['counts']['planned'] == 8 and result['usage']['known_tokens'] == 100_000
    assert result['usage']['is_partial'] is True
    assert result['limits']['reserve_tokens_per_entry'] is None
    assert result['current_entry_id'] == 'task_repeat_candidate'
    assert 'entries' not in result and 'PRIVATE_ENTRY' not in json.dumps(result)
    assert engine.requests == []


def test_batch_api_reports_unavailable_instead_of_inventing_zero_counts(recording_service):
    engine, url = recording_service
    folder = engine.root / 'batches' / 'broken-batch'
    folder.mkdir(parents=True)
    (folder / 'report.json').write_text('{broken', encoding='utf-8')
    result = request(url + '/api/batches')['batches'][0]
    assert result['status'] == 'unavailable'
    assert 'counts' not in result and 'usage' not in result
    assert '未知' in result['report_error']
    assert engine.requests == []
