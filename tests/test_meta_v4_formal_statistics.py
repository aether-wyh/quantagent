"""Hand-authored arithmetic fixtures only: no saved studies or market access."""
from copy import deepcopy
import hashlib

import pytest

from quanta_agents.meta_v3.formal_statistics import ARCHITECTURES, summarize_frozen_slots


def fixture(cases=(("A", "F1", "real_research"),), repeats=(1, 2, 3)):
    slots, outcomes = [], []
    for case, family, role in cases:
        for repeat in repeats:
            for arch in ARCHITECTURES:
                sid = f"{case}.{repeat}.{arch}"
                slots.append(dict(slot_id=sid, case_id=case, family=family, role=role,
                    case_definition_sha256=hashlib.sha256(case.encode()).hexdigest(),
                    repeat=repeat, architecture=arch, calendar_sha256="c" * 64, initial_capital_cny="1000000"))
                outcomes.append(dict(slot_id=sid, classification="valid_nonsuccess", reason="generated fixture"))
    return dict(version="frozen_slot_statistics_v1", input_kind="generated_fixture", statistical_draft_sha256="d" * 64,
                slots=slots, original_order=[s["slot_id"] for s in slots], shared_shock_ids=[]), outcomes


def test_unequal_families_have_different_weights_with_all_original_pairs():
    manifest, outcomes = fixture((("A", "F1", "real_research"), ("B", "F2", "real_research"),
                                  ("C", "F2", "real_research"), ("N", "control", "negative_control")))
    for slot, outcome in zip(manifest["slots"], outcomes):
        success = (slot["case_id"], slot["architecture"]) in set(zip(("A", "B", "C"), ARCHITECTURES))
        outcome.update(classification="valid_success" if success else "valid_nonsuccess", sharpe_rf2="2" if success else "0.5")
        if slot["role"] == "negative_control":
            outcome.update(classification="correct_abstention", sharpe_rf2="100")
    # This is a missing nonsuccess; no post-result change to the manifest.
    outcomes.pop(next(i for i, row in enumerate(outcomes) if row["slot_id"] == f"C.3.{ARCHITECTURES[0]}"))
    result = summarize_frozen_slots(manifest, outcomes)
    for arch, expected in zip(ARCHITECTURES, ("1/2", "1/4", "1/4")):
        summary = result["architectures"][arch]
        assert (summary["original_real_slots"], summary["successes"]) == (9, 3)
        assert summary["raw_success_rate"] == summary["case_equal_success_rate"] == "1/3"
        assert summary["family_equal_success_rate"] == expected
        assert summary["eligible_sharpe_rf2_median"] == "1/2"  # Nonwinners remain eligible.
        assert result["negative_controls"][arch]["correct_abstention_rate"] == "1"
    for pair in result["paired_gains"].values():
        assert pair["original_pairs"] == len(pair["pairs"]) == 9
        assert pair["raw_mean_difference"] == "0"
        assert pair["family_equal_mean_difference"] == "1/4"
    assert result["original_real_slots"] == 27 and result["original_slots"] == 36
    assert len(result["slot_outcomes"]) == 36


def test_all_missing_pairs_are_retained_and_unknown_does_not_mean_negative_return():
    manifest, _ = fixture()
    result = summarize_frozen_slots(manifest, [])
    for summary in result["architectures"].values():
        assert summary["original_real_slots"] == summary["missing_outcomes"] == summary["outcome_unknown_slots"] == 3
        assert summary["successes"] == 0 and summary["raw_success_rate"] == "0"
        assert summary["eligible_sharpe_rf2_median"] is None
    for summary in result["paired_gains"].values():
        assert summary["original_pairs"] == 3 and summary["raw_mean_difference"] == "0"
        assert all(row["v4_outcome_unknown"] and row["baseline_outcome_unknown"] for row in summary["pairs"])
        assert all(not row["v4_source_outcome_present"] and not row["baseline_source_outcome_present"] for row in summary["pairs"])
    assert any("not a negative economic return" in text for text in result["limitations"])


@pytest.mark.parametrize("failure", ["not_started", "invalid_final", "missing_final", "incomplete_account",
    "no_trades", "budget_stop", "error", "unrecovered_failure", "contamination", "outcome_unknown"])
