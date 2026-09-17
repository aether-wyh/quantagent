"""Read-only cycle-accounting tests with generated SQLite/decision fixtures."""
import json
import sqlite3
from pathlib import Path

from test_research_v4_viewer import VIEWER


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def _call(call_id, task_id, tokens, action='inspect_inputs', args=None, result=None):
    response = {'action': action, 'arguments_json': json.dumps(args or {}),
        'public_summary': 'Generated viewer fixture'}
    return {'id': call_id, 'task_id': task_id,
        'status': 'applied' if tokens is not None else 'pending',
        'known_tokens': tokens, 'receipt': {'response': response} if tokens is not None else None,
        'result': result}


def _ledger(root, plan, calls):
    root.mkdir(parents=True, exist_ok=True)
    _write_json(root / 'plan.json', plan)
    with sqlite3.connect(root / 'ledger.sqlite3') as db:
        db.executescript('''
            CREATE TABLE stage(plan TEXT,plan_hash TEXT,paused INTEGER,reason TEXT);
            CREATE TABLE tasks(id TEXT,mode TEXT,terminal TEXT,final_call TEXT);
            CREATE TABLE calls(id TEXT,task_id TEXT,ordinal INTEGER,status TEXT,
                known_tokens INTEGER,reserve INTEGER,receipt TEXT,result TEXT,created REAL);
        ''')
        db.execute('INSERT INTO stage VALUES(?,?,0,NULL)', (json.dumps(plan), VIEWER._digest(plan)))
        db.executemany('INSERT INTO tasks VALUES(?,\'explore\',NULL,NULL)', [(k,) for k in plan['tasks']])
        for index, call in enumerate(calls, 1):
            db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?)',
                (call['id'], call['task_id'], index, call['status'], call['known_tokens'], 80000,
                 json.dumps(call['receipt']) if call['receipt'] else None,
                 json.dumps(call['result']) if call['result'] else None, index))


def _cycle(tmp_path):
    parent = (tmp_path / 'cycle').resolve()
    task_id, request_id = 'research', 'request_002'
    parent_plan = {'tasks': {task_id: {'case_hash': 'parent_case'}}, 'provenance': {}}
    request = {'kind': 'research_extension_request_v1', 'current_case_hash': 'parent_case',
        'request': {'problem': 'Generated scope extension'}}
    _ledger(parent, parent_plan, [_call('inspect_001', task_id, 17),
        _call(request_id, task_id, 11, 'request_research_extension', request['request'],
              {'artifact_hash': VIEWER._digest(request)})])
    _write_json(parent / 'tools' / task_id / request_id / 'artifact.json', request)
    folder = parent / 'controller_extensions' / request_id
    child = folder / 'stage'
    intent = {'kind': 'controller_extension_admission_v1', 'parent_task': task_id,
        'parent_root': str(parent), 'parent_plan_hash': VIEWER._digest(parent_plan),
        'parent_case_hash': 'parent_case', 'request_id': request_id,
        'request_hash': VIEWER._digest(request), 'decision': {'status': 'ready'},
        'policy': {'task_calls': 2}, 'deadline_epoch': 12345, 'child_case_hash': 'child_case'}
    child_plan = {'tasks': {'extension': {'case_hash': 'child_case'}},
        'policy': intent['policy'], 'deadline_epoch': intent['deadline_epoch'],
        'provenance': {'research_extension': {'intent_hash': VIEWER._digest(intent),
            'intent_path': str(folder / 'intent.json'), 'decision_path': str(folder / 'decision.json')}}}
    _ledger(child, child_plan, [_call('child_001', 'extension', 100),
        _call('child_002', 'extension', None)])
    _write_json(folder / 'intent.json', intent)
    decision = {'kind': 'controller_extension_decision_v1', 'status': 'ready',
        'intent_hash': VIEWER._digest(intent), 'child_root': str(child),
        'child_budget_registered': True, 'child_plan_hash': VIEWER._digest(child_plan)}
    _write_json(folder / 'decision.json', decision)
    return parent, child, folder, decision


def test_cycle_counts_bound_parent_and_child_once_without_writes(tmp_path):
    parent, child, folder, decision = _cycle(tmp_path)
    files = {p: p.read_bytes() for p in parent.rglob('*') if p.is_file()}
    status = VIEWER.cycle_snapshot(parent, child)
    assert status['aggregation_complete'] is True
    assert status['call_count'] == 4 and status['known_tokens'] == 128
    assert status['returned_calls'] == 3 and status['pending_calls'] == 1
    assert status['reserved'] == 80000
    assert status['current_stage']['role'] == 'child'
    assert status['current_stage']['call_count'] == 2
    assert [s['role'] for s in status['stages']] == ['parent', 'child']
    assert all(p.read_bytes() == original for p, original in files.items())


def test_unbound_child_is_excluded_and_partial_totals_are_visible(tmp_path):
    parent, child, folder, decision = _cycle(tmp_path)
    decision['child_plan_hash'] = 'wrong_hash'
    _write_json(folder / 'decision.json', decision)
    status = VIEWER.cycle_snapshot(parent, child)
    assert status['aggregation_complete'] is False
    assert status['current_stage'] is None
    assert status['call_count'] == 2 and status['known_tokens'] == 28
    assert len(status['stages']) == 1
    assert any('stage plan' in item['error'] for item in status['errors'])


def test_controller_keeps_prior_v4_and_diagnostic_separate_from_current_cycle(tmp_path):
    parent, child, folder, decision = _cycle(tmp_path)
    prior = (tmp_path / 'prior').resolve()
    _ledger(prior, {'tasks': {'review': {}}, 'provenance': {}}, [
        _call('prior_001', 'review', 10000), _call('prior_002', 'review', 20000),
        _call('prior_003', 'review', 22182)])
    path = tmp_path / 'status.json'
    _write_json(path, {'stages': [{'id': 'real_research'}],
        'observed_at': '2026-09-08T05:00:00+00:00', 'cycle_root': str(parent),
        'research_root': str(child), 'prior_v4_research_root': str(prior),
        'new_v4_research_calls': 999, 'new_v4_known_tokens': 999,
        'new_v4_diagnostic_calls': 1, 'new_v4_diagnostic_known_tokens': 8691})
    status = VIEWER.controller_snapshot(path)
    assert status['new_v4_research_calls'] == 4 and status['new_v4_known_tokens'] == 128
    assert status['research_status']['call_count'] == 2
    assert status['prior_v4_research_status']['call_count'] == 3
    assert status['prior_v4_research_status']['known_tokens'] == 52182
    assert status['new_v4_diagnostic_calls'] == 1 and status['new_v4_diagnostic_known_tokens'] == 8691
    assert 'historical_ledger_paths' not in status, 'V3 ledgers belong to the separate top-level history scope.'
