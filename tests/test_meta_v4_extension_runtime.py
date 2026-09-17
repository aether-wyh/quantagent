"""Extension scheduling counterexamples: scripted gateway, real tools/ledger.

Every receipt and token number here is generated engineering evidence. No
model is called and no generated receipt proves a provider or model identity.
"""
import json
import time
from pathlib import Path

from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import Ledger, digest
from quanta_agents.meta_v3.research_extension import decide_extension
from quanta_agents.meta_v3.runtime import ResearchRuntime, source_pins
from test_meta_v3_research_entry import fixture
from test_meta_v4_controller import contracts


def _stage(tmp_path, *, sibling=False):
    ids = ['a_extension'] + (['b_independent'] if sibling else [])
    tasks = {}
    for task_id in ids:
        case = fixture.prepare(tmp_path / task_id, flat=True)
        case['research_policy'] = {'version': 'structural_research_v1',
            'action_limits': {'request_research_extension': 1}}
        tasks[task_id] = {'idea': 'Inspect whether the supplied scope can answer the question.',
            'documents': [], 'case': case, 'case_hash': digest(case)}
    ledger = Ledger.create(tmp_path / 'stage', tasks=tasks,
        policy=ClosingPolicy(task_calls=4, stage_calls=4 * len(tasks)),
        deadline_epoch=time.time() + 7200,
        provenance={'source_pins': source_pins(), 'controller_policy': contracts(tasks),
            'extension_handoff_policy': {'version': 'yield_to_controller_v1'},
            'fixture_only': True})
    return ResearchRuntime(ledger.root)


def _scripted_gateway(runtime, monkeypatch):
    receipts, prompts = {}, []
    monkeypatch.setattr(runtime, 'verify_identity_route', lambda: {
        'status': 'available', 'engineering_fixture': True,
        'provider_binding_verified': False})

    def run(self, *, prompt, schema, workdir, **kwargs):
        body = json.loads(prompt)
        intent = json.loads((Path(workdir) / 'intent.json').read_text(encoding='utf-8'))
        task_id = intent['task_id']
        prompts.append({'task_id': task_id, 'prompt': body})
        history = body['own_complete_action_history']
        if not history:
            action = 'inspect_inputs'
            args = {'table': 'coverage', 'offset': 0, 'limit': 32}
        elif task_id == 'a_extension' and len(history) == 1:
            action = 'request_research_extension'
            args = {'evidence_ids': [history[0]['id']],
                'problem': 'The generated input lacks the requested independent benchmark.',
                'request_kind': 'benchmark',
                'specification': 'An implemented independently sourced benchmark adapter.',
                'expected_information_gain': 'Separate a shared benchmark move from the candidate effect.',
                'requested_resource_bounds': {'symbols': 2, 'sessions': 12,
                    'model_calls': 2, 'download_bytes': 0, 'wall_seconds': 3600}}
        else:
            action = 'submit_research_report'
            args = {'outcome': 'abstain',
                'conclusion': 'The saved evidence cannot establish the proposed independent effect.',
                'evidence_ids': [history[0]['id']], 'program_evidence_id': None,
                'limitations': ['Scripted engineering input and no implemented benchmark.'],
                'next_step': 'Retain the source gap for a separately admitted implementation.',
                'falsifiers': ['An independently sourced benchmark becomes available.']}
        response = {'action': action, 'arguments_json': json.dumps(args),
            'public_summary': 'Scripted extension scheduling fixture, not model research.',
            'self_review': dict.fromkeys(('assessment', 'uncertainty', 'next_step', 'falsifier'),
                'Generated engineering fixture only.')}
        runtime.gateway_module._validate_output(response, schema)
        receipt = {'response': response, 'usage': {'input_tokens': 10, 'output_tokens': 10},
            'request_identity': {'intent_id': intent['intent_id']}, 'artifact_sha256': {},
            'model_verified': True, 'engineering_fixture': True}
        receipts[intent['intent_id']] = receipt
        (Path(workdir) / 'scripted_receipt.json').write_text(json.dumps(receipt), encoding='utf-8')

    monkeypatch.setattr(runtime.gateway_module.CodexGateway, 'run', run)
    monkeypatch.setattr(runtime.gateway_module, 'verify_saved_completion',
        lambda folder, **kwargs: receipts[Path(folder).name])
    return prompts


