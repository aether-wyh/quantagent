from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quanta_agents.meta.factor_algebra import evaluate_expression
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec, canonical_expression, expression_guide


def panel(days=30, stocks=6):
    dates = pd.bdate_range("2019-12-16", periods=days)
    columns = [f"s{i}" for i in range(stocks)]
    growth = np.linspace(0.001, 0.02, stocks)
    opening = pd.DataFrame(100 * (1 + growth[None, :]) ** np.arange(days)[:, None],
                           index=dates, columns=columns)
    score = pd.DataFrame(np.tile(np.arange(stocks, dtype=float), (days, 1)), index=dates, columns=columns)
    return SimpleNamespace(fields={"open": opening, "close": opening * 1.001, "quality": score,
        "volume": opening * 1000, "raw_open": opening * 0.3,
        "adjustment_factor": opening * 0 + 0.3, "open_observed": opening * 0 + 1},
        eligible=opening.notna(), provenance={"scope": "synthetic", "execution_only_fields": ["open_observed"]})


def test_next_open_alignment_preserves_boundaries_and_ignores_future_membership():
    p = panel()
    p.fields["open"].iloc[3, 1] = np.nan
    p.fields["open_observed"].iloc[5, 2] = 0
    p.eligible.iloc[2, 3] = False
    engine = FactorEngine(p)
    label = engine.labels(2)
    assert label.iloc[0, 0] == pytest.approx(p.fields["open"].iloc[3, 0] / p.fields["open"].iloc[1, 0] - 1)
    assert label.iloc[-3:].isna().all().all()
    assert np.isnan(label.iloc[0, 1])  # missing exit
    assert np.isnan(label.iloc[2, 1])  # missing entry
    assert np.isnan(label.iloc[2, 2])  # endpoint exists numerically but is not observed
    assert np.isnan(label.iloc[2, 3])  # ineligible signal date
    assert pd.notna(label.iloc[0, 3])  # future eligibility cannot censor the sample
    label.iloc[0, 0] = 999
    assert engine.labels(2).iloc[0, 0] != 999


def test_safe_language_identity_and_forbidden_fields():
    a = FactorSpec("one", "cs_rank( close / lag(close, 2) )")
    b = FactorSpec("two", " cs_rank((close/lag(close,2))) ", version="2")
    assert a.factor_id == b.factor_id
    assert a.spec_id != b.spec_id
    assert canonical_expression("close + volume") != canonical_expression("volume + close")
    for expression in ["label", "forward_return", "future_close", "raw_open", "adjustment_factor",
                       "open_observed", "lag(close,-1)", "close.iloc[0]", "__import__('os')",
                       "ema(close, 0)", "ema(close,121)", "rolling_corr(close,volume,2.0)",
                       "rolling_residual(close, volume, window=3)"]:
        with pytest.raises(ValueError):
            FactorSpec("invalid", expression)
    p = panel()
    p.fields["outcome"] = p.fields["open"].copy()
    p.provenance["field_roles"] = {"outcome": "label"}
    with pytest.raises(ValueError, match="unknown field"):
        FactorEngine(p).compute(FactorSpec("hidden_label", "outcome"))


@pytest.mark.parametrize("expression", [
    "cs_rank(close / rolling_mean(close, 3))", "where(close > lag(close, 1), quality, -quality)",
    "rolling_mean(close, 3) + rolling_mean(close, 3)", "ema(ema(ema(close, 3), 3), 3)",
    "rolling_corr(close, volume, 5)", "rolling_residual(close, volume, 5)", "ts_rank(close, 4)",
])
def test_factor_values_are_causal_for_every_extension(expression):
    p = panel()
    before = FactorEngine(p).compute(FactorSpec("x", expression))
    for name in p.fields:
        p.fields[name].iloc[17:] *= -1_000_000
    p.eligible.iloc[17:] = False
    after = FactorEngine(p).compute(FactorSpec("x", expression))
    assert_frame_equal(before.iloc[:17], after.iloc[:17])


def test_existing_language_equivalence_nested_universe_and_shared_cache():
    p = panel()
    p.eligible.iloc[:, -1] = False
    spec = FactorSpec("x", "cs_rank(rolling_mean(close, 3)) + cs_rank(volume)")
    engine = FactorEngine(p)
    expected = evaluate_expression(spec.expression,
        {k: v for k, v in p.fields.items() if k in {"close", "volume"}}, rank_universe=p.eligible).where(p.eligible)
    assert_frame_equal(engine.compute(spec), expected)
    evaluated = engine.cache_info["node_evaluations"]
    assert_frame_equal(engine.compute(spec), expected)
    assert engine.cache_info["node_evaluations"] == evaluated
    engine.compute(FactorSpec("shared", "cs_rank(rolling_mean(close, 3))"))
    assert engine.cache_info["node_evaluations"] == evaluated
    engine.evaluate(spec, horizons=(1, 3))
    engine.evaluate(FactorSpec("other", "quality"), horizons=(1, 3))
    assert engine.cache_info["label_evaluations"] == 2


