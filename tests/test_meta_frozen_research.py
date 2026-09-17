import json
import sys
import zipfile

import pandas as pd
import pytest

from quanta_agents.meta.runtime import Engine, MODEL, EFFORT, digest
from test_meta_ashare_runtime import Gateway, fake_case


FROZEN = {
    'name': 'Frozen comparison protocol',
    'research_instructions': '  CANDIDATE_GUIDANCE_SENTINEL: seek discriminating evidence.\n',
    'source_run_id': 'earlier-run',
    'assessment': 'OLD_ASSESSMENT_MUST_NOT_BECOME_THIS_RUN_SELF_CHECK',
    'next_step': 'historical next step',
}


def complete(engine):
    engine.worker.join(45)
    assert not engine.worker.is_alive()


def config(**overrides):
    return {'calls_per_architecture': 12, 'frozen_candidate': dict(FROZEN),
            'evaluation_split': 'development', **overrides}


class PrivateTraceGateway(Gateway):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.steps = []
        self.schemas = []

    def run(self, **kwargs):
        step = kwargs['workdir'].name.rsplit('-', 1)[0]
        self.steps.append(step)
        self.schemas.append(kwargs['schema'])
        result = super().run(**kwargs)
        if step != 'meta_proposal':
            arm = step.split('_')[0]
            result['response']['decision_summary'] = 'PRIVATE_HISTORY_' + arm
        return result


