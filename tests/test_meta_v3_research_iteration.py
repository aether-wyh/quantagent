"""Research opportunities, saved accounting attribution and frozen revisions."""
from copy import deepcopy
import json,time

import pytest

from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest,Ledger
from quanta_agents.meta_v3.research_iteration import account_attribution
from test_meta_v3_l2_research_entry import case,program


def configured():
    c=case();c['research_policy']={'version':'structural_research_v1','action_limits':{
        'develop_strategy':5,'diagnose_execution':2,'register_experiment':2,'request_research_extension':1,'read_evidence':6}}
    return c


def execute(tools,eid,action,args):
    result=tools.execute(eid,action,args)
    tools.history.append({'id':eid,'response':{'action':action,'arguments_json':json.dumps(args)},'result':result})
    return result


def test_attribution_and_registered_fourth_candidate_after_two_controls(tmp_path):
    tools=ResearchTools(tmp_path,'unit',configured(),[])
    execute(tools,'baseline','develop_strategy',{'program':program()})
    for eid,expr in [('all_cash','0'),('small','0.025')]:
        p=program();p['target_weight_expression']=expr
        execute(tools,eid,'develop_strategy',{'program':p})
    assert 'develop_strategy' in tools.menu()
    attribution=execute(tools,'diagnosis','diagnose_execution',{'evidence_ids':['baseline','all_cash','small']})
    account=attribution['public']['accounts'][0]
    assert account['net_pnl']=='22.42' and account['fees_on_recorded_trades']=='17.08'
    assert account['turnover_multiple_of_initial_cash']=='0.079977'
    assert account['saved_cash_days']==5 and account['all_cash_days']==3
    assert attribution['public']['pairs'][0]['comparison_minus_reference_net_pnl']=='-22.42'
    assert attribution['public']['causal_root_cause_identified'] is False
    revision=program();revision['target_weight_expression']='where(close > 1, 0.05, 0)'
    declaration={'baseline_evidence_id':'baseline','diagnosis_evidence_id':'diagnosis',
        'mechanism_hypotheses':['Extra exit splits increase minimum fees','Holding the extra day changes marked exposure'],
        'distinguishing_prediction':'Same total registered shares and cash dividend; one earlier exit has lower total minimum fees but different price exposure.',
        'structural_change':'Engineering exit structure only, no alpha claim','revision_program':revision,
        'success_rule':'Compare full-capital cash, fees and rights against frozen baseline, keeping price-exposure difference explicit.',
        'failure_rule':'Missing rights or extra capital invalidates the comparison.'}
    register=execute(tools,'preregister','register_experiment',declaration)
    assert not register['public']['executed']
    evaluated=execute(tools,'revision','develop_strategy',{'program':revision,'experiment_evidence_id':'preregister'})
    comparison=evaluated['public']['experiment']['comparison']
    assert comparison['pairs'][0]['same_cash_calendar_and_initial_capital']
    assert comparison['pairs'][0]['comparison_minus_reference_net_pnl']=='3.30'
    assert comparison['pairs'][0]['comparison_minus_reference_fees']=='-5.00'
    # The3.30 improvement differs from the5.00 fee saving. The tool must keep
    # the adverse1.70 price-path difference, not assert that fees explain all.
    assert not evaluated['formal_target_success']
    page=execute(tools,'month','read_evidence',{'evidence_id':'diagnosis','table':'attribution_monthly','offset':0,'limit':32})
    assert page['public']['returned_rows']==3 and page['public']['next_offset'] is None


def test_default_limit_unchanged_and_frozen_revision_cannot_be_rewritten(tmp_path):
    tools=ResearchTools(tmp_path/'legacy','unit',case(),[])
    tools.history=[{'id':str(i),'response':{'action':'develop_strategy'},'result':None} for i in range(3)]
    assert 'develop_strategy' not in tools.menu() and 'register_experiment' not in tools.menu()
    with pytest.raises(AdmissionBlocked,match='opportunity bound'):tools.execute('fourth','develop_strategy',{'program':program()})
    new=ResearchTools(tmp_path/'new','unit',configured(),[])
    execute(new,'b','develop_strategy',{'program':program()})
    execute(new,'d','diagnose_execution',{'evidence_ids':['b']})
    revision=program();revision['target_weight_expression']='0'
    execute(new,'r','register_experiment',{'baseline_evidence_id':'b','diagnosis_evidence_id':'d','mechanism_hypotheses':['Trading costs'],
        'distinguishing_prediction':'Cash-only path has no trades','structural_change':'No trading control','revision_program':revision,
        'success_rule':'Keep capital','failure_rule':'Any trade'})
    with pytest.raises(AdmissionBlocked,match='differs from preregistered'):new.execute('bad','develop_strategy',{'program':program(),'experiment_evidence_id':'r'})


def test_requesting_futures_does_not_grant_asset_semantics_or_budget(tmp_path):
    data=configured();tools=ResearchTools(tmp_path,'unit',data,[])
    execute(tools,'inputs','inspect_inputs',{'table':'coverage','offset':0,'limit':32})
    old=digest(data)
    result=execute(tools,'request','request_research_extension',{'evidence_ids':['inputs'],'problem':'Current asset class cannot test a futures trend explanation',
        'request_kind':'asset_class','specification':'Need real futures contracts,multipliers,margin,roll and settlement evidence',
        'expected_information_gain':'Separate trend exposure from stock-only selection effects',
        'requested_resource_bounds':{'symbols':4,'sessions':252,'model_calls':10,'download_bytes':10000000,'wall_seconds':3600}})
    assert result['public']['status']=='pending_controller_admission' and not result['public']['budget_granted']
    assert not result['public']['new_data_loaded'] and digest(data)==old
    assert 'request_research_extension' not in tools.menu()


def test_larger_action_allocation_does_not_spend_final_opportunity(tmp_path):
    from quanta_agents.meta_v3.closing import ClosingPolicy
    from quanta_agents.meta_v3.runtime import ResearchRuntime,source_pins,make_prompt,action_schema
    from test_meta_v3_research_entry import action
    data=configured();task={'case':data,'case_hash':digest(data),'idea':'Engineering only','documents':[]}
    ledger=Ledger.create(tmp_path/'runtime',policy=ClosingPolicy(task_calls=2,stage_calls=2),tasks={'test':task},
        deadline_epoch=time.time()+7200,provenance={'source_pins':source_pins(),'fixture_only':True})
    runtime=ResearchRuntime(ledger.root);action(runtime,task,'develop_strategy',{'program':program()})
    tools=runtime._tools('test');history=runtime._history('test')
    intent=runtime.ledger.reserve('test',tools.menu(),lambda menu,state,decision:
        (make_prompt(task,tools,history,menu,state,decision,runtime.plan['policy']),action_schema(menu)))
    assert intent['schema']['properties']['action']['enum']==['submit_research_report']
