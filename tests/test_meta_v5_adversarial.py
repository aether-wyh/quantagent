"""Independent V5 custody counterexamples, using generated local inputs only.

No market data, gateway/model calls, paid runs, or formal evaluator are used.
Hashes prove local integrity against the controller's frozen identity, never
the external truth of an operator-provided source or a natural-language claim.
"""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v5.analytics import evaluate_bundle, digest
from quanta_agents.meta_v5.registry import Catalog, prepare_catalog, write_catalog, file_hash
from quanta_agents.meta_v5.reflection import validate_reflection, next_actions


def explicit_policy():
    return {"version": "v5_stability_policy_v1", "expected_years": [2020, 2021],
            "annualization": 252, "risk_free_rate": .02, "min_sessions_per_year": 2,
            "min_paired_cell_fraction": 1., "min_unit_coverage_fraction": 1.,
            "min_positive_excess_year_fraction": .5, "min_positive_excess_unit_fraction": .5,
            "max_worst_year_excess_loss": .05, "max_drawdown": .5,
            "max_positive_pnl_concentration": 1., "max_stale_fraction": 0.,
            "require_known_fees": True, "require_exposure": True,
            "require_execution_certified": False}


def saved(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def arm(nav):
    return {"nav": list(nav), "exposure": [.6] * len(nav), "fees": [1.] * len(nav),
            "stale": [0] * len(nav)}


def generated_bundle(tmp_path):
    source = tmp_path / "generated_source.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        saved(source, {"source_class": "generated_engineering", "market_data": False,
                       "statement": "Synthetic test values only; no financial conclusion."})
    return {"version": "v5_stability_bundle_v1", "candidate_id": "base", "program_hash": "1" * 64,
            "scope_id": "fixed_two_units", "split": "development", "expected_units": ["a", "b"],
            "provenance": {"source_class": "generated_engineering", "accounting_mode": "generated_no_cashflows",
                "account_currency": "CNY", "fee_unit": "CNY", "external_cash_flows": "none_after_initial",
                "execution_certified": False, "exposed": True, "source_hashes": {str(source): file_hash(source)},
                "cost_policy": {"kind": "generated_one_CNY_each_session", "nav_already_net": True}},
            "pairs": [{"unit_id": uid, "unit_kind": "stock", "calendar": ["2020-01-02", "2020-12-31", "2021-01-04", "2021-12-31"],
                       "initial_nav": 100., "candidate": arm([110., 120., 125., 140.]),
                       "benchmark": arm([101., 110., 111., 120.])} for uid in ("a", "b")]}


def frozen_catalog(tmp_path):
    bundle, policy = generated_bundle(tmp_path), explicit_policy()
    prepared = prepare_catalog([bundle], policy)
    stage = tmp_path / "stage"
    stage.mkdir()
    identity = write_catalog(stage, prepared)
    catalog = Catalog(stage, deepcopy(identity))
    assert catalog.verify()
    return bundle, policy, stage, catalog, identity


@pytest.mark.parametrize("split", ["confirmation", "final", "holdout", "test", "DEVELOPMENT"])
def test_non_development_rejected_before_source_file_is_opened(tmp_path, monkeypatch, split):
    bundle = generated_bundle(tmp_path)
    bundle["candidate_id"], bundle["scope_id"], bundle["split"] = "renamed", "renamed_scope", split
    def forbidden_read(_):
        pytest.fail("Protected input reached the file reader before the split gate")
    monkeypatch.setattr("quanta_agents.meta_v5.registry.file_hash", forbidden_read)
    with pytest.raises(ValueError, match="confirmation/final|development"):
        prepare_catalog([bundle], explicit_policy())


@pytest.mark.parametrize("change", ["unexposed", "certified", "unadmitted_class", "empty_sources"])
def test_renaming_cannot_launder_source_class_or_execution_authority(tmp_path, change):
    bundle = generated_bundle(tmp_path)
    bundle["candidate_id"], bundle["scope_id"] = "new_discovery", "new_unseen_scope"
    if change == "unexposed": bundle["provenance"]["exposed"] = False
    elif change == "certified": bundle["provenance"]["execution_certified"] = True
    elif change == "unadmitted_class": bundle["provenance"]["source_class"] = "formal_holdout"
    else: bundle["provenance"]["source_hashes"] = {}
    with pytest.raises(ValueError):
        prepare_catalog([bundle], explicit_policy())


