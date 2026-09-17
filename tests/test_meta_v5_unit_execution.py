"""Generated engineering fixtures exercise continuous real-backend unit ledgers.

No model calls or real market conclusions. Year-boundary data verify that cash,
fees and shares continue across years without a synthetic allocation of PnL.
"""
from copy import deepcopy
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from quanta_agents.meta_v3.ledger import digest, serial
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v5 import unit_execution as ue
from quanta_agents.meta_v5.analytics import compare_profiles
from quanta_agents.meta_v5.registry import Catalog, prepare_catalog, write_catalog
from quanta_agents.meta_v5.runtime import validate_task_contract
from quanta_agents.meta_v5.tools import V5ResearchTools, ACTIONS
from test_meta_v3_real_entry import case as generated_case
from test_meta_v5_execution_adapter import policy as base_policy, record


def unit_policy(case, runs=8):
    return {"version": ue.VERSION, "codes": case["decision_fixture"]["codes"],
        "initial_cash_per_account": case["initial_cash"], "weight_policy": "preserve_original_weights_zero_other_targets",
        "max_account_runs_total": runs, "max_wall_seconds_per_profile": 60,
        "max_wall_seconds_total": 180, "max_retained_bytes": 32 * 1024**2}


def program(weight="0.4"):
    return {"version": "factor_strategy_program_v1", "factors": [], "target_weight_expression": weight,
            "hypothesis": "Generated engineering arithmetic", "applicability": ["Generated fixture"],
            "invalidation_conditions": ["Unknown account or changed capital"]}


def crossed_case(tmp_path):
    case = generated_case(tmp_path)
    case["execution_backend"] = "v3_streamed_001"
    case["archive_storage_policy"] = {"version": "zlib_records_v1"}
    old = case["decision_fixture"]["calendar"]
    new = list(pd.bdate_range("2018-12-24", periods=len(old)).strftime("%Y-%m-%d"))
    mapping = dict(zip(old, new))
    case["decision_fixture"]["calendar"] = new
    for table in ("field_rows", "eligibility_rows"):
        for row in case["decision_fixture"][table]:
            row["session"] = mapping[row["session"]]
            for key in ("effective_at", "available_at"):
                row[key] = mapping[row[key][:10]] + row[key][10:]
    for row in case["raw_source_bindings"]["obligations"]:
        row["date"] = mapping[row["date"]]
    for item in case["raw_source_bindings"]["source_artifacts"]:
        path = Path(item["root"]) / item["rows_file"]
        rows = json.loads(gzip.decompress(path.read_bytes()))
        for row in rows:
            row["date"] = mapping[row["date"]]
        payload = gzip.compress(serial(rows).encode(), mtime=0)
        path.write_bytes(payload)
        item["rows_sha256"] = hashlib.sha256(payload).hexdigest()
    return case


def test_mask_preserves_full_cross_section_and_calendar(tmp_path):
    case = crossed_case(tmp_path)
    _, full = ue.build_targets(case, program("where(cs_rank(close) > 0.5, 0.4, 0)"))
    code = case["decision_fixture"]["codes"][0]
    masked = ue.mask_targets(full, code)
    assert len(masked) == len(full["targets"])
    assert all(a == b for a, b in zip(masked, full["targets"]) if a["symbol"] == code)
    assert all(Decimal(r["target_weight"]) == 0 for r in masked if r["symbol"] != code)
    assert all(Decimal(r["target_weight"]) == 0 for r in masked if r["symbol"] == code)
    # Recomputing ranks on just this stock would yield rank 1 and buy it. The
    # complete original universe correctly leaves the lower-ranked stock cash.
    assert any(Decimal(r["target_weight"]) > 0 for r in full["targets"])


def test_contract_rejects_dropped_stock_or_rescaled_capital(tmp_path):
    case = crossed_case(tmp_path)
    valid = unit_policy(case)
    for change in ({"codes": list(reversed(valid["codes"]))}, {"initial_cash_per_account": "5000.00"},
                   {"weight_policy": "rescale_to_one"}, {"max_account_runs_total": 0}):
        with pytest.raises(ValueError):
            ue.validate_policy({**valid, **change}, case)
    contract = {"action_limits": dict.fromkeys(ACTIONS, 8), "required_scope_id": "full",
                "execution_scope_id": "full", "execution_unit_id": "main", "benchmark_program_hashes": [],
                "revision_baseline_profile_id": None, "priority": 0}
    validate_task_contract(contract)
    validate_task_contract({**contract, "unit_execution": valid})


