"""Generated receipt doubles test protocol mechanics, never supplier authenticity."""
import hashlib
import json
import time

import pytest

from quanta_agents.meta_v3 import generator_proposal as gp, generator_controls as gc, research_batch
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from quanta_agents.meta_v3.research_tools import save_once
from quanta_agents.meta_v3.runtime import ResearchRuntime, make_prompt, action_schema
from test_meta_v3_generator_controls import inputs, SEED
from test_meta_v3_batch_research import declaration


def setup(tmp_path):
    case, space = inputs(tmp_path, values=(.1, .2, .4, .8, 2))
    root = tmp_path/'prospective'
    gp.prepare(root, case, space, count=3, seed=SEED, idea='Generated proposal protocol only.', documents=[],
        policy=ClosingPolicy(task_calls=4, stage_calls=4, stage_tokens=600000), deadline_epoch=time.time()+7000)
    return root, ResearchRuntime(root/'model_stage')


def generated_call(rt, action, args, receipts, *, confirmed=True):
    task = rt.plan['tasks'][gp.TASK]; tools = rt._tools(gp.TASK); history = rt.ledger.history(gp.TASK)
    build = lambda menu, state, decision: (make_prompt(task, tools, history, menu, state, decision, rt.plan['policy']), action_schema(menu))
    intent = rt.ledger.reserve(gp.TASK, tools.menu(), build)
    response = {'action': action, 'arguments_json': json.dumps(args), 'public_summary': 'Generated test double only',
        'self_review': dict.fromkeys(('assessment','uncertainty','next_step','falsifier'), 'Generated protocol fixture')}
    module('meta.codex_gateway')._validate_output(response, intent['schema'])
    folder = rt.root/'calls'/intent['intent_id']
    save_once(folder/'generated_receipt_marker.json', {'generated_test_double_only': True})
    pin = hashlib.sha256((folder/'generated_receipt_marker.json').read_bytes()).hexdigest()
    receipt = {'response': response, 'usage': {'input_tokens': 10, 'output_tokens': 10}, 'request_identity': intent,
        'artifact_sha256': {'generated_receipt_marker.json': pin}, 'model': 'gpt-6-astra', 'effort': 'xhigh',
        'model_verified': confirmed, 'duration_seconds': 0,
        'identity_verification': {'level': 'GENERATED_TEST_DOUBLE_NOT_AUTHENTIC'}}
    receipts[intent['intent_id']] = receipt
    rt.ledger.receive_saved(intent['intent_id'], lambda *a, **k: receipt)
    rt._apply(intent['intent_id'])
    return intent


def generated_final(rt, receipts, eid, *, confirmed=True):
    return generated_call(rt, 'submit_research_report', {'outcome':'abstain', 'conclusion':'No funded outcome in proposal stage.',
        'evidence_ids':[eid], 'program_evidence_id':None, 'limitations':['Generated protocol fixture'],
        'next_step':'No performance assertion', 'falsifiers':['Actual evidence differs']}, receipts, confirmed=confirmed)


def mock_verifier(monkeypatch, receipts):
    monkeypatch.setattr(module('meta.codex_gateway'), 'verify_saved_completion', lambda folder, **kwargs: receipts[folder.name])


def test_proposal_menu_hides_execution_and_control_choices(tmp_path):
    root, rt = setup(tmp_path); menu = set(rt._tools(gp.TASK).menu())
    assert menu == gp.PHASE_ACTIONS
    plan, _, _ = gp.verify(root)
    assert plan['budget']['candidates_per_arm'] == 3 and plan['budget']['scan_cells_per_arm'] == 144
    receipts = {}; intent = generated_call(rt, 'register_batch', declaration((.2,)), receipts)
    assert SEED not in intent['prompt'] and 'domain_index' not in intent['prompt']
    assert not list((root/'controls').rglob('worker_result.json'))
    with pytest.raises(AdmissionBlocked, match='sealed before control'): gc.run_control(root/'controls', 'fixed')
    with pytest.raises(AdmissionBlocked, match='must finish'): gp.seal(root)


def test_fabricated_receipt_files_do_not_pass_actual_gateway_verifier(tmp_path):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'register_batch', declaration((.2,)), receipts)
    generated_final(rt, receipts, one['intent_id'])
    with pytest.raises(module('meta.codex_gateway').GatewayError, match='Missing saved completion'): gp.seal(root)
    assert not (root/'control_release.json').exists()


