"""Generated-input parity with the reviewed calendar source; no market values."""
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec
from quanta_agents.meta_v7 import assets as module
from quanta_agents.meta_v7.assets import V7AssetRegistry

CALENDAR = Path("D:/大学/金融投资与量化/因子日历测试")


@pytest.fixture(scope="module")
def original():
    path = CALENDAR / module._SOURCE
    if not path.exists():
        pytest.skip("reviewed external calendar source unavailable; no source parity claim")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == module._SOURCE_SHA256
    spec = importlib.util.spec_from_file_location("_v7_reviewed_calendar_test", path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


@pytest.fixture(scope="module")
def generated():
    rng = np.random.default_rng(731)
    close = 20 * np.exp(np.cumsum(rng.normal(0, .012, (1340, 4)), axis=0))
    opening = close * np.exp(rng.normal(0, .007, close.shape))
    high = np.maximum(close, opening) + rng.uniform(.05, .4, close.shape)
    low = np.minimum(close, opening) - rng.uniform(.05, .4, close.shape)
    volume = rng.uniform(1000, 1000000, close.shape)
    arrays = {"close": close, "open": opening, "high": high, "low": low,
              "volume": volume, "amount": close * volume}
    for index, key in enumerate(arrays):
        arrays[key][430 + index * 7, index % 4] = np.nan
    arrays["volume"][700, 1] = 0
    arrays["amount"][710, 2] = 0
    arrays["open"][720, 3] = 0
    arrays["close"][850:890, 2] = 12  # Flat windows exercise variance/zero-denominator semantics.
    arrays["high"][740, 0] = arrays["low"][740, 0]  # zero high-low range
    dates = pd.bdate_range("2010-01-01", periods=len(close), name="date")
    frames = {k: pd.DataFrame(v, index=dates, columns=pd.Index(list("ABCD"), name="stock")) for k, v in arrays.items()}
    eligible = pd.DataFrame(True, index=dates, columns=frames["close"].columns)
    eligible.iloc[1310, 1] = False
    panel = MarketPanel(frames, eligible, {"kind": "generated_test", "scope": "synthetic source-function parity only"})
    return panel, arrays


@pytest.mark.parametrize("name", sorted(module._reviewed_expressions()))
def test_exact_original_formula_and_missing_mask_on_generated_inputs(original, generated, name):
    panel, arrays = generated
    expr = module._reviewed_expressions()[name]
    actual = FactorEngine(panel).compute(FactorSpec(name, expr)).to_numpy()
    expected = original._finish(getattr(original, name)(arrays)).astype(float)
    expected[~panel.eligible.to_numpy()] = np.nan
    np.testing.assert_array_equal(np.isfinite(actual), np.isfinite(expected))
    # Engine is float64; original wrapper exports float32. Source cumulative
    # sum/moment roundoff does not imply bit-exact numerical algorithms.
    np.testing.assert_allclose(actual, expected, rtol=2e-5, atol=2e-6, equal_nan=True)


def test_ingestion_is_metadata_only_and_does_not_execute_source(tmp_path, original, monkeypatch):
    monkeypatch.setattr(original, "calculate_factor", lambda *a, **k: pytest.fail("ingestion executed source"))
    registry = V7AssetRegistry(tmp_path)
    result = registry.ingest_calendar(CALENDAR)
    assert result["executable"] >= 30
    assert result["source_definitions"] == len({spec.calculator.__name__ for spec in original.FACTOR_REGISTRY.values()})
    assert len(result["unavailable"]) > 0 and result["catalogued"] == 0
    assert registry.ingest_calendar(CALENDAR)["ids"] == result["ids"]
    entry = registry.get("calendar.standard.mtm")
    assert entry["expression"] == "close - lag(close, 12)"
    assert entry["source"]["function"] == "mtm" and entry["source"]["line"] == 342
    assert len(entry["source"]["function_sha256"]) == 64 and len(entry["source"]["helper_proofs"]) > 5
    assert not entry["metadata"]["input_values_read"] and not entry["profitability_claim"]
    unavailable = registry.get("calendar.standard.tema")
    assert not unavailable["executable"] and unavailable["expression"] is None
    assert "EMA" in unavailable["unavailable_reason"]


def test_changed_calendar_source_cannot_be_blessed_by_new_hash(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / module._SOURCE).write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    registry = V7AssetRegistry(tmp_path / "registry")
    with pytest.raises(ValueError, match="unreviewed"):
        registry.ingest_calendar(source)
    assert registry.list() == []


def test_v7_import_alias_is_the_new_subclass_and_bad_report_is_explicit(tmp_path):
    assert module.AssetRegistry is V7AssetRegistry
    registry = module.AssetRegistry(tmp_path)
    registry.register({"id": "one", "expression": "close"})
    for report in ([], {"scope": []}):
        with pytest.raises(ValueError, match="object"):
            registry.describe_candidates(["one"], report)


def test_shared_root_retains_cross_study_cache_and_aliases(tmp_path, generated, monkeypatch):
    panel, _ = generated
    root = tmp_path / "shared"
    first = V7AssetRegistry(root)
    first.register({"id": "a", "expression": "rolling_mean(close,5)"})
    first.register({"id": "alias", "expression": "rolling_mean((close),5)"})
    frames, stats = first.resolve(["a", "alias"], panel)
    assert stats["computed"] == stats["alias_reuses"] == 1
    second = V7AssetRegistry(root)
    monkeypatch.setattr(FactorEngine, "compute", lambda *a, **k: pytest.fail("shared cache recomputed"))
    cached, second_stats = second.resolve(["alias"], panel)
    assert second_stats["computed"] == 0 and second_stats["cache_hits"] == 1
    assert_frame_equal(frames["a"], cached["alias"])


def test_required_field_failure_is_local_and_explicit(tmp_path, generated):
    panel, _ = generated
    registry = V7AssetRegistry(tmp_path)
    registry.register({"id": "bad", "expression": "missing_industry_exposure"})
    registry.register({"id": "good", "expression": "close-lag(close,5)"})
    frames, stats = registry.resolve(["bad", "good"], panel)
    assert set(frames) == {"good"} and not stats["complete"]
    assert stats["unavailable"]["bad"]["missing_fields"] == ["missing_industry_exposure"]


def test_candidate_shape_and_training_score_neighbors_are_not_algebra_or_return_correlation(tmp_path):
    registry = V7AssetRegistry(tmp_path)
    for name, expression in (("ma5", "rolling_mean(close,5)"), ("alias", "rolling_mean((close),5)"),
                             ("ma10", "rolling_mean(close,10)"), ("algebra", "close+close"), ("other", "2*close")):
        registry.register({"id": name, "expression": expression})
    report = {"status": "completed", "scope": {"start": "2016-01-01", "end": "2020-12-31", "role": "training_development"},
              "correlations": [{"left": "ma5", "right": "ma10", "mean_ic": .8, "observed_days": 100},
                               {"left": "ma5", "right": "unknown", "mean_ic": 1}]}
    result = registry.describe_candidates(["ma5", "algebra"], report)
    assert {row["kind"] for row in result["formula_neighbors"]} == {"canonical_expression_identical", "same_syntax_shape_different_parameters"}
    assert all(row["query"] != "algebra" for row in result["formula_neighbors"])
    assert len(result["score_neighbors"]) == 1
    assert result["score_neighbors"][0]["scope"]["end"] == "2020-12-31"
    assert not result["independent_evidence_claimed"] and len(result["diagnostic_report_sha256"]) == 64
    report["scope"]["role"] = "validation"
    with pytest.raises(ValueError, match="training-scoped"):
        registry.describe_candidates(["ma5"], report)


def test_metadata_catalogue_does_not_promote_expression_or_result_columns(tmp_path):
    source = tmp_path / "mapping.csv"
    source.write_text("record_id,name,expression,mean_ic,net_sharpe\n01,old,close,0.9,9\n", encoding="utf-8")
    registry = V7AssetRegistry(tmp_path / "registry")
    summary = registry.import_metadata(source, "calendar")
    entry = registry.get(summary["ids"][0])
    assert entry["status"] == "catalogued" and not entry["executable"] and entry["expression"] is None
    assert "mean_ic" not in str(entry) and "net_sharpe" not in str(entry)
