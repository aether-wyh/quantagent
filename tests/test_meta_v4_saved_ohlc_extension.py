"""Generated prices and stubbed parent receipt: no paid request or market claim.

The date-axis metadata comes from the previously frozen 2019 scope. Every test
price is generated here. The source pin and authenticated-parent seam are
explicit engineering substitutions; no old model receipt is forged or edited.
"""
from copy import deepcopy
import hashlib
import json

import pytest

from quanta_agents.meta_v3 import saved_ohlc_extension as adapter
from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.runtime import verify_case_sources
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3 import research_batch


def prepared_fixture(tmp_path, monkeypatch, requested=None):
    original = json.loads((ROOT / 'experiment_traces/meta_framework_v3/year_inputs_001/case.json').read_text(encoding='utf-8'))
    days = original['decision_fixture']['calendar']
    selected, fields, eligibility = [], [], []
    for index, day in enumerate(days):
        close = 10 + index / 100
        selected.append({'date': day, 'code': 'sh600004', 'raw_close': close,
            'raw_open': close + 0.1, 'raw_high': close + 0.2, 'raw_low': close - 0.1,
            'volume': 1000, 'amount': close * 1000})
    folder = tmp_path / 'year_inputs_001'
    folder.mkdir()
    source = folder / 'selected_rows.json'
    source.write_text(json.dumps(selected), encoding='utf-8')
    pin = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(adapter, 'SELECTED_ROWS_SHA256', pin)
    for row in selected:
        base = {'session': row['date'], 'symbol': row['code'], 'source_evidence_id': pin,
            'effective_at': row['date'] + 'T15:05:00+08:00', 'available_at': row['date'] + 'T15:05:00+08:00'}
        eligibility.append({**base, 'eligible': True})
        for name, key in [('close', 'raw_close'), ('volume', 'volume'), ('amount', 'amount')]:
            fields.append({**base, 'field': name, 'value': row[key]})
    case = {'description': 'GENERATED ENGINEERING FIXTURE; only calendar metadata is shared with the old scope.',
        'research_class': 'real_saved_development', 'execution_backend': 'v3_streamed_001', 'initial_cash': '1000000',
        'research_policy': {'version': 'structural_research_v1', 'action_limits': {'develop_strategy': 3}},
        'decision_fixture': {'kind': 'exposed_real_decision_table', 'codes': ['sh600004'], 'calendar': days,
            'fields': deepcopy(adapter.ORIGINAL_FIELDS), 'field_rows': fields, 'eligibility_rows': eligibility},
        'raw_source_bindings': {'source_artifacts': [], 'obligations': []},
        'evidence_sources': [{'path': str(source), 'sha256': pin}]}
    request = {'kind': 'research_extension_request_v1', 'current_case_hash': digest(case),
        'request': {'request_kind': 'data', 'requested_fields': ['open', 'high', 'low'] if requested is None else requested}}
    task = {'case': case, 'case_hash': digest(case)}
    # No gateway or original ledger is involved. This seam is the explicit test fixture.
    monkeypatch.setattr(adapter, '_parent', lambda *_: ({'provenance': {'fixture_only': True}}, task, request, [], []))
    return case, task, request, source, selected


@pytest.mark.parametrize('requested', [['open'], ['low', 'open', 'high']])
def test_additive_selected_values_and_nominal_times_preserve_parent(tmp_path, monkeypatch, requested):
    parent, _, _, source, selected = prepared_fixture(tmp_path, monkeypatch, requested)
    before, source_before = deepcopy(parent), source.read_bytes()
    result = adapter.prepare(tmp_path / 'unused_fixture_parent', 'test', 'fixture_request', tmp_path / 'output')
    child = result['child_case']
    assert parent == before and source.read_bytes() == source_before
    added = child['decision_fixture']['field_rows'][len(parent['decision_fixture']['field_rows']):]
    assert len(added) == 244 * len(requested)
    expected = {(row['date'], name): row[adapter.MAPPING[name]] for row in selected for name in requested}
    assert all(row['value'] == expected[(row['session'], row['field'])] for row in added)
    assert all(row['effective_at'] == row['available_at'] == row['session'] + 'T15:05:00+08:00' for row in added)
    restored = deepcopy(child)
    restored['decision_fixture']['fields'] = restored['decision_fixture']['fields'][:3]
    restored['decision_fixture']['field_rows'] = restored['decision_fixture']['field_rows'][:len(before['decision_fixture']['field_rows'])]
    restored['evidence_sources'].pop()
    assert restored == before
    manifest = json.loads((tmp_path / 'output/derivation_manifest.json').read_text(encoding='utf-8'))
    assert manifest['every_value_matches'] is True
    assert len(manifest['value_checks']) == len(added)
    assert manifest['child_decision_table_hash'] == digest(child['decision_fixture'])
    assert manifest['model_calls'] == manifest['strategy_executions'] == manifest['downloads'] == 0
    assert manifest['broader_raw_archives_read'] is False
    assert result['source_admissions_complete'] is False and len(result['source_admissions']) == 1
    verify_case_sources({'case': child, 'case_hash': digest(child)})
    with pytest.raises(ValueError, match='output already exists'):
        adapter.prepare(tmp_path, 'test', 'fixture_request', tmp_path / 'output')


