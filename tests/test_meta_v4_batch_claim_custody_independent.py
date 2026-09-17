"""Generated, non-executed account dictionaries test scalar custody boundaries."""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v3.claim_support import review_claims
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.research_iteration import executable_program_hash, public_diagnosis
from test_meta_v4_report_arguments import new_runtime


def _saved(action, artifact, arguments=None):
    return {'action': action, 'artifact_hash': digest(artifact), 'public': deepcopy(artifact),
        '_registered_artifact': deepcopy(artifact), '_registered_arguments': deepcopy(arguments or {})}


def _chain(case=None):
    case = case or {'research_class': 'synthetic_calibration', 'initial_cash': '1000',
        'decision_fixture': {'calendar': ['2030-01-02', '2030-01-03', '2030-01-04']}}
    days = case['decision_fixture']['calendar']
    declared, rows = [], []
    for index in (1, 2):
        cid = f'c{index:03d}'
        program = {'version': 'factor_strategy_program_v1',
            'factors': [{'name': 'fixture', 'expression': 'close'}],
            'target_weight_expression': str(index - 1), 'hypothesis': 'Not executed fixture ' + cid}
        identity = {'candidate_id': cid, 'program_hash': digest(program),
            'executable_program_hash': executable_program_hash(program)}
        declared.append({**identity, 'program': program})
        account = {'evidence_id': cid, 'program_hash': identity['program_hash'],
            'executable_program_hash': identity['executable_program_hash'],
            'status': 'completed_mechanical', 'complete_account': True,
            'statistics_scope': 'complete saved calendar', 'initial_cash': case['initial_cash'],
            'saved_cash_days': len(days), 'last_complete_date': days[-1], 'unvalued_trade_count': 0,
            'all_cash_days': 1, 'net_pnl': '-50' if index == 1 else '100',
            'mean_marked_share_fraction_of_gross_assets': '0.25', 'maximum_drawdown': '0.10',
            'fees_on_recorded_trades': '11.25' if index == 1 else '8.75'}
        rows.append({**identity, 'status': 'completed', 'raw_status': 'completed_mechanical',
            'account': account, 'observed_scan_completion': {'full_calendar_completed': True,
                'raw_result_saved': True, 'valued_calendar_sessions': len(days)}})
    registration = {'kind': 'frozen_research_batch_v1', 'case_hash': digest(case),
        'data_and_cost_contract_hash': digest(case), 'initial_cash': case['initial_cash'], 'candidates': declared}
    execution = {'kind': 'batch_execution_evidence_v1', 'batch_id': 'registration',
        'registration_hash': digest(registration), 'candidates': rows}
    page = {'registration_evidence_id': 'registration', 'batch_results_hash': digest(rows),
        'offset': 1, 'total_rows': 2, 'next_offset': None, 'rows': [deepcopy(rows[1])]}
    request = {'registration_evidence_id': 'registration', 'candidate_id': None,
        'table': 'results', 'offset': 1, 'limit': 1}
    evidence = {'registration': _saved('register_batch', registration),
        'execution': _saved('execute_batch', execution), 'page': _saved('inspect_batch', page, request)}
    evidence['page']['public'].update(returned_rows=1, requested_limit=1)
    return case, evidence


def _claim(case, *, metric='net_pnl', unit='CNY', value='100'):
    return {'claim_id': 'fixture_claim', 'kind': 'numeric', 'evidence_id': 'page',
        'research_class': case['research_class'], 'path': ['rows', 0, 'account', metric],
        'relation': 'eq', 'value': value, 'unit': unit}


def _check(case, evidence, claim=None):
    result = review_claims([claim or _claim(case)], evidence,
        research_class=case['research_class'], frozen_case=case)
    assert result['formal_target_success'] is False and result['general_report_truth_verified'] is False
    return result['claims'][0]


