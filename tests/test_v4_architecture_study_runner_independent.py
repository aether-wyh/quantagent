"""Independent controller boundary checks; no AI, strategy or source reads.

The request and snapshot below are explicitly generated fixtures. Admission
is observed at its API boundary; existing descendant tests enforce the actual
registry's exact reserve contract.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_v4_architecture_study as runner
import prepare_v4_architecture_study as prep
from quanta_agents.meta_v3 import research_extension, saved_ohlc_extension
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest


@pytest.mark.parametrize('requested_wall,expected', [(1800, 'ready'), (719, 'needs_implementation')])
def test_short_extension_keeps_original_final_reserves_or_refuses_before_preparation(
        tmp_path, monkeypatch, requested_wall, expected):
    policy = ClosingPolicy(task_calls=24, stage_calls=24, task_tokens=1400000,
                           stage_tokens=1400000, closing_seconds=600)
    plan = {'policy': asdict(policy), 'deadline_epoch': 107200,
        'provenance': {'study_trial': {'study_id': 'generated', 'trial_id': 'v1'},
            'extension_service_policy': {'fields': ['open', 'high', 'low'],
                'maximum_child_wall_seconds': 3600, 'maximum_child_model_calls': 14,
                'maximum_child_tokens': 900000}}}
    request = {'request': {'request_kind': 'data', 'requested_fields': ['open'],
        'requested_resource_bounds': {'symbols': 1, 'sessions': 244, 'model_calls': 14,
                                     'download_bytes': 0, 'wall_seconds': requested_wall}}}
    prepared_calls, decisions = [], []
    child = {'research_policy': {'action_limits': {'request_research_extension': 1}}}
    monkeypatch.setattr(runner.time, 'time', lambda: 100000)
    monkeypatch.setattr(runner, 'Ledger', lambda _: object())
    monkeypatch.setattr(research_extension, '_parent_request',
        lambda *a: (deepcopy(plan), {'case': {}}, deepcopy(request), {}, []))
    monkeypatch.setattr(runner.sr, 'snapshot', lambda _: {'calls': [
        {'trial_id': 'v1', 'known_tokens': 15000}, {'trial_id': 'v1', 'known_tokens': 20000},
        {'trial_id': 'other', 'known_tokens': None}]})
    monkeypatch.setattr(runner, '_source_admissions', lambda *a: [])

    def prepare(*args):
        prepared_calls.append(args)
        return {'child_case': deepcopy(child), 'source_admissions': []}

    def decide(*args, **kwargs):
        decisions.append(kwargs)
        return kwargs['decision']

    monkeypatch.setattr(saved_ohlc_extension, 'prepare', prepare)
    monkeypatch.setattr(research_extension, 'decide_extension', decide)
    result = runner.grant(tmp_path, 'research', 'generated_request')
    assert result['status'] == expected
    assert len(decisions) == 1
    if expected == 'needs_implementation':
        assert prepared_calls == [], 'A short request must not consume preparation/admission intent.'
        assert set(decisions[0]) == {'decision'}
        assert result['resource_bounds'] is None
    else:
        assert len(prepared_calls) == 1
        granted = decisions[0]['policy']
        assert all(getattr(granted, name) == getattr(policy, name)
                   for name in ('call_reserve', 'closing_reserve', 'closing_seconds'))
        assert granted.stage_calls + 2 + 1 <= policy.stage_calls
        assert granted.stage_tokens + 35000 + policy.closing_reserve <= policy.stage_tokens
        assert decisions[0]['deadline_epoch'] <= plan['deadline_epoch'] - policy.closing_seconds
        assert decisions[0]['child_case']['research_policy']['action_limits']['request_research_extension'] == 0


def test_rehashed_foreign_source_rejected_before_any_referenced_source_read(tmp_path, monkeypatch):
    # Only the already admitted original case document is read. No canary or
    # original market-source bytes are needed to test this metadata boundary.
    monkeypatch.setattr(runner, 'verify_case_sources', lambda _: None)
    spec = runner.read(prep.build(tmp_path / 'generated_scope_gate')['spec_path'])
    canary = tmp_path / 'never_open_sealed_2024_source.json'
    assert not canary.exists()
    for trial in spec['study_plan']['trials']:
        tasks = spec['stages'][trial['id']]['tasks']
        task = next(iter(tasks.values()))
        task['case']['evidence_sources'].append({'path': str(canary), 'sha256': 'a' * 64})
        task['case_hash'] = trial['case_hash'] = digest(task['case'])
        trial['tasks_hash'] = digest(tasks)
    assert len({t['case_hash'] for t in spec['study_plan']['trials']}) == 1
    reached = []

    def source_read(task):
        reached.append(task)
        pytest.fail('Foreign source reference reached byte-verification boundary.')

    monkeypatch.setattr(runner, 'verify_case_sources', source_read)
    with pytest.raises(AdmissionBlocked, match='exact original case'):
        runner.validate_spec(spec)
    assert reached == []
    assert not canary.exists()
