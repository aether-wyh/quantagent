"""Independent saved-account counterexamples; no model, market or account execution."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

import pytest

from quanta_agents.meta_v3.claim_support import review_claims
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3 import research_batch
from test_meta_v3_batch_research import configured, execute
from test_meta_v3_contrast_integration import account
from test_meta_v3_research_entry import program
from test_meta_v3_revision_preregistration import saved


def generated_evidence(tmp_path, monkeypatch, *, calendar_mode=None,
                       partial=False, metric='maximum_drawdown', threshold='-0.04'):
    monkeypatch.setattr(research_batch.subprocess, 'Popen',
                        lambda *a, **k: pytest.fail('unexpected account process'))
    tools = ResearchTools(tmp_path / 'stage', 'independent', configured(tmp_path), [])
    base = program(); base['target_weight_expression'] = '0.4'
    revision = program(); revision['target_weight_expression'] = '0.2'
    calendar = tools.case['decision_fixture']['calendar']
    capital = tools.case['initial_cash']
    baseline = account(base, calendar, capital, '-1000', '100')
    revised = account(revision, calendar, capital, '-600', '150')
    if calendar_mode == 'drop_same_session':
        # Explicit negative saved fixture, before either artifact is registered.
        # Both retain completed result/status and agree with each other, but each
        # omits a session required by the actual frozen case calendar.
        baseline['raw']['result']['daily'].pop(1)
        revised['raw']['result']['daily'].pop(1)
    elif calendar_mode == 'equal_length_shift':
        for artifact in (baseline, revised):
            for row in artifact['raw']['result']['daily']:
                row['date'] = str(date.fromisoformat(row['date']) + timedelta(days=10))
    elif calendar_mode == 'same_reverse_order':
        for artifact in (baseline, revised):
            artifact['raw']['result']['daily'].reverse()
    if partial:
        body = revised['raw'].pop('result')
        body['daily'] = body['daily'][:2]
        revised['raw'].update(status='failed', partial=body,
                              error='Generated incomplete valued prefix')
    saved(tools, 'baseline', 'develop_strategy', baseline)
    saved(tools, 'diagnosis', 'diagnose_execution', {'input_evidence_ids': ['baseline']})
    declaration = {
        'baseline_evidence_id': 'baseline', 'diagnosis_evidence_id': 'diagnosis',
        'mechanism_hypotheses': ['A different funded path; no identified cause'],
        'distinguishing_prediction': 'Drawdown decreases by at least four percentage points',
        'structural_change': 'Generated prospective exposure change',
        'revision_program': revision,
        'success_rule': 'Inspect the frozen observed check only',
        'failure_rule': 'Missing days or invalid accounting remain unevaluable',
        'contrast_checks': [{'id': 'drawdown_down', 'hypothesis_index': 0,
                             'metric': metric, 'operator': 'lte', 'threshold': threshold}],
    }
    registration = execute(tools, 'registration', 'register_experiment', declaration)
    tools._attach_experiment(revised, {'experiment_evidence_id': 'registration'})
    # Preserve the real current public producer's program/capital fields as well
    # as its actual registration/comparison attachment, without calling a worker.
    public = {'program_hash': digest(revision), 'full_initial_cash': capital,
              'raw_status': revised['raw']['status'], 'experiment': revised['experiment']['public']}
    return {'registration': registration,
            'revision': {'action': 'develop_strategy', 'public': public}}


def claim(**changes):
    return {'claim_id': 'observation', 'kind': 'registered_check',
            'evidence_id': 'revision', 'research_class': 'synthetic_calibration',
            'check_id': 'drawdown_down', 'status': 'matched', **changes}


def review(evidence, item):
    return review_claims([item], evidence, research_class='synthetic_calibration')['claims'][0]


@pytest.mark.parametrize('calendar_mode', ['drop_same_session', 'equal_length_shift', 'same_reverse_order'])
def test_same_short_calendar_reports_the_producers_unevaluable_observation(tmp_path, monkeypatch, calendar_mode):
    evidence = generated_evidence(tmp_path, monkeypatch, calendar_mode=calendar_mode)
    experiment = evidence['revision']['public']['experiment']
    assert experiment['comparison']['pairs'][0]['same_cash_calendar_and_initial_capital'] is True
    assert experiment['declared_check_results']['checks'][0]['status'] == 'unevaluable'
    assert 'frozen calendar' in experiment['declared_check_results']['checks'][0]['reason']
    result = review(evidence, claim(status='unevaluable'))
    assert result['status'] == 'supported', result


@pytest.mark.parametrize('partial', [False, True])
def test_money_units_keep_recorded_fee_facts_even_when_account_partial(tmp_path, monkeypatch, partial):
    evidence = generated_evidence(tmp_path, monkeypatch, partial=partial,
                                  metric='fees_on_recorded_trades', threshold='-50')
    expected = 'unevaluable' if partial else 'contradicted'
    assert review(evidence, claim(status=expected))['status'] == 'supported'
    numeric = {'claim_id': 'saved_fee', 'kind': 'numeric', 'evidence_id': 'revision',
               'research_class': 'synthetic_calibration', 'relation': 'eq',
               'path': ['experiment', 'declared_check_results', 'checks', 0, 'revision_value'],
               'unit': 'CNY', 'value': '150'}
    assert review(evidence, numeric)['status'] == 'supported'
    assert review(evidence, {**numeric, 'unit': 'percent'})['status'] == 'unsupported'
    delta = {**numeric, 'value': '50', 'path': numeric['path'][:-1] + ['revision_minus_baseline']}
    assert review(evidence, delta)['status'] == ('needs_review' if partial else 'supported')


def test_fraction_delta_and_threshold_are_differences_and_cannot_certify_cause(tmp_path, monkeypatch):
    evidence = generated_evidence(tmp_path, monkeypatch)
    row = evidence['revision']['public']['experiment']['declared_check_results']['checks'][0]
    assert Decimal(row['baseline_value']) == Decimal('0.10')
    assert Decimal(row['revision_value']) == Decimal('0.06')
    assert Decimal(row['revision_minus_baseline']) == Decimal('-0.04')
    numeric = {'claim_id': 'delta', 'kind': 'numeric', 'evidence_id': 'revision',
               'research_class': 'synthetic_calibration', 'relation': 'eq',
               'path': ['experiment', 'declared_check_results', 'checks', 0, 'revision_minus_baseline'],
               'unit': 'percentage_points', 'value': '-4'}
    assert review(evidence, numeric)['status'] == 'supported'
    assert review(evidence, {**numeric, 'unit': 'percent'})['status'] == 'unsupported'
    threshold = {**numeric, 'path': numeric['path'][:-1] + ['threshold']}
    assert review(evidence, threshold)['status'] == 'supported'
    observed = review(evidence, claim(text='This proves a profitable causal mechanism.'))
    assert observed['status'] == 'supported' and observed['text_support'] == 'unverified'
    assert observed['mechanism_or_strategy_success_verified'] is False


def test_contrast_cannot_change_the_public_executed_account_capital(tmp_path, monkeypatch):
    evidence = generated_evidence(tmp_path, monkeypatch)
    changed = deepcopy(evidence)
    experiment = changed['revision']['public']['experiment']
    # A coherently copied contrast from a smaller-capital scope must not certify
    # the revision public result that explicitly states the original full capital.
    experiment['declared_check_results']['frozen_initial_cash'] = '5000.00'
    for account_row in experiment['comparison']['accounts']:
        account_row['initial_cash'] = '5000.00'
    assert changed['revision']['public']['full_initial_cash'] == '10000.00'
    result = review(changed, claim())
    assert result['status'] != 'supported', result
