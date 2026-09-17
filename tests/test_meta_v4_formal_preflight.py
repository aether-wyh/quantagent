"""Metadata only: adversarial denominator and policy changes, never market data."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from quanta_agents.meta_v3.formal_preflight import (
    current_proposal,evaluate,digest,GRANT_FIELDS,FUNDED_FIELDS,DEPENDENCIES)


def generated_metadata(real=6,control=False):
    cases=[]
    for n in range(real):
        cases.append({'key':f'case{n}','scientific_case_id':f'real{n}',
            'definition_hash':digest({'independent_definition':n}),'role':'real_research',
            'family':f'family{n%3}','exposure_class':'unreviewed_definition',
            'input_binding':dict.fromkeys(('task_sha256','initial_strategy_sha256','manifest_sha256',
                'calendar_sha256','membership_sha256','data_snapshot_id','split'),'a'*64)})
    if control:
        cases.append(dict(deepcopy(cases[0]),key='control',scientific_case_id='control',
            definition_hash=digest('control'),role='negative_control',family='control'))
    return {'cases':cases,'implementation_pins':{'generated_only.py':'b'*64},
        'periods':{'final':{'start':'2024-01-01','end':'2025-12-31'}},
        'market_identity_scope':'generated metadata only', 'market_manifest_summary':{},
        'legacy_execution_scope':{'scope':'generated_unverified'}}


def gates(result):return {g['id']:g for g in result['gates']}


def test_five_real_plus_negative_control_never_makes_six_real_or_54_formal():
    metadata=generated_metadata(5,True);proposal=current_proposal(metadata)
    result=evaluate(metadata,proposal);g=gates(result)
    assert len(result['candidate_mapping'])==54
    assert g['real_case_denominator']['observed']['distinct_real_cases']==5
    assert g['three_architectures_three_original_starts']['observed']['real_case_slots']==45
    assert g['real_case_denominator']['status']==g['three_architectures_three_original_starts']['status']=='incomplete'


@pytest.mark.parametrize('duplicate',['scientific_id','content','start'])
def test_renamed_case_or_repeated_start_does_not_restore_independence(duplicate):
    metadata=generated_metadata()
    if duplicate=='scientific_id':metadata['cases'][-1]['scientific_case_id']=metadata['cases'][0]['scientific_case_id']
    if duplicate=='content':metadata['cases'][-1]['definition_hash']=metadata['cases'][0]['definition_hash']
    proposal=current_proposal(metadata)
    if duplicate=='start':proposal['slots'][-1]=dict(proposal['slots'][0],id='renamed_extra_start')
    g=gates(evaluate(metadata,proposal))
    assert g['three_architectures_three_original_starts' if duplicate=='start' else 'real_case_denominator']['status']=='incomplete'


@pytest.mark.parametrize('field,value',[('net_sharpe_operator','gte'),('net_sharpe_threshold','0.9'),
    ('initial_capital_cny','100000'),('capital_basis','invested_cash_only'),
    ('minimum_real_oos_sessions',244),('risk_free_annual','0')])
def test_original_financial_gate_cannot_be_loosened(field,value):
    metadata=generated_metadata();proposal=current_proposal(metadata)
    proposal['financial_policy'][field]=value
    assert gates(evaluate(metadata,proposal))['financial_policy_preserved']['status']=='incomplete'


def test_calendar_mismatch_and_omitted_common_date_dependence_are_separate_failures():
    metadata=generated_metadata();proposal=current_proposal(metadata)
    proposal['slots'][0]['input_binding']['calendar_sha256']='c'*64
    proposal['statistical_design']={'one_sided_alpha':'0.05','dependence_units':DEPENDENCIES[:-1],
        'date_block_length':20,'block_length_sensitivity':[10,40],
        'resampling':'synchronized_date_blocks_and_case_clusters','case_weighting':'frozen family weights',
        'multiple_comparison_rule':'generated only','failure_score_rule':'all original starts',
        'analysis_implementation_hash':'f'*64}
    g=gates(evaluate(metadata,proposal))
    assert g['common_data_and_inputs']['status']=='incomplete'
    assert g['dependence_aware_statistical_design']['status']=='incomplete'


def test_architecture_labels_unequal_grants_or_arm_block_order_are_not_fair():
    metadata=generated_metadata();proposal=current_proposal(metadata)
    for slot in proposal['slots']:
        slot['grant']=dict.fromkeys(GRANT_FIELDS,100)
        slot['grant'].update(closing_calls=1,closing_tokens=1,closing_seconds=1)
    proposal['slots'][0]['grant']['candidates']=101
    proposal['architectures']['strong_single']['prompt_assistance']=['work_contract']
    proposal['execution_order']=[s['id'] for s in sorted(proposal['slots'],key=lambda s:s['architecture'])]
    g=gates(evaluate(metadata,proposal))
    assert g['common_full_stack_grants']['status']=='incomplete'
    assert g['actual_architecture_contracts']['status']=='incomplete'
    assert g['paired_original_order']['status']=='incomplete'


def test_self_certified_flags_never_clear_exposure_execution_or_future_gates():
    metadata=generated_metadata();proposal=current_proposal(metadata)
    proposal.update(formal_accepted=True,exposure_verified=True,execution_verified=True,
        final_sealed=True,prospective_verified=True)
    result=evaluate(metadata,proposal);g=gates(result)
    assert all(g[name]['status']=='incomplete' for name in ('heldout_exposure_review',
        'metadata_source_scope','execution_evidence.executable_capacity','one_time_frozen_evaluator_release','prospective_observed_evidence'))
    assert result['formal_success_denominator_contribution']==0
    assert result['new_registered_slots']==result['new_research_calls']==result['sealed_value_reads']==0


@pytest.mark.parametrize('funding',['missing','insufficient','full'])
def test_equal_trial_grants_require_a_separate_complete_whole_study_allocation(funding):
    metadata=generated_metadata();proposal=current_proposal(metadata)
    for slot in proposal['slots']:
        slot['grant']=dict.fromkeys(GRANT_FIELDS,100)
        slot['grant'].update(closing_calls=1,closing_tokens=1,closing_seconds=1)
    if funding!='missing':
        proposal['whole_study_allocation']={'ceilings':dict.fromkeys(FUNDED_FIELDS,5400),
            'headroom':dict.fromkeys(FUNDED_FIELDS,0),'grant_transfer':'forbidden'}
        if funding=='insufficient':proposal['whole_study_allocation']['ceilings']['process_io_bytes']-=1
    result=evaluate(metadata,proposal)
    assert gates(result)['common_full_stack_grants']['status']==('ready' if funding=='full' else 'incomplete')
    assert not result['formal_financial_accepted'] and result['new_registered_slots']==0


def test_six_distinct_definitions_can_pass_structural_gates_without_financial_acceptance():
    metadata=generated_metadata();proposal=current_proposal(metadata)
    g=gates(evaluate(metadata,proposal))
    assert all(g[name]['status']=='ready' for name in ('real_case_denominator','mechanism_families',
        'three_architectures_three_original_starts','common_data_and_inputs','financial_policy_preserved'))
    assert g['prospective_predeclared_design']['observed']['new_fixed_minimum_duration'] is None
    assert g['one_time_frozen_evaluator_release']['status']=='incomplete'


def test_cli_rejects_sealed_value_path_before_read(monkeypatch):
    path=Path(__file__).resolve().parents[1]/'scripts/formal_preflight.py'
    spec=importlib.util.spec_from_file_location('formal_preflight_cli',path)
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    def forbidden(*args):pytest.fail('No candidate or market file may be read')
    monkeypatch.setattr(Path,'read_bytes',forbidden)
    with pytest.raises(ValueError,match='candidate_'):
        cli.proposal_path('D:/qlib_data/parquet_cn_a_qfq_tradeable_v2_2015_2025/sh600004.parquet')
