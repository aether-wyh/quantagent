"""Registered ordinary-input entry and generated response application only."""
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from quanta_agents.meta_v3 import study_registry as sr, research_batch
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.kernel import ROOT, module
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.runtime import ResearchRuntime, source_pins
from test_meta_v3_research_entry import fixture, action


@pytest.fixture
def entry(tmp_path,monkeypatch):
    monkeypatch.setattr(sr,'REGISTRY',tmp_path/'canonical.sqlite3')
    def forbidden(*args,**kwargs):pytest.fail('No model, subprocess or account execution')
    monkeypatch.setattr(research_batch.subprocess,'Popen',forbidden)
    monkeypatch.setattr(research_batch,'run',forbidden)
    monkeypatch.setattr(module('meta.codex_gateway').CodexGateway,'run',forbidden)
    spec=importlib.util.spec_from_file_location('study_cli',ROOT/'scripts/run_research_v3.py')
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    case=fixture.prepare(tmp_path/'case',flat=True);casefile=tmp_path/'case.json';casefile.write_text(json.dumps(case),encoding='utf-8')
    task={'idea':'Use evidence to decide whether to abstain.','documents':[],'case':case,'case_hash':digest(case)}
    policy=ClosingPolicy(task_calls=4,stage_calls=4,stage_tokens=600000)
    study={'study_id':'ordinary','trials':[{'id':'one','root':str((tmp_path/'stage').resolve()),
        'case_hash':digest(case),'architecture_hash':'b'*64,'repeat':1,'tasks_hash':digest({'test':task}),
        'source_pins_hash':digest(source_pins()),'policy':asdict(policy),'duration_seconds':7200}]}
    planfile=tmp_path/'study.json';planfile.write_text(json.dumps(study),encoding='utf-8')
    def invoke(args):
        monkeypatch.setattr(sys,'argv',['run_research_v3.py']+args);cli.main()
    invoke(['study-freeze','--plan',str(planfile)])
    args=['create','--root',str(tmp_path/'stage'),'--case',str(casefile),'--idea',task['idea'],
        '--task-id','test','--calls','4','--hours','2','--study-id','ordinary','--trial-id','one']
    return invoke,args,task,tmp_path/'stage'


def test_registered_public_entry_applies_evidence_and_legal_final(entry):
    invoke,args,task,root=entry;invoke(args)
    runtime=ResearchRuntime(root);runtime.verify_inputs()
    one=action(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    final=action(runtime,task,'submit_research_report',{'outcome':'abstain','conclusion':'Generated input alone cannot establish a trading edge.',
        'evidence_ids':[one['id']],'program_evidence_id':None,'limitations':['Generated protocol check only'],
        'next_step':'Complete trustworthy execution evidence','falsifiers':['Valid new execution evidence differs']})
    assert final['status']=='applied' and runtime.ledger.status('test')['terminal']=='submitted'
    s=sr.snapshot('ordinary');assert s['known_tokens']==40 and len(s['calls'])==2 and s['unresolved_reserve']==0
    assert not s['full_stack_comparison_admitted'] and not s['tool_resource_accounting_integrated']
    assert not list(root.rglob('worker_result.json'))
    invoke(['study-status','--study-id','ordinary'])


def test_cli_destination_mismatch_does_not_consume_slot(entry):
    invoke,args,task,root=entry;args[args.index('--root')+1]=str(root.parent/'wrong')
    with pytest.raises(AdmissionBlocked,match='destination'):invoke(args)
    assert sr.snapshot('ordinary')['trials'][0]['claimed_at'] is None


def test_cli_requires_complete_study_binding(entry):
    invoke,args,task,root=entry;args=args[:-2]
    with pytest.raises(SystemExit) as error:invoke(args)
    assert error.value.code==2 and sr.snapshot('ordinary')['trials'][0]['claimed_at'] is None