def test_one_failed_side_keeps_pair_and_cannot_become_success_or_sharpe(failure):
    manifest, outcomes = fixture(repeats=(1,))
    outcomes[0].update(classification="valid_success", sharpe_rf2="2")
    outcomes[1].update(classification=failure, sharpe_rf2="999")
    result = summarize_frozen_slots(manifest, outcomes)
    assert result["paired_gains"][ARCHITECTURES[1]]["raw_mean_difference"] == "1"
    assert result["architectures"][ARCHITECTURES[1]]["original_real_slots"] == 1
    assert result["architectures"][ARCHITECTURES[1]]["eligible_sharpe_count"] == 0
    assert result["slot_outcomes"][1]["classification"] == failure


def test_shared_budget_stop_order_costs_provider_and_references_survive_without_mutation():
    manifest, outcomes = fixture(repeats=(1,))
    manifest["original_order"].reverse()
    manifest["shared_shock_ids"] = ["common_budget_stop"]
    for row in outcomes:
        row.update(classification="budget_stop", reason="whole study exhausted",
            provider_version="fixture-provider-v1", shared_shock_ids=["provider_incident"],
            costs={"known_tokens": 8, "unknown_reserve": 17},
            audit_binding={"reference": "generated audit reference only", "sha256": "a" * 64})
    originals = deepcopy((manifest, outcomes))
    result = summarize_frozen_slots(manifest, outcomes)
    assert (manifest, outcomes) == originals
    assert result["original_order"] == [row["slot_id"] for row in result["slot_outcomes"]]
    assert result["shared_shock_ids"] == ["common_budget_stop"]
    for row in result["slot_outcomes"]:
        assert row["reason"] == "whole study exhausted" and row["success"] == 0
        assert row["provider_version"] == "fixture-provider-v1" and row["shared_shock_ids"] == ["provider_incident"]
        assert row["costs"] == {"known_tokens": 8, "unknown_reserve": 17}
        assert row["audit_binding"] == outcomes[0]["audit_binding"]
    result["slot_outcomes"][0]["costs"]["known_tokens"] = 999
    assert outcomes[0]["costs"]["known_tokens"] == 8
    assert result["audit_bindings_verified"] is result["input_authentication_performed"] is False
    assert any("not independent samples" in text for text in result["limitations"])


def test_control_success_label_and_huge_sharpe_never_enter_real_denominator():
    manifest, outcomes = fixture((("N", "control", "negative_control"),), repeats=(1,))
    for row in outcomes:
        row.update(classification="valid_success", sharpe_rf2="1000")
    outcomes[0]["classification"] = "correct_abstention"
    result = summarize_frozen_slots(manifest, outcomes)
    assert result["original_real_slots"] == 0
    for summary in result["architectures"].values():
        assert summary["successes"] == 0 and summary["raw_success_rate"] is None
        assert summary["eligible_sharpe_rf2_median"] is None
    assert result["negative_controls"][ARCHITECTURES[0]]["correct_abstention_rate"] == "1"
    assert result["negative_controls"][ARCHITECTURES[1]]["correct_abstention_rate"] == "0"
    assert all(pair["original_pairs"] == 0 and pair["raw_mean_difference"] is None for pair in result["paired_gains"].values())


def test_saved_input_needs_reference_but_reference_does_not_authenticate_or_accept():
    manifest, outcomes = fixture(repeats=(1,))
    manifest["input_kind"] = "caller_validated_saved_records"
    for row in outcomes:
        row.update(classification="valid_success", sharpe_rf2="2")
    outcomes[1]["audit_binding"] = {"reference": "caller-supplied/not-read.json", "sha256": "a" * 64}
    outcomes[2].update(audit_binding=deepcopy(outcomes[1]["audit_binding"]), outcome_unknown=True)
    result = summarize_frozen_slots(manifest, outcomes)
    assert [row["success"] for row in result["slot_outcomes"]] == [0, 1, 0]
    assert [row["sharpe_eligible"] for row in result["slot_outcomes"]] == [False, True, False]
    assert result["slot_outcomes"][0]["counting_reason"] == "missing_audit_reference"
    assert result["audit_bindings_verified"] is result["formal_financial_accepted"] is False


def test_even_and_negative_nonwinner_median_is_exact_and_not_success_filtered():
    manifest, outcomes = fixture(repeats=(1, 2, 3, 4))
    for row in outcomes:
        repeat = int(row["slot_id"].split(".")[1])
        row.update(sharpe_rf2={1: "-2", 2: "-1", 3: "0.2", 4: "2"}[repeat],
                   classification="valid_success" if repeat == 4 else "valid_nonsuccess")
    result = summarize_frozen_slots(manifest, outcomes)
    assert all(row["eligible_sharpe_count"] == 4 and row["eligible_sharpe_rf2_median"] == "-2/5"
               for row in result["architectures"].values())


