"""Scheduling-only maintenance and captured real ModelLoop context; no paid calls."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from quanta_agents.factor_campaign import campaign as module
from quanta_agents.factor_campaign.campaign import Campaign, once, read, sha
from quanta_agents.factor_campaign.combination import CombinationSpec
from quanta_agents.factor_campaign.protocol import default_protocol, digest
from quanta_agents.meta_v6.factors import FactorSpec
from quanta_agents.research_kernel.store import write_json


def bare_campaign(tmp_path):
    cfg = default_protocol(tmp_path / "source")
    once(tmp_path / "protocol.json", cfg)
    once(tmp_path / "protocol_identity.json", {"sha256": sha(tmp_path / "protocol.json")})
    state = {"version":"V10A","phase":"prepared","batch":0,"primary_evaluated":0,"combinations_evaluated":0,
             "new_evaluated":0,"reference_evaluated":0,"best_factor_floor":None,"best_combination_floor":None,
             "numeric_wall_seconds":0.,"numeric_cpu_seconds":0.,"stop_requested":False,"historical_target_met":False,
             "plateau_extensions":0,"failures":0}
    write_json(tmp_path / "state.json",state)
    for name,value in (("catalog.json",[]),("summaries.json",{}),("combination_summaries.json",{})):
        write_json(tmp_path / "versions/V10A" / name,value)
    write_json(tmp_path / "reference_catalog.json",[])
    return Campaign(tmp_path)


def evidence(spec=None, *, status="evaluated", value=.02):
    result={"direction":1,"direction_fit":{"raw_train_mean_pearson_ic":.03},"status":status,
            "annual":[{"year":year,"mean_pearson_ic":value,"valid_days":220,"evaluation_coverage":.91} for year in range(2019,2025)],
            "summary":{"mean_pearson_ic":value},"models_by_interval":[{"status":"fitted","fit_start":"2016-01-01",
            "fit_end":"2018-12-31","predict_start":"2019-01-02","predict_end":"2024-12-31",
            "train_days":680,"train_cells":70000,"sample_mask_id":"actual-training-mask","last_label_endpoint":"2018-12-28"}]}
    if spec is not None:result.update(spec=spec.to_dict(),combination_id=spec.combination_id)
    return result


def declarations(campaign,specs):
    path=campaign.version_root / "batches" / f"{campaign.state['batch']:04d}_combinations.json"
    once(path,[s.to_dict() for s in specs])
    return path


def test_frozen_execution_queue_preserves_specs_and_completed_history_on_resume(tmp_path,monkeypatch):
    from quanta_agents.factor_campaign import selection
    campaign=bare_campaign(tmp_path)
    specs=[CombinationSpec("registered",tuple(f"f{i}" for i in range(n)),ridge_lambda=regularizer)
           for n,regularizer in ((24,.001),(24,.01),(4,.1),(8,1.))]
    path=declarations(campaign,specs)
    original=path.read_bytes()
    completed={specs[0].combination_id:evidence(specs[0])}
    order=campaign._combination_execution(specs,completed,path)
    frozen_path=path.with_name("0000_combination_execution_v2.json")
    frozen=frozen_path.read_bytes()
    registered=read(frozen_path)
    assert registered["declaration_sha256"]==sha(path)
    assert registered["historical_completed_ids"]==[specs[0].combination_id]
    assert set(registered["ordered_combination_ids"])=={s.combination_id for s in specs}
    assert {s.combination_id:s.to_dict() for s in order}=={s.combination_id:s.to_dict() for s in specs}
    assert order[-1].combination_id==specs[0].combination_id
    # A new successful result must not recompute an already-frozen batch queue.
    completed[order[0].combination_id]=evidence(order[0])
    monkeypatch.setattr(selection,"execution_order",lambda *args:pytest.fail("Frozen order must not be recomputed"))
    resumed=Campaign(tmp_path)._combination_execution(specs,completed,path)
    assert [s.combination_id for s in resumed]==[s.combination_id for s in order]
    assert frozen_path.read_bytes()==frozen and path.read_bytes()==original


def test_scheduler_cannot_mutate_spec_metadata_even_if_id_stays_the_same(tmp_path,monkeypatch):
    from quanta_agents.factor_campaign import selection
    from dataclasses import replace
    campaign=bare_campaign(tmp_path)
    spec=CombinationSpec("original",("a","b","c","d"))
    path=declarations(campaign,[spec])
    monkeypatch.setattr(selection,"execution_order",lambda specs,reports:[replace(spec,name="silently renamed")])
    with pytest.raises(ValueError,match="contents"):
        campaign._combination_execution([spec],{},path)
    assert not path.with_name("0000_combination_execution_v2.json").exists()


def test_changed_original_declaration_fails_existing_execution_queue(tmp_path):
    campaign=bare_campaign(tmp_path)
    spec=CombinationSpec("original",("a","b","c","d"))
    path=declarations(campaign,[spec])
    campaign._combination_execution([spec],{},path)
    path.write_text(json.dumps([spec.to_dict()],indent=2),encoding="utf-8")
    with pytest.raises(ValueError,match="changed"):
        campaign._combination_execution([spec],{},path)


def test_later_batch_freezes_new_order_using_new_completed_coverage(tmp_path,monkeypatch):
    from quanta_agents.factor_campaign import selection
    campaign=bare_campaign(tmp_path)
    specs=[CombinationSpec("registered",tuple(f"f{i}" for i in range(n))) for n in (4,8,12,24)]
    calls=[]
    original=selection.execution_order
    def capture(specs,reports):calls.append(sorted(reports));return original(specs,reports)
    monkeypatch.setattr(selection,"execution_order",capture)
    first=campaign._combination_execution(specs,{},declarations(campaign,specs))
    campaign._state(batch=1)
    done={first[0].combination_id:evidence(first[0])}
    campaign._combination_execution(specs,done,declarations(campaign,specs))
    assert calls==[[],sorted(done)]
    assert (campaign.version_root/"batches/0000_combination_execution_v2.json").exists()
    assert (campaign.version_root/"batches/0001_combination_execution_v2.json").exists()


def test_actual_batch_uses_frozen_order_and_dense_control_does_not_consume_limit(tmp_path,monkeypatch):
    from quanta_agents.factor_campaign import selection,combination
    campaign=bare_campaign(tmp_path)
    reference_ids=[f"f{i}" for i in range(46)]
    write_json(campaign.root/"reference_catalog.json",[{"factor_id":fid} for fid in reference_ids])
    dense=CombinationSpec("dense",tuple(reference_ids),selection_rule="all_46_legacy_dense_control")
    ordinary=[CombinationSpec("ordinary",tuple(reference_ids[:n])) for n in (4,8,12)]
    specs=ordinary+[dense]
    path=declarations(campaign,specs)
    old_bytes=path.read_bytes()
    monkeypatch.setattr(selection,"execution_order",lambda specs,reports:[dense,*ordinary])
    monkeypatch.setattr(campaign,"context",lambda:SimpleNamespace())
    monkeypatch.setattr(campaign,"_resource_ready",lambda:True)
    monkeypatch.setattr(combination,"CombinationEvaluator",lambda *args,**kwargs:SimpleNamespace())
    for spec in specs:
        once(campaign.version_root/"combinations"/spec.combination_id/"report.json",evidence(spec))
    events=[]
    monkeypatch.setattr(campaign,"event",lambda kind,**values:events.append((kind,values)))
    campaign.combination_batch(limit=1)
    actual=[values["combination_id"] for kind,values in events if kind=="combination_evaluated"]
    assert actual==[dense.combination_id,ordinary[0].combination_id]
    assert campaign.state["combinations_evaluated"]==1
    assert campaign.state["combination_controls_evaluated"]==1 and campaign.state["combination_controls_attempted"]==1
    queue_bytes=(campaign.version_root/"batches/0000_combination_execution_v2.json").read_bytes()
    monkeypatch.setattr(selection,"execution_order",lambda *args:pytest.fail("Resume must use original frozen order"))
    campaign.combination_batch(limit=1)
    assert campaign.state["combinations_evaluated"]==2
    assert events[-1][1]["combination_id"]==ordinary[1].combination_id
    assert path.read_bytes()==old_bytes and (campaign.version_root/"batches/0000_combination_execution_v2.json").read_bytes()==queue_bytes


def test_dense_success_unavailable_and_exception_are_separate_control_counts(tmp_path):
    campaign=bare_campaign(tmp_path)
    refs=[f"f{i}" for i in range(46)]
    write_json(campaign.root/"reference_catalog.json",[{"factor_id":fid} for fid in refs])
    dense=[CombinationSpec("dense",tuple(refs),ridge_lambda=value,selection_rule="all_46_legacy_dense_control") for value in (.001,.01,.1)]
    normal=CombinationSpec("normal",tuple(refs[:4]))
    reports={dense[0].combination_id:evidence(dense[0]),dense[1].combination_id:evidence(dense[1],status="fit_unavailable"),normal.combination_id:evidence(normal)}
    write_json(campaign.version_root/"combination_summaries.json",reports)
    once(campaign.version_root/"failures"/(dense[2].combination_id+".json"),{"stage":"numeric_combination","spec":dense[2].to_dict(),"error":"synthetic failure"})
    before=(campaign.version_root/"combination_summaries.json").read_bytes()
    campaign._recount()
    assert campaign.state["combinations_evaluated"]==1
    assert campaign.state["combination_controls_evaluated"]==1 and campaign.state["combination_controls_attempted"]==3
    assert (campaign.version_root/"combination_summaries.json").read_bytes()==before


def review_fixture(campaign):
    rows=[]
    for i in range(48):
        spec=FactorSpec(f"source_{i}",f"pct_change(close, {i+2})",parents=("documented_ancestor",),metadata={"source_id":f"library_{i}","omitted_long_source":"original provenance"})
        rows.append({"factor_id":spec.factor_id,"spec":spec.to_dict(),"roles":["condition" if i>=46 else "return"],
                     "route":"condition" if i>=46 else "quality","parents":["documented_ancestor"],
                     "source":{"path":"fixture-source.json","sha256":"fixture-source-hash"},"mechanism":"documented causal mechanism","origin":"reference" if i<46 else "new","entity_type":"single_factor",
                     "lineage":{"transformation_kind":"raw_formula","parents":["documented_ancestor"]}})
    refs=[r["factor_id"] for r in rows[:46]]
    good=CombinationSpec("quality4",tuple(refs[:4]),ridge_lambda=.001)
    duplicate=CombinationSpec("same4",tuple(refs[:4]),ridge_lambda=.01)
    dense=CombinationSpec("dense46",tuple(refs),selection_rule="all_46_legacy_dense_control")
    failed=CombinationSpec("failed8",tuple(refs[:8]))
    pending=CombinationSpec("pending12",tuple(refs[:12]),target="rank_return_demeaned",update_rule="quarterly_expanding")
    declarations(campaign,[good,duplicate,dense,failed,pending])
    write_json(campaign.root/"reference_catalog.json",rows[:46])
    write_json(campaign.version_root/"catalog.json",rows)
    factors={row["factor_id"]:evidence() for row in rows}
    increment_id=rows[-2]["factor_id"]
    increment_path=campaign.version_root/"batches/0000_increment"/(increment_id+".json")
    factors[increment_id].update(complementarity_checked=True,complementarity_passed=True,complementarity_delta=.006,
                                 complementarity_evidence=str(increment_path),sample_mask_id="WRONG_FACTOR_MASK")
    folds=[{"status":"evaluated","valid_days":100,"sample_mask_id":f"actual-common-fold-{i}","paired_delta_pearson_ic":.006,
            "baseline_id":"baseline","augmented_id":"augmented","models":{"baseline_common":[{"status":"fitted","sample_mask_id":f"actual-fit-common-{i}"}]}} for i in (1,2)]
    once(increment_path,{"factor_id":increment_id,"passed":True,"mean_delta":.006,"base_ids":refs[:4],"inner_baseline_ids":refs[:3],
                         "folds":folds,"exposed_history_increment":{"status":"evaluated","sample_mask_id":"exposed-common","paired_delta_pearson_ic":-.01}})
    write_json(campaign.version_root/"summaries.json",factors)
    good_report=evidence(good)
    duplicate_report={**evidence(duplicate),"numeric_duplicate_of":good.combination_id}
    dense_report=evidence(dense,status="fit_unavailable",value=None)
    dense_report["models_by_interval"]=[{"status":"unavailable","reason":"insufficient common training days/cells","fit_start":"2016-01-01","fit_end":"2018-12-31","predict_start":"2019-01-02","predict_end":"2024-12-31"}]
    reports={good.combination_id:good_report,duplicate.combination_id:duplicate_report,dense.combination_id:dense_report}
    for cid,report in reports.items():once(campaign.version_root/"combinations"/cid/"report.json",report)
    write_json(campaign.version_root/"combination_summaries.json",{cid:{k:v for k,v in report.items() if k!="models_by_interval"} for cid,report in reports.items()})
    once(campaign.version_root/"failures"/(failed.combination_id+".json"),{"stage":"numeric_combination","spec":failed.to_dict(),"error":"synthetic numerical error"})
    calibration=campaign.root/"verification/combination_calibration_fixture"
    once(calibration/"summary.json",{"study_counted":False,"results":[{"member_count":46,"combination_id":dense.combination_id,"status":"fit_unavailable"}]})
    once(calibration/dense.combination_id/"report.json",dense_report)
    return rows,good,dense,failed,pending,increment_id


def test_review_captures_rich_context_through_actual_model_loop_and_saved_request(tmp_path,monkeypatch):
    from quanta_agents.factor_campaign import model as model_module
    campaign=bare_campaign(tmp_path)
    rows,good,dense,failed,pending,increment_id=review_fixture(campaign)
    original_loop=model_module.ModelLoop
    received=[]
    answer={"answer":"Synthetic captured engineering review", "evidence_ids":[good.combination_id]}
    response={"kind":"review",**{k:answer for k in ("failure_analysis","framework_diagnosis","proposed_improvement","cross_version_comparison")},
              "next_action":"extend","proposed_changes":[],"falsifier":"Synthetic fixture"}
    class Transport:
        def run(self,**kwargs):
            received.append(kwargs["prompt"])
            write_json(kwargs["workdir"]/"synthetic_response.json",response)
    def verifier(folder,**kwargs):
        return {"response":read(folder/"synthetic_response.json"),"model":"gpt-6-astra","effort":"xhigh",
                "runtime_identity":{"verified":True},"usage":{"input_tokens":1,"output_tokens":1}}
    class CapturingLoop(original_loop):
        def __init__(self,root):super().__init__(root,verifier=verifier)
        def request(self,action,kind,context):return super().request(action,kind,context,gateway=Transport())
    monkeypatch.setattr(model_module,"ModelLoop",CapturingLoop)
    campaign.review()
    request_path=campaign.version_root/"decisions/V10A_batch0000_review.request.json"
    context=read(request_path)["context"]
    assert len(received)==1 and "actual-common-fold-1" in received[0] and "WRONG_FACTOR_MASK" not in received[0]
    leading=next(iter(context["leading_factors"].values()))
    assert leading["spec"]["expression"] and leading["name"] and leading["roles"] and leading["route"]
    assert leading["parents"]==["documented_ancestor"] and leading["source"]["sha256"]=="fixture-source-hash"
    assert leading["entity_type"]=="single_factor" and leading["lineage"]["transformation_kind"]=="raw_formula"
    parent_ids={p["parent_id"] for p in context["selected_parents"]}
    condition_id=rows[-1]["factor_id"]
    assert condition_id in parent_ids and condition_id not in context["leading_factors"]
    assert context["factor_definitions"][condition_id]["roles"]==["condition"]
    assert all(fid in context["factor_definitions"] for fid in parent_ids) and not context["missing_factor_definitions"]
    assert all(fid in context["factor_definitions"] for row in context["factor_definitions"].values() for fid in row["lineage"]["parent_definition_refs"])
    assert context["cross_version_evidence"]["status"]=="unavailable" and "V9A" in context["cross_version_evidence"]["comparison_limit"]
    combination=context["leading_combinations"][good.combination_id]
    assert combination["spec"]==good.to_dict()
    assert set(combination["member_definition_refs"])==set(good.feature_ids)
    assert all(context["factor_definitions"][fid]["spec"]["expression"] for fid in good.feature_ids)
    assert combination["fit_availability"]["interval_count"]==1
    assert combination["fit_availability"]["intervals"][0]["sample_mask_id"]=="actual-training-mask"
    coverage=context["combination_coverage"]
    assert coverage["outcomes"]=={"successful":1,"duplicate":1,"fit_unavailable":1,"implementation_failed":1,"pending":1}
    assert coverage["distinct_member_sets"]==4 and coverage["ordinary_successful"]==1
    assert {r["size"] for r in coverage["dimensions"]}=={4,8,12,46}
    assert any(r["target"]=="rank_return_demeaned" and r["update"]=="quarterly_expanding" and r["pending"]==1 for r in coverage["dimensions"])
    controls=context["combination_controls"]
    assert len(controls)==2 and any(r["scope"]=="calibration_not_study_counted" and r["study_counted"] is False for r in controls)
    assert all(r["fit_availability"]["failure_reasons"]=={"insufficient common training days/cells":1} for r in controls)
    paired=context["complementarity_evidence"][increment_id]
    assert paired["common_sample_ids"]==["actual-common-fold-1","actual-common-fold-2"] and paired["source"]["sha256"]
    assert paired["exposed_history_increment"]["paired_delta_pearson_ic"]==-.01
    saved=request_path.read_bytes()
    print("review_context_utf8_bytes="+str(len(json.dumps(context,ensure_ascii=False,allow_nan=False).encode("utf-8"))))
    campaign.review()
    assert request_path.read_bytes()==saved and len(received)==1  # Already applied review has no second call.


def test_previous_version_snapshots_keep_latest_two_actual_counts_costs_and_unknowns(tmp_path):
    campaign=bare_campaign(tmp_path)
    for number in range(7,10):
        snapshot={"state":{"version":f"V{number}A","updated_utc":f"2026-09-{number:02d}T00:00:00+00:00",
                  "primary_evaluated":300,"new_evaluated":254,"combinations_evaluated":200,"best_factor_floor":.02,
                  "best_combination_floor":.04,"numeric_wall_seconds":100.*number,"numeric_cpu_seconds":80.*number},
                  "scale_completed":True,"cost":{"known_total_tokens":number*1000,"currency_cost":None,"unknown_usage_calls":1}}
        once(campaign.root/f"versions/V{number}A/framework_close_snapshot.json",snapshot)
    # The active version's checkpoint cannot masquerade as prior-version evidence.
    once(campaign.version_root/"framework_close_snapshot.json",{"state":{"version":"V10A"},"scale_completed":False})
    previous=campaign._review_previous_versions()
    assert previous["status"]=="available" and [r["version"] for r in previous["previous_versions"]]==["V9A","V8A"]
    for row in previous["previous_versions"]:
        assert row["source"]["sha256"]==sha(row["source"]["path"])
        assert row["scale_completed"] and row["counts"]["new_evaluated"]==254
        assert row["counts"]["combination_controls_attempted"] is None
        assert row["cumulative_cost_at_close"]["currency_cost"] is None and row["cumulative_cost_at_close"]["unknown_usage_calls"]==1
        assert row["best_factor_floor"]==.02 and row["numeric_wall_seconds"]


def test_runtime_failed_dense_control_is_visible_as_failure_not_unattempted(tmp_path):
    campaign=bare_campaign(tmp_path)
    rows,good,dense,failed,pending,increment_id=review_fixture(campaign)
    reports=read(campaign.version_root/"combination_summaries.json")
    from dataclasses import replace
    broken=replace(dense,ridge_lambda=.01)
    once(campaign.version_root/"failures"/(broken.combination_id+".json"),{"stage":"numeric_combination","spec":broken.to_dict(),"error":"synthetic runtime failure"})
    context=campaign._review_combinations(reports,{row["factor_id"]:row for row in rows},[r["factor_id"] for r in rows[:46]],[])
    control=next(r for r in context["controls"] if r["combination_id"]==broken.combination_id)
    assert control["status"]=="implementation_failed" and control["failure"]["error"]=="synthetic runtime failure"
    assert control["failure"]["source"]["sha256"] and control["fit_availability"]["recorded"] is False


def test_recursive_lineage_and_large_legacy_sources_use_one_resolvable_definition_table(tmp_path):
    campaign=bare_campaign(tmp_path)
    marker="DO_NOT_INLINE_LEGACY_TABLE_"*6000
    legacy_source={"kind":"legacy_inventory", "source_id":"old.source", "path":"retained-inventory.json",
                   "sha256":"retained-original-sha", "prior_results":[marker]}
    grandparent=FactorSpec("grandparent","pct_change(close, 20)",metadata={"source":legacy_source,"old_table":marker})
    parent=FactorSpec("parent","pct_change(close, 10)",parents=(grandparent.factor_id,),
                      metadata={"source":legacy_source,"lineage":{"transformation_kind":"raw_formula","parent_definitions":[grandparent.to_dict()]}})
    children=[FactorSpec("child"+str(i),f"pct_change(close, {i})",parents=(parent.factor_id,),metadata={"old_table":marker}) for i in (2,3)]
    rows=[{"factor_id":spec.factor_id,"spec":spec.to_dict(),"source":legacy_source,"parents":[parent.factor_id],
           "entity_type":"single_factor","lineage":{"transformation_kind":"conditional_interaction","supervised":False,
           "matched_registered_ids":[parent.name],"parent_definitions":[parent.to_dict()]}} for spec in children]
    write_json(campaign.version_root/"catalog.json",rows)
    known={row["factor_id"]:row for row in rows}
    original=deepcopy(known)
    definitions=campaign._review_definitions(known,set(known))
    assert set(definitions)=={s.factor_id for s in [*children,parent,grandparent]} and known==original
    serialized=json.dumps(definitions,ensure_ascii=False)
    assert "DO_NOT_INLINE_LEGACY_TABLE" not in serialized and "parent_definitions\"" not in serialized
    for definition in definitions.values():
        assert "metadata" not in definition["spec"]
        assert all(fid in definitions for fid in definition["lineage"]["parent_definition_refs"])
        assert definition["source"]["path"]=="retained-inventory.json" and definition["source"]["sha256"]=="retained-original-sha"
        assert definition["source"]["record_sha256"]==digest(legacy_source)
    assert definitions[grandparent.factor_id]["registration_locator"]["owner_definition_ref"]==parent.factor_id
    assert definitions[parent.factor_id]["lineage"]["parent_definition_refs"]==[grandparent.factor_id]
    assert definitions[children[0].factor_id]["lineage"]["transformation_kind"]=="conditional_interaction"
