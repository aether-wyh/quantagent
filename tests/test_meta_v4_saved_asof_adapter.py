"""Fixed adapter/retention checks using three generated temporary JSON inputs."""
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from quanta_agents.meta_v3 import asof_return_views


def generated_report():
    # Calendar metadata only; all prices, hashes and actions below are generated.
    holidays = {'2019-04-05', '2019-05-01', '2019-05-02', '2019-05-03', '2019-06-07', '2019-09-13'}
    holidays |= {'2019-02-' + str(d).zfill(2) for d in range(4, 9)}
    holidays |= {'2019-10-' + str(d).zfill(2) for d in (1, 2, 3, 4, 7)}
    cursor, days = date(2019, 1, 2), []
    while cursor <= date(2019, 12, 31):
        if cursor.weekday() < 5 and cursor.isoformat() not in holidays:
            days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    assert len(days) == 244 and days[60] == '2019-04-03'
    price = lambda d: {'session': d, 'symbol': 'sh600004', 'close': '10.00', 'reference_previous_close': '10.00',
        'source_id': hashlib.sha256(('generated-price-' + d).encode()).hexdigest()}
    action = {'action_id': 'sh600004-generated-action', 'symbol': 'sh600004', 'kind': 'cash',
        'announcement_date': '2019-08-03', 'record_date': '2019-08-08', 'ex_date': '2019-08-09',
        'payment_date': '2019-08-09', 'listing_date': None, 'available_at': '2019-08-05T00:00:00+08:00',
        'availability_basis': 'declared_simulated', 'share_increment_per_original_share': '0',
        'gross_cash_per_original_share': '0.10', 'basis': 'per_original_pre_ex_share', 'status': 'implementation',
        'source_id': 'a' * 64}
    return {'normalized_inputs': {'calendar': days, 'symbols': ['sh600004'],
        'prices': [price(d) for d in days], 'previous_anchors': [price('2018-12-28')], 'actions': [action],
        'coverage': [{'session': d, 'symbol': 'sh600004', 'status': 'unknown', 'source_id': 'c' * 64} for d in days],
        'as_of': '2026-09-08T12:00:00+00:00'},
        'original_archive_manifest': {'availability_contract': {'actual_available_at': None,
            'actual_arrival_evidence': 'not_provided', 'simulated_economic_use_policy': {'evidence_type': 'simulation_not_observed_arrival'}}},
        'historical_arrival_verified': False, 'raw_price_origin_authenticated': False,
        'complete_announcement_inventory_verified': False, 'strategy_executed': False, 'account_executed': False}


@pytest.fixture
def driver(tmp_path, monkeypatch):
    file = Path(__file__).resolve().parents[1] / 'scripts/run_v4_saved_asof_return_diagnostic.py'
    spec = importlib.util.spec_from_file_location('saved_asof_driver_test', file)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    monkeypatch.setattr(value, 'ROOT', tmp_path)
    monkeypatch.setattr(value, 'PRIOR_DIRECTORY', tmp_path / 'validation/prior_generated')
    monkeypatch.setattr(value, 'code_pins', lambda: {'generated_test_code': 'b' * 64})
    return value


def write_generated_inputs(driver, monkeypatch, report=None):
    report = generated_report() if report is None else report
    report['scope'] = {'subject': driver.ORIGINAL_SUBJECT}
    intent = {'scope': report['scope'], 'as_of': '2026-09-08T12:00:00+00:00'}
    folder = driver.PRIOR_DIRECTORY; folder.mkdir(parents=True, exist_ok=True)
    for name, value in (('intent.json', intent), ('report.json', report)):
        (folder / name).write_text(driver.serial(value) + '\n', encoding='utf-8')
    receipt = {'subject': driver.ORIGINAL_SUBJECT, 'formal_target_success': False, 'strategy_executed': False,
        'report_sha256': driver.digest(report), 'report_file_sha256': hashlib.sha256((folder / 'report.json').read_bytes()).hexdigest()}
    (folder / 'receipt.json').write_text(driver.serial(receipt) + '\n', encoding='utf-8')
    monkeypatch.setattr(driver, 'PINNED_INPUTS', {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
        for name in ('intent.json', 'report.json', 'receipt.json')})
    return report