def test_sealed_slots_keep_domain_rejection_missing_and_all_call_costs(tmp_path, monkeypatch):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'register_batch', declaration((.2,.35)), receipts)
    generated_final(rt, receipts, one['intent_id'])
    mock_verifier(monkeypatch, receipts)
    result = gp.seal(root)
    assert [x['proposal_status'] for x in result['slots']] == ['inside_domain','outside_domain','not_proposed']
    assert result['known_tokens'] == 40 and result['call_count'] == 2
    assert all(x['reserved_scan_cells'] == 48 for x in result['slots'])
    assert result['full_stack_comparison_admitted'] is False
    assert gp.seal(root) == result
    run = gp.run_model(root)
    assert [x['status'] for x in run['candidates']] == ['completed','invalid','invalid']
    assert [x['proposal_status'] for x in run['candidates']] == ['inside_domain','outside_domain','not_proposed']
    assert run['reserved_candidates'] == 3 and run['reserved_scan_cells'] == 144
    assert run['candidates'][0]['account']['initial_cash'] == '1000000.00'
    monkeypatch.setattr(research_batch.subprocess, 'Popen', lambda *a, **k: pytest.fail('model account rerun'))
    assert gp.run_model(root, execute_new=False)['candidates'] == run['candidates']


def test_abstention_preserves_all_missing_slots_and_no_account_execution(tmp_path, monkeypatch):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'inspect_inputs', {'table':'fields','offset':0,'limit':32}, receipts)
    generated_final(rt, receipts, one['intent_id'])
    mock_verifier(monkeypatch, receipts); result = gp.seal(root)
    assert [x['proposal_status'] for x in result['slots']] == ['not_proposed']*3
    monkeypatch.setattr(research_batch.subprocess, 'Popen', lambda *a, **k: pytest.fail('missing proposal executed'))
    assert gp.run_model(root)['started_candidates'] == 0


def test_unconfirmed_provider_model_keeps_control_release_closed(tmp_path, monkeypatch):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'register_batch', declaration((.2,)), receipts, confirmed=False)
    generated_final(rt, receipts, one['intent_id'], confirmed=False)
    mock_verifier(monkeypatch, receipts); result = gp.seal(root)
    assert result['local_completion_verified'] and not result['provider_model_effort_confirmed']
    with pytest.raises(AdmissionBlocked, match='unverified model'): gc.run_control(root/'controls','fixed')
    assert not (root/'controls/arms').exists()


def test_proof_file_drift_after_seal_blocks_every_arm(tmp_path, monkeypatch):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'register_batch', declaration((.2,)), receipts)
    generated_final(rt, receipts, one['intent_id']); mock_verifier(monkeypatch, receipts)
    gp.seal(root)
    (rt.root/'calls'/one['intent_id']/'generated_receipt_marker.json').write_text('{}', encoding='utf-8')
    for arm in ('fixed','random','model'):
        with pytest.raises(AdmissionBlocked, match='proof drift'): gc.run_control(root/'controls',arm)


def test_any_prior_control_observation_refuses_prospective_seal(tmp_path, monkeypatch):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'register_batch', declaration((.2,)), receipts)
    generated_final(rt, receipts, one['intent_id']); mock_verifier(monkeypatch, receipts)
    (root/'controls/arms').mkdir()
    with pytest.raises(AdmissionBlocked, match='outcomes preceded'): gp.seal(root)
    assert not (root/'proposal_receipt.json').exists()


def test_unknown_model_call_does_not_get_replacement_or_release(tmp_path):
    root, rt = setup(tmp_path); task=rt.plan['tasks'][gp.TASK]; tools=rt._tools(gp.TASK)
    build=lambda menu,state,decision:(make_prompt(task,tools,[],menu,state,decision,rt.plan['policy']),action_schema(menu))
    intent=rt.ledger.reserve(gp.TASK,tools.menu(),build)
    rt.ledger.unknown(intent['intent_id'],'generated unknown; no actual dispatch')
    with pytest.raises(AdmissionBlocked, match='must finish'): gp.seal(root)
    with pytest.raises(AdmissionBlocked):rt.ledger.reserve(gp.TASK,tools.menu(),build)
    assert len(rt.ledger.status(gp.TASK)['calls'])==1
    assert rt.ledger.status(gp.TASK)['unknown_or_pending_reserve']==80000
