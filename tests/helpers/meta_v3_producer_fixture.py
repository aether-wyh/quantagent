"""Generated producer validation only; exercises the public CLI without a supplier."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True);parser.add_argument('--registry',required=True)
    parser.add_argument('--mode',required=True)
    args=parser.parse_args();root=Path(args.root)
    from quanta_agents.meta_v3 import generator_controls as gc, registered_producer as rp, study_registry as sr
    from quanta_agents.meta_v3.ledger import AdmissionBlocked, Ledger, serial
    sr.REGISTRY=Path(args.registry)
    original=gc.run_control
    def checked(control,arm,**kwargs):
        checks=[]
        def rejects(name,operation):
            try:operation()
            except AdmissionBlocked as exc:checks.append({'check':name,'error':str(exc)})
            else:raise AssertionError(name+' was admitted')
        rejects('wrong frozen arm',lambda:original(control,'random' if arm=='fixed' else 'fixed'))
        plan_path=Path(control)/'plan.json';saved=plan_path.read_bytes()
        changed=json.loads(saved);changed['space']['parameters']['weight'][0]=.7
        plan_path.write_text(serial(changed),encoding='utf-8')
        rejects('changed frozen domain',lambda:original(control,arm))
        plan_path.write_bytes(saved)
        ledger=Ledger(root)
        rejects('standalone has no model authority',lambda:ledger.reserve('producer',('submit_research_report',),lambda *a:('Generated no supplier probe',{})))
        (root/'admission_probes.json').write_text(serial({'checks':checks,'actual_model_calls':0}),encoding='utf-8')
        return original(control,arm,**kwargs)
    if args.mode!='closing':gc.run_control=checked
    if args.mode=='unknown':
        def interrupted(root,intent,result):
            (Path(root)/'generated_uncommitted_result.json').write_text(serial(result),encoding='utf-8')
            raise OSError('Generated interruption before canonical producer receipt')
        rp._finish=interrupted
    entry=Path(__file__).resolve().parents[2]/'scripts/run_registered_producer_v3.py'
    spec=importlib.util.spec_from_file_location('producer_cli',entry)
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    sys.argv=[str(entry),'run','--root',str(root)]
    cli.main()


if __name__=='__main__':main()
