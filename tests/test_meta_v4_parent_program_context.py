"""Generated receipts only: exact parent programs, immutable scope, no model calls."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from quanta_agents.meta_v3 import codex_session_gateway as capture
from quanta_agents.meta_v3 import research_extension as extension
from quanta_agents.meta_v3.closing import ClosingDecision, ClosingPolicy
from quanta_agents.meta_v3.ledger import AdmissionBlocked, Ledger, digest, serial
from quanta_agents.meta_v3.research_iteration import executable_program_hash
from quanta_agents.meta_v3.runtime import ResearchRuntime, action_schema, make_prompt, source_pins
from test_meta_v3_l2_research_entry import program
from test_meta_v3_research_iteration import configured
from test_meta_v4_controller import contracts


@pytest.fixture
def prepare(tmp_path, monkeypatch):
    def no_model(*args, **kwargs):
        pytest.fail('These counterexamples must never call a provider')
    monkeypatch.setattr(capture.CodexGateway, 'run', no_model)
    monkeypatch.setattr(capture.base.CodexGateway, 'run', no_model)
    receipts = {}
    verified = []
    def verifier(folder, **kwargs):
        verified.append(Path(folder).name)
        return receipts[Path(folder).name]
    monkeypatch.setattr(capture, 'verify_saved_completion', verifier)

    def create(*, opted_in=True):
        case = configured()
        case['report_policy'] = {'version': 'claim_support_v1'}
        case['experiment_design_policy'] = {'version': 'scalar_conjunction_design_review_v1'}
        task = {'case': case, 'case_hash': digest(case), 'idea': 'Generated context fidelity check', 'documents': []}
        provenance = {'source_pins': source_pins(), 'fixture_only': True,
                      'controller_policy': contracts(['test']), 'harness_version': '4.0.0-dev',
                      'runtime_identity_route': {'version': 'codex_session_v1'}}
        if opted_in:
            provenance.update(extension_context_policy={'version': 'parent_programs_v1'},
                              report_argument_policy={'version': 'report_lf_escape_v1'})
        parent = Ledger.create(tmp_path/'p', policy=ClosingPolicy(task_calls=6, stage_calls=6),
                               tasks={'test': task}, deadline_epoch=time.time()+7200, provenance=provenance)
        runtime = ResearchRuntime(parent.root)
        def action(name, args):
            intent = parent.reserve('test', runtime._tools('test').menu(),
                                    lambda menu, *a: ('Generated engineering prompt', action_schema(menu)))
            response = {'action': name, 'arguments_json': json.dumps(args),
                        'public_summary': 'Generated fixture; no provider response',
                        'self_review': dict.fromkeys(('assessment', 'uncertainty', 'next_step', 'falsifier'), 'Fixture')}
            receipt = {'response': response, 'usage': {'input_tokens': 10, 'output_tokens': 10},
                       'request_identity': {'intent_id': intent['intent_id']},
                       'artifact_sha256': {capture.SESSION: 'a'*64}, 'model_verified': False,
                       'runtime_identity': {'verified': True, 'level': 'generated_engineering_fixture'}}
            receipts[intent['intent_id']] = receipt
            parent.receive_saved(intent['intent_id'], lambda *a, **k: receipt)
            runtime._apply(intent['intent_id'])
            row = parent.history('test')[-1]
            assert row['status'] == 'applied', row
            return row['id']
        spec = program()
        spec['factors'] = [{'name': 'signal', 'expression': 'close > 1'}]
        spec['target_weight_expression'] = 'where(signal, 0.05, 0)'
        source_id = action('develop_strategy', {'program': spec})
        request_id = action('request_research_extension', {
            'evidence_ids': [source_id], 'problem': 'Keep the exact original program in a new-field contrast.',
            'request_kind': 'data', 'requested_fields': ['volume'],
            'specification': 'Add generated volume on the same symbols and sessions; preserve original definition.',
            'expected_information_gain': 'Separate the original definition from an extra field condition.',
            'requested_resource_bounds': {'symbols': 1, 'sessions': 5, 'model_calls': 4,
                                          'download_bytes': 0, 'wall_seconds': 7200}})
        child = deepcopy(case)
        child['decision_fixture']['fields'].append({'name': 'volume', 'unit': 'engineering shares'})
        added = deepcopy(child['decision_fixture']['field_rows'])
        for row in added:
            row.update(field='volume', value=100)
        child['decision_fixture']['field_rows'].extend(added)
        source = tmp_path/'source.json'
        source.write_text(serial(child), encoding='utf-8')
        child['evidence_sources'] = [{'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]
        decision = {'status': 'ready', 'reason': 'Generated volume exists; engineering fixture only.',
                    'asset_contract': 'a_share_cash_equity',
                    'resource_bounds': {'symbols': 1, 'sessions': 5, 'model_calls': 4,
                                        'download_bytes': 0, 'wall_seconds': 7200},
                    'exposure_statement': 'Generated sources, previously exposed parent evidence, no OOS.',
                    'source_admissions': [{'path': str(source), 'role': 'engineering',
                                           'partition': 'generated_fixture', 'content_date_range': None}]}
        return SimpleNamespace(parent=parent, source_id=source_id, request_id=request_id, program=spec,
                               receipts=receipts, verified=verified,
                               kwargs={'decision': decision, 'child_case': child,
                                       'policy': ClosingPolicy(task_calls=4, stage_calls=4, stage_tokens=600000),
                                       'deadline_epoch': time.time()+7000})
    return create


def test_complete_parent_program_reaches_child_prompt_and_preserves_scope(prepare):
    f = prepare()
    old_plan = (f.parent.root/'plan.json').read_bytes()
    old_history = f.parent.history('test')
    decision = extension.decide_extension(f.parent.root, 'test', f.request_id, **f.kwargs)
    runtime = ResearchRuntime(decision['child_root'])
    task = runtime.plan['tasks']['extension']
    tools = runtime._tools('extension')
    state = runtime.ledger.status('extension')['budget_state']
    prompt = json.loads(make_prompt(task, tools, [], tools.menu(), state,
                                   ClosingDecision('explore', ()), runtime.plan['policy']))
    row = prompt['documents'][-1]['parent_evidence'][0]
    bound = row['frozen_parent_program']
    assert bound['program'] == f.program
    assert bound['program_hash'] == digest(f.program)
    assert bound['executable_program_hash'] == executable_program_hash(f.program)
    assert bound['source_parent_call_id'] == row['parent_evidence_id'] == f.source_id
    assert bound['source_artifact_hash'] == row['artifact_hash']
    assert bound['source_response_hash'] == digest(f.receipts[f.source_id]['response'])
    assert bound['source_model_artifact_sha256'] == {capture.SESSION: 'a'*64}
    assert f.source_id in f.verified and f.request_id in f.verified
    assert 'not a child-local execution' in bound['interpretation']
    assert runtime.plan['provenance']['extension_context_policy'] == {'version': 'parent_programs_v1'}
    assert runtime.plan['provenance']['report_argument_policy'] == {'version': 'report_lf_escape_v1'}
    assert task['case'] == f.kwargs['child_case']
    assert runtime.ledger.history('extension') == []
    assert runtime.ledger.status('extension')['known_tokens'] == 0
    assert (f.parent.root/'plan.json').read_bytes() == old_plan and f.parent.history('test') == old_history


def test_coherently_rehashed_artifact_cannot_replace_original_model_program(prepare):
    f = prepare()
    path = f.parent.root/'tools/test'/f.source_id/'artifact.json'
    artifact = json.loads(path.read_text(encoding='utf-8'))
    artifact['program']['target_weight_expression'] = '0'
    path.write_text(serial(artifact), encoding='utf-8')
    result = f.parent.call(f.source_id)['result']
    result['artifact_hash'] = digest(artifact)
    with f.parent.transaction() as db:
        db.execute('UPDATE calls SET result=? WHERE id=?', (serial(result), f.source_id))
    with pytest.raises(AdmissionBlocked, match='parent program differs from bound model request'):
        extension.decide_extension(f.parent.root, 'test', f.request_id, **f.kwargs)
    assert not (f.parent.root/'controller_extensions').exists()


@pytest.mark.parametrize('invalid', ['unverified_identity', 'foreign_request'])
def test_each_cited_program_needs_its_own_verified_identity(prepare, invalid):
    f = prepare()
    if invalid == 'unverified_identity':
        f.receipts[f.source_id]['runtime_identity']['verified'] = False
        reason = 'runtime session identity unverified'
    else:
        f.receipts[f.source_id]['request_identity']['intent_id'] = f.request_id
        reason = 'model request identity mismatch'
    with pytest.raises(AdmissionBlocked, match=reason):
        extension.decide_extension(f.parent.root, 'test', f.request_id, **f.kwargs)
    assert not (f.parent.root/'controller_extensions').exists()


def test_full_program_context_overflow_blocks_instead_of_silent_truncation(prepare):
    f = prepare()
    # Preserve the authentic generated program, but leave only 500 bytes of
    # context room. Its hash/public view fits; its complete definition does not.
    row = f.parent.call(f.source_id)['result']
    row['public'] = {'fixture_padding': 'x'*63500}
    with f.parent.transaction() as db:
        db.execute('UPDATE calls SET result=? WHERE id=?', (serial(row), f.source_id))
    with pytest.raises(AdmissionBlocked, match='bounded explicit evidence pages'):
        extension.decide_extension(f.parent.root, 'test', f.request_id, **f.kwargs)
    assert not (f.parent.root/'controller_extensions').exists()


def test_legacy_scope_keeps_original_context_without_program_policy(prepare):
    f = prepare(opted_in=False)
    f.receipts[f.source_id]['runtime_identity']['verified'] = False
    decision = extension.decide_extension(f.parent.root, 'test', f.request_id, **f.kwargs)
    child = json.loads((Path(decision['child_root'])/'plan.json').read_text(encoding='utf-8'))
    row = child['tasks']['extension']['documents'][-1]['parent_evidence'][0]
    assert set(row) == {'parent_evidence_id', 'action', 'artifact_hash', 'public_result'}
    assert f.source_id not in f.verified
    assert 'extension_context_policy' not in child['provenance']
    assert 'report_argument_policy' not in child['provenance']


def test_unknown_context_policy_rejected():
    assert extension.validate_context_policy(None) is None
    assert extension.validate_context_policy({'version': 'parent_programs_v1'}) is None
    for value in ({'version': 'parent_programs_v2'}, {'version': 'parent_programs_v1', 'truncate': True}, []):
        with pytest.raises(AdmissionBlocked, match='unknown extension context policy'):
            extension.validate_context_policy(value)


@pytest.mark.parametrize('v4', [False, True])
def test_generic_creation_flags_only_new_v4_scopes(tmp_path, v4):
    script = Path(__file__).resolve().parents[1]/'scripts/run_research_v3.py'
    spec = spec_from_file_location('generic_research_entry_context_test', script)
    entry = module_from_spec(spec)
    spec.loader.exec_module(entry)
    controller = tmp_path/'controller.json'
    controller.write_text(serial(contracts(['test'])), encoding='utf-8')
    case = configured()
    task = {'case': case, 'case_hash': digest(case), 'idea': 'Generated no-call creation', 'documents': []}
    args = SimpleNamespace(controller_plan=str(controller) if v4 else None, identity_route=None,
                           study_id=None, root=tmp_path/'created', hours=2)
    original = {'source_pins': source_pins(), 'fixture_only': True}
    ledger = entry.create_stage(args, policy=ClosingPolicy(), tasks={'test': task}, provenance=original)
    plan = json.loads((ledger.root/'plan.json').read_text(encoding='utf-8'))
    assert ('extension_context_policy' in plan['provenance']) == v4
    assert ('report_argument_policy' in plan['provenance']) == v4
    if v4:
        assert plan['provenance']['extension_context_policy'] == {'version': 'parent_programs_v1'}
        assert plan['provenance']['report_argument_policy'] == {'version': 'report_lf_escape_v1'}
    assert ledger.history('test') == [] and 'extension_context_policy' not in original
