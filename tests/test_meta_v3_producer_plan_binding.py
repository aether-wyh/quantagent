"""Control-plan trust and shared headroom, with no strategy execution."""
import hashlib
import json
from pathlib import Path

import pytest
from quanta_agents.meta_v3 import registered_producer as rp,study_registry as sr,process_envelope as pe,study_allocation as sa
from quanta_agents.meta_v3.ledger import AdmissionBlocked,serial
from quanta_agents.meta_v3.runtime import source_pins
from test_meta_v3_registered_producer import setup_producer

def test_actual_native_gate_rejects_full_plan_drift_despite_matching_local_hash(setup_producer):
    plan,tasks,policy=setup_producer(freeze=False)
    entry=Path(__file__).parent/'helpers/meta_v3_producer_binding_fixture.py'
    trial=plan['trials'][0];trial['process_envelope'].update(entrypoint=str(entry.resolve()),entrypoint_sha256=hashlib.sha256(entry.read_bytes()).hexdigest())
    sr.freeze(plan)
    ledger=sr.create_stage(trial['root'],'producer','fixed',policy=policy,tasks=tasks,duration_seconds=7200,provenance={'source_pins':source_pins()})
    receipt=rp.dispatch(ledger.root)
    assert receipt['exit_code']==0,(ledger.root/'process_runs/1/worker.log').read_text(encoding='utf-8',errors='replace')
    data=json.loads((ledger.root/'binding_probes.json').read_text(encoding='utf-8'))
    assert data['healthy_original_accepted'] and data['account_executions']==0
    assert all(x['blocked'] for x in data['probes']),[x['name'] for x in data['probes'] if not x['blocked']]
    assert receipt['metrics']['active_processes']==0 and receipt['metrics']['cpu_ms']>0

@pytest.mark.parametrize('exhausted',['model','tool','process',None])
def test_shared_headroom_gates_both_dispatch_and_actual_generation(setup_producer,monkeypatch,exhausted):
    ledger=setup_producer()[0]
    state={'integrated':True,**{k+'_allocation_exhausted':k==exhausted for k in ('model','tool','process')}}
    # Explicit generated allocation state, not an observed supplier overrun.
    monkeypatch.setattr(sa,'status',lambda *a:state)
    def reserve_only(root):
        intent,_=pe.reserve(root)
        return {'reserved_process_intent':intent,'native_launches':0}
    monkeypatch.setattr(pe,'supervise',reserve_only)
    dispatch_blocked=False;dispatch_error=None
    try:rp.dispatch(ledger.root)
    except AdmissionBlocked as exc:dispatch_blocked=True;dispatch_error=str(exc)
    # Only isolate the additional shared-allocation check in _active. Native
    # membership itself is exercised by the separate actual Job test.
    monkeypatch.setattr(pe,'_current',lambda *a:{'integrated':True,'generated_native_state':True})
    active_blocked=False;active_error=None
    with sr._db() as db:
        binding=rp._binding(db,ledger.root)
        try:rp._active(db,ledger.root,binding)
        except AdmissionBlocked as exc:active_blocked=True;active_error=str(exc)
    observation={'generated_allocation_state':state,'dispatch_blocked':dispatch_blocked,'dispatch_error':dispatch_error,
        'actual_generation_gate_blocked':active_blocked,'actual_generation_gate_error':active_error,
        'process_intents_used':pe.status(ledger.root)['launches_used'],'native_launches':0,'actual_models':0,'accounts':0}
    (ledger.root/'shared_headroom_probe.json').write_text(serial(observation),encoding='utf-8')
    assert dispatch_blocked==(exhausted is not None) and active_blocked==(exhausted is not None),observation
    assert observation['process_intents_used']==(0 if exhausted else 1)
