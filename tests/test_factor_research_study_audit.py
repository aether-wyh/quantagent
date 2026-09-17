"""Independent fault-injection checks for V9A persistence and phase boundaries."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from quanta_agents.factor_research.generation import build_builtin_proposals
from quanta_agents.factor_research.protocol import default_protocol
from quanta_agents.factor_research import study as module


@pytest.fixture
def study(tmp_path, monkeypatch):
    # Source snapshots stay inside this temporary study; no market arrays load.
    stable_source = Path(module.__file__).parents[1] / "meta_v6" / "data.py"
    monkeypatch.setattr(module, "source_paths", lambda: [stable_source])
    instance = module.FactorStudy(tmp_path / "study")
    families = build_builtin_proposals()
    baseline = [module.factor_spec({"name": "baseline", "expression": "pct_change(close, 5)"})]
    instance.initialize(default_protocol(tmp_path / "project"), families, baseline,
                        origin={"kind": "synthetic_control_audit_no_market_execution"})
    return instance


def _mark_all_implementation_failed(study):
    for row in module.read(study.root / "expansion.json")["candidates"]:
        spec = module.factor_spec(row)
        module.once(study.root / "development" / (spec.factor_id + ".json"),
            {"factor_id": spec.factor_id, "candidate": row, "status": "implementation_failed",
             "error": "deliberate synthetic fixture"})


def test_freeze_then_confirm_blocks_search_and_second_admission(study):
    _mark_all_implementation_failed(study)
    frozen = study.freeze()
    assert frozen["selected"] == []
    with pytest.raises(ValueError, match="phase"):
        study.develop()
    study.confirm()
    assert study.state["phase"] == "complete"
    assert study.state["closed"] is True
    assert study.state["confirmation_accesses"] == 1
    with pytest.raises(ValueError, match="phase"):
        study.confirm()
    with pytest.raises(ValueError, match="phase"):
        study.develop()


def test_saved_protocol_cannot_expand_numeric_authority(study):
    changed = study.config
    changed["confirmation_end"] = "2025-12-31"
    module.write_json(study.root / "protocol.json", changed)
    with pytest.raises(ValueError):
        study.guard("development")


def test_source_code_pin_is_enforced_without_executing_changed_source(study, monkeypatch):
    pinned = next(iter(module.read(study.root / "source_pins.json")))
    original_sha = module.sha
    monkeypatch.setattr(module, "sha", lambda path: "f" * 64 if str(path) == pinned else original_sha(path))
    with pytest.raises(ValueError, match="source|pin|integrity"):
        study.guard("development")


def test_calendar_pin_is_checked_before_any_numeric_load(study, monkeypatch):
    calendar = study.config["data"]["calendar_path"]
    original_sha = module.sha
    monkeypatch.setattr(module, "sha", lambda path: "f" * 64 if str(path) == calendar else original_sha(path))
    import quanta_agents.meta_v6.data as data_module
    def forbidden(*args, **kwargs):
        pytest.fail("modified calendar reached numeric loader")
    monkeypatch.setattr(data_module, "load_market_panel", forbidden)
    with pytest.raises(ValueError, match="source|calendar|pin|integrity"):
        study._load("development")


def test_evaluation_failures_remain_counted_and_are_not_silently_retried(study, monkeypatch):
    calls = []
    def fail(spec, **kwargs):
        calls.append(spec.factor_id)
        raise ArithmeticError("deliberate evaluator failure")
    monkeypatch.setattr(study, "_load", lambda phase: object())
    monkeypatch.setattr(study, "_evaluator", lambda panel: SimpleNamespace(
        evaluate=fail, cache=SimpleNamespace(info={})))
    study.develop(limit=1)
    assert study.state["unique_evaluations_started"] == 1
    first = calls[0]
    report = module.read(study.root / "development" / (first + ".json"))
    assert report["status"] == "implementation_failed"
    study.develop(limit=1)
    assert study.state["unique_evaluations_started"] == 2
    assert calls.count(first) == 1


def test_crash_after_start_receipt_does_not_lose_budget_count(study, monkeypatch):
    real_state = study._state
    def crash(**changes):
        if "unique_evaluations_started" in changes:
            raise RuntimeError("fault after durable start before counter")
        real_state(**changes)
    monkeypatch.setattr(study, "_load", lambda phase: object())
    def fail(*args, **kwargs):
        raise ArithmeticError("synthetic evaluation failure")
    monkeypatch.setattr(study, "_evaluator", lambda panel: SimpleNamespace(
        evaluate=fail, cache=SimpleNamespace(info={})))
    monkeypatch.setattr(study, "_state", crash)
    with pytest.raises(RuntimeError, match="durable start"):
        study.develop(limit=1)
    assert len(list((study.root / "starts").glob("*.json"))) == 1
    monkeypatch.setattr(study, "_state", real_state)
    study.develop(limit=1)
    assert study.state["unique_evaluations_started"] == 1


def test_confirmation_admission_survives_crash_before_phase_transition(study, monkeypatch):
    _mark_all_implementation_failed(study)
    study.freeze()
    real_state = study._state
    def crash(**changes):
        if changes.get("phase") == "confirmation":
            raise RuntimeError("fault after durable confirmation admission")
        real_state(**changes)
    monkeypatch.setattr(study, "_state", crash)
    with pytest.raises(RuntimeError, match="durable confirmation"):
        study.confirm()
    assert (study.root / "confirmation_admission.json").exists()
    saved = module.read(study.root / "confirmation_admission.json")
    monkeypatch.setattr(study, "_state", real_state)
    study.confirm()
    assert study.state["phase"] == "complete"
    assert study.state["confirmation_accesses"] == 1
    assert module.read(study.root / "confirmation_admission.json") == saved


@pytest.mark.parametrize("name", ["baseline.json", "expansion.json", "proposals.json", "symbols.json"])
def test_initialized_research_inputs_cannot_drift_without_detection(study, name):
    target = study.root / name
    original = module.read(target)
    if name == "baseline.json":
        original[0]["expression"] = "close"
    elif name == "expansion.json":
        original["candidates"][0]["spec"]["expression"] = "close"
    elif name == "proposals.json":
        original["families"][0]["mechanism"] = "changed after initialization"
    else:
        original.pop()
    module.write_json(target, original)
    with pytest.raises(ValueError):
        study.guard("development")


def test_frozen_selection_content_is_verified_before_confirmation_admission(study):
    _mark_all_implementation_failed(study)
    study.freeze()
    frozen = module.read(study.root / "frozen_candidates.json")
    frozen["formula_and_direction_frozen"] = False
    module.write_json(study.root / "frozen_candidates.json", frozen)
    with pytest.raises(ValueError):
        study.confirm()
    assert not (study.root / "confirmation_admission.json").exists()


def test_modified_market_source_is_refused_before_loading_values(study, monkeypatch):
    import quanta_agents.meta_v6.data as data_module
    import quanta_agents.factor_research.adapters as adapters
    original = data_module.inspect_parquet_sources
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        result[0] = {**result[0], "sha256": "0" * 64}
        return result
    monkeypatch.setattr(data_module, "inspect_parquet_sources", changed)
    def forbidden(*args, **kwargs):
        pytest.fail("modified market source reached numerical loader")
    monkeypatch.setattr(adapters, "load_research_panel", forbidden)
    with pytest.raises(ValueError, match="source|snapshot"):
        study._load("development")
