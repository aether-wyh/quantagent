"""Public-contract branch and claimed saved-only recovery; no paid model calls."""
from copy import deepcopy
import json
import time

import pytest

from quanta_agents.meta_v3.ledger import Ledger,digest,AdmissionBlocked
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.research_tools import ResearchTools,save_once
from quanta_agents.meta_v3.runtime import ResearchRuntime,source_pins
from quanta_agents.meta_v3.saved_recovery import prepare,proofs,READ_ACTIONS
from quanta_agents.meta_v3 import research_batch
from test_meta_v3_batch_research import configured,declaration,execute,read_results,report
from test_meta_v3_research_entry import action,program


def test_public_contract_describes_both_final_evidence_branches(tmp_path):
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    args=tools.contract()['actions']['submit_research_report']['arguments']
    assert all(s in args['program_evidence_id'] for s in ('develop_strategy','execute_batch','batch_candidate_id','abstention'))
    execute(tools,'registration','register_batch',declaration((.2,)))
    execute(tools,'run','execute_batch',{'registration_evidence_id':'registration'})
    read_results(tools)
    assert tools.final(report(candidate='c001'))['legal_submission']
    p=program();p['target_weight_expression']='0.3'
    execute(tools,'ordinary','develop_strategy',{'program':p})
    ordinary=report();ordinary.pop('batch_candidate_id');ordinary['program_evidence_id']='ordinary';ordinary['evidence_ids']=['ordinary']
    assert tools.final(ordinary)['legal_submission']


def parent_with_batch(tmp_path,monkeypatch):
    case=configured(tmp_path);task={'case':case,'case_hash':digest(case),'idea':'Engineering contract recovery fixture','documents':[]}
    ledger=Ledger.create(tmp_path/'parent',policy=ClosingPolicy(task_calls=10,stage_calls=10,task_tokens=600000,stage_tokens=600000),
        tasks={'test':task},deadline_epoch=time.time()+7200,provenance={'source_pins':source_pins(),'fixture_only':True})
    rt=ResearchRuntime(ledger.root)
    save_once(ledger.root/'public_contract_at_admission.json',rt._tools('test').contract())
    reg=action(rt,task,'register_batch',declaration((.2,)))
    run=action(rt,task,'execute_batch',{'registration_evidence_id':reg['id']})
    ledger.pause('Engineering contract defect fixture')
    # Only explicit saved-response test receipts are substituted, never supplier evidence.
    monkeypatch.setattr(rt.gateway_module,'verify_saved_completion',lambda folder,**_:ledger.call(folder.name)['receipt'])
    return rt,reg,run


def test_claimed_recovery_reads_parent_batch_with_no_replay_or_parent_writes(tmp_path,monkeypatch):
    parent,reg,run=parent_with_batch(tmp_path,monkeypatch)
    before=proofs(parent.root);old_plan=deepcopy(parent.plan)
    child=prepare(parent.root,tmp_path/'recovery','test',reason='Engineering public final-ID contract correction.')
    rt=ResearchRuntime(child.root);task=rt.plan['tasks']['test'];tools=rt._tools('test')
    assert rt.plan['policy']['stage_calls']==8 and rt.plan['policy']['stage_tokens']==400000
    assert rt.plan['deadline_epoch']==old_plan['deadline_epoch'] and task['case']==old_plan['tasks']['test']['case']
    assert set(tools.menu())<=set(READ_ACTIONS)
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('saved recovery dispatched strategy'))
    monkeypatch.setattr(research_batch,'run',lambda *a,**k:pytest.fail('saved recovery recomputed batch'))
    with pytest.raises(AdmissionBlocked,match='forbidden'):tools.execute('no','develop_strategy',{'program':program()})
    page=action(rt,task,'inspect_batch',{'registration_evidence_id':reg['id'],'candidate_id':None,'table':'results','offset':0,'limit':32})
    assert page['result']['public']['next_offset'] is None
    diagnosis=action(rt,task,'diagnose_execution',{'evidence_ids':[run['id']+'/c001']})
    assert diagnosis['status']=='applied'
    final=report(candidate='c001');final['program_evidence_id']=run['id'];final['evidence_ids']=[run['id'],page['id'],diagnosis['id']]
    result=action(rt,task,'submit_research_report',final)
    assert result['status']=='applied' and result['result']['legal_submission']
    assert child.status('test')['terminal']=='submitted' and parent.ledger.status('test')['final_call'] is None
    assert proofs(parent.root)==before
    with pytest.raises(AdmissionBlocked,match='already claimed'):prepare(parent.root,tmp_path/'duplicate','test',reason='duplicate')