def fake_core(driver):
    def build(**bundle):
        views = []
        for signal in bundle['signal_dates']:
            index = bundle['calendar'].index(signal)
            window = bundle['calendar'][max(1, index-59):index+1]
            views.append({'signal_date': signal, 'status': 'insufficient_history' if index < 60 else 'complete_window',
                'available_return_sessions': len(window),
                'rows': [{'session': day, 'symbol': symbol, 'diagnostic_return': None,
                    'qualified_return': None, 'generated_qualified_return': None, 'blockers': ['generated_stub_only']}
                    for day in window for symbol in bundle['symbols']]})
        return {'submitted_input_sha256': driver.digest({'version': asof_return_views.VERSION, **bundle}), 'views': views}
    return build


def test_preparation_preserves_all_original_49_opportunities_and_unknown_times(driver):
    report = generated_report(); before = driver.digest(report)
    bundle = driver.prepare_inputs(report)
    assert len(bundle['calendar']) == len(bundle['price_versions']) == len(bundle['coverage_versions']) == 245
    assert bundle['calendar'][0] == '2018-12-28' and len(bundle['signal_dates']) == 49
    assert bundle['signal_dates'] == report['normalized_inputs']['calendar'][::5]
    history = [min(bundle['calendar'].index(d), 60) for d in bundle['signal_dates']]
    assert history[:12] == list(range(1, 57, 5)) and history[12:] == [60] * 37
    assert bundle['evidence_receipts'] == [] and bundle['evidence_class'] == 'caller_bound_exposed_development'
    for rows in (bundle['price_versions'], bundle['action_versions'], bundle['coverage_versions']):
        assert all(r['effective_at'] is None and r['observed_arrival_at'] is None and r['evidence_id'] is None for r in rows)
    assert driver.mapping_notes(report)['saved_action_time_declarations'][0]['declared_available_at'] == '2019-08-05T00:00:00+08:00'
    assert driver.digest(report) == before


def test_pinned_generated_input_loading_and_manifest_cutoff(driver, monkeypatch):
    report = write_generated_inputs(driver, monkeypatch)
    assert driver.read_saved_inputs()['report.json'] == report
    report['normalized_inputs']['as_of'] = '2026-09-09T12:00:00+00:00'
    write_generated_inputs(driver, monkeypatch, report)
    with pytest.raises(ValueError, match='cutoff changed'):
        driver.read_saved_inputs()


def test_changed_prior_bytes_are_rejected(driver, monkeypatch):
    write_generated_inputs(driver, monkeypatch)
    with (driver.PRIOR_DIRECTORY / 'report.json').open('a', encoding='utf-8') as stream:
        stream.write(' ')
    with pytest.raises(ValueError, match='artifact drift'):
        driver.read_saved_inputs()


