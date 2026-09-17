"""Independent offline controller counterexamples; no real model or study state."""
import time
import pytest

from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import Ledger, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime, source_pins
from test_meta_v4_controller import contracts, scripted_gateway, stage
from test_meta_v3_research_entry import fixture


def malformed_stage(tmp_path, change):
    tasks = {}
    for name in ('a_invalid', 'b_independent'):
        case = fixture.prepare(tmp_path / name, flat=True)
        if name == 'a_invalid':
            change(case)
        tasks[name] = {'idea': 'Inspect the declared input.', 'documents': [],
                       'case': case, 'case_hash': digest(case)}
    ledger = Ledger.create(tmp_path / 'stage', tasks=tasks,
        policy=ClosingPolicy(task_calls=3, stage_calls=6),
        deadline_epoch=time.time() + 7200,
        provenance={'source_pins': source_pins(), 'controller_policy': contracts(tasks)})
    return ResearchRuntime(ledger.root)


def test_invalid_task_fixture_does_not_prevent_independent_execution(tmp_path, monkeypatch):
    """Frozen input metadata rejection belongs to that task, not the whole stage."""
    def change(case):
        case['decision_fixture']['fields'][0]['unit'] = ''
    runtime = malformed_stage(tmp_path, change)
    calls = scripted_gateway(runtime, monkeypatch)
    status = runtime.run()
    assert calls == ['b_independent', 'b_independent']
    assert status['tasks']['b_independent']['terminal'] == 'submitted'
    assert status['work_schedule']['tasks']['a_invalid']['status'] == 'blocked_task_source'


def test_invalid_task_action_policy_does_not_prevent_independent_execution(tmp_path, monkeypatch):
    """Input admission must include the task-specific tool contract before ready."""
    def change(case):
        case['research_policy'] = {'version': 'structural_research_v1',
                                   'action_limits': {'inspect_inputs': -1}}
    runtime = malformed_stage(tmp_path, change)
    calls = scripted_gateway(runtime, monkeypatch)
    status = runtime.run()
    assert calls == ['b_independent', 'b_independent']
    assert status['tasks']['b_independent']['terminal'] == 'submitted'
    assert status['work_schedule']['tasks']['a_invalid']['status'] != 'ready'


@pytest.mark.parametrize('field', ['decision_fixture', 'raw_source_bindings'])
def test_missing_task_schema_field_is_local_and_visible(tmp_path, monkeypatch, field):
    runtime = malformed_stage(tmp_path, lambda case: case.pop(field))
    calls = scripted_gateway(runtime, monkeypatch)
    status = runtime.run()
    assert calls == ['b_independent', 'b_independent']
    assert field in status['work_schedule']['tasks']['a_invalid']['source_check']['reason']


def test_deadline_crossed_during_source_preflight_closes_stage_without_another_run(tmp_path, monkeypatch):
    """A bounded source pass can finish after its starting ledger snapshot expires."""
    runtime = stage(tmp_path)
    calls = scripted_gateway(runtime, monkeypatch)
    clock = [runtime.plan['deadline_epoch'] - 1]
    monkeypatch.setattr(time, 'time', lambda: clock[0])
    original = runtime.verify_task_inputs
    def verify(task_id):
        try:
            return original(task_id)
        finally:
            clock[0] = runtime.plan['deadline_epoch'] + 1
    monkeypatch.setattr(runtime, 'verify_task_inputs', verify)
    # Both source branches are unavailable, so stale ready selection cannot
    # incidentally force an atomic reserve to materialize their terminal state.
    from pathlib import Path
    artifact = runtime.plan['tasks']['independent']['case']['raw_source_bindings']['source_artifacts'][0]
    (Path(artifact['root']) / artifact['rows_file']).unlink()
    status = runtime.run()
    assert calls == []
    assert all(s['terminal'] == 'terminal_without_submission' for s in status['tasks'].values())
    assert status['work_schedule']['stage_disposition'] == 'all_tasks_terminal'
