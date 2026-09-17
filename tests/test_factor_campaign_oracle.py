"""Adversarial tests authored outside the campaign implementation."""
from __future__ import annotations

import copy
import json

import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_acceptance_v10 import oracle


def annual_at(value, *, coverage=.8, days=200):
    return [{"year": year, "mean_pearson_ic": value, "valid_days": days,
             "evaluation_coverage": coverage} for year in range(2019, 2025)]


@pytest.mark.parametrize("kind,threshold", [("single_factor", .05), ("combination", .10)])
def test_strict_point_threshold_no_confidence_or_absolute_substitute(kind, threshold):
    assert not oracle.judge_annual(annual_at(threshold), kind)["point_estimate_passed"]
    passing = oracle.judge_annual(annual_at(np.nextafter(threshold, 1.)), kind)
    assert passing["point_estimate_passed"]
    assert not passing["accepted"]  # Metric arrays alone can never certify success.
    assert not oracle.judge_annual(annual_at(-threshold - .2), kind)["point_estimate_passed"]


def test_every_year_support_and_fixed_year_identity_are_required():
    rows = annual_at(.9)
    for index in range(6):
        bad = copy.deepcopy(rows)
        bad[index]["mean_pearson_ic"] = None
        assert not oracle.judge_annual(bad, "single_factor")["point_estimate_passed"]
    with pytest.raises(ValueError, match="all six"):
        oracle.judge_annual(rows[:-1], "single_factor")
    with pytest.raises(ValueError, match="all six"):
        oracle.judge_annual(rows[:1] * 6, "single_factor")
    for key, value in (("valid_days", 199), ("evaluation_coverage", np.nextafter(.8, 0)),
                       ("mean_pearson_ic", float("nan"))):
        bad = copy.deepcopy(rows)
        bad[3][key] = value
        assert not oracle.judge_annual(bad, "single_factor")["point_estimate_passed"]


def test_pearson_is_not_rankic_and_constants_and_missing_stay_unknown():
    assert oracle.scalar_pearson([1, 2, 3], [1, 2, 100]) < .9
    assert oracle.scalar_pearson(oracle.ranks([1, 2, 3]), oracle.ranks([1, 2, 100])) == pytest.approx(1)
    assert oracle.ranks([4, 2, 2, 9]).tolist() == [3, 1.5, 1.5, 4]
    assert oracle.scalar_pearson([1, 1, 1], [1, 2, 3]) is None
    assert oracle.scalar_pearson([np.nan, np.nan], [1, 2]) is None
    assert oracle.scalar_pearson([1, np.nan, 3], [1, 2, 6]) == pytest.approx(1)
    with pytest.raises(ValueError, match="lengths"):
        oracle.scalar_pearson([1], [1, 2])


def test_date_guard_precedes_any_numeric_conversion():
    class ForbiddenNumeric:
        def __array__(self, *args, **kwargs):
            pytest.fail("2025 numeric array was materialized")
    with pytest.raises(ValueError, match="2025"):
        oracle.independent_daily(["2024-12-31", "2025-01-02"], ForbiddenNumeric(),
                                 ForbiddenNumeric(), ForbiddenNumeric())


def test_literal_endpoint_and_year_tail_and_common_sample():
    dates = pd.bdate_range("2019-12-02", "2020-02-03").astype(str).tolist()
    opening = np.ones((len(dates), 105)) * 10
    scores = np.broadcast_to(np.arange(105, dtype=float), opening.shape).copy()
    pool = np.ones(opening.shape, bool)
    observed = np.ones(opening.shape)
    opening[1] = 10 + np.arange(105)
    opening[6] = opening[1] * (1 + np.arange(105) / 1050)
    rows = oracle.independent_daily(dates, opening, scores, pool, observed=observed,
                                    start=dates[0], end=dates[-1])
    assert rows[0]["pearson_ic"] == pytest.approx(1)
    assert rows[0]["paired_count"] == 105
    tail = [row for row in rows if row["date"].startswith("2019")][-6:]
    assert len(tail) == 6 and all(not row["label_safe"] and row["paired_count"] == 0 for row in tail)
    observed[6, :6] = 0
    reduced = oracle.independent_daily(dates, opening, scores, pool, observed=observed,
                                       start=dates[0], end=dates[-1])
    assert reduced[0]["paired_count"] == 99 and reduced[0]["pearson_ic"] is None
    scores[0, 6] = np.nan
    reduced = oracle.independent_daily(dates, opening, scores, pool, observed=observed,
                                       start=dates[0], end=dates[-1])
    assert reduced[0]["paired_count"] == 98 and reduced[0]["pool_count"] == 105