@pytest.mark.parametrize('mutation, message', [
    ('wrong_kind', 'nonempty distinct subset'), ('unrequested_field', 'nonempty distinct subset'),
    ('empty_fields', 'nonempty distinct subset'), ('wrong_axes', 'original year_inputs_001'),
    ('wrong_contract', 'original close/volume/amount'), ('source_drift', 'selected source hash drift'),
    ('old_value_changed', 'original decision values'), ('missing_price', 'absent or invalid'),
])
def test_refuses_changed_scope_or_source_without_writing_output(tmp_path, monkeypatch, mutation, message):
    case, task, request, source, selected = prepared_fixture(tmp_path, monkeypatch)
    if mutation == 'wrong_kind': request['request']['request_kind'] = 'universe'
    if mutation == 'unrequested_field': request['request']['requested_fields'] = ['future_close']
    if mutation == 'empty_fields': request['request']['requested_fields'] = []
    if mutation == 'wrong_axes': case['decision_fixture']['calendar'] = case['decision_fixture']['calendar'][:-1]
    if mutation == 'wrong_contract': case['decision_fixture']['fields'][0]['unit'] = 'adjusted price'
    if mutation == 'old_value_changed': case['decision_fixture']['field_rows'][0]['value'] += 1
    if mutation == 'source_drift': source.write_text('[]', encoding='utf-8')
    if mutation == 'missing_price':
        selected[0]['raw_high'] = None
        source.write_text(json.dumps(selected), encoding='utf-8')
        pin = hashlib.sha256(source.read_bytes()).hexdigest()
        monkeypatch.setattr(adapter, 'SELECTED_ROWS_SHA256', pin)
        case['evidence_sources'][0]['sha256'] = pin
    task['case_hash'] = digest(case)
    with pytest.raises(ValueError, match=message):
        adapter.prepare(tmp_path / 'unused_fixture_parent', 'test', 'fixture_request', tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_does_not_read_any_unselected_source(tmp_path, monkeypatch):
    case, task, _, _, _ = prepared_fixture(tmp_path, monkeypatch)
    case['evidence_sources'].append({'path': str(tmp_path / 'never_open_full_history.json'), 'sha256': '0' * 64})
    task['case_hash'] = digest(case)
    result = adapter.prepare(tmp_path / 'unused_fixture_parent', 'test', 'fixture_request', tmp_path / 'output')
    assert result['child_case']['evidence_sources'][-2] == case['evidence_sources'][-1]


def test_batch_case_adds_only_requested_semantics_and_can_register_new_field_batch(tmp_path, monkeypatch):
    parent, task, request, source, _ = prepared_fixture(tmp_path, monkeypatch, ['low', 'open'])
    parent['research_policy']['action_limits'].update(register_batch=1, execute_batch=1, inspect_batch=2)
    semantics = {f['name']: {'unit': f['unit'], 'raw_precision': 'original generated value contract',
                            'digit_derivation': None} for f in parent['decision_fixture']['fields']}
    # An existing non-null derivation must survive exactly; OHLC receives none.
    semantics['volume']['digit_derivation'] = {
        'source_unit': 'shares', 'minimum_increment': '1', 'integer_conversion': 'exact_decimal_no_rounding',
        'source_evidence_sha256': parent['evidence_sources'][0]['sha256'], 'base': 10, 'place': 0, 'width': 1}
    parent['batch_policy'] = {'version': 'bounded_batch_v1', 'max_candidates_total': 4,
        'max_scan_cells_total': 100000, 'max_wall_seconds': 60,
        'output_stop_threshold_bytes': 10485760, 'field_semantics': semantics}
    task['case_hash'] = request['current_case_hash'] = digest(parent)
    before, source_before = deepcopy(parent), source.read_bytes()
    monkeypatch.setattr(research_batch.subprocess, 'Popen',
                        lambda *a, **k: pytest.fail('unexpected strategy execution'))
    prepared = adapter.prepare(tmp_path / 'unused_fixture_parent', 'test', 'fixture_request', tmp_path / 'output')
    child = prepared['child_case']
    assert parent == before and source.read_bytes() == source_before
    assert child['research_policy'] == before['research_policy']
    for key, value in before['batch_policy'].items():
        if key != 'field_semantics':
            assert child['batch_policy'][key] == value
    assert {name: child['batch_policy']['field_semantics'][name] for name in semantics} == semantics
    additions = {name: {'unit': 'CNY raw ' + name, 'raw_precision': 'unknown', 'digit_derivation': None}
                 for name in ('low', 'open')}
    assert child['batch_policy']['field_semantics'] == {**semantics, **additions}
    manifest = json.loads((tmp_path / 'output/derivation_manifest.json').read_text(encoding='utf-8'))
    update = manifest['batch_field_semantics_update']
    assert update['added_field_semantics'] == additions
    assert update['parent_batch_policy_hash'] == digest(before['batch_policy'])
    assert update['child_batch_policy_hash'] == digest(child['batch_policy'])
    assert update['preserved_original_semantics_hash'] == digest(semantics)
    assert update['budget_fields_unchanged'] is True
    tools = ResearchTools(tmp_path / 'child_stage', 'test', child, [])
    assert research_batch.policy(child) == child['batch_policy']
    from test_meta_v3_batch_research import declaration
    batch = declaration((0.1, 0.2))
    batch['families'][0]['program_template']['target_weight_expression'] = '(close > open) * {{weight}}'
    result = tools.execute('register_ohlc', 'register_batch', batch)
    assert result['public']['reserved_candidates'] == 2
    assert result['public']['validation_failures'] == 0
    assert not list(tools.batch_folder.rglob('intent.json'))
