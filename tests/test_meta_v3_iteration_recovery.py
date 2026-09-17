"""Offline regression against the preserved independent engineering failure."""
from copy import deepcopy
import hashlib
import json

import pytest

from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3 import research_iteration as iteration
from test_meta_v3_research_iteration import configured

SOURCE=ROOT/'docs/research/meta_framework_v3_handoff/parent_iteration_review_001/fixture_execution'
ARTIFACT=SOURCE/'tools/unit/failed_after_fill/artifact.json'


def saved():return json.loads(ARTIFACT.read_text(encoding='utf-8'))


def imported_tools(tmp_path):
    artifact=saved()
    entry={'id':'failed_after_fill','response':{'action':'develop_strategy'},
        'result':{'artifact_hash':digest(artifact)}}
    return ResearchTools(tmp_path,'unit',configured(),[entry],imported={'root':str(SOURCE),'task_id':'unit','rows':[entry]})


def test_saved_failed_fill_diagnoses_without_execution_or_nav_invention(tmp_path,monkeypatch):
    before=hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    tools=imported_tools(tmp_path)
    monkeypatch.setattr(tools.raw,'develop',lambda *a,**k:pytest.fail('must not rerun a saved failure'))
    result=tools.execute('repaired','diagnose_execution',{'evidence_ids':['failed_after_fill']})
    item=result['public']['accounts'][0]
    assert item['last_complete_date']=='2026-01-06' and item['last_valued_nav']=='100000.00'
    assert item['final_nav'] is None and item['net_pnl'] is None and item['return_on_full_initial_cash'] is None
    assert item['maximum_drawdown'] is None and not item['complete_account']
    assert item['saved_account_state']['cash']=='95992.66'
    assert item['saved_account_state']['positions']=={'600006.SH':400}
    assert item['fees_on_recorded_trades']=='5.04' and item['unvalued_trade_count']==1
    assert 'missing held mark' in item['error']['message']
    tools.history.append({'id':'repaired','response':{'action':'diagnose_execution'},'result':result})
    for table,field,value in [('attribution_unvalued_trades','quantity',400),('attribution_rights','entitled_shares',400)]:
        page=tools.execute(table,'read_evidence',{'evidence_id':'repaired','table':table,'offset':0,'limit':32})
        assert page['public']['rows'][0][field]==value
    assert hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()==before


def test_failure_before_first_valuation_keeps_fills_and_same_prefix_has_no_final_comparison():
    value=saved();value['raw']['partial']['daily']=[]
    a=iteration.account_attribution('zero_valued_days',value)
    assert a['trade_count']==1 and a['unvalued_trade_count']==1 and a['last_valued_nav'] is None
    assert a['saved_account_state']['positions']=={'600006.SH':400}
    compared=iteration.diagnose([('a',saved()),('b',saved())])
    assert not compared['pairs'][0]['same_cash_calendar_and_initial_capital']
    assert 'comparison_minus_reference_net_pnl' not in compared['pairs'][0]


def test_cosmetic_revision_is_saved_but_cannot_register_or_execute(tmp_path,monkeypatch):
    tools=imported_tools(tmp_path);original=saved()['program'];p=deepcopy(original)
    p['hypothesis']+='; only wording changed'
    p['applicability']=['Same expression, new narrative']
    assert digest(p)!=digest(original) and iteration.executable_program_hash(p)==iteration.executable_program_hash(original)
    declaration={'baseline_evidence_id':'b','diagnosis_evidence_id':'d','mechanism_hypotheses':['Unknown; no executable difference'],
        'distinguishing_prediction':'No targets change','structural_change':'Cosmetic only','revision_program':p,
        'success_rule':'No new computation','failure_rule':'Duplicate run'}
    with pytest.raises(AdmissionBlocked,match='narrative-only'):
        iteration.register_experiment(declaration,{'program':original},{'input_evidence_ids':['b']},tools.program.validate_program,tools.case['decision_fixture']['fields'])
    monkeypatch.setattr(tools.raw,'develop',lambda *a,**k:pytest.fail('duplicate execution'))
    with pytest.raises(AdmissionBlocked,match='identical executable rules'):
        tools.execute('cosmetic','develop_strategy',{'program':p})
    proof=json.loads((tools.folder/'cosmetic/duplicate_reference.json').read_text(encoding='utf-8'))
    assert proof['reuse_evidence_id']=='failed_after_fill' and not proof['new_execution']
    assert (tools.folder/'cosmetic/request.json').is_file()
    assert not (tools.folder/'cosmetic/workbench').exists()
    p['target_weight_expression']='0'
    declaration['revision_program']=p
    assert iteration.register_experiment(declaration,{'program':original},{'input_evidence_ids':['b']},tools.program.validate_program,tools.case['decision_fixture']['fields'])['executed'] is False
