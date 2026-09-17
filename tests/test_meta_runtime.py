import json
import threading
from pathlib import Path

import pytest

from quanta_agents.meta import benchmark
from quanta_agents.meta.runtime import Engine, BASE_INSTRUCTIONS, MODEL, EFFORT, digest
from quanta_agents.meta.store import now


def wait(engine):
    engine.worker.join(15)
    assert not engine.worker.is_alive()


class ControlledGateway:
    def __init__(self, block=False, missing_usage=False):
        self.prompts = []
        self.entered = threading.Event()
        self.release = threading.Event()
        if not block:
            self.release.set()
        self.missing_usage = missing_usage

    def run(self, *, prompt, schema, workdir, on_event, cancelled):
        self.prompts.append(prompt)
        self.entered.set()
        assert self.release.wait(10)
        if cancelled():
            raise RuntimeError('cancelled')
        if 'research_instructions' in schema['properties']:
            response = {k: 'Use evidence and competing explanations.' for k in schema['required']}
        else:
            response = {'strategy': benchmark.baseline_strategy(), 'summary': 'diagnosis',
                        'hypotheses': ['falsifiable'], 'next_test': 'test'}
        usage = {'input_tokens': 100, 'cached_input_tokens': 50, 'output_tokens': 20, 'reasoning_output_tokens': 10}
        if self.missing_usage:
            usage = dict.fromkeys(usage)
        on_event({'kind': 'reasoning', 'text': 'Public provider summary', 'data': {}})
        return {'response': response, 'usage': usage, 'model': MODEL, 'effort': EFFORT,
                'duration_seconds': 1, 'model_verified': False, 'verification': 'test_gateway'}


