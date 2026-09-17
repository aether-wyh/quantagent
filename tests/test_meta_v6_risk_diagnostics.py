from __future__ import annotations

import json

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.risk_diagnostics import (
    BLOCK_LENGTH, BOOTSTRAP_REPETITIONS, BOOTSTRAP_SEED, METRICS,
    _block_indices, date_block_bootstrap, evaluate_risk_information, risk_information_semantics,
)


def fixture(days=70, stocks=8):
    dates = pd.bdate_range("2019-11-18", periods=days)
    cols = [f"s{i}" for i in range(stocks)]
    amplitude = np.linspace(.005, .05, stocks)
    returns = np.where(np.arange(days)[:, None] % 2, -amplitude, amplitude)
    prices = pd.DataFrame(100*np.cumprod(1+returns, axis=0), index=dates, columns=cols)
    scores = pd.DataFrame(np.tile(amplitude, (days, 1)), index=dates, columns=cols)
    return scores, prices, prices.notna(), dates


def run(scores, prices, eligible, dates, **kwargs):
    return evaluate_risk_information(scores, prices, eligible, dates, minimum=3, quantiles=3, **kwargs)


def test_exact_twenty_open_returns_and_last_endpoint_excludes_d22():
    scores, prices, eligible, dates = fixture()
    prices.iloc[:22, 0] = np.array([777, 100, 95, 110, 90, *np.linspace(91, 108, 17)])
    before = prices.copy(deep=True)
    result = run(scores, prices, eligible, dates)
    path = prices.iloc[2:22, 0].to_numpy()/prices.iloc[1:21, 0].to_numpy()-1
    assert len(path) == 20
    assert result["labels"]["future_vol"].iloc[0, 0] == pytest.approx(np.std(path, ddof=1)*np.sqrt(252))
    assert result["labels"]["future_downside"].iloc[0, 0] == pytest.approx(np.sqrt(np.mean(np.minimum(path, 0)**2))*np.sqrt(252))
    assert result["labels"]["future_entry_max_loss"].iloc[0, 0] == pytest.approx(.10)
    changed = prices.copy()
    changed.iloc[22:, 0] *= .1
    after = run(scores, changed, eligible, dates)
    for metric in METRICS:
        assert after["labels"][metric].iloc[0, 0] == result["labels"][metric].iloc[0, 0]
        assert result["labels"][metric].iloc[-21:].isna().all().all()
    assert_frame_equal(prices, before)


@pytest.mark.parametrize("bad", [np.nan, 0, -1, np.inf])
def test_missing_or_invalid_any_path_price_invalidates_whole_window(bad):
    scores, prices, eligible, dates = fixture(days=30)
    prices.iloc[12, 0] = bad
    result = run(scores, prices, eligible, dates, horizon=3)
    for metric in METRICS:
        values = result["labels"][metric].iloc[:, 0]
        assert values.iloc[8:12].isna().all()
        assert pd.notna(values.iloc[7]) and pd.notna(values.iloc[12])
    # A missing physical price row must not compress the session window.
    dropped = run(scores, prices.drop(dates[12]), eligible, dates, horizon=3)
    for metric in METRICS:
        assert dropped["labels"][metric].loc[dates[8:12]].isna().all().all()


def test_future_perturbation_changes_only_affected_labels_not_scores_buckets_or_earlier_windows():
    scores, prices, eligible, dates = fixture(days=35)
    saved = [frame.copy(deep=True) for frame in (scores, prices, eligible)]
    original = run(scores, prices, eligible, dates, horizon=3)
    changed = prices.copy()
    changed.iloc[12, 0] *= .5
    result = run(scores, changed, eligible, dates, horizon=3)
    unaffected = dates.difference(dates[8:12])
    for metric in METRICS:
        assert_frame_equal(original["labels"][metric].loc[unaffected], result["labels"][metric].loc[unaffected])
    columns = ["date", "metric", "quantile", "signal_members"]
    assert_frame_equal(original["quantile_risk"][columns], result["quantile_risk"][columns])
    for frame, old in zip((scores, prices, eligible), saved):
        assert_frame_equal(frame, old)
    assert result["summary"]["risk_labels_registered_as_signal_fields"] is False


