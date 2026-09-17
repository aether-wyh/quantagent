from copy import deepcopy
import hashlib
import json

import pytest

from quanta_agents.meta_v5.reflection import (
    next_actions, public_contract, validate_evidence_ref, validate_reflection,
)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def profile():
    result = {
        "version": "v5_stability_profile_v1", "candidate_id": "candidate_a", "program_hash": "a" * 64,
        "scope_id": "frozen_scope", "split": "development", "bundle_hash": "b" * 64, "policy_hash": "c" * 64,
        "comparison_identity": {"expected_units": ["asset_a"], "calendar": ["2020-01-02", "2021-01-04"], "cost": "frozen_cost"},
        "development_eligible": False, "formal_target_success": False,
        "cells": [
            {"cell_id": "asset_a:2020", "unit_id": "asset_a", "year": 2020, "sessions": 2, "complete": True,
             "candidate_metrics": {"return": -0.1, "sharpe": -0.3}, "benchmark_metrics": {"return": 0.02}, "excess_return": -0.12, "quality_flags": []},
            {"cell_id": "asset_a:2021", "unit_id": "asset_a", "year": 2021, "sessions": 2, "complete": True,
             "candidate_metrics": {"return": 0.2, "sharpe": 1.1}, "benchmark_metrics": {"return": 0.05}, "excess_return": 0.15, "quality_flags": []},
        ],
        "issues": [{"id": "heterogeneity_a", "severity": "warning", "code": "heterogeneity", "cell_ids": ["asset_a:2020", "asset_a:2021"], "message": "The paired excess differs across the retained cells."}],
    }
    result["profile_hash"] = digest(result)
    return result


def declaration(p=None):
    p = p or profile()
    return {
        "version": "v5_reflection_declaration_v1",
        **{k: p[k] for k in ("candidate_id", "program_hash", "scope_id", "profile_hash", "split")},
        "retained_cell_ids": [c["cell_id"] for c in p["cells"]],
        "evidence": [{"evidence_id": "loss", "source": "cell", "source_id": "asset_a:2020", "field": "excess_return", "reported_value": -0.12}],
        "issue_responses": [{
            "issue_id": "heterogeneity_a", "cell_ids": ["asset_a:2020", "asset_a:2021"],
            "status": "provisional_explanation", "statement": "Exposure or an unidentified price-volume interaction may explain the difference.",
            "explanations": [{"explanation_id": "exposure", "statement": "Different exposure drives the observed difference.", "evidence_ids": ["loss"]},
                             {"explanation_id": "unknown_interaction", "statement": "An unmeasured interaction may survive exposure matching.", "evidence_ids": []}],
            "unknowns": ["The interaction's mechanism is not known."],
            "counterevidence": {"state": "present", "evidence_ids": ["loss"], "note": "The negative cell remains a counterexample."},
            "next_step": {"kind": "experiment", "experiment_id": "matched_exposure"},
        }],
        "experiments": [{
            "experiment_id": "matched_exposure", "kind": "discriminating_test", "scope_id": p["scope_id"], "split": "development",
            "retained_cell_ids": [c["cell_id"] for c in p["cells"]], "issue_ids": ["heterogeneity_a"],
            "explanation_ids": ["exposure", "unknown_interaction"], "evidence_ids": ["loss"],
            "controls": [{"control_id": "original_candidate", "purpose": "Keep the original full path."},
                         {"control_id": "same_scope_benchmark", "purpose": "Measure common market returns."}],
            "procedure": "Match lagged exposure strata while retaining the complete registered cells and cost policy.",
            "completion_criteria": "Record every paired cell, missing strata, and signed residual differences.",
            "prediction": {"statement": "The between-cell difference attenuates after exposure matching.", "observable": "Paired residual differences after fixed exposure stratification.",
                           "decision_rule": "A persistent signed difference refutes exposure as a sufficient explanation.", "supports_explanation_id": "exposure", "refutes_explanation_id": "unknown_interaction"},
            "tradeable_condition": {"expression": "close > lag(close, 1)", "timing": "previous_completed_session", "status": "unvalidated_hypothesis_only"},
            "on_failure": "retain_unresolved",
        }],
        "conclusion": {"text": "This remains a provisional research declaration.", "mechanism_status": "unresolved", "causal_mechanism_identified": False,
                       "formal_target_success": False, "experiments_executed": False},
    }