@pytest.fixture(scope="module")
def funded(tmp_path_factory):
    root = tmp_path_factory.mktemp("v5_units")
    case = crossed_case(root / "inputs")
    history, stage = [], root / "stage"
    v4 = ResearchTools(stage, "research", case, history)
    for name, weight in (("candidate", "0.4"), ("benchmark", "0.2"), ("revision", "0.3")):
        args = {"program": program(weight)}
        result = v4.execute(name, "develop_strategy", args)
        assert result["public"]["raw_status"] == "completed_mechanical"
        record(history, name, "develop_strategy", args, result)
    policy = base_policy(2018)
    policy["expected_years"] = [2018, 2019]
    identity = write_catalog(stage, prepare_catalog([], policy))
    contract = {"action_limits": dict.fromkeys(ACTIONS, 16), "required_scope_id": "cross_year_two_stocks",
        "execution_scope_id": "cross_year_two_stocks", "execution_unit_id": "main_account",
        "benchmark_program_hashes": [digest(program("0.2"))], "revision_baseline_profile_id": None, "priority": 0,
        "unit_execution": unit_policy(case)}
    tools = V5ResearchTools(stage, "research", case, history, catalog=Catalog(stage, identity), v5_contract=contract)
    artifacts = []
    for index, evidence in enumerate(("candidate", "revision")):
        call_id = "profile_" + str(index)
        args = {"evidence_id": evidence, "benchmark_evidence_id": "benchmark"}
        result = tools.execute(call_id, "profile_execution", args)
        record(history, call_id, "profile_execution", args, result)
        artifacts.append(json.loads((tools.folder / call_id / "artifact.json").read_text(encoding="utf-8")))
    return tools, case, artifacts


def test_real_worker_stock_accounts_preserve_cash_holdings_costs_across_years(funded):
    tools, case, artifacts = funded
    first = artifacts[0]
    assert first["bundle"]["expected_units"] == case["decision_fixture"]["codes"]
    assert len(first["profile"]["cells"]) == 4
    assert first["main_portfolio_pair"]["unit_kind"] == "portfolio"
    assert all(p["unit_kind"] == "stock" for p in first["bundle"]["pairs"])
    for row in first["unit_execution_records"]["candidate"]["accounts"]:
        raw = row["artifact"]["raw"]
        assert raw["status"] == "completed_mechanical"
        daily = raw["result"]["daily"]
        assert [r["date"] for r in daily] == case["decision_fixture"]["calendar"]
        assert all(set(r["holdings"]) <= {row["code"]} for r in daily)
        assert raw["result"]["initial_cash"] == case["initial_cash"]
        assert raw["result"]["final_snapshot"]["external_cash_flow"] == case["initial_cash"]
        assert Decimal(daily[-1]["fees_paid_cumulative"]) > 0
    for code in case["decision_fixture"]["codes"]:
        cells = [r for r in first["profile"]["cells"] if r["unit_id"] == code]
        assert cells[1]["candidate_metrics"]["starting_nav"] == cells[0]["candidate_metrics"]["ending_nav"]
        assert cells[1]["candidate_metrics"]["starting_nav"] != float(case["initial_cash"])
    assert first["profile"]["summary"]["statuses"]["source_quality"] == "pass"


def test_benchmark_raw_ledgers_reused_and_same_scope_comparison(funded):
    tools, case, (first, second) = funded
    assert all(r["reused"] for r in second["unit_execution_records"]["benchmark"]["accounts"])
    assert second["unit_execution_records"]["benchmark"]["usage"]["account_runs"] == 6
    assert first["bundle"]["pairs"][0]["benchmark"] == second["bundle"]["pairs"][0]["benchmark"]
    assert len(compare_profiles(first["profile"], second["profile"])["cells"]) == 4
    assert set(tools.profiles()) == {"profile_0", "profile_1"}
    assert second["unit_execution_records"]["benchmark"]["usage"]["wall_seconds"] > 0


