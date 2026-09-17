"""Independent revision-accountability tests through the real V5 dispatcher.

All NAVs are explicitly generated controller fixtures. The final-selection
tests also execute real V4 accounting on synthetic inputs; neither V4 final
nor V5 gates are mocked. These tests establish software behavior, not a link
between generated NAVs and market performance or the truth of review prose.
"""
from copy import deepcopy

import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v5.registry import Catalog, prepare_catalog, write_catalog
from quanta_agents.meta_v5.tools import ACTIONS, V5ResearchTools
from test_meta_v3_research_entry import fixture
from test_meta_v5_adversarial import arm, explicit_policy, generated_bundle
from test_meta_v5_execution_adapter import program
from test_meta_v5_workflow import DEMO


def bundles(tmp_path, *, unknown=True):
    old = generated_bundle(tmp_path)
    old.update(candidate_id="original", program_hash=digest(program(.2)))
    old["expected_units"] = ["return_decline", "drawdown_worse", "unknown_unit"]
    pair = old["pairs"][0]
    old["pairs"] = [{**deepcopy(pair), "unit_id": unit} for unit in old["expected_units"]]
    new = deepcopy(old)
    new.update(candidate_id="revision", program_hash=digest(program(.4)))
    for p, values in zip(new["pairs"], (
        [108., 118., 125., 139.],
        [110., 130., 110., 160.],
        [130., 150., None if unknown else 170., 190.],
    )):
        p["candidate"] = arm(values)
    return old, new


def setup(tmp_path, *, unknown=True, execute=False, changed_scope=False):
    root = tmp_path / "stage"
    root.mkdir()
    case = fixture.prepare(tmp_path / "generated_case", flat=True)
    history = []
    if execute:
        native = ResearchTools(root, "review", case, history)
        actual = DEMO.saved_call(native, "develop_strategy", {"program": program(.4)}, call_id="executed_revision")
        assert actual["public"]["raw_status"] == "completed_mechanical"
    old, new = bundles(root, unknown=unknown)
    if changed_scope:
        new["scope_id"] = "different_scope"
    identity = write_catalog(root, prepare_catalog([old, new], explicit_policy()))
    catalog = Catalog(root, identity)
    contract = {"action_limits": {a: 128 for a in ACTIONS}, "required_scope_id": old["scope_id"],
                "execution_scope_id": old["scope_id"], "execution_unit_id": "synthetic_account",
                "benchmark_program_hashes": [], "revision_baseline_profile_id": "original"}
    tools = V5ResearchTools(root, "review", case, history, catalog=catalog, v5_contract=contract)
    return tools


def inspect(tools, *profiles):
    for profile in profiles:
        DEMO.read_pages(tools, profile)


def compare(tools, *, reverse=False):
    old, new = ("revision", "original") if reverse else ("original", "revision")
    result = DEMO.saved_call(tools, "compare_stability_revision", {
        "baseline_profile_id": old, "revision_profile_id": new})
    return result, tools._prior(result["evidence_id"], "compare_stability_revision")


def review_args(result, comparison, *, decision="continue_development", accept=True):
    return {"comparison_evidence_id": result["evidence_id"], "decision": decision,
            "responses": [{"cell_id": cell, "explanation":
                f"Retain {cell}; this generated regression or missing evidence remains unresolved.",
                "tradeoff_accepted": accept} for cell in comparison["review_required_cell_ids"]]}


def save_review(tools, result, comparison, **kwargs):
    return DEMO.saved_call(tools, "record_revision_review", review_args(result, comparison, **kwargs))


def reflected_final_setup(tmp_path):
    tools = setup(tmp_path, unknown=False, execute=True)
    inspect(tools, "original", "revision")
    profile = tools._profile("revision")
    assert profile["development_eligible"] is True
    reflection = DEMO.saved_call(tools, "record_stability_reflection", {
        "profile_id": "revision", "declaration": DEMO.fixture_reflection(profile)})
    args = {"outcome": "strategy_for_development", "conclusion": "Generated V5 selection gate test only.",
            "program_evidence_id": "executed_revision", "evidence_ids": ["executed_revision", reflection["evidence_id"]],
            "limitations": ["Synthetic NAV catalog is a gate fixture, not market evidence."],
            "next_step": "Retain all generated regressions for further development.",
            "falsifiers": ["Any omitted original cell or modified comparison identity."]}
    return tools, args


def test_actual_compare_retains_return_decline_drawdown_regression_and_unknown_despite_aggregate_gain(tmp_path):
    tools = setup(tmp_path)
    inspect(tools, "original", "revision")
    result, saved = compare(tools)
    cells = {r["cell_id"]: r for r in saved["comparison"]["cells"]}
    assert set(cells) == {f"{unit}:{year}" for unit in ("return_decline", "drawdown_worse", "unknown_unit") for year in (2020, 2021)}
    assert cells["return_decline:2020"]["status"] == "degraded"
    assert cells["drawdown_worse:2021"]["status"] == "improved"
    assert cells["drawdown_worse:2021"]["max_drawdown_change"] > 0
    assert cells["unknown_unit:2021"]["status"] == "unknown"
    assert cells["unknown_unit:2021"]["excess_return_change"] is None
    assert sum(c["excess_return_change"] for c in cells.values() if c["excess_return_change"] is not None) > 0
    assert set(saved["review_required_cell_ids"]) == {"return_decline:2020", "drawdown_worse:2021", "unknown_unit:2021"}
    assert not saved["comparison"]["adoption_recommended"]
    assert not saved["comparison"]["new_development_eligible"]
    assert not result["formal_target_success"]


