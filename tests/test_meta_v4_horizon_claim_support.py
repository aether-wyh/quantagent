"""Hand-checkable endpoint returns through the actual frozen diagnostic tool.

Generated prices are engineering fixtures, never new market observations or
model behavior. Two eligible events share both horizons; their two-session
holding intervals overlap once. Every open increases by ten percent.
"""
from copy import deepcopy

import pandas as pd
import pytest

from quanta_agents.meta_v3.claim_support import review_claims
from quanta_agents.meta_v3.evidence_views import horizon_summary
from quanta_agents.meta_v3.kernel import module


SCOPE = 'real_saved_development'
COMMON = ['horizon_summary', 'denominators', 'common_sample_events']
MEAN_ONE = ['horizon_summary', 'curve', 0, 'mean_gross_forward_return']
MEAN_TWO = ['horizon_summary', 'curve', 1, 'mean_gross_forward_return']
OVERLAP = ['horizon_summary', 'curve', 1, 'dependence', 'same_stock_overlapping_event_pairs']


@pytest.fixture
def source():
    dates = pd.bdate_range('2019-01-02', periods=6)
    opening = pd.DataFrame({'fixture': [100, 110, 121, 133.1, 146.41, 161.051]}, index=dates)
    eligible = pd.DataFrame(True, index=dates, columns=opening.columns)
    feature = pd.DataFrame(1.0, index=dates, columns=opening.columns)
    filters = pd.DataFrame({'fixture': [1, 1, 0, 0, 0, 0]}, index=dates)
    identity = {'case_id': 'generated_horizon_claim_test', 'split': 'development',
        'datahash': 'a' * 64, 'strategy_hash': 'b' * 64, 'source_hash': 'c' * 64,
        'start': str(dates[0].date()), 'end': str(dates[-1].date()), 'loaded_through': str(dates[-1].date())}
    report = module('meta.horizon_diagnostics').build_horizon_diagnostics(
        opening=opening, eligible=eligible, scores=feature, filters=filters,
        feature=feature, identity=identity, expression='generated_feature', horizons=[1, 2])
    report['descriptive_conditioning'] = []
    return {'h': {'action': 'diagnose_horizons', 'public': {'horizon_summary': horizon_summary(report)}}}


def _check(source, path=COMMON, unit='count', value='2', *, scope=SCOPE, claim_scope=None, **extra):
    claim = {'claim_id': 'horizon_fact', 'kind': 'numeric', 'evidence_id': 'h',
        'research_class': claim_scope or scope, 'path': path, 'relation': 'eq',
        'unit': unit, 'value': value, **extra}
    return review_claims([claim], source, research_class=scope, report_text='Generated gross diagnostic statement.')


@pytest.mark.parametrize('path,unit,value,places,expected', [
    (COMMON, 'count', '2', None, 'supported'),
    (MEAN_ONE, 'percent', '10', 6, 'supported'),
    (MEAN_TWO, 'percent', '21', 6, 'supported'),
    (OVERLAP, 'count', '1', None, 'supported'),
    (COMMON, 'count', '3', None, 'contradicted'),
    (COMMON, 'CNY', '2', None, 'unsupported'),
    (MEAN_ONE, 'percent', '0.1', 6, 'contradicted'),
    (MEAN_ONE, 'percentage_points', '10', 6, 'unsupported'),
    (MEAN_ONE, 'CNY', '10', 6, 'unsupported'),
    (OVERLAP, 'count', '2', None, 'contradicted'),
])
def test_actual_common_sample_paths_and_unit_counterexamples(source, path, unit, value, places, expected):
    result = _check(source, path, unit, value, **({'decimal_places': places} if places is not None else {}))
    assert result['claims'][0]['status'] == expected
    assert result['report_text_support'] == 'needs_review'
    assert result['general_report_truth_verified'] is False
    assert result['formal_target_success'] is False


@pytest.mark.parametrize('mutation', ['wrong_action', 'wrong_horizon', 'wrong_count',
    'wrong_sample_hash', 'wrong_return_policy', 'wrong_split', 'fake_metadata_path'])
def test_same_numbers_do_not_register_unbound_metadata_or_curve_rows(source, mutation):
    summary = source['h']['public']['horizon_summary']
    path = MEAN_ONE
    if mutation == 'wrong_action':
        source['h']['action'] = 'inspect_execution'
    elif mutation == 'wrong_horizon':
        summary['curve'][0]['horizon_sessions'] = 2
    elif mutation == 'wrong_count':
        summary['curve'][0]['observations'] += 1
    elif mutation == 'wrong_sample_hash':
        summary['curve'][0]['common_sample_hash'] = 'f' * 64
    elif mutation == 'wrong_return_policy':
        summary['policy']['return'] = 'net portfolio return after actual fees'
    elif mutation == 'wrong_split':
        summary['scope']['split'] = 'final'
    else:
        source['h']['public']['metadata'] = {'horizon_summary': deepcopy(summary)}
        path = ['metadata'] + MEAN_ONE
    result = _check(source, path, 'percent', '10', decimal_places=6)
    assert result['claims'][0]['status'] == 'needs_review'
    assert result['claims'][0]['reason'] == 'unregistered_metric_semantics'


def test_new_horizon_metrics_require_admitted_research_class(source):
    assert _check(source, scope='synthetic_calibration')['claims'][0]['status'] == 'supported'
    assert _check(source, scope='formal_oos')['claims'][0]['status'] == 'needs_review'
    assert _check(source, claim_scope='formal_oos')['claims'][0]['status'] == 'unsupported'


def test_overlap_count_cannot_claim_an_independent_sample_size(source):
    summary = source['h']['public']['horizon_summary']
    summary['curve'][1]['dependence']['independent_sample_size'] = 2
    result = _check(source, ['horizon_summary', 'curve', 1, 'dependence', 'independent_sample_size'])
    assert result['claims'][0]['status'] == 'needs_review'
    summary['curve'][1]['dependence']['same_stock_overlapping_event_pairs'] = 2
    assert _check(source, OVERLAP, value='2')['claims'][0]['status'] == 'needs_review'


def test_unknown_gross_mean_and_prose_remain_unverified(source):
    source['h']['public']['horizon_summary']['curve'][0]['mean_gross_forward_return'] = None
    result = _check(source, MEAN_ONE, 'percent', '0')
    assert result['claims'][0]['reason'] == 'saved_value_unknown_not_zero'
    prose = {'claim_id': 'mechanism', 'kind': 'descriptive', 'evidence_id': 'h',
        'research_class': SCOPE, 'text': 'Overlapping losses prove that the mechanism fails.'}
    assert review_claims([prose], source, research_class=SCOPE)['claims'][0]['status'] == 'needs_review'
