"""Generated registry/ledger fixtures only; no strategy, runtime or model dispatch."""
import json
import shutil
import sqlite3
import subprocess

import pytest

from test_research_v4_viewer import VIEWER
from test_research_v4_cycle_viewer import _call, _ledger, _write_json


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(VIEWER, 'PROJECT_ROOT', tmp_path)
    path = tmp_path / 'experiment_traces/meta_framework_v3/study_registry.sqlite3'
    path.parent.mkdir(parents=True)
    specs = [{'id': code + str(repeat), 'root': str(tmp_path / 'v4s1' / (code + str(repeat))),
        'repeat': repeat, 'architecture_contract': {'architecture': name}}
        for name, (code, _) in VIEWER.STUDY_ARCHITECTURES.items() for repeat in (1, 2, 3)]
    plan = {'study_id': 'v4s1', 'trials': specs}
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE studies(id TEXT,plan TEXT,plan_hash TEXT);
            CREATE TABLE trials(study_id TEXT,id TEXT,root TEXT,spec TEXT,claimed_at REAL,stage_plan_hash TEXT);
            CREATE TABLE calls(study_id TEXT,trial_id TEXT,id TEXT,reserve INTEGER,known_tokens INTEGER);
            CREATE TABLE producer_runs(study_id TEXT,trial_id TEXT,intent TEXT,intent_hash TEXT,receipt TEXT,receipt_hash TEXT);
            CREATE TABLE trial_descendants(root TEXT,study_id TEXT,trial_id TEXT,parent_root TEXT,request_id TEXT,binding TEXT,expected_plan TEXT,stage_plan_hash TEXT);
            CREATE TABLE model_call_stages(study_id TEXT,trial_id TEXT,id TEXT,root TEXT,stage_plan_hash TEXT,task_id TEXT);
        ''')
        db.execute('INSERT INTO studies VALUES(?,?,?)', ('v4s1', json.dumps(plan), VIEWER._digest(plan)))
        db.executemany('INSERT INTO trials VALUES(?,?,?,?,NULL,NULL)',
            [('v4s1', s['id'], s['root'], json.dumps(s)) for s in specs])
        db.execute('INSERT INTO calls VALUES(?,?,?,?,?)', ('unrelated_old_study', 'v1', 'old', 9000, 1000000))
    return path, specs


def _started_stage(path, spec, *, child=False, terminal=False, pending=False):
    from pathlib import Path
    root = Path(spec['root']) / 'child' if child else Path(spec['root'])
    plan = {'tasks': {'research': {}}, 'provenance': {'fixture_only': True}}
    call_id = 'child_call' if child else 'parent_call'
    _ledger(root, plan, [_call(call_id, 'research', None if pending else (20 if child else 10))])
    if terminal:
        with sqlite3.connect(root / 'ledger.sqlite3') as db:
            db.execute("UPDATE tasks SET terminal='submitted',final_call=?", (call_id,))
    with sqlite3.connect(path) as db:
        if child:
            db.execute('INSERT INTO trial_descendants VALUES(?,?,?,?,?,?,?,?)',
                (str(root), 'v4s1', spec['id'], spec['root'], 'request', '{}', '{}', VIEWER._digest(plan)))
        else:
            db.execute('UPDATE trials SET claimed_at=1,stage_plan_hash=? WHERE id=?', (VIEWER._digest(plan), spec['id']))
        db.execute('INSERT INTO calls VALUES(?,?,?,?,?)', ('v4s1', spec['id'], call_id, 80000, None if pending else (20 if child else 10)))
        db.execute('INSERT INTO model_call_stages VALUES(?,?,?,?,?,?)',
            ('v4s1', spec['id'], call_id, str(root), VIEWER._digest(plan), 'research'))
    return root


def _producer(path, *, outcome='abstain', bad_hash=False, metrics=None):
    intent = {'kind': 'generated_viewer_producer_fixture'}
    receipt = {'kind': 'registered_template_control_producer_v1', 'intent_hash': VIEWER._digest(intent),
        'result': {'candidates': [{'candidate_id': 'c001', 'status': 'completed'}],
            'development_selection': {'outcome': outcome, 'selected_candidate_id': 'c001' if outcome != 'abstain' else None,
                'selected_metrics': (metrics if metrics is not None else
                    {'return_on_full_initial_cash': 0.125, 'sharpe_rf2': 0.7}) if outcome != 'abstain' else None}},
        'actual_model_calls': 0, 'model_final': False, 'formal_target_success': False, 'ended_at': 1}
    with sqlite3.connect(path) as db:
        db.execute("UPDATE trials SET claimed_at=1 WHERE id='f1'")
        db.execute('INSERT INTO producer_runs VALUES(?,?,?,?,?,?)', ('v4s1', 'f1', json.dumps(intent),
            VIEWER._digest(intent), json.dumps(receipt), 'wrong' if bad_hash else VIEWER._digest(receipt)))


def test_missing_registry_never_creates_it_and_retains_planned_nine(tmp_path, monkeypatch):
    monkeypatch.setattr(VIEWER, 'PROJECT_ROOT', tmp_path)
    status = VIEWER.study_snapshot('v4s1')
    assert status['state'] == '未登记' and not status['registered']
    assert len(status['slots']) == 9 and all(s['state'] == '未登记' for s in status['slots'])
    assert not list(tmp_path.iterdir())


def test_canonical_parent_child_count_once_and_never_include_other_study(tmp_path, monkeypatch):
    path, specs = _fixture(tmp_path, monkeypatch)
    _started_stage(path, specs[0], terminal=True)
    _started_stage(path, specs[0], child=True, pending=True)
    _producer(path, outcome='development_candidate')
    originals = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    # Reading must not import the transaction-taking core registry snapshot.
    source = VIEWER.study_snapshot.__code__.co_names
    assert 'study_registry' not in source and 'ResearchRuntime' not in source
    status = VIEWER.study_snapshot('v4s1')
    assert len(status['slots']) == 9
    assert status['totals']['call_count'] == 2
    assert status['totals']['known_tokens'] == 10
    assert status['totals']['unknown_reserve'] == 80000
    assert status['totals']['parent_call_count'] == status['totals']['child_call_count'] == 1
    assert status['totals']['not_started'] == 7 and status['totals']['terminal'] == 1
    parent = next(s for s in status['slots'] if s['id'] == 'v1')
    assert parent['status'] == 'started', 'A completed parent cannot hide its unfinished child.'
    assert not parent['errors']
    fixed = next(s for s in status['slots'] if s['id'] == 'f1')
    assert fixed['status'] == 'terminal' and fixed['call_count'] == 0
    assert '12.50%' in fixed['result_summary']
    assert fixed['producer']['model_report'] is False
    assert all(p.read_bytes() == data for p, data in originals.items())
    assert set(originals) == {p for p in tmp_path.rglob('*') if p.is_file()}


def test_terminal_child_and_parent_complete_original_slot(tmp_path, monkeypatch):
    path, specs = _fixture(tmp_path, monkeypatch)
    _started_stage(path, specs[0], terminal=True)
    _started_stage(path, specs[0], child=True, terminal=True)
    status = VIEWER.study_snapshot('v4s1')
    assert status['totals']['terminal'] == 1 and status['totals']['known_tokens'] == 30


def test_positive_selection_decimal_strings_display_without_changing_receipt(tmp_path, monkeypatch):
    path, _ = _fixture(tmp_path, monkeypatch)
    metrics = {'return_on_full_initial_cash': '0.12500000000000000000001',
        'sharpe_rf2': '1.234567890123456789012345678901234567890'}
    _producer(path, outcome='development_candidate', metrics=metrics)
    original = path.read_bytes()
    slot = next(s for s in VIEWER.study_snapshot('v4s1')['slots'] if s['id'] == 'f1')
    assert slot['status'] == 'terminal' and not slot['errors']
    assert slot['result_summary'] == '开发候选：c001 · 完整本金收益 12.50% · RF2 Sharpe 1.235'
    assert slot['producer']['development_selection']['selected_metrics'] == metrics
    assert slot['producer']['model_report'] is False and slot['formal_target_success'] is False
    assert path.read_bytes() == original


@pytest.mark.parametrize('bad_hash', [False, True])
def test_fixed_abstain_is_producer_result_and_tamper_is_not_terminal(tmp_path, monkeypatch, bad_hash):
    path, _ = _fixture(tmp_path, monkeypatch)
    _producer(path, bad_hash=bad_hash)
    slot = next(s for s in VIEWER.study_snapshot('v4s1')['slots'] if s['id'] == 'f1')
    assert slot['status'] == ('started' if bad_hash else 'terminal')
    assert bool(slot['errors']) == bad_hash
    if not bad_hash:
        assert slot['result_summary'] == '弃权' and slot['formal_target_success'] is False


def test_controller_explicit_selector_reloads_and_drops_stale_inline_claim(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    path = tmp_path / 'gui_status_001.json'
    _write_json(path, {'stages': [], 'study_id': 'v4s1', 'study_status': {'known_tokens': 99999}})
    assert VIEWER.controller_snapshot(path)['study_status']['totals']['known_tokens'] == 0
    _write_json(path, {'stages': [], 'study_id': 'missing', 'study_status': {'known_tokens': 99999}})
    status = VIEWER.controller_snapshot(path)['study_status']
    assert status['state'] == '未登记' and status['slots'] == []
    _write_json(path, {'stages': [], 'study_status': {'known_tokens': 99999}})
    assert 'study_status' not in VIEWER.controller_snapshot(path)


def test_saved_stage_plan_tamper_keeps_slot_and_canonical_charges(tmp_path, monkeypatch):
    path, specs = _fixture(tmp_path, monkeypatch)
    root = _started_stage(path, specs[0], terminal=True)
    _write_json(root / 'plan.json', {'tampered': True})
    status = VIEWER.study_snapshot('v4s1')
    assert len(status['slots']) == 9 and status['totals']['known_tokens'] == 10
    assert status['totals']['terminal'] == 0 and status['slots'][0]['errors']


def test_missing_call_stage_binding_retains_cost_without_guessing_parent(tmp_path, monkeypatch):
    path, specs = _fixture(tmp_path, monkeypatch)
    _started_stage(path, specs[0], terminal=True)
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM model_call_stages')
    status = VIEWER.study_snapshot('v4s1')
    assert status['totals']['known_tokens'] == 10 and status['totals']['call_count'] == 1
    assert status['totals']['parent_call_count'] == 0 and status['totals']['terminal'] == 0
    assert status['slots'][0]['errors']


def test_real_page_renderer_consumes_api_nine_slots_without_html_injection(tmp_path, monkeypatch):
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node is required for the isolated DOM rendering check')
    path, _ = _fixture(tmp_path, monkeypatch)
    _producer(path, outcome='development_candidate')
    status = VIEWER.study_snapshot('v4s1')
    status['slots'][0]['result_summary'] = '<script>unsafe()</script>'
    script = VIEWER.PAGE.split('<script>', 1)[1].split('function renderResearch', 1)[0]
    harness = '''