@pytest.mark.parametrize("attack", ["omit", "aggregate_only", "duplicate", "invented_cell", "blank", "unaccepted"])
def test_actual_review_rejects_missing_cells_aggregate_only_or_unaccepted_tradeoffs(tmp_path, attack):
    tools = setup(tmp_path)
    inspect(tools, "original", "revision")
    result, comparison = compare(tools)
    args = review_args(result, comparison)
    if attack == "omit":
        args["responses"].pop()
    elif attack == "aggregate_only":
        args["responses"] = [{"cell_id": "overall", "explanation": "The total score improved.", "tradeoff_accepted": True}]
    elif attack == "duplicate":
        args["responses"][1] = deepcopy(args["responses"][0])
    elif attack == "invented_cell":
        args["responses"][0]["cell_id"] = "winner:2021"
    elif attack == "blank":
        args["responses"][0]["explanation"] = "  "
    else:
        args["responses"][0]["tradeoff_accepted"] = False
    with pytest.raises(AdmissionBlocked):
        DEMO.saved_call(tools, "record_revision_review", args)
    assert list(tools._saved("record_revision_review")) == []


@pytest.mark.parametrize("decision,accept", [("continue_development", True), ("reject", False), ("needs_evidence", False)])
def test_complete_explicit_review_saves_declaration_without_claiming_semantic_or_formal_truth(tmp_path, decision, accept):
    tools = setup(tmp_path)
    inspect(tools, "original", "revision")
    comparison_result, comparison = compare(tools)
    result = save_review(tools, comparison_result, comparison, decision=decision, accept=accept)
    record = tools._prior(result["evidence_id"], "record_revision_review")
    assert len(record["responses"]) == 3
    assert record["baseline_profile_hash"] == tools._profile("original")["profile_hash"]
    assert record["revision_profile_hash"] == tools._profile("revision")["profile_hash"]
    assert record["semantic_truth_verified"] is False
    assert record["formal_target_success"] is False
    assert tools._profile("revision")["development_eligible"] is False


def test_compare_dispatch_rejects_changed_scope_even_after_all_original_cells_were_read(tmp_path):
    tools = setup(tmp_path, changed_scope=True)
    inspect(tools, "original", "revision")
    with pytest.raises(ValueError, match="scope/policy changed"):
        compare(tools)


@pytest.mark.parametrize("attack", ["calendar", "benchmark", "unit_set", "initial_capital", "cost"])
def test_changed_comparison_denominator_is_rejected_before_tools_can_admit_it(tmp_path, attack):
    # These attacks are blocked even earlier than compare dispatch: a single
    # controller scope cannot contain conflicting comparison identities.
    old, new = bundles(tmp_path)
    if attack == "calendar": new["pairs"][0]["calendar"][0] = "2020-01-03"
    elif attack == "benchmark": new["pairs"][0]["benchmark"]["nav"][-1] = 70.
    elif attack == "unit_set":
        new["expected_units"].pop()
        new["pairs"].pop()
    elif attack == "initial_capital": new["pairs"][0]["initial_nav"] = 50.
    else: new["provenance"]["cost_policy"]["kind"] = "free_fees"
    with pytest.raises(ValueError, match="comparison|identity|scope"):
        prepare_catalog([old, new], explicit_policy())


def test_eligible_profile_and_bound_reflection_cannot_bypass_missing_revision_review(tmp_path):
    tools, args = reflected_final_setup(tmp_path)
    with pytest.raises(AdmissionBlocked, match="cited complete degradation review"):
        tools.final(args)


def test_final_rejects_comparison_reference_without_review(tmp_path):
    tools, args = reflected_final_setup(tmp_path)
    result, _ = compare(tools)
    args["evidence_ids"].append(result["evidence_id"])
    with pytest.raises(AdmissionBlocked, match="cited complete degradation review"):
        tools.final(args)


def test_saved_review_must_be_explicitly_cited_in_final(tmp_path):
    tools, args = reflected_final_setup(tmp_path)
    result, comparison = compare(tools)
    save_review(tools, result, comparison)
    with pytest.raises(AdmissionBlocked, match="cited complete degradation review"):
        tools.final(args)


def test_review_of_reverse_comparison_cannot_authorize_forward_revision(tmp_path):
    tools, args = reflected_final_setup(tmp_path)
    result, comparison = compare(tools, reverse=True)
    review = save_review(tools, result, comparison)
    args["evidence_ids"].append(review["evidence_id"])
    with pytest.raises(AdmissionBlocked, match="cited complete degradation review"):
        tools.final(args)


def test_latest_rejection_blocks_reusing_older_accepted_review(tmp_path):
    tools, args = reflected_final_setup(tmp_path)
    result, comparison = compare(tools)
    accepted = save_review(tools, result, comparison)
    rejected = save_review(tools, result, comparison, decision="reject", accept=False)
    args["evidence_ids"].extend([accepted["evidence_id"], rejected["evidence_id"]])
    with pytest.raises(AdmissionBlocked, match="cited complete degradation review"):
        tools.final(args)


def test_real_v4_fills_and_complete_cited_review_allow_development_final_only(tmp_path):
    tools, args = reflected_final_setup(tmp_path)
    result, comparison = compare(tools)
    review = save_review(tools, result, comparison)
    args["evidence_ids"].append(review["evidence_id"])
    final = tools.final(args)  # Real V4 final executes too; no final/gate mocks.
    assert final["legal_submission"] is True
    assert final["v5_stability_checked"] is True
    assert final["formal_target_success"] is False
    assert final["target_achieved"] is False
    assert final["execution_valid"] is False
    assert tools._prior(review["evidence_id"], "record_revision_review")["semantic_truth_verified"] is False
