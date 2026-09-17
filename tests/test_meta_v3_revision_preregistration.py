"""Generated saved evidence tests; no account, native Job or supplier execution."""
from copy import deepcopy
import json
import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest
from quanta_agents.meta_v3.research_tools import ResearchTools,save_once
from quanta_agents.meta_v3 import research_batch
from test_meta_v3_batch_research import configured,declaration,execute
from test_meta_v3_research_entry import program


def saved(tools,eid,action,artifact):
    """Explicitly generated trusted-history stand-in, not a real model or account."""
    folder=tools.folder/eid;folder.mkdir()
    artifact={'fixture_only':True,'fixture_note':'Generated saved-tool identity only; no executed account',**artifact}
    save_once(folder/'artifact.json',artifact)
    tools.history.append({'id':eid,'response':{'action':action,'arguments_json':'{}'},'result':{'artifact_hash':digest(artifact)}})


@pytest.fixture
def setup(tmp_path,monkeypatch):
    # These tests never authorize an account; any accidental batch child is fatal.
    monkeypatch.setattr(research_batch.subprocess,'Popen',lambda *a,**k:pytest.fail('unexpected execution process'))
    tools=ResearchTools(tmp_path/'stage','test',configured(tmp_path),[])
    baseline=program();baseline['target_weight_expression']='0.4'
    saved(tools,'baseline','develop_strategy',{'program':baseline})
    saved(tools,'diagnosis','diagnose_execution',{'input_evidence_ids':['baseline']})
    revision=program();revision['target_weight_expression']='0.2'
    args={'baseline_evidence_id':'baseline','diagnosis_evidence_id':'diagnosis',
        'mechanism_hypotheses':['Different exposure changes the generated path; no causal claim'],
        'distinguishing_prediction':'Compare the full-capital paths without deleting a failed candidate',
        'structural_change':'Generated target change for registration-order validation',
        'revision_program':revision,'success_rule':'Must be prospectively registered',
        'failure_rule':'Previously observed executable rule cannot be relabeled prospective'}
    return tools,args


@pytest.mark.parametrize('raw_status',['completed_mechanical','failed'])
def test_saved_ordinary_rule_cannot_be_relabeled_preregistered(setup,raw_status):
    tools,args=setup
    saved(tools,'observed','develop_strategy',{'program':deepcopy(args['revision_program']),'raw':{'status':raw_status}})
    with pytest.raises(AdmissionBlocked,match='already recorded'):
        execute(tools,'posthoc','register_experiment',args)
    assert not (tools.folder/'posthoc/artifact.json').exists()
    ref=json.loads((tools.folder/'posthoc/duplicate_reference.json').read_text(encoding='utf-8'))
    assert ref['reuse_evidence_id']=='observed' and ref['new_execution'] is False


def test_changing_prose_does_not_make_seen_rule_prospective(setup):
    tools,args=setup
    saved(tools,'observed','develop_strategy',{'program':deepcopy(args['revision_program'])})
    args['revision_program']['hypothesis']='A newly written explanation after seeing the same executable rule'
    with pytest.raises(AdmissionBlocked,match='already recorded'):
        execute(tools,'posthoc_prose','register_experiment',args)


def test_existing_batch_reservation_uses_its_original_candidate_identity(setup):
    tools,args=setup
    execute(tools,'batch','register_batch',declaration((0.2,)))
    registration=json.loads((tools.folder/'batch/artifact.json').read_text(encoding='utf-8'))
    args['revision_program']=deepcopy(registration['candidates'][0]['program'])
    with pytest.raises(AdmissionBlocked,match='recorded in batch'):
        execute(tools,'posthoc_batch','register_experiment',args)
    assert not list(tools.batch_folder.rglob('intent.json'))
    assert not (tools.folder/'posthoc_batch/artifact.json').exists()


def test_fresh_distinct_revision_still_registers_without_execution(setup):
    tools,args=setup
    result=execute(tools,'fresh','register_experiment',args)
    assert result['public']['executed'] is False
    artifact=json.loads((tools.folder/'fresh/artifact.json').read_text(encoding='utf-8'))
    assert artifact['kind']=='preregistered_revision_v1' and artifact['success_not_evaluated'] is True
    assert artifact['revision_program_hash']==digest(args['revision_program'])
    assert not list(tools.root.rglob('worker_result.json'))


def test_saved_evidence_drift_cannot_be_used_for_prospective_label(setup):
    tools,args=setup
    saved(tools,'observed','develop_strategy',{'program':deepcopy(args['revision_program'])})
    p=tools.folder/'observed/artifact.json';v=json.loads(p.read_text(encoding='utf-8'))
    v['program']['target_weight_expression']='0.3';p.write_text(json.dumps(v),encoding='utf-8')
    with pytest.raises(AdmissionBlocked,match='saved tool evidence changed'):
        execute(tools,'drifted','register_experiment',args)


def test_existing_duplicate_execution_guard_still_precedes_any_account(setup):
    tools,args=setup
    saved(tools,'observed','develop_strategy',{'program':deepcopy(args['revision_program'])})
    with pytest.raises(AdmissionBlocked,match='already recorded'):
        execute(tools,'no_rerun','develop_strategy',{'program':args['revision_program']})
    assert not (tools.folder/'no_rerun/subattempts.json').exists()
