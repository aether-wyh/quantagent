"""Generated matrices only; no external observations, models or accounts."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quanta_agents.meta_v6.cross_sectional import compute_hf0280, cross_sectional_ols


def fixture(days=46):
    # Sylvester columns have known zero means and pairwise orthogonality.
    h = np.ones((1, 1))
    for _ in range(6):
        h = np.block([[h, h], [h, -h]])
    dates = pd.bdate_range("2019-10-01", periods=days)
    codes = [f"s{i:02}" for i in range(64)]
    def frame(values):
        return pd.DataFrame(np.broadcast_to(values, (days, 64)).copy(), index=dates, columns=codes)
    amplitude = (np.arange(days)[:, None] + 1) / 10
    fields = {"rbar_up17": frame(h[:, 1]), "rbar_down17": frame(h[:, 6]),
              "r_0931_1000": frame(h[:, 2]), "r_1001_1030": frame(h[:, 3]),
              "overnight_return": frame(h[:, 4])}
    fields["gu_1m"] = frame(10 + 4*h[:, 1] + .1*h[:, 2] - .2*h[:, 3] + .3*h[:, 4] + amplitude*h[:, 5])
    fields["gd_1m"] = frame(7 - 2*h[:, 6] + .4*h[:, 2] + .5*h[:, 3] - .6*h[:, 4]
                            + 2*amplitude*h[:, 5] + 3*amplitude*h[:, 7])
    eligible = pd.DataFrame(True, index=dates, columns=codes)
    return fields, eligible, dates, frame(3*amplitude*h[:, 7])


def generic(fields, eligible, dates, **kwargs):
    controls = {k: fields[k] for k in ["rbar_up17", "r_0931_1000", "r_1001_1030", "overnight_return"]}
    return cross_sectional_ols(fields["gu_1m"], controls, eligible=eligible, calendar=dates, **kwargs)


def test_raw_multicontrol_ols_recovers_known_intercept_coefficients_and_orthogonal_error():
    fields, mask, dates, _ = fixture(4)
    actual = generic(fields, mask, dates)
    np.testing.assert_allclose(actual.coefficients.to_numpy(), np.tile([10, 4, .1, -.2, .3], (4, 1)), atol=2e-14)
    for key in ["rbar_up17", "r_0931_1000", "r_1001_1030", "overnight_return"]:
        np.testing.assert_allclose((actual.residuals*fields[key]).sum(axis=1), 0, atol=2e-12)
    np.testing.assert_allclose(actual.residuals.sum(axis=1), 0, atol=2e-12)
    assert actual.diagnostics.status.eq("ok").all()
    assert actual.diagnostics["rank"].eq(5).all()
    assert actual.diagnostics.residual_degrees_of_freedom.eq(59).all()


def test_membership_and_nonfinite_inputs_never_enter_regression_or_receive_predictions():
    fields, mask, dates, _ = fixture(2)
    mask.iloc[:, -1] = False
    fields["gu_1m"].iloc[:, -1] = 1e200
    fields["gu_1m"].iloc[0, 0] = np.inf
    fields["rbar_up17"].iloc[0, 1] = np.nan
    actual = generic(fields, mask, dates)
    assert actual.diagnostics.complete_stocks.tolist() == [61, 63]
    assert actual.residuals.iloc[:, -1].isna().all()
    assert actual.residuals.iloc[0, :2].isna().all()
    fields["gu_1m"].iloc[:, -1] = -1e300
    assert_frame_equal(actual.residuals, generic(fields, mask, dates).residuals)


def test_exact_fifty_sample_boundary_and_generic_positive_residual_degrees_of_freedom():
    fields, mask, dates, _ = fixture(2)
    mask.iloc[0, 50:] = False
    mask.iloc[1, 49:] = False
    actual = generic(fields, mask, dates)
    assert actual.diagnostics.status.tolist() == ["ok", "insufficient_samples"]
    assert actual.residuals.iloc[1].isna().all()
    y = fields["gu_1m"].iloc[:, :5]
    controls = {str(k): fields[k].iloc[:, :5] for k in list(fields)[:4]}
    result = cross_sectional_ols(y, controls, eligible=mask.iloc[:, :5], calendar=dates, min_stocks=1)
    assert result.diagnostics.required_stocks.eq(6).all()
    assert result.diagnostics.status.eq("insufficient_samples").all()


def test_rank_deficiency_fails_entire_date_without_pseudoinverse_factor():
    fields, mask, dates, _ = fixture(3)
    fields["rbar_up17"].iloc[1] = fields["r_0931_1000"].iloc[1]
    actual = generic(fields, mask, dates)
    assert actual.diagnostics.status.tolist() == ["ok", "rank_deficient", "ok"]
    assert actual.residuals.iloc[1].isna().all()
    assert actual.coefficients.iloc[1].isna().all()


def test_intercept_only_is_allowed_and_valid_zero_residual_is_not_missing():
    _, mask, dates, _ = fixture(2)
    y = mask.astype(float)*7
    result = cross_sectional_ols(y, {}, eligible=mask, calendar=dates)
    assert result.diagnostics.status.eq("ok").all()
    np.testing.assert_allclose(result.coefficients["intercept"], 7, atol=2e-14)
    np.testing.assert_allclose(result.residuals, 0, atol=2e-14)
    assert result.residuals.notna().all(axis=None)


@pytest.mark.parametrize("kind", ["linalg", "nonfinite"])
def test_solver_failure_is_retained_as_missing_with_reason(monkeypatch, kind):
    fields, mask, dates, _ = fixture(2)
    def fail(x, y, rcond):
        if kind == "linalg":
            raise np.linalg.LinAlgError("generated failure")
        return np.full(x.shape[1], np.nan), np.array([]), x.shape[1], np.ones(x.shape[1])
    monkeypatch.setattr(np.linalg, "lstsq", fail)
    result = generic(fields, mask, dates)
    assert result.residuals.isna().all(axis=None)
    assert result.diagnostics.status.eq("solver_failed" if kind == "linalg" else "nonfinite_solution").all()


def test_hf0280_matches_known_three_equation_solution_and_fixed_complete_twenty_mean():
    fields, mask, dates, expected = fixture()
    originals = {k: v.copy(deep=True) for k, v in fields.items()}
    result = compute_hf0280(fields, eligible=mask, calendar=dates)
    np.testing.assert_allclose(result.daily_residual, expected, atol=2e-13)
    expected_score = expected.rolling(20, min_periods=20).mean()
    np.testing.assert_allclose(result.scores, expected_score, atol=2e-13, equal_nan=True)
    assert result.scores.iloc[:19].isna().all(axis=None)
    assert result.scores.iloc[19].notna().all()
    assert result.diagnostics.all_regressions_ok.all()
    assert result.semantics["direction"] == "higher_preferred"
    assert result.semantics["controls_ranked"] is False
    for k in fields:
        assert_frame_equal(fields[k], originals[k])


def test_each_initial_equation_uses_own_complete_cases_then_residual_intersection():
    fields, mask, dates, _ = fixture(1)
    fields["gu_1m"].iloc[0, 0] = np.nan
    fields["gd_1m"].iloc[0, 1] = np.nan
    result = compute_hf0280(fields, eligible=mask, calendar=dates)
    assert result.regressions["up"].diagnostics.complete_stocks.iloc[0] == 63
    assert result.regressions["down"].diagnostics.complete_stocks.iloc[0] == 63
    assert result.regressions["final"].diagnostics.complete_stocks.iloc[0] == 62
    assert result.daily_residual.iloc[0, :2].isna().all()


def test_final_regression_must_also_have_fifty_samples():
    fields, mask, dates, _ = fixture(1)
    fields["gu_1m"].iloc[0, :14] = np.nan
    fields["gd_1m"].iloc[0, 14:28] = np.nan
    result = compute_hf0280(fields, eligible=mask, calendar=dates)
    assert result.regressions["up"].diagnostics.status.iloc[0] == "ok"
    assert result.regressions["down"].diagnostics.status.iloc[0] == "ok"
    assert result.regressions["final"].diagnostics.complete_stocks.iloc[0] == 36
    assert result.regressions["final"].diagnostics.status.iloc[0] == "insufficient_samples"
    assert result.daily_residual.isna().all(axis=None)


def test_missing_stock_day_breaks_exact_twenty_sessions_until_twenty_new_observations():
    fields, mask, dates, _ = fixture(45)
    fields["gu_1m"].iloc[21, 0] = np.nan
    result = compute_hf0280(fields, eligible=mask, calendar=dates)
    assert pd.notna(result.scores.iloc[20, 0])
    assert result.scores.iloc[21:41, 0].isna().all()
    assert pd.notna(result.scores.iloc[41, 0])
    assert result.scores.iloc[21:41, 1:].notna().all(axis=None)


def test_missing_whole_common_session_is_reinserted_instead_of_skipped():
    fields, mask, dates, _ = fixture(45)
    fields = {k: v.drop(dates[21]) for k, v in fields.items()}
    result = compute_hf0280(fields, eligible=mask, calendar=dates)
    assert result.scores.index.equals(dates)
    assert result.diagnostics.up_status.iloc[21] == "insufficient_samples"
    assert result.scores.iloc[21:41].isna().all(axis=None)
    assert result.scores.iloc[41].notna().all()


def test_failure_of_one_cross_section_invalidates_all_stocks_for_its_trailing_windows():
    fields, mask, dates, _ = fixture(45)
    fields["rbar_down17"].iloc[21] = fields["overnight_return"].iloc[21]
    result = compute_hf0280(fields, eligible=mask, calendar=dates)
    assert result.diagnostics.down_status.iloc[21] == "rank_deficient"
    assert result.daily_residual.iloc[21].isna().all()
    assert result.scores.iloc[21:41].isna().all(axis=None)
    assert result.scores.iloc[41].notna().all()


def test_future_values_and_membership_cannot_change_prior_scores_or_coefficients():
    fields, mask, dates, _ = fixture(46)
    before = compute_hf0280(fields, eligible=mask, calendar=dates)
    for frame in fields.values():
        frame.iloc[30:] = -1e100
    mask.iloc[30:] = False
    after = compute_hf0280(fields, eligible=mask, calendar=dates)
    assert_frame_equal(before.scores.iloc[:30], after.scores.iloc[:30], check_exact=True)
    assert_frame_equal(before.daily_residual.iloc[:30], after.daily_residual.iloc[:30], check_exact=True)
    for name in before.regressions:
        assert_frame_equal(before.regressions[name].coefficients.iloc[:30], after.regressions[name].coefficients.iloc[:30], check_exact=True)
    prefix = compute_hf0280({k: v.iloc[:30] for k, v in fields.items()}, eligible=mask.iloc[:30], calendar=dates[:30])
    assert_frame_equal(before.scores.iloc[:30], prefix.scores, check_exact=True)


@pytest.mark.parametrize("problem", ["calendar_order", "calendar_duplicate", "time", "timezone", "outside", "columns", "eligibility_nan", "complex", "minimum_bool", "missing_field"])
def test_invalid_axes_scope_and_contract_fail_explicitly(problem):
    fields, mask, dates, _ = fixture(3)
    if problem == "calendar_order": dates = dates[::-1]
    elif problem == "calendar_duplicate": dates = pd.DatetimeIndex([dates[0], dates[0], dates[2]])
    elif problem == "time": dates = dates + pd.Timedelta(hours=1)
    elif problem == "timezone": dates = dates.tz_localize("UTC")
    elif problem == "outside": fields["gu_1m"].index = dates + pd.Timedelta(days=50)
    elif problem == "columns": fields["gu_1m"] = fields["gu_1m"].iloc[:, ::-1]
    elif problem == "eligibility_nan": mask = mask.astype(float); mask.iloc[0, 0] = np.nan
    elif problem == "complex": fields["gu_1m"] = fields["gu_1m"].astype(complex)
    elif problem == "missing_field": del fields["overnight_return"]
    with pytest.raises((ValueError, TypeError)):
        if problem == "minimum_bool": generic(fields, mask, dates, min_stocks=True)
        else: compute_hf0280(fields, eligible=mask, calendar=dates)
