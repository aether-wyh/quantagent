"""Final LF transport repair: generated receipts plus an immutable real failure."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from quanta_agents.meta_v3 import extension_handoff
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import Ledger, digest
from quanta_agents.meta_v3.report_arguments import decode
from quanta_agents.meta_v3.runtime import ResearchRuntime, action_schema, source_pins
from test_meta_v3_research_entry import fixture
from test_meta_v4_controller import contracts

POLICY = {'version': 'report_lf_escape_v1'}
REAL_FOLDER = ROOT / 'experiment_traces/v4c1/controller_extensions/ap_009_56ec0f958ff1/stage/calls/extension_010_d3395f3bba3a'


def response(text, action='submit_research_report'):
    return {'action': action, 'arguments_json': text}


@pytest.mark.parametrize('text', ['{"key":1,"key":2}', '[1,2]', 'null'])
def test_legacy_decoder_preserves_plain_json_loads_semantics(text):
    assert decode(response(text)) == (json.loads(text), None)


def test_legacy_decoder_preserves_plain_json_loads_nonfinite_behavior():
    args, proof = decode(response('{"value":NaN}'))
    assert math.isnan(args['value']) and proof is None


@pytest.mark.parametrize('text', ['{"key":1,"key":2}', '{"value":NaN}', '[1,2]'])
def test_legacy_runtime_keeps_its_original_strict_object_requirement(tmp_path, text):
    runtime = new_runtime(tmp_path, report_policy=None)
    with pytest.raises(ValueError):
        runtime._decoded_arguments(response(text))


def test_legacy_child_binding_keeps_plain_json_loads_duplicate_behavior(tmp_path, monkeypatch):
    # Binding-only generated fixture: it grants no real ledger submission.
    raw = response('{"conclusion":"first","conclusion":"last"}')
    receipt = {'response': raw, 'engineering_fixture': True}
    report = {'legal_submission': True, 'model_report': json.loads(raw['arguments_json'])}
    call = {'task_id': 'extension', 'status': 'applied', 'receipt': receipt, 'result': report}
    folder = tmp_path / 'calls' / 'generated_final'
    folder.mkdir(parents=True)
    (folder / 'application.json').write_text(json.dumps({
        'failed': False, 'model_response_hash': digest(raw), 'result': report}), encoding='utf-8')
    child = SimpleNamespace(root=tmp_path, call=lambda _: call)
    monkeypatch.setattr(extension_handoff, '_verify_saved_call', lambda *_: receipt)
    bound = extension_handoff._child_report(child, {'provenance': {}},
        {'terminal': 'submitted', 'final_call': 'generated_final'})
    assert bound['public_result']['model_report'] == {'conclusion': 'last'}


def test_actual_saved_failure_has_exactly_25_lossless_lf_changes():
    path = REAL_FOLDER / 'response.json'
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    original = json.loads(path.read_text(encoding='utf-8'))
    args, proof = decode(original, POLICY)
    assert args == json.loads(original['arguments_json'], strict=False)
    assert proof['changed_count'] == 25
    assert proof['normalized_characters'] - proof['original_characters'] == 25
    assert all(original['arguments_json'][i] == '\n' for i in proof['changed_character_indices'])
    assert args['outcome'] == 'abstain' and len(args['evidence_ids']) == 9 and len(args['claims']) == 12
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with pytest.raises(json.JSONDecodeError, match='Invalid control character'):
        decode(original)


def test_quotes_backslashes_and_valid_escaped_controls_preserve_text():
    value = {'conclusion': 'quoted "x" and backslash \\\nnext line\tvalid escaped tab', 'path': 'a\\b'}
    text = json.dumps(value, ensure_ascii=False).replace('\\n', '\n')
    decoded, proof = decode(response(text), POLICY)
    assert decoded == value and proof['changed_count'] == 1
    strict, strict_proof = decode(response(json.dumps(value)), POLICY)
    assert strict == value and strict_proof['mode'] == 'strict_json'
    assert strict_proof['original_text_sha256'] == strict_proof['normalized_text_sha256']


@pytest.mark.parametrize('text', [
    '{"x":"first\nsecond","x":2}',
    '{"x":"first\nsecond","nested":{"key":1,"key":2}}',
    '{"x":"first\nsecond","v":NaN}',
    '{"x":"first\nsecond","v":Infinity}',
    '{"x":"first\nsecond","v":1e999}',
    '{"x":"first\nsecond',
    '{"x":"first\nsecond",}',
    '{"x":"first\nsecond\tbad"}',
    '{"x":"first\nsecond\rbad"}',
    '{"x":"first\nsecond\x00bad"}',
    '{"x":"backslash\\\nline"}',
])
def test_other_json_errors_are_not_repaired(text):
    with pytest.raises(ValueError):
        decode(response(text), POLICY)


@pytest.mark.parametrize('action', ['inspect_inputs', 'develop_strategy', 'request_research_extension'])
def test_every_nonfinal_action_stays_strict(action):
    with pytest.raises(json.JSONDecodeError):
        decode(response('{"text":"one\ntwo"}', action), POLICY)
    assert decode(response('{"text":"one\\ntwo"}', action), POLICY)[1] is None


def new_runtime(tmp_path, *, report_policy=POLICY, controller=True, other_provenance=None):
    case = fixture.prepare(tmp_path / 'case', flat=True)
    case['report_policy'] = {'version': 'claim_support_v1'}
    task = {'case': case, 'case_hash': digest(case), 'idea': 'Generated final delivery fixture', 'documents': []}
    provenance = {'source_pins': source_pins(), 'fixture_only': True}
    if controller:
        provenance['controller_policy'] = contracts(['extension'])
    if report_policy is not None:
        provenance['report_argument_policy'] = report_policy
    provenance.update(other_provenance or {})
    ledger = Ledger.create(tmp_path / 'stage', policy=ClosingPolicy(task_calls=2, stage_calls=2),
        tasks={'extension': task}, deadline_epoch=time.time() + 7200, provenance=provenance)
    return ResearchRuntime(ledger.root)


def receive_final(runtime, *, invalid_domain=False):
    case = runtime.plan['tasks']['extension']['case']
    input_id = 'input:' + digest(case)
    report = {'outcome': 'abstain', 'conclusion': 'Generated first line\nGenerated second line',
        'evidence_ids': [input_id], 'program_evidence_id': None, 'limitations': ['Engineering fixture'],
        'next_step': 'Inspect real evidence', 'falsifiers': ['An original differs'],
        'claims': [{'claim_id': 'scope', 'kind': 'descriptive', 'evidence_id': input_id,
            'research_class': case['research_class'], 'text': 'Generated fixture only'}]}
    if invalid_domain:
        report['evidence_ids'] = ['foreign_evidence']
    tools = runtime._tools('extension')
    intent = runtime.ledger.reserve('extension', tools.menu(), lambda menu, *_: ('Generated fixture', action_schema(menu)))
    raw = {**response(json.dumps(report).replace('\\n', '\n')), 'public_summary': 'Generated fixture, no provider call',
        'self_review': dict.fromkeys(('assessment', 'uncertainty', 'next_step', 'falsifier'), 'Generated fixture')}
    receipt = {'response': raw, 'usage': {'input_tokens': 1, 'output_tokens': 1},
        'request_identity': {'intent_id': intent['intent_id']}, 'artifact_sha256': {},
        'model_verified': True, 'engineering_fixture': True}
    runtime.ledger.receive_saved(intent['intent_id'], lambda *_a, **_k: receipt)
    return intent['intent_id'], report, receipt


@pytest.mark.parametrize('enabled, expected', [(False, 'invalid_final'), (True, 'submitted')])
def test_actual_runtime_entry_is_opt_in_and_preserves_model_response(tmp_path, enabled, expected):
    runtime = new_runtime(tmp_path, report_policy=POLICY if enabled else None)
    cid, report, receipt = receive_final(runtime)
    original = deepcopy(receipt['response'])
    runtime._apply(cid)
    call = runtime.ledger.call(cid)
    assert runtime.ledger.status('extension')['terminal'] == expected
    assert call['receipt']['response'] == original
    saved = json.loads((runtime.root / 'calls' / cid / 'application.json').read_text(encoding='utf-8'))
    if enabled:
        assert saved['argument_decoding']['changed_count'] == 1
        assert call['result']['model_report'] == report and call['result']['legal_submission'] is True
    else:
        assert 'argument_decoding' not in saved and saved['failed'] is True


def test_repaired_transport_still_rejects_foreign_final_evidence(tmp_path):
    runtime = new_runtime(tmp_path)
    cid, _, _ = receive_final(runtime, invalid_domain=True)
    runtime._apply(cid)
    saved = json.loads((runtime.root / 'calls' / cid / 'application.json').read_text(encoding='utf-8'))
    assert saved['argument_decoding']['changed_count'] == 1
    assert saved['failed'] is True and 'foreign or unknown final evidence' in saved['result']['error']
    assert runtime.ledger.status('extension')['terminal'] == 'invalid_final'


@pytest.mark.parametrize('tamper', [False, True])
def test_saved_application_replay_uses_same_decoder_and_verifies_proof(tmp_path, monkeypatch, tamper):
    runtime = new_runtime(tmp_path)
    cid, report, _ = receive_final(runtime)
    finish = runtime.ledger.finish_apply
    monkeypatch.setattr(runtime.ledger, 'finish_apply', lambda *_a, **_k: (_ for _ in ()).throw(OSError('generated interruption')))
    with pytest.raises(OSError, match='generated interruption'):
        runtime._apply(cid)
    assert runtime.ledger.call(cid)['status'] == 'applying'
    path = runtime.root / 'calls' / cid / 'application.json'
    if tamper:
        saved = json.loads(path.read_text(encoding='utf-8'))
        saved['argument_decoding']['normalized_text_sha256'] = '0' * 64
        path.write_text(json.dumps(saved), encoding='utf-8')
    monkeypatch.setattr(runtime.ledger, 'finish_apply', finish)
    if tamper:
        with pytest.raises(ValueError, match='argument decoding proof drift'):
            runtime._apply(cid)
    else:
        runtime._apply(cid)
        assert runtime.ledger.call(cid)['result']['model_report'] == report
        assert runtime.ledger.status('extension')['terminal'] == 'submitted'


def test_child_report_binding_uses_original_response_and_decoding_proof(tmp_path, monkeypatch):
    runtime = new_runtime(tmp_path)
    cid, report, receipt = receive_final(runtime)
    runtime._apply(cid)
    monkeypatch.setattr(extension_handoff, '_verify_saved_call', lambda *_: receipt)
    state = runtime.ledger.status('extension')
    result = extension_handoff._child_report(runtime.ledger, runtime.plan, state)
    assert result['public_result']['model_report'] == report and result['child_call_id'] == cid
    path = runtime.root / 'calls' / cid / 'application.json'
    saved = json.loads(path.read_text(encoding='utf-8'))
    saved['argument_decoding']['changed_character_indices'] = []
    path.write_text(json.dumps(saved), encoding='utf-8')
    with pytest.raises(ValueError, match='argument decoding proof drift'):
        extension_handoff._child_report(runtime.ledger, runtime.plan, state)


@pytest.mark.parametrize('policy, controller, other, message', [
    ({'version': 'unknown'}, True, None, 'unknown report argument policy'),
    ({'version': 'report_lf_escape_v1', 'allow_tabs': True}, True, None, 'unknown report argument policy'),
    (POLICY, False, None, 'requires a V4 controller'),
    (None, True, {'extension_context_policy': {'version': 'unknown'}}, 'context policy'),
    (None, False, {'extension_context_policy': {'version': 'parent_programs_v1'}}, 'requires a V4 controller'),
])
def test_runtime_preflight_validates_frozen_report_and_context_flags(tmp_path, policy, controller, other, message):
    runtime = new_runtime(tmp_path, report_policy=policy, controller=controller, other_provenance=other)
    with pytest.raises(ValueError, match=message):
        runtime.verify_inputs(global_only=True)
