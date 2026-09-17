"""Declared opportunity lineage; generated receipts, never model/account work."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from quanta_agents.meta_v3 import study_registry as sr
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from test_meta_v3_study_registry import prepared, create, isolate_registry
from test_meta_v3_ledger import A, request, settle


def relabel(plan, tmp_path, label):
    result = deepcopy(plan)
    result['study_id'] = label
    for i, trial in enumerate(result['trials']):
        trial['id'] = f'{label}_{i}'
        trial['root'] = str((tmp_path/f'{label}_{i}').resolve())
    return result


def test_expanded_study_cannot_reissue_old_slot_or_lose_unknown_cost(tmp_path):
    plan, tasks, pins = prepared(tmp_path)
    job = create(plan, tasks, pins)
    intent = job.reserve('one', A, request)
    job.unknown(intent['intent_id'], 'Generated unresolved completion')
    changed = relabel(plan, tmp_path, 'expanded')
    extra = deepcopy(changed['trials'][0])
    extra.update(id='new_case', root=str(tmp_path/'new_case'), case_hash='3'*64)
    changed['trials'].append(extra)
    with pytest.raises(AdmissionBlocked, match='cohort already registered'):
        sr.freeze(changed)
    assert sr.snapshot('study')['unresolved_reserve'] == 80
    with pytest.raises(AdmissionBlocked, match='unregistered study'):
        sr.snapshot('expanded')
    # The failed composite declaration must not consume the genuinely new slot.
    sr.freeze({'study_id':'prospective', 'trials':[extra]})


def test_split_study_cannot_reissue_any_member_of_frozen_cohort(tmp_path):
    plan, _, _ = prepared(tmp_path, trial_count=2)
    changed = relabel(plan, tmp_path, 'split')
    changed['trials'] = changed['trials'][1:]
    with pytest.raises(AdmissionBlocked, match='cohort already registered'):
        sr.freeze(changed)
    assert len(sr.snapshot('study')['trials']) == 2


def test_input_source_and_budget_revision_do_not_replace_old_opportunity(tmp_path):
    plan, _, _ = prepared(tmp_path)
    changed = relabel(plan, tmp_path, 'revision')
    changed['trials'][0]['tasks_hash'] = '3'*64
    changed['trials'][0]['source_pins_hash'] = '4'*64
    changed['trials'][0]['policy']['stage_tokens'] += 100
    changed['trials'][0]['duration_seconds'] += 100
    with pytest.raises(AdmissionBlocked, match='cohort already registered'):
        sr.freeze(changed)


def test_new_repeat_cannot_extend_claimed_cohort(tmp_path):
    plan, tasks, pins = prepared(tmp_path)
    create(plan, tasks, pins)
    changed = relabel(plan, tmp_path, 'optional_restart')
    changed['trials'][0]['repeat'] = 2
    with pytest.raises(AdmissionBlocked, match='cohort already registered'):
        sr.freeze(changed)


def test_concurrent_disjoint_repeat_labels_cannot_split_one_cohort(tmp_path):
    plan, _, _ = prepared(tmp_path)
    left = relabel(plan, tmp_path, 'left')
    right = relabel(plan, tmp_path, 'right')
    for proposed in (left, right):
        proposed['trials'][0]['case_hash'] = '3'*64
    right['trials'][0]['repeat'] = 2
    barrier = Barrier(2)
    def register(proposed):
        barrier.wait(timeout=5)
        try:
            sr.freeze(proposed)
            return 'registered'
        except AdmissionBlocked:
            return 'blocked'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(register, (left, right)))
    assert sorted(results) == ['blocked', 'registered']


def test_new_architecture_reports_prior_case_cost_without_double_booking(tmp_path):
    plan, tasks, pins = prepared(tmp_path, trial_count=2)
    one = create(plan, tasks, pins, 0)
    two = create(plan, tasks, pins, 1)
    settle(one, one.reserve('one', A, request), cost=17)
    pending = two.reserve('one', A, request)
    two.unknown(pending['intent_id'], 'Generated unknown')
    changed = relabel(plan, tmp_path, 'new_architecture')
    for trial in changed['trials']:
        trial['architecture_hash'] = '4'*64
    sr.freeze(changed)
    current = sr.snapshot('new_architecture')
    assert current['known_tokens'] == 0 and current['unresolved_reserve'] == 0
    history = current['case_history'][0]
    assert history['case_hash'] == '1'*64 and history['external_claimed_trials'] == 2
    assert history['external_known_tokens'] == 17 and history['external_unresolved_reserve'] == 80
    assert history['all_known_tokens'] == 17 and history['all_unresolved_reserve'] == 80
    assert history['formal_freshness_verified'] is False
    # Exactly the same original call identities, not copied synthetic charges.
    assert {(x['study_id'], x['trial_id'], x['id']) for x in history['calls']} == {
        ('study', c['trial_id'], c['id']) for c in sr.snapshot('study')['calls']}


def test_prospective_declared_case_is_distinct_but_not_automatically_fresh_oos(tmp_path):
    plan, tasks, pins = prepared(tmp_path)
    create(plan, tasks, pins)
    changed = relabel(plan, tmp_path, 'new_case')
    changed['trials'][0]['case_hash'] = '5'*64
    sr.freeze(changed)
    result = sr.snapshot('new_case')
    history = result['case_history'][0]
    assert history['external_claimed_trials'] == 0 and history['all_known_tokens'] == 0
    assert history['formal_freshness_verified'] is False
    assert result['full_stack_comparison_admitted'] is False


def test_unclaimed_predeclared_sibling_stays_available_after_other_repeat_fails(tmp_path):
    plan, tasks, pins = prepared(tmp_path, trial_count=2)
    one = create(plan, tasks, pins, 0)
    pending = one.reserve('one', A, request)
    one.unknown(pending['intent_id'], 'Generated unknown')
    two = create(plan, tasks, pins, 1)
    intent = two.reserve('one', A, request)
    settle(two, intent, cost=20)
    result = sr.snapshot('study')
    assert result['known_tokens'] == 20 and result['unresolved_reserve'] == 80
    assert len(result['calls']) == 2
