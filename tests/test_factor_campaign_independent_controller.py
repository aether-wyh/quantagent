"""Independent controller regression cases; no market or real model is invoked."""
from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from quanta_agents.factor_campaign import campaign as module
from quanta_agents.factor_campaign.campaign import Campaign, once, read, sha
from quanta_agents.factor_campaign.protocol import default_protocol
from quanta_agents.factor_campaign.selection import version_decision, factor_pool, memberships
from quanta_agents.meta_v6.factors import FactorSpec
from quanta_agents.research_kernel.store import write_json


def bare_campaign(tmp_path):
    cfg = default_protocol(tmp_path / "source")
    once(tmp_path / "protocol.json", cfg)
    once(tmp_path / "protocol_identity.json", {"sha256": sha(tmp_path / "protocol.json")})
    state = {"version": "V10A", "phase": "prepared", "batch": 0, "primary_evaluated": 0,
             "combinations_evaluated": 0, "new_evaluated": 0, "reference_evaluated": 0,
             "best_factor_floor": None, "best_combination_floor": None, "numeric_wall_seconds": 0.,
             "numeric_cpu_seconds": 0., "stop_requested": False, "historical_target_met": False,
             "plateau_extensions": 0, "failures": 0}
    write_json(tmp_path / "state.json", state)
    version = tmp_path / "versions/V10A"
    for name, value in (("catalog.json", []), ("summaries.json", {}), ("combination_summaries.json", {})):
        write_json(version / name, value)
    once(tmp_path / "reference_catalog.json", [])
    return Campaign(tmp_path)


def row(name, *, origin="new", role="return", entity="single_factor"):
    spec = FactorSpec(name, f"close + {len(name)}")
    return {"factor_id": name, "spec": spec.to_dict(), "origin": origin,
            "roles": [role], "entity_type": entity, "controls": [], "parameters": {}, "family_id": name}


def evidence(quality=.1):
    return {"direction": 1, "direction_fit": {"raw_train_mean_pearson_ic": quality},
            "annual": [{"year": year, "mean_pearson_ic": .02, "valid_days": 210,
                        "evaluation_coverage": .9} for year in range(2019, 2025)]}


def test_budget_cap_reaches_review_without_marking_financial_goal_complete(tmp_path):
    campaign = bare_campaign(tmp_path)
    budget = campaign.config["budget"]
    state = {**campaign.state, "primary_evaluated": 299, "combinations_evaluated": 200,
             "numeric_wall_seconds": 21600}
    assert version_decision(state, budget) == "review_incomplete_scale"
    state["primary_evaluated"] = 300
    assert version_decision(state, budget) == "review_completed_scale"
    assert state["historical_target_met"] is False
    state.update(numeric_wall_seconds=1, plateau_extensions=1)
    assert version_decision(state, budget) == "extend"
    state["plateau_extensions"] = 2
    assert version_decision(state, budget) == "review_completed_scale"


def test_search_counts_separate_controls_duplicates_failures_and_composite_formulas(tmp_path):
    campaign = bare_campaign(tmp_path)
    rows = [row("reference", origin="reference"), row("new"), row("control", origin="control"),
            row("duplicate"), row("aggregate", entity="combination"), row("failed")]
    reports = {r["factor_id"]: evidence() for r in rows if r["factor_id"] != "failed"}
    reports["duplicate"]["numeric_duplicate_of"] = "new"
    combos = {"good": {**evidence(), "status": "evaluated"},
              "failed": {**evidence(), "status": "fit_unavailable"},
              "partial": {**evidence(), "status": "partial_fit_unavailable"},
              "dupe": {**evidence(), "status": "evaluated", "numeric_duplicate_of": "good"}}
    write_json(campaign.version_root / "catalog.json", rows)
    write_json(campaign.version_root / "summaries.json", reports)
    write_json(campaign.version_root / "combination_summaries.json", combos)
    campaign._recount()
    assert campaign.state["primary_evaluated"] == 2
    assert campaign.state["new_evaluated"] == 1
    assert campaign.state["combinations_evaluated"] == 1
    assert campaign.state["controls_evaluated"] == 1


def test_condition_and_complement_survive_low_marginal_ic_and_future_results_do_not_change_members():
    rows = [row(f"f{i}", role="condition" if i == 0 else "return") for i in range(7)]
    reports = {r["factor_id"]: evidence(.1 - i * .01) for i, r in enumerate(rows)}
    reports["f0"]["direction_fit"]["raw_train_mean_pearson_ic"] = .00001
    reports["f6"].update(complementarity_passed=True, complementarity_delta=.004)
    pool = factor_pool(rows, reports, maximum=4)
    assert {"f0", "f6"} <= {r["factor_id"] for r in pool}
    signals = {r["factor_id"]: np.random.default_rng(i).normal(size=150) for i, r in enumerate(rows)}
    original = memberships(rows, reports, signals, sizes=(4,))
    changed = copy.deepcopy(reports)
    for i, report in enumerate(changed.values()):
        for annual in report["annual"]:
            annual["mean_pearson_ic"] = 999 - i
    assert memberships(rows, changed, signals, sizes=(4,)) == original