def test_entry_loss_is_not_peak_to_trough_drawdown_and_never_negative():
    scores, prices, eligible, dates = fixture(days=30)
    prices.iloc[1:5, 0] = [100, 120, 105, 110]
    prices.iloc[1:5, 1] = [100, 90, 120, 110]
    result = run(scores, prices, eligible, dates, horizon=3)
    assert result["labels"]["future_entry_max_loss"].iloc[0, 0] == 0
    assert result["labels"]["future_entry_max_loss"].iloc[0, 1] == pytest.approx(.1)


def test_direction_is_applied_once_and_quantile_risk_follows_declared_preference():
    scores, prices, eligible, dates = fixture()
    result = run(scores, prices, eligible, dates, direction=-1)
    np.testing.assert_allclose(result["daily_ic"].raw_rank_ic.dropna(), 1)
    np.testing.assert_allclose(result["daily_ic"].oriented_rank_ic.dropna(), 1)
    reversed_raw = run(-scores, prices, eligible, dates, direction=-1)
    np.testing.assert_allclose(reversed_raw["daily_ic"].raw_rank_ic.dropna(), -1)
    np.testing.assert_allclose(reversed_raw["daily_ic"].oriented_rank_ic.dropna(), -1)
    grouped = result["quantile_risk"].groupby(["metric", "quantile"]).risk_mean.mean().unstack()
    assert (grouped[3] < grouped[1]).all()


def test_future_membership_does_not_censor_signal_and_observation_mask_is_sensitivity_only():
    scores, prices, eligible, dates = fixture()
    eligible.iloc[1:, 0] = False
    base = run(scores, prices, eligible, dates)
    assert all(pd.notna(base["labels"][metric].iloc[0, 0]) for metric in METRICS)
    observed = prices.notna()
    observed.iloc[10, 1] = False
    strict = run(scores, prices, eligible, dates, observed_price_mask=observed)
    assert all(pd.isna(strict["labels"][metric].iloc[0, 1]) for metric in METRICS)
    assert (strict["coverage"].label_n <= strict["coverage"].price_only_label_n).all()
    assert strict["summary"]["semantics"]["observed_price_mask_supplied"] is True


def test_ties_not_split_by_column_order_and_missing_year_dates_retained():
    scores, prices, eligible, dates = fixture()
    scores.iloc[:, :] = 1
    scores.loc[scores.index.year == 2020] = np.nan
    result = run(scores, prices, eligible, dates)
    assert result["daily_ic"].raw_rank_ic.isna().all()
    assert set(result["annual"].year) == {2019, 2020}
    assert result["annual"].loc[result["annual"].year.eq(2020), "valid_dates_oriented_rank_ic"].eq(0).all()
    assert len(result["daily_ic"]) == 3*len(dates)
    by_day = result["quantile_risk"].groupby(["date", "metric"])
    assert all((group.signal_members.gt(0).sum() <= 1) for _, group in by_day)


def test_common_sample_controls_are_rank_residual_descriptions_without_new_scores():
    scores, prices, eligible, dates = fixture(stocks=12)
    controls = {"old_factor": scores.copy(), "log_amount": scores.copy() * 3}
    controls["old_factor"].iloc[:, 0] = np.nan
    saved = {key: frame.copy(deep=True) for key, frame in controls.items()}
    result = run(scores, prices, eligible, dates, controls=controls)
    usable = result["daily_ic"].paired_n.gt(0)
    assert result["daily_ic"].loc[usable, "common_n"].eq(11).all()
    assert result["daily_ic"].loc[usable, "control_rank_deficient"].all()
    assert result["daily_ic"].partial_oriented_rank_ic.isna().all()
    assert not {"residual_scores", "targets", "weights"} & result.keys()
    for key in controls:
        assert_frame_equal(controls[key], saved[key])


