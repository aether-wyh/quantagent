"""Generated numeric panels only; no historical market values or model calls."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quanta_agents.meta_v7.combination import (
    CombinationFitError, compile_to_strategy_expr, fit_combinations, predict,
)
from quanta_agents.research_kernel.compiler import evaluate_expression, factor_ids


def fixture_panel(periods=360, stocks=16):
    random = np.random.default_rng(2901)
    dates = pd.bdate_range("2018-08-01", periods=periods)
    columns = ["S" + str(i) for i in range(stocks)]
    def frame(values):
        return pd.DataFrame(values, index=dates, columns=columns)
    a, b = (random.normal(size=(periods, stocks)) for _ in range(2))
    frames = {"A": frame(a), "B": frame(b), "Duplicate": frame(-a),
              "Sparse": frame(random.normal(size=a.shape))}
    frames["Sparse"].iloc[10:] = np.nan
    labels = frame(a - .65 * b + random.normal(scale=.2, size=a.shape))
    eligible = frame(np.ones(a.shape, dtype=bool))
    return frames, eligible, labels


def fit(frames, eligible, labels, **overrides):
    arguments = {"train_start": eligible.index[0], "train_end": eligible.index[280],
                 "horizon_sessions": 5, "ridge_lambda": .1,
                 "selection": {"min_ic_days": 30, "min_annual_days": 20,
                               "min_abs_mean_ic": .02, "min_stable_year_fraction": 1.},
                 "min_train_days": 30, "min_train_cells": 200}
    arguments.update(overrides)
    return fit_combinations(frames, eligible, labels, **arguments)


def test_freezes_signed_models_and_retains_all_selection_rejections():
    frames, eligible, labels = fixture_panel()
    result = fit(frames, eligible, labels)
    assert result["selected_factors"] == ["A", "B"]
    audit = {row["factor_id"]: row for row in result["factor_selection"]}
    assert audit["B"]["direction"] == -1
    assert "absolute_rank_correlation_redundancy" in audit["Duplicate"]["reasons"]
    assert "insufficient_factor_coverage" in audit["Sparse"]["reasons"]
    assert result["models"]["equal_rank"]["coefficients"] == [.5, -.5]
    assert result["models"]["ridge"]["coefficients"][1] < 0
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert result["fit_scope"]["last_signal_date"] == eligible.index[274].isoformat()
    assert result["fit_scope"]["purged_terminal_sessions"] == 6


def test_future_and_purged_labels_factors_cannot_change_frozen_fit():
    frames, eligible, labels = fixture_panel()
    original = fit(frames, eligible, labels)
    poisoned = {name: value.copy() for name, value in frames.items()}
    for value in poisoned.values():
        value.iloc[275:] = np.inf
    poisoned_labels = labels.copy()
    poisoned_labels.iloc[275:] = -1e300
    poisoned_pool = eligible.copy()
    poisoned_pool.iloc[275:] = False
    assert fit(poisoned, poisoned_pool, poisoned_labels) == original
    assert_frame_equal(labels, fixture_panel()[2])


def test_future_dtype_poison_is_not_allowed_to_invalidate_numeric_prefix():
    frames, eligible, labels = fixture_panel()
    original = fit(frames, eligible, labels)
    poisoned = {name: value.astype(object) for name, value in frames.items()}
    for value in poisoned.values():
        value.iloc[275:] = "UNREAD_FUTURE"
    poisoned_labels = labels.astype(object)
    poisoned_labels.iloc[275:] = "UNREAD_FUTURE_LABEL"
    poisoned_pool = eligible.astype(object)
    poisoned_pool.iloc[275:] = None
    assert fit(poisoned, poisoned_pool, poisoned_labels) == original
    poisoned["A"].iloc[20, 0] = "INVALID_TRAIN_VALUE"
    with pytest.raises(ValueError):
        fit(poisoned, poisoned_pool, poisoned_labels)


@pytest.mark.parametrize("bad", [None, "True", 1])
def test_non_boolean_safe_prefix_eligibility_is_rejected(bad):
    frames, eligible, labels = fixture_panel()
    eligible = eligible.astype(object)
    eligible.iloc[30, 2] = bad
    with pytest.raises(CombinationFitError, match="complete booleans"):
        fit(frames, eligible, labels)


def test_compile_predict_and_direct_frozen_ridge_arithmetic_agree():
    frames, eligible, labels = fixture_panel()
    result = fit(frames, eligible, labels)
    for method in ("equal_rank", "ridge"):
        expression = compile_to_strategy_expr(result, model=method)
        scores = predict(result, frames, eligible, model=method)
        assert_frame_equal(scores, evaluate_expression(expression, frames, eligible))
    model = result["models"]["ridge"]
    raw = [frames[name].where(eligible).rank(axis=1, pct=True) - .5 for name in result["selected_factors"]]
    direct = sum((value - mean) / scale * coefficient for value, mean, scale, coefficient in
                 zip(raw, model["feature_means"], model["feature_scales"], model["coefficients"]))
    assert_frame_equal(direct, predict(result, frames, eligible))


def test_no_missing_value_fill_and_labels_not_required_for_prediction():
    frames, eligible, labels = fixture_panel()
    frames["B"].iloc[30, 0] = np.nan
    labels.iloc[31, 1] = np.nan
    result = fit(frames, eligible, labels)
    expected_cells = 275 * 16 - 2
    assert result["models"]["ridge"]["common_sample"]["cells"] == expected_cells
    prediction = predict(result, frames, eligible)
    assert pd.isna(prediction.iloc[30, 0])
    assert pd.notna(prediction.iloc[31, 1])
    eligible.iloc[-1, 2] = False
    assert pd.isna(predict(result, frames, eligible).iloc[-1, 2])


def test_equal_date_weighted_ridge_matches_independent_closed_form():
    frames, eligible, labels = fixture_panel()
    eligible.iloc[:120, 7:] = False
    result = fit(frames, eligible, labels)
    dates = eligible.index[:275]
    pool = eligible.loc[dates]
    model = result["models"]["ridge"]
    columns = [(frames[name].loc[dates].where(pool).rank(axis=1, pct=True) - .5)
               for name in result["selected_factors"]]
    common = pool & labels.loc[dates].notna()
    for column in columns:
        common &= column.notna()
    counts = common.sum(axis=1)
    target = labels.loc[dates].where(common).rank(axis=1, pct=True)
    target = target.sub(target.mean(axis=1), axis=0)
    mask = common.to_numpy()
    x = np.column_stack([column.to_numpy()[mask] for column in columns])
    y = target.to_numpy()[mask]
    weights = common.div(counts, axis=0).to_numpy()[mask] / len(dates)
    means = np.average(x, axis=0, weights=weights)
    scales = np.sqrt(np.average((x-means) ** 2, axis=0, weights=weights))
    z = (x-means) / scales
    expected = np.linalg.solve(z.T @ (weights[:, None] * z) + .1 * np.eye(x.shape[1]), z.T @ (weights*y))
    np.testing.assert_allclose(model["feature_means"], means, atol=1e-14)
    np.testing.assert_allclose(model["feature_scales"], scales, atol=1e-14)
    np.testing.assert_allclose(model["coefficients"], expected, atol=1e-14)
    assert "each_valid_date_equal_mass" in model["common_sample"]["weighting"]


def test_declared_weak_marginal_pair_keeps_both_main_effect_controls():
    frames, eligible, labels = fixture_panel(stocks=32)
    rng = np.random.default_rng(71)
    weak = pd.DataFrame(rng.normal(size=labels.shape), index=labels.index, columns=labels.columns)
    frames = {"A": frames["A"], "Weak": weak}
    centered_a = frames["A"].rank(axis=1, pct=True) - .5
    centered_weak = weak.rank(axis=1, pct=True) - .5
    labels = centered_a + 2.5 * centered_a * centered_weak
    result = fit(frames, eligible, labels, interaction_pairs=[("A", "Weak")],
                 selection={"min_ic_days": 30, "min_annual_days": 20, "min_abs_mean_ic": .1})
    assert result["selected_factors"] == ["A"]
    assert result["augmented_for_declared_pairs"] == ["Weak"]
    assert set(result["models"]) == {"equal_rank", "ridge", "ridge_augmented", "ridge_interactions"}
    augmented = result["models"]["ridge_augmented"]
    interacted = result["models"]["ridge_interactions"]
    assert [feature["id"] for feature in augmented["features"]] == ["A", "Weak"]
    assert [feature["kind"] for feature in interacted["features"]] == [
        "main_effect", "main_effect_control", "centered_rank_product"]
    assert augmented["common_sample"] == interacted["common_sample"]
    np.testing.assert_allclose(augmented["feature_means"], interacted["feature_means"][:2])
    np.testing.assert_allclose(augmented["feature_scales"], interacted["feature_scales"][:2])
    assert factor_ids(compile_to_strategy_expr(result, model="ridge_interactions")) == {"A", "Weak"}
    assert_frame_equal(predict(result, frames, eligible, model="ridge_interactions"),
                       evaluate_expression(interacted["expression"], frames, eligible))


def test_annual_reversal_rejected_using_only_fit_years():
    frames, eligible, labels = fixture_panel(periods=600)
    frames = {"A": frames["A"]}
    labels = frames["A"].copy()
    labels.loc[labels.index.year == 2019] *= -1
    with pytest.raises(CombinationFitError, match="no eligible base") as caught:
        fit(frames, eligible, labels, train_end=eligible.index[520],
            selection={"min_ic_days": 30, "min_annual_days": 20, "min_stable_year_fraction": 1.})
    row = caught.value.audit["factor_selection"][0]
    assert "unstable_annual_direction" in row["reasons"]
    assert {item["year"] for item in row["annual"]} <= {2018, 2019, 2020}
    json.dumps(caught.value.audit, allow_nan=False)


def test_return_candidate_allowlist_does_not_block_supported_pair_endpoint():
    frames, eligible, labels = fixture_panel()
    result = fit(frames, eligible, labels, return_candidate_ids=["A"], interaction_pairs=[("A", "B")])
    assert result["selected_factors"] == ["A"]
    assert result["augmented_for_declared_pairs"] == ["B"]
    row = next(row for row in result["factor_selection"] if row["factor_id"] == "B")
    assert row["support_passed"] and not row["declared_return_candidate"]
    assert "not_declared_return_candidate" in row["reasons"]
    assert result["configuration"]["return_candidate_ids"] == ["A"]


def test_pure_zero_marginal_interaction_survives_unavailable_base_models():
    dates = pd.bdate_range("2016-01-01", periods=150)
    columns = ["S" + str(i) for i in range(16)]
    x = np.tile(np.repeat([-1., 1.], 8), (150, 1))
    z = np.tile(np.repeat([-1., 1., -1., 1.], 4), (150, 1))
    frames = {"A": pd.DataFrame(x, index=dates, columns=columns),
              "B": pd.DataFrame(z, index=dates, columns=columns)}
    eligible = pd.DataFrame(True, index=dates, columns=columns)
    labels = pd.DataFrame(x*z, index=dates, columns=columns)
    result = fit_combinations(frames, eligible, labels, train_start=dates[0], train_end=dates[-1],
                              horizon_sessions=5, ridge_lambda=.1, interaction_pairs=[("A", "B")])
    assert result["selected_factors"] == []
    assert all(row["mean_ic"] == 0. and row["support_passed"] for row in result["factor_selection"])
    assert result["model_status"]["equal_rank"]["status"] == "unavailable"
    assert result["model_status"]["ridge"]["reason"] == "no eligible base return factor"
    assert set(result["models"]) == {"ridge_augmented", "ridge_interactions"}
    assert result["models"]["ridge_interactions"]["train_fit_diagnostics"]["mean_daily_rank_ic"] > .9
    scores = predict(result, frames, eligible, model="ridge_interactions")
    assert_frame_equal(scores, evaluate_expression(compile_to_strategy_expr(result, model="ridge_interactions"), frames, eligible))
    json.dumps(result, allow_nan=False)


def test_unavailable_declared_pair_retains_successful_base_methods():
    frames, eligible, labels = fixture_panel()
    result = fit(frames, eligible, labels, interaction_pairs=[("A", "Sparse")])
    assert set(result["models"]) == {"equal_rank", "ridge"}
    assert result["model_status"]["ridge_interactions"] == {
        "status": "unavailable", "reason": "no supported predeclared interaction pair"}
    assert result["interaction_audit"][0]["unsupported_endpoints"] == ["Sparse"]


def test_pair_common_sample_failure_does_not_block_supported_base():
    frames, eligible, labels = fixture_panel()
    frames["B"].iloc[:, 10:] = np.nan
    result = fit(frames, eligible, labels, return_candidate_ids=["A"],
                 interaction_pairs=[("A", "B")], min_train_cells=3300)
    assert set(result["models"]) == {"equal_rank", "ridge"}
    status = result["model_status"]["ridge_interactions"]
    assert status["status"] == "unavailable" and status["reason"] == "insufficient common training sample"
    assert status["common_sample"]["cells"] == 2750
    assert result["models"]["ridge"]["common_sample"]["cells"] == 4400


def test_insufficient_common_sample_raises_with_full_selection_audit():
    frames, eligible, labels = fixture_panel()
    with pytest.raises(CombinationFitError, match="insufficient common") as caught:
        fit(frames, eligible, labels, min_train_cells=100000)
    assert len(caught.value.audit["factor_selection"]) == len(frames)
    assert caught.value.audit["status"] == "failed"
    assert caught.value.audit["common_sample"]["cells"] > 0


@pytest.mark.parametrize("argument", [{"ridge_lambda": 0}, {"ridge_lambda": np.nan},
                                    {"horizon_sessions": -1}, {"horizon_sessions": True},
                                    {"interaction_pairs": [("A", "B"), ("B", "A")]},
                                    {"selection": {"max_factors": 7}}])
def test_invalid_or_implicit_fit_contract_rejected(argument):
    frames, eligible, labels = fixture_panel()
    with pytest.raises(ValueError):
        fit(frames, eligible, labels, **argument)


def test_artifact_is_immutable_and_factor_label_role_rejected():
    frames, eligible, labels = fixture_panel()
    artifact = fit(frames, eligible, labels)
    broken = deepcopy(artifact)
    broken["models"]["ridge"]["coefficients"][0] += .1
    with pytest.raises(CombinationFitError, match="hash differs"):
        predict(broken, frames, eligible)
    frames["A"].attrs["is_label"] = True
    with pytest.raises(ValueError, match="label-role"):
        fit(frames, eligible, labels)


def test_calendar_and_numeric_axes_must_match():
    frames, eligible, labels = fixture_panel()
    with pytest.raises(ValueError, match="label axes"):
        fit(frames, eligible, labels.iloc[:-1])
    with pytest.raises(ValueError, match="sorted"):
        fit({name: f.iloc[::-1] for name, f in frames.items()}, eligible.iloc[::-1], labels.iloc[::-1])


def test_source_inputs_are_unchanged_by_fit():
    frames, eligible, labels = fixture_panel()
    before = {name: value.copy(deep=True) for name, value in frames.items()}
    pool_before, labels_before = eligible.copy(), labels.copy()
    fit(frames, eligible, labels)
    for name, value in frames.items():
        assert_frame_equal(value, before[name])
    assert_frame_equal(eligible, pool_before)
    assert_frame_equal(labels, labels_before)
