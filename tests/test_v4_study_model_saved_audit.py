"""Generated read-only audit boundary counterexamples; no research execution."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_v4_study_model_saved as audit
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.research_iteration import executable_program_hash


def program(weight):
    return {'version': 'factor_strategy_program_v1', 'factors': [],
            'target_weight_expression': str(weight)}


@pytest.mark.parametrize('same_rule', [False, True])
def test_reuse_requires_current_rule_not_just_authentic_old_receipt(tmp_path, monkeypatch, same_rule):
    root = tmp_path / 'parent'; batch = root / 'batches/research/reg'
    old_program, new_program = program(1), program(1 if same_rule else 0)
    artifact = {'program': old_program}
    reference = {'ordinary_evidence_id': 'ordinary', 'artifact_hash': digest(artifact)}
    declared = {'candidate_id': 'c001', 'parameters': {}, 'program': new_program,
        'program_hash': digest(new_program), 'executable_program_hash': executable_program_hash(new_program),
        'validation_error': None}
    disposition = {'candidate_id': 'c001', 'status': 'reused', 'reference': reference}
    audit.save(batch / 'candidates/c001/disposition.json', disposition)
    stage = {'root': root, 'task_id': 'research', 'plan': {'tasks': {'research': {'case': {}}}},
        'calls': [{'id': 'ordinary', 'receipt': {'response': {'action': 'develop_strategy'}}}],
        'returned_artifacts': {'ordinary': artifact}, 'returned_results': {'ordinary': {'artifact_hash': digest(artifact)}}}
    invoked = []

    def original(*args):
        invoked.append(True)
        return {'artifact_hash': digest(artifact), 'metrics': {'net_return': '0.1'}}

    monkeypatch.setattr(audit, 'candidate', original)
    if not same_rule:
        with pytest.raises(AdmissionBlocked, match='executable differs'):
            audit.batch_candidate(stage, batch, declared, disposition)
        assert invoked == []
    else:
        row = audit.batch_candidate(stage, batch, declared, disposition)
        assert row['new_execution'] is False and row['metrics'] == {'net_return': '0.1'}
        assert invoked == [True]


def test_incomplete_job_refuses_before_stage_snapshot_or_tree_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    root = tmp_path / 'experiment_traces/v4s1/v1'
    audit.save(root.parent / 'spec.json', {'study_plan': {'trials': [{'id': 'v1', 'root': str(root)}]}})
    monkeypatch.setattr(audit, 'snapshot', lambda *a: pytest.fail('Live stage must not be read.'))
    monkeypatch.setattr(audit, 'canonical', lambda *a: pytest.fail('Completion gate must fail first.'))
    with pytest.raises(AdmissionBlocked, match='receipt.json'):
        audit.audit('v1')


def test_registered_but_unexecuted_candidates_remain_once_and_invalid_program_is_retained(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    root = tmp_path / 'experiment_traces/v4s1/v1'
    case = {'kind': 'generated_only'}; valid = program(1)
    declarations = [{'candidate_id': 'c001', 'parameters': {}, 'program': valid,
        'program_hash': digest(valid), 'executable_program_hash': executable_program_hash(valid), 'validation_error': None},
        {'candidate_id': 'c002', 'parameters': {}, 'program': {},
         'program_hash': digest({}), 'executable_program_hash': None, 'validation_error': 'Generated invalid program'}]
    registration = {'case_hash': digest(case), 'candidates': declarations, 'reserved_candidates': 2}
    plan = {'tasks': {'research': {'case': case}}, 'provenance': {'architecture_contract': {'architecture': 'generated'}}}
    call = {'id': 'reg', 'status': 'applied', 'known_tokens': 0, 'reserve': 1,
            'receipt': {'response': {'action': 'register_batch'}}, 'result': {'artifact_hash': digest(registration)}}
    stage = {'root': root, 'task_id': 'research', 'plan': plan,
             'state': {'terminal': 'terminal_without_submission'}, 'calls': [call]}
    trial = {'id': 'v1', 'root': str(root), 'tasks_hash': digest(plan['tasks']),
             'architecture_contract': plan['provenance']['architecture_contract'], 'case_hash': digest(case)}
    bound = {'stage_plan_hash': digest(plan), 'call_stages': {'reg': {'root': str(root)}},
             'model_calls': {'reg': {'known_tokens': 0, 'reserve': 1}}, 'descendants': []}
    audit.save(root.parent / 'spec.json', {'study_plan': {'trials': [trial]}})
    audit.save(root / 'process_runs/1/receipt.json', {'metrics': {'active_processes': 0}})
    audit.save(root / 'batches/research/reg/registration.json', registration)
    monkeypatch.setattr(audit, 'snapshot', lambda *a: stage)
    monkeypatch.setattr(audit, 'canonical', lambda *a: bound)
    monkeypatch.setattr(audit, 'verify_call', lambda *a: (call['result'], registration))
    result = audit.audit('v1')
    assert result['candidate_opportunity_count'] == 2
    assert {r['status'] for r in result['accounts']} == {'not_started'}
    assert all(r['metrics'] is None for r in result['accounts'])
    assert result['batch_reviews'][0]['execution_observation_call_ids'] == []
