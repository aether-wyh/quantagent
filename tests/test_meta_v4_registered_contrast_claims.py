"""Hand-reconcilable registered contrasts, no model calls or account reruns."""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v3.claim_support import review_claims
from quanta_agents.meta_v3.ledger import digest
from test_meta_v3_contrast_integration import setup
from test_meta_v3_batch_research import execute


@pytest.fixture
def evidence(setup):
    tools, args, revision = setup
    execute(tools, 'registration', 'register_experiment', args)
    registration = json.loads((tools.folder / 'registration/artifact.json').read_text(encoding='utf-8'))
    tools._attach_experiment(revision, {'experiment_evidence_id': 'registration'})
    return {
        'registration': {'action': 'register_experiment', 'public': registration},
        'revision': {'action': 'develop_strategy', 'public': {
            'program_hash': registration['revision_program_hash'], 'experiment': revision['experiment']['public']}},
    }


def check(evidence, **changes):
    claim = {'claim_id': 'declared', 'kind': 'registered_check', 'evidence_id': 'revision',
             'research_class': 'synthetic_calibration', 'check_id': 'pnl_up', 'status': 'matched'}
    claim.update(changes)
    return review_claims([claim], evidence, research_class='synthetic_calibration', report_text='Unverified prose')


def test_real_registration_attachment_can_support_and_contradict_report_status(evidence):
    original = deepcopy(evidence)
    result = check(evidence)
    assert result['claims'][0]['status'] == 'supported'
    assert result['claims'][0]['observed_status'] == 'matched'
    assert result['claims'][0]['mechanism_or_strategy_success_verified'] is False
    assert check(evidence, check_id='fees_down')['claims'][0]['status'] == 'contradicted'
    assert check(evidence, check_id='fees_down', status='contradicted')['claims'][0]['status'] == 'supported'
    assert result['report_text_support'] == 'needs_review' and result['formal_target_success'] is False
    assert evidence == original


@pytest.mark.parametrize('mutation', ['uncited_registration', 'wrong_action', 'wrong_revision',
    'changed_registration', 'changed_threshold', 'changed_delta', 'flipped_status',
    'changed_account_metric', 'smaller_capital', 'unaligned_calendar', 'partial_account',
    'changed_counts', 'causal_promotion', 'foreign_baseline'])
def test_unbound_or_changed_facts_cannot_certify_a_registered_prediction(evidence, mutation):
    public = evidence['revision']['public']; experiment = public['experiment']
    result = experiment['declared_check_results']; row = result['checks'][1]
    if mutation == 'uncited_registration': evidence.pop('registration')
    elif mutation == 'wrong_action': evidence['revision']['action'] = 'diagnose_execution'
    elif mutation == 'wrong_revision': public['program_hash'] = 'f' * 64
    elif mutation == 'changed_registration': evidence['registration']['public']['declaration']['contrast_checks'][1]['threshold'] = '1000'
    elif mutation == 'changed_threshold': row['threshold'] = '1000'
    elif mutation == 'changed_delta': row['revision_minus_baseline'] = '999'
    elif mutation == 'flipped_status': row['status'] = 'contradicted'
    elif mutation == 'changed_account_metric': experiment['comparison']['accounts'][1]['net_pnl'] = '-999'
    elif mutation == 'smaller_capital': experiment['comparison']['accounts'][1]['initial_cash'] = '100'
    elif mutation == 'unaligned_calendar': experiment['comparison']['pairs'][0]['same_cash_calendar_and_initial_capital'] = False
    elif mutation == 'partial_account': experiment['comparison']['accounts'][1]['complete_account'] = False
    elif mutation == 'changed_counts': result['counts']['matched'] = 2
    elif mutation == 'causal_promotion': result['causal_mechanism_identified'] = True
    else: experiment['baseline_evidence_id'] = 'another_baseline'
    assert check(evidence)['claims'][0]['status'] == 'unsupported'


@pytest.mark.parametrize('suffix,unit,value,expected', [
    (['counts', 'matched'], 'count', '1', 'supported'),
    (['counts', 'contradicted'], 'count', '1', 'supported'),
    (['checks', 1, 'revision_minus_baseline'], 'CNY', '400', 'supported'),
    (['checks', 1, 'revision_minus_baseline'], 'CNY', '1000', 'contradicted'),
    (['checks', 0, 'revision_minus_baseline'], 'CNY', '50', 'supported'),
    (['checks', 0, 'threshold'], 'CNY', '-50', 'supported'),
    (['checks', 1, 'baseline_value'], 'CNY', '-1000', 'supported'),
    (['checks', 1, 'revision_value'], 'CNY', '-600', 'supported'),
    (['checks', 1, 'revision_minus_baseline'], 'percent', '400', 'unsupported'),
])
def test_numeric_check_facts_keep_original_signs_units_and_denominators(evidence, suffix, unit, value, expected):
    claim = {'claim_id': 'numeric', 'kind': 'numeric', 'evidence_id': 'revision',
        'research_class': 'synthetic_calibration', 'path': ['experiment', 'declared_check_results'] + suffix,
        'relation': 'eq', 'unit': unit, 'value': value}
    result = review_claims([claim], evidence, research_class='synthetic_calibration')
    assert result['claims'][0]['status'] == expected


def test_partial_account_can_support_only_the_unevaluable_status(setup):
    tools, args, revision = setup
    execute(tools, 'registration', 'register_experiment', args)
    registration = json.loads((tools.folder / 'registration/artifact.json').read_text(encoding='utf-8'))
    body = revision['raw'].pop('result'); body['daily'] = body['daily'][:2]
    revision['raw'].update(status='failed', partial=body, error='Generated incomplete account')
    tools._attach_experiment(revision, {'experiment_evidence_id': 'registration'})
    evidence = {'registration': {'action': 'register_experiment', 'public': registration},
                'revision': {'action': 'develop_strategy', 'public': {'experiment': revision['experiment']['public']}}}
    assert check(evidence, status='unevaluable')['claims'][0]['status'] == 'supported'
    assert check(evidence)['claims'][0]['status'] == 'contradicted'


def test_old_prose_and_causal_claims_are_not_promoted_by_the_new_typed_observation(evidence):
    for kind, expected in [('descriptive', 'needs_review'), ('causal', 'unsupported')]:
        claim = {'claim_id': 'prose', 'kind': kind, 'evidence_id': 'revision',
            'research_class': 'synthetic_calibration', 'text': 'A matched check proves a profitable causal mechanism.'}
        result = review_claims([claim], evidence, research_class='synthetic_calibration')
        assert result['claims'][0]['status'] == expected
    assert check(evidence, status='strategy_success')['claims'][0]['status'] == 'invalid'
    assert check(evidence, check_id='not_registered')['claims'][0]['status'] == 'unsupported'
    assert check(evidence, research_class='formal_oos')['claims'][0]['status'] == 'unsupported'