def _repin(evidence, *, regenerate_page=True):
    """Keep test custody hashes coherent so content guards are exercised."""
    registration = evidence['registration']['_registered_artifact']
    execution = evidence['execution']['_registered_artifact']
    execution['registration_hash'] = digest(registration)
    page = evidence['page']['_registered_artifact']
    if regenerate_page:
        page['batch_results_hash'] = digest(execution['candidates'])
        page['rows'] = deepcopy(execution['candidates'][1:2])
    for saved in evidence.values():
        saved['artifact_hash'] = digest(saved['_registered_artifact'])
        saved['public'] = deepcopy(saved['_registered_artifact'])
    evidence['page']['public'].update(returned_rows=1, requested_limit=1)


def test_complete_visible_page_supports_local_index_and_distinct_cash_day_count():
    case, evidence = _chain()
    before = deepcopy(evidence)
    assert _check(case, evidence)['status'] == 'supported'
    assert _check(case, evidence, _claim(case, metric='all_cash_days', unit='count', value='1'))['status'] == 'supported'
    assert evidence == before, 'Custody review must not modify saved evidence.'
    # The local page index 0 is globally c002, not c001.
    assert evidence['page']['public']['rows'][0]['candidate_id'] == 'c002'


def test_complete_candidate_is_not_disqualified_by_an_original_unknown_neighbor():
    case, evidence = _chain()
    # research_batch.run preserves an unresolved row with identity/status/error,
    # but no program hashes or account. It must not certify that unknown row,
    # or erase a different candidate's complete saved account scalar.
    execution = evidence['execution']['_registered_artifact']
    execution['candidates'][0] = {'candidate_id': 'c001', 'status': 'unknown',
        'error': 'Generated original unknown result shape', 'family_id': 'fixture',
        'parameters': {}, 'complexity': {}}
    _repin(evidence)
    assert _check(case, evidence)['status'] == 'supported'


def test_original_invalid_template_neighbor_does_not_block_complete_candidate():
    case, evidence = _chain()
    broken_program = {'invalid_fixture': 'missing executable fields'}
    registration = evidence['registration']['_registered_artifact']
    registration['candidates'][0].update(program=broken_program,
        program_hash=digest(broken_program), executable_program_hash=None,
        validation_error='ValueError: generated invalid template', complexity=None)
    execution = evidence['execution']['_registered_artifact']
    execution['candidates'][0] = {'candidate_id': 'c001', 'status': 'invalid',
        'error': 'ValueError: generated invalid template', 'family_id': 'fixture',
        'parameters': {}, 'complexity': None}
    _repin(evidence)
    assert _check(case, evidence)['status'] == 'supported'


def test_invalid_registered_target_cannot_be_promoted_by_fake_completed_result():
    case, evidence = _chain()
    broken_program = {'invalid_fixture': 'missing executable fields'}
    registration = evidence['registration']['_registered_artifact']
    registration['candidates'][1].update(program=broken_program,
        program_hash=digest(broken_program), executable_program_hash=None,
        validation_error='ValueError: generated invalid target', complexity=None)
    row = evidence['execution']['_registered_artifact']['candidates'][1]
    row.update(program_hash=digest(broken_program), executable_program_hash=None)
    row['account'].update(program_hash=digest(broken_program), executable_program_hash=None)
    # All fabricated completion/account flags remain positive; the original
    # invalid registration must still deny scalar support for this target.
    _repin(evidence)
    assert _check(case, evidence)['status'] == 'unsupported'


@pytest.mark.parametrize('mutation', ['wrong_batch', 'wrong_offset', 'wrong_execution_hash',
    'row_candidate_id', 'account_candidate_id', 'program_identity', 'duplicate_candidate'])
