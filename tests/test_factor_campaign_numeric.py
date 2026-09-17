"""Synthetic contracts for causal wide predictors and shared statistical fits."""
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_campaign.numeric import NumericContext
from quanta_agents.factor_campaign.combination import (
    CombinationEvaluator, CombinationSpec, replay_predictions,
)
from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.factors import FactorSpec
from quanta_agents.meta_v7.combination import _fit_model


def panel(end="2020-12-31", stocks=16):
    dates = pd.bdate_range("2015-01-01", end, name="date")
    columns = pd.Index(["s"+str(i) for i in range(stocks)], name="symbol")
    rng = np.random.default_rng(82)
    opening = pd.DataFrame(20*np.exp(rng.normal(0, .012, (len(dates), stocks)).cumsum(0)),
                           index=dates, columns=columns)
    close = opening*(1+rng.normal(0, .005, opening.shape))
    volume = pd.DataFrame(rng.uniform(100, 1000, opening.shape), index=dates, columns=columns)
    return MarketPanel({"open": opening, "close": close, "high": np.maximum(close, opening)*1.01,
        "low": np.minimum(close, opening)*.99, "volume": volume, "amount": volume*close,
        "is_st": opening*0, "is_delisting": opening*0, "open_observed": opening*0+1},
        opening.notna(), {"source": "v10_synthetic_82"})


def context(p=None, **kwargs):
    return NumericContext(panel() if p is None else p, min_cross_section=5,
        min_train_days=20, bootstrap_samples=20, block_sessions=10, **kwargs)


def specs(count=4):
    return [FactorSpec("momentum"+str(i), f"close / lag(close, {i+2}) - 1") for i in range(count)]


def combination(items, **kwargs):
    return CombinationSpec("synthetic", tuple(s.factor_id for s in items), **kwargs)


def test_fixed_old_rank_target_parity_and_raw_target_difference():
    ctx = context().register(specs(8))
    items = list(ctx.specs.values())
    evaluator = CombinationEvaluator(ctx)
    rank_spec = combination(items, target="rank_return_demeaned")
    report, predictions = evaluator.evaluate(rank_spec, start="2019-01-01", end="2019-12-31")
    model = report["models_by_interval"][0]
    assert model["status"] == "fitted"
    dates, _, labels, _ = ctx.evaluator._scope(rank_spec.fit_start, rank_spec.fit_end)
    frames = {key: pd.DataFrame(ctx.ranked(key), index=ctx.dates, columns=ctx.columns).loc[dates]
              for key in rank_spec.feature_ids}
    features = [{"id": key, "kind": "base", "expression": {"op": "factor", "id": key}}
                for key in rank_spec.feature_ids]
    legacy = _fit_model(features, frames, ctx.pool.loc[dates], labels,
        {"min_cross_section": 5}, {"configuration": {"min_train_days": 20, "min_train_cells": 100}},
        ridge_lambda=.1)
    for key in ("coefficients", "feature_means", "feature_scales"):
        np.testing.assert_allclose(model[key], legacy[key], rtol=1e-10, atol=1e-10)
    days = evaluator.statistic_day_computations
    raw, _ = evaluator.evaluate(combination(items), start="2019-01-01", end="2019-12-31")
    assert evaluator.statistic_day_computations == days
    assert not np.allclose(model["coefficients"], raw["models_by_interval"][0]["coefficients"])
    pd.testing.assert_frame_equal(predictions, replay_predictions(ctx, report["models_by_interval"]))


def test_wide46_members_and_spec_identity():
    ctx = context().register(specs(46))
    items = list(ctx.specs.values())
    evaluator = CombinationEvaluator(ctx)
    spec = combination(items)
    prediction, models = evaluator._predict(spec, start="2019-01-01", end="2019-03-31")
    assert models[0]["status"] == "fitted"
    assert len(models[0]["coefficients"]) == 46
    assert prediction.loc["2019-01-02"].notna().sum() == 16
    reverse = CombinationSpec("different description", tuple(reversed(spec.feature_ids)))
    assert reverse.combination_id == spec.combination_id
    assert CombinationSpec.from_dict(spec.to_dict()) == spec


@pytest.mark.parametrize("rule", ["quarterly_rolling3y", "quarterly_expanding"])
def test_quarterly_label_maturity_and_future_perturbation(rule):
    original = panel()
    changed = deepcopy(original)
    for field in ("open", "close", "high", "low", "amount", "volume"):
        changed.fields[field].loc["2019-07-01":] *= 3
    items = specs()
    ctx = context(original).register(items)
    other = context(changed).register(items)
    spec = combination(items, update_rule=rule)
    evaluator = CombinationEvaluator(ctx)
    prediction, models = evaluator._predict(spec, start="2019-01-01", end="2020-12-31")
    later, changed_models = CombinationEvaluator(other)._predict(spec, start="2019-01-01", end="2020-12-31")
    assert len(models) == 8
    pd.testing.assert_frame_equal(prediction.loc[:"2019-06-28"], later.loc[:"2019-06-28"])
    # Q3 coefficients also cannot see the July mutation: its last six June
    # signal labels must be excluded until their endpoints have matured.
    for left, right in zip(models[:3], changed_models[:3]):
        assert left == right
    for model in models:
        assert model["status"] == "fitted"
        assert pd.Timestamp(model["last_label_endpoint"]) <= pd.Timestamp(model["fit_end"])
        assert pd.Timestamp(model["fit_end"]) < pd.Timestamp(model["predict_start"])
        for annual in model["annual_endpoint_purge"].values():
            assert len(annual["purged_signal_dates"]) == 6
    assert models[1]["fit_start"] == ("2016-04-01" if rule == "quarterly_rolling3y" else "2016-01-01")
    pd.testing.assert_frame_equal(prediction, replay_predictions(ctx, models))


