"""Report-policy integration with actual generated accounting and final entry."""
import time

import pytest

from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import Ledger, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime, source_pins
from test_meta_v3_research_entry import fixture, action, program


@pytest.mark.parametrize('positive_claim, expected', [(False, 'supported'), (True, 'contradicted')])
def test_final_checks_actual_account_and_does_not_promote_prose(tmp_path, positive_claim, expected):
    case = fixture.prepare(tmp_path / 'case', flat=True)
    case['report_policy'] = {'version': 'claim_support_v1'}
    case['research_policy'] = {'version': 'structural_research_v1', 'action_limits': {'diagnose_execution': 1}}
    task = {'idea': 'Check whether costs can be recovered.', 'documents': [], 'case': case, 'case_hash': digest(case)}
    ledger = Ledger.create(tmp_path / 'stage', policy=ClosingPolicy(task_calls=4, stage_calls=4),
        tasks={'test': task}, deadline_epoch=time.time() + 7200, provenance={'source_pins': source_pins()})
    runtime = ResearchRuntime(ledger.root)
    contract = runtime._tools('test').contract()
    assert contract['actions']['submit_research_report']['arguments']['claims']['version'] == 'claim_support_v1'
    account = action(runtime, task, 'develop_strategy', {'program': program()})
    assert account['status'] == 'applied'
    diagnosis = action(runtime, task, 'diagnose_execution', {'evidence_ids': [account['id']]})
    assert diagnosis['status'] == 'applied'
    report = {'outcome': 'abstain', 'conclusion': 'Review the cost-bearing generated account.',
        'evidence_ids': [account['id'], diagnosis['id']], 'program_evidence_id': None,
        'limitations': ['Synthetic engineering evidence'], 'next_step': 'Obtain admissible market evidence',
        'falsifiers': ['Independent arithmetic differs'],
        'claims': [{'claim_id': 'net', 'kind': 'numeric', 'evidence_id': diagnosis['id'],
            'path': ['accounts', 0, 'return_on_full_initial_cash'],
            'relation': 'gt' if positive_claim else 'lt', 'value': '0', 'unit': 'percent',
            'research_class': 'synthetic_calibration'}]}
    final = action(runtime, task, 'submit_research_report', report)
    assert final['status'] == 'applied', final
    result = final['result']
    assert result['claim_support']['claims'][0]['status'] == expected
    assert result['legal_submission'] is True
    assert result['substantive_report_accepted'] is None
    assert result['claim_support']['general_report_truth_verified'] is False
    assert result['formal_target_success'] is False


def test_final_checks_saved_whole_input_coverage_at_its_actual_row_position(tmp_path):
    case = fixture.prepare(tmp_path / 'case', flat=True)
    case['report_policy'] = {'version': 'claim_support_v1'}
    task = {'idea': 'Inspect input coverage only.', 'documents': [], 'case': case, 'case_hash': digest(case)}
    ledger = Ledger.create(tmp_path / 'stage', policy=ClosingPolicy(task_calls=2, stage_calls=2),
        tasks={'test': task}, deadline_epoch=time.time() + 7200, provenance={'source_pins': source_pins()})
    runtime = ResearchRuntime(ledger.root)
    inputs = action(runtime, task, 'inspect_inputs', {'table': 'coverage', 'offset': 0, 'limit': 32})
    assert inputs['status'] == 'applied'
    rows = inputs['result']['public']['rows']
    index = next(i for i, row in enumerate(rows) if row.get('kind') == 'whole_input_scope')
    assert index != 0  # Field and obligation rows have different semantics.
    report = {'outcome': 'abstain', 'conclusion': 'The supplied input scope remains an engineering fixture.',
        'evidence_ids': [inputs['id']], 'program_evidence_id': None,
        'limitations': ['No market or strategy validation'], 'next_step': 'Obtain admissible market inputs',
        'falsifiers': ['The saved coverage differs from the supplied case'],
        'claims': [{'claim_id': metric, 'kind': 'numeric', 'evidence_id': inputs['id'],
            'path': ['rows', index, metric], 'relation': 'eq', 'value': str(value), 'unit': unit,
            'research_class': 'synthetic_calibration'} for metric, value, unit in (
                ('sessions', len(case['decision_fixture']['calendar']), 'count'),
                ('initial_cash', case['initial_cash'], 'CNY'))]}
    final = action(runtime, task, 'submit_research_report', report)
    assert final['status'] == 'applied'
    assert [row['status'] for row in final['result']['claim_support']['claims']] == ['supported', 'supported']
    assert final['result']['substantive_report_accepted'] is None
    assert final['result']['formal_target_success'] is False
