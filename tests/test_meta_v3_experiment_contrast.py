"""Declared observation checks on generated saved evidence, never executed accounts."""
from copy import deepcopy
from decimal import Decimal
import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest
from quanta_agents.meta_v3 import experiment_contrast as ec

CALENDAR=['2018-01-02','2018-01-03','2018-01-04']


def evidence():
    checks=[{'id':'fees_fall','hypothesis_index':0,'metric':'fees_on_recorded_trades','operator':'lte','threshold':'-50'},
            {'id':'pnl_improves','hypothesis_index':1,'metric':'net_pnl','operator':'gt','threshold':'100'}]
    registration={'baseline_program_hash':'baseline_program','revision_program_hash':'revision_program',
        'declaration':{'baseline_evidence_id':'baseline','mechanism_hypotheses':['Lower trading fees','Different market exposure'],
            'contrast_checks':checks}}
    baseline={'evidence_id':'baseline','program_hash':'baseline_program','complete_account':True,'initial_cash':'1000000',
        'daily':[{'date':d} for d in CALENDAR],'net_pnl':'-1000','fees_on_recorded_trades':'100','recorded_slippage_in_prices':'20'}
    revision={**deepcopy(baseline),'evidence_id':'registered_revision','program_hash':'revision_program',
        'net_pnl':'-600','fees_on_recorded_trades':'150','recorded_slippage_in_prices':'30'}
    return registration,{'accounts':[baseline,revision]}


def test_more_pnl_with_more_fees_contradicts_fee_saving_not_causally_resolved():
    registration,attribution=evidence();result=ec.evaluate(registration,attribution,CALENDAR,'1000000')
    assert result['checks'][0]['revision_minus_baseline']=='50'
    assert result['checks'][0]['status']=='contradicted'
    assert result['checks'][1]['revision_minus_baseline']=='400'
    assert result['checks'][1]['status']=='matched'
    assert result['counts']=={'matched':1,'contradicted':1,'unevaluable':0}
    assert result['hypotheses'][0]['contradicted']==1 and result['hypotheses'][1]['matched']==1
    assert result['causal_mechanism_identified'] is False and result['formal_target_success'] is False
    assert result['checks_hash']==digest(registration['declaration']['contrast_checks'])


@pytest.mark.parametrize('fault',['incomplete','both_drop_session','reverse_session','less_capital','both_less_capital','wrong_program'])
def test_incomparable_accounts_do_not_pass_even_favorable_numeric_values(fault):
    registration,attribution=evidence();a,b=attribution['accounts']
    b['net_pnl']='999999';b['fees_on_recorded_trades']='0'
    if fault=='incomplete':b['complete_account']=False
    elif fault=='both_drop_session':
        a['daily'].pop(1);b['daily'].pop(1)
    elif fault=='reverse_session':b['daily'].reverse()
    elif fault=='less_capital':b['initial_cash']='500000'
    elif fault=='both_less_capital':a['initial_cash']=b['initial_cash']='500000'
    else:b['program_hash']='other_program'
    result=ec.evaluate(registration,attribution,CALENDAR,'1000000')
    assert result['counts']=={'matched':0,'contradicted':0,'unevaluable':2}
    assert all(c['revision_minus_baseline'] is None and c['reason'] for c in result['checks'])


def test_unknown_slippage_is_not_zero_while_other_complete_metric_remains_observable():
    registration,attribution=evidence()
    registration['declaration']['contrast_checks'][0].update(metric='recorded_slippage_in_prices',threshold='0')
    attribution['accounts'][1]['recorded_slippage_in_prices']=None
    result=ec.evaluate(registration,attribution,CALENDAR,'1000000')
    assert result['checks'][0]['status']=='unevaluable' and result['checks'][0]['revision_value'] is None
    assert result['checks'][1]['status']=='matched'


def test_decimal_difference_is_exact_and_never_changes_full_principal():
    registration,attribution=evidence();a,b=attribution['accounts']
    a['net_pnl']='12345678901234.123456789012';b['net_pnl']='12345678901234.123456789013'
    registration['declaration']['contrast_checks']=[{'id':'pnl_exact','hypothesis_index':0,'metric':'net_pnl','operator':'eq','threshold':'0.000000000001'}]
    original=deepcopy(attribution);r=ec.evaluate(registration,attribution,CALENDAR,'1000000')
    assert Decimal(r['checks'][0]['revision_minus_baseline'])==Decimal('0.000000000001')
    assert r['checks'][0]['status']=='matched' and attribution==original


@pytest.mark.parametrize('change',[{'threshold':0},{'threshold':'NaN'},{'metric':'sharpe_of_winning_days'},
    {'hypothesis_index':True},{'operator':'approximately'},{'threshold':'1e6'}])
def test_unsupported_or_ambiguous_frozen_check_rejected(change):
    registration,_=evidence();checks=registration['declaration']['contrast_checks'];checks[0].update(change)
    with pytest.raises(AdmissionBlocked):ec.validate(checks,2)


def test_duplicate_prediction_identity_rejected():
    registration,_=evidence();checks=registration['declaration']['contrast_checks'];checks[1]['id']=checks[0]['id']
    with pytest.raises(AdmissionBlocked,match='unique bounded'):ec.validate(checks,2)
