"""Independent generated-only entry refusals; no account backend is executed."""
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from quanta_agents.meta_v3 import conditional_risk_derivation as derivation
from quanta_agents.meta_v3 import real_execution, saved_execution, target_schedule
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.research_tools import ResearchTools, save_once
from quanta_agents.meta_v3.runtime import verify_case_sources
from quanta_agents.meta_v3.source_admission import preflight_case
from test_meta_v4_conditional_risk_derivation import example


def entry_case(tmp_path, *, derived=True):
    base, bundle = example()
    base.update(description='Generated engineering entry check; no market or research evidence',
                raw_source_bindings={'source_artifacts': [], 'obligations': [], 'corporate_actions': []})
    if not derived:
        return base
    case = {**base, **derivation.build(base, bundle)}
    payload = b'Generated canary only; not market observations.'
    canary = tmp_path / 'generated_source_canary.txt'; canary.write_bytes(payload)
    case['evidence_sources'] = [{'path': str(canary), 'sha256': hashlib.sha256(payload).hexdigest()}]
    return case


def program():
    return {'version': 'factor_strategy_program_v1', 'factors': [],
        'target_weight_expression': derivation.FIELD, 'hypothesis': 'Generated entry verification',
        'applicability': ['Engineering only'], 'invalidation_conditions': ['Any claim of real evidence']}


def corrupt(case, kind):
    record = case[derivation.KEY]
    if kind == 'field_weight':
        next(r for r in case['decision_fixture']['field_rows'] if r['field'] == derivation.FIELD)['value'] = .7
    if kind == 'receipt_selection': record['anchor_receipts'][0]['measurement']['selected'].reverse()
    if kind == 'schedule_receipt': case[target_schedule.KEY]['anchor_inputs'][0]['input_receipt_sha256'] = '0' * 64
    if kind == 'bundle_value': record['bundle']['market_rows'][8]['value'] += .1
    if kind == 'source_claim': record['source_authenticated'] = True
    if kind == 'real_class': case['evidence_class'] = 'real_verified'
    if kind == 'sealed_case':
        case['decision_fixture']['calendar'] = ['2024' + day[4:] for day in case['decision_fixture']['calendar']]
    if kind == 'sealed_bundle':
        record['bundle']['original_calendar'] = ['2024' + day[4:] for day in record['bundle']['original_calendar']]
    if kind == 'drop_record': case.pop(derivation.KEY)
    if kind == 'drop_record_field_contract':
        case.pop(derivation.KEY)
        case['decision_fixture']['fields'] = [f for f in case['decision_fixture']['fields'] if f['name'] != derivation.FIELD]
    if kind == 'drop_schedule': case.pop(target_schedule.KEY)


@pytest.mark.parametrize('entry', ['runtime', 'research_tools', 'real_execution'])
@pytest.mark.parametrize('kind', ['field_weight','receipt_selection','schedule_receipt','bundle_value','source_claim',
    'real_class','sealed_case','sealed_bundle','drop_record','drop_record_field_contract','drop_schedule'])
def test_real_entry_refuses_bad_derivation_before_source_bytes_or_account_dispatch(tmp_path, monkeypatch, entry, kind):
    case = entry_case(tmp_path); corrupt(case, kind)
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('unverified entry opened source bytes'))
    monkeypatch.setattr(saved_execution, 'freeze_saved_research_plan', lambda **kw: pytest.fail('unverified entry reached account freeze'))
    monkeypatch.setattr(saved_execution.SavedRawResearch, 'create', lambda *a, **kw: pytest.fail('unverified entry reached account dispatch'))
    candidate = tmp_path / 'candidate'; candidate.mkdir()
    with pytest.raises(ValueError):
        if entry == 'runtime': verify_case_sources({'case': case, 'case_hash': digest(case)})
        elif entry == 'research_tools': ResearchTools(tmp_path / 'stage', 'generated', case, [])
        else: real_execution.develop(candidate, case, program(), save_once)
    assert not (candidate / 'workbench/raw_children').exists()
    if entry == 'research_tools': assert not (tmp_path / 'stage').exists()


def test_runtime_verifies_inline_derivation_before_reading_declared_source_canary(tmp_path, monkeypatch):
    case = entry_case(tmp_path); calls = []
    original_verify, original_read = derivation.verify_case, Path.read_bytes
    def verify(value):
        report = original_verify(value); calls.append('derived_verified')
        assert report['binding_verified'] is True and report['source_authenticated'] is False
        return report
    def read(path):
        assert calls and calls[-1] == 'derived_verified'
        calls.append('source_bytes')
        return original_read(path)
    monkeypatch.setattr(derivation, 'verify_case', verify)
    monkeypatch.setattr(Path, 'read_bytes', read)
    verify_case_sources({'case': case, 'case_hash': digest(case)})
    assert calls == ['derived_verified', 'source_bytes']


def test_public_contract_distinguishes_generated_selector_from_real_admission(tmp_path, monkeypatch):
    case = entry_case(tmp_path)
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('public contract opened source'))
    tools = ResearchTools(tmp_path / 'stage', 'generated', case, [])
    contract = tools.contract(); report = contract['conditional_risk_derivation']
    assert contract['evidence_class'] == 'generated_engineering'
    assert 'GENERATED ENGINEERING ONLY' in contract['limitations'][0]
    assert 'not an autonomous researcher selector' in report['scope']
    assert report['binding_verified'] is True
    for key in ('source_authenticated','source_arrival_verified','action_coverage_verified','real_research','formal_target_success'):
        assert report[key] is False
    assert contract['target_schedule']['input_receipt_authentication'] is False
    assert 'not a registered fair-study resource protocol' in contract['conditional_derivation_resource_scope']


def test_mutation_after_tool_initialization_is_not_hidden_by_cached_verification(tmp_path, monkeypatch):
    case = entry_case(tmp_path); tools = ResearchTools(tmp_path/'stage', 'generated', case, [])
    corrupt(case, 'field_weight')
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('changed public contract opened source'))
    with pytest.raises(ValueError): tools.contract()
    candidate = tmp_path / 'candidate'; candidate.mkdir()
    monkeypatch.setattr(saved_execution, 'freeze_saved_research_plan', lambda **kw: pytest.fail('cached verification dispatched account'))
    with pytest.raises(ValueError): real_execution.develop(candidate, case, program(), save_once)


def test_old_case_without_reserved_field_has_no_derived_contract_or_recomputation(tmp_path, monkeypatch):
    case = entry_case(tmp_path, derived=False)
    monkeypatch.setattr(derivation, 'evaluate_window', lambda *a, **kw: pytest.fail('ordinary case computed risk matrix'))
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('ordinary inline checks opened source'))
    preflight_case(case)
    verify_case_sources({'case': case, 'case_hash': digest(case)})
    contract = ResearchTools(tmp_path/'stage', 'generated', case, []).contract()
    assert derivation.verify_case(case) is None
    assert 'conditional_risk_derivation' not in contract
    assert 'conditional_derivation_resource_scope' not in contract
    assert 'target_schedule' not in contract


def test_metadata_refuses_nonengineering_class_before_numerical_recomputation(tmp_path, monkeypatch):
    case = entry_case(tmp_path); case['evidence_class'] = 'real_verified'
    monkeypatch.setattr(derivation, 'evaluate_window', lambda *a, **kw: pytest.fail('nonengineering metadata reached numerical work'))
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('nonengineering metadata opened source'))
    with pytest.raises(ValueError): preflight_case(case)
