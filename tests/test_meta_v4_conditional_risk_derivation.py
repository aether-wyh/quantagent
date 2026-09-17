"""Generated-only custody/timing tests; no market files or research jobs."""
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import pytest

from quanta_agents.meta_v3 import conditional_risk_derivation as derivation
from quanta_agents.meta_v3 import real_program, target_schedule
from quanta_agents.meta_v3.ledger import digest


def stamped(row):
    row['source_evidence_id'] = derivation.generated_row_id(row)
    return row


def example():
    days = []
    cursor = date(2018, 1, 2)
    while len(days) < 77:
        if cursor.weekday() < 5:
            days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    codes = ['sh' + str(600000 + i) for i in range(12)]
    signals = days[-16:]
    fields, eligibility_rows = [], []
    for day in signals:
        for code in codes:
            common = {'session': day, 'symbol': code, 'effective_at': day + 'T15:00:00+08:00',
                'available_at': day + 'T15:00:00+08:00', 'source_evidence_id': digest({'generated': day, 'symbol': code})}
            fields.append({**common, 'field': 'close', 'value': 10.0})
            eligibility_rows.append({**common, 'eligible': True})
    case = {'research_class': 'real_saved_development', 'evidence_class': 'generated_engineering',
        'execution_backend': 'v3_streamed_001', 'initial_cash': '1000000.00',
        'decision_fixture': {'kind': 'exposed_real_decision_table', 'codes': codes, 'calendar': signals,
            'fields': [{'name': 'close', 'unit': 'generated_currency'}],
            'field_rows': fields, 'eligibility_rows': eligibility_rows}}
    bundle = {'version': derivation.VERSION, 'evidence_class': derivation.CLASS,
        'original_calendar': days, 'symbols': codes, 'market_rows': [], 'stock_rows': []}
    pattern = [-3, -3, -2, -2, -1, -1, 1, 2, 3, 4]
    for i, day in enumerate(days[1:], 1):
        market = pattern[(i-1) % 10] / 100
        common = {'session': day, 'previous_session': days[i-1], 'effective_at': day + 'T15:00:00+08:00',
            'available_at': day + 'T15:00:00+08:00', 'source_status': 'generated_known'}
        bundle['market_rows'].append(stamped({**common, 'value': market}))
        for j, code in enumerate(codes):
            eligible = stamped({'eligible': True, 'effective_at': day + 'T15:00:00+08:00',
                'available_at': day + 'T15:00:00+08:00', 'source_status': 'generated_known'})
            stock_return = 0.2 * market + (1 if i % 2 else -1) * (1 + (j + i//2) % 3) / 1000
            bundle['stock_rows'].append(stamped({**common, 'symbol': code, 'value': stock_return,
                'return_basis': 'generated_causal_total_economic_return', 'action_coverage_status': 'generated_complete',
                'eligibility': eligible}))
    return case, bundle


def built():
    case, bundle = example()
    return {**case, **derivation.build(case, bundle)}


def stock_row(bundle, day=None, code=None):
    code = code or bundle['symbols'][0]
    day = day or bundle['original_calendar'][12]
    return next(r for r in bundle['stock_rows'] if r['session'] == day and r['symbol'] == code)


def test_exact_sixty_return_window_includes_signal_and_preserves_previous_close():
    case, bundle = example(); before = digest({'case': case, 'bundle': bundle})
    result = derivation.build(case, bundle); record = result[derivation.KEY]
    first = record['anchor_receipts'][0]; day = case['decision_fixture']['calendar'][0]
    index = bundle['original_calendar'].index(day)
    assert first['window_sessions'] == bundle['original_calendar'][index-59:index+1]
    assert len(first['window_sessions']) == 60 and first['window_sessions'][-1] == day
    assert first['first_previous_session'] == bundle['original_calendar'][index-60]
    assert len(record['anchor_receipts']) == 4
    assert digest({'case': case, 'bundle': bundle}) == before
    assert all(r['measurement']['status'] == 'ready' for r in record['anchor_receipts'])
    assert derivation.verify_case({**case, **result})['binding_verified'] is True


def test_entire_derived_grid_and_schedule_are_custodied_without_real_certification():
    case = built(); report = derivation.verify_case(case); contract = derivation.public_contract(case)
    rows = [r for r in case['decision_fixture']['field_rows'] if r['field'] == derivation.FIELD]
    assert len(rows) == 16 * 12
    assert report['anchor_evaluations'] == 4 and report['work_units']['input_cells'] == 4 * 60 * 13
    assert contract['source_authenticated'] is False and contract['action_coverage_verified'] is False
    assert contract['source_arrival_verified'] is False and contract['formal_target_success'] is False
    assert contract['real_research'] is False and 'GENERATED ENGINEERING ONLY' in contract['scope']
    anchor_receipts = {r['signal_date']: r for r in case[derivation.KEY]['anchor_receipts']}
    for row in rows:
        if row['session'] in anchor_receipts:
            assert row['source_evidence_id'] == digest(anchor_receipts[row['session']])
        else:
            assert row['value'] == 0


@pytest.mark.parametrize('kind', ['market_unknown','market_null','return_unknown','return_null',
    'adjusted_price','action_unknown','eligibility_unknown','eligibility_null','eligibility_late',
    'return_late','time_unknown','case_eligibility_late','signal_eligibility_conflict'])
def test_unknown_and_late_inputs_remain_common_cash_with_original_reasons(kind):
    case, bundle = example(); first = case['decision_fixture']['calendar'][0]
    row = stock_row(bundle); market = bundle['market_rows'][11]
    if kind == 'market_unknown': market['source_status'] = 'unknown'; stamped(market)
    if kind == 'market_null': market['value'] = None; stamped(market)
    if kind == 'return_unknown': row['source_status'] = 'unknown'; stamped(row)
    if kind == 'return_null': row['value'] = None; stamped(row)
    if kind == 'adjusted_price': row['return_basis'] = 'unverified_adjusted_price'; stamped(row)
    if kind == 'action_unknown': row['action_coverage_status'] = 'unknown'; stamped(row)
    if kind == 'eligibility_unknown': row['eligibility']['source_status'] = 'unknown'; stamped(row['eligibility']); stamped(row)
    if kind == 'eligibility_null': row['eligibility']['eligible'] = None; stamped(row['eligibility']); stamped(row)
    if kind == 'eligibility_late': row['eligibility']['available_at'] = first + 'T15:11:00+08:00'; stamped(row['eligibility']); stamped(row)
    if kind == 'return_late': row['available_at'] = first + 'T15:11:00+08:00'; stamped(row)
    if kind == 'time_unknown': row['available_at'] = None; stamped(row)
    if kind == 'case_eligibility_late': case['decision_fixture']['eligibility_rows'][0]['available_at'] = first + 'T15:11:00+08:00'
    if kind == 'signal_eligibility_conflict':
        row = stock_row(bundle, first); row['eligibility']['eligible'] = False; stamped(row['eligibility']); stamped(row)
    result = derivation.build(case, bundle)
    receipt = result[derivation.KEY]['anchor_receipts'][0]
    assert receipt['source_state'] == 'unavailable' and receipt['source_failures']
    assert receipt['measurement']['status'] == 'target_cash'
    assert result[target_schedule.KEY]['anchor_inputs'][0]['status'] == 'unavailable'
    assert all(r['value'] == 0 for r in result['decision_fixture']['field_rows'] if r['field'] == derivation.FIELD and r['session'] == first)
    assert derivation.verify_case({**case, **result})['source_authenticated'] is False


def test_historical_known_false_does_not_create_unannounced_continuous_eligibility_filter():
    case, bundle = example(); row = stock_row(bundle)
    row['eligibility']['eligible'] = False; stamped(row['eligibility']); stamped(row)
    result = derivation.build(case, bundle)
    first = result[derivation.KEY]['anchor_receipts'][0]
    assert first['source_failures'] == [] and first['measurement']['status'] == 'ready'
    assert row['symbol'] in first['measurement']['estimable_symbols']


def test_known_current_ineligibility_is_preserved_but_never_hides_unknown_returns():
    case, bundle = example(); first = case['decision_fixture']['calendar'][0]
    row = stock_row(bundle, first); row['eligibility']['eligible'] = False; stamped(row['eligibility']); stamped(row)
    case['decision_fixture']['eligibility_rows'][0]['eligible'] = False
    result = derivation.build(case, bundle)
    measurement = result[derivation.KEY]['anchor_receipts'][0]['measurement']
    assert measurement['status'] == 'ready'
    assert {'symbol': row['symbol'], 'reason': 'known_ineligible'} in measurement['excluded']
    other = stock_row(bundle); other['value'] = None; stamped(other)
    result = derivation.build(case, bundle)
    assert result[derivation.KEY]['anchor_receipts'][0]['measurement']['status'] == 'target_cash'


@pytest.mark.parametrize('kind', ['class','bundle_class','backend','sealed_case','sealed_bundle',
    'missing_market','missing_stock','previous_session','symbol_order','case_calendar_gap',
    'hash_tamper','nested_hash_tamper','unknown_basis','source_field_extra','duplicate_stock','oversized_time'])
def test_malformed_or_out_of_scope_inputs_refused_without_source_reads(monkeypatch, kind):
    case, bundle = example()
    if kind == 'class': case['evidence_class'] = 'real_verified'
    if kind == 'bundle_class': bundle['evidence_class'] = 'real_verified'
    if kind == 'backend': case['execution_backend'] = 'v3_l2_cash_001'
    if kind == 'sealed_case': case['decision_fixture']['calendar'] = ['2024' + d[4:] for d in case['decision_fixture']['calendar']]
    if kind == 'sealed_bundle': bundle['original_calendar'] = ['2024' + d[4:] for d in bundle['original_calendar']]
    if kind == 'missing_market': bundle['market_rows'].pop()
    if kind == 'missing_stock': bundle['stock_rows'].pop()
    if kind == 'previous_session': bundle['market_rows'][10]['previous_session'] = bundle['original_calendar'][0]; stamped(bundle['market_rows'][10])
    if kind == 'symbol_order': bundle['symbols'] = list(reversed(bundle['symbols']))
    if kind == 'case_calendar_gap': case['decision_fixture']['calendar'].pop(1)
    if kind == 'hash_tamper': bundle['market_rows'][10]['value'] += 0.1
    if kind == 'nested_hash_tamper': bundle['stock_rows'][10]['eligibility']['eligible'] = False; stamped(bundle['stock_rows'][10])
    if kind == 'unknown_basis': bundle['stock_rows'][10]['return_basis'] = 'actual_verified'; stamped(bundle['stock_rows'][10])
    if kind == 'source_field_extra': bundle['market_rows'][10]['secret_path'] = 'not-opened'
    if kind == 'duplicate_stock': bundle['stock_rows'][10] = deepcopy(bundle['stock_rows'][11])
    if kind == 'oversized_time': bundle['market_rows'][10]['available_at'] = 'x' * 1000
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('derivation opened a source'))
    with pytest.raises(ValueError): derivation.build(case, bundle)


@pytest.mark.parametrize('kind', ['weight','field_unit','field_id','receipt','schedule','drop_row','base_input','class_claim','policy_hash'])
def test_custody_rejects_changed_outputs_and_claims(kind):
    case = built(); record = case[derivation.KEY]
    row = next(r for r in case['decision_fixture']['field_rows'] if r['field'] == derivation.FIELD)
    if kind == 'weight': row['value'] = 0.7
    if kind == 'field_unit': case['decision_fixture']['fields'][-1]['unit'] = 'verified_real_target'
    if kind == 'field_id': row['source_evidence_id'] = '0' * 64
    if kind == 'receipt': record['anchor_receipts'][0]['measurement']['selected'].reverse()
    if kind == 'schedule': case[target_schedule.KEY]['anchor_inputs'][0]['input_receipt_sha256'] = '0' * 64
    if kind == 'drop_row': case['decision_fixture']['field_rows'].remove(row)
    if kind == 'base_input': case['decision_fixture']['field_rows'][0]['value'] += 1
    if kind == 'class_claim': record['source_authenticated'] = True
    if kind == 'policy_hash': record['numeric_policy_sha256'] = '0' * 64
    with pytest.raises(ValueError): derivation.verify_case(case)


def test_later_observations_do_not_change_an_earlier_anchor():
    case, bundle = example(); original = derivation.build(case, bundle)
    row = stock_row(bundle, bundle['original_calendar'][-1]); row['value'] += 0.001; stamped(row)
    changed = derivation.build(case, bundle)
    assert original[derivation.KEY]['anchor_receipts'][0] == changed[derivation.KEY]['anchor_receipts'][0]
    assert original[derivation.KEY]['bundle_sha256'] != changed[derivation.KEY]['bundle_sha256']


def test_fixed_derived_field_flows_through_original_target_builder_and_schedule():
    case = built()
    program = {'version': 'factor_strategy_program_v1', 'factors': [], 'target_weight_expression': derivation.FIELD,
        'hypothesis': 'Generated integration only', 'applicability': ['Generated input'], 'invalidation_conditions': ['No real inference']}
    compiled = real_program.validate_program(program, public_field_contract=case['decision_fixture']['fields'])
    ordinary = real_program.build_targets(compiled, decision_fixture=case['decision_fixture'], frozen_policy=real_program.POLICY)
    targets = target_schedule.apply_schedule(ordinary, case=case)
    days = case['decision_fixture']['calendar']
    assert {r['signal_date'] for r in targets['targets']} == {days[0], days[5], days[10], days[-2]}
    assert sum(float(r['target_weight']) for r in targets['targets'] if r['signal_date'] == days[0]) == pytest.approx(0.8)
    assert all(r['target_weight'] == '0' for r in targets['targets'] if r['signal_date'] == days[-2])
    assert targets['formal_target_success'] is False


def test_no_opt_in_no_new_verifier_or_public_claim():
    case, _ = example()
    assert derivation.verify_case(case) is None and derivation.public_contract(case) is None


@pytest.mark.parametrize('location', ['source_value', 'saved_metadata'])
def test_huge_integer_is_a_local_value_error_not_an_uncaught_overflow(location):
    if location == 'source_value':
        case, bundle = example()
        bundle['market_rows'][10]['value'] = 10**1000
        stamped(bundle['market_rows'][10])
        with pytest.raises(ValueError, match='finite JSON number'):
            derivation.build(case, bundle)
    else:
        case = built()
        case[derivation.KEY]['anchor_receipts'][0]['measurement']['downside_count'] = 10**1000
        with pytest.raises(ValueError, match='strict finite JSON metadata'):
            derivation.validate_case_metadata(case)