def test_candidate_rename_preserves_development_exposure_of_same_sources(tmp_path):
    bundle, policy, stage, catalog, identity = frozen_catalog(tmp_path)
    clone = deepcopy(bundle)
    clone["candidate_id"], clone["scope_id"] = "renamed", "new_label_for_same_data"
    next_stage = tmp_path / "renamed_stage"
    next_stage.mkdir()
    write_catalog(next_stage, prepare_catalog([clone], policy))
    original = json.loads((stage / "v5_catalog/exposure.json").read_text(encoding="utf-8"))
    renamed = json.loads((next_stage / "v5_catalog/exposure.json").read_text(encoding="utf-8"))
    assert original["sources"] == renamed["sources"]
    for record in (original, renamed):
        assert record["split"] == "development" and record["exposed"] is True
        assert record["rename_does_not_restore_holdout"] is True
        assert record["formal_release_authority"] is False
    assert catalog.profiles()["base"]["formal_target_success"] is False


def test_changed_source_content_is_rejected_even_if_bundle_and_profile_unchanged(tmp_path):
    bundle, _, _, catalog, _ = frozen_catalog(tmp_path)
    source = next(iter(bundle["provenance"]["source_hashes"]))
    from pathlib import Path
    saved(Path(source), {"source_class": "generated_engineering", "tampered": True})
    with pytest.raises(ValueError, match="source changed"):
        catalog.verify()


def test_self_rehashed_fake_profile_cannot_override_controller_identity(tmp_path):
    _, _, stage, catalog, _ = frozen_catalog(tmp_path)
    path = stage / "v5_catalog/base.profile.json"
    profile = json.loads(path.read_text(encoding="utf-8"))
    profile["cells"][0]["excess_return"] = 999.
    profile["development_eligible"] = True
    profile["profile_hash"] = digest({k: v for k, v in profile.items() if k != "profile_hash"})
    saved(path, profile)
    with pytest.raises(ValueError, match="profile drift"):
        catalog.profiles()


def test_coherently_rehashed_bundle_profile_and_local_manifest_still_fail_external_pin(tmp_path):
    bundle, policy, stage, catalog, identity = frozen_catalog(tmp_path)
    forged = deepcopy(bundle)
    forged["pairs"][0]["candidate"]["nav"][-1] = 999.
    profile = evaluate_bundle(forged, policy)
    changed_identity = deepcopy(identity)
    changed_identity["entries"][0].update(bundle_hash=digest(forged), profile_hash=profile["profile_hash"])
    saved(stage / "v5_catalog/base.bundle.json", forged)
    saved(stage / "v5_catalog/base.profile.json", profile)
    saved(stage / "v5_catalog/manifest.json", changed_identity)
    with pytest.raises(ValueError, match="manifest drift"):
        catalog.verify()


def test_exposure_record_cannot_be_silently_relabelled_as_unseen(tmp_path):
    _, _, stage, catalog, _ = frozen_catalog(tmp_path)
    path = stage / "v5_catalog/exposure.json"
    exposure = json.loads(path.read_text(encoding="utf-8"))
    exposure.update(exposed=False, split="confirmation", sources=[])
    saved(path, exposure)
    with pytest.raises(ValueError, match="exposure|catalog|manifest"):
        catalog.verify()


@pytest.mark.parametrize("attack", ["unit", "calendar", "benchmark", "capital", "cost"])
def test_same_scope_catalog_cannot_mix_cherry_picked_comparison_identities(tmp_path, attack):
    base = generated_bundle(tmp_path)
    revision = deepcopy(base)
    revision.update(candidate_id="revision", program_hash="2" * 64)
    if attack == "unit":
        revision["expected_units"].pop()
        revision["pairs"].pop()
    elif attack == "calendar":
        revision["pairs"][0]["calendar"][0] = "2020-01-03"
    elif attack == "benchmark": revision["pairs"][0]["benchmark"]["nav"][-1] = 90.
    elif attack == "capital": revision["pairs"][0]["initial_nav"] = 50.
    else: revision["provenance"]["cost_policy"]["kind"] = "different_cost"
    with pytest.raises(ValueError, match="scope|comparison|identity"):
        prepare_catalog([base, revision], explicit_policy())


