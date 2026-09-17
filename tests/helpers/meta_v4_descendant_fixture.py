"""Generated receipts in an actual parent/child Windows Job; never a supplier."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from quanta_agents.meta_v3 import study_registry as sr, process_envelope as pe
from quanta_agents.meta_v3 import codex_session_gateway as capture
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import Ledger,digest,serial
from quanta_agents.meta_v3.research_extension import decide_extension
from quanta_agents.meta_v3.runtime import ResearchRuntime,action_schema


def action(runtime,task_id,name,args):
    tools=runtime._tools(task_id)
    intent=runtime.ledger.reserve(task_id,tools.menu(),lambda menu,*a:('Generated native-job fixture',action_schema(menu)))
    response={'action':name,'arguments_json':json.dumps(args),'public_summary':'Generated fixture, no provider',
              'self_review':dict.fromkeys(('assessment','uncertainty','next_step','falsifier'),'Fixture')}
    receipt={'response':response,'usage':{'input_tokens':10,'output_tokens':10},
             'request_identity':{'intent_id':intent['intent_id']},'artifact_sha256':{'runtime_session.jsonl':'a'*64},
             'model_verified':False,'runtime_identity':{'verified':True,'level':'generated_fixture'}}
    runtime.ledger.receive_saved(intent['intent_id'],lambda *a,**k:receipt)
    runtime._apply(intent['intent_id'])
    row=runtime.ledger.call(intent['intent_id'])
    assert row['status']=='applied',row
    return row['id']


def final(runtime,task):
    case=runtime.plan['tasks'][task]['case']
    return action(runtime,task,'submit_research_report',{
        'outcome':'abstain','conclusion':'Generated native-job inputs only.',
        'evidence_ids':['input:'+digest(case)],'program_evidence_id':None,
        'limitations':['Generated only'],'next_step':'Inspect real evidence','falsifiers':['Real evidence differs']})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    parser.add_argument('--registry',required=True);parser.add_argument('--child',action='store_true')
    args=parser.parse_args();sr.REGISTRY=Path(args.registry)
    runtime=ResearchRuntime(args.root)
    capture.CodexGateway.run=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Supplier calls forbidden'))
    if args.child:
        assert pe.inside(runtime.root)
        call=action(runtime,'extension','inspect_inputs',{'table':'fields','offset':0,'limit':32})
        observed=pe.public_status(runtime.root)
        final(runtime,'extension')
        (runtime.root/'native_child_probe.json').write_text(serial({'call_id':call,'process':observed,'actual_model_calls':0}),encoding='utf-8')
        return
    first=action(runtime,'test','inspect_inputs',{'table':'coverage','offset':0,'limit':32})
    request=action(runtime,'test','request_research_extension',{
        'evidence_ids':[first],'problem':'Check a new generated field under the original trial.',
        'request_kind':'data','requested_fields':['volume'],'specification':'Generated volume on the same axes',
        'expected_information_gain':'Test inherited accounting only, no financial claim.',
        'requested_resource_bounds':{'symbols':1,'sessions':5,'model_calls':3,'download_bytes':0,'wall_seconds':7200}})
    capture.verify_saved_completion=lambda folder,**k:runtime.ledger.call(Path(folder).name)['receipt']
    case=deepcopy(runtime.plan['tasks']['test']['case'])
    case['decision_fixture']['fields'].append({'name':'volume','unit':'generated shares'})
    rows=deepcopy(case['decision_fixture']['field_rows'])
    for row in rows:row.update(field='volume',value=100)
    case['decision_fixture']['field_rows'].extend(rows)
    source=runtime.root/'source.json';source.write_text(serial(case),encoding='utf-8')
    case['evidence_sources']=[{'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]
    decision={'status':'ready','reason':'Generated native-job resource fixture.',
              'asset_contract':'a_share_cash_equity','resource_bounds':{
                  'symbols':1,'sessions':5,'model_calls':3,'download_bytes':0,'wall_seconds':7200},
              'exposure_statement':'Generated fields only, not market research.',
              'source_admissions':[{'path':str(source),'role':'engineering','partition':'generated_fixture','content_date_range':None}]}
    result=decide_extension(runtime.root,'test',request,decision=decision,child_case=case,
                            policy=ClosingPolicy(task_calls=3,stage_calls=3,stage_tokens=600000),
                            deadline_epoch=min(time.time()+7000,runtime.plan['deadline_epoch']))
    subprocess.run([sys.executable,__file__,'--root',result['child_root'],'--registry',str(sr.REGISTRY),'--child'],check=True)
    final(runtime,'test')
    (runtime.root/'native_descendant_validation.json').write_text(serial({'child_root':result['child_root'],
        'study':sr.snapshot('native_descendants'),'actual_model_calls':0}),encoding='utf-8')


if __name__=='__main__':main()