def test_head_is_chosen_without_future_labels_and_never_replaced():
    dates = pd.bdate_range("2019-01-02", periods=20).astype(str).tolist()
    scores = np.broadcast_to(np.arange(120, dtype=float), (20, 120)).copy()
    opening = np.exp(np.arange(20)[:, None] * np.arange(120)[None, :] / 10000)
    observed = np.ones(opening.shape)
    observed[6, -1] = 0
    result = oracle.independent_daily(dates, opening, scores, np.ones(opening.shape, bool), observed=observed,
                                      start=dates[0], end=dates[-1])
    assert result[0]["paired_count"] == 119
    assert result[0]["top40_return"] is None and not result[0]["top40_complete"]


def test_known_signal_and_noise_are_selected_differently_on_all_six_years():
    dates = sum([pd.bdate_range(f"{year}-01-02", periods=212).astype(str).tolist()
                 for year in range(2019, 2025)], [])
    drift = np.linspace(-.002, .002, 120)
    opening = np.exp(np.arange(len(dates))[:, None] * drift[None, :])
    signal = np.broadcast_to(drift, opening.shape)
    pool = np.ones(opening.shape, bool)
    known = oracle.independent_annual(oracle.independent_daily(dates, opening, signal, pool, diagnostics=False))
    noise = np.random.default_rng(721).normal(size=opening.shape)
    bad = oracle.independent_annual(oracle.independent_daily(dates, opening, noise, pool, diagnostics=False))
    assert oracle.judge_annual(known, "single_factor")["point_estimate_passed"]
    assert not oracle.judge_annual(bad, "single_factor")["point_estimate_passed"]
    assert all(row["valid_days"] == 206 for row in known)
    assert all(row["evaluation_coverage"] == pytest.approx(206 / 212) for row in known)
    assert all(len(row["purged_signal_dates"]) == 6 for row in known)


def test_independent_pool_historical_membership_seasoning_missing_and_status(tmp_path):
    dates = pd.bdate_range("2017-01-02", periods=150).astype(str).tolist()
    columns = ["sh600000", "sh600001", "sh600002"]
    membership = tmp_path / "members.txt"
    membership.write_text(f"sh600000 {dates[0]} {dates[-1]}\nsh600001 {dates[125]} {dates[-1]}\n"
                          f"sh600002 {dates[0]} {dates[-1]}\n", encoding="utf-8")
    fields = {name: np.ones((150, 3)) for name in ("close", "amount")}
    fields.update(is_st=np.zeros((150, 3)), is_delisting=np.zeros((150, 3)))
    fields["is_st"][140, 0] = 1
    fields["close"][10, 2] = np.nan
    fields["amount"][130, 0] = np.nan
    pool = oracle._source_pool(fields, dates, columns, membership)
    assert not pool[:119].any()
    assert pool[119, 0] and not pool[119, 1] and not pool[119, 2]
    assert pool[125, 1] and pool[130, 2]
    assert not pool[130:, 0].any()


def test_inlined_registered_aggregates_cannot_claim_single_factor():
    known = [{"name": "a", "expression": "pct_change(close, 5)"},
             {"name": "b", "expression": "rolling_mean(volume, 7)"}]
    lineage = {"transformation_kind": "raw_formula", "aggregation_of_registered_factors": [], "supervised": False}
    assert oracle.classify_formula("close / rolling_mean(close, 5) - 1", lineage, known) == "single_factor"
    assert oracle.classify_formula(".2 * pct_change(close, 5) + .8 * rolling_mean(volume, 7)", lineage, known) == "combination"
    assert oracle.classify_formula("pct_change(close, 5) * rolling_mean(volume, 7)", lineage, known) == "combination"
    condition = {**lineage, "transformation_kind": "conditional_interaction"}
    assert oracle.classify_formula("pct_change(close, 5) * rolling_mean(volume, 7)", condition, known) == "single_factor"
    assert oracle.classify_formula("close", {**lineage, "supervised": True}, known) == "combination"
    with pytest.raises(ValueError, match="transformation_kind"):
        oracle.classify_formula("close", {}, known)


def test_oracle_freeze_is_idempotent_but_modified_protocol_blocks(tmp_path):
    first = oracle.freeze_oracle(tmp_path)
    assert oracle.freeze_oracle(tmp_path) == first
    assert oracle.verify_oracle(tmp_path) == first
    first["protocol"]["single_factor_threshold"] = .001
    (tmp_path / "oracle_freeze.json").write_text(json.dumps(first), encoding="utf-8")
    with pytest.raises(ValueError, match="protocol changed"):
        oracle.verify_oracle(tmp_path)
    assert oracle.FROZEN_PROTOCOL["single_factor_threshold"] == .05


def test_arrays_or_self_asserted_replay_cannot_bypass_source_authority(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "package.json").write_text(json.dumps({"entity_type": "single_factor", "accepted": True,
                                                      "replay_verified": True}), encoding="utf-8")
    with pytest.raises((FileNotFoundError, KeyError)):
        oracle.audit_package(package, tmp_path / "nonexistent_authority")


