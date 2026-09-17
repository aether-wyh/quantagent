"""Independent report transport counterexamples; fixtures never call a model."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from quanta_agents.meta_v3 import extension_handoff
from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.report_arguments import decode, STRUCTURED_VERSION
from quanta_agents.meta_v3.runtime import action_schema
from test_meta_v3_research_entry import fixture
from test_meta_v4_controller import contracts
from test_meta_v4_report_arguments import new_runtime, response

POLICY = {'version': STRUCTURED_VERSION}


def _report(runtime, claims):
    case = runtime.plan['tasks']['extension']['case']
    return {'outcome': 'abstain', 'program_evidence_id': None,
        'evidence_ids': ['input:' + digest(case)], 'conclusion': 'Fixture "quoted" text\\path\nand LF',
        'claims': {'version': 'claim_support_v1', 'claims': claims},
        'limitations': ['Generated transport fixture'], 'falsifiers': ['Saved evidence differs'],
        'next_step': 'Independent review only'}


def _claim(runtime, cid='first'):
    case = runtime.plan['tasks']['extension']['case']
    return {'claim_id': cid, 'kind': 'descriptive', 'evidence_id': 'input:' + digest(case),
        'research_class': case['research_class'], 'text': 'Unverified generated prose'}


def _receive(runtime, report):
    tools = runtime._tools('extension')
    intent = runtime.ledger.reserve('extension', tools.menu(),
        lambda menu, *_: ('Generated independent test, no provider', action_schema(menu)))
    raw = {**response(json.dumps(report).replace('\\n', '\n')),
        'public_summary': 'Generated fixture',
        'self_review': dict.fromkeys(('assessment', 'uncertainty', 'next_step', 'falsifier'), 'Fixture')}
    receipt = {'response': raw, 'usage': {'input_tokens': 1, 'output_tokens': 1},
        'request_identity': {'intent_id': intent['intent_id']}, 'artifact_sha256': {},
        'model_verified': True, 'engineering_fixture': True}
    runtime.ledger.receive_saved(intent['intent_id'], lambda *_a, **_k: receipt)
    return intent['intent_id'], receipt


@pytest.mark.parametrize('version', [None, True, 1, ['claim_support_v1'], {'version': 'claim_support_v1'}])
def test_present_wrapper_version_requires_exact_supported_string(version):
    with pytest.raises(ValueError, match='unsupported claims envelope'):
        decode(response(json.dumps({'claims': {'version': version, 'claims': [1]}})), POLICY)


@pytest.mark.parametrize('versioned', [False, True])
def test_all_sixteen_items_and_order_preserved_without_extra_normalization(versioned):
    claims = [{'claim_id': str(index), 'nested': {'text': f'原文 {index} \\ " \n'}} for index in range(16)]
    wrapper = {'claims': claims, **({'version': 'claim_support_v1'} if versioned else {})}
    raw = response(json.dumps({'claims': wrapper, 'unrelated': {'claims': [17]}}))
    before = deepcopy(raw)
    args, proof = decode(raw, POLICY)
    assert args == {'claims': claims, 'unrelated': {'claims': [17]}}
    transform = proof['claims_envelope_normalization']
    assert transform['claim_count'] == 16 and transform['discarded_claims'] == transform['added_claims'] == 0
    assert transform['extracted_claims_sha256'] == digest(claims)
    assert proof['decoded_arguments_sha256'] == digest(args)
    assert raw == before


def test_nested_wrapper_items_and_duplicate_claims_survive_and_fail_original_claim_review(tmp_path):
    runtime = new_runtime(tmp_path, report_policy=POLICY)
    first = _claim(runtime)
    claims = [first, deepcopy(first), {'claims': [first]}, None]
    report = _report(runtime, claims)
    decoded, _ = runtime._decoded_arguments(response(json.dumps(report)))
    result = runtime._tools('extension').final(decoded)
    assert result['model_report']['claims'] == claims
    findings = result['claim_support']['claims']
    assert len(findings) == 4
    assert findings[1]['reason'] == 'duplicate_claim_id'
    assert [row['status'] for row in findings] == ['needs_review', 'invalid', 'invalid', 'invalid']
    assert result['claim_support']['evidence_support_accepted'] is False
    assert result['substantive_report_accepted'] is None and result['formal_target_success'] is False
    # A nested envelope in place of the array is not recursively extracted.
    with pytest.raises(ValueError, match='unsupported claims envelope'):
        decode(response(json.dumps({'claims': {'claims': {'claims': [first]}}})), POLICY)


@pytest.mark.parametrize('change', ['foreign_reference', 'extra_final_key'])
def test_extraction_does_not_relax_original_report_domain(tmp_path, change):
    runtime = new_runtime(tmp_path, report_policy=POLICY)
    report = _report(runtime, [_claim(runtime)])
    if change == 'foreign_reference':
        report['evidence_ids'] = ['foreign']
    else:
        report['already_accepted'] = True
    cid, receipt = _receive(runtime, report)
    runtime._apply(cid)
    assert runtime.ledger.status('extension')['terminal'] == 'invalid_final'
    assert runtime.ledger.call(cid)['receipt']['response'] == receipt['response']


@pytest.mark.parametrize('trial', ['v1', 's1'])
def test_original_saved_v1_success_application_proof_is_byte_for_byte_compatible(trial):
    root = ROOT / 'experiment_traces/v4s1' / trial
    plan = json.loads((root / 'plan.json').read_text(encoding='utf-8'))
    assert plan['provenance']['report_argument_policy'] == {'version': 'report_lf_escape_v1'}
    state = json.loads((root / 'status.json').read_text(encoding='utf-8'))['tasks']['research']
    folder = root / 'calls' / state['final_call']
    paths = [root / 'ledger.sqlite3', folder / 'response.json', folder / 'application.json']
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    raw = json.loads(paths[1].read_text(encoding='utf-8'))
    application = json.loads(paths[2].read_text(encoding='utf-8'))
    args, proof = decode(raw, plan['provenance']['report_argument_policy'])
    assert proof == application['argument_decoding']
    assert args == application['result']['model_report']
    assert 'claims_envelope_normalization' not in proof
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == original for p, original in before.items())


def test_v2_saved_replay_and_child_binding_require_the_exact_extraction_proof(tmp_path, monkeypatch):
    runtime = new_runtime(tmp_path, report_policy=POLICY)
    report = _report(runtime, [_claim(runtime, 'second'), _claim(runtime, 'first')])
    cid, receipt = _receive(runtime, report)
    finish = runtime.ledger.finish_apply
    monkeypatch.setattr(runtime.ledger, 'finish_apply', lambda *_a, **_k: (_ for _ in ()).throw(OSError('fixture interruption')))
    with pytest.raises(OSError, match='fixture interruption'):
        runtime._apply(cid)
    path = runtime.root / 'calls' / cid / 'application.json'
    original_application = path.read_bytes()
    saved = json.loads(original_application)
    assert saved['argument_decoding']['changed_count'] == 1
    assert saved['argument_decoding']['claims_envelope_normalization']['claim_count'] == 2
    monkeypatch.setattr(runtime.ledger, 'finish_apply', finish)
    corrupt = deepcopy(saved)
    corrupt['argument_decoding']['claims_envelope_normalization']['claim_count'] = 1
    path.write_text(json.dumps(corrupt), encoding='utf-8')
    with pytest.raises(ValueError, match='saved report argument decoding proof drift'):
        runtime._apply(cid)
    path.write_bytes(original_application)
    runtime._apply(cid)
    monkeypatch.setattr(extension_handoff, '_verify_saved_call', lambda *_: receipt)
    state = runtime.ledger.status('extension')
    bound = extension_handoff._child_report(runtime.ledger, runtime.plan, state)
    assert bound['public_result']['model_report']['claims'] == report['claims']['claims']
    assert bound['public_result']['substantive_report_accepted'] is None
    assert runtime.ledger.call(cid)['receipt']['response'] == receipt['response']
    corrupt['argument_decoding']['claims_envelope_normalization']['claim_count'] = 2
    corrupt['argument_decoding']['decoded_arguments_sha256'] = '0' * 64
    path.write_text(json.dumps(corrupt), encoding='utf-8')
    with pytest.raises(ValueError, match='child report argument decoding proof drift'):
        extension_handoff._child_report(runtime.ledger, runtime.plan, state)


@pytest.mark.parametrize('command', ['create', 'create-batch'])
def test_future_v4_cli_freezes_v2_policy_through_actual_creation(tmp_path, monkeypatch, capsys, command):
    spec = importlib.util.spec_from_file_location('independent_research_cli', ROOT / 'scripts/run_research_v3.py')
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    case = fixture.prepare(tmp_path / 'case', flat=True)
    case_path = tmp_path / 'case.json'
    case_path.write_text(json.dumps(case), encoding='utf-8')
    controller = tmp_path / 'controller.json'
    controller.write_text(json.dumps(contracts(['research_001'])), encoding='utf-8')
    stage = tmp_path / 'new_stage'
    argv = ['run_research_v4.py', command, '--root', str(stage), '--controller-plan', str(controller), '--calls', '2']
    if command == 'create':
        argv += ['--case', str(case_path), '--idea', 'Generated CLI fixture']
    else:
        manifest = tmp_path / 'manifest.json'
        manifest.write_text(json.dumps({'protocol': 'Generated fixture only', 'tasks': [
            {'id': 'research_001', 'case_path': str(case_path), 'idea': 'Generated CLI fixture'}]}), encoding='utf-8')
        argv += ['--manifest', str(manifest)]
    monkeypatch.setattr(sys, 'argv', argv)
    cli.main(require_v4=True)
    capsys.readouterr()
    plan = json.loads((stage / 'plan.json').read_text(encoding='utf-8'))
    assert plan['provenance']['report_argument_policy'] == POLICY
    assert plan['provenance']['extension_context_policy'] == {'version': 'parent_programs_v1'}
    assert plan['tasks']['research_001']['case']['report_policy'] == {'version': 'claim_support_v1'}
    assert not list((stage / 'calls').glob('*')) if (stage / 'calls').exists() else True