def test_generated_cli_retains_hashes_fsyncs_intent_and_refuses_same_directory(driver, monkeypatch):
    write_generated_inputs(driver, monkeypatch)
    monkeypatch.setattr(asof_return_views, 'build', fake_core(driver))
    synced = []
    monkeypatch.setattr(driver.os, 'fsync', lambda fd: synced.append(driver.os.fstat(fd).st_size))
    output = driver.ROOT / 'validation/new_generated'
    monkeypatch.setattr(sys, 'argv', ['driver', '--output', str(output)])
    driver.main()
    intent, report, receipt = [json.loads((output / name).read_text(encoding='utf-8'))
        for name in ('intent.json', 'report.json', 'receipt.json')]
    assert receipt['state'] == 'COMPLETE' and len(synced) == 3 and all(size > 0 for size in synced)
    assert intent['input_manifest_sha256'] == driver.digest(intent['inputs'])
    assert receipt['input_manifest_sha256'] == report['input_manifest_sha256'] == intent['input_manifest_sha256']
    assert receipt['intent_sha256'] == driver.digest(intent)
    assert receipt['report_sha256'] == driver.digest(report)
    assert receipt['input_sha256'] == report['input_sha256'] == driver.digest(report['normalized_inputs'])
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError, match='already exists'):
        driver.run(output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_generated_saved_inputs_reach_real_new_core_without_acquiring_qualification(driver, monkeypatch):
    write_generated_inputs(driver, monkeypatch)
    output = driver.ROOT / 'validation/generated_real_core'
    receipt = driver.run(output)
    assert receipt['state'] == 'COMPLETE', receipt.get('error')
    report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    views = report['asof_views']['views']
    assert len(views) == 49
    assert [v['available_return_sessions'] for v in views[:12]] == list(range(1, 57, 5))
    assert all(v['available_return_sessions'] == 60 for v in views[12:])
    assert all(row['qualified_return'] is None and row['generated_qualified_return'] is None
               for view in views for row in view['rows'])
    assert receipt['new_research_attempts'] == 0 and receipt['formal_target_success'] is False


def test_code_drift_is_refused_after_durable_intent_before_saved_input_reads(driver, monkeypatch):
    calls = iter(({'code': 'a' * 64}, {'code': 'b' * 64}))
    monkeypatch.setattr(driver, 'code_pins', lambda: next(calls))
    monkeypatch.setattr(driver, 'read_saved_inputs', lambda: pytest.fail('source opened after code drift'))
    output = driver.ROOT / 'validation/drift'
    receipt = driver.run(output)
    assert receipt['state'] == 'INCOMPLETE_TERMINAL' and (output / 'intent.json').exists()
    assert not (output / 'report.json').exists()
    assert 'before saved input reads' in receipt['error']['message']


@pytest.mark.parametrize('mutation', ['input_digest', 'dropped_signal', 'dropped_row', 'warmup_relabel', 'qualified'])
def test_bad_core_output_is_retained_as_failure_without_retries(driver, monkeypatch, mutation):
    write_generated_inputs(driver, monkeypatch); ordinary = fake_core(driver)
    def bad(**bundle):
        result = ordinary(**bundle)
        if mutation == 'input_digest': result['submitted_input_sha256'] = '0' * 64
        if mutation == 'dropped_signal': result['views'].pop(0)
        if mutation == 'dropped_row': result['views'][12]['rows'].pop()
        if mutation == 'warmup_relabel': result['views'][0]['status'] = 'complete_window'
        if mutation == 'qualified': result['views'][12]['rows'][0]['qualified_return'] = '0.1'
        return result
    monkeypatch.setattr(asof_return_views, 'build', bad)
    output = driver.ROOT / 'validation' / mutation
    receipt = driver.run(output)
    assert receipt['state'] == 'INCOMPLETE_TERMINAL' and not (output / 'report.json').exists()
    assert json.loads((output / 'receipt.json').read_text(encoding='utf-8')) == receipt


def test_postprocessing_cannot_leave_validation_or_overwrite_input_directory(driver):
    with pytest.raises(ValueError, match='child of workspace validation'):
        driver.run(driver.ROOT / 'elsewhere')
    assert not (driver.ROOT / 'elsewhere').exists()


def test_actual_fixed_input_paths_are_never_used_by_generated_fixture(driver, monkeypatch):
    write_generated_inputs(driver, monkeypatch)
    assert driver.PRIOR_DIRECTORY.is_relative_to(driver.ROOT)
    assert 'prior_generated' in str(driver.PRIOR_DIRECTORY)
    assert all(p.parent == driver.PRIOR_DIRECTORY for p in driver.PRIOR_DIRECTORY.iterdir())


def test_source_pin_inventory_covers_package_canaries_and_existing_execution_sources(tmp_path, monkeypatch):
    file = Path(__file__).resolve().parents[1] / 'scripts/run_v4_saved_asof_return_diagnostic.py'
    spec = importlib.util.spec_from_file_location('saved_asof_driver_pin_test', file)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    from quanta_agents.meta_v3 import runtime
    existing = {'existing_execution_source': 'c' * 64}
    monkeypatch.setattr(runtime, 'source_pins', lambda: existing)
    script = tmp_path / 'scripts/run_v4_saved_asof_return_diagnostic.py'
    script.parent.mkdir(parents=True)
    script.write_bytes(file.read_bytes())
    monkeypatch.setattr(value, 'ROOT', tmp_path)
    monkeypatch.setattr(value, '__file__', str(script))
    package = tmp_path / 'src/quanta_agents'
    canaries = [package / '__init__.py', package / 'workflow.py', package / 'nested/lazy.py']
    for path in canaries:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# generated code pin canary\n', encoding='utf-8')
    (package / 'unrelated.txt').write_text('not Python source', encoding='utf-8')
    pins = value.code_pins()
    expected = {**existing, **{path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [script, *canaries]}}
    assert pins == expected and existing == {'existing_execution_source': 'c' * 64}
    for path in canaries[:2]:
        before = value.code_pins()
        path.write_text('# changed generated code pin canary\n', encoding='utf-8')
        after = value.code_pins()
        key = path.relative_to(tmp_path).as_posix()
        assert before[key] != after[key]
        assert {k for k in before if before[k] != after[k]} == {key}
