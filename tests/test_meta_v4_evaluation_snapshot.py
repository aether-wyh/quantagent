"""Generated canonical custody, no market reader, model, strategy or recovery."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3

import pytest

from quanta_agents.meta_v3 import study_registry as sr
from quanta_agents.meta_v3.evaluation_snapshot import closed_study_snapshot
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest, serial


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serial(value), encoding='utf-8')


@pytest.fixture
def generated(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path / 'canonical.sqlite3')
    case = {'research_class': 'synthetic_calibration', 'initial_cash': '1000000',
            'decision_fixture': {'codes': ['generated'], 'calendar': ['2019-01-02'],
                                 'field_rows': ['DO_NOT_COPY_MARKET_VALUES']}}
    tasks = {'task': {'case': case, 'case_hash': digest(case)}}
    pins = {'generated_engine': 'a' * 64}
    specs = [{'id': f't{i}', 'root': str(tmp_path / f't{i}'), 'case_hash': digest(case),
        'architecture_hash': str(i + 1) * 64, 'repeat': 1, 'tasks_hash': digest(tasks),
        'source_pins_hash': digest(pins), 'policy': {}, 'duration_seconds': 100,
        **({'producer_contract': {'kind': 'generated_only'}} if i == 1 else {})} for i in range(3)]
    plan = {'study_id': 'generated', 'trials': specs}
    stages = []
    with sr._db(create=True) as db:
        db.execute('INSERT INTO studies VALUES(?,?,?,?)', ('generated', 'f' * 64, serial(plan), digest(plan)))
        for i, spec in enumerate(specs):
            root = Path(spec['root'])
            binding = {'study_id': 'generated', 'trial_id': spec['id'], 'study_plan_hash': digest(plan),
                'trial_hash': digest(spec), 'root': str(root), 'claimed_at': 10}
            stage = {'tasks': tasks, 'policy': {}, 'provenance': {'source_pins': pins, 'study_trial': binding},
                'deadline_epoch': 110, 'model': 'generated', 'effort': 'generated'}
            stage_hash = digest(stage) if i < 2 else None
            db.execute('INSERT INTO trials VALUES(?,?,?,?,?,?)',
                ('generated', spec['id'], str(root), serial(spec), 10 if i < 2 else None, stage_hash))
            if i == 2:
                continue
            stages.append(stage); write(root / 'plan.json', stage)
            with sqlite3.connect(root / 'ledger.sqlite3') as local:
                local.executescript('''CREATE TABLE stage(id,plan,plan_hash,paused,reason);
                    CREATE TABLE tasks(id,input,mode,terminal,final_call);
                    CREATE TABLE calls(id,task_id,ordinal,status,intent,receipt,known_tokens,result);''')
                local.execute('INSERT INTO stage VALUES(1,?,?,0,NULL)', (serial(stage), stage_hash))
                local.execute('INSERT INTO tasks VALUES(?,?,?,?,?)',
                    ('task', serial(tasks['task']), 'explore', 'submitted' if i == 0 else None, 'final_1' if i == 0 else None))
            intent = {'study_id': 'generated', 'trial_id': spec['id'], 'slot': 1, 'stage_plan_hash': stage_hash}
            dispatch = {'generated_identity': spec['id']}
            receipt = {'intent_hash': digest(intent), 'dispatch_hash': digest(dispatch),
                'exit_code': 0, 'metrics': {'active_processes': 0}}
            db.execute('INSERT INTO process_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                ('generated', spec['id'], 1, serial(intent), digest(intent), serial(dispatch), digest(dispatch),
                 None, None, serial(receipt), digest(receipt)))
            if i == 1:
                producer_intent = {'study_id': 'generated', 'trial_id': spec['id'], 'stage_plan_hash': stage_hash}
                producer_receipt = {'intent_hash': digest(producer_intent), 'result': {'development_selection':
                    {'outcome': 'abstain', 'selected_candidate_id': None, 'selected_program_hash': None}}}
                db.execute('INSERT INTO producer_runs VALUES(?,?,?,?,?,?)', ('generated', spec['id'],
                    serial(producer_intent), digest(producer_intent), serial(producer_receipt), digest(producer_receipt)))
    report = {'outcome': 'abstain', 'program_evidence_id': None, 'evidence_ids': ['input:' + digest(case)],
              'conclusion': 'Generated abstention. No replacement strategy.'}
    response = {'action': 'submit_research_report', 'arguments_json': serial(report)}
    result = {'legal_submission': True, 'model_report': report}
    intent = {'intent_id': 'final_1', 'task_id': 'task', 'plan_hash': digest(stages[0])}
    receipt = {'request_identity': {'intent_id': 'final_1'}, 'usage': {'input_tokens': 2, 'output_tokens': 3},
               'artifact_sha256': {'scripted': 'a' * 64}, 'response': response}
    with sqlite3.connect(sr.REGISTRY) as db:
        db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',
            ('generated', 't0', 'final_1', digest(intent), 10, 5, digest(receipt)))
    with sqlite3.connect(tmp_path / 't0/ledger.sqlite3') as db:
        db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?,?)',
            ('final_1', 'task', 1, 'applied', serial(intent), serial(receipt), 5, serial(result)))
    write(tmp_path / 't0/calls/final_1/application.json',
          {'model_response_hash': digest(response), 'result': result, 'failed': False})
    return tmp_path, plan, response


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def test_original_slots_abstentions_and_projection_are_stable_read_only(generated, monkeypatch):
    root, _, _ = generated
    before = hashes(root)
    def no_mutation(*a, **k):
        pytest.fail('snapshot must not enter mutable registry transaction')
    monkeypatch.setattr(sr, '_db', no_mutation)
    result = closed_study_snapshot('generated')
    assert result == closed_study_snapshot('generated')
    assert hashes(root) == before
    assert [r['id'] for r in result['trials']] == ['t0', 't1', 't2']
    assert result['trials'][2]['status'] == 'not_started'
    assert result['trials'][0]['selection'] == {'task': None}
    producer = result['trials'][1]
    assert producer['stage']['tasks'][0]['terminal'] is None
    assert producer['selection']['outcome'] == 'abstain'
    assert 'DO_NOT_COPY_MARKET_VALUES' not in serial(result)
    assert result['formal_acceptance'] is False


@pytest.mark.parametrize('failure', ['process', 'model', 'task'])
def test_unresolved_dispatch_or_task_is_not_closed(generated, failure):
    root, _, _ = generated
    if failure == 'process':
        with sqlite3.connect(sr.REGISTRY) as db:
            db.execute("UPDATE process_runs SET receipt=NULL,receipt_hash=NULL WHERE trial_id='t0'")
    else:
        with sqlite3.connect(root / 't0/ledger.sqlite3') as db:
            db.execute("UPDATE calls SET status='pending'" if failure == 'model'
                       else 'UPDATE tasks SET terminal=NULL,final_call=NULL')
    with pytest.raises(AdmissionBlocked, match='not closed'):
        closed_study_snapshot('generated')


def test_final_application_cannot_replace_original_selection(generated):
    root, _, response = generated
    result = {'legal_submission': True, 'model_report': {'outcome': 'strategy_for_development', 'program_evidence_id': 'other'}}
    write(root / 't0/calls/final_1/application.json',
          {'model_response_hash': digest(response), 'result': result, 'failed': False})
    with pytest.raises(AdmissionBlocked, match='application/result drift'):
        closed_study_snapshot('generated')


def test_invalid_final_keeps_failed_payload_and_null_selection(generated):
    root, _, response = generated
    result = {'error': 'Scripted original final validation failure'}
    with sqlite3.connect(root / 't0/ledger.sqlite3') as db:
        db.execute("UPDATE calls SET status='failed',result=?", (serial(result),))
        db.execute("UPDATE tasks SET terminal='invalid_final',final_call=NULL")
    write(root / 't0/calls/final_1/application.json',
          {'model_response_hash': digest(response), 'result': result, 'failed': True})
    task = closed_study_snapshot('generated')['trials'][0]['stage']['tasks'][0]
    assert task['selection'] is task['final'] is None
    assert task['final_attempts'][0]['result'] == result
    assert task['failure_reason'] == 'invalid_final'


def test_missing_original_unclaimed_trial_is_rejected(generated):
    with sqlite3.connect(sr.REGISTRY) as db:
        db.execute("DELETE FROM trials WHERE id='t2'")
    with pytest.raises(AdmissionBlocked, match='original trial set'):
        closed_study_snapshot('generated')