def test_cross_batch_wrong_page_and_candidate_aliases_are_unsupported(mutation):
    case, evidence = _chain()
    page = evidence['page']['_registered_artifact']
    execution = evidence['execution']['_registered_artifact']
    if mutation == 'wrong_batch':
        page['registration_evidence_id'] = 'another_batch'
        evidence['page']['_registered_arguments']['registration_evidence_id'] = 'another_batch'
        _repin(evidence, regenerate_page=False)
    elif mutation == 'wrong_offset':
        page['offset'] = 0
        evidence['page']['_registered_arguments']['offset'] = 0
        page['next_offset'] = 1
        _repin(evidence, regenerate_page=False)
    elif mutation == 'wrong_execution_hash':
        page['batch_results_hash'] = '0' * 64
        _repin(evidence, regenerate_page=False)
    else:
        if mutation == 'row_candidate_id':
            execution['candidates'][1]['candidate_id'] = 'c001'
        elif mutation == 'account_candidate_id':
            execution['candidates'][1]['account']['evidence_id'] = 'c001'
        elif mutation == 'program_identity':
            execution['candidates'][1]['program_hash'] = execution['candidates'][0]['program_hash']
        else:
            evidence['registration']['_registered_artifact']['candidates'][1] = deepcopy(
                evidence['registration']['_registered_artifact']['candidates'][0])
            execution['candidates'][1] = deepcopy(execution['candidates'][0])
        _repin(evidence)
    assert _check(case, evidence)['status'] == 'unsupported'


@pytest.mark.parametrize('mutation', ['unknown', 'failed', 'reused', 'partial_calendar',
    'unvalued_trade', 'smaller_capital', 'scan_incomplete'])
def test_incomplete_or_fake_reused_accounts_never_supply_full_performance(mutation):
    case, evidence = _chain()
    row = evidence['execution']['_registered_artifact']['candidates'][1]
    if mutation in ('unknown', 'failed', 'reused'):
        row['status'] = mutation
        if mutation == 'reused':
            row['reference'] = {'batch_id': 'foreign', 'candidate_id': 'c002', 'receipt_hash': '0' * 64}
    elif mutation == 'partial_calendar':
        row['account']['saved_cash_days'] -= 1
    elif mutation == 'unvalued_trade':
        row['account']['unvalued_trade_count'] = 1
    elif mutation == 'smaller_capital':
        row['account']['initial_cash'] = '1'
    else:
        row['observed_scan_completion']['full_calendar_completed'] = False
    _repin(evidence)
    assert _check(case, evidence)['status'] == 'unsupported'


@pytest.mark.parametrize('mutation', ['no_artifact', 'public_only_tamper', 'blocked',
    'wrong_action', 'missing_registration', 'missing_execution', 'wrong_request_table'])
def test_fabricated_metadata_or_broken_custody_is_not_a_unit_authority(mutation):
    case, evidence = _chain()
    if mutation == 'no_artifact':
        evidence['page'].pop('_registered_artifact')
    elif mutation == 'public_only_tamper':
        evidence['page']['public']['rows'][0]['account']['net_pnl'] = '999'
    elif mutation == 'blocked':
        evidence['page']['public']['delivery_blocked'] = True
    elif mutation == 'wrong_action':
        evidence['page']['action'] = 'read_evidence'
    elif mutation == 'missing_registration':
        evidence.pop('registration')
    elif mutation == 'missing_execution':
        evidence.pop('execution')
    else:
        evidence['page']['_registered_arguments']['table'] = 'attribution'
    assert _check(case, evidence)['status'] in ('unsupported', 'needs_review')


def test_units_signs_and_missing_frozen_case_do_not_gain_support():
    case, evidence = _chain()
    assert _check(case, evidence, _claim(case, unit='percent'))['reason'] == 'incompatible_units'
    assert _check(case, evidence, _claim(case, metric='maximum_drawdown', unit='percentage_points', value='10'))['reason'] == 'incompatible_units'
    assert _check(case, evidence, _claim(case, value='-100'))['status'] == 'contradicted'
    assert _check(case, evidence, _claim(case, metric='mean_marked_share_fraction_of_gross_assets', unit='percent', value='25'))['status'] == 'supported'
    result = review_claims([_claim(case)], evidence, research_class=case['research_class'])
    assert result['claims'][0]['status'] == 'unsupported'


def test_public_projection_bool_is_not_identical_to_saved_integer():
    case, evidence = _chain()
    evidence['execution']['_registered_artifact']['candidates'][1]['parameters'] = {'flag': 1}
    _repin(evidence)
    evidence['page']['public']['rows'][0]['parameters']['flag'] = True
    assert _check(case, evidence)['status'] == 'unsupported'