def test_recovery_detects_parent_receipt_drift_and_never_repairs_parent(tmp_path,monkeypatch):
    parent,reg,run=parent_with_batch(tmp_path,monkeypatch)
    child=prepare(parent.root,tmp_path/'recovery','test',reason='Engineering public final-ID contract correction.')
    rt=ResearchRuntime(child.root)
    receipt=parent.root/'batches/test'/reg['id']/'candidates/c001/receipt.json'
    original=receipt.read_bytes();receipt.unlink()
    with pytest.raises((FileNotFoundError,AdmissionBlocked)):rt.verify_inputs()
    with pytest.raises(AdmissionBlocked,match='read-only recovery cannot repair'):rt._tools('test')._candidate(run['id']+'/c001')
    assert not receipt.exists()
    receipt.write_bytes(original)
    rt.verify_inputs()


def test_saved_recovery_cannot_spend_unknown_or_consumed_final(tmp_path,monkeypatch):
    parent,reg,run=parent_with_batch(tmp_path,monkeypatch)
    with parent.ledger.transaction() as db:db.execute("UPDATE calls SET known_tokens=NULL,status='unknown' WHERE id=?",(run['id'],))
    with pytest.raises(AdmissionBlocked,match='settled'):prepare(parent.root,tmp_path/'unknown','test',reason='unknown')
    assert not (parent.root/'test_saved_recovery_claim.json').exists()


def test_copied_recovery_directory_cannot_reuse_original_claim(tmp_path,monkeypatch):
    import shutil
    parent,_,_=parent_with_batch(tmp_path,monkeypatch)
    child=prepare(parent.root,tmp_path/'recovery','test',reason='Engineering root-binding fixture.')
    copied=tmp_path/'copied_stage';shutil.copytree(child.root,copied)
    assert not Ledger(copied).status('test')['calls']
    with pytest.raises(AdmissionBlocked,match='runtime root differs'):
        ResearchRuntime(copied).run()
    assert not Ledger(copied).status('test')['calls'] and not child.status('test')['calls']


def test_recovery_admission_path_must_be_inside_claimed_root(tmp_path,monkeypatch):
    from quanta_agents.meta_v3.saved_recovery import verify_saved_recovery
    parent,_,_=parent_with_batch(tmp_path,monkeypatch)
    child=prepare(parent.root,tmp_path/'recovery','test',reason='Engineering admission-path fixture.')
    plan=json.loads((child.root/'plan.json').read_text(encoding='utf-8'))
    plan['provenance']['saved_contract_recovery']['decision_path']=str(tmp_path/'copied_admission.json')
    with pytest.raises(AdmissionBlocked,match='inside claimed root'):verify_saved_recovery(plan,child.root)


def test_legacy_final_recovery_cannot_claim_saved_recovery_balance(tmp_path,monkeypatch):
    import importlib.util
    from quanta_agents.meta_v3.kernel import ROOT
    spec=importlib.util.spec_from_file_location('legacy_final_recovery',ROOT/'scripts/prepare_v3_final_recovery.py')
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    parent,_,_=parent_with_batch(tmp_path,monkeypatch)
    prepare(parent.root,tmp_path/'recovery','test',reason='Engineering exclusive claim fixture.')
    with pytest.raises(AdmissionBlocked,match='already claimed'):legacy.prepare(parent.root,tmp_path/'legacy','test')
    assert not (tmp_path/'legacy').exists()
