from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec
from quanta_agents.factor_research.contracts import FactorFamily, JointConstraint, ParameterRange
from quanta_agents.factor_research.generation import (build_builtin_proposals, expand_proposals,
    save_proposals, load_proposals, evaluate_falsifiers, repair_candidate, mechanism_direction_status)
from quanta_agents.factor_research.lineage import LineageStore
from quanta_agents.factor_research.search import (FamilyHistory, select_parents,
    parameter_neighbors, allocate_family_budget)


def market_panel(days=150, stocks=8):
    rng = np.random.default_rng(312)
    dates = pd.bdate_range("2017-01-02", periods=days)
    cols = [f"s{i}" for i in range(stocks)]
    close = pd.DataFrame(40 * np.exp(np.cumsum(rng.normal(0, .018, (days, stocks)), axis=0)), index=dates, columns=cols)
    opening = close * np.exp(rng.normal(0, .006, close.shape))
    high = np.maximum(opening, close) * (1 + rng.uniform(.001, .02, close.shape))
    low = np.minimum(opening, close) * (1 - rng.uniform(.001, .02, close.shape))
    volume = pd.DataFrame(rng.lognormal(10, .6, close.shape), index=dates, columns=cols)
    eligible = close.notna()
    eligible.iloc[::3, -1] = False
    return SimpleNamespace(fields={"open": opening, "close": close, "high": high,
                           "low": low, "volume": volume, "amount": volume * close},
                           eligible=eligible, provenance={"scope": "synthetic_generation_risk_tests"})


def test_frozen_arm_denominator_keeps_duplicate_and_matched_control_costs():
    result = expand_proposals(build_builtin_proposals())
    assert result.summary["primary_attempts_by_arm"] == {"existing_library": 12, "rule_perturbation": 12, "llm_structure": 12}
    assert result.summary["attempts"] == 60
    assert result.summary["status_counts"] == {"admitted": 47, "duplicate": 13}
    ids = {c.spec.factor_id for c in result.candidates}
    for candidate in result.candidates:
        assert set(candidate.control_ids.values()) <= ids
        assert set(candidate.main_effect_ids) <= ids
    assert any(len(arms) > 1 for arms in result.summary["formula_memberships"].values())


def test_existing_arm_exactly_preserves_observed_library_definitions():
    path = Path(__file__).resolve().parents[1] / "output/research/meta_v9_20260909/library_inventory.json"
    if not path.exists():
        pytest.skip("historical source artifact not distributed with isolated checkout")
    original = {r["id"]: r["expression"] for r in json.loads(path.read_text(encoding="utf-8"))["executable_definitions"]}
    for family in build_builtin_proposals():
        if family.arm == "existing_library":
            parent = family.provenance["source_id"]
            assert FactorSpec("old", original[parent]).factor_id == FactorSpec("new", family.expression_template).factor_id


@pytest.mark.parametrize("change", [
    {"expression_template": "label_return"},
    {"expression_template": "lag(close, -1)"},
    {"expression_template": "close.iloc[-1]"},
    {"expression_template": "other_observable"},
    {"primary_horizon": 20},
    {"expected_direction": True},
    {"falsifiers": []},
    {"unexpected_free_python": "pass"},
])
def test_proposal_import_fails_closed_on_temporal_field_schema_and_label_changes(change):
    row = build_builtin_proposals()[0].to_dict()
    row.update(change)
    with pytest.raises(ValueError):
        FactorFamily.from_dict(row)


def test_joint_parameter_constraints_and_interaction_main_effects_are_binding():
    family = build_builtin_proposals()[-1]
    constrained = replace(family, parameters={"short": ParameterRange((3, 30), "short"),
                                              "long": ParameterRange((20, 40), "long")})
    assert {tuple(sorted(p.items())) for p in constrained.parameter_points()} == {
        (("long", 20), ("short", 3)), (("long", 40), ("short", 3)), (("long", 40), ("short", 30))}
    with pytest.raises(ValueError, match="no parameter point"):
        replace(family, constraints=(JointConstraint("short", "gt", "long"),))
    with pytest.raises(ValueError, match="both main effects"):
        replace(family, controls=(family.controls[0], replace(family.controls[1], main_effect=False)))
    with pytest.raises(ValueError, match="literal integers"):
        ParameterRange((True, 5), "window")


