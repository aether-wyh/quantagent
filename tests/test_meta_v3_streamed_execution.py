"""Generated accounting paths; never independent market/strategy evidence."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from quanta_agents.meta_v3.kernel import ROOT, module
from quanta_agents.meta_v3 import saved_execution as streamed


def inputs(tmp_path, count=260):
    days = list(pd.bdate_range("2019-01-02", periods=count).strftime("%Y-%m-%d"))
    codes = ["sh600004", "sh600006"]
    artifacts, obligations, targets = [], [], []
    for code in codes:
        root = tmp_path / code
        root.mkdir(parents=True)
        rows = [{"code":code,"date":day,"raw_open":10.,"raw_close":10.,"raw_prev_close":10.,
            "raw_price_text":{"raw_open":"10.00","raw_close":"10.00","raw_prev_close":"10.00"},
            "volume":10000000,"stock_name":"Generated engineering stock","execution_valid":False}
            for day in days]
        raw = gzip.compress(json.dumps(rows).encode(), mtime=0)
        manifest = json.dumps({"codes":[code],"execution_valid":False,"adjusted_price_or_factor_inversion_used":False}).encode()
        (root/"rows.json.gz").write_bytes(raw); (root/"manifest.json").write_bytes(manifest)
        artifacts.append({"code":code,"root":str(root.resolve()),"rows_file":"rows.json.gz",
            "rows_sha256":hashlib.sha256(raw).hexdigest(),"manifest_file":"manifest.json",
            "manifest_sha256":hashlib.sha256(manifest).hexdigest()})
        for i, day in enumerate(days):
            obligations.extend({"code":code,"date":day,"kind":kind,"status":"fixture_complete",
                "evidence_sha256":"f"*64,"note":"Generated accounting check only"} for kind in streamed.KINDS)
            if i:
                targets.append({"symbol":code,"signal_date":days[i-1],"trade_date":day,
                    "available_at":days[i-1]+"T15:10:00+08:00",
                    "target_weight":"0.4" if i%2 and i<count-1 else "0"})
    return {"identity":{"run_id":"test","architecture":"engineering","observation_id":"ledger",
                "strategy_hash":"1"*64,"data_hash":"2"*64,"source_hash":"3"*64},
            "codes":codes,"calendar":days,"targets":targets,"source_artifacts":artifacts,
            "obligations":obligations,"initial_cash":"1000000.00","fixture_only":True}


def run(root, engine, values):
    plan = engine.freeze_saved_research_plan(**values)
    job = engine.SavedRawResearch.create(root, plan)
    return job, plan, job.execute_saved(expected_plan_sha256=plan["plan_sha256"])


def test_streamed_matches_frozen_kernel_and_recovery_never_reexecutes(tmp_path, monkeypatch):
    values = inputs(tmp_path/"inputs", 12)
    old = module("raw_saved_research")
    _, _, original = run(tmp_path/"original", old, values)
    job, plan, new = run(tmp_path/"streamed", streamed, values)
    assert original["status"] == new["status"] == "completed_mechanical"
    assert new["result"] == original["result"]
    assert new["resource_usage"]["persisted_payload_bytes"] < original["resource_usage"]["persisted_payload_bytes"]
    monkeypatch.setattr(streamed, "simulate_streamed_portfolio", lambda **k: pytest.fail("repeated simulation"))
    monkeypatch.setattr(streamed, "_load_saved", lambda *a: pytest.fail("reopened prices during recovery"))
    assert job.reconcile_saved_only(expected_plan_sha256=plan["plan_sha256"]) == new


def test_260_generated_sessions_keep_one_capital_deposit_and_all_losses(tmp_path):
    values = inputs(tmp_path/"inputs")
    _, _, result = run(tmp_path/"streamed", streamed, values)
    assert result["status"] == "completed_mechanical", result.get("error")
    r = result["result"]
    assert len(r["daily"]) == 260 and r["calendar"] == values["calendar"]
    assert sum(e["event"]["kind"] == "cash_deposit" for e in r["journal"]) == 1
    assert r["final_snapshot"]["external_cash_flow"] == "1000000.00"
    assert len(r["trades"]) > 500 and float(r["final_snapshot"]["cash"]) < 1000000
    assert all(float(day["cash_available"]) >= 0 for day in r["daily"])
    assert r["daily"][-1]["holdings"] == {}
    assert result["resource_usage"]["persisted_payload_bytes"] < 12*1024**2
    assert result["execution_valid"] is False


@pytest.mark.parametrize("commit_ack_lost", [False, True])
def test_interrupted_event_preserves_uncertainty_or_committed_prefix(tmp_path, monkeypatch, commit_ack_lost):
    values = inputs(tmp_path/"inputs", 12)
    plan = streamed.freeze_saved_research_plan(**values)
    job = streamed.SavedRawResearch.create(tmp_path/"streamed", plan)
    append = job._append
    def interrupted(kind, payload):
        if kind == "checkpoint" and payload["phase"] == "event_applied" and payload["event"]["kind"] == "buy_fill":
            if commit_ack_lost:
                append(kind, payload)
            raise OSError("injected persistence interruption")
        return append(kind, payload)
    monkeypatch.setattr(job, "_append", interrupted)
    result = job.execute_saved(expected_plan_sha256=plan["plan_sha256"])
    assert result["status"] == "failed" and result["result"] is None
    assert bool(result["pending_event_intent"]) is not commit_ack_lost
    assert result["partial"]["snapshot"]["external_cash_flow"] == "1000000.00"
    assert result["partial"]["snapshot"]["event_count"] == (2 if commit_ack_lost else 1)
    assert result["valuation_complete_through"] == values["calendar"][0]
    monkeypatch.setattr(streamed, "simulate_streamed_portfolio", lambda **k: pytest.fail("repeated simulation"))
    monkeypatch.setattr(streamed, "_load_saved", lambda *a: pytest.fail("reopened source"))
    assert job.reconcile_saved_only(expected_plan_sha256=plan["plan_sha256"]) == result


def test_unknown_action_on_day_40_preserves_existing_inventory(tmp_path):
    values = inputs(tmp_path/"inputs", 50)
    # Buy before the missing obligation and retain risk until the blocked day.
    for target in values["targets"]:
        if target["trade_date"] >= values["calendar"][37] and target["trade_date"] < values["calendar"][-1]:
            target["target_weight"] = "0.4"
    for row in values["obligations"]:
        if row["date"] == values["calendar"][40] and row["kind"] == "corporate_actions":
            row["status"] = "unknown"
    _, _, result = run(tmp_path/"streamed", streamed, values)
    assert result["status"] == "failed" and result["result"] is None
    assert result["valuation_complete_through"] == values["calendar"][39]
    assert result["partial"]["progress"]["daily"][-1]["holdings"]
    assert result["partial"]["snapshot"]["external_cash_flow"] == "1000000.00"


def test_cash_dividend_and_deferred_tax_match_frozen_accounting(tmp_path):
    values = inputs(tmp_path/"inputs", 12)
    days = values["calendar"]
    adapter = module("corporate_action_adapter")
    values["corporate_actions"] = [adapter.CashDividendAnnouncement(
        action_id="generated-cash", symbol=values["codes"][0], announcement_date=days[2],
        record_date=days[5], ex_date=days[6], cash_payment_date=days[6], gross_cash_per_share="0.17",
        short_holding_tax_rate="0.20", tax_rule=adapter.SUPPORTED_TAX_RULE, account_type=adapter.ACCOUNT_TYPE,
        stock_distribution_per_share="0", stock_distribution_kind="none", rights_issue=False,
        implementation_status="implementation_notice", source_url="fixture://explicit-generated-event",
        source_sha256="a"*64, source_fetched_at="2026-09-07T00:00:00+00:00", facts_verified=True)]
    _, _, original = run(tmp_path/"original", module("raw_saved_research"), values)
    _, _, result = run(tmp_path/"streamed", streamed, values)
    assert result["status"] == original["status"] == "completed_mechanical"
    assert result["result"] == original["result"]
    kinds = {entry["event"]["kind"] for entry in result["result"]["journal"]}
    assert {"cash_dividend_paid", "tax_assessed", "tax_paid", "activate_entitlement"} <= kinds
    assert any(float(day["cash_receivable_gross"]) > 0 for day in result["result"]["daily"])


def test_real_entry_requires_explicit_long_backend_and_returns_full_account_summary(tmp_path):
    from quanta_agents.meta_v3.research_tools import ResearchTools
    from quanta_agents.meta_v3.ledger import AdmissionBlocked
    values = inputs(tmp_path/"inputs", 50)
    for row in values["obligations"]:
        row["status"] = "documented_scope" if row["kind"] == "corporate_actions" else "declared_simulation"
    cells, eligibility = [], []
    for day in values["calendar"]:
        for code in values["codes"]:
            metadata = {"session":day,"symbol":code,"available_at":day+"T15:05:00+08:00",
                "effective_at":day+"T15:05:00+08:00","source_evidence_id":"e"*64}
            cells.append({**metadata,"field":"close","value":10.})
            eligibility.append({**metadata,"eligible":True})
    case = {"research_class":"real_saved_development","description":"Generated engineering stand-in only",
        "initial_cash":"1000000.00","decision_fixture":{"kind":"exposed_real_decision_table",
            "codes":values["codes"],"calendar":values["calendar"],"fields":[{"name":"close","unit":"CNY"}],
            "field_rows":cells,"eligibility_rows":eligibility},
        "raw_source_bindings":{k:values[k] for k in ("source_artifacts", "obligations")}}
    with pytest.raises(AdmissionBlocked, match="explicit streamed"):
        ResearchTools(tmp_path/"old", "test", case, [])
    case["execution_backend"] = "v3_streamed_001"
    tools = ResearchTools(tmp_path/"stage", "test", case, [])
    result = tools.execute("candidate", "develop_strategy", {"program":{
        "version":"factor_strategy_program_v1","factors":[],"target_weight_expression":"0.4",
        "hypothesis":"Generated arithmetic path","applicability":["Engineering only"],"invalidation_conditions":["Wrong accounting"]}})
    assert result["public"]["raw_status"] == "completed_mechanical"
    summary = result["public"]["account_summary"]
    assert summary["cash_days_including_no_position_days"] == 50
    assert float(summary["net_return_on_full_initial_cash"]) < 0
    assert "partial" in summary["order_status_counts"] or "filled" in summary["order_status_counts"]
