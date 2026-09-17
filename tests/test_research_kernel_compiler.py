"""Synthetic language semantics only; no model, market data, or account calls."""
from copy import deepcopy

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.research_kernel.compiler import (ALLOCATION_DEFAULTS, CapabilityGap, MAX_ARGS,
    MAX_DEPTH, MAX_NODES, MAX_WINDOW, canonical_expression, evaluate_expression, expression_id, factor_ids,
    strategy_id, validate_strategy)


def factor(name): return {"op": "factor", "id": name}
def constant(value): return {"op": "constant", "value": value}
def node(op, *args, **kwargs): return {"op": op, "args": list(args), **kwargs}


def panel(days=12, stocks=5):
    dates = pd.bdate_range("2020-01-01", periods=days)
    columns = pd.Index(["s" + str(i) for i in range(stocks)])
    data = np.arange(days * stocks, dtype=float).reshape(days, stocks) + 1
    frames = {"F" + str(i): pd.DataFrame(data * i - i**2, index=dates, columns=columns) for i in range(1, 6)}
    eligible = pd.DataFrame(True, index=dates, columns=columns)
    return frames, eligible


def strategy(score=None, **kwargs):
    return {"name": "synthetic", "score": factor("F1") if score is None else score, **kwargs}


@pytest.mark.parametrize("count", [3, 5])
def test_multifactor_weighted_sum_is_explicit_and_unranked(count):
    frames, eligible = panel()
    weights = [(-1 if i % 2 else 1) * (i + 1) for i in range(count)]
    expr = node("weighted_sum", *[factor("F" + str(i + 1)) for i in range(count)], weights=weights)
    expected = sum(frames["F" + str(i + 1)] * weights[i] for i in range(count))
    assert_frame_equal(evaluate_expression(expr, frames, eligible), expected)
    assert factor_ids(expr) == {"F" + str(i + 1) for i in range(count)}
    assert_frame_equal(evaluate_expression(node("rank", expr), frames, eligible), expected.rank(axis=1, pct=True))


def test_two_weak_factors_can_form_explicit_interaction_without_gating_by_ic():
    frames, eligible = panel(days=2, stocks=4)
    frames["F1"].iloc[:] = [-1, -1, 1, 1]
    frames["F2"].iloc[:] = [-1, 1, -1, 1]
    synthetic_label = np.array([1., -1., -1., 1.])
    assert np.corrcoef(frames["F1"].iloc[0], synthetic_label)[0, 1] == 0
    assert np.corrcoef(frames["F2"].iloc[0], synthetic_label)[0, 1] == 0
    interaction = evaluate_expression(node("multiply", factor("F1"), factor("F2")), frames, eligible)
    np.testing.assert_array_equal(interaction.iloc[0], synthetic_label)
    # This is an expressiveness test, not observed market predictiveness.


def test_rank_uses_only_eligible_cross_section_and_does_not_split_ties():
    frames, eligible = panel(days=2, stocks=4)
    frames["F1"].iloc[:] = [1., 1., 9., 1000.]
    eligible.iloc[:, -1] = False
    actual = evaluate_expression(node("rank", factor("F1")), frames, eligible)
    np.testing.assert_allclose(actual.iloc[0, :3], [.5, .5, 1.])
    assert actual.iloc[:, -1].isna().all()


def test_where_unknown_condition_and_selected_branch_missing_are_preserved():
    frames, eligible = panel(days=1, stocks=5)
    frames["F1"].iloc[:] = [np.nan, 0., 1., 1., 0.]
    frames["F2"].iloc[:] = [4., np.nan, 7., np.nan, np.nan]
    frames["F3"].iloc[:] = [5., 6., np.nan, 8., np.nan]
    result = evaluate_expression(node("where", factor("F1"), factor("F2"), factor("F3")), frames, eligible)
    np.testing.assert_allclose(result.iloc[0], [np.nan, 6., 7., np.nan, np.nan], equal_nan=True)
    comparison = evaluate_expression(node("gt", factor("F2"), constant(5)), frames, eligible)
    np.testing.assert_allclose(comparison.iloc[0], [0., np.nan, 1., np.nan, np.nan], equal_nan=True)
    frames["F1"].iloc[0, 0] = .2
    with pytest.raises(ValueError, match="where condition"): evaluate_expression(node("where", factor("F1"), constant(1), constant(0)), frames, eligible)


@pytest.mark.parametrize("op", ["gt", "lt", "ge", "le"])
def test_comparison_nan_never_becomes_false(op):
    frames, eligible = panel(days=1, stocks=3)
    frames["F1"].iloc[:] = [np.nan, 2., 2.]
    frames["F2"].iloc[:] = [2., np.nan, 2.]
    result = evaluate_expression(node(op, factor("F1"), factor("F2")), frames, eligible)
    assert result.iloc[0, :2].isna().all()
    assert result.iloc[0, 2] == (1. if op in {"ge", "le"} else 0.)


