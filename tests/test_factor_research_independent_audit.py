"""Adversarial V9A checks authored outside the production implementation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_research import adapters
from quanta_agents.factor_research.cache import FactorCache
from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec


_module = importlib.util.spec_from_file_location("v9a_audit_oracle",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_factor_research_v9a.py")
oracle = importlib.util.module_from_spec(_module)
_module.loader.exec_module(oracle)


def synthetic_panel(periods=540, stocks=12):
    dates = pd.bdate_range("2017-01-02", periods=periods, name="date")
    columns = pd.Index([f"sh{600000 + i}" for i in range(stocks)], name="symbol")
    rng = np.random.default_rng(43921)
    close = np.exp(np.cumsum(rng.normal(0, .017, (periods, stocks)), axis=0)) * np.arange(10, 10 + stocks)
    opening = close * np.exp(rng.normal(0, .005, close.shape))
    frame = lambda values: pd.DataFrame(values, index=dates, columns=columns)
    fields = {"close": frame(close), "open": frame(opening),
        "high": frame(np.maximum(opening, close) * 1.01),
        "low": frame(np.minimum(opening, close) * .99),
        "volume": frame(np.exp(rng.normal(10, .2, close.shape))),
        "amount": frame(np.exp(rng.normal(15, .2, close.shape))),
        "is_st": frame(np.zeros_like(close)), "is_delisting": frame(np.zeros_like(close)),
        "open_observed": frame(np.ones_like(close))}
    return MarketPanel(fields, frame(np.ones_like(close, dtype=bool)), {"test": "independent_synthetic"})


def test_unauthorized_loader_call_fails_before_entering_source(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unauthorized request reached the source loader")
    monkeypatch.setattr(adapters, "load_market_panel", forbidden)
    with pytest.raises(ValueError, match="authorization"):
        adapters.load_research_panel("unopened", start="2015-01-01", end="2025-01-01",
                                     calendar_path="unopened")


def test_numeric_poison_after_authorized_prefix_is_never_validated():
    original = synthetic_panel(periods=300)
    next_day = pd.DatetimeIndex([pd.Timestamp("2025-01-02")], name="date")
    fields = {name: pd.concat([frame, pd.DataFrame("DO_NOT_CONVERT_FUTURE", index=next_day,
                                                  columns=frame.columns)])
              for name, frame in original.fields.items()}
    eligible = pd.concat([original.eligible,
        pd.DataFrame("DO_NOT_COERCE_FUTURE", index=next_day, columns=original.eligible.columns)])
    poison = SimpleNamespace(fields=fields, eligible=eligible, provenance=original.provenance)
    output = adapters.factor_panel(poison, end=str(original.dates[-1].date()))
    expected = adapters.factor_panel(original)
    pd.testing.assert_frame_equal(output.eligible, expected.eligible, check_freq=False)
    for name in output.fields:
        pd.testing.assert_frame_equal(output.fields[name], expected.fields[name], check_freq=False)


def test_nested_rank_ignores_ineligible_stock_before_and_inside_formula():
    first = synthetic_panel()
    first.fields["is_st"].iloc[:, -1] = 1
    second = first.copy()
    first.fields["close"].iloc[:, -1] = .001
    second.fields["close"].iloc[:, -1] = 1e9
    spec = FactorSpec("nested_rank", "cs_rank(cs_rank(close) + cs_rank(rolling_mean(close, 5)))")
    a = FactorEngine(adapters.factor_panel(first)).compute(spec)
    b = FactorEngine(adapters.factor_panel(second)).compute(spec)
    pd.testing.assert_frame_equal(a, b)
    assert a.iloc[119:, -1].isna().all()
    assert a.iloc[119:, :-1].notna().all().all()


def test_future_tail_perturbation_and_extension_preserve_past_scores():
    original = synthetic_panel()
    cutoff = original.dates[410]
    altered = original.copy()
    for frame in altered.fields.values():
        if frame is altered.fields["is_st"] or frame is altered.fields["is_delisting"] or frame is altered.fields["open_observed"]:
            continue
        frame.iloc[411:] = frame.iloc[411:] * 19
    spec = FactorSpec("causal_window", "rolling_corr(close / rolling_mean(close, 5), volume / rolling_mean(volume, 7), 9)")
    before = FactorEngine(adapters.factor_panel(original, end=str(cutoff.date()))).compute(spec)
    full = FactorEngine(adapters.factor_panel(original)).compute(spec).loc[:cutoff]
    changed = FactorEngine(adapters.factor_panel(altered)).compute(spec).loc[:cutoff]
    pd.testing.assert_frame_equal(before, full)
    pd.testing.assert_frame_equal(before, changed)


def test_cache_returns_isolated_values_and_unit_free_formula_has_expected_scaling(tmp_path):
    original = synthetic_panel()
    scaled = original.copy()
    multipliers = np.geomspace(.01, 100, len(original.symbols))
    for name in ("open", "high", "low", "close"):
        scaled.fields[name] = scaled.fields[name] * multipliers
    spec = FactorSpec("relative_price", "close / rolling_mean(close, 5) - 1")
    cache = FactorCache(adapters.factor_panel(original), cache_dir=tmp_path)
    actual = cache.compute(spec)
    cached = cache.compute(spec)
    actual.iloc[:, :] = 999
    pd.testing.assert_frame_equal(cache.compute(spec), cached)
    clean = cache.compute(spec, use_cache=False)
    pd.testing.assert_frame_equal(clean, cached)
    disk = FactorCache(adapters.factor_panel(original), cache_dir=tmp_path).compute(spec)
    pd.testing.assert_frame_equal(disk, cached)
    transformed = FactorEngine(adapters.factor_panel(scaled)).compute(spec)
    np.testing.assert_allclose(transformed, cached, rtol=1e-12, atol=1e-12, equal_nan=True)
    # Check selected values by a literal five-number mean, not another rolling implementation.
    for row in (119, 222, 450):
        for stock in (0, 5):
            prices = original.fields["close"].iloc[row - 4:row + 1, stock].tolist()
            expected = prices[-1] / (sum(prices) / 5) - 1
            assert cached.iloc[row, stock] == pytest.approx(expected, abs=1e-12)


def test_hand_oracle_distinguishes_pearson_rankic_and_constant_unknown():
    assert oracle.scalar_pearson([1, 2, 3], [1, 2, 100]) != pytest.approx(1)
    assert oracle.scalar_pearson(oracle.average_tie_ranks([1, 2, 3]),
                                 oracle.average_tie_ranks([1, 2, 100])) == pytest.approx(1)
    assert oracle.average_tie_ranks([4, 2, 2, 9]) == [3, 1.5, 1.5, 4]
    assert oracle.scalar_pearson([1, 1, 1], [2, 4, 6]) is None
    assert oracle.scalar_pearson([np.nan] * 3, [2, 4, 6]) is None


def test_independent_endpoint_oracle_uses_t_plus_six_and_purges_year_boundary():
    dates = pd.bdate_range("2018-12-17", periods=25).astype(str).tolist()
    opening = np.ones((25, 3)) * 10
    scores = np.tile([1., 2., 3.], (25, 1))
    pool = np.ones((25, 3), dtype=bool)
    opening[1] = [10, 20, 40]
    opening[6] = [11, 24, 80]
    rows = oracle.independent_daily(dates, opening, scores, pool,
        start=dates[0], end=dates[-1], direction=1, min_cross_section=3)
    assert rows[0]["pearson_ic"] == pytest.approx(oracle.scalar_pearson([1, 2, 3], [.1, .2, 1]))
    last_2018 = [r for r in rows if r["date"].startswith("2018")][-6:]
    assert all(r["pearson_ic"] is None and r["paired_count"] == 0 for r in last_2018)


def evaluator(panel):
    from quanta_agents.factor_research.evaluation import FactorEvaluator
    return FactorEvaluator(panel, train_start="2017-01-01", train_end="2017-12-31",
        min_cross_section=5, min_train_days=40, block_sessions=5, bootstrap_samples=20)


def assert_optional_close(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert actual == pytest.approx(expected, abs=1e-11)


def test_production_daily_and_annual_match_independent_endpoint_and_statistic_oracle():
    panel = synthetic_panel()
    # Absent endpoint must remove that stock from the pair, not become a zero return.
    panel.fields["open_observed"].iloc[330, 3] = 0
    # A constant cross-section must stay unknown despite otherwise valid labels.
    panel.fields["close"].iloc[360] = 30
    ev = evaluator(panel)
    spec = FactorSpec("raw_price_diagnostic", "close")
    report = ev.evaluate(spec, start="2018-01-01", end="2018-12-31")
    values = ev.compute(spec)
    daily = oracle.independent_daily(panel.dates.astype(str), panel.fields["open"], values,
        ev.pool, start="2018-01-01", end="2018-12-31", direction=report["direction"],
        min_cross_section=5, observed=panel.fields["open_observed"].to_numpy())
    assert len(daily) == len(report["daily"])
    for expected, actual in zip(daily, report["daily"]):
        assert actual["date"] == expected["date"]
        assert actual["paired_count"] == expected["paired_count"]
        assert actual["pool_count"] == expected["eligible_count"]
        assert_optional_close(actual["pearson_ic"], expected["pearson_ic"])
        assert_optional_close(actual["rank_ic"], expected["rank_ic"])
    annual = oracle.independent_annual(daily)[0]
    actual = report["annual"][0]
    assert actual["valid_days"] == annual["ic_days"]
    assert actual["paired_cells"] == annual["paired_observations"]
    assert_optional_close(actual["mean_pearson_ic"], annual["mean_pearson_ic"])
    assert_optional_close(actual["mean_rank_ic"], annual["mean_rank_ic"])
    assert report["daily"][-1]["pearson_ic"] is None
    reference = {"daily": daily, "annual": [annual]}
    assert oracle.compare_report(reference, report)["passed"]
    report["daily"][0]["pearson_ic"] = 8
    assert not oracle.compare_report(reference, report)["passed"]


def test_constant_and_nan_factors_never_have_a_successful_evaluation():
    ev = evaluator(synthetic_panel())
    for expression in ("close - close", "0 / 0"):
        report = ev.evaluate(FactorSpec("degenerate", expression), start="2018-01-01", end="2018-12-31")
        assert report["status"] == "insufficient_evidence"
        assert report["direction"] == 0
        assert report["summary"]["mean_pearson_ic"] is None
        assert report["summary"]["valid_days"] == 0


def test_increment_uses_same_training_cells_and_separates_sample_selection():
    panel = synthetic_panel()
    # Candidate selects a variable subset using an observed price condition.
    ev = evaluator(panel)
    candidate = FactorSpec("selective_candidate", "where(close > rolling_mean(close, 10), volume, 0 / 0)")
    base = [FactorSpec("base_short", "pct_change(close, 5)"),
            FactorSpec("base_long", "pct_change(close, 20)")]
    report = ev.incremental(candidate, base, start="2018-01-01", end="2018-12-31")
    assert report["status"] == "evaluated"
    assert report["entity_type"] == "predictor_comparison"
    assert report["models"]["baseline_common"]["sample_mask_id"] == report["models"]["augmented"]["sample_mask_id"]
    assert report["models"]["baseline_common"]["feature_order"] == report["models"]["augmented"]["feature_order"][:-1]
    assert report["original_train_sample_mask_id"] != report["train_sample_mask_id"]
    assert report["common_cells"] < report["baseline_original_cells"]
    deltas = []
    for row in report["daily"]:
        assert row["baseline_common_paired_count"] == row["augmented_paired_count"]
        if row["delta_pearson_ic"] is not None:
            assert row["delta_pearson_ic"] == pytest.approx(row["augmented_pearson_ic"] - row["baseline_common_pearson_ic"])
            deltas.append(row["delta_pearson_ic"])
    assert report["paired_delta_pearson_ic"] == pytest.approx(sum(deltas) / len(deltas))
    # Column input order cannot change a fixed deterministic matched comparison.
    reordered = ev.incremental(candidate, list(reversed(base)), start="2018-01-01", end="2018-12-31")
    assert reordered["models"] == report["models"]
    assert reordered["daily"] == report["daily"]
    # Reconstruct source-formula ranks and labels explicitly, then solve Ridge
    # through augmented least squares (production uses a regularized Gram solve).
    close = panel.fields["close"].to_numpy()
    opening = panel.fields["open"].to_numpy()
    volume = panel.fields["volume"].to_numpy()
    order = report["models"]["augmented"]["feature_order"]
    records = []
    for day, date in enumerate(panel.dates):
        if date.year != 2017 or day < 119 or day + 6 >= len(panel.dates) or panel.dates[day + 6].year != 2017:
            continue
        raw = {base[0].factor_id: close[day] / close[day - 5] - 1,
               base[1].factor_id: close[day] / close[day - 20] - 1,
               candidate.factor_id: np.array([volume[day, k] if close[day, k] > sum(close[day - 9:day + 1, k]) / 10
                                               else np.nan for k in range(close.shape[1])])}
        ranks = {}
        for identity, values in raw.items():
            observed = [k for k, value in enumerate(values) if np.isfinite(value)]
            result = np.full(len(values), np.nan)
            rr = oracle.average_tie_ranks([values[k] for k in observed])
            for k, rank in zip(observed, rr):
                result[k] = rank / len(observed) - .5
            ranks[identity] = result
        common = [k for k in range(close.shape[1]) if all(np.isfinite(ranks[identity][k]) for identity in order)]
        if len(common) < 5:
            continue
        labels = [opening[day + 6, k] / opening[day + 1, k] - 1 for k in common]
        target_ranks = np.array(oracle.average_tie_ranks(labels)) / len(common)
        target = target_ranks - target_ranks.mean()
        records.append((np.array([[ranks[identity][k] for identity in order] for k in common]), target))
    design = np.concatenate([record[0] for record in records])
    target = np.concatenate([record[1] for record in records])
    weights = np.concatenate([np.full(len(x), 1 / len(x) / len(records)) for x, _ in records])
    means = np.sum(design * weights[:, None], axis=0)
    scales = np.sqrt(np.sum((design - means) ** 2 * weights[:, None], axis=0))
    standardized = (design - means) / scales
    augmented_design = np.vstack([standardized * np.sqrt(weights[:, None]), np.sqrt(.1) * np.eye(len(order))])
    augmented_target = np.concatenate([target * np.sqrt(weights), np.zeros(len(order))])
    coefficients = np.linalg.lstsq(augmented_design, augmented_target, rcond=None)[0]
    np.testing.assert_allclose(report["models"]["augmented"]["coefficients"], coefficients, atol=1e-10, rtol=1e-10)