def test_same_scope_valid_revision_may_change_program_and_candidate_results(tmp_path):
    base = generated_bundle(tmp_path)
    revision = deepcopy(base)
    revision.update(candidate_id="revision", program_hash="2" * 64)
    revision["pairs"][0]["candidate"]["nav"][-1] = 145.
    prepared = prepare_catalog([base, revision], explicit_policy())
    assert len(prepared["entries"]) == 2
    assert all(e["profile"]["formal_target_success"] is False for e in prepared["entries"])


def test_unknown_year_end_contaminates_next_year_start_without_reset_or_compression(tmp_path):
    bundle = generated_bundle(tmp_path)
    bundle["pairs"][0]["candidate"]["nav"][1] = None
    profile = evaluate_bundle(bundle, explicit_policy())
    cells = {c["cell_id"]: c for c in profile["cells"]}
    assert len(cells) == profile["summary"]["expected_cells"] == 4
    assert cells["a:2021"]["candidate_metrics"]["starting_nav"] is None
    assert cells["a:2021"]["candidate_metrics"]["return"] is None
    assert cells["a:2021"]["candidate_metrics"]["max_drawdown"] is None
    assert cells["a:2021"]["complete"] is False
    assert cells["b:2021"]["complete"] is True
    assert profile["development_eligible"] is False


def test_full_negative_year_is_allowed_when_same_scope_relative_evidence_is_better(tmp_path):
    bundle = generated_bundle(tmp_path)
    for pair in bundle["pairs"]:
        pair["candidate"] = arm([105., 110., 105., 104.])
        pair["benchmark"] = arm([100., 105., 90., 80.])
    profile = evaluate_bundle(bundle, explicit_policy())
    assert profile["development_eligible"] is True
    assert profile["cells"][1]["candidate_metrics"]["return"] < 0
    assert profile["cells"][1]["excess_return"] > 0
    assert profile["statistical_significance_established"] is False
    assert profile["causal_mechanism_identified"] is False
    assert "independence" in profile["summary"]["dependence_statement"].lower()


def test_fully_formed_stopped_reflection_remains_a_declaration_not_mechanism_evidence(tmp_path):
    bundle = generated_bundle(tmp_path)
    bundle["pairs"][0]["candidate"] = arm([90., 80., 70., 60.])
    profile = evaluate_bundle(bundle, explicit_policy())
    assert profile["issues"]
    declaration = {"version": "v5_reflection_declaration_v1",
        **{k: profile[k] for k in ("candidate_id", "program_hash", "scope_id", "profile_hash", "split")},
        "retained_cell_ids": [c["cell_id"] for c in profile["cells"]], "evidence": [], "experiments": [],
        "issue_responses": [{"issue_id": i["id"], "cell_ids": i["cell_ids"], "status": "stopped",
            "statement": "This synthetic difference remains unexplained.", "explanations": [],
            "unknowns": ["No mechanism experiment has run."],
            "counterevidence": {"state": "not_yet_assessed", "evidence_ids": [], "note": "No unsupported causal assertion."},
            "next_step": {"kind": "stop", "reason": "No independent distinguishing evidence is available."}}
            for i in profile["issues"]],
        "conclusion": {"text": "Complete declarations alone establish no mechanism.", "mechanism_status": "unresolved",
            "causal_mechanism_identified": False, "formal_target_success": False, "experiments_executed": False}}
    record = validate_reflection(declaration, profile)
    assert record["quality_validated"] is True
    assert record["semantic_truth_verified"] is False
    assert record["causal_mechanism_identified"] is False and record["experiments_executed"] is False
    assert record["unresolved_issue_ids"] == [i["id"] for i in profile["issues"]]
    assert all(a["execution_authorized"] is False and a["formal_target_success"] is False
               for a in next_actions(profile, record))


@pytest.mark.parametrize("field,value", [("account_currency", "USD"), ("fee_unit", "CNY_10000"),
                                         ("external_cash_flows", "unknown")])
def test_unit_and_funding_identity_cannot_be_omitted_or_changed(tmp_path, field, value):
    bundle = generated_bundle(tmp_path)
    bundle["provenance"][field] = value
    with pytest.raises(ValueError):
        prepare_catalog([bundle], explicit_policy())
