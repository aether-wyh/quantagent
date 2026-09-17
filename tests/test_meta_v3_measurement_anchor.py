"""029-C01: deleted canonical receipts must not become legacy projections."""
from copy import deepcopy
import json
import shutil
import sqlite3

import pytest

from quanta_agents.meta_v3 import study_registry as sr, tool_resources as tr, tool_measurements as tm
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from test_meta_v3_tool_resources import setup, reply


def test_lost_anchors_cannot_use_projected_metrics_as_authority(setup,tmp_path,monkeypatch):
    runtime,task=setup()
    original=reply(runtime,task,'inspect_inputs',{'table':'fields','offset':0,'limit':32})
    assert original['status']=='applied'
    # A second generated receipt supplies a distinct pending tool intent. It
    # does not execute the producer; corruption variants share this same seed.
    next_call=reply(runtime,task,'inspect_inputs',{'table':'coverage','offset':0,'limit':32},apply=False)
    runtime.ledger.begin_apply(next_call['id'])
    tools=runtime._tools('test');canonical=sr.REGISTRY
    model_probe=deepcopy(next_call['intent']);model_probe['intent_id']+='_probe'
    all_results=[]
    for corruption in ('missing_row','missing_table','missing_row_zero_projection'):
        variant=tmp_path/(corruption+'.sqlite3');shutil.copyfile(canonical,variant)
        with sqlite3.connect(variant) as db:
            if corruption=='missing_table':
                db.execute('ALTER TABLE tool_measurements RENAME TO preserved_tool_measurements')
            else:
                db.execute('CREATE TABLE preserved_tool_measurements AS SELECT * FROM tool_measurements')
                db.execute('DELETE FROM tool_measurements WHERE id=?',(original['id'],))
                if corruption=='missing_row_zero_projection':
                    db.execute('UPDATE tool_actions SET metrics=? WHERE id=?',
                        (json.dumps(dict.fromkeys(tr.MEASURED,0)),original['id']))
        probes={
            'trial_status':lambda:tr.status(runtime.root),
            'study_status':lambda:sr.snapshot('tools'),
            'startup_recovery':lambda:tm.reconcile_available(runtime.root),
            'tool_reservation':lambda:tr._reserve(tools,next_call['id'],'inspect_inputs',{'table':'coverage','offset':0,'limit':32}),
            'model_reservation':lambda:sr.reserve_model(runtime.root,model_probe,80)}
        with monkeypatch.context() as patch:
            patch.setattr(sr,'REGISTRY',variant)
            for name,probe in probes.items():
                try:
                    probe();outcome={'blocked':False,'error':None}
                except AdmissionBlocked as exc:
                    outcome={'blocked':'measurement' in str(exc) and ('missing' in str(exc) or 'required' in str(exc)), 'error':str(exc)}
                except Exception as exc:
                    outcome={'blocked':False,'error':type(exc).__name__+': '+str(exc)}
                all_results.append({'corruption':corruption,'probe':name,**outcome})
    (tmp_path/'anchor_probe_summary.json').write_text(json.dumps(all_results,indent=2),encoding='utf-8')
    assert all(r['blocked'] for r in all_results),all_results
    assert tr.status(runtime.root)['used']['actions']==1


def test_new_registration_cannot_request_legacy_measurement_protocol(setup,monkeypatch):
    original=sr.freeze
    def downgraded(plan):
        plan=deepcopy(plan);plan['trials'][0]['measurement_protocol']=None
        return original(plan)
    monkeypatch.setattr(sr,'freeze',downgraded)
    with pytest.raises(AdmissionBlocked,match='requires original measurement protocol'):setup()
    assert not sr.REGISTRY.exists()


def test_removing_protocol_from_frozen_spec_cannot_downgrade_stage(setup):
    runtime,_=setup()
    with sqlite3.connect(sr.REGISTRY) as db:
        spec=json.loads(db.execute('SELECT spec FROM trials').fetchone()[0]);spec.pop('measurement_protocol')
        db.execute('UPDATE trials SET spec=?',(json.dumps(spec),))
    with pytest.raises(AdmissionBlocked,match='trial specification drift'):tr.status(runtime.root)


def test_legacy_projection_fixture_is_visible_but_read_only(setup,tmp_path):
    # Explicitly generated old-format projection, not an old paid experiment.
    from quanta_agents.meta_v3.ledger import digest,serial
    from test_meta_v3_study_allocation import proposal,create
    from test_meta_v3_ledger import A,request
    plan,tasks,pins=proposal(tmp_path);sr.freeze(plan)
    with sqlite3.connect(sr.REGISTRY) as db:
        old=json.loads(db.execute('SELECT plan FROM studies').fetchone()[0])
        for t in old['trials']:
            t.pop('measurement_protocol')
            db.execute('UPDATE trials SET spec=? WHERE id=?',(serial(t),t['id']))
        semantic=sorted([{k:v for k,v in t.items() if k not in ('id','root')} for t in old['trials']],key=serial)
        db.execute('UPDATE studies SET plan=?,plan_hash=?,semantic_hash=?',(serial(old),digest(old),digest(semantic)))
    job=create(plan,tasks,pins,0)
    metrics={'wall_ms':1,'controller_cpu_ms':1,'retained_output_bytes':16}
    with sqlite3.connect(sr.REGISTRY) as db:
        db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',('allocated','t0','legacy','a'*64,80,20,'b'*64))
        db.execute('INSERT INTO tool_actions VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            ('allocated','t0','legacy','one','inspect_inputs','c'*64,serial({'actions':1,'candidates':0,'scan_cells':0,'comparisons':0}),0.,serial(metrics),'returned','d'*64))
    state=tr.status(job.root)
    assert state['measurement_protocol'] is None and not state['measurement_protocol_current']
    assert state['used']['retained_output_bytes']==16 and tr.allowed(job.root,A)==()
    assert tm.reconcile_available(job.root)['legacy_read_only'] is True
    with pytest.raises(AdmissionBlocked,match='legacy_measurement_scope_read_only'):job.reserve('one',A,request)
    with pytest.raises(AdmissionBlocked,match='legacy measurement scope is read-only'):tm.reconcile(job.root,'legacy')
    with pytest.raises(AdmissionBlocked,match='legacy measurement scope is read-only'):tr._settle(job.root,'legacy',metrics,'returned','d'*64)
    assert sr.snapshot('allocated')['known_tokens']==20
    with sqlite3.connect(sr.REGISTRY) as db:
        assert 'measurement_protocol' not in json.loads(db.execute("SELECT spec FROM trials WHERE id='t0'").fetchone()[0])
        assert db.execute('SELECT count(*) FROM calls').fetchone()[0]==1
