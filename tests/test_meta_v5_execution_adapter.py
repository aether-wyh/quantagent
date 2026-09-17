"""Exercise V5 profile_execution through actual V4 accounting on generated data.

These are real executions of the software with synthetic 12-session inputs,
not real market tests, model calls, executable economics, or formal acceptance.
"""
from copy import deepcopy
from decimal import Decimal
import json

import pytest

from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v5.execution_adapter import saved_path
from quanta_agents.meta_v5.registry import Catalog, prepare_catalog, write_catalog, file_hash
from quanta_agents.meta_v5.tools import V5ResearchTools, ACTIONS
from test_meta_v3_research_entry import fixture


def program(weight):
    return {"version": "factor_strategy_program_v1", "factors": [],
            "target_weight_expression": str(weight), "hypothesis": "Generated arithmetic test only.",
            "applicability": ["Synthetic fixture"], "invalidation_conditions": ["Accounting mismatch"]}


def test_failed_before_account_exists_is_unknown_not_zero_return():
    assert saved_path({"program": program(2), "raw": None, "workbench": {"status": "failed"}},
                      "failed", ["2020-01-02"], 10000) is None


def policy(year):
    return {"version": "v5_stability_policy_v1", "expected_years": [year],
            "annualization": 252, "risk_free_rate": .02, "min_sessions_per_year": 2,
            "min_paired_cell_fraction": 1., "min_unit_coverage_fraction": 1.,
            "min_positive_excess_year_fraction": .5, "min_positive_excess_unit_fraction": .5,
            "max_worst_year_excess_loss": .05, "max_drawdown": .5,
            "max_positive_pnl_concentration": 1., "max_stale_fraction": 0.,
            "require_known_fees": True, "require_exposure": True, "require_execution_certified": False}


def record(history, call_id, action, args, result):
    history.append({"id": call_id, "status": "applied", "response": {"action": action,
                    "arguments_json": json.dumps(args)}, "result": result})


@pytest.fixture
def account_fixture(tmp_path):
    case = fixture.prepare(tmp_path / "case", flat=True)
    stage = tmp_path / "stage"
    stage.mkdir()
    history = []
    v4 = ResearchTools(stage, "test", case, history)
    for call_id, weight in (("candidate", .4), ("benchmark", .2)):
        args = {"program": program(weight)}
        result = v4.execute(call_id, "develop_strategy", args)
        assert result["public"]["raw_status"] == "completed_mechanical"
        record(history, call_id, "develop_strategy", args, result)
    year = int(case["decision_fixture"]["calendar"][0][:4])
    prepared = prepare_catalog([], policy(year))
    identity = write_catalog(stage, prepared)
    contract = {"action_limits": {a: 8 for a in ACTIONS}, "required_scope_id": "fixture_continuous",
                "execution_scope_id": "fixture_continuous", "execution_unit_id": "fixture_account",
                "benchmark_program_hashes": [digest(program(.2))], "revision_baseline_profile_id": None,
                "priority": 0}
    tools = V5ResearchTools(stage, "test", case, history, catalog=Catalog(stage, identity), v5_contract=contract)
    return tools, case, history, stage


def generated_artifact(tools, evidence_id="candidate"):
    return tools._candidate(evidence_id)


def profile_action(tools, history, call_id="profile", benchmark="benchmark"):
    args = {"evidence_id": "candidate", "benchmark_evidence_id": benchmark}
    result = tools.execute(call_id, "profile_execution", args)
    record(history, call_id, "profile_execution", args, result)
    artifact = json.loads((tools.folder / call_id / "artifact.json").read_text(encoding="utf-8"))
    return result, artifact


