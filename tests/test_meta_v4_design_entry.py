"""Warning-only design review through the real saved-tool entry; no model calls."""
import json

import pytest

from quanta_agents.meta_v3.experiment_design import VERSION
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3.source_admission import preflight_case
from test_meta_v3_research_iteration import configured, execute, program


@pytest.mark.parametrize('enabled', [False, True])
def test_design_warning_is_opt_in_and_does_not_reject_registration(tmp_path, enabled):
    case = configured()
    if enabled:
        case['experiment_design_policy'] = {'version': VERSION}
    before = digest(case)
    tools = ResearchTools(tmp_path, 'unit', case, [])
    registration_contract = tools.contract()['actions']['register_experiment']
    assert ('design_review' in registration_contract) is enabled
    execute(tools, 'baseline', 'develop_strategy', {'program': program()})
    execute(tools, 'diagnosis', 'diagnose_execution', {'evidence_ids': ['baseline']})
    revision = program()
    revision['target_weight_expression'] = '0'
    declaration = {'baseline_evidence_id': 'baseline', 'diagnosis_evidence_id': 'diagnosis',
        'mechanism_hypotheses': ['Trading-cost explanation'],
        'distinguishing_prediction': 'Engineering contradiction: delta cannot be positive and nonpositive.',
        'structural_change': 'Freeze the cash-only control', 'revision_program': revision,
        'success_rule': 'Keep the original full capital and calendar', 'failure_rule': 'Any trade',
        'contrast_checks': [
            {'id': 'positive', 'hypothesis_index': 0, 'metric': 'net_pnl', 'operator': 'gt', 'threshold': '0'},
            {'id': 'nonpositive', 'hypothesis_index': 0, 'metric': 'net_pnl', 'operator': 'lte', 'threshold': '0'}]}
    result = execute(tools, 'registered', 'register_experiment', declaration)
    saved = json.loads((tools.folder / 'registered' / 'artifact.json').read_text(encoding='utf-8'))
    assert digest(saved) == result['artifact_hash']
    assert saved['declaration'] == declaration
    assert saved['executed'] is False and saved['success_not_evaluated'] is True
    assert ('design_review' in saved) is enabled
    assert digest(case) == before and len(tools.history) == 3
    if enabled:
        review = saved['design_review']
        assert review['status'] == 'evaluated_with_warnings'
        assert any(row['code'] == 'contradictory_numeric_conditions' for row in review['issues'])
        assert review['warning_only'] is True
        assert review['design_acceptance_decision'] == 'not_made'
        assert review['causal_mechanism_identified'] is False
    # A warning consumes the normal registration opportunity; it grants no extra slot.
    assert sum(row['response']['action'] == 'register_experiment' for row in tools.history) == 1


@pytest.mark.parametrize('policy', [None, {'version': 'unknown'}, {'version': VERSION, 'required': True}])
def test_unknown_design_policy_fails_before_tool_setup(tmp_path, policy):
    case = configured()
    case['experiment_design_policy'] = policy
    for operation in (lambda: preflight_case(case), lambda: ResearchTools(tmp_path, 'unit', case, [])):
        with pytest.raises(ValueError, match='unknown frozen experiment design policy'):
            operation()
    assert not (tmp_path / 'tools').exists()