def test_all_success_still_has_no_formal_acceptance_or_lower_bound():
    manifest, outcomes = fixture()
    for row in outcomes:
        row.update(classification="valid_success", sharpe_rf2="2")
    result = summarize_frozen_slots(manifest, outcomes)
    assert all(row["raw_success_rate"] == "1" for row in result["architectures"].values())
    assert result["lower_bound"] is result["primary_weighting"] is None
    assert result["lower_bound_status"] == "not_evaluable"
    assert result["formal_financial_accepted"] is result["formal_architecture_improvement_accepted"] is False


@pytest.mark.parametrize("fault", ["slot_id", "architecture_start", "case_alias", "outcome", "extra_outcome",
    "order_duplicate", "order_missing", "missing_architecture", "family", "role", "calendar", "capital"])
def test_original_identity_pair_and_case_metadata_cannot_drift(fault):
    manifest, outcomes = fixture((("A", "F1", "real_research"), ("B", "F2", "real_research")))
    if fault == "slot_id":
        manifest["slots"][1]["slot_id"] = manifest["slots"][0]["slot_id"]
    elif fault == "architecture_start":
        manifest["slots"][1]["architecture"] = ARCHITECTURES[0]
    elif fault == "case_alias":
        for slot in manifest["slots"]:
            if slot["case_id"] == "B":
                slot["case_definition_sha256"] = manifest["slots"][0]["case_definition_sha256"]
    elif fault == "outcome":
        outcomes.append(deepcopy(outcomes[0]))
    elif fault == "extra_outcome":
        outcomes.append(dict(outcomes[0], slot_id="not-an-original-slot"))
    elif fault == "order_duplicate":
        manifest["original_order"][-1] = manifest["original_order"][0]
    elif fault == "order_missing":
        manifest["original_order"].pop()
    elif fault == "missing_architecture":
        manifest["slots"].pop(); manifest["original_order"].pop(); outcomes.pop()
    else:
        key, value = {"family": ("family", "other"), "role": ("role", "negative_control"),
                      "calendar": ("calendar_sha256", "e" * 64), "capital": ("initial_capital_cny", "1")}[fault]
        manifest["slots"][1][key] = value
    with pytest.raises(ValueError):
        summarize_frozen_slots(manifest, outcomes)


@pytest.mark.parametrize("value", [True, "NaN", "Infinity", "-Infinity", "1e999999", "1e-999999", "1" * 101])
def test_untrusted_numbers_are_bounded_finite_and_not_boolean(value):
    manifest, outcomes = fixture(repeats=(1,))
    outcomes[0]["sharpe_rf2"] = value
    with pytest.raises(ValueError):
        summarize_frozen_slots(manifest, outcomes)


@pytest.mark.parametrize("target", ["manifest", "outcome", "audit_binding"])
def test_self_reported_verified_flag_is_not_a_credential(target):
    manifest, outcomes = fixture(repeats=(1,))
    if target == "manifest":
        manifest["verified"] = True
    elif target == "outcome":
        outcomes[0]["verified"] = True
    else:
        outcomes[0]["audit_binding"] = {"reference": "somewhere", "sha256": "a" * 64, "verified": True}
    with pytest.raises(ValueError):
        summarize_frozen_slots(manifest, outcomes)


def test_slot_count_is_bounded_before_expensive_arithmetic():
    manifest, outcomes = fixture()
    manifest["slots"] = manifest["slots"] * 100
    with pytest.raises(ValueError, match="invalid original slots"):
        summarize_frozen_slots(manifest, outcomes)


@pytest.mark.parametrize("field", ["outcome_count", "text_length", "shock_count", "non_string_classification", "nested_nonfinite"])
def test_input_payload_boundaries(field):
    manifest, outcomes = fixture(repeats=(1,))
    if field == "outcome_count":
        outcomes.append(deepcopy(outcomes[0]))
    elif field == "text_length":
        outcomes[0]["reason"] = "x" * 16385
    elif field == "shock_count":
        manifest["shared_shock_ids"] = [str(index) for index in range(865)]
    elif field == "non_string_classification":
        outcomes[0]["classification"] = ["valid_success"]
    else:
        outcomes[0]["costs"] = {"known_tokens": float("inf")}
    with pytest.raises(ValueError):
        summarize_frozen_slots(manifest, outcomes)