def test_review_class_cannot_relabel_a_synthetic_frozen_case_as_real():
    case, evidence = _chain()
    claim = _claim(case) | {'research_class': 'real_saved_development'}
    result = review_claims([claim], evidence, research_class='real_saved_development', frozen_case=case)
    assert result['claims'][0]['status'] == 'unsupported'


def _diagnosis(case, evidence):
    accounts = [deepcopy(row['account']) for row in evidence['execution']['_registered_artifact']['candidates']]
    for account in accounts:
        account['daily'] = [{'date': d} for d in case['decision_fixture']['calendar']]
    artifact = {'kind': 'saved_execution_attribution_v1', 'input_evidence_ids': ['c001', 'c002'],
        'accounts': accounts, 'pairs': [{'reference_evidence_id': 'c001', 'comparison_evidence_id': 'c002',
            'same_cash_calendar_and_initial_capital': True, 'comparison_minus_reference_fees': '-2.50'}]}
    saved = _saved('diagnose_execution', artifact)
    saved['public'] = public_diagnosis(artifact)
    return saved


@pytest.mark.parametrize('mutation', ['none', 'claim_sign', 'saved_sign', 'swapped_accounts', 'calendar_gap'])
def test_fee_difference_is_original_comparison_minus_reference(mutation):
    case, evidence = _chain()
    saved = _diagnosis(case, evidence)
    claim = _claim(case, value='-2.50') | {'path': ['pairs', 0, 'comparison_minus_reference_fees']}
    artifact = saved['_registered_artifact']
    if mutation == 'claim_sign':
        claim['value'] = '2.50'
    elif mutation == 'saved_sign':
        artifact['pairs'][0]['comparison_minus_reference_fees'] = '2.50'
    elif mutation == 'swapped_accounts':
        artifact['pairs'][0].update(reference_evidence_id='c002', comparison_evidence_id='c001')
    elif mutation == 'calendar_gap':
        artifact['accounts'][0]['daily'].pop()
    saved['artifact_hash'] = digest(artifact)
    saved['public'] = public_diagnosis(artifact)
    result = _check(case, {'page': saved}, claim)
    assert result['status'] == ('supported' if mutation == 'none' else 'contradicted' if mutation == 'claim_sign' else 'unsupported')


def test_final_uses_real_arguments_json_and_replaces_auxiliary_fields(tmp_path):
    runtime = new_runtime(tmp_path)
    tools = runtime._tools('extension')
    case, evidence = _chain(tools.case)
    history = []
    for eid, saved in evidence.items():
        artifact = deepcopy(saved['_registered_artifact'])
        original_request = deepcopy(saved['_registered_arguments'])
        folder = tools.folder / eid
        folder.mkdir(parents=True)
        (folder / 'artifact.json').write_text(json.dumps(artifact), encoding='utf-8')
        result = {k: deepcopy(v) for k, v in saved.items() if not k.startswith('_registered_')}
        result.update(evidence_id=eid, _registered_artifact={'spoofed': True},
            _registered_arguments={'table': 'wrong'})
        # This is the actual ledger.history response schema: no 'arguments' key.
        raw = {'action': saved['action'], 'arguments_json': json.dumps(original_request),
            'public_summary': 'Generated fixture; no model call', 'self_review': {}}
        history.append({'id': eid, 'status': 'applied', 'response': raw, 'result': result})
    tools.history = history
    report = {'outcome': 'abstain', 'program_evidence_id': None, 'evidence_ids': list(evidence),
        'conclusion': 'Unverified generated account fixture', 'claims': [_claim(case)],
        'limitations': ['No strategy was executed'], 'falsifiers': ['Saved custody mismatch'],
        'next_step': 'Independent review'}
    before = deepcopy(history)
    result = tools.final(report)
    assert result['claim_support']['claims'][0]['status'] == 'supported'
    assert tools.history == before
    assert result['substantive_report_accepted'] is None and result['formal_target_success'] is False
