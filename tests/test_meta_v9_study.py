"""Persistent V9 boundary checks using only temporary metadata and mock calls."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from quanta_agents.meta_v9 import study as s


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def initialized(tmp_path, monkeypatch, *, config_change=None):
    # These metadata/state tests do not depend on the developer machine's disk.
    monkeypatch.setattr(s.shutil, "disk_usage", lambda path: SimpleNamespace(free=10**12))
    source = tmp_path / "implementation.py"
    source.write_text("# synthetic source fixture\n", encoding="utf-8")
    monkeypatch.setattr(s, "source_files", lambda: [source])
    inventory = tmp_path / "inventory.json"
    write(inventory, {"executable_definitions": [
        {"id": "A", "name": "synthetic", "expression": "close", "roles": ["return"],
         "source": "generated test", "metadata": {}}]})
    cfg = s.default_config(tmp_path / "project")
    if config_change:
        config_change(cfg)
    result = s.V9Study(tmp_path / "study")
    result.initialize(cfg, inventory, {"unused_test_source": True})
    result.seal()
    return result, source


def receipt():
    return {"model": "gpt-6-astra", "effort": "xhigh", "runtime_identity": {"verified": True},
        "response": {"hypothesis": "synthetic", "falsifier": "counterexample", "pairs": []},
        "usage": {"input_tokens": 100, "output_tokens": 20,
                  "reasoning_output_tokens": 12, "cached_input_tokens": 30}}


def gateway(monkeypatch, calls):
    from quanta_agents.meta_v6 import gateway as g
    class Stub:
        def __init__(self, **kwargs):
            pass
        def run(self, **kwargs):
            calls.append(kwargs)
            folder = Path(kwargs["workdir"])
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "prompt.txt").write_text(kwargs["prompt"], encoding="utf-8")
            return receipt()
    monkeypatch.setattr(g, "CodexGateway", Stub)


def test_initialization_freezes_metadata_without_loading_numeric_data(tmp_path, monkeypatch):
    from quanta_agents.meta_v6 import data
    monkeypatch.setattr(data, "load_market_panel", lambda **kw: pytest.fail("initialization read market data"))
    study, _ = initialized(tmp_path, monkeypatch)
    assert study.config["data"]["authorized_end"] == "2020-12-31"
    assert study.config["data"]["end"] == "2020-12-31"
    assert study.config["asset_ids"] == ["A"]
    assert study.status()["model_calls"] == 0
    assert study.status()["account_starts"] == 0


def test_declaration_scope_cannot_include_fold_validation_year(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        initialized(tmp_path, monkeypatch,
            config_change=lambda cfg: cfg.update(declaration_end="2018-12-31"))


@pytest.mark.parametrize("file_name", ["config.json", "definitions.json"])
def test_frozen_config_and_definitions_mutation_is_detected(tmp_path, monkeypatch, file_name):
    study, _ = initialized(tmp_path, monkeypatch)
    path = study.root / file_name
    value = s.read(path)
    if file_name == "config.json":
        value["budget"]["max_accounts"] += 1
    else:
        value[0]["expression"] = "close * 2"
    write(path, value)
    with pytest.raises(ValueError, match="[Cc]hang|[Ff]roz|[Ii]mmut|[Dd]iffer|[Ii]ntegrity"):
        study.verify()


def test_model_receipt_reuse_preserves_budget_and_exact_input_binding(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch)
    calls = []
    gateway(monkeypatch, calls)
    first = study.model_call("declare", {"evidence": 1}, "frozen instruction")
    again = study.model_call("declare", {"evidence": 1}, "frozen instruction")
    assert first == again
    assert len(calls) == 1
    assert study.usage()["total_tokens"] == 120
    assert study.usage()["reasoning_output_tokens"] == 12
    with pytest.raises(ValueError, match="[Ff]roz|[Ii]nput|[Cc]hang|[Dd]iffer"):
        study.model_call("declare", {"evidence": 2}, "frozen instruction")
    assert len(calls) == 1


def test_previously_started_model_attempt_only_uses_offline_recovery(tmp_path, monkeypatch):
    from quanta_agents.meta_v6 import gateway as g
    study, _ = initialized(tmp_path, monkeypatch)
    calls = []
    gateway(monkeypatch, calls)
    write(study.root / "model_calls" / "declare" / "started.json", {"phase": "declare", "epoch": 0})
    def recovered_receipt(folder):
        # Simulate the original provider's preserved prompt artifact as well as
        # its receipt; offline recovery itself must not invoke the gateway.
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        saved_input = (folder.parent / "frozen_prompt.txt").read_text(encoding="utf-8")
        (folder / "prompt.txt").write_text(saved_input, encoding="utf-8")
        return receipt()
    monkeypatch.setattr(g, "verify_saved_completion", recovered_receipt)
    result = study.model_call("declare", {"evidence": 1}, "frozen instruction")
    assert result["offline_recovery"] is True
    assert calls == []
    assert study.status()["model_calls"] == 1


def test_model_budget_stops_new_phase_before_gateway(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch,
        config_change=lambda cfg: cfg["budget"].update(max_model_calls=1))
    calls = []
    gateway(monkeypatch, calls)
    study.model_call("declare", {"evidence": 1}, "instruction")
    with pytest.raises(ValueError, match="budget"):
        study.model_call("select", {"evidence": 2}, "instruction")
    assert len(calls) == 1
    assert study.status()["model_calls"] == 1


def test_account_budget_and_finished_callback_do_not_cancel_later_phases(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch,
        config_change=lambda cfg: cfg["budget"].update(max_accounts=1, account_timeout_seconds=10))
    now = [100.]
    monkeypatch.setattr(s.time, "monotonic", lambda: now[0])
    study.reserve_account("fold_0:ridge", "generated-account")
    assert study.cancelled() is False
    now[0] = 111.
    assert study.cancelled() is True
    study.event("development", detail={"event": "account_finished", "identity": "generated-account"})
    assert study.cancelled() is False
    with pytest.raises(ValueError, match="budget"):
        study.reserve_account("fold_0:benchmark", "generated-account-2")
    assert study.status()["account_starts"] == 1


def test_known_failed_call_usage_is_counted_without_calling_it_verified(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch)
    folder = study.root / "model_calls" / "declare"
    write(folder / "started.json", {"phase": "declare", "epoch": 0})
    write(folder / "gateway_failure.json", {"error": "generated fixture failure", "usage": receipt()["usage"], "retry": False})
    usage = study.usage()
    assert usage["total_tokens"] == 120
    assert usage["calls"][0]["verified"] is False
    assert usage["unknown_usage_calls"] == []


def report(completed=3):
    spec = {"version": 1, "name": "frozen", "score": {"op": "factor", "id": "A"}, "allocation": {}}
    return {"methods": {"ridge": {"completed_folds": completed}}, "final_fit_status": "fitted",
        "final_strategy_specs": {"ridge": spec},
        "final_fit": {"artifact_sha256": "fit-hash", "fit_input_sha256": "input-hash"}}


def selection(method="ridge"):
    return {"method": method, "conclusion": "synthetic decision",
        "evidence_for_choice": ["generated fixture"], "remaining_uncertainty": "not independent"}


def test_incomplete_method_cannot_be_promoted_and_no_numeric_load(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch)
    write(study.root / "development_report.json", report(completed=2))
    with pytest.raises(ValueError, match="complete"):
        study.select(decision=selection())
    assert not (study.root / "selected_strategy.json").exists()


def test_frozen_selection_cannot_be_changed_after_diagnostic_unlock(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch)
    write(study.root / "development_report.json", report())
    chosen = study.select(decision=selection())
    frozen = deepcopy(s.read(study.root / "selected_strategy.json"))
    write(study.root / "diagnostic_unlocked.json", {"reselection_allowed": False})
    assert study.select(decision=selection("equal_rank")) == chosen
    assert s.read(study.root / "selected_strategy.json") == frozen


def test_rejected_method_does_not_unlock_or_load_later_data(tmp_path, monkeypatch):
    from quanta_agents.meta_v6 import data
    study, _ = initialized(tmp_path, monkeypatch)
    write(study.root / "selection.json", selection("reject"))
    monkeypatch.setattr(data, "load_market_panel", lambda **kw: pytest.fail("rejected method read later data"))
    assert study.diagnose()["status"] == "not_unlocked_rejected_in_development"
    assert not (study.root / "diagnostic_unlocked.json").exists()


def test_nonrejected_study_cannot_close_without_diagnostic_report(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch)
    write(study.root / "selection.json", selection())
    with pytest.raises((ValueError, FileNotFoundError)):
        study.close(decision={"conclusion": "premature", "robust_strategy_supported": False,
                              "recommended_status": "research_candidate_only"})
    assert not (study.root / "closed.json").exists()


def packet_report(config):
    features = [{"id": "A", "kind": "main_effect", "factor_ids": ["A"]}]
    pairs = [["A", "B"], ["A", "C"], ["B", "C"]]
    features.extend({"id": "interaction:" + ":".join(pair), "kind": "centered_rank_product",
                     "factor_ids": pair} for pair in pairs)
    fitted = {"selected_factors": ["A"],
        "model_status": {"equal_rank": {"status": "fitted"}, "ridge": {"status": None},
            "ridge_augmented": {"status": "unavailable", "reason": "generated missing support"},
            "ridge_interactions": {"status": "fitted"}},
        "models": {"ridge_interactions": {"features": features,
            "coefficients": [99., .125, -.25, 0.], "feature_scales": [100., .5, .0625, .125]}}}
    folds = [{"plan": fold, "fit_status": "fitted", "fit": deepcopy(fitted),
              "accounts": {}, "attribution": {}, "interaction_control": {"status": "not_evaluable"}}
             for fold in config["folds"]]
    return {"methods": {}, "folds": folds, "final_fit_status": "fitted", "final_fit": fitted,
        "final_strategy_specs": {"ridge_interactions": {"marker": "generated complete recipe"},
                                 "equal_rank": {"marker": "generated complete recipe"}},
        "account_denominator": {"declared": 0, "completed": 0},
        "limitations": ["generated metadata only"]}


def test_selection_packet_preserves_final_fit_eligibility_and_signed_pair_terms(tmp_path, monkeypatch):
    study, _ = initialized(tmp_path, monkeypatch)
    write(study.root / "declaration.json", {"hypothesis": "generated", "falsifier": "generated", "pairs": []})
    source = packet_report(study.config)
    original = deepcopy(source)
    packet = study.selection_packet(source)
    assert packet["final_fit_status"] == "fitted"
    assert packet["final_model_status"] == {"equal_rank": "fitted", "ridge": None,
        "ridge_augmented": "unavailable", "ridge_interactions": "fitted"}
    assert packet["available_specs"] == ["equal_rank", "ridge_interactions"]
    expected = [
        {"factor_ids": ["A", "B"], "coefficient": .125, "feature_scale": .5},
        {"factor_ids": ["A", "C"], "coefficient": -.25, "feature_scale": .0625},
        {"factor_ids": ["B", "C"], "coefficient": 0., "feature_scale": .125}]
    assert packet["final_interaction_terms"] == expected
    assert all(fold["interaction_terms"] == expected for fold in packet["folds"])
    assert "coefficient/feature_scale" in packet["interaction_coefficient_semantics"]
    assert "not causal effect" in packet["interaction_coefficient_semantics"]
    assert source == original
    json.dumps(packet, allow_nan=False)


@pytest.mark.parametrize("fit_status", ["failed", None])
def test_selection_packet_does_not_infer_fit_success_from_selected_factors(tmp_path, monkeypatch, fit_status):
    study, _ = initialized(tmp_path, monkeypatch)
    write(study.root / "declaration.json", {"hypothesis": "generated", "falsifier": "generated", "pairs": []})
    source = packet_report(study.config)
    source.update(final_fit_status=fit_status, final_fit=None, final_strategy_specs={})
    source["folds"][0].update(fit_status=fit_status, fit=None)
    packet = study.selection_packet(source)
    assert packet["final_fit_status"] == fit_status
    assert packet["final_model_status"] == {}
    assert packet["available_specs"] == []
    assert packet["final_interaction_terms"] == []
    assert packet["folds"][0]["fit_status"] == fit_status
    assert packet["folds"][0]["interaction_terms"] == []
