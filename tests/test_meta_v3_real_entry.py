"""Engineering generated inputs exercise the real adapter; no market inference."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from quanta_agents.meta_v3 import real_program
from quanta_agents.meta_v3.kernel import ROOT
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from quanta_agents.meta_v3.research_tools import ResearchTools

spec=importlib.util.spec_from_file_location("fixture_real_entry",ROOT/"scripts/prepare_v3_calibration.py")
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)


def case(tmp_path):
    value=fixture.prepare(tmp_path/"data",flat=True)
    # Deliberately declared engineering stand-in, never registered as research.
    value["research_class"]="real_saved_development"
    value["decision_fixture"]["kind"]="exposed_real_decision_table"
    value["description"]="Engineering generated stand-in for real-adapter contracts"
    for row in value["raw_source_bindings"]["obligations"]:
        row["status"]="documented_scope" if row["kind"]=="corporate_actions" else "declared_simulation"
        row["note"]="Generated engineering fixture; not real evidence"
    return value


def program():
    return {"version":"factor_strategy_program_v1","factors":[],"target_weight_expression":"where(close > 0, 0.4, 0)",
        "hypothesis":"Engineering only","applicability":["Generated input"],"invalidation_conditions":["Wrong cash or timing"]}


def test_real_path_keeps_source_class_full_cash_and_costs(tmp_path):
    data=case(tmp_path)
    tools=ResearchTools(tmp_path/"stage","unit",data,[])
    result=tools.execute("trial","develop_strategy",{"program":program()})
    assert result["public"]["raw_status"]=="completed_mechanical"
    assert result["public"]["full_initial_cash"]=="10000.00"
    assert float(result["public"]["cash_summary"]["final_cash"])<10000
    assert all(x==0 for x in result["public"]["cash_summary"]["positions"].values())
    import json
    plan=json.loads((tmp_path/"stage/tools/unit/trial/workbench/raw_children/program/plan.json").read_text())
    assert plan["fixture_only"] is False and plan["execution_valid"] is False
    assert not any(x["status"]=="fixture_complete" for x in plan["obligations"])


def test_late_and_future_real_fields_do_not_backfill_past_decisions(tmp_path):
    data=case(tmp_path)["decision_fixture"]
    compiled=real_program.validate_program(program(),public_field_contract=data["fields"])
    def run(d):return real_program.build_targets(compiled,decision_fixture=d,frozen_policy=real_program.POLICY)
    original=run(data)
    changed=deepcopy(data)
    for row in changed["field_rows"]:
        if row["session"]==data["calendar"][-1] and row["field"]=="close":row["value"]=0
    assert run(changed)["targets"]==original["targets"]
    for row in changed["field_rows"]:
        if row["session"]==data["calendar"][0] and row["field"]=="close":row["available_at"]=row["session"]+"T15:11:00+08:00"
    late=run(changed)
    assert all(x["target_weight"]=="0" for x in late["targets"][:2])
    assert any(x["reason"]=="after_decision_cutoff" for x in late["masked_inputs"])


def test_real_path_refuses_fixture_certification_and_unknown_actions(tmp_path):
    data=case(tmp_path)
    bad=deepcopy(data);bad["raw_source_bindings"]["obligations"][0]["status"]="fixture_complete"
    with pytest.raises(AdmissionBlocked):ResearchTools(tmp_path/"bad","unit",bad,[])
    data["raw_source_bindings"]["obligations"][0]["status"]="unknown"
    tools=ResearchTools(tmp_path/"stage","unit",data,[])
    result=tools.execute("trial","develop_strategy",{"program":program()})
    assert result["public"]["raw_status"]=="failed"
    assert result["public"]["final_snapshot"] is None
    assert result["formal_target_success"] is False
