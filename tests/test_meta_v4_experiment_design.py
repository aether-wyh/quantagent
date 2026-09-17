"""Hand-calculated scalar sets; engineering evidence, not causal evaluation."""
from copy import deepcopy
from decimal import localcontext
import json

import pytest

from quanta_agents.meta_v3.experiment_design import review_experiment_design


def check(identifier, index, op, threshold, metric="net_pnl"):
    return {"id": identifier, "hypothesis_index": index, "metric": metric,
            "operator": op, "threshold": threshold}


def declaration(checks=None, count=2):
    result = {"mechanism_hypotheses": [f"Uninterpreted hypothesis {index}" for index in range(count)]}
    if checks is not None:
        result["contrast_checks"] = checks
    return result


HAND_CASES = [
    {"name": "opposite_signs", "input": declaration([
        check("positive", 0, "gt", "0"), check("negative", 1, "lt", "0")]),
     "expected_relation": "disjoint", "expected_warning_codes": [],
     "hand_answer": "No real number is both strictly positive and strictly negative; zero satisfies neither."},
    {"name": "contradictory_single_hypothesis", "input": declaration([
        check("positive", 0, "gt", "0"), check("nonpositive", 0, "lte", "0")], 1),
     "expected_relation": None, "expected_warning_codes": ["contradictory_numeric_conditions"],
     "hand_answer": "The conjunction x > 0 and x <= 0 is empty. One hypothesis is allowed."},
    {"name": "equality_vs_closed_bounds", "input": declaration([
        check("zero", 0, "eq", "0"), check("lower", 1, "gte", "-0.00"), check("upper", 1, "lte", "0.0")]),
     "expected_relation": "equivalent", "expected_warning_codes": ["equivalent_numeric_predictions"],
     "hand_answer": "Both prediction sets contain exactly zero; the two closed bounds are individually necessary."},
    {"name": "single_hypothesis", "input": declaration([check("positive", 0, "gt", "0")], 1),
     "expected_relation": None, "expected_warning_codes": [],
     "hand_answer": "The nonempty interval (0, infinity) is a legal scalar prediction; no competing hypothesis is required."},
    {"name": "no_checks", "input": declaration(), "expected_relation": "not_evaluated",
     "expected_warning_codes": [],
     "hand_answer": "Neither prose hypothesis has numeric checks; both remain unassessed, without an equivalence claim."},
    {"name": "duplicate_and_weaker_bound", "input": declaration([
        check("strict", 0, "gt", "0"), check("same", 0, "gt", "-0.0"), check("weak", 0, "gte", "0")], 1),
     "expected_relation": None, "expected_warning_codes": ["duplicate_numeric_conditions", "redundant_numeric_condition"],
     "hand_answer": "Two copies of x > 0 duplicate each other; either strict bound entails x >= 0."},
    {"name": "shared_boundary", "input": declaration([
        check("nonnegative", 0, "gte", "0"), check("nonpositive", 1, "lte", "0")]),
     "expected_relation": "overlapping_non_equivalent", "expected_warning_codes": [],
     "hand_answer": "The sets overlap at zero, but the first also permits positive values and the second negative values."},
    {"name": "different_metrics", "input": declaration([
        check("pnl", 0, "gt", "0"), check("fees", 1, "lt", "0", "fees_on_recorded_trades")]),
     "expected_relation": "overlapping_non_equivalent", "expected_warning_codes": [],
     "hand_answer": "Positive PnL change and negative fee change can occur together; opposite signs on distinct coordinates do not separate predictions."},
]


@pytest.mark.parametrize("case", HAND_CASES, ids=lambda case: case["name"])
def test_hand_calculated_examples(case):
    result = review_experiment_design(case["input"])
    relations = [row["relation"] for row in result["pair_comparisons"]]
    assert relations == ([] if case["expected_relation"] is None else [case["expected_relation"]])
    assert sorted(issue["code"] for issue in result["issues"] if issue["severity"] == "warning") == sorted(case["expected_warning_codes"])
    assert result["warning_only"] is True
    assert result["design_acceptance_decision"] == "not_made"
    assert result["causal_mechanism_identified"] is False
    assert result["formal_target_success"] is False


@pytest.mark.parametrize("lower_op, upper_op, empty", [
    ("gte", "lte", False), ("gt", "lte", True),
    ("gte", "lt", True), ("gt", "lt", True),
])
def test_closed_and_open_equal_endpoints(lower_op, upper_op, empty):
    result = review_experiment_design(declaration([
        check("lower", 0, lower_op, "1"), check("upper", 0, upper_op, "1")], 1))
    interval = result["hypotheses"][0]["metric_intervals"][0]
    assert interval["empty"] is empty
    assert result["hypotheses"][0]["status"] == ("contradictory" if empty else "satisfiable")
    if empty:
        assert result["issues"][0]["witness_check_ids"] == ["lower", "upper"]


def test_decimal_precision_cannot_merge_distinct_thresholds():
    # These represent distinct adjacent trillionths beyond binary-float precision.
    value = declaration([check("lower", 0, "gte", "999999999999999.999999999999"),
                         check("upper", 0, "lte", "999999999999999.999999999998")], 1)
    with localcontext() as context:
        context.prec = 2
        result = review_experiment_design(value)
    assert result["hypotheses"][0]["status"] == "contradictory"
    assert result["issues"][0]["intersection"]["lower"] == "999999999999999.999999999999"
    assert result["issues"][0]["intersection"]["upper"] == "999999999999999.999999999998"


