"""Independent control generation and real shared subprocesses on generated data."""
from copy import deepcopy
import json
import time

import pytest

from quanta_agents.meta_v3 import generator_controls as gc, research_batch, runtime
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.research_tools import save_once
from test_meta_v3_batch_research import configured, program

SEED = '0123456789abcdef' * 4


def inputs(tmp_path, values=(.1, .2, .3, .4, .5, .6, .7, .8)):
    case = configured(tmp_path)
    case['initial_cash'] = '1000000.00'
    p = program(); p['target_weight_expression'] = '{{weight}}'
    return case, {'program_template': p, 'parameters': {'weight': list(values)}, 'axis_order': ['weight']}


def freeze(tmp_path, count=3, values=(.1, .2, .3, .4, .5, .6, .7, .8)):
    case, space = inputs(tmp_path, values)
    root = tmp_path / 'controls'
    result = gc.freeze(root, case, space, count=count, seed=SEED, deadline_epoch=time.time()+300)
    return root, case, space, result


def test_code_generated_controls_are_reproducible_before_execution_and_keep_axis_order(tmp_path):
    case, space = inputs(tmp_path)
    space['parameters'] = {'z': [.1, .3], 'a': [0, .1, .2, .3]}
    space['axis_order'] = ['z', 'a']
    space['program_template']['target_weight_expression'] = '{{z}} + {{a}}'
    one = gc.freeze(tmp_path/'one', case, space, count=4, seed=SEED, deadline_epoch=time.time()+300)
    two = gc.freeze(tmp_path/'two', case, space, count=4, seed=SEED, deadline_epoch=time.time()+300)
    assert one['arms'] == two['arms']
    assert [r['domain_index'] for r in one['arms']['fixed']] == [0, 2, 4, 7]
    assert one['arms']['fixed'][2]['parameters'] == {'z': .3, 'a': 0}
    assert len({r['domain_index'] for r in one['arms']['random']}) == 4
    assert gc.verify(tmp_path/'one')[1] == one
    assert not list((tmp_path/'one').rglob('intent.json'))
    case['initial_cash'] = '1'; space['parameters']['z'][0] = 99
    frozen, _ = gc.verify(tmp_path/'one')
    assert frozen['case']['initial_cash'] == '1000000.00'
    assert frozen['space']['parameters']['z'][0] == .1


def test_duplicate_slots_remain_charged_in_both_arms_and_shared_funded_results_recover(tmp_path, monkeypatch):
    root, case, _, controls = freeze(tmp_path, values=(.2, .2, .2))
    assert controls['reserved_candidates_total'] == 6
    assert controls['reserved_scan_cells_total'] == 288
    results = [gc.run_control(root, arm) for arm in gc.ARMS]
    for arm, result in zip(gc.ARMS, results):
        assert [r['status'] for r in result['candidates']] == ['completed', 'reused', 'reused']
        assert result['reserved_candidates'] == 3 and result['reserved_scan_cells'] == 144
        assert result['started_candidates'] == 1
        account = result['candidates'][0]['account']
        assert account['initial_cash'] == case['initial_cash']
        assert account['complete_account'] is True
        assert result['model_comparison_admitted'] is False and result['formal_target_success'] is False
        assert result['actual_project_model_calls'] == 0
    saved = {str(p):p.read_bytes() for p in root.rglob('worker_result.json')}
    assert len(saved) == 2  # Cross-arm reuse cannot add uncharged search opportunity.
    monkeypatch.setattr(research_batch.subprocess, 'Popen', lambda *a, **k: pytest.fail('saved control rerun'))
    replay = gc.run_control(root, 'fixed', execute_new=False)
    assert replay['candidates'] == results[0]['candidates']
    assert saved == {str(p):p.read_bytes() for p in root.rglob('worker_result.json')}


def test_invalid_candidates_are_preserved_without_resampling_or_execution(tmp_path, monkeypatch):
    case, space = inputs(tmp_path)
    space['program_template']['target_weight_expression'] = 'lag(close, -{{weight}})'
    root = tmp_path/'invalid'
    controls = gc.freeze(root, case, space, count=3, seed=SEED, deadline_epoch=time.time()+300)
    assert all(r['validation_error'] for rows in controls['arms'].values() for r in rows)
    monkeypatch.setattr(research_batch.subprocess, 'Popen', lambda *a, **k: pytest.fail('invalid control executed'))
    result = gc.run_control(root, 'random')
    assert [r['status'] for r in result['candidates']] == ['invalid'] * 3
    assert result['reserved_candidates'] == 3 and result['started_candidates'] == 0


def test_funded_execution_failure_is_kept_and_does_not_draw_replacement(tmp_path):
    root, _, _, _ = freeze(tmp_path, count=1, values=(2,))
    result = gc.run_control(root, 'fixed')
    assert result['reserved_candidates'] == 1 and result['started_candidates'] == 1
    assert [r['status'] for r in result['candidates']] == ['failed']
    assert result['candidates'][0]['parameters'] == {'weight': 2}
    assert len(list(root.rglob('worker_result.json'))) == 1