def test_missing_nonfinite_zero_division_and_zero_weight_propagate():
    frames, eligible = panel(days=3)
    frames["F1"].iloc[0, 0] = np.inf
    frames["F2"].iloc[1, 0] = np.nan
    frames["F2"].iloc[2, 0] = 0.
    result = evaluate_expression(node("divide", factor("F1"), factor("F2")), frames, eligible)
    assert result.iloc[:, 0].isna().all()
    zero = node("weighted_sum", factor("F1"), factor("F2"), weights=[1, 0])
    assert np.isnan(evaluate_expression(zero, frames, eligible).iloc[1, 0])
    assert factor_ids(zero) == {"F1", "F2"}


@pytest.mark.parametrize("op", ["lag", "mean", "std"])
def test_full_windows_and_future_perturbation(op):
    frames, eligible = panel(days=20)
    frames["F1"].iloc[4, 1] = np.nan
    expression = node(op, factor("F1"), window=3)
    before = evaluate_expression(expression, frames, eligible)
    expected = frames["F1"].shift(3) if op == "lag" else (frames["F1"].rolling(3, min_periods=3).mean()
        if op == "mean" else frames["F1"].rolling(3, min_periods=3).std(ddof=1))
    assert_frame_equal(before, expected)
    modified, eligible2 = {k: v.copy() for k, v in frames.items()}, eligible.copy()
    for value in modified.values(): value.iloc[11:] = -99999.
    eligible2.iloc[11:] = False
    after = evaluate_expression(expression, modified, eligible2)
    assert_frame_equal(before.iloc[:11], after.iloc[:11])


def test_historical_observation_not_erased_by_membership_but_rank_is_masked():
    frames, eligible = panel(days=4, stocks=3)
    eligible.iloc[0, 0] = False
    lagged = evaluate_expression(node("lag", factor("F1"), window=1), frames, eligible)
    assert lagged.iloc[1, 0] == frames["F1"].iloc[0, 0]
    lag_rank = evaluate_expression(node("lag", node("rank", factor("F1")), window=1), frames, eligible)
    assert np.isnan(lag_rank.iloc[1, 0])
    assert evaluate_expression(node("std", factor("F1"), window=1), frames, eligible).isna().all().all()


@pytest.mark.parametrize("window", [0, -1, 1.5, True, MAX_WINDOW + 1])
def test_invalid_or_future_windows_rejected(window):
    with pytest.raises(ValueError, match="positive bounded integer"): canonical_expression(node("lag", factor("F1"), window=window))


@pytest.mark.parametrize("identifier", ["label", "forward_return", "future_price", "F1_label", "outcome", "target_weight", "F1.future", "__import__('os')", "../F1"])
def test_forbidden_labels_and_code_are_not_operands(identifier):
    with pytest.raises(ValueError): canonical_expression(factor(identifier))


def test_unknown_operation_has_explicit_capability_gap():
    with pytest.raises(CapabilityGap, match="cross_sectional_ols"):
        canonical_expression(node("cross_sectional_ols", factor("F1")))
    with pytest.raises(ValueError): canonical_expression("F1 + F2")
    with pytest.raises(ValueError): canonical_expression({"op": "factor", "id": "F1", "python": "anything"})


@pytest.mark.parametrize("problem", ["index_order", "column_order", "extra_unused_frame", "duplicate_columns", "duplicate_dates", "non_numeric", "complex", "label_role", "eligible_na", "eligible_not_bool"])
def test_exact_axes_and_registered_signal_frame_contract(problem):
    frames, eligible = panel()
    if problem == "index_order": frames["F1"] = frames["F1"].iloc[::-1]
    elif problem == "column_order": frames["F1"] = frames["F1"].iloc[:, ::-1]
    elif problem == "extra_unused_frame": frames["F5"] = frames["F5"].iloc[:-1]
    elif problem == "duplicate_columns": eligible.columns = ["x"] * eligible.shape[1]
    elif problem == "duplicate_dates": eligible.index = [eligible.index[0]] * len(eligible)
    elif problem == "non_numeric": frames["F1"] = frames["F1"].astype(str)
    elif problem == "complex": frames["F1"] = frames["F1"].astype(complex)
    elif problem == "label_role": frames["F1"].attrs["role"] = "future_return_label"
    elif problem == "eligible_na": eligible = eligible.astype("boolean"); eligible.iloc[0, 0] = pd.NA
    elif problem == "eligible_not_bool": eligible = eligible.astype(float)
    with pytest.raises(ValueError): evaluate_expression(factor("F1"), frames, eligible)


