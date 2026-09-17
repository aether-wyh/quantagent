"""Adversarial, hand-computable contracts for the V9A numerical adapter."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_research.adapters import factor_panel, load_research_panel
from quanta_agents.factor_research.evaluation import FactorEvaluator, pearson_ic
from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec
from quanta_agents.research_kernel.universe import execution_pool


def panel(end="2020-12-31", stocks=12):
    dates = pd.bdate_range("2015-01-01", end, name="date")
    names = pd.Index([f"sh{600000+i}" for i in range(stocks)], name="symbol")
    rng = np.random.default_rng(11)
    moves = rng.normal(.0003, .012, (len(dates), stocks))
    opening = pd.DataFrame(20 * np.exp(np.cumsum(moves, axis=0)), index=dates, columns=names)
    close = opening * (1 + rng.normal(0, .004, opening.shape))
    volume = pd.DataFrame(rng.uniform(100, 1000, opening.shape), index=dates, columns=names)
    fields = {"open": opening, "close": close,
        "high": np.maximum(opening, close) * 1.01,
        "low": np.minimum(opening, close) * .99, "volume": volume,
        "amount": volume * close,
        "is_st": opening * 0, "is_delisting": opening * 0,
        "open_observed": opening * 0 + 1}
    return MarketPanel(fields, pd.DataFrame(True, index=dates, columns=names),
        {"source": "synthetic_seed_11", "historical_available_at_verified": False})


def evaluator(p, **kwargs):
    return FactorEvaluator(p, train_start="2016-01-01", train_end="2018-12-31",
        min_cross_section=5, min_train_days=20, bootstrap_samples=30, block_sessions=10, **kwargs)


def assert_equal(a, b):
    pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-12, atol=1e-12)


def test_engine_import_has_no_account_dependency():
    root = str(Path(__file__).resolve().parents[1] / "src")
    code = (f"import sys; sys.path.insert(0, {root!r}); "
            "from quanta_agents.factor_research.evaluation import FactorEvaluator; "
            "assert 'quanta_agents.meta_v6.portfolio' not in sys.modules")
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


def test_raw_pearson_is_not_rank_ic():
    dates = pd.DatetimeIndex(["2020-01-02"])
    a = pd.DataFrame([[1., 2., 3., 100.]], index=dates)
    b = pd.DataFrame([[1., 2., 3., 4.]], index=dates)
    pool = a.notna()
    result, count = pearson_ic(a, b, pool, 3)
    x, y = a.iloc[0].to_numpy(), b.iloc[0].to_numpy()
    expected = np.sum((x - x.mean()) * (y - y.mean())) / np.sqrt(
        np.sum((x - x.mean())**2) * np.sum((y - y.mean())**2))
    assert result.iloc[0] == pytest.approx(expected)
    assert result.iloc[0] < .9
    assert count.iloc[0] == 4


def test_same_pool_used_inside_nested_rank_and_no_history_masking():
    p = panel()
    p.fields["is_st"].iloc[:, -1] = 1
    p.fields["close"].iloc[:, -1] = 1000000
    adapted = factor_panel(p)
    expected_pool = execution_pool(p)
    assert_equal(adapted.eligible, expected_pool)
    spec = FactorSpec("nested", "cs_rank(cs_rank(close) + cs_rank(volume))")
    actual = evaluator(p).compute(spec)
    first = p.fields["close"].where(expected_pool).rank(axis=1, pct=True)
    second = p.fields["volume"].where(expected_pool).rank(axis=1, pct=True)
    expected = (first + second).where(expected_pool).rank(axis=1, pct=True)
    assert_equal(actual, expected)
    # Histories remain available before a stock becomes eligible. Seasoning
    # controls the output/rank pool, not the input history of rolling operators.
    lagged = evaluator(p).compute(FactorSpec("lag", "rolling_mean(close, 20)"))
    assert lagged.iloc[119, 0] == pytest.approx(p.fields["close"].iloc[100:120, 0].mean())


def test_future_append_and_perturbation_cannot_change_old_scores():
    full = panel()
    cut = "2018-12-31"
    prefix = factor_panel(full, end=cut)
    spec = FactorSpec("causal", "cs_rank(rolling_mean(close, 20) / lag(close, 5))")
    early = FactorEngine(prefix).compute(spec)
    before = evaluator(full).compute(spec).loc[:cut]
    changed = deepcopy(full)
    for name in ("open", "close", "high", "low", "amount", "volume"):
        changed.fields[name].loc["2019-01-01":] *= 17
    after = evaluator(changed).compute(spec).loc[:cut]
    assert_equal(early, before)
    assert_equal(early, after)


def test_label_exact_observed_endpoints_and_annual_purge():
    p = panel()
    e = evaluator(p)
    dates, safe, labels, endpoints = e._scope("2019-01-01", "2020-12-31")
    date = dates[20]
    pos = p.dates.get_loc(date)
    expected = p.fields["open"].iloc[pos+6, 0] / p.fields["open"].iloc[pos+1, 0] - 1
    assert labels.loc[date].iloc[0] == pytest.approx(expected)
    for year in (2019, 2020):
        annual = safe.loc[safe.index.year == year]
        assert annual.iloc[-6:].eq(False).all()
        assert annual.iloc[:-6].all()
        assert len(endpoints[str(year)]["purged_signal_dates"]) == 6
    p.fields["open_observed"].iloc[pos+6, 0] = 0
    missing = evaluator(p)
    assert pd.isna(missing.labels.loc[date].iloc[0])
    # Interior missing open does not invalidate the endpoint return label.
    p.fields["open_observed"].iloc[pos+6, 0] = 1
    p.fields["open_observed"].iloc[pos+3, 0] = 0
    assert evaluator(p).labels.loc[date].iloc[0] == pytest.approx(expected)


def test_constant_nan_empty_and_training_direction_are_not_successes():
    e = evaluator(panel())
    for expression in ("close / close", "close / (close - close)"):
        result = e.evaluate(FactorSpec("bad", expression), start="2019-01-01", end="2020-12-31")
        assert result["direction"] == 0
        assert result["status"] == "insufficient_evidence"
        assert result["summary"]["mean_pearson_ic"] is None
        assert result["summary"]["valid_days"] == 0
        json.dumps(result, allow_nan=False)
    spec = FactorSpec("rev", "close / lag(close, 5)")
    result = e.evaluate(spec, start="2019-01-01", end="2020-12-31")
    with pytest.raises(ValueError, match="direction"):
        e.evaluate(spec, start="2019-01-01", end="2020-12-31", direction=-result["direction"])
    empty = e.evaluate(spec, start="2020-12-26", end="2020-12-27")
    assert empty["status"] == "insufficient_evidence"
    assert empty["daily"] == []


def test_cached_uncached_single_batch_and_reopened_cache_equal(tmp_path):
    p = panel()
    specs = [FactorSpec("rev", "close / lag(close, 5)"),
             FactorSpec("range", "cs_rank((high-low)/close)")]
    original = FactorEngine(factor_panel(p))
    e = evaluator(p, cache_dir=tmp_path)
    for spec in specs:
        assert_equal(e.compute(spec), original.compute(spec))
    again = evaluator(p, cache_dir=tmp_path)
    for spec in specs:
        assert_equal(again.compute(spec), original.compute(spec))
    assert again.cache.info["disk_hits"] == 2
    results = again.evaluate_batch(specs, start="2019-01-01", end="2020-12-31")
    for spec in specs:
        single = e.evaluate(spec, start="2019-01-01", end="2020-12-31")
        assert single["daily"] == results[spec.factor_id]["daily"]
        assert single["summary"] == results[spec.factor_id]["summary"]


def test_2025_rejected_before_loader_and_custom_fields_blocked(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("numeric loader entered")
    monkeypatch.setattr("quanta_agents.factor_research.adapters.load_market_panel", forbidden)
    with pytest.raises(ValueError, match="no numeric authorization"):
        load_research_panel("unused", start="2024-01-01", end="2025-01-01", calendar_path="unused")
    p = panel()
    p.fields["secret_future"] = p.fields["open"].shift(-1)
    e = evaluator(p)
    for expression in ("secret_future", "is_st", "open_observed"):
        with pytest.raises(ValueError):
            e.compute(FactorSpec("forbidden", expression))


def test_ridge_common_samples_and_column_order_future_labels_do_not_fit():
    p = panel()
    candidate = FactorSpec("candidate", "(high - low) / close")
    bases = [FactorSpec("momentum", "close / lag(close, 20)"),
             FactorSpec("volume", "volume / rolling_mean(volume, 20)")]
    # A missing candidate input creates sample change; amount and close remain
    # available so it cannot silently disappear from the baseline denominator.
    p.fields["high"].iloc[300::3, :4] = np.nan
    e = evaluator(p)
    r = e.incremental(candidate, bases, start="2019-01-01", end="2020-12-31")
    assert r["status"] == "evaluated"
    assert r["common_cells"] < r["baseline_original_cells"]
    models = r["models"]
    assert models["baseline_common"]["sample_mask_id"] == models["augmented"]["sample_mask_id"]
    assert models["baseline_original"]["sample_mask_id"] != models["augmented"]["sample_mask_id"]
    assert models["baseline_common"]["feature_order"] == sorted(s.factor_id for s in bases)
    assert models["augmented"]["feature_order"] == models["baseline_common"]["feature_order"] + [candidate.factor_id]
    changed = deepcopy(p)
    changed.fields["open"].loc["2019-01-01":] *= np.linspace(1, 3, len(changed.dates[changed.dates >= "2019-01-01"]))[:, None]
    later = evaluator(changed).incremental(candidate, list(reversed(bases)), start="2019-01-01", end="2020-12-31")
    for name in models:
        for key in ("coefficients", "feature_means", "feature_scales", "feature_order", "sample_mask_id"):
            assert models[name][key] == later["models"][name][key]
    with pytest.raises(ValueError, match="strictly after"):
        e.incremental(candidate, bases, start="2018-01-01", end="2019-12-31")


def test_interaction_comparison_keeps_both_main_effects():
    p = panel()
    a = FactorSpec("a", "close / lag(close, 5)")
    b = FactorSpec("b", "volume / rolling_mean(volume, 20)")
    f = FactorSpec("interaction", f"(cs_rank({a.expression}) - 0.5) * (cs_rank({b.expression}) - 0.5)")
    base = FactorSpec("base", "(high - low) / close")
    r = evaluator(p).incremental(f, [base], main_effects=[a, b], start="2019-01-01", end="2020-12-31")
    assert r["status"] == "evaluated"
    assert set(r["main_effect_ids"]) <= set(r["models"]["baseline_common"]["feature_order"])
    assert len(r["models"]["augmented"]["feature_order"]) == 4


def test_top40_missing_exit_stays_missing_without_replacement():
    p = panel(stocks=50)
    e = evaluator(p)
    spec = FactorSpec("volume", "volume")
    direction = e.fit_direction(spec)["direction"]
    date = pd.Timestamp("2019-03-05")
    ordered = (p.fields["volume"].loc[date] * direction).sort_values(ascending=False, kind="stable")
    missing_symbol = ordered.index[0]
    terminal = p.dates[p.dates.get_loc(date) + 6]
    p.fields["open_observed"].loc[terminal, missing_symbol] = 0
    result = evaluator(p).evaluate(spec, start="2019-01-01", end="2019-12-31")
    row = next(row for row in result["daily"] if row["date"] == str(date.date()))
    assert row["top40_count"] == 40
    assert row["top40_label_count"] == 39
    assert row["top40_missing_label_count"] == 1
    assert row["top40_relative_pool"] is None
    assert row["top40_observed_mean_forward_return"] is not None


def test_frozen_calendar_rejects_a_missing_final_month(tmp_path):
    p = panel(end="2020-11-30")
    calendar = tmp_path / "calendar.txt"
    calendar.write_text("\n".join(str(day.date()) for day in pd.bdate_range("2015-01-01", "2020-12-31")), encoding="utf-8")
    p.provenance["request"] = {"calendar_path": str(calendar)}
    e = evaluator(p)
    with pytest.raises(ValueError, match="missing sessions"):
        e.evaluate(FactorSpec("volume", "volume"), start="2020-01-01", end="2020-12-31")


def test_training_calendar_year_end_can_follow_final_session(tmp_path):
    p = panel(end="2018-12-28")
    calendar = tmp_path / "calendar.txt"
    calendar.write_text("\n".join(str(day.date()) for day in p.dates), encoding="utf-8")
    p.provenance["request"] = {"calendar_path": str(calendar)}
    e = evaluator(p)
    fitted = e.fit_direction(FactorSpec("volume", "volume"))
    assert fitted["valid_days"] > 20
    assert fitted["train_end"] == "2018-12-31"
