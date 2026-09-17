"""Generated committed peer costs between dispatch check and process intent."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import time

import pytest
from quanta_agents.meta_v3 import process_envelope as pe,registered_producer as rp,study_registry as sr
from quanta_agents.meta_v3 import study_allocation as sa,tool_measurements as tm
from quanta_agents.meta_v3.ledger import AdmissionBlocked,digest,serial
from quanta_agents.meta_v3.runtime import source_pins
from test_meta_v3_registered_producer import setup_producer

def mixed(setup_producer):
    plan,tasks,policy=setup_producer(freeze=False)
    one=plan['trials'][0];peer=deepcopy(one)
    peer.update(id='ordinary',root=str(Path(one['root']).parent/'ordinary'),architecture_hash=digest('ordinary generated peer'))
    peer.pop('producer_contract');peer['process_envelope']['arguments'][1]=peer['root']
    plan['trials'].append(peer)
    for k in ('model_tokens','model_calls'):plan['allocation'][k]*=2
    for k in ('tool_resources','process_resources'):
        plan['allocation'][k]={n:2*v for n,v in plan['allocation'][k].items()}
    sr.freeze(plan)
    stages=[sr.create_stage(t['root'],'producer',t['id'],policy=policy,tasks=tasks,duration_seconds=7200,provenance={'source_pins':source_pins()}) for t in plan['trials']]
    return stages

def commit_generated_peer_cost(kind):
    """Synthetic canonical records only: no gateway, supplier proof or outputs."""
    if kind=='healthy':return
    with sr._db() as db:
        _,row,spec=sr._trial(db,'producer','ordinary')
        known=spec['policy']['stage_tokens']+1 if kind=='model' else 0
        proof=digest({'explicit_generated_cost_fixture':kind})
        db.execute('INSERT INTO calls(study_id,trial_id,id,intent_hash,reserve,known_tokens,proof_hash) VALUES(?,?,?,?,?,?,?)',
            ('producer','ordinary','generated_peer_cost',digest({'generated_intent':kind}),1,known,proof))
        if kind=='tool':
            quote={'actions':1,'candidates':0,'scan_cells':0,'comparisons':0}
            metrics={'wall_ms':spec['tool_budget']['wall_ms']+1,'controller_cpu_ms':0,'retained_output_bytes':0}
            result_hash=digest({'generated_tool_result':True})
            db.execute('INSERT INTO tool_actions(study_id,trial_id,id,task_id,action,request_hash,quote,started_at,metrics,outcome,result_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                ('producer','ordinary','generated_peer_cost','producer','inspect_inputs',digest({'generated_request':True}),serial(quote),time.time(),serial(metrics),'returned',result_hash))
            tool=db.execute('SELECT * FROM tool_actions').fetchone()
            body={'kind':tm.VERSION,'tool_intent':tm.identity(db,tool),'metrics':metrics,'outcome':'returned','result_hash':result_hash,'before_bytes':0,'outputs':[]}
            tm._validate(body,body['tool_intent'])
            db.execute('INSERT INTO tool_measurements(study_id,trial_id,id,receipt_hash,body) VALUES(?,?,?,?,?)',
                ('producer','ordinary','generated_peer_cost',digest(body),serial(body)))

def count_intents(trial='fixed'):
    with sr._db() as db:
        return db.execute('SELECT count(*) FROM process_runs WHERE trial_id=? AND intent IS NOT NULL',(trial,)).fetchone()[0]

@pytest.mark.parametrize('kind',['model','tool','healthy'])
def test_committed_peer_cost_after_outer_check_is_rechecked_at_real_reservation(setup_producer,monkeypatch,kind):
    ledger,peer=mixed(setup_producer);events=[];original_admit=sa.admit_tool
    def observe_admit(db,study):
        original_admit(db,study)
        events.append({'phase':'complete_headroom_check_returned','transaction_active':db.in_transaction,
            'model_exhausted':sa.status(db,study)['model_allocation_exhausted'],'tool_exhausted':sa.status(db,study)['tool_allocation_exhausted']})
    monkeypatch.setattr(sa,'admit_tool',observe_admit)
    def reserve_only(root):
        assert events and events[0]['phase']=='complete_headroom_check_returned'
        commit_generated_peer_cost(kind)
        with sr._db() as db:state=sa.status(db,'producer')
        events.append({'phase':'peer_cost_committed_before_real_reserve','generated_only':True,'state':state})
        value,_=pe.reserve(root)
        events.append({'phase':'process_intent_reserved','intent':value})
        return {'native_launches':0}
    monkeypatch.setattr(pe,'supervise',reserve_only)
    blocked=False;error=None
    try:rp.dispatch(ledger.root)
    except AdmissionBlocked as exc:blocked=True;error=str(exc)
    with sr._db() as db:after=sa.status(db,'producer')
    evidence={'kind':kind,'events':events,'blocked':blocked,'error':error,'producer_process_intents':count_intents(),
        'producer_work_intent':rp.status(ledger.root)['record']['intent'],'allocation_after':after,
        'actual_models':0,'native_jobs':0,'accounts':0,'cost_records_are_generated_not_supplier_observations':True}
    (ledger.root/'committed_race_probe.json').write_text(serial(evidence),encoding='utf-8')
    assert blocked==(kind!='healthy') and evidence['producer_process_intents']==(1 if kind=='healthy' else 0),evidence
    assert evidence['producer_work_intent'] is None
    assert after['model_overrun']==(1 if kind=='model' else 0)
    assert after['tool_overrun']['wall_ms']==(1 if kind=='tool' else 0)

def test_producer_check_holds_canonical_write_lock_until_process_reservation(setup_producer,monkeypatch):
    ledger,_=mixed(setup_producer);original=sa.admit_tool;checks=[]
    def under_lock(db,study):
        original(db,study)
        assert db.in_transaction
        other=sqlite3.connect(sr.REGISTRY,timeout=.05,isolation_level=None)
        try:
            with pytest.raises(sqlite3.OperationalError,match='locked'):other.execute('BEGIN IMMEDIATE')
        finally:other.close()
        checks.append({'canonical_transaction_active':True,'competing_write_transaction_rejected':True})
    monkeypatch.setattr(sa,'admit_tool',under_lock)
    intent,_=pe.reserve(ledger.root)
    (ledger.root/'same_transaction_probe.json').write_text(serial({'checks':checks,'intent':intent,'actual_jobs':0}),encoding='utf-8')
    assert len(checks)==1 and count_intents()==1

def test_ordinary_process_reservation_keeps_existing_tool_exhaustion_closing_path(setup_producer):
    _,ordinary=mixed(setup_producer);commit_generated_peer_cost('tool')
    with sr._db() as db:state=sa.status(db,'producer')
    assert state['tool_allocation_exhausted'] and not state['process_allocation_exhausted']
    intent,_=pe.reserve(ordinary.root)
    assert intent['trial_id']=='ordinary' and count_intents('ordinary')==1 and count_intents()==0
    (ordinary.root/'ordinary_closing_reservation_probe.json').write_text(serial({'intent':intent,'state':state,'actual_jobs':0,
        'boundary':'Reservation remains possible; no model final or full closing run was executed.'}),encoding='utf-8')