@pytest.fixture(scope="module")
def combo_fixture():
    from quanta_agents.meta_v6.data import MarketPanel
    from quanta_agents.meta_v6.factors import FactorSpec
    from quanta_agents.factor_campaign.numeric import NumericContext
    from quanta_agents.factor_campaign.combination import CombinationEvaluator
    dates = pd.bdate_range("2015-01-01", "2024-12-31", name="date")
    columns = pd.Index([f"sh{600000+i}" for i in range(120)], name="symbol")
    rng = np.random.default_rng(112)
    close = 20 * np.exp(np.cumsum(rng.normal(0, .007, (len(dates), len(columns))), axis=0))
    opening = close * np.exp(rng.normal(0, .003, close.shape))
    field = lambda values: pd.DataFrame(values, index=dates, columns=columns)
    fields = {"close": field(close), "open": field(opening),
              "high": field(np.maximum(close, opening) * 1.01), "low": field(np.minimum(close, opening) * .99),
              "volume": field(np.exp(rng.normal(10, .2, close.shape))),
              "amount": field(np.exp(rng.normal(15, .2, close.shape))),
              "is_st": field(np.zeros(close.shape)), "is_delisting": field(np.zeros(close.shape)),
              "open_observed": field(np.ones(close.shape))}
    ctx = NumericContext(MarketPanel(fields, field(np.ones(close.shape, bool)), {"test": "synthetic_no_final_authority"}),
                         bootstrap_samples=1, max_cache_bytes=32 * 1024**2)
    specs = [FactorSpec("f1", "pct_change(close, 5)"), FactorSpec("f2", "close / open - 1"),
             FactorSpec("f3", "high / low - 1"), FactorSpec("f4", "volume / rolling_mean(volume, 5) - 1")]
    ctx.register(specs)
    values = {spec.factor_id: ctx.compute(spec).to_numpy() for spec in specs}
    authority = {"dates": dates.astype(str).tolist(), "columns": columns.tolist()}
    arrays = {"open": opening, "pool": ctx.pool.to_numpy(), "open_observed": np.ones(close.shape)}
    return ctx, CombinationEvaluator(ctx), values, authority, arrays


@pytest.mark.parametrize("target,method,update", [
    ("raw_return_demeaned", "ridge", "fixed"),
    ("rank_return_demeaned", "ridge", "fixed"),
    ("raw_return_demeaned", "equal_direction", "fixed"),
    ("raw_return_demeaned", "ridge", "quarterly_rolling3y"),
    ("rank_return_demeaned", "ridge", "quarterly_expanding"),
])
def test_complete_numeric_combo_independently_refitted_and_replayed(combo_fixture, target, method, update):
    from quanta_agents.factor_campaign.combination import CombinationSpec
    from quanta_agents.factor_acceptance_v10.replay import replay_combination
    ctx, evaluator, values, authority, arrays = combo_fixture
    spec = CombinationSpec("audit", tuple(values), target=target, method=method, update_rule=update)
    prediction, models = evaluator._predict(spec, start="2019-01-01", end="2024-12-31")
    package = {"spec": spec.to_dict(), "models_by_interval": models}
    replay = replay_combination(package, authority, arrays, values)
    np.testing.assert_allclose(replay, prediction.to_numpy(), rtol=1e-9, atol=1e-11, equal_nan=True)
    bad = copy.deepcopy(package)
    bad["models_by_interval"][-1]["coefficients"][0] += .001
    with pytest.raises(ValueError, match="coefficients differs"):
        replay_combination(bad, authority, arrays, values)


def test_model_endpoint_future_rows_missing_update_and_member_shuffle_rejected(combo_fixture):
    from quanta_agents.factor_campaign.combination import CombinationSpec
    from quanta_agents.factor_acceptance_v10.replay import replay_combination
    ctx, evaluator, values, authority, arrays = combo_fixture
    spec = CombinationSpec("audit_bad", tuple(values))
    _, models = evaluator._predict(spec, start="2019-01-01", end="2024-12-31")
    package = {"spec": spec.to_dict(), "models_by_interval": models}
    bad = copy.deepcopy(package)
    bad["models_by_interval"] = []
    with pytest.raises(ValueError, match="model updates"):
        replay_combination(bad, authority, arrays, values)
    bad = copy.deepcopy(package)
    bad["models_by_interval"][0]["fit_end"] = "2019-01-03"
    with pytest.raises(ValueError, match="fit window"):
        replay_combination(bad, authority, arrays, values)
    bad = copy.deepcopy(package)
    bad["models_by_interval"][0]["feature_order"] = list(reversed(bad["models_by_interval"][0]["feature_order"]))
    with pytest.raises(ValueError, match="member changes"):
        replay_combination(bad, authority, arrays, values)
