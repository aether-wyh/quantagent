"""Explicit generated worker for process-envelope validation; no model service."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def burn(seconds):
    started=time.process_time()
    while time.process_time()-started<seconds:sum(i*i for i in range(200))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--registry',required=True)
    p.add_argument('--mode',required=True);a=p.parse_args();root=Path(a.root)
    if a.mode=='child':
        subprocess.run([sys.executable,'-c',"import time; t=time.process_time();\nwhile time.process_time()-t<0.3: sum(i*i for i in range(200))"],check=True,
                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        blob=b'x'*1048576;path=root/'child_probe.bin';path.write_bytes(blob);assert path.read_bytes()==blob
        (root/'child_probe.json').write_text(json.dumps({'primary_cpu_ms':int(time.process_time()*1000),'child_finished':True}),encoding='utf-8')
        return
    if a.mode=='burn':burn(5);return
    if a.mode=='crash':(root/'before_nonzero_exit.txt').write_text('generated failure',encoding='utf-8');os._exit(7)
    from quanta_agents.meta_v3 import study_registry as sr, process_envelope as pe
    from quanta_agents.meta_v3.runtime import ResearchRuntime
    from quanta_agents.meta_v3.ledger import digest, serial
    sr.REGISTRY=Path(a.registry)
    runtime=ResearchRuntime(root)
    if a.mode=='closing':
        while runtime.ledger.status('test')['mode']=='explore':burn(.05)
    mode=a.mode
    class GeneratedGateway:
        def __init__(self,**kwargs):pass
        def run(self,*,prompt,schema,workdir,**kwargs):
            intent=json.loads((workdir/'intent.json').read_text(encoding='utf-8'))
            history=[r for r in runtime._history('test') if r['id']!=intent['intent_id']];n=len(history)
            if mode=='closing':
                name='submit_research_report'
                args={'outcome':'abstain','conclusion':'Generated process closing reserve check; no actual research model.',
                    'evidence_ids':['input:'+runtime.plan['tasks']['test']['case_hash']],'program_evidence_id':None,
                    'limitations':['Generated fixture'],'next_step':'Complete real admission.','falsifiers':['Accounting mismatch']}
            elif n==0:name='inspect_inputs';args={'table':'fields','offset':0,'limit':32}
            elif n==1:
                name='register_batch'
                program={'version':'factor_strategy_program_v1','factors':[],'target_weight_expression':'{{weight}}',
                    'hypothesis':'Generated accounting check','applicability':['Synthetic'],'invalidation_conditions':['Nonzero fees']}
                args={'families':[{'id':'simple','priority':1,'origin':'model_intuition','mechanism_status':'unknown_anomaly',
                    'mechanism':'Generated only','role':'original','program_template':program,'parameters':{'weight':[.4]},'digit_fields':[]}],
                    'comparisons':[],'selection_rule':'Read all generated results','stop_rule':'continue_settled_failures'}
            elif n==2:name='execute_batch';args={'registration_evidence_id':history[1]['id']}
            elif n==3:name='inspect_batch';args={'registration_evidence_id':history[1]['id'],'candidate_id':None,'table':'results','offset':0,'limit':32}
            elif n==4:
                name='submit_research_report'
                args={'outcome':'strategy_for_development','conclusion':'Generated account lost declared costs; no alpha claim.',
                    'evidence_ids':[history[1]['id'],history[2]['id'],history[3]['id']],'program_evidence_id':history[2]['id'],
                    'batch_candidate_id':'c001','limitations':['Generated prices and generated model receipts; not formal.'],
                    'next_step':'Admit actual evidence.','falsifiers':['Accounting mismatch']}
            else:raise AssertionError('Unexpected generated model opportunity')
            response={'action':name,'arguments_json':json.dumps(args),'public_summary':'Generated fixture, no model supplier',
                'self_review':dict.fromkeys(('assessment','uncertainty','next_step','falsifier'),'Generated only')}
            runtime.gateway_module._validate_output(response,schema)
            receipt={'response':response,'usage':{'input_tokens':10,'output_tokens':10},
                'request_identity':{'intent_id':intent['intent_id']},'artifact_sha256':{},'model_verified':False,'generated_fixture':True}
            (workdir/'generated_receipt.json').write_text(serial(receipt),encoding='utf-8')
    runtime.gateway_module.CodexGateway=GeneratedGateway
    runtime.gateway_module.verify_saved_completion=lambda folder,**kw:json.loads((folder/'generated_receipt.json').read_text(encoding='utf-8'))
    result=runtime.run()
    (root/'generated_runtime_validation.json').write_text(serial({'status':result,'history':runtime._history('test'),
        'process_resources_before_exit':pe.public_status(root),'actual_model_calls':0,'generated_only':True}),encoding='utf-8')


if __name__=='__main__':main()