def test_model_resume_uses_original_preregistered_context_not_live_changed_state(tmp_path, monkeypatch):
    from quanta_agents.factor_campaign import model
    campaign = bare_campaign(tmp_path)
    observed = []
    class FakeLoop:
        def __init__(self, root):
            pass
        def request(self, action, kind, context):
            observed.append(copy.deepcopy(context))
            return {"status": "waiting", "blocker": {"kind": "synthetic_timeout"}}
    monkeypatch.setattr(model, "ModelLoop", FakeLoop)
    campaign._model("same_action", "review", {"batch": 0, "quality": .01})
    campaign._model("same_action", "review", {"batch": 99, "quality": .99})
    assert observed == [{"batch": 0, "quality": .01}] * 2


def test_cached_fake_acceptance_never_bypasses_fresh_oracle_call(tmp_path, monkeypatch):
    campaign = bare_campaign(tmp_path)
    write_json(tmp_path / "acceptance/authority.json", {"synthetic_placeholder": True})
    factor = row("candidate")
    report = evidence()
    for annual in report["annual"]:
        annual["mean_pearson_ic"] = .2
    write_json(campaign.version_root / "catalog.json", [factor])
    write_json(campaign.version_root / "summaries.json", {"candidate": report})
    folder = campaign.version_root / "factors/candidate"
    once(folder / "independent_acceptance.json", {"verdict": {"accepted": True},
                                                  "source_verified": True, "replay_verified": True})
    calls = []
    monkeypatch.setattr(campaign, "_audit", lambda folder: calls.append(folder) or {
        "verdict": {"accepted": False}, "source_verified": True, "replay_verified": True})
    assert campaign.verify_contenders() is False
    assert calls == [folder] and campaign.state["historical_target_met"] is False


def test_complement_interruption_preserves_batch_baseline_and_already_discovered_increment(tmp_path, monkeypatch):
    from quanta_agents.factor_campaign import combination, selection
    campaign = bare_campaign(tmp_path)
    rows = [row(f"f{i}") for i in range(6)]
    for source, name in zip(rows[:4], ("F1", "F2", "F3", "F7")):
        source["spec"]["name"] = name
    write_json(campaign.root / "reference_catalog.json", rows[:4])
    write_json(campaign.version_root / "catalog.json", rows)
    reports = {r["factor_id"]: evidence() for r in rows}
    reports["f4"]["high_correlation_ids"] = ["f0"]
    write_json(campaign.version_root / "summaries.json", reports)
    monkeypatch.setattr(campaign, "context", lambda: SimpleNamespace(register=lambda _: None))
    # f4 is currently excluded from the selected pool for redundancy. It still
    # needs one common-sample increment opportunity so rescue is reachable.
    monkeypatch.setattr(module, "factor_pool", lambda rows, summaries: rows[:4])
    monkeypatch.setattr(campaign, "_signatures", lambda: {})
    monkeypatch.setattr(selection, "memberships", lambda *a, **k: [{"feature_ids": tuple(f"f{i}" for i in range(4))}])
    class FakeEvaluator:
        def __init__(self, *args, **kwargs):
            pass
        def paired_increment(self, base, augmented, **kwargs):
            positive = "f4" in augmented.feature_ids
            return {"status": "evaluated", "valid_days": 100,
                    "paired_delta_pearson_ic": .01 if positive else -.01}
    monkeypatch.setattr(combination, "CombinationEvaluator", FakeEvaluator)
    calls = 0
    def first_run_ready():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("after first candidate checkpoint")
        return True
    monkeypatch.setattr(campaign, "_resource_ready", first_run_ready)
    with pytest.raises(KeyboardInterrupt):
        campaign.complement_batch(maximum=2)
    saved = read(campaign.version_root / "batches/0000_increment/baseline.json")
    assert saved["candidate_ids"] == ["f4", "f5"]
    monkeypatch.setattr(campaign, "_resource_ready", lambda: True)
    increment = campaign.complement_batch(maximum=2)
    assert read(campaign.version_root / "batches/0000_increment/baseline.json") == saved
    assert increment == 1  # The first discovery belongs to this interrupted batch.