def test_applied_extension_yields_without_reserving_another_call(tmp_path, monkeypatch):
    runtime = _stage(tmp_path)
    prompts = _scripted_gateway(runtime, monkeypatch)
    state = runtime.run()
    assert [p['task_id'] for p in prompts] == ['a_extension', 'a_extension']
    assert state['work_schedule']['tasks']['a_extension']['status'] == 'waiting_for_extension_controller'
    history = runtime.ledger.history('a_extension')
    assert [row['response']['action'] for row in history] == ['inspect_inputs', 'request_research_extension']
    assert all(row['status'] == 'applied' for row in history)
    artifact = runtime.root / 'tools' / 'a_extension' / history[-1]['id'] / 'artifact.json'
    assert json.loads(artifact.read_text(encoding='utf-8'))['status'] == 'pending_controller_admission'
    state_again = runtime.run()
    assert len(prompts) == 2
    assert len(state_again['tasks']['a_extension']['calls']) == 2
    assert state_again['tasks']['a_extension']['unknown_or_pending_reserve'] == 0
    assert state_again['tasks']['a_extension']['terminal'] is None


def test_needs_implementation_decision_returns_to_model_with_followup(tmp_path, monkeypatch):
    runtime = _stage(tmp_path)
    prompts = _scripted_gateway(runtime, monkeypatch)
    runtime.run()
    request_id = runtime.ledger.history('a_extension')[-1]['id']
    reason = 'The requested benchmark adapter is not implemented; no child budget is granted.'
    decision = decide_extension(runtime.root, 'a_extension', request_id,
        decision={'status': 'needs_implementation', 'reason': reason,
            'asset_contract': 'a_share_cash_equity', 'resource_bounds': None,
            'exposure_statement': 'Generated engineering test; no independent market evidence.'})
    assert decision['child_budget_registered'] is False
    assert len(prompts) == 2
    state = runtime.run()
    assert len(prompts) == 3
    followup = prompts[-1]['prompt']['controller_extension_followup']
    assert followup['status'] == 'needs_implementation'
    assert followup['blocks_parent_dispatch'] is False
    assert followup['requests'][0]['request_id'] == request_id
    assert followup['requests'][0]['detail']['controller_reason'] == reason
    assert state['tasks']['a_extension']['terminal'] == 'submitted'
    assert runtime.ledger.history('a_extension')[-1]['result']['legal_submission'] is True
    assert state['tasks']['a_extension']['unknown_or_pending_reserve'] == 0


def test_extension_handoff_blocks_only_its_task(tmp_path, monkeypatch):
    runtime = _stage(tmp_path, sibling=True)
    prompts = _scripted_gateway(runtime, monkeypatch)
    state = runtime.run()
    assert [p['task_id'] for p in prompts] == [
        'a_extension', 'a_extension', 'b_independent', 'b_independent']
    assert state['work_schedule']['tasks']['a_extension']['status'] == 'waiting_for_extension_controller'
    assert state['tasks']['a_extension']['terminal'] is None
    assert state['tasks']['b_independent']['terminal'] == 'submitted'
    assert state['work_schedule']['stage_disposition'] == 'blocked_partial'
    assert len(runtime.ledger.history('a_extension')) == 2
    assert len(runtime.ledger.history('b_independent')) == 2
    assert all(row['unknown_or_pending_reserve'] == 0 for row in state['tasks'].values())
    runtime.run()
    assert len(prompts) == 4, 'A waiting request must not consume a retry or rerun its completed sibling.'