const assert=require('node:assert/strict');
class Element {constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.textContent='';}
 append(...items){this.children.push(...items)} replaceChildren(...items){this.children=items}
 set innerHTML(value){throw Error('HTML injection')}
}
const target=new Element('div');
const document={createElement:tag=>new Element(tag),getElementById:id=>{assert.equal(id,'study');return target}};
'''
    checks = '''
renderStudy(status);
const walk=e=>[e,...e.children.flatMap(walk)];
const nodes=walk(target), rows=nodes.filter(e=>e.dataset.trialId);
assert.equal(rows.length,9);assert.equal(new Set(rows.map(e=>e.dataset.trialId)).size,9);
assert.ok(nodes.some(e=>e.textContent.includes('开发候选：c001')));
assert.ok(nodes.some(e=>e.textContent==='<script>unsafe()</script>'));
assert.ok(nodes.some(e=>e.textContent.includes('正式 54 次')));
renderStudy(null);assert.equal(target.children.length,0);
'''
    rendered = subprocess.run([node, '-e', harness + script + '\nconst status=' + json.dumps(status) + ';' + checks],
        capture_output=True, text=True, encoding='utf-8')
    assert rendered.returncode == 0, rendered.stderr
    assert VIEWER.PAGE.index('id="study"') < VIEWER.PAGE.index('id="cycle-results"')
    assert 'renderStudy(s.controller_status?.study_status)' in VIEWER.PAGE
