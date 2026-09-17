"""Canary-only preflight tests, no sealed input or source acquisition."""
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from quanta_agents.meta_v3 import research_extension as extension
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from quanta_agents.meta_v3.source_admission import admit_paths,substantive_change
from test_meta_v3_research_extension import prepared


def test_metadata_only_extension_cannot_register_fresh_budget(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    with parent.transaction() as db:_,plan,_=parent._plan(db)
    child=deepcopy(plan['tasks']['test']['case']);child['description']+=' metadata only'
    child['evidence_sources']=kwargs['child_case']['evidence_sources'];kwargs['child_case']=child
    with pytest.raises(AdmissionBlocked,match='no substantive'):extension.decide_extension(parent.root,'test',eid,**kwargs)
    assert not (parent.root/'controller_extensions'/eid/'stage').exists()


@pytest.mark.parametrize('invalid',['dates','path','partition'])
def test_rejected_scope_never_reads_new_canary(tmp_path,monkeypatch,invalid):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    child=kwargs['child_case'];canary=tmp_path/'unadmitted_canary.txt';canary.write_text('Engineering only')
    child['evidence_sources'].append({'path':str(canary),'sha256':hashlib.sha256(canary.read_bytes()).hexdigest()})
    if invalid=='dates':child['decision_fixture']['calendar'][0]='2024-12-31'
    if invalid=='partition':kwargs['decision']['source_admissions'].append({'path':str(canary),'role':'development_market_data',
        'partition':'sealed_holdout','content_date_range':['2024-01-01','2025-12-31']})
    reads=[];original=Path.read_bytes
    def observed(p):
        if p.resolve()==canary.resolve():reads.append(str(p))
        return original(p)
    monkeypatch.setattr(Path,'read_bytes',observed)
    with pytest.raises((AdmissionBlocked,ValueError)):extension.decide_extension(parent.root,'test',eid,**kwargs)
    assert reads==[]
    assert not (parent.root/'controller_extensions'/eid/'stage').exists()


def test_historical_disclosure_dates_do_not_grant_market_partition(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch);case=kwargs['child_case']
    path=case['evidence_sources'][0]['path']
    declaration=[{'path':path,'role':'historical_notice','partition':'public_disclosure','content_date_range':['2012-11-16','2012-11-16']}]
    assert not admit_paths(case,declaration)['content_verified']
    case['raw_source_bindings']['source_artifacts']=[{'root':str(tmp_path),'rows_file':Path(path).name,'manifest_file':Path(path).name}]
    with pytest.raises(AdmissionBlocked,match='notice admission'):admit_paths(case,declaration)


def test_more_existing_tool_quota_is_not_new_capability(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    with parent.transaction() as db:_,plan,_=parent._plan(db)
    old=plan['tasks']['test']['case'];new=deepcopy(old)
    new['research_policy']['action_limits']['develop_strategy']+=1
    with pytest.raises(AdmissionBlocked,match='quota-only'):substantive_change(old,new,'tool')
    new['research_policy']['action_limits']['diagnose_execution']=0
    assert substantive_change(new,old,'tool')['new_actions']==['diagnose_execution']


@pytest.mark.parametrize('change',['unit_space','field_order','unit_semantics','existing_value'])
def test_metadata_and_corrections_are_not_new_data(tmp_path,monkeypatch,change):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    with parent.transaction() as db:_,plan,_=parent._plan(db)
    old=plan['tasks']['test']['case'];new=deepcopy(old)
    if change=='unit_space':new['decision_fixture']['fields'][0]['unit']+=' '
    if change=='field_order':new['decision_fixture']['field_rows'].reverse()
    if change=='unit_semantics':new['decision_fixture']['fields'][0]['unit']='changed unit'
    if change=='existing_value':new['decision_fixture']['field_rows'][0]['value']+=1
    with pytest.raises(AdmissionBlocked,match='no substantive'):substantive_change(old,new,'data')


def test_wrong_deliverable_or_silent_correction_cannot_renew_budget(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    with parent.transaction() as db:_,plan,_=parent._plan(db)
    old=plan['tasks']['test']['case'];new=kwargs['child_case']
    with pytest.raises(AdmissionBlocked,match='deliverables absent'):substantive_change(old,new,'data',['unfulfilled'])
    new['decision_fixture']['field_rows'][0]['value']+=1
    with pytest.raises(AdmissionBlocked,match='existing data correction'):substantive_change(old,new,'data',['volume'])


def test_actual_additional_dates_can_deliver_existing_fields(tmp_path,monkeypatch):
    parent,eid,kwargs=prepared(tmp_path,monkeypatch)
    with parent.transaction() as db:_,plan,_=parent._plan(db)
    old=plan['tasks']['test']['case'];new=deepcopy(old)
    new['decision_fixture']['calendar'].append('2026-01-13')
    row=deepcopy(new['decision_fixture']['field_rows'][-1])
    row.update(session='2026-01-13',effective_at='2026-01-13T15:05:00+08:00',available_at='2026-01-13T15:05:00+08:00')
    new['decision_fixture']['field_rows'].append(row)
    # This tests the material-change classifier only. Full admission still
    # requires complete eligibility/account grids, path partitions and bounds.
    changed=substantive_change(old,new,'data',['close'])
    assert changed['new_observation_coordinates']==1 and changed['added_sessions']==['2026-01-13']