def test_paired_train_prediction_common_and_inner_fold():
    p = panel()
    p.fields["volume"].iloc[::3, :4] = np.nan
    items = specs(4) + [FactorSpec("selective_volume", "volume")]
    ctx = context(p).register(items)
    ev = CombinationEvaluator(ctx)
    result = ev.paired_increment(combination(items[:4]), combination(items),
        start="2017-01-01", end="2017-12-31", fit_start="2016-01-01", fit_end="2016-12-31")
    assert result["status"] == "evaluated"
    a, b = result["models"]["baseline_common"][0], result["models"]["augmented"][0]
    assert a["sample_mask_id"] == b["sample_mask_id"]
    assert a["train_cells"] == b["train_cells"]
    assert a["sample_mask_id"] != result["models"]["baseline_original"][0]["sample_mask_id"]
    for day in result["daily"]:
        assert day["baseline_common_paired_count"] == day["augmented_paired_count"]
    assert result["baseline_original_cells"] > result["common_cells"]


def test_cache_original_corruption_and_lambda_share(tmp_path):
    items = specs(4)
    first = context(cache_dir=tmp_path).register(items)
    ev = CombinationEvaluator(first)
    spec = combination(items)
    a, models = ev._predict(spec, start="2019-01-01", end="2019-12-31")
    days = ev.statistic_day_computations
    ev._predict(combination(items, ridge_lambda=1), start="2019-01-01", end="2019-12-31")
    assert ev.statistic_day_computations == days
    fresh = context(cache_dir=tmp_path).register(items)
    second = CombinationEvaluator(fresh)
    b, other = second._predict(spec, start="2019-01-01", end="2019-12-31")
    pd.testing.assert_frame_equal(a, b)
    assert models == other and second.statistic_day_computations == 0
    # Simulate a stopped process before corrupting an on-disk cache; Windows
    # correctly prevents overwriting an actively mapped file.
    first.cache.arrays.clear()
    fresh.cache.arrays.clear()
    import gc
    gc.collect()
    rankfile = next((tmp_path / "numeric").glob("rank_*.npy"))
    rankfile.write_bytes(b"corrupt retained rebuildable cache")
    record = next((tmp_path / "numeric").glob("stats_*.json"))
    record.write_text("{}", encoding="utf-8")
    third = context(cache_dir=tmp_path).register(items)
    c, rebuilt = CombinationEvaluator(third)._predict(spec, start="2019-01-01", end="2019-12-31")
    pd.testing.assert_frame_equal(a, c)
    assert rebuilt == models
    assert third.cache.rejected >= 2


def test_equal_direction_signs_and_constant_failure():
    items = specs(4)
    ctx = context().register(items)
    spec = combination(items, method="equal_direction")
    ev = CombinationEvaluator(ctx)
    _, models = ev._predict(spec, start="2019-01-01", end="2019-12-31")
    expected = [ctx.evaluator.fit_direction(ctx.resolve(key))["direction"] for key in spec.feature_ids]
    assert models[0]["directions"] == expected
    np.testing.assert_equal(models[0]["coefficients"], np.array(expected)/4)
    constant = FactorSpec("constant", "close / close")
    ctx.register([constant])
    failed, prediction = ev.evaluate(combination([constant]), start="2019-01-01", end="2019-12-31")
    assert failed["status"] == "fit_unavailable" and prediction.isna().all().all()
    assert failed["summary"]["mean_pearson_ic"] is None
    missing = FactorSpec("entirely_missing", "(close - close) / (close - close)")
    ctx.register([missing])
    unavailable, empty = ev.evaluate(combination([missing]), start="2019-01-01", end="2019-12-31")
    assert unavailable["status"] == "fit_unavailable" and empty.isna().all().all()


def test_invalid_dates_axes_2025_and_mismatched_pair():
    ctx = context().register(specs())
    ev = CombinationEvaluator(ctx)
    spec = combination(list(ctx.specs.values()))
    with pytest.raises(ValueError):
        ev.evaluate(spec, start="2018-01-01", end="2018-12-31")
    with pytest.raises(ValueError):
        ev.evaluate(spec, start="2025-01-01", end="2025-12-31")
    with pytest.raises(ValueError):
        ctx.evaluate_prediction("bad", ctx.pool.iloc[::-1]*np.nan, start="2019-01-01", end="2019-12-31")
    with pytest.raises(ValueError):
        ev.paired_increment(spec, spec, start="2019-01-01", end="2019-12-31")
    with pytest.raises(ValueError):
        combination(list(ctx.specs.values()), method="equal_direction", update_rule="quarterly_expanding")