def test_complete_frozen_comparison_does_not_feed_final_to_models(tmp_path):
    gateway = ControlledGateway()
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create('live')
        wait(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(gateway.prompts) == 5
        assert all('"split": "final"' not in prompt for prompt in gateway.prompts)
        assert run['comparison']['promotion'] is False
        assert run['comparison']['scope'] == 'development_smoke_only'
        assert run['usage']['total_tokens'] == 600  # not 650 (reasoning) or 850 (cache)
        assert len(run['calls']) == 5
        assert len({c['id'] for c in run['calls']}) == 5
        names = {a['name'] for a in run['artifacts']}
        assert {'frozen_submissions.json', 'comparison.json', 'source_snapshot.zip', 'calls.json'} <= names
        with pytest.raises(ValueError):
            engine.start(run_id)
    finally:
        engine.close()


def test_pause_resume_preserves_completed_call_and_intervention_marks_run(tmp_path):
    gateway = ControlledGateway(block=True)
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create('live')
        assert gateway.entered.wait(5)
        engine.control(run_id, 'pause')
        gateway.release.set()
        wait(engine)
        assert engine.get(run_id)['status'] == 'paused'
        assert len(gateway.prompts) == 1
        engine.control(run_id, 'message', '检查子期稳定性。')
        engine.control(run_id, 'resume')
        wait(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(gateway.prompts) == 5
        assert '检查子期稳定性' in gateway.prompts[1]
        assert run['comparable'] is False
        assert run['comparison']['comparable'] is False
    finally:
        engine.close()


def test_budget_stops_before_next_paid_call(tmp_path):
    gateway = ControlledGateway()
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create('live', {'max_calls': 1})
        wait(engine)
        assert engine.get(run_id)['status'] == 'budget_exceeded'
        assert len(gateway.prompts) == 1
    finally:
        engine.close()


def test_unknown_usage_is_partial_and_keeps_reservation(tmp_path):
    engine = Engine(tmp_path, ControlledGateway(missing_usage=True))
    try:
        run_id = engine.create('live', {'soft_tokens': 1000, 'hard_tokens': 64000})
        wait(engine)
        run = engine.get(run_id)
        assert run['status'] == 'budget_exceeded'
        assert run['usage']['is_partial'] is True
        assert run['usage']['unknown_calls'] == 2
        assert run['usage']['cost_amount'] is None
    finally:
        engine.close()


def test_failed_call_requires_explicit_retry_and_keeps_attempt(tmp_path):
    class FailsOnce(ControlledGateway):
        def run(self, **kwargs):
            if not self.prompts:
                self.prompts.append(kwargs['prompt'])
                raise RuntimeError('unknown transport outcome')
            return super().run(**kwargs)
    engine = Engine(tmp_path, FailsOnce())
    try:
        run_id = engine.create('live')
        wait(engine)
        assert engine.get(run_id)['status'] == 'failed'
        with pytest.raises(ValueError, match='未知'):
            engine.control(run_id, 'resume')
        engine.control(run_id, 'retry')
        wait(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(run['calls']) == 6
        assert run['calls'][0]['status'] == 'retry_authorized'
        assert run['calls'][1]['attempt'] == 2
        assert run['usage']['unknown_calls'] == 1
    finally:
        engine.close()


def test_restart_reconciles_durable_receipt_and_blocks_unknown(tmp_path):
    engine = Engine(tmp_path)
    run_id = engine.create('fixture', start=False)
    folder = tmp_path / run_id / 'calls' / 'baseline_initial-1'
    folder.mkdir(parents=True)
    receipt = {'response': {'strategy': benchmark.baseline_strategy()}, 'usage': {'input_tokens': 0, 'output_tokens': 0}}
    (folder / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
    engine.store.save_call({'id': 'test-call', 'run_id': run_id, 'step': 'baseline_initial', 'attempt': 1,
                           'role': 'baseline_researcher', 'status': 'running', 'workdir': str(folder), 'prompt_hash': digest('test')})
    engine.store.update(run_id, {'status': 'running', 'active_started_epoch': 1.0})
    engine.close()
    engine = Engine(tmp_path)
    try:
        run = engine.get(run_id)
        assert run['status'] == 'interrupted'
        assert run['active_started_epoch'] is None
        assert run['calls'][0]['status'] == 'completed'
    finally:
        engine.close()


def test_cancel_reaches_gateway_and_prevents_followup(tmp_path):
    gateway = ControlledGateway(block=True)
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create('live')
        assert gateway.entered.wait(5)
        engine.control(run_id, 'cancel')
        gateway.release.set()
        wait(engine)
        assert engine.get(run_id)['status'] == 'cancelled'
        assert len(gateway.prompts) == 1
    finally:
        engine.close()


def test_invalid_model_output_can_be_retried_without_reusing_bad_receipt(tmp_path):
    class InvalidOnce(ControlledGateway):
        def run(self, **kwargs):
            receipt = super().run(**kwargs)
            if len(self.prompts) == 1:
                receipt['response']['strategy']['hold_days'] = 9999
            return receipt
    engine = Engine(tmp_path, InvalidOnce())
    try:
        run_id = engine.create('live')
        wait(engine)
        assert engine.get(run_id)['status'] == 'failed'
        assert engine.get(run_id)['usage']['total_tokens'] == 120
        engine.control(run_id, 'retry')
        wait(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(run['calls']) == 6
        assert run['calls'][1]['attempt'] == 2
    finally:
        engine.close()


def test_cached_invalid_receipt_is_marked_failed_not_reused_forever(tmp_path):
    engine = Engine(tmp_path, ControlledGateway())
    try:
        run_id = engine.create('fixture', start=False)
        response = {'strategy': {**benchmark.baseline_strategy(), 'hold_days': 999},
                    'summary': '', 'hypotheses': [], 'next_test': ''}
        engine.store.save_call({'id': run_id + '/cached', 'run_id': run_id, 'step': 'baseline_initial',
                               'attempt': 1, 'role': 'baseline_researcher', 'status': 'completed',
                               'prompt_hash': digest('same prompt'), 'receipt': {'response': response}, 'usage': None})
        with pytest.raises(ValueError, match='校验'):
            engine._model(run_id, 'baseline_initial', 'baseline_researcher', 'same prompt', engine._response_schema())
        assert engine.store.calls(run_id)[0]['status'] == 'failed'
    finally:
        engine.close()


def test_completed_wall_duration_does_not_keep_growing(tmp_path, monkeypatch):
    engine = Engine(tmp_path)
    try:
        run_id = engine.create('fixture')
        wait(engine)
        elapsed = engine.get(run_id)['wall_elapsed_seconds']
        monkeypatch.setattr('quanta_agents.meta.runtime.time.time', lambda: 9_999_999_999)
        assert engine.get(run_id)['wall_elapsed_seconds'] == elapsed
    finally:
        engine.close()
