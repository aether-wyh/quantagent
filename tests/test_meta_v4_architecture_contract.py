"""Architecture behavior and pre-dispatch binding, with generated receipts only."""
from copy import deepcopy
from dataclasses import asdict
import json
from types import SimpleNamespace
import time

import pytest

from quanta_agents.meta_v3 import architecture_contract as ac, study_registry as sr
from quanta_agents.meta_v3.closing import ClosingPolicy, ClosingDecision
from quanta_agents.meta_v3.ledger import Ledger, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime, source_pins
from test_meta_v3_research_entry import fixture
from test_meta_v4_controller import contracts, scripted_gateway
from test_meta_v4_working_evidence import row


@pytest.mark.parametrize('name', ac.NAMES)
def test_canonical_contract_describes_real_behavior_and_fixed_is_not_runnable(name):
    contract = ac.make(name)
    assert ac.validate(contract) == contract
    status = ac.describe(contract)
    assert status['runtime_entry_integrated'] == (name != 'fixed_template_search')
    assert status['full_stack_comparison_admitted'] is False
    assert len({digest(ac.make(n)) for n in ac.NAMES}) == 3


@pytest.mark.parametrize('field,value', [
    ('prompt_assistance', []), ('entrypoint', 'invented_runner'),
    ('research_model', {'model': 'gpt-6-astra', 'effort': 'low'}),
    ('tool_authority', 'external_tools'), ('unknown_flag', True)])
def test_contract_cannot_keep_name_while_changing_behavior(field, value):
    contract = ac.make('v4_evidence_workflow')
    contract[field] = value
    with pytest.raises(ValueError, match='behavior contract drift'):
        ac.validate(contract)


@pytest.mark.parametrize('name,controller,model,message', [
    ('v4_evidence_workflow', False, 'gpt-6-astra', 'scoped runtime'),
    ('strong_single', True, 'different', 'model or effort'),
    ('fixed_template_search', True, 'gpt-6-astra', 'not integrated')])
def test_contract_enforces_actual_runtime_entry(name, controller, model, message):
    provenance = {'architecture_contract': ac.make(name)}
    if controller:
        provenance['controller_policy'] = contracts(['test'])
    with pytest.raises(ValueError, match=message):
        ac.validate_runtime(provenance, model=model)


def parts(tmp_path, name='v4_evidence_workflow'):
    case = fixture.prepare(tmp_path / 'case', flat=True)
    tasks = {'test': {'idea': 'Evaluate the same generated input.', 'documents': [],
                      'case': case, 'case_hash': digest(case)}}
    policy = ClosingPolicy(task_calls=3, stage_calls=3, stage_tokens=600000)
    provenance = {'source_pins': source_pins(), 'controller_policy': contracts(tasks)}
    if name is not None:
        provenance['architecture_contract'] = ac.make(name)
    return tasks, policy, provenance


def registered(tmp_path, monkeypatch, name='v4_evidence_workflow'):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path / 'canonical.sqlite3')
    tasks, policy, provenance = parts(tmp_path, name)
    contract = provenance['architecture_contract']
    trial = {'id': 'one', 'root': str((tmp_path / 'stage').resolve()),
        'case_hash': tasks['test']['case_hash'], 'architecture_hash': digest(contract),
        'architecture_contract': contract, 'repeat': 1, 'tasks_hash': digest(tasks),
        'source_pins_hash': digest(provenance['source_pins']), 'policy': asdict(policy),
        'duration_seconds': 7200}
    plan = {'study_id': 'generated_architecture', 'trials': [trial]}
    return tasks, policy, provenance, plan


def create(parts):
    tasks, policy, provenance, study = parts
    return sr.create_stage(study['trials'][0]['root'], study['study_id'], 'one',
        policy=policy, tasks=tasks, duration_seconds=7200, provenance=provenance)


def test_freeze_rejects_unbound_label_hash_before_registering(tmp_path, monkeypatch):
    items = registered(tmp_path, monkeypatch)
    items[-1]['trials'][0]['architecture_hash'] = 'f' * 64
    with pytest.raises(ValueError, match='hash does not bind'):
        sr.freeze(items[-1])
    assert not sr.REGISTRY.exists()


