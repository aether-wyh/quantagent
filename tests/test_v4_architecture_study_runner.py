"""Preparation and one-shot registration only; no research model or market runs."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_v4_architecture_study as prep
import run_v4_architecture_study as runner
from quanta_agents.meta_v3 import study_registry as sr
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest


@pytest.fixture
def specification(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path / 'isolated_registry.sqlite3')
    monkeypatch.setattr(runner.pe, 'supervise', lambda *_: {'generated_supervisor_fixture': True})
    result = prep.build(tmp_path / 'cohort')
    path = Path(result['spec_path'])
    return path, runner.read(path)


def test_complete_cohort_preserves_common_inputs_and_all_opportunities(specification):
    path, spec = specification
    assert not sr.REGISTRY.exists()
    assert len(spec['study_plan']['trials']) == 9
    assert len(set(spec['protocol']['dispatch_order'])) == 9
    assert len({digest(next(iter(s['tasks'].values()))) for s in spec['stages'].values()}) == 1
    assert spec['protocol']['formal_success_denominator_contribution'] == 0
    assert spec['protocol']['formal_gates_retained']['minimum_net_sharpe_rf2_strict'] == 1
    assert not list(path.parent.glob('*/plan.json'))


def test_all_nine_slots_create_under_real_registered_contract_but_cannot_restart(specification):
    path, spec = specification
    receipt = runner.freeze(path)
    assert receipt['slots'] == 9
    for trial_id in spec['protocol']['dispatch_order']:
        assert runner.dispatch(path, trial_id) == {'generated_supervisor_fixture': True}
        with pytest.raises(AdmissionBlocked, match='already exists'):
            runner.dispatch(path, trial_id)
    snapshot = sr.snapshot(spec['study_plan']['study_id'])
    assert snapshot['calls'] == [] and snapshot['known_tokens'] == 0
    assert len(snapshot['trials']) == 9


@pytest.mark.parametrize('change', ['different_input', 'missing_repeat', 'different_grant', 'changed_entry', 'formal_promotion'])
def test_mismatched_cohort_rejected_before_canonical_registration(specification, change):
    _, original = specification; spec = deepcopy(original)
    trial = spec['study_plan']['trials'][0]; stage = spec['stages'][trial['id']]
    if change == 'different_input':
        next(iter(stage['tasks'].values()))['idea'] = 'A different easier research question'
        trial['tasks_hash'] = digest(stage['tasks'])
    elif change == 'missing_repeat':
        trial['repeat'] = 2
    elif change == 'different_grant':
        trial['policy']['stage_calls'] -= 1
        trial['policy']['task_calls'] -= 1
    elif change == 'changed_entry':
        trial['process_envelope']['arguments'] = ['status', '--study-id', 'cohort']
    else:
        spec['protocol']['formal_success_denominator_contribution'] = 1
        for stage in spec['stages'].values(): stage['provenance']['comparison_protocol_hash'] = digest(spec['protocol'])
    with pytest.raises(AdmissionBlocked): runner.validate_spec(spec)
    assert not sr.REGISTRY.exists()
