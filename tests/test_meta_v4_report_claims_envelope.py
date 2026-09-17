"""Preserve actual malformed report content without changing old deliveries."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from quanta_agents.meta_v3.claim_support import contract, review_claims
from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.report_arguments import decode, STRUCTURED_VERSION
from test_meta_v4_report_arguments import new_runtime, response

POLICY = {'version': STRUCTURED_VERSION}


@pytest.mark.parametrize('trial', ['s2', 'v2'])
def test_saved_real_wrapper_is_lossless_and_old_failure_is_preserved(trial):
    root = ROOT / 'experiment_traces/v4s1' / trial
    state = json.loads((root / 'status.json').read_text(encoding='utf-8'))['tasks']['research']
    assert state['terminal'] == 'invalid_final'
    folder = root / 'calls' / state['calls'][-1]['id']
    paths = [folder / 'response.json', root / 'ledger.sqlite3', folder / 'application.json']
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    original = json.loads(paths[0].read_text(encoding='utf-8'))
    source = json.loads(original['arguments_json'])
    assert type(source['claims']) is dict
    assert set(source['claims']) == ({'claims', 'version'} if trial == 's2' else {'claims'})
    decoded, proof = decode(original, POLICY)
    assert decoded == {**source, 'claims': source['claims']['claims']}
    assert proof['claims_envelope_normalization']['claim_items_modified'] is False
    assert decode(original, {'version': 'report_lf_escape_v1'})[0] == source
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths] == before


@pytest.mark.parametrize('claims', [
    {'claims': []}, {'claims': [1] * 17}, {'claims': {'claims': [1]}},
    {'claims': [1], 'version': 'unrecognized'}, {'items': [1]},
    {'claims': [1], 'version': 'claim_support_v1', 'accepted': True},
])
def test_unknown_or_empty_wrappers_are_not_repaired(claims):
    with pytest.raises(ValueError, match='unsupported claims envelope'):
        decode(response(json.dumps({'claims': claims})), POLICY)


def test_nonfinal_actions_do_not_receive_domain_shape_repair():
    value = {'claims': {'claims': [1]}}
    decoded, proof = decode(response(json.dumps(value), 'register_batch'), POLICY)
    assert decoded == value and proof is None


def test_wrapper_does_not_bypass_claim_validation_or_certify_prose():
    claim = {'claim_id': 'scope', 'kind': 'descriptive', 'evidence_id': 'input',
        'research_class': 'synthetic_calibration', 'text': 'A generated fixture'}
    decoded, _ = decode(response(json.dumps({'claims': {'claims': [claim]}})), POLICY)
    result = review_claims(decoded['claims'], {'input': {'action': 'frozen_input', 'public': {}}},
        research_class='synthetic_calibration')
    assert result['claims'][0]['status'] == 'needs_review'
    assert result['formal_target_success'] is False
    assert result['general_report_truth_verified'] is False
    invalid = review_claims([1], {}, research_class='synthetic_calibration')
    assert invalid['claims'][0]['status'] == 'invalid'
    assert invalid['evidence_support_accepted'] is False


def test_new_runtime_applies_shape_repair_before_unchanged_final_validation(tmp_path):
    runtime = new_runtime(tmp_path, report_policy=POLICY)
    case = runtime.plan['tasks']['extension']['case']
    from quanta_agents.meta_v3.ledger import digest
    eid = 'input:' + digest(case)
    claim = {'claim_id': 'scope', 'kind': 'descriptive', 'evidence_id': eid,
        'research_class': case['research_class'], 'text': 'Generated fixture only'}
    report = {'outcome': 'abstain', 'program_evidence_id': None, 'evidence_ids': [eid],
        'conclusion': 'Generated bound report', 'claims': {'claims': [claim]},
        'limitations': ['No research execution'], 'falsifiers': ['Source differs'],
        'next_step': 'Inspect evidence'}
    decoded, proof = runtime._decoded_arguments(response(json.dumps(report)))
    result = runtime._tools('extension').final(decoded)
    assert result['legal_submission'] and result['model_report']['claims'] == [claim]
    assert result['formal_target_success'] is False
    foreign = deepcopy(decoded); foreign['evidence_ids'] = ['foreign']
    with pytest.raises(ValueError, match='foreign or unknown'):
        runtime._tools('extension').final(foreign)


def test_contract_declares_array_shape_without_a_second_claims_container():
    shape = contract()
    assert shape['type'] == 'array' and shape['min_items'] == 1 and shape['max_items'] == 16
    assert 'claims' not in shape
