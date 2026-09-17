"""Synthetic export fault checks; no historical market loader is called."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_research import export as module
from quanta_agents.factor_research.study import sha, source_paths
from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec
from quanta_agents.research_kernel.store import digest


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding="utf-8")


@pytest.fixture
def export_case(tmp_path):
    dates = pd.bdate_range("2018-01-01", periods=160, name="date")
    symbols = pd.Index(["sh600001", "sh600002", "sh600003", "sh600004", "sh600005"], name="symbol")
    values = 10. + np.arange(len(dates) * len(symbols)).reshape(len(dates), len(symbols)) / 1000
    opening = pd.DataFrame(values, index=dates, columns=symbols)
    pool = opening.notna()
    panel = MarketPanel({"open": opening, "close": opening + .5,
                         "open_observed": opening * 0 + 1}, pool,
                        {"factor_research": {"allowed_signal_fields": ["open", "close"]}})
    spec = FactorSpec("frozen_export", "close")
    engine = FactorEngine(panel)
    evaluator = SimpleNamespace(panel=panel, engine=engine, pool=pool,
                                universe_id="synthetic_pool", compute=engine.compute)
    study = SimpleNamespace(root=tmp_path / "study", expansion_path=tmp_path / "study" / "expansion.json",
        config={"label": {"formula": "open[t+6]/open[t+1]-1", "horizon": 5},
                "baseline": {"asset_ids": ["F2", "F3", "F7"], "ridge_lambda": .1},
                "limitations": ["synthetic_export_contract_test"]})
    row = {"spec": spec.to_dict(), "family_id": "test.family", "arm": "llm_structure",
           "parameters": {}, "control_ids": {}, "main_effect_ids": [],
           "proposal_id": "test.proposal", "trial_id": "test.trial"}
    selected = [{"factor_id": spec.factor_id, "direction": -1}]
    save(study.expansion_path, {"candidates": [row]})
    save(study.root / "source_pins.json", {str(p): sha(p) for p in source_paths()})
    save(study.root / "development" / (spec.factor_id + ".json"),
         {"train": {"direction_fit": {"direction": -1}, "annual": []},
          "development": {"annual": []}})
    save(study.root / "confirmation" / (spec.factor_id + ".json"),
         {"historical_target_met": False, "report": {"annual": []}, "status": "evaluated"})
    save(study.root / "confirmation_data_manifest.json", {"source": "synthetic"})
    return study, evaluator, {spec.factor_id: row}, selected, spec


def test_export_axes_and_raw_scores_direction_applied_once(export_case):
    study, evaluator, rows, selected, spec = export_case
    result = module.export_bundles(study, evaluator, rows, selected)
    imported, bundle = module.load_bundle(result[0]["bundle"])
    assert bundle["direction"] == -1
    expected = evaluator.compute(spec)
    with np.load(result[0]["audit_snapshot"], allow_pickle=False) as saved:
        assert saved["dates"].tolist() == expected.index.to_numpy().tolist()
        assert saved["symbols"].tolist() == list(expected.columns)
        np.testing.assert_allclose(saved["scores"], expected.to_numpy())
        # Saved values are raw; a downstream consumer applies the separately
        # frozen orientation once, after the imported expression is evaluated.
        np.testing.assert_allclose(saved["scores"] * bundle["direction"],
            FactorEngine(evaluator.panel).compute(imported).to_numpy() * -1)
    assert result[0]["reimport_equal"] is True


def test_export_rejects_same_numbers_with_wrong_stock_columns(export_case):
    study, evaluator, rows, selected, spec = export_case
    actual = evaluator.compute(spec)
    wrong = actual.copy()
    wrong.columns = actual.columns[::-1]
    evaluator.compute = lambda requested: wrong.copy()
    with pytest.raises(ValueError):
        module.export_bundles(study, evaluator, rows, selected)


def test_export_does_not_bless_incomplete_preexisting_snapshot(export_case):
    study, evaluator, rows, selected, spec = export_case
    path = study.root / "bundles" / (spec.factor_id + "_audit.npz")
    path.parent.mkdir(parents=True)
    # Simulate a stopped previous write before any bundle manifest existed.
    np.savez_compressed(path, dates=np.array(["2018-01-01"], dtype="datetime64[ns]"),
        symbols=np.array(["wrong_symbol"]), open=np.zeros((1, 1)), scores=np.zeros((1, 1)),
        pool=np.ones((1, 1), dtype=bool))
    with pytest.raises(ValueError):
        module.export_bundles(study, evaluator, rows, selected)
    assert not (study.root / "bundles" / "manifest.json").exists()


def test_bundle_rejects_changed_calculator_even_with_valid_content_digest(export_case):
    study, evaluator, rows, selected, spec = export_case
    result = module.export_bundles(study, evaluator, rows, selected)
    path = Path(result[0]["bundle"])
    bundle = json.loads(path.read_text(encoding="utf-8"))
    factor_source = next(key for key in bundle["calculator_source_hashes"]
                         if Path(key).name == "factors.py")
    bundle["calculator_source_hashes"][factor_source] = "0" * 64
    bundle["bundle_sha256"] = digest({k: v for k, v in bundle.items() if k != "bundle_sha256"})
    other = study.root / "valid_bundle_for_other_calculator.json"
    save(other, bundle)
    with pytest.raises(ValueError):
        module.load_bundle(other)