def test_actual_v4_account_becomes_source_bound_v5_profile_with_known_daily_economics(account_fixture):
    tools, case, history, stage = account_fixture
    original = generated_artifact(tools)
    result, artifact = profile_action(tools, history)
    bundle, profile = artifact["bundle"], artifact["profile"]
    assert bundle["program_hash"] == digest(program(.4))
    assert len(bundle["provenance"]["source_hashes"]) == 2
    for path, expected in bundle["provenance"]["source_hashes"].items():
        assert file_hash(path) == expected
    assert bundle["provenance"]["source_class"] == "generated_engineering"
    pair = bundle["pairs"][0]
    assert pair["calendar"] == case["decision_fixture"]["calendar"]
    assert len(pair["candidate"]["nav"]) == 12
    for arm_name in ("candidate", "benchmark"):
        path = pair[arm_name]
        assert all(x is not None for values in path.values() for x in values)
        assert all(0 <= x <= 1 for x in path["exposure"])
        assert all(x >= 0 for x in path["fees"])
        assert path["exposure"][-1] == 0 and path["stale"][-1] == 0
    last_fee = Decimal(original["raw"]["result"]["daily"][-1]["fees_paid_cumulative"])
    assert sum(pair["candidate"]["fees"]) == pytest.approx(float(last_fee))
    assert profile["summary"]["statuses"]["source_quality"] == "pass"
    assert profile["formal_target_success"] is False and result["execution_valid"] is False
    # Loading the dynamic profile verifies the original V4 artifact again.
    assert tools.profiles()["profile"]["profile_hash"] == profile["profile_hash"]


def test_profile_execution_rejects_a_benchmark_not_frozen_by_controller(account_fixture):
    tools, _, history, _ = account_fixture
    tools.v5_contract = {**tools.v5_contract, "benchmark_program_hashes": []}
    with pytest.raises(ValueError, match="benchmark.*frozen"):
        profile_action(tools, history)


def test_absent_benchmark_retains_unknown_cells_instead_of_inventing_cash_comparison(account_fixture):
    tools, _, history, _ = account_fixture
    _, artifact = profile_action(tools, history, benchmark=None)
    assert artifact["bundle"]["pairs"][0]["benchmark"] is None
    assert len(artifact["bundle"]["provenance"]["source_hashes"]) == 1
    profile = artifact["profile"]
    assert profile["summary"]["paired_cells"] == 0
    assert profile["cells"][0]["excess_return"] is None
    assert profile["development_eligible"] is False


@pytest.mark.parametrize("field,value", [("external_cash_flow", "10100.00"), ("external_cash_flow", None)])
def test_external_cash_flow_change_or_missing_identity_is_not_treated_as_return(account_fixture, field, value):
    tools, case, _, _ = account_fixture
    artifact = deepcopy(generated_artifact(tools))
    artifact["raw"]["result"]["final_snapshot"][field] = value
    with pytest.raises(ValueError, match="cash-flow"):
        saved_path(artifact, "candidate", case["decision_fixture"]["calendar"], case["initial_cash"])


def test_initial_capital_mismatch_is_rejected(account_fixture):
    tools, case, _, _ = account_fixture
    artifact = deepcopy(generated_artifact(tools))
    artifact["raw"]["result"]["initial_cash"] = "1000.00"
    with pytest.raises(ValueError, match="initial capital"):
        saved_path(artifact, "candidate", case["decision_fixture"]["calendar"], case["initial_cash"])


def test_saved_calendar_cannot_compress_a_missing_interior_day(account_fixture):
    tools, case, _, _ = account_fixture
    artifact = deepcopy(generated_artifact(tools))
    artifact["raw"]["result"]["daily"].pop(3)
    with pytest.raises(ValueError, match="calendar|prefix"):
        saved_path(artifact, "candidate", case["decision_fixture"]["calendar"], case["initial_cash"])


def test_missing_fee_observation_is_not_backfilled_from_later_cumulative_total(account_fixture):
    tools, case, _, _ = account_fixture
    artifact = deepcopy(generated_artifact(tools))
    artifact["raw"]["result"]["daily"][3]["fees_paid_cumulative"] = None
    path = saved_path(artifact, "candidate", case["decision_fixture"]["calendar"], case["initial_cash"])
    assert path["fees"][3:5] == [None, None]
    assert path["fees"][5] is not None


def test_stored_v4_artifact_tamper_is_detected_when_dynamic_profile_is_reopened(account_fixture):
    tools, _, history, _ = account_fixture
    profile_action(tools, history)
    path = tools.folder / "candidate/artifact.json"
    artifact = json.loads(path.read_text(encoding="utf-8"))
    old_fee = Decimal(artifact["raw"]["result"]["daily"][0]["fees_paid_cumulative"])
    artifact["raw"]["result"]["daily"][0]["fees_paid_cumulative"] = str(old_fee + Decimal("1.00"))
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="changed|drift"):
        tools.profiles()
