"""Generated as-of inputs through the existing risk and public entry contracts.

No real observations, account backend, retained validation or research book is
read or executed. Only the temporary canary is read in the positive source test.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
from pathlib import Path

import pytest

from quanta_agents.meta_v3 import asof_return_views as views
from quanta_agents.meta_v3 import conditional_risk_derivation as derivation
from quanta_agents.meta_v3 import real_execution, real_program, saved_execution, target_schedule
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.research_tools import ResearchTools, save_once
from quanta_agents.meta_v3.runtime import verify_case_sources
from quanta_agents.meta_v3.source_admission import preflight_case
from test_meta_v4_conditional_risk_derivation import example, stamped


def bind(sources, category, version):
    sealed, receipt = views.bind_generated(version)
    sources[category].append(sealed)
    sources['evidence_receipts'].append(receipt)
    return sealed


def rebound(sources, category, version):
    """Replace a generated version and its old receipt, preserving inventory size."""
    index = sources[category].index(version)
    old = version['evidence_id']
    sealed, receipt = views.bind_generated(version)
    sources[category][index] = sealed
    sources['evidence_receipts'] = [r for r in sources['evidence_receipts'] if r['receipt_id'] != old]
    sources['evidence_receipts'].append(receipt)
    return sealed


def generated_inputs():
    case, bundle = example()
    case.update(description='Generated as-of risk entry only',
        raw_source_bindings={'source_artifacts': [], 'obligations': [], 'corporate_actions': []})
    sources = {key: [] for key in derivation.ASOF_SOURCE_FIELDS}
    old_market = {row['session']: row['value'] for row in bundle['market_rows']}
    old_stock = {(row['session'], row['symbol']): row['value'] for row in bundle['stock_rows']}
    with localcontext() as context:
        context.prec = 40
        previous = {code: Decimal('100') for code in [*bundle['symbols'], views.INDEX]}
        for index, day in enumerate(bundle['original_calendar']):
            for code in [*bundle['symbols'], views.INDEX]:
                prior = previous[code]
                value = None if index == 0 else (old_market[day] if code == views.INDEX else old_stock[(day, code)])
                close = prior if value is None else (prior * (1 + Decimal(str(value)))).quantize(Decimal('.000000000001'))
                common = {'symbol': code, 'effective_at': day + 'T15:00:00+08:00',
                    'observed_arrival_at': day + 'T15:05:00+08:00', 'arrival_basis': 'generated', 'evidence_id': None}
                bind(sources, 'price_versions', {**common, 'version_id': f'price/{code}/{day}/v1',
                    'source_id': digest({'generated_price': [day, code, str(close)]}),
                    'session': day, 'close': str(close), 'reference_previous_close': str(prior) if index else None})
                if index:
                    bind(sources, 'coverage_versions', {**common, 'version_id': f'coverage/{code}/{day}/v1',
                        'source_id': digest({'generated_coverage': [day, code]}), 'session': day,
                        'status': 'not_applicable_price_index' if code == views.INDEX else 'generated_complete',
                        'action_ids': []})
                previous[code] = close
    bundle.update(version=derivation.ASOF_VERSION, asof_sources=sources)
    for row in bundle['market_rows']:
        row.update(value=None, source_status='unknown'); stamped(row)
    for row in bundle['stock_rows']:
        row.update(value=None, source_status='unknown', return_basis='unknown', action_coverage_status='unknown'); stamped(row)
    return case, bundle


@pytest.fixture(scope='module')
def generated_base():
    return generated_inputs()


@pytest.fixture(scope='module')
def generated_built(generated_base):
    case, bundle = generated_base
    return {**case, **derivation.build(case, bundle)}


def first_row(view, symbol=None, day=None):
    symbol = symbol or 'sh600000'
    return next(row for row in view['rows'] if row['symbol'] == symbol and (day is None or row['session'] == day))


def rehash_saved(case):
    """Rebind altered envelopes; only numerical recomputation can detect the lie."""
    record = case[derivation.KEY]
    for receipt in record['anchor_receipts']:
        view = receipt['asof_view']
        view['view_sha256'] = digest({key: value for key, value in view.items() if key != 'view_sha256'})
        receipt['asof_view_sha256'] = view['view_sha256']
        receipt['measurement_sha256'] = digest(receipt['measurement'])
        identity = digest(receipt)
        for row in case['decision_fixture']['field_rows']:
            if row['field'] == derivation.FIELD and row['session'] == receipt['signal_date']:
                row['source_evidence_id'] = identity
        next(row for row in case[target_schedule.KEY]['anchor_inputs']
            if row['signal_date'] == receipt['signal_date'])['input_receipt_sha256'] = identity
    record['bundle_sha256'] = digest(record['bundle'])
    record['anchor_receipts_sha256'] = digest(record['anchor_receipts'])
    record['output_fixture_sha256'] = digest(case['decision_fixture'])
    record['schedule_policy_sha256'] = digest(case[target_schedule.KEY])


def program():
    return {'version': 'factor_strategy_program_v1', 'factors': [],
        'target_weight_expression': derivation.FIELD, 'hypothesis': 'Generated as-of entry verification',
        'applicability': ['Engineering only'], 'invalidation_conditions': ['Any claim of real evidence']}


def test_v1_output_is_byte_identical_and_does_not_select_versions(monkeypatch):
    monkeypatch.setattr(views, 'build', lambda **kw: pytest.fail('v1 selected as-of versions'))
    case, bundle = example()
    assert digest(derivation.build(case, bundle)) == 'ad09a4154cc3be8a9fd52b9a41902da140ddf54939c57878fb89f40fa76b9084'
    assert derivation.verify_case({**case, **derivation.build(case, bundle)})['version'] == derivation.VERSION


def test_generated_views_reach_original_sixty_return_risk_and_schedule(generated_built):
    case = generated_built; record = case[derivation.KEY]
    assert record['version'] == derivation.ASOF_VERSION
    calendar = record['bundle']['original_calendar']; days = case['decision_fixture']['calendar']
    assert [r['signal_date'] for r in record['anchor_receipts']] == days[::5]
    for receipt in record['anchor_receipts']:
        index = calendar.index(receipt['signal_date']); view = receipt['asof_view']
        assert receipt['window_sessions'] == view['window_sessions'] == calendar[index-59:index+1]
        assert receipt['first_previous_session'] == view['first_previous_session'] == calendar[index-60]
        assert len(view['rows']) == 60 * 13
        assert all(row['generated_qualified_return'] is not None and row['qualified_return'] is None for row in view['rows'])
        assert receipt['asof_view_sha256'] == view['view_sha256']
        assert receipt['measurement']['status'] == 'ready'
        assert sum(Decimal(w) for w in receipt['measurement']['target_weights'].values()) == Decimal('.8')
    compiled = real_program.validate_program(program(), public_field_contract=case['decision_fixture']['fields'])
    ordinary = real_program.build_targets(compiled, decision_fixture=case['decision_fixture'], frozen_policy=real_program.POLICY)
    targets = target_schedule.apply_schedule(ordinary, case=case)
    assert {row['signal_date'] for row in targets['targets']} == {days[0], days[5], days[10], days[-2]}
    assert all(row['target_weight'] == '0' for row in targets['targets'] if row['signal_date'] == days[-2])
    assert days[-1] == record['anchor_receipts'][-1]['signal_date']
    assert days[-1] not in {row['signal_date'] for row in targets['targets']}


def test_metadata_binds_views_without_numerical_recomputation(generated_built, monkeypatch):
    monkeypatch.setattr(views, 'build', lambda **kw: pytest.fail('metadata selected versions or recomputed returns'))
    monkeypatch.setattr(derivation, 'evaluate_window', lambda *a, **kw: pytest.fail('metadata evaluated a risk window'))
    report = derivation.validate_case_metadata(generated_built)
    assert report['version'] == derivation.ASOF_VERSION and report['metadata_binding_verified'] is True
    assert report['numerical_recomputation_verified'] is False and report['source_authenticated'] is False


def test_later_price_version_changes_later_window_not_earlier_receipt(generated_base, generated_built):
    case, bundle = deepcopy(generated_base)
    sources = bundle['asof_sources']; days = case['decision_fixture']['calendar']
    original_day = bundle['original_calendar'][20]; code = bundle['symbols'][0]
    row = deepcopy(next(r for r in sources['price_versions'] if r['session'] == original_day and r['symbol'] == code))
    row.update(version_id=row['version_id'].replace('/v1', '/v2'),
        close=str((Decimal(row['close']) * Decimal('1.001')).quantize(Decimal('.000000000001'))),
        effective_at=days[5] + 'T15:00:00+08:00', observed_arrival_at=days[5] + 'T15:05:00+08:00')
    changed_version = bind(sources, 'price_versions', row)
    changed = derivation.build(case, bundle)
    result = changed[derivation.KEY]
    baseline = generated_built[derivation.KEY]
    assert result['bundle_sha256'] != baseline['bundle_sha256']
    assert result['anchor_receipts'][0] == baseline['anchor_receipts'][0]
    def earlier_fields(value):
        return [r for r in value['decision_fixture']['field_rows']
                if r['field'] == derivation.FIELD and r['session'] < days[5]]
    assert len(earlier_fields(changed)) == 5 * 12
    assert earlier_fields(changed) == earlier_fields(generated_built)
    later = result['anchor_receipts'][1]['asof_view']
    selected = first_row(later, code, original_day)
    assert selected['selected_versions']['current_price']['version_id'] == changed_version['version_id']
    assert selected['maximum_available_at'] == days[5] + 'T15:05:00+08:00'
    assert selected['generated_qualified_return'] != first_row(baseline['anchor_receipts'][1]['asof_view'], code, original_day)['generated_qualified_return']
    assert result['anchor_receipts'][1]['measurement']['status'] == 'ready'


def test_late_action_and_coverage_reach_later_risk_with_actual_previous_close(generated_base, generated_built, monkeypatch):
    case, bundle = deepcopy(generated_base); sources = bundle['asof_sources']
    calendar = bundle['original_calendar']; days = case['decision_fixture']['calendar']
    day, code = calendar[20], bundle['symbols'][0]
    action_id = 'generated-cash-action'
    common = {'symbol': code, 'effective_at': days[5] + 'T15:00:00+08:00',
        'observed_arrival_at': days[5] + 'T15:05:00+08:00', 'arrival_basis': 'generated', 'evidence_id': None}
    bind(sources, 'action_versions', {**common, 'version_id': 'action/cash/v1', 'action_id': action_id,
        'source_id': digest({'generated_action': action_id}), 'kind': 'cash', 'status': 'implementation',
        'announcement_date': calendar[18], 'record_date': calendar[19], 'ex_date': day,
        'payment_date': day, 'listing_date': None, 'basis': 'per_original_pre_ex_share',
        'share_increment_per_original_share': '0', 'gross_cash_per_original_share': '0.17'})
    coverage = deepcopy(next(r for r in sources['coverage_versions'] if r['session'] == day and r['symbol'] == code))
    coverage.update(common, version_id=coverage['version_id'].replace('/v1', '/v2'), action_ids=[action_id])
    bind(sources, 'coverage_versions', coverage)
    price = deepcopy(next(r for r in sources['price_versions'] if r['session'] == day and r['symbol'] == code))
    actual_prior = Decimal(price['reference_previous_close'])
    price.update(common, version_id=price['version_id'].replace('/v1', '/v2'),
        reference_previous_close=str(actual_prior - Decimal('.17')))
    bind(sources, 'price_versions', price)
    observed = []; original_evaluate = derivation.evaluate_window
    def evaluate(market, returns, **kwargs):
        observed.append({'market': deepcopy(market), 'returns': deepcopy(returns)})
        return original_evaluate(market, returns, **kwargs)
    monkeypatch.setattr(derivation, 'evaluate_window', evaluate)
    result = derivation.build(case, bundle)
    receipts = result[derivation.KEY]['anchor_receipts']
    assert receipts[0] == generated_built[derivation.KEY]['anchor_receipts'][0]
    assert [r for r in result['decision_fixture']['field_rows'] if r['session'] < days[5]] == [
        r for r in generated_built['decision_fixture']['field_rows'] if r['session'] < days[5]]
    row = first_row(receipts[1]['asof_view'], code, day)
    expected = (Decimal(price['close']) + Decimal('.17')) / actual_prior - 1
    counterfactual = (Decimal(price['close']) + Decimal('.17')) / (actual_prior - Decimal('.17')) - 1
    assert float(row['generated_qualified_return']) == pytest.approx(float(expected), abs=1e-12)
    assert abs(float(row['generated_qualified_return']) - float(counterfactual)) > .0001
    assert row['formula_inputs']['gross_cash_per_original_pre_ex_share'] == '0.17'
    assert len(row['selected_versions']['actions']) == 1 and row['qualified_return'] is None
    offset = receipts[1]['window_sessions'].index(day)
    assert observed[1]['returns'][code][offset] == pytest.approx(float(expected), abs=1e-12)
    assert receipts[1]['measurement']['status'] == 'ready'


@pytest.mark.parametrize('kind', ['missing_stock_receipt', 'missing_index_receipt', 'unknown_arrival', 'coverage_unknown'])
def test_unqualified_diagnostic_never_becomes_fallback_risk_input(generated_base, kind):
    case, bundle = deepcopy(generated_base); sources = bundle['asof_sources']
    day = bundle['original_calendar'][20]
    code = views.INDEX if kind == 'missing_index_receipt' else bundle['symbols'][0]
    category = 'coverage_versions' if kind == 'coverage_unknown' else 'price_versions'
    row = next(r for r in sources[category] if r['session'] == day and r['symbol'] == code)
    if kind.startswith('missing'):
        sources['evidence_receipts'] = [r for r in sources['evidence_receipts'] if r['receipt_id'] != row['evidence_id']]
    else:
        row.update(observed_arrival_at=None) if kind == 'unknown_arrival' else row.update(status='unknown')
        rebound(sources, category, row)
    output = derivation.build(case, bundle); record = output[derivation.KEY]
    assert len(record['anchor_receipts']) == 4
    for receipt in record['anchor_receipts']:
        assert len(receipt['asof_view']['rows']) == 60 * 13
        selected = first_row(receipt['asof_view'], code, day)
        assert selected['diagnostic_return'] is not None
        assert selected['generated_qualified_return'] is None and selected['qualified_return'] is None
        assert selected['blockers'] and receipt['source_failures']
        assert receipt['measurement']['status'] == 'target_cash'
        assert all(value == '0' for value in receipt['measurement']['target_weights'].values())


@pytest.mark.parametrize('kind', ['historical_eligibility', 'current_case_eligibility'])
def test_original_qualification_stays_separate_and_later_anchor_recovers(generated_base, kind):
    case, bundle = deepcopy(generated_base); first = case['decision_fixture']['calendar'][0]
    if kind == 'historical_eligibility':
        row = next(r for r in bundle['stock_rows'] if r['session'] == bundle['original_calendar'][20])
        row['eligibility']['available_at'] = first + 'T15:11:00+08:00'; stamped(row['eligibility']); stamped(row)
    else:
        case['decision_fixture']['eligibility_rows'][0]['available_at'] = first + 'T15:11:00+08:00'
    result = derivation.build(case, bundle)[derivation.KEY]
    assert all(row['generated_qualified_return'] is not None for row in result['anchor_receipts'][0]['asof_view']['rows'])
    assert result['anchor_receipts'][0]['measurement']['status'] == 'target_cash'
    assert result['anchor_receipts'][1]['measurement']['status'] == 'ready'


@pytest.mark.parametrize('kind', ['market_value', 'stock_value', 'market_status', 'stock_status', 'stock_basis', 'stock_coverage'])
def test_v2_placeholder_grid_cannot_supply_an_alternate_return(generated_base, monkeypatch, kind):
    case, bundle = deepcopy(generated_base)
    row = bundle['market_rows'][0] if kind.startswith('market') else bundle['stock_rows'][0]
    if kind.endswith('value'): row['value'] = .02
    if kind.endswith('status'): row['source_status'] = 'generated_known'
    if kind == 'stock_basis': row['return_basis'] = 'generated_causal_total_economic_return'
    if kind == 'stock_coverage': row['action_coverage_status'] = 'generated_complete'
    stamped(row)
    monkeypatch.setattr(views, 'build', lambda **kw: pytest.fail('fallback grid reached as-of computation'))
    with pytest.raises(ValueError, match='fallback'):
        derivation.build(case, bundle)


def corrupted(case, kind):
    record = case[derivation.KEY]
    if kind == 'view_hash': record['anchor_receipts'][0]['asof_view_sha256'] = '0' * 64
    if kind == 'rehash_false_view':
        first_row(record['anchor_receipts'][0]['asof_view'])['generated_qualified_return'] = '.123'
        rehash_saved(case)
    if kind == 'rebind_new_source':
        sources = record['bundle']['asof_sources']; row = sources['price_versions'][13]
        row['close'] = str(Decimal(row['close']) + 1); rebound(sources, 'price_versions', row)
        rehash_saved(case)
    if kind == 'field_weight':
        next(r for r in case['decision_fixture']['field_rows'] if r['field'] == derivation.FIELD)['value'] = .7
    if kind == 'source_claim': record['anchor_receipts'][0]['asof_view']['source_authenticated'] = True; rehash_saved(case)
    if kind == 'qualified_claim': first_row(record['anchor_receipts'][0]['asof_view'])['qualified_return'] = '.1'; rehash_saved(case)
    if kind == 'real_class': case['evidence_class'] = 'real_verified'
    if kind == 'sealed_bundle': record['bundle']['original_calendar'] = ['2024' + d[4:] for d in record['bundle']['original_calendar']]
    if kind == 'drop_record': case.pop(derivation.KEY)


@pytest.mark.parametrize('entry', ['runtime', 'research_tools', 'real_execution'])
@pytest.mark.parametrize('kind', ['view_hash', 'rehash_false_view', 'rebind_new_source', 'field_weight',
    'source_claim', 'qualified_claim', 'real_class', 'sealed_bundle', 'drop_record'])
def test_asof_entry_refuses_tamper_before_any_source_or_account(generated_built, tmp_path, monkeypatch, entry, kind):
    case = deepcopy(generated_built); corrupted(case, kind)
    if kind in ('rehash_false_view', 'rebind_new_source'):
        assert derivation.validate_case_metadata(case)['metadata_binding_verified'] is True
    case['evidence_sources'] = [{'path': str(tmp_path / 'never_opened'), 'sha256': '0' * 64}]
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('bad as-of entry opened source bytes'))
    monkeypatch.setattr(saved_execution, 'freeze_saved_research_plan', lambda **kw: pytest.fail('bad as-of entry reached account freeze'))
    monkeypatch.setattr(saved_execution.SavedRawResearch, 'create', lambda *a, **kw: pytest.fail('bad as-of entry dispatched an account'))
    candidate = tmp_path / 'candidate'; candidate.mkdir()
    with pytest.raises(ValueError):
        if entry == 'runtime': verify_case_sources({'case': case, 'case_hash': digest(case)})
        elif entry == 'research_tools': ResearchTools(tmp_path / 'stage', 'generated', case, [])
        else: real_execution.develop(candidate, case, program(), save_once)
    assert not (candidate / 'workbench/raw_children').exists()


def test_full_recomputation_precedes_the_only_temporary_source_read(generated_built, tmp_path, monkeypatch):
    case = deepcopy(generated_built); path = tmp_path / 'generated_canary.txt'
    payload = b'Generated source ordering check only.'; path.write_bytes(payload)
    case['evidence_sources'] = [{'path': str(path), 'sha256': hashlib.sha256(payload).hexdigest()}]
    original_build, original_read = views.build, Path.read_bytes; calls = []
    def build(**kwargs):
        assert kwargs['evidence_class'] == derivation.CLASS
        result = original_build(**kwargs); calls.append('asof_recomputed'); return result
    def read(p):
        assert p == path and calls == ['asof_recomputed']
        calls.append('canary_read'); return original_read(p)
    monkeypatch.setattr(views, 'build', build); monkeypatch.setattr(Path, 'read_bytes', read)
    verify_case_sources({'case': case, 'case_hash': digest(case)})
    assert calls == ['asof_recomputed', 'canary_read']


def test_public_contract_exposes_generated_v2_without_authentication(generated_built, tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('inline public contract opened source'))
    contract = ResearchTools(tmp_path / 'stage', 'generated', deepcopy(generated_built), []).contract()
    report = contract['conditional_risk_derivation']
    assert report['version'] == derivation.ASOF_VERSION and report['anchor_evaluations'] == 4
    assert report['binding_verified'] is True and report['numerical_recomputation_verified'] is True
    sources = generated_built[derivation.KEY]['bundle']['asof_sources']
    assert report['version_view_work_units'] == {
        **{key: len(value) for key, value in sources.items()}, 'signal_views': 4, 'output_rows': 4 * 60 * 13}
    assert 'not an admitted fair-study resource protocol' in report['version_view_resource_scope']
    assert 'GENERATED ENGINEERING ONLY' in report['scope'] and 'not an autonomous researcher selector' in report['scope']
    for key in ('source_authenticated', 'source_arrival_verified', 'action_coverage_verified', 'real_research', 'formal_target_success'):
        assert report[key] is False
    assert contract['target_schedule']['input_receipt_authentication'] is False


def test_v2_source_policy_cannot_be_stripped_with_the_reserved_field(generated_base, monkeypatch):
    case, _ = deepcopy(generated_base)
    case['source_policy'] = {'version': derivation.ASOF_VERSION}
    monkeypatch.setattr(views, 'build', lambda **kw: pytest.fail('stripped v2 declaration recomputed returns'))
    with pytest.raises(ValueError, match='cannot lose its derivation record'):
        preflight_case(case)