def test_expired_scope_retains_all_unstarted_slots_and_original_deadline(tmp_path, monkeypatch):
    root, _, _, _ = freeze(tmp_path)
    plan, _ = gc.verify(root)
    monkeypatch.setattr(gc.time, 'time', lambda: plan['deadline_epoch'] + 1)
    monkeypatch.setattr(research_batch.subprocess, 'Popen', lambda *a, **k: pytest.fail('expired control started'))
    result = gc.run_control(root, 'fixed')
    assert [r['status'] for r in result['candidates']] == ['not_started'] * 3
    assert result['reserved_candidates'] == 3 and result['started_candidates'] == 0
    path = root/'arms/fixed/batches/frozen/run_intent.json'
    before = path.read_bytes()
    again = gc.run_control(root, 'fixed', execute_new=False)
    # A later saved-only observation has a different observation reason; it
    # must preserve all original slots, their disposition and the old evidence.
    without_reason = lambda rows: [{k:v for k,v in row.items() if k != 'reason'} for row in rows]
    assert without_reason(again['candidates']) == without_reason(result['candidates'])
    assert all(row['reason'] == 'saved_only_recovery' for row in again['candidates'])
    original = json.loads((root/'arms/fixed/observations/001.json').read_text(encoding='utf-8'))
    assert original['candidates'] == result['candidates'] and path.read_bytes() == before


@pytest.mark.parametrize('change,expected', [('seed', 'plan identity'), ('candidate', 'provenance'), ('totals', 'provenance')])
def test_seed_candidate_and_budget_receipt_drift_refused(tmp_path, change, expected):
    root, _, _, _ = freeze(tmp_path)
    path = root / ('plan.json' if change == 'seed' else 'controls.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    if change == 'seed': data['seed'] = 'f' * 64
    elif change == 'candidate': data['arms']['random'][0]['parameters']['weight'] = 999
    else: data['reserved_candidates_total'] = 1
    path.write_text(json.dumps(data), encoding='utf-8')  # Generated corruption fixture.
    with pytest.raises(AdmissionBlocked, match=expected): gc.verify(root)


def test_changed_generator_source_refused_before_dispatch(tmp_path, monkeypatch):
    root, _, _, _ = freeze(tmp_path)
    monkeypatch.setattr(runtime, 'source_pins', lambda: {'changed': '0'*64})
    with pytest.raises(AdmissionBlocked, match='source drift'): gc.run_control(root, 'fixed')
    assert not list(root.rglob('intent.json'))


def test_reroll_in_same_scope_is_refused_and_originals_unchanged(tmp_path):
    root, case, space, _ = freeze(tmp_path)
    before = {p.name:p.read_bytes() for p in root.iterdir()}
    with pytest.raises(AdmissionBlocked, match='overwrite or reroll'):
        gc.freeze(root, case, space, count=3, seed='f'*64, deadline_epoch=time.time()+300)
    assert before == {p.name:p.read_bytes() for p in root.iterdir()}


def test_unresolved_worker_in_one_arm_blocks_new_other_arm(tmp_path, monkeypatch):
    root, _, _, _ = freeze(tmp_path)
    save_once(root/'arms/fixed/batches/frozen/candidates/c001/intent.json', {'generated_unknown_dispatch': True})
    monkeypatch.setattr(research_batch.subprocess, 'Popen', lambda *a, **k: pytest.fail('unknown work ignored'))
    with pytest.raises(AdmissionBlocked, match='every arm'): gc.run_control(root, 'random')
    assert not (root/'arms/random/batches/frozen/registration.json').exists()


@pytest.mark.parametrize('field,value', [('count', 0), ('seed', 'random'), ('deadline_epoch', 0)])
def test_invalid_control_bounds_refused_before_any_scope_write(tmp_path, field, value):
    case, space = inputs(tmp_path); args = {'count': 3, 'seed': SEED, 'deadline_epoch': time.time()+300}
    args[field] = value; root = tmp_path/'bad'
    with pytest.raises(AdmissionBlocked): gc.freeze(root, case, space, **args)
    assert not root.exists()


def test_control_scan_reservation_cannot_exceed_case_budget(tmp_path):
    case, space = inputs(tmp_path); case['batch_policy']['max_scan_cells_total'] = 143
    with pytest.raises(AdmissionBlocked, match='opportunity budget'):
        gc.freeze(tmp_path/'too_many', case, space, count=3, seed=SEED, deadline_epoch=time.time()+300)
    assert not (tmp_path/'too_many').exists()


def test_no_real_comparison_before_authentic_model_arm(tmp_path, monkeypatch):
    root, _, _, _ = freeze(tmp_path)
    plan, controls = gc.verify(root)
    plan['case']['research_class'] = 'real_saved_development'
    # Directly test the scope guard, without fabricating real input provenance.
    monkeypatch.setattr(gc, 'verify', lambda _: (plan, controls))
    with pytest.raises(AdmissionBlocked, match='real comparative execution closed'):
        gc.run_control(root, 'fixed')
    assert not list(root.rglob('intent.json'))