def test_snapshot_copies_inputs_and_fingerprint_includes_values_eligibility_provenance():
    p = panel()
    engine = FactorEngine(p)
    prior = engine.compute(FactorSpec("x", "close"))
    p.fields["close"].iloc[0, 0] = -123
    p.eligible.iloc[0, 0] = False
    assert_frame_equal(engine.compute(FactorSpec("x", "close")), prior)
    assert FactorEngine(p).data_fingerprint != engine.data_fingerprint
    p = panel()
    p.provenance["scope"] = "another_sample"
    assert FactorEngine(p).data_fingerprint != engine.data_fingerprint
    value = engine.compute(FactorSpec("x", "close"))
    value.iloc[0, 0] = 999
    assert_frame_equal(engine.compute(FactorSpec("x", "close")), prior)


def test_metrics_report_known_order_tail_coverage_and_duplicate_incremental_evidence():
    p = panel()
    engine = FactorEngine(p)
    spec = FactorSpec("quality", "quality")
    result = engine.evaluate(spec, horizons=(1, 4), quantiles=3,
                             existing_factors={"same": engine.compute(spec)})
    assert result.daily_ic["rank_ic"].dropna().eq(1).all()
    assert set(result.annual.year) == {2019, 2020}
    coverage = result.coverage[result.coverage.horizon.eq(4)]
    assert coverage.eligible_count.eq(6).all()
    assert coverage.tail(5).paired_count.eq(0).all()
    assert coverage.tail(5).evaluation_coverage.eq(0).all()
    assert result.correlations.iloc[0].mean_rank_correlation == 1
    assert result.incremental.residual_ic_days.eq(0).all()
    assert result.incremental.residual_mean_rank_ic.isna().all()
    for q in (1, 2, 3):
        assert result.turnover[result.turnover["quantile"].eq(q)].turnover.iloc[1:].eq(0).all()
    assert all(v["mean_top_minus_bottom"] > 0 for v in result.summary["horizons"].values())
    assert result.summary["execution_certified"] is False
    json.dumps(result.to_dict(), allow_nan=False)


def test_ties_are_not_arbitrarily_split_and_unknown_returns_are_not_zero():
    p = panel()
    result = FactorEngine(p).evaluate(FactorSpec("constant", "1"), horizons=(1,), quantiles=3)
    assert result.daily_ic.rank_ic.isna().all()
    assert result.quantile_returns[result.quantile_returns["count"].eq(0)].mean_forward_return.isna().all()
    assert result.summary["horizons"]["1"]["mean_top_minus_bottom"] is None


def test_extensions_use_only_trailing_observations_and_complete_pair_windows():
    p = panel()
    p.fields["volume"] = 2 * p.fields["close"] + 7
    engine = FactorEngine(p)
    ema = engine.compute(FactorSpec("ema", "ema(close, 3)"))
    assert_frame_equal(ema, p.fields["close"].ewm(span=3, adjust=False, min_periods=3, ignore_na=False).mean())
    residual = engine.compute(FactorSpec("residual", "rolling_residual(volume, close, 5)"))
    assert residual.iloc[:4].isna().all().all()
    assert np.abs(residual.iloc[4:].to_numpy()).max() < 1e-8
    p.fields["volume"].iloc[10, 0] = np.nan
    corr = FactorEngine(p).compute(FactorSpec("corr", "rolling_corr(close, volume, 5)"))
    assert corr.iloc[10:15, 0].isna().all()


def test_grid_and_label_horizon_contract_fails_closed():
    p = panel()
    p.fields["close"] = p.fields["close"].iloc[::-1]
    with pytest.raises(ValueError, match="grid"):
        FactorEngine(p)
    engine = FactorEngine(panel())
    for horizon in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            engine.labels(horizon)


def test_atr_tema_and_bounded_cache_keep_same_scores():
    p = panel()
    p.fields["high"], p.fields["low"] = p.fields["close"] * 1.01, p.fields["close"] * 0.99
    high_low = "high-low"
    high_previous = "abs(high-lag(close,1))"
    low_previous = "abs(low-lag(close,1))"
    pair_max = f"where({high_low}>{high_previous},{high_low},{high_previous})"
    true_range = f"where(({pair_max})>{low_previous},({pair_max}),{low_previous})"
    atr = FactorSpec("ATR14", f"rolling_mean({true_range},14)")
    tema = FactorSpec("TEMA", "3*ema(close,5)-3*ema(ema(close,5),5)+ema(ema(ema(close,5),5),5)")
    cached, uncached = FactorEngine(p), FactorEngine(p, max_cache_bytes=1)
    previous = p.fields["close"].shift(1)
    tr = pd.DataFrame(np.maximum.reduce([(p.fields["high"] - p.fields["low"]).to_numpy(),
        (p.fields["high"] - previous).abs().to_numpy(), (p.fields["low"] - previous).abs().to_numpy()]),
        index=previous.index, columns=previous.columns)
    assert_frame_equal(cached.compute(atr), tr.rolling(14, min_periods=14).mean())
    e1 = p.fields["close"].ewm(span=5, adjust=False, min_periods=5).mean()
    e2 = e1.ewm(span=5, adjust=False, min_periods=5).mean()
    e3 = e2.ewm(span=5, adjust=False, min_periods=5).mean()
    assert_frame_equal(cached.compute(tema), 3*e1-3*e2+e3)
    assert_frame_equal(cached.compute(atr), uncached.compute(atr))
    assert uncached.cache_info["cache_bytes"] == 0
    assert "ema(x, window)" in expression_guide()["functions"]
