"""Actual Job gate probe, generated metadata only; never runs an account."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--registry',required=True);p.add_argument('--mode')
    a=p.parse_args();root=Path(a.root)
    from quanta_agents.meta_v3 import registered_producer as rp,generator_controls as gc,study_registry as sr
    from quanta_agents.meta_v3.ledger import AdmissionBlocked,serial
    sr.REGISTRY=Path(a.registry)
    intent,plan,c=rp._reserve(root);control=root/'control'
    gc.freeze(control,plan['tasks']['producer']['case'],c['space'],count=c['count'],seed=c['seed'],deadline_epoch=plan['deadline_epoch'],only_arm=c['arm'])
    original=json.loads((control/'plan.json').read_text(encoding='utf-8'))
    original_controls=(control/'controls.json').read_bytes()
    rp.authorize_control(control,c['arm']);gc.verify(control)
    mutations=[('wall_seconds_per_arm',('budget','wall_seconds_per_arm'),1200),
        ('output_stop_threshold_bytes_per_arm',('budget','output_stop_threshold_bytes_per_arm'),original['budget']['output_stop_threshold_bytes_per_arm']+1),
        ('scan_cells_per_arm',('budget','scan_cells_per_arm'),original['budget']['scan_cells_per_arm']+1),
        ('extra_budget_field',('budget','extra'),1),('selection',('selection_protocol',),'Choose best only'),
        ('algorithm',('algorithms','random'),'different algorithm'),('domain_size',('domain_size',),999),
        ('scope',('scope',),'unrestricted search'),('formal_flag',('formal_target_success',),True),
        ('future_created_at',('created_at',),original['deadline_epoch']+100),('extra_plan_field',('extra',),'added')]
    probes=[]
    for name,keys,value in mutations:
        changed=deepcopy(original);cursor=changed
        for key in keys[:-1]:cursor=cursor[key]
        cursor[keys[-1]]=value
        (control/'plan.json').write_text(serial(changed),encoding='utf-8')
        # A local matching hash is deliberately regenerated, not trusted.
        (control/'controls.json').write_text(serial(gc._controls(changed)),encoding='utf-8')
        blocked=False;error=None
        try:rp.authorize_control(control,c['arm']);gc.verify(control)
        except AdmissionBlocked as exc:blocked=True;error=str(exc)
        probes.append({'name':name,'blocked':blocked,'error':error,'changed_plan':changed})
    (control/'plan.json').write_text(serial(original),encoding='utf-8');(control/'controls.json').write_bytes(original_controls)
    rp.authorize_control(control,c['arm']);gc.verify(control)
    result={'probe_only':True,'healthy_original_accepted':True,'probes':probes,'account_executions':0,'actual_model_calls':0,'formal_target_success':False}
    (root/'binding_probes.json').write_text(serial(result),encoding='utf-8')
    rp._finish(root,intent,result)

if __name__=='__main__':main()