def test_valid_declaration_retains_counterevidence_without_certifying_causality():
    p, d = profile(), declaration()
    original = deepcopy(d)
    record = validate_reflection(d, p)
    assert d == original
    assert record["quality_validated"] is True
    assert record["semantic_truth_verified"] is False
    assert record["causal_mechanism_identified"] is False
    assert record["formal_target_success"] is False
    assert record["experiments_executed"] is False
    assert record["unresolved_issue_ids"] == ["heterogeneity_a"]
    assert record["reflection_hash"] == digest({k:v for k,v in record.items() if k != "reflection_hash"})
    action = next_actions(p, record)[0]
    assert action["action"] == "run_discriminating_experiment"
    assert action["counterevidence_state"][0]["evidence_ids"] == ["loss"]
    assert action["execution_authorized"] is False
    assert action["requires_new_saved_evidence"] is True


@pytest.mark.parametrize("field,value", [("candidate_id", "other"), ("program_hash", "d" * 64),
                                         ("profile_hash", "e" * 64), ("scope_id", "new_scope"), ("split", "final")])
def test_cross_candidate_or_stale_binding_is_rejected(field, value):
    d = declaration(); d[field] = value
    with pytest.raises(ValueError):
        validate_reflection(d, profile())


def test_profile_tampering_requires_new_profile_and_old_reflection_is_rejected():
    p = profile(); d = declaration(p)
    p["cells"][0]["excess_return"] = 1.0
    with pytest.raises(ValueError, match="hash"):
        validate_reflection(d, p)
    p["profile_hash"] = digest({k:v for k,v in p.items() if k != "profile_hash"})
    with pytest.raises(ValueError, match="profile_hash"):
        validate_reflection(d, p)


@pytest.mark.parametrize("mutation", [
    lambda d: d["evidence"][0].update(source_id="asset_missing:2020"),
    lambda d: d["evidence"][0].update(reported_value=0.4),
    lambda d: d["evidence"][0].update(field="unseen_future_result"),
    lambda d: d["issue_responses"].clear(),
    lambda d: d["issue_responses"][0].update(issue_id="invented"),
    lambda d: d["retained_cell_ids"].pop(0),
    lambda d: d["issue_responses"][0]["cell_ids"].pop(0),
    lambda d: d["experiments"][0]["retained_cell_ids"].pop(0),
    lambda d: d["experiments"][0].update(scope_id="winner_only"),
    lambda d: d["experiments"][0].update(split="confirmation"),
    lambda d: d["experiments"][0]["controls"].pop(),
    lambda d: d["experiments"][0]["controls"][0].update(control_id="invented_control"),
    lambda d: d["experiments"][0].update(procedure="   "),
    lambda d: d["experiments"][0].update(completion_criteria=""),
    lambda d: d["experiments"][0].update(prediction=None),
    lambda d: d["experiments"][0]["prediction"].update(refutes_explanation_id="exposure"),
    lambda d: d["experiments"][0]["prediction"].update(supports_explanation_id="invented_explanation"),
    lambda d: d["issue_responses"][0]["counterevidence"].update(evidence_ids=[]),
    lambda d: d["conclusion"].update(causal_mechanism_identified=True),
    lambda d: d["conclusion"].update(formal_target_success=True),
    lambda d: d["conclusion"].update(experiments_executed=True),
    lambda d: d.update(hidden_future_path="somewhere"),
])
def test_false_facts_scope_culling_empty_experiments_and_fabricated_outcomes_rejected(mutation):
    d = declaration(); mutation(d)
    with pytest.raises(ValueError):
        validate_reflection(d, profile())


@pytest.mark.parametrize("expression", ["year == 2020", "unit_id == 1", "calendar_year > 2021", "lag(close, -1) > close", "__import__('os')"])
def test_calendar_identity_or_future_information_cannot_be_trade_conditions(expression):
    d = declaration(); d["experiments"][0]["tradeable_condition"]["expression"] = expression
    with pytest.raises(ValueError):
        validate_reflection(d, profile())


def test_unknown_mechanism_may_stop_without_inventing_explanations():
    p, d = profile(), declaration()
    d["issue_responses"][0].update(status="stopped", explanations=[], statement="No discriminating test can yet be specified.", next_step={"kind": "stop", "reason": "Required measurement is unavailable."})
    d["experiments"] = []
    record = validate_reflection(d, p)
    assert next_actions(p, record)[0]["action"] == "abstain"
    assert record["unresolved_issue_ids"] == ["heterogeneity_a"]