def test_inputs_and_cached_subtrees_cannot_be_mutated_by_results():
    frames, eligible = panel()
    before, before_eligible = {k: v.copy(deep=True) for k, v in frames.items()}, eligible.copy(deep=True)
    shared = node("mean", factor("F1"), window=3)
    expr = node("add", shared, shared)
    result = evaluate_expression(expr, frames, eligible)
    result.iloc[:] = -1
    for key in frames: assert_frame_equal(frames[key], before[key])
    assert_frame_equal(eligible, before_eligible)
    assert_frame_equal(evaluate_expression(expr, frames, eligible), before["F1"].rolling(3).mean() * 2)


def test_aliases_defaults_and_display_names_do_not_split_semantic_ids():
    left = node("neg", node("cs_rank", node("rolling_mean", factor("F1"), window=3)))
    right = node("negate", node("rank", node("mean", factor("F1"), window=3)))
    assert expression_id(left) == expression_id(right)
    assert expression_id(constant(1)) == expression_id(constant(1.))
    assert expression_id(constant(-0.)) == expression_id(constant(0))
    a = strategy(left, metadata={"seed": "a"})
    b = strategy(right, version=1, allocation=deepcopy(ALLOCATION_DEFAULTS), gate=None, risk_score=None, metadata={"seed": "b"})
    b["name"] = "different display name"
    assert strategy_id(a) == strategy_id(b)
    assert expression_id(node("add", factor("F1"), factor("F2"))) != expression_id(node("add", factor("F2"), factor("F1")))
    assert strategy_id(strategy(factor("F1"))) != strategy_id(strategy(node("negate", factor("F1"))))


def test_strategy_normalization_copies_and_preserves_explicit_gate_risk():
    value = strategy(node("rank", factor("F1")), allocation={"weighting": "inverse_volatility"},
        risk_score=node("abs", factor("F3")), gate=node("where", node("lt", factor("F2"), constant(2)), constant(.5), constant(1)))
    before = deepcopy(value)
    normalized = validate_strategy(value)
    assert normalized["allocation"]["top_n"] == 20
    assert normalized["risk_score"] == value["risk_score"]
    normalized["score"]["args"][0]["id"] = "F5"
    assert value == before


@pytest.mark.parametrize("update", [
    {"market_filter": "trend20"}, {"allocation": {"unknown": 3}}, {"allocation": {"top_n": 0}},
    {"allocation": {"gross_exposure": 1.1}}, {"allocation": {"max_stock_weight": 0}},
    {"allocation": {"rebalance_sessions": -1}}, {"allocation": {"membership_buffer": 2}},
    {"allocation": {"weighting": "inverse_volatility"}}, {"risk_score": factor("F2")},
    {"allocation": {"weighting": []}}, {"version": True}, {"metadata": {"bad": float("nan")}},
])
def test_invalid_strategy_controls_fail_explicitly(update):
    with pytest.raises(ValueError): validate_strategy(strategy(**update))


def test_tree_parameter_and_cycle_budgets_prevent_unbounded_work():
    expr = factor("F1")
    for _ in range(MAX_DEPTH): expr = node("abs", expr)
    with pytest.raises(ValueError, match="budget"): canonical_expression(expr)
    cyclic = {"op": "abs", "args": []}; cyclic["args"].append(cyclic)
    with pytest.raises(ValueError, match="budget"): canonical_expression(cyclic)
    broad = node("add", *[factor("F1")] * (MAX_ARGS + 1))
    with pytest.raises(ValueError, match="bounded JSON list"): canonical_expression(broad)
    branch = node("add", *[factor("F1")] * MAX_ARGS)
    with pytest.raises(ValueError, match="node budget"): canonical_expression(node("add", *[branch] * MAX_ARGS))
    for number in [True, float("nan"), float("inf"), 10**50]:
        with pytest.raises(ValueError): canonical_expression(constant(number))
    with pytest.raises(ValueError): canonical_expression(node("weighted_sum", factor("F1"), weights=[]))


def test_library_digest_can_be_an_opaque_factor_identifier():
    frames, eligible = panel()
    identity = "0123456789abcdef" * 4
    result = evaluate_expression(factor(identity), {identity: frames["F1"]}, eligible)
    assert factor_ids(factor(identity)) == {identity}
    assert_frame_equal(result, frames["F1"])


def test_rebalance_interval_matches_account_capacity_without_limiting_rolling_windows():
    assert validate_strategy(strategy(allocation={"rebalance_sessions": 120}))["allocation"]["rebalance_sessions"] == 120
    with pytest.raises(ValueError, match="rebalance_sessions"):
        validate_strategy(strategy(allocation={"rebalance_sessions": 121}))
    assert canonical_expression(node("mean", factor("F1"), window=MAX_WINDOW))["window"] == MAX_WINDOW