def test_budget_rejection_does_not_admit_candidate_without_its_controls():
    family = build_builtin_proposals()[-1]
    result = expand_proposals((family,), max_candidates=2)
    assert not result.candidates
    assert {a["status"] for a in result.attempts} == {"budget_rejected"}
    assert result.summary["primary_attempts_by_arm"] == {"llm_structure": 4}
    limited = expand_proposals((family,), max_attempts=4)
    assert limited.summary["proposed_attempts"] == 12
    assert limited.summary["admitted_attempts_including_duplicates"] == 3


def test_json_import_reproduces_all_identities_and_refuses_tampering(tmp_path):
    path = tmp_path / "proposal.json"
    families = build_builtin_proposals()
    save_proposals(path, families)
    assert [f.proposal_id for f in load_proposals(path)] == [f.proposal_id for f in families]
    row = json.loads(path.read_text(encoding="utf-8"))
    row["families"][0]["expression_template"] = "close"
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_proposals(path)
    with pytest.raises(ValueError, match="overwrite"):
        save_proposals(path, families)


def test_new_structures_are_causal_scale_invariant_and_non_degenerate():
    families = [f for f in build_builtin_proposals() if f.arm == "llm_structure"]
    specs = [FactorSpec(f.family_id, f.expression_template.format(**point)) for f in families for point in f.parameter_points()]
    original = market_panel()
    old = FactorEngine(original)
    changed = market_panel()
    for field in changed.fields:
        changed.fields[field].iloc[110:] *= 1000
    changed.eligible.iloc[110:] = False
    future = FactorEngine(changed)
    # Share-price denomination differs independently across stocks; relative
    # return and CLV hypotheses must remain unchanged, including internal ranks.
    scaled = market_panel()
    for field in ("open", "close", "high", "low"):
        scaled.fields[field] *= np.arange(1, 9)
    scaled.fields["amount"] *= 1000  # currency units, not extra activity
    units = FactorEngine(scaled)
    for spec in specs:
        values = old.compute(spec)
        assert values.iloc[60:].nunique(axis=1).gt(1).all()
        assert_frame_equal(values.iloc[:110], future.compute(spec).iloc[:110])
        assert_frame_equal(values, units.compute(spec), check_exact=False, atol=1e-10, rtol=1e-10)


def test_every_unique_formula_and_matched_control_executes_on_synthetic_panel():
    result = expand_proposals(build_builtin_proposals())
    engine = FactorEngine(market_panel())
    for candidate in result.candidates:
        values = engine.compute(candidate.spec)
        assert values.shape == (150, 8)
        assert values.iloc[-20:].notna().any().any(), candidate.spec.name
        assert values.iloc[-20:].nunique(axis=1).gt(1).any(), candidate.spec.name


def test_compression_interaction_is_zero_when_pressure_is_zero():
    p = market_panel()
    # A symmetric daily range has exactly no close-location pressure while
    # volatility state remains variable. This falsifies accidental main-effect
    # substitution in the implementation without using future return labels.
    p.fields["high"] = p.fields["close"] + 2
    p.fields["low"] = p.fields["close"] - 2
    family = build_builtin_proposals()[-1]
    spec = FactorSpec("test", family.expression_template.format(short=3, long=20))
    values = FactorEngine(p).compute(spec).iloc[30:]
    assert values.notna().any().any()
    assert np.nanmax(np.abs(values.to_numpy())) < 1e-12


def test_falsifier_is_unknown_without_paired_evidence_and_rejects_identity_substitution():
    candidate = next(c for c in expand_proposals(build_builtin_proposals()).candidates if c.arm == "llm_structure")
    assert all(r["status"] == "not_evaluable" for r in evaluate_falsifiers(candidate, []))
    falsifier = candidate.falsifiers[0]
    row = {"trial_id": candidate.trial_id, "factor_id": candidate.spec.factor_id,
           "falsifier_id": falsifier.falsifier_id, "metric": falsifier.metric, "split": falsifier.split,
           "control_ids": [candidate.control_ids[k] for k in falsifier.control_refs],
           "sample_mask_id": "same-stock-days", "paired_days": 240, "value": -0.001}
    assert evaluate_falsifiers(candidate, [row])[0]["status"] == "falsified"
    assert evaluate_falsifiers(candidate, [{**row, "value": None}])[0]["status"] == "not_evaluable"
    assert evaluate_falsifiers(candidate, [{**row, "paired_days": 1}])[0]["status"] == "not_evaluable"
    with pytest.raises(ValueError, match="mismatch"):
        evaluate_falsifiers(candidate, [{**row, "split": "confirmation"}])
    with pytest.raises(ValueError, match="mismatch"):
        evaluate_falsifiers(candidate, [{**row, "control_ids": ["wrong-formula"]}])
    reversed_sign = evaluate_falsifiers(candidate, [{**row, "value": .001, "fitted_direction": -1}])[0]
    assert reversed_sign["status"] == "supported"
    assert reversed_sign["mechanism_direction_status"] == "contradicted"
    assert reversed_sign["mechanism_support"] == "not_supported"