def test_later_version_preparation_keeps_inherited_candidates_and_their_origin(tmp_path, monkeypatch):
    campaign = bare_campaign(tmp_path)
    campaign._state(version="V11A", last_parent_version="V10A")
    reference = row("ref", origin="reference")
    inherited = {**row("prior_mechanism", origin="inherited"), "inherited_from_version": "V10A"}
    write_json(tmp_path / "reference_catalog.json", [reference])
    write_json(campaign.version_root / "inherited_catalog.json", [reference, inherited])
    write_json(campaign.version_root / "catalog.json", [reference, inherited])
    write_json(campaign.version_root / "framework_origin.json", {"parent_version": "V10A", "patch_id": "reviewed_patch"})
    write_json(tmp_path / "versions/V10A/batches/0000_parents.json", [{"parent_id": "prior_mechanism"}])
    received = []
    monkeypatch.setattr(campaign, "_model", lambda action, kind, context: received.append(context) or {"templates": []})
    monkeypatch.setattr(campaign, "_bind_lineage", lambda rows: rows)
    monkeypatch.setattr(module, "expand", lambda families, **kwargs: ([], []))
    monkeypatch.setattr(module, "library_neighborhoods", lambda refs: [])
    campaign.prepare()
    retained = {r["factor_id"]: r for r in read(campaign.version_root / "catalog.json")}
    assert "prior_mechanism" in retained
    assert retained["prior_mechanism"]["origin"] == "inherited"
    assert retained["prior_mechanism"]["inherited_from_version"] == "V10A"
    assert "prior_mechanism" in {r["id"] for r in received[0]["registered_parents"]}


def test_admission_reserves_memory_for_first_panel_and_job_temporaries(tmp_path, monkeypatch):
    from quanta_agents.factor_campaign import resources
    campaign = bare_campaign(tmp_path)
    requests = []
    class Guard:
        def __init__(self, root):
            pass
        def check(self, **kwargs):
            requests.append(kwargs)
            return {"allowed": True}
    monkeypatch.setattr(resources, "ResourceGuard", Guard)
    assert campaign._resource_ready()
    campaign._context = object()
    assert campaign._resource_ready()
    assert requests[0]["required_memory_bytes"] > 0
    assert requests[1]["required_memory_bytes"] > 0


def control_repair_fixture(tmp_path, monkeypatch, *, two=False):
    campaign = bare_campaign(tmp_path)
    controls = [{"name": "price_effect", "expression_template": "pct_change(close, {w}))", "rationale": "price main effect"}]
    if two:
        controls.append({"name": "volume_effect", "expression_template": "pct_change(volume, {w}))", "rationale": "volume main effect"})
    family = {"family_id": "conditional_family", "expression_template": "close / rolling_mean(close, {w}) - 1",
              "parameters": [{"name": "w", "values": [5, 10]}], "role": "condition", "route": "condition",
              "mechanism": "fixed price-volume condition", "parents": [], "controls": controls,
              "falsifier": "no increment after main effects"}
    rows, attempts = module.expand([family], origin={"kind": "synthetic_model"})
    write_json(campaign.version_root / "catalog.json", rows)
    write_json(campaign.version_root / "initial_expansion.json", {"model_attempts": attempts})
    monkeypatch.setattr(campaign, "_bind_lineage", lambda rows: rows)
    return campaign, attempts


def test_control_syntax_repair_retains_original_failures_and_is_applied_once(tmp_path, monkeypatch):
    campaign, initial = control_repair_fixture(tmp_path, monkeypatch)
    calls = []
    def repair(action, kind, context):
        calls.append(action)
        return {"parent_id": "conditional_family", "expression": "pct_change(close, {w})", "reason": "remove one extra closing parenthesis"}
    monkeypatch.setattr(campaign, "_model", repair)
    assert campaign.repair_controls()
    assert campaign.repair_controls()
    assert len(calls) == 1
    assert read(campaign.version_root / "initial_expansion.json")["model_attempts"] == initial
    catalog = read(campaign.version_root / "catalog.json")
    assert sum(r["origin"] == "control" for r in catalog) == 2
    assert all(r["spec"]["expression"] != "close" for r in catalog)


def test_control_syntax_repair_cannot_change_economic_expression(tmp_path, monkeypatch):
    campaign, initial = control_repair_fixture(tmp_path, monkeypatch)
    before = read(campaign.version_root / "catalog.json")
    monkeypatch.setattr(campaign, "_model", lambda *a, **k: {
        "parent_id": "conditional_family", "expression": "close", "reason": "pretend syntax repair"})
    assert campaign.repair_controls() is False
    assert read(campaign.version_root / "catalog.json") == before
    assert read(campaign.version_root / "initial_expansion.json")["model_attempts"] == initial


def test_two_broken_controls_in_same_family_can_be_repaired_sequentially(tmp_path, monkeypatch):
    campaign, initial = control_repair_fixture(tmp_path, monkeypatch, two=True)
    calls = []
    def repair(action, kind, context):
        calls.append(action)
        expression = context["broken_control"]["expression_template"][:-1]
        return {"parent_id": "conditional_family", "expression": expression, "reason": "remove one extra closing parenthesis"}
    monkeypatch.setattr(campaign, "_model", repair)
    assert campaign.repair_controls()
    assert len(calls) == 2
    assert sum(r["origin"] == "control" for r in read(campaign.version_root / "catalog.json")) == 4
    assert read(campaign.version_root / "initial_expansion.json")["model_attempts"] == initial
