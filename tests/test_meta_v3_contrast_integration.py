"""Public registration and saved-result attachment; generated records, zero execution."""
from copy import deepcopy
from decimal import Decimal
import json
import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3 import research_batch
from test_meta_v3_batch_research import configured,execute
from test_meta_v3_research_entry import program
from test_meta_v3_revision_preregistration import saved


def account(p,calendar,capital,pnl,fees):
    """Hand-authored internally reconcilable two-trade example, not kernel output."""
    initial=Decimal(capital);loss=Decimal(pnl);cost=Decimal(fees);cash=initial-1000-cost/2
    exit_price=(1000+loss+cost)/10
    days=[]
    for i,day in enumerate(calendar):
        price=Decimal(100)+(exit_price-100)*i/(len(calendar)-1)
        final=i==len(calendar)-1;available=initial+loss if final else cash
        nav=available if final else cash+10*price
        days.append({'date':day,'simulated_net_asset_value':str(nav),'cash_available':str(available),'gross_asset_value':str(nav)})
    trades=[{'date':calendar[0],'symbol':'generated','side':'buy','quantity':10,'raw_price':'100','fees':{'total':str(cost/2)},'slippage_amount':'0'},
            {'date':calendar[-1],'symbol':'generated','side':'sell','quantity':10,'raw_price':str(exit_price),'fees':{'total':str(cost/2)},'slippage_amount':'0'}]
    return {'fixture_only':True,'fixture_note':'Generated saved-account arithmetic only; not an executed strategy',
        'program':deepcopy(p),'raw':{'status':'completed_mechanical','result':{'initial_cash':str(initial),'daily':days,'trades':trades,
            'final_snapshot':{'cash':str(initial+loss),'external_cash_flow':str(initial),'fees_paid':str(cost),'lots':{},'actions':{},'pending_orders':{}}}}}


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('unexpected account process'))
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    base=program();base['target_weight_expression']='0.4'
    revision=program();revision['target_weight_expression']='0.2'
    calendar=tools.case['decision_fixture']['calendar'];capital=tools.case['initial_cash']
    baseline=account(base,calendar,capital,'-1000','100')
    saved(tools,'baseline','develop_strategy',baseline)
    saved(tools,'diagnosis','diagnose_execution',{'input_evidence_ids':['baseline']})
    args={'baseline_evidence_id':'baseline','diagnosis_evidence_id':'diagnosis',
        'mechanism_hypotheses':['Lower fees','Different exposure'],
        'distinguishing_prediction':'Fee saving and final funded PnL have separate observable contrasts',
        'structural_change':'Generated prospective program identity; no executed strategy claim',
        'revision_program':revision,'success_rule':'Inspect all observed and contradicted predictions',
        'failure_rule':'Incomplete evidence or no distinguishing pattern remains unresolved',
        'contrast_checks':[{'id':'fees_down','hypothesis_index':0,'metric':'fees_on_recorded_trades','operator':'lte','threshold':'-50'},
            {'id':'pnl_up','hypothesis_index':1,'metric':'net_pnl','operator':'gt','threshold':'100'}]}
    return tools,args,account(revision,calendar,capital,'-600','150')


def test_public_frozen_check_reaches_result_and_ignores_later_caller_threshold_change(setup):
    tools,args,revision=setup
    public=tools.contract()['actions']['register_experiment']
    assert 'contrast_checks' in public['arguments'] and 'net_pnl' in public['contrast_metric_units']
    execute(tools,'registration','register_experiment',args)
    original=json.loads((tools.folder/'registration/artifact.json').read_text(encoding='utf-8'))
    args['contrast_checks'][0]['threshold']='100'
    tools._attach_experiment(revision,{'experiment_evidence_id':'registration'})
    result=revision['experiment']['public']['declared_check_results']
    assert result==revision['experiment']['declared_check_results']
    assert result['checks'][0]['threshold']=='-50' and result['checks'][0]['status']=='contradicted'
    assert result['checks'][1]['revision_minus_baseline']=='400.00' and result['checks'][1]['status']=='matched'
    assert result['registration_hash']==digest(original) and result['frozen_initial_cash']==tools.case['initial_cash']
    assert result['causal_mechanism_identified'] is False
    (tools.root/'generated_attachment.json').write_text(json.dumps(revision,ensure_ascii=True,indent=2),encoding='utf-8')


def test_legacy_registration_keeps_its_existing_unscored_comparison(setup):
    tools,args,revision=setup;args.pop('contrast_checks')
    execute(tools,'legacy','register_experiment',args)
    tools._attach_experiment(revision,{'experiment_evidence_id':'legacy'})
    assert 'declared_check_results' not in revision['experiment']
    assert 'Model must judge' in revision['experiment']['public']['criterion_judgment']


def test_invalid_contrast_cannot_be_saved_as_a_registration(setup):
    tools,args,_=setup;args['contrast_checks'][0]['threshold']=0
    with pytest.raises(AdmissionBlocked,match='bounded decimal string'):
        execute(tools,'bad_check','register_experiment',args)
    assert not (tools.folder/'bad_check/artifact.json').exists()


def test_partial_revision_keeps_unknown_final_values_in_attached_checks(setup):
    tools,args,revision=setup;execute(tools,'registration','register_experiment',args)
    body=revision['raw'].pop('result');body['daily']=body['daily'][:2]
    revision['raw'].update(status='failed',partial=body,error='Explicit generated interruption')
    tools._attach_experiment(revision,{'experiment_evidence_id':'registration'})
    result=revision['experiment']['declared_check_results']
    assert result['counts']=={'matched':0,'contradicted':0,'unevaluable':2}
    assert revision['experiment']['attribution']['accounts'][1]['final_nav'] is None