def test_repair_must_reexecute_and_change_identity_and_record_failures(tmp_path):
    original = next(c for c in expand_proposals(build_builtin_proposals()).candidates if c.family_id == "existing.F2")
    store = LineageStore(tmp_path / "lineage.sqlite")
    store.record_trial(original)
    store.record_outcome(original.trial_id, "implementation_failed", evidence={"error": "synthetic implementation mismatch"})
    store.record_repair_attempt(original.trial_id, "pct_change(close, 6)", "restore declared trailing calculation")
    engine = FactorEngine(market_panel())
    executed = []
    def executor(spec):
        executed.append(spec.factor_id)
        return engine.compute(spec)
    repaired = repair_candidate(original, "pct_change(close, 6)", reason="synthetic corrected implementation",
                                repair_number=1, executor=executor)
    assert executed == [repaired.spec.factor_id]
    assert repaired.spec.factor_id != original.spec.factor_id
    assert repaired.trial_id != original.trial_id
    store.record_trial(repaired, parent_trial_ids=(original.trial_id,))
    assert store.ancestors(repaired.trial_id)[0]["trial_id"] == original.trial_id
    store.record_repair_attempt(original.trial_id, "pct_change(close, 7)", "second attempt")
    with pytest.raises(ValueError, match="exhausted"):
        store.record_repair_attempt(original.trial_id, "pct_change(close, 8)", "third attempt")
    store.record_outcome(repaired.trial_id, "implementation_failed", evidence={"error": "second synthetic defect"})
    with pytest.raises(ValueError, match="exhausted"):
        store.record_repair_attempt(repaired.trial_id, "pct_change(close, 8)", "cannot reset cap through new identity")
    with pytest.raises(ValueError, match="degenerate"):
        repair_candidate(original, "0 * close", reason="invalid fix", repair_number=2, executor=executor)
    with pytest.raises(ValueError, match="undeclared"):
        repair_candidate(original, "close + amount", reason="scope expansion", repair_number=1, executor=executor)
    assert store.verify()
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE events SET payload='{}' WHERE sequence=1")
    with pytest.raises(ValueError, match="corrupt"):
        store.verify()


@pytest.mark.parametrize("phase", ["frozen", "confirmation", "complete", "cancelled"])
def test_all_search_and_repair_entry_points_close_after_freeze(phase):
    family = build_builtin_proposals()[-1]
    candidate = expand_proposals((family,)).candidates[0]
    with pytest.raises(ValueError, match="closed"):
        expand_proposals((family,), phase=phase)
    with pytest.raises(ValueError, match="closed"):
        parameter_neighbors(family, family.parameter_points()[0], phase=phase)
    with pytest.raises(ValueError, match="closed"):
        select_parents([], phase=phase)
    with pytest.raises(ValueError, match="closed"):
        repair_candidate(candidate, "close", reason="change", repair_number=1, executor=lambda s: None, phase=phase)


def test_scheduler_rejects_confirmation_feedback_and_reports_only_measured_estimates():
    with pytest.raises(ValueError, match="confirmation"):
        FamilyHistory("a", split="confirmation", evidence_end_year=2024)
    with pytest.raises(ValueError, match="confirmation"):
        FamilyHistory("a", evidence_end_year=2021)
    selected = select_parents([FamilyHistory("quality", 3, 3, best_development_ic=.02),
                               FamilyHistory("complement", 2, 2, best_development_ic=.01, best_paired_increment=.001),
                               FamilyHistory("unexplored")])
    assert [r["family_id"] for r in selected] == ["quality", "complement", "unexplored"]
    estimate = allocate_family_budget(build_builtin_proposals())
    assert estimate["primary_attempts"] == 36
    assert estimate["matched_control_attempts"] == 24
    assert estimate["suggested_workers"] == 1
    assert estimate["estimated_wall_seconds"] is None