def test_equality_can_be_implied_by_two_bounds_only():
    result = review_experiment_design(declaration([
        check("zero", 0, "eq", "0"), check("lower", 0, "gte", "0"), check("upper", 0, "lte", "0")], 1))
    redundant = {row["check_ids"][0]: row for row in result["issues"]}
    assert redundant["zero"]["implied_by_check_ids"] == ["lower", "upper"]
    assert redundant["lower"]["implied_by_check_ids"] == ["zero"]
    assert redundant["upper"]["implied_by_check_ids"] == ["zero"]
    assert any("do not remove all" in limitation for limitation in result["limitations"])


def test_equivalence_ignores_order_scale_and_redundant_inequalities():
    result = review_experiment_design(declaration([
        check("a_upper", 0, "lt", "2.0"), check("a_lower", 0, "gte", "-1"),
        check("a_weak", 0, "gt", "-2"), check("b_lower", 1, "gte", "-1.00"),
        check("b_upper", 1, "lt", "2")]))
    assert result["pair_comparisons"][0]["relation"] == "equivalent"
    redundant = [row for row in result["issues"] if row["code"] == "redundant_numeric_condition"]
    assert redundant[0]["check_ids"] == ["a_weak"]
    assert redundant[0]["implied_by_check_ids"] == ["a_lower"]


def test_multiple_metrics_compare_full_prediction_sets():
    result = review_experiment_design(declaration([
        check("pnl_a", 0, "gt", "0"), check("fees_a", 0, "lt", "0", "fees_on_recorded_trades"),
        check("pnl_b", 1, "gt", "0"), check("fees_b", 1, "gte", "0", "fees_on_recorded_trades")]))
    assert result["pair_comparisons"][0]["relation"] == "disjoint"
    assert result["pair_comparisons"][0]["disjoint_metrics"] == ["fees_on_recorded_trades"]


def test_missing_coordinate_is_unbounded_and_does_not_imply_equivalence():
    result = review_experiment_design(declaration([
        check("pnl_a", 0, "gt", "0"), check("pnl_b", 1, "gt", "0"),
        check("fees_b", 1, "lt", "0", "fees_on_recorded_trades")]))
    assert result["pair_comparisons"][0]["relation"] == "overlapping_non_equivalent"


def test_two_inconsistent_hypotheses_are_equivalent_empty_not_successful_contrasts():
    result = review_experiment_design(declaration([
        check("pnl_a", 0, "gt", "0"), check("pnl_b", 0, "lt", "0"),
        check("fees_a", 1, "eq", "1", "fees_on_recorded_trades"),
        check("fees_b", 1, "eq", "2", "fees_on_recorded_trades")]))
    assert result["pair_comparisons"][0]["relation"] == "equivalent_empty"
    assert sum(issue["code"] == "contradictory_numeric_conditions" for issue in result["issues"]) == 2
    assert not any(issue["code"] == "redundant_numeric_condition" for issue in result["issues"])


def test_one_empty_prediction_does_not_receive_a_disjoint_design_claim():
    result = review_experiment_design(declaration([
        check("a", 0, "gt", "0"), check("b", 0, "lte", "0"), check("c", 1, "gt", "0")]))
    assert result["pair_comparisons"][0]["relation"] == "not_evaluated"
    assert result["pair_comparisons"][0]["reason"] == "one_prediction_set_empty"


@pytest.mark.parametrize("checks", [None, []])
def test_no_checks_are_explicitly_unassessed(checks):
    result = review_experiment_design(declaration(checks))
    assert result["status"] == "not_evaluated"
    assert all(row["status"] == "not_evaluated" for row in result["hypotheses"])
    assert result["issue_counts"] == {"warning": 0, "info": 2}


def test_partial_numeric_coverage_keeps_other_hypothesis_unassessed():
    result = review_experiment_design(declaration([check("pnl", 0, "gt", "0")]))
    assert result["hypotheses"][1]["status"] == "not_evaluated"
    assert result["pair_comparisons"][0]["relation"] == "not_evaluated"


def test_review_is_pure_json_serializable_and_ignores_prose_and_outcomes():
    value = declaration([check("positive", 0, "gt", "0")], 1)
    value.update(scan_count=31, remaining_budget=47, outcome="This proves the cause")
    before = deepcopy(value)
    result = review_experiment_design(value)
    assert value == before
    json.dumps(result, allow_nan=False)
    value["mechanism_hypotheses"][0] = "Any outcome proves this; no free-text judgment is claimed."
    assert review_experiment_design(value) == result
    assert "scan_count" not in result and "remaining_budget" not in result


@pytest.mark.parametrize("changes", [
    {"threshold": "NaN"}, {"threshold": "Infinity"}, {"threshold": "1e-3"},
    {"threshold": 0}, {"hypothesis_index": True}, {"hypothesis_index": 2},
    {"operator": "ne"}, {"metric": "invented_metric"},
])
def test_existing_check_schema_stays_authoritative(changes):
    item = {**check("bounded", 0, "gte", "0"), **changes}
    with pytest.raises(ValueError):
        review_experiment_design(declaration([item]))