@pytest.mark.parametrize('change', ['missing', 'different', 'fixed'])
def test_create_refuses_changed_architecture_before_consuming_trial(tmp_path, monkeypatch, change):
    items = registered(tmp_path, monkeypatch,
        name='fixed_template_search' if change == 'fixed' else 'v4_evidence_workflow')
    sr.freeze(items[-1])
    if change == 'missing':
        items[2].pop('architecture_contract')
    elif change == 'different':
        items[2]['architecture_contract'] = ac.make('strong_single')
    with pytest.raises(ValueError, match='architecture contract|not integrated'):
        create(items)
    assert sr.snapshot('generated_architecture')['trials'][0]['claimed_at'] is None


def test_saved_stage_verification_detects_architecture_swap(tmp_path, monkeypatch):
    items = registered(tmp_path, monkeypatch)
    sr.freeze(items[-1])
    ledger = create(items)
    saved = json.loads((ledger.root / 'plan.json').read_text(encoding='utf-8'))
    sr.verify_stage(ledger.root, saved)
    saved['provenance']['architecture_contract'] = ac.make('strong_single')
    with pytest.raises(ValueError, match='architecture contract missing or changed'):
        sr.verify_stage(ledger.root, saved)


def test_same_input_tools_and_history_differ_only_in_v4_assistance():
    history = [row(status='failed')]
    history[0]['response']['arguments_json'] = '{}'
    history[0]['response']['self_review'] = {
        'padding': 'x' * 5500, 'assessment': 'Preserve this middle failure.',
        'uncertainty': 'y' * 5500, 'next_step': 'Read the original evidence.'}
    original = deepcopy(history)
    task = {'idea': 'Same question', 'documents': []}
    policy = asdict(ClosingPolicy())
    budget = {'task_calls_used': 1, 'stage_calls_used': 1, 'task_exposure': 20,
        'stage_exposure': 20, 'deadline_epoch': 10000, 'now_epoch': 0}
    tools = SimpleNamespace(contract=lambda: {'generated': True, 'read_evidence': 'available'})
    menu = ('read_evidence', 'submit_research_report')
    prompts = {}
    for name in ('v4_evidence_workflow', 'strong_single', None):
        runtime = ResearchRuntime.__new__(ResearchRuntime)
        runtime.controller_policy = contracts(['test'])
        provenance = {'controller_policy': runtime.controller_policy}
        if name is not None:
            provenance['architecture_contract'] = ac.make(name)
        runtime.plan = {'tasks': {'test': task}, 'policy': policy, 'provenance': provenance}
        text, schema = runtime._scoped_prompt('test', tools, history, menu, budget,
            ClosingDecision('explore', ()), None)
        prompts[name] = json.loads(text), schema
    v4, schema = prompts['v4_evidence_workflow']
    single, single_schema = prompts['strong_single']
    assert prompts[None] == prompts['v4_evidence_workflow']
    assert 'work_contract' in v4 and v4['working_evidence_index']['rows']
    assert {k: v for k, v in v4.items() if k not in ('work_contract', 'working_evidence_index')} == single
    assert single_schema == schema and single['allowed_actions'] == list(menu)
    assert history == original and single['own_complete_action_history'][0]['status'] == 'failed'


@pytest.mark.parametrize('name', ['v4_evidence_workflow', 'strong_single'])
def test_actual_dispatch_uses_bound_assistance_and_shared_tool_final_checks(tmp_path, monkeypatch, name):
    tasks, policy, provenance = parts(tmp_path, name)
    ledger = Ledger.create(tmp_path / 'stage', tasks=tasks, policy=policy,
        deadline_epoch=time.time() + 7200, provenance=provenance)
    runtime = ResearchRuntime(ledger.root)
    called = scripted_gateway(runtime, monkeypatch, verbose=True)
    status = runtime.run()
    assert called == ['test', 'test']
    assert status['tasks']['test']['terminal'] == 'submitted'
    history = ledger.history('test')
    final = history[-1]
    assert final['result']['legal_submission'] is True
    assert final['result']['formal_target_success'] is False
    intent = ledger.call(final['id'])['intent']
    prompt = json.loads(intent['prompt'])
    assert ('work_contract' in prompt) == (name == 'v4_evidence_workflow')
    assert ('working_evidence_index' in prompt) == (name == 'v4_evidence_workflow')
    assert prompt['own_complete_action_history'][0]['id'] == history[0]['id']
    assert 'read_evidence' in prompt['public_tool_contract']['actions']