def test_partial_rank_correlation_matches_direct_same_day_ols():
    scores, prices, eligible, dates = fixture(stocks=20)
    rng = np.random.default_rng(13)
    control = pd.DataFrame(np.tile(rng.permutation(20), (len(dates), 1)), index=dates, columns=scores.columns)
    result = run(scores, prices, eligible, dates, controls={"old_factor": control})
    label = result["labels"]["future_vol"].iloc[0]
    x = (-scores.iloc[0]).rank().to_numpy()
    y = (-label).rank().to_numpy()
    design = np.column_stack([np.ones(20), control.iloc[0].rank().to_numpy()])
    response = np.column_stack([x, y])
    residual = response-design@np.linalg.lstsq(design, response, rcond=None)[0]
    expected = np.corrcoef(residual.T)[0, 1]
    row = result["daily_ic"].loc[result["daily_ic"].metric.eq("future_vol")].iloc[0]
    assert row.partial_oriented_rank_ic == pytest.approx(expected)


def test_fixed_block_bootstrap_preserves_missing_dates_and_is_not_iid():
    dates = pd.bdate_range("2019-01-01", periods=100)
    daily = pd.Series(np.r_[np.ones(30), np.full(40, np.nan), -np.ones(30)], index=dates, name="rank_ic")
    first, second = date_block_bootstrap(daily), date_block_bootstrap(daily)
    assert_frame_equal(first, second)
    row = first.iloc[0]
    assert row.calendar_dates == 100 and row.observed_dates == 60 and row.missing_dates == 40
    assert row.block_length == 20 and row.repetitions == 1000 and row.seed == 20260909
    indices = _block_indices(100, BLOCK_LENGTH, BOOTSTRAP_REPETITIONS, BOOTSTRAP_SEED)
    assert (np.diff(indices.reshape(1000, 5, 20), axis=2) == 1).all()
    draws = daily.to_numpy()[indices]
    counts = np.isfinite(draws).sum(axis=1)
    expected = np.divide(np.nansum(draws, axis=1), counts, out=np.full(1000, np.nan), where=counts>0)
    expected = expected[np.isfinite(expected)]
    np.testing.assert_allclose([row.ci_low, row.ci_high], np.quantile(expected, [.025, .975]))
    compressed = date_block_bootstrap(daily.dropna()).iloc[0]
    assert row.resample_plan_sha256 != compressed.resample_plan_sha256
    assert row.stock_day_iid == False


def test_bootstrap_restores_unselected_calendar_dates_and_short_ci_is_unavailable():
    scores, prices, eligible, dates = fixture(days=90)
    selected = dates.delete(slice(30, 40))
    result = run(scores, prices, eligible, selected)
    assert result["summary"]["bootstrap_calendar_dates"] == len(dates)
    assert len(result["daily_ic"]) == 3*len(selected)
    assert result["bootstrap"].calendar_dates.eq(90).all()
    small = date_block_bootstrap(pd.Series(np.arange(25), index=dates[:25])).iloc[0]
    assert small.status == "insufficient_calendar_or_observed_dates" and pd.isna(small.ci_low)


def test_semantics_can_be_frozen_before_any_factor_values_and_matches_evaluation():
    semantics = risk_information_semantics(direction=-1, horizon=20, minimum=3, quantiles=3)
    json.dumps(semantics, allow_nan=False)
    scores, prices, eligible, dates = fixture()
    result = run(scores, prices, eligible, dates)
    assert result["summary"]["semantics"] == semantics
    assert "fresh quotes" in semantics["price_observation_limit"]
    assert semantics["bootstrap"]["repetitions"] == 1000
    assert semantics["label_access"].startswith("Diagnostics only")
    with pytest.raises(ValueError, match="direction"):
        run(scores, prices, eligible, dates, direction=0)
    with pytest.raises(ValueError, match="chronological"):
        run(scores, prices, eligible, dates[::-1])