def test_unknown_data_gap_schedules_source_completion_without_mechanism_claim():
    p = profile()
    p["cells"][0]["complete"] = False
    p["issues"][0]["code"] = "missing_benchmark"
    p["profile_hash"] = digest({k:v for k,v in p.items() if k != "profile_hash"})
    d = declaration(p)
    d["issue_responses"][0].update(status="data_gap", explanations=[])
    e = d["experiments"][0]
    e.update(kind="source_completion", explanation_ids=[], prediction=None,
             controls=[{"control_id": "source_identity", "purpose": "Retain the original supplier identity."}, {"control_id": "full_scope_coverage", "purpose": "Keep every original cell."}])
    e["tradeable_condition"]["expression"] = None
    record = validate_reflection(d, p)
    actions = next_actions(p, record)
    assert actions[0]["action"] == "complete_evidence"
    assert len(actions) == 1, "A bound source experiment should not also create a duplicate generic request"
    assert all(a["priority"] == 10 for a in actions)
    assert record["causal_mechanism_identified"] is False


def test_coverage_precedes_and_blocks_experiment_readiness_without_dropping_it():
    p = profile(); p["cells"][0]["complete"] = False
    p["profile_hash"] = digest({k:v for k,v in p.items() if k != "profile_hash"})
    record = validate_reflection(declaration(p), p)
    actions = next_actions(p, record)
    assert [a["action"] for a in actions] == ["complete_evidence", "run_discriminating_experiment"]
    assert actions[1]["ready"] is False
    assert actions == next_actions(p, record)
    assert actions[1]["unresolved_issue_ids"] == ["heterogeneity_a"]


@pytest.mark.parametrize("code", ["fees_unknown", "exposure_unknown", "stale_quality_unknown", "stale_quality_exceeded", "cost_policy_unknown", "execution_not_certified", "coverage_below_policy"])
def test_known_quality_gap_codes_prioritize_evidence_even_when_nav_is_complete(code):
    p = profile(); p["issues"][0]["code"] = code
    p["profile_hash"] = digest({k:v for k,v in p.items() if k != "profile_hash"})
    action = next_actions(p)[0]
    assert action["action"] == "complete_evidence"
    assert action["issue_ids"] == ["heterogeneity_a"]


def test_stopped_missing_evidence_issue_does_not_schedule_repeated_acquisition():
    p = profile(); p["issues"][0]["code"] = "fees_unknown"
    p["profile_hash"] = digest({k:v for k,v in p.items() if k != "profile_hash"})
    d = declaration(p)
    d["issue_responses"][0].update(status="stopped", explanations=[], next_step={"kind": "stop", "reason": "The fixed source scope cannot supply the required evidence."})
    d["experiments"] = []
    actions = next_actions(p, validate_reflection(d, p))
    assert [a["action"] for a in actions] == ["abstain"]
    assert actions[0]["unresolved_issue_ids"] == ["heterogeneity_a"]


def test_clean_profile_only_prepares_confirmation_and_never_releases_holdout():
    p = profile(); p["issues"] = []; p["development_eligible"] = True
    p["profile_hash"] = digest({k:v for k,v in p.items() if k != "profile_hash"})
    action = next_actions(p)[0]
    assert action["action"] == "prepare_confirmation"
    assert action["holdout_release_authorized"] is False
    assert action["execution_authorized"] is False


def test_next_actions_rejects_forged_record_not_just_bad_declaration():
    p = profile(); record = validate_reflection(declaration(p), p)
    record["causal_mechanism_identified"] = True
    record["reflection_hash"] = digest({k:v for k,v in record.items() if k != "reflection_hash"})
    with pytest.raises(ValueError, match="record"):
        next_actions(p, record)


def test_contract_is_defensive_copy_and_fact_reference_missing_is_not_zero():
    contract = public_contract(); contract["declaration_schema"]["required"].clear()
    assert public_contract()["declaration_schema"]["required"]
    r = declaration()["evidence"][0]; r.update(field="candidate_metrics.fees", reported_value=0)
    with pytest.raises(ValueError, match="absent"):
        validate_evidence_ref(r, profile())


def test_factual_reference_checks_but_does_not_claim_to_verify_free_text_truth():
    d = declaration()
    d["conclusion"]["text"] = "A prose assertion supplied by the researcher, not machine-certified."
    record = validate_reflection(d, profile())
    assert record["semantic_truth_verified"] is False
    assert "trusted" in public_contract()["trusted_input"].lower() or "Controller" in public_contract()["trusted_input"]