def test_frozen_candidate_first_runs_24_calls_without_cross_arm_history(tmp_path, fake_case):
    gateway = PrivateTraceGateway()
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create(case='ashare', research_config=config(research_order=['candidate', 'baseline']))
        complete(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert gateway.steps == [f'{arm}_round_{n}' for arm in ['candidate', 'baseline'] for n in range(1, 13)]
        assert len(run['calls']) == len(run['self_checks']) == 24
        assert all(call['role'] != 'meta_designer' for call in run['calls'])
        assert run['usage']['total_tokens'] == 24 * 120
        for step, prompt in zip(gateway.steps, gateway.prompts):
            own = step.split('_')[0]
            other = 'baseline' if own == 'candidate' else 'candidate'
            assert 'PRIVATE_HISTORY_' + other not in prompt
            if own == 'baseline':
                assert 'CANDIDATE_GUIDANCE_SENTINEL' not in prompt
        assert FROZEN['assessment'] not in json.dumps(run['self_checks'])
        assert run['steps']['meta_proposal']['research_instructions'] == FROZEN['research_instructions']
        assert run['steps']['meta_proposal']['source_proposal_hash'] == digest(FROZEN)
        assert all(len(run['research'][arm]) == 12 for arm in ['baseline', 'candidate'])
        assert gateway.schemas[5]['properties']['action']['enum'] == ['diagnose', 'backtest']
        assert 'submit' in gateway.schemas[6]['properties']['action']['enum']
        assert gateway.schemas[11]['properties']['action']['enum'] == ['submit']
        assert set(run['comparison']['arm_results']) == {'baseline', 'candidate'}
        assert run['comparison']['evaluation_is_oos'] is False
        assert run['confirmation_opened'] is False
        assert run['confirmation_exposure'] is None
        assert 'confirmation' not in fake_case.splits
        assert engine.store.db.execute('SELECT COUNT(*) FROM evaluation_exposures').fetchone()[0] == 0
        assert run['budget']['max_calls'] >= 24
        assert run['budget']['max_architecture_tokens'] == 1_000_000
        assert run['model'] == MODEL and run['effort'] == EFFORT
    finally:
        engine.close()


@pytest.mark.parametrize('arm', ['baseline', 'candidate'])
def test_single_arm_uses_12_calls_and_does_not_fabricate_other_submission(tmp_path, fake_case, arm):
    gateway = PrivateTraceGateway()
    engine = Engine(tmp_path, gateway)
    research = config(only_architecture=arm)
    if arm == 'baseline':
        research['frozen_candidate'] = None
    try:
        run_id = engine.create(case='ashare', research_config=research)
        complete(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert gateway.steps == [f'{arm}_round_{n}' for n in range(1, 13)]
        assert len(run['calls']) == 12
        other = 'candidate' if arm == 'baseline' else 'baseline'
        assert run['research'][other] == []
        assert run['steps'][other + '_refine']['skipped'] is True
        assert 'response' not in run['steps'][other + '_refine']
        assert set(run['comparison']['arm_results']) == {arm}
        assert other not in run['comparison']
        assert run['comparison']['score_delta'] is None
        frozen = json.loads((tmp_path / run_id / 'frozen_submissions.json').read_text(encoding='utf-8'))
        assert set(frozen) == {arm}
        assert run['config']['experiment_protocol']['expected_max_model_calls_without_retries'] == 12
        assert run['comparison']['promotion'] is False
    finally:
        engine.close()


def test_eighteen_rounds_and_scaled_accident_budget(tmp_path, fake_case):
    engine = Engine(tmp_path)
    try:
        run_id = engine.create('fixture', case='ashare', research_config=config(
            calls_per_architecture=18, only_architecture='candidate'))
        complete(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(run['calls']) == 18
        assert run['research']['candidate'][-1]['response']['action'] == 'submit'
        assert run['budget']['hard_tokens'] == 3_600_000
        assert run['budget']['max_calls'] == 78
        assert run['budget']['max_attempts_per_step'] == 2
        assert run['budget']['max_call_seconds'] == 1800
    finally:
        engine.close()


def test_task_initial_strategy_is_used_and_starting_execution_is_persisted(tmp_path, fake_case, monkeypatch):
    module = sys.modules['quanta_agents.meta.ashare_case']
    observed = []
    class TaskCase(fake_case):
        def __init__(self, config=None):
            self._evaluation_raw = {}
        def initial_strategy(self):
            return {**module.baseline_strategy(), 'score_expression': 'pct_change(close, 60)'}
        def evaluate(self, strategy, split='development'):
            observed.append((dict(strategy), split))
            result = {**super().evaluate(strategy, split), 'strategy_hash': digest(strategy)}
            self._evaluation_raw[(split, result['strategy_hash'])] = {
                '_daily_df': pd.DataFrame({'date': ['2020-01-02'], 'balance': [1_000_000]}),
                '_trades_df': pd.DataFrame(columns=['date', 'side']),
                '_target_weights': pd.DataFrame({'sh600000': [0.0]}, index=pd.to_datetime(['2020-01-02'])),
            }
            return result
    monkeypatch.setattr(module, 'AShareCase', TaskCase)
    engine = Engine(tmp_path)
    try:
        run_id = engine.create('fixture', case='ashare', research_config=config(
            calls_per_architecture=6, only_architecture='baseline', frozen_candidate=None))
        complete(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert observed[0][0]['score_expression'] == 'pct_change(close, 60)'
        assert run['steps']['prepare']['initial_strategy'] == observed[0][0]
        with zipfile.ZipFile(tmp_path / run_id / 'starting_evidence_execution.zip') as archive:
            assert set(archive.namelist()) == {'daily.csv', 'trades.csv', 'target_weights.csv'}
    finally:
        engine.close()


def test_candidate_first_pause_restart_reuses_paid_response_and_releases_market_cache(tmp_path, fake_case):
    gateway = PrivateTraceGateway(blocked=True)
    engine = Engine(tmp_path, gateway)
    try:
        run_id = engine.create(case='ashare', research_config=config(research_order=['candidate', 'baseline']))
        assert gateway.entered.wait(5)
        engine.control(run_id, 'pause')
        gateway.release.set()
        complete(engine)
        assert engine.get(run_id)['status'] == 'paused'
        assert len(gateway.prompts) == 1
        assert engine.case_instances == {}
        engine.close()
        engine = Engine(tmp_path, gateway)
        engine.control(run_id, 'resume')
        complete(engine)
        run = engine.get(run_id)
        assert run['status'] == 'completed', run.get('last_error')
        assert len(gateway.prompts) == len(run['calls']) == 24
        assert all(call['attempt'] == 1 for call in run['calls'])
        assert engine.case_instances == {}
    finally:
        gateway.release.set()
        engine.close()


def test_sequential_runs_release_only_their_market_cache(tmp_path, fake_case):
    engine = Engine(tmp_path)
    sentinel = object()
    engine.case_instances['unrelated_sentinel'] = sentinel
    try:
        for _ in range(2):
            run_id = engine.create('fixture', case='ashare', research_config=config(
                calls_per_architecture=6, only_architecture='baseline', frozen_candidate=None))
            complete(engine)
            assert engine.get(run_id)['status'] == 'completed'
            assert engine.case_instances == {'unrelated_sentinel': sentinel}
    finally:
        engine.close()


@pytest.mark.parametrize('research', [
    [], 'bad', {'calls_per_architecture': True}, {'calls_per_architecture': 5},
    {'calls_per_architecture': 19}, {'calls_per_architecture': 12.0},
    {'research_order': ['baseline', 'baseline']}, {'research_order': ['candidate', 'baseline']},
    {'evaluation_split': 'final'}, {'evaluation_split': []}, {'model': 'other'},
    {'only_architecture': 'other'}, {'only_architecture': 'candidate'},
    {'frozen_candidate': 'text'}, {'frozen_candidate': {'name': 'incomplete'}},
    {'frozen_candidate': {**FROZEN, 'research_instructions': []}},
    {'frozen_candidate': {**FROZEN, 'research_instructions': ' '}},
    {'frozen_candidate': {**FROZEN, 'model': 'other'}},
    {'frozen_candidate': {**FROZEN, 'budget': {}}},
])
def test_invalid_research_configuration_does_not_start_or_create_run(tmp_path, fake_case, research):
    gateway = Gateway()
    engine = Engine(tmp_path, gateway)
    try:
        with pytest.raises(ValueError):
            engine.create(case='ashare', research_config=research)
        assert engine.store.runs() == []
        assert engine.worker is None and not gateway.prompts
    finally:
        engine.close()


def test_active_idempotent_create_returns_same_run_without_model_duplication(tmp_path, fake_case):
    gateway = PrivateTraceGateway(blocked=True)
    engine = Engine(tmp_path, gateway)
    research = config(calls_per_architecture=6, only_architecture='baseline', frozen_candidate=None)
    try:
        run_id = engine.create(case='ashare', research_config=research, request_key='batch.task1.rep1.baseline')
        assert gateway.entered.wait(5)
        retry = engine.create(case='ashare', research_config=dict(reversed(list(research.items()))),
                              request_key='batch.task1.rep1.baseline')
        assert retry == run_id
        assert len(engine.store.runs()) == 1 and len(gateway.prompts) == 1
        with pytest.raises(ValueError, match='different creation request'):
            engine.create(case='ashare', research_config={**research, 'calls_per_architecture': 12},
                          request_key='batch.task1.rep1.baseline')
        gateway.release.set()
        complete(engine)
        assert len(gateway.prompts) == 6
    finally:
        gateway.release.set()
        engine.close()


def test_idempotent_create_never_implicitly_starts_a_queued_run(tmp_path, fake_case):
    engine = Engine(tmp_path)
    try:
        run_id = engine.create('fixture', case='ashare', start=False, request_key='queued')
        assert engine.create('fixture', case='ashare', start=True, request_key='queued') == run_id
        assert engine.worker is None and engine.get(run_id)['status'] == 'queued'
    finally:
        engine.close()


@pytest.mark.parametrize('key', ['', '../unsafe', 'with space', 'a' * 161, True, 123])
def test_invalid_request_key_is_rejected_before_run_creation(tmp_path, fake_case, key):
    engine = Engine(tmp_path)
    try:
        with pytest.raises(ValueError, match='request_key'):
            engine.create(case='ashare', request_key=key)
        assert engine.store.runs() == [] and engine.worker is None
    finally:
        engine.close()


def test_market_exposure_registry_is_shared_across_task_ids(tmp_path, fake_case, monkeypatch):
    module = sys.modules['quanta_agents.meta.ashare_case']
    class FamilyCase(fake_case):
        def __init__(self, config=None):
            self.task = config['task']
        def manifest(self):
            return {'case_id': self.task, 'evaluation_family_id': 'same_market', 'data_hash': 'constant'}
    monkeypatch.setattr(module, 'AShareCase', FamilyCase)
    engine = Engine(tmp_path)
    try:
        ids = []
        for task in ['repair', 'continuation']:
            ids.append(engine.create('fixture', case='ashare', case_config={'task': task},
                       research_config=config(calls_per_architecture=6, only_architecture='baseline',
                                              frozen_candidate=None, evaluation_split='confirmation')))
            complete(engine)
        run = engine.get(ids[-1])
        assert run['status'] == 'completed', run.get('last_error')
        assert run['confirmation_exposure']['case_key'] == 'same_market'
        assert run['confirmation_exposure']['previously_opened'] is True
        assert run['confirmation_exposure']['prior_runs'][0]['run_id'] == ids[0]
    finally:
        engine.close()