def test_main_portfolio_annual_cells_are_delivered_with_summary(funded):
    tools, case, artifacts = funded
    args = {"profile_id": "profile_0", "table": "summary", "offset": 0, "limit": 1}
    result = tools.execute("main_summary", "inspect_stability", args)
    public = result["public"]["rows"][0]["main_portfolio_diagnostic"]
    assert [r["year"] for r in public["annual_cells"]] == [2018, 2019]
    assert public["summary"] == artifacts[0]["main_portfolio_profile"]["summary"]
    assert "stock_diagnostics" in tools.contract()["v5"]


def test_worker_recomputes_mask_and_rejects_forged_targets(funded, tmp_path):
    tools, _, artifacts = funded
    sources = artifacts[0]["unit_execution_records"]["candidate"]["source_hashes"]
    source = next(Path(p) for p in sources if p.endswith("input.json"))
    request = json.loads(source.read_text(encoding="utf-8"))
    request["masked_targets"][0]["target_weight"] = "0.99"
    (tmp_path / "input.json").write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(ValueError, match="exact mask"):
        ue._worker(tmp_path)


def test_budget_failure_retains_all_units_and_never_retries(tmp_path, monkeypatch):
    case = crossed_case(tmp_path / "inputs")
    policy = unit_policy(case, runs=1)
    original = {"program": program()}
    first = ue.run_accounts(tmp_path / "stage", "bounded", case, original, policy)
    assert len(first["accounts"]) == 2
    assert first["accounts"][0]["status"] == "completed_mechanical"
    assert first["accounts"][1]["artifact"] is None
    assert first["accounts"][1]["reason"] == "account_run_budget_exhausted"
    monkeypatch.setattr(ue, "_launch", lambda *a, **k: pytest.fail("saved diagnostics were reexecuted"))
    second = ue.run_accounts(tmp_path / "stage", "bounded", case, original, policy)
    assert second["usage"]["account_runs"] == 1
    assert all(r["reused"] for r in second["accounts"])


def test_cache_source_tamper_is_rejected(funded):
    tools, case, artifacts = funded
    record = artifacts[0]["unit_execution_records"]["candidate"]
    path = next(Path(p) for p in record["source_hashes"] if p.endswith("targets.json"))
    original = path.read_bytes()
    try:
        path.write_bytes(original + b" ")
        with pytest.raises(ValueError, match="changed"):
            ue.run_accounts(tools.root, tools.task_id, case, tools._candidate("candidate"), tools.v5_contract["unit_execution"])
    finally:
        path.write_bytes(original)


def test_compile_failure_is_missing_account_not_zero(tmp_path):
    case = crossed_case(tmp_path / "inputs")
    value = ue.run_accounts(tmp_path / "stage", "compile", case, {"program": program("2")}, unit_policy(case))
    assert value["usage"]["account_runs"] == 0
    assert len(value["accounts"]) == 2
    assert all(r["artifact"] is None and r["reason"] == "compile_failed" for r in value["accounts"])


def test_measurement_saved_before_parent_crash_recovers_without_reexecution(tmp_path, monkeypatch):
    case = crossed_case(tmp_path / "inputs")
    policy = unit_policy(case, runs=1)
    original = {"program": program()}
    save = ue.save_once
    def crash(path, value):
        if path.name == "result.json":
            raise OSError("parent failed after measurement")
        return save(path, value)
    monkeypatch.setattr(ue, "save_once", crash)
    with pytest.raises(OSError, match="after measurement"):
        ue.run_accounts(tmp_path / "stage", "recovery", case, original, policy)
    monkeypatch.setattr(ue, "save_once", save)
    monkeypatch.setattr(ue, "_launch", lambda *a, **k: pytest.fail("recovery dispatched a second account"))
    value = ue.run_accounts(tmp_path / "stage", "recovery", case, original, policy)
    assert value["usage"]["account_runs"] == 1
    assert value["accounts"][0]["status"] == "completed_mechanical"
    assert value["accounts"][0]["reused"] is True
    assert value["accounts"][1]["artifact"] is None
