import sys
import threading
import types

import pytest

from quanta_agents.meta.runtime import Engine, MODEL, EFFORT
from quanta_agents.meta.ashare_research import fixture_response


@pytest.fixture
def fake_case(monkeypatch):
    module = types.ModuleType('quanta_agents.meta.ashare_case')
    module.baseline_strategy = lambda: {'score_expression': '-pct_change(close, 10)',
        'filter_expression': 'close > 0', 'top_n': 10, 'rebalance_days': 5, 'gross_exposure': .8}
    def schema():
        props = {'score_expression': {'type': 'string'}, 'filter_expression': {'type': 'string'},
            'top_n': {'type': 'integer'}, 'rebalance_days': {'type': 'integer'},
            'gross_exposure': {'type': 'number'}}
        return {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}
    module.strategy_schema = schema
    class Case:
        splits = []
        def __init__(self, config=None):
            pass
        def manifest(self):
            return {'case_id': 'test_ashare', 'data_hash': 'constant'}
        def development_packet(self):
            return {'definition': 'plain reversal', 'split': 'development'}
        def evaluate(self, strategy, split='development'):
            self.splits.append(split)
            assert split != 'final'
            return {'score': .3, 'metrics': {}, 'eligible': True,
                    'evidence': 'CONFIRMATION_SECRET_728' if split == 'confirmation' else 'dev_only'}
        def diagnose(self, strategy, expression, horizon=5):
            return {'diagnosis': 'dev_only', 'horizon': horizon}
    module.AShareCase = Case
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return Case


class Gateway:
    def __init__(self, blocked=False):
        self.prompts = []
        self.entered = threading.Event()
        self.release = threading.Event()
        if not blocked:
            self.release.set()
    def run(self, *, prompt, schema, workdir, on_event, cancelled):
        self.prompts.append(prompt)
        self.entered.set()
        assert self.release.wait(10)
        step = workdir.name.rsplit('-', 1)[0]
        return {'response': fixture_response(step, schema),
            'usage': {'input_tokens': 100, 'output_tokens': 20, 'cached_input_tokens': 30, 'reasoning_output_tokens': 5},
            'model': MODEL, 'effort': EFFORT, 'duration_seconds': .01,
            'model_verified': False, 'verification': 'test_double'}


def finish(engine):
    engine.worker.join(20)
    assert not engine.worker.is_alive()


def test_real_action_loop_keeps_confirmation_out_of_prompts_and_self_checks(tmp_path, fake_case):
    gateway = Gateway()
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create(case='ashare')
        finish(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(gateway.prompts) == 13
        assert all('CONFIRMATION_SECRET_728' not in p for p in gateway.prompts)
        assert 'final' not in fake_case.splits
        assert len(run['research']['baseline']) == len(run['research']['candidate']) == 6
        assert len(run['self_checks']) == 13
        assert run['usage']['total_tokens'] == 13 * 120
        assert not run['comparison']['promotion'] and not run['comparison']['final_opened']
        assert not run['confirmation_exposure']['previously_opened']
        assert all(c['attempt'] == 1 for c in run['calls'])
    finally:
        engine.close()


def test_pause_after_paid_response_reuses_it_inside_research_phase(tmp_path, fake_case):
    gateway = Gateway(blocked=True)
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create(case='ashare')
        assert gateway.entered.wait(5)
        engine.control(run_id, 'pause')
        gateway.release.set()
        finish(engine)
        assert engine.get(run_id)['status'] == 'paused'
        assert len(gateway.prompts) == 1
        assert engine.get(run_id)['research']['baseline'] == []
        engine.control(run_id, 'resume')
        finish(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(gateway.prompts) == 13
        assert len(run['calls']) == 13
    finally:
        engine.close()


def test_repeated_confirmation_is_registered_even_for_fixture_runs(tmp_path, fake_case):
    engine = Engine(tmp_path)
    try:
        first = engine.create('fixture', case='ashare')
        finish(engine)
        second = engine.create('fixture', case='ashare')
        finish(engine)
        run = engine.get(second)
        assert run['status'] == 'completed', run.get('last_error')
        assert run['confirmation_exposure']['previously_opened']
        assert run['confirmation_exposure']['prior_runs'][0]['run_id'] == first
        assert not run['comparison']['promotion']
    finally:
        engine.close()


def test_invalid_action_is_rejected_before_controller_dispatch(tmp_path, fake_case):
    class Invalid(Gateway):
        def run(self, **kwargs):
            result = super().run(**kwargs)
            result['response']['action'] = 'read_final'
            return result
    engine = Engine(tmp_path, Invalid())
    try:
        run_id = engine.create(case='ashare')
        finish(engine)
        run = engine.get(run_id)
        assert run['status'] == 'failed'
        assert run['usage']['total_tokens'] == 120
        assert run['calls'][0]['status'] == 'failed'
        assert 'confirmation' not in fake_case.splits
    finally:
        engine.close()


def test_recovery_repairs_round_artifacts_without_repaying_and_links_prior_evidence(tmp_path, fake_case):
    gateway = Gateway()
    engine = Engine(tmp_path, gateway)
    original = engine.artifact
    failed = False
    def fail_once(run_id, name, data, label=''):
        nonlocal failed
        if name == 'baseline_round_1.json' and not failed:
            failed = True
            raise OSError('simulated artifact write interruption')
        return original(run_id, name, data, label)
    engine.artifact = fail_once
    try:
        run_id = engine.create(case='ashare')
        finish(engine)
        assert engine.get(run_id)['status'] == 'failed'
        assert len(engine.get(run_id)['research']['baseline']) == 1
        engine.control(run_id, 'resume')
        finish(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(gateway.prompts) == 13
        assert len(run['self_checks']) == 13
        assert (tmp_path / run_id / 'baseline_round_1.json').is_file()
        first = next(x for x in run['self_checks'] if x['step'] == 'baseline_round_1')
        record = run['research']['baseline'][0]
        assert first['evidence_hash'] == record['reviewed_evidence_hash']
        assert first['evidence_hash'] != record['observation_hash']
    finally:
        engine.close()
