"""Offline synthetic recovery; the paid gateway and all accounts are mocked."""
from copy import deepcopy

import pytest

from quanta_agents.meta_v6 import application_reference_recovery as recovery
from quanta_agents.meta_v6 import information_application as app
from test_meta_v6_information_application import environment, no_real_calls, response, synthetic_fit, edit


def extra_refs(value):
    value["factor_assessments"][0]["evidence_refs"] += ["/hf0280_source_limitations",
        "/return_ic_bootstrap_supplement/factors/9", "/return_ic_bootstrap_supplement/proposal_timing"]
    value["factor_assessments"][1]["evidence_refs"].append("/return_ic_bootstrap_supplement/factors/10")
    value["factor_assessments"][2]["evidence_refs"].append("/return_ic_bootstrap_supplement/factors/11")


def projection_case():
    fit = synthetic_fit()
    fit["hf0280_source_limitations"] = ["Synthetic publication-vintage limitation"]
    fit["return_ic_bootstrap_supplement"] = {"proposal_timing": {"post_hoc_supplement": True,
        "pre_results_preregistration_claimed": False}, "factors": [{"factor_key": r["factor_key"], "factor_id": r["factor_id"],
        "direction": r["direction"], "source_factor_status": r["status"]} for r in fit["factors"]]}
    value = response(fit)
    extra_refs(value)
    return fit, value


@pytest.fixture
def failed_reference_stage(environment):
    root, fit, proposed, exposures, calls, paid, before = environment
    factor_folder = root / "cycles" / app.FACTOR_CYCLE
    edit(factor_folder / "fit_factor_view.json", lambda x: x.update(hf0280_source_limitations=["SYNTHETIC vintage limitation"]))
    edit(factor_folder / "factor_index.json", lambda x: x.update(fit_factor_view_sha256=app.file_hash(factor_folder / "fit_factor_view.json")))
    def bootstrap(x):
        x["factor_index_sha256"] = app.file_hash(factor_folder / "factor_index.json")
        x["fit_factor_view_sha256"] = app.file_hash(factor_folder / "fit_factor_view.json")
        for row, factor in zip(x["factors"], fit["factors"]): row["factor_id"] = factor["factor_id"]
    edit(factor_folder / "return_ic_bootstrap.json", bootstrap)
    extra_refs(proposed)
    with pytest.raises(ValueError, match="assessment cites another factor"):
        app.propose_information_application(root)
    old_bytes = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    return root, proposed, paid, old_bytes


def test_exact_five_extra_references_checked_original_response_unchanged():
    fit, value = projection_case()
    before = deepcopy(value)
    projected, checks = recovery.project_reference_response(value, fit)
    assert len(checks) == 5 and value == before
    assert recovery._decisions(projected) == recovery._decisions(value)
    assert all(pointer.startswith("/factors/") for item in projected["factor_assessments"] for pointer in item["evidence_refs"])
    assert [c["target_factor_key"] for c in checks] == ["HF0280", "HF0280", None, "F7", "F8"]
    assert all(c["independently_verified"] for c in checks)
    compiled = app.validate_application_response(projected, fit, {"new_portfolio_proposals_max": 3})
    assert compiled["specs"][0]["factor_weights"] == {"HF0280": .5, "F8": -.5}


@pytest.mark.parametrize("bad_ref", ["/return_ic_bootstrap_supplement/factors/10", "/return_ic_bootstrap_supplement/factors/-1",
    "/return_ic_bootstrap_supplement/factors/09", "/return_ic_bootstrap_supplement/factors/9/direction",
    "/return_ic_bootstrap_supplement/factors/999", "/return_ic_bootstrap_supplement", "/unknown",
    "/return_ic_bootstrap_supplement/method", "/hf0280_source_limitations/0"])
def test_whitelist_does_not_accept_other_factor_or_unapproved_path(bad_ref):
    fit, value = projection_case()
    value["factor_assessments"][0]["evidence_refs"].append(bad_ref)
    with pytest.raises(ValueError): recovery.project_reference_response(value, fit)


@pytest.mark.parametrize("problem", ["wrong_id", "wrong_direction", "wrong_status", "hf_wrong_owner", "timing_rewritten", "missing_path"])
def test_same_factor_and_limitation_identity_required(problem):
    fit, value = projection_case()
    if problem == "wrong_id": fit["return_ic_bootstrap_supplement"]["factors"][9]["factor_id"] = "other"
    elif problem == "wrong_direction": fit["return_ic_bootstrap_supplement"]["factors"][9]["direction"] = -1
    elif problem == "wrong_status": fit["return_ic_bootstrap_supplement"]["factors"][9]["source_factor_status"] = "failed"
    elif problem == "hf_wrong_owner": value["factor_assessments"][1]["evidence_refs"].append("/hf0280_source_limitations")
    elif problem == "timing_rewritten": fit["return_ic_bootstrap_supplement"]["proposal_timing"]["post_hoc_supplement"] = False
    elif problem == "missing_path": fit.pop("hf0280_source_limitations")
    with pytest.raises(ValueError): recovery.project_reference_response(value, fit)


def test_reference_recovery_preserves_all_paid_text_and_old_bytes(failed_reference_stage, monkeypatch):
    root, proposed, paid, before = failed_reference_stage
    monkeypatch.setattr(app, "call_researcher", lambda *a, **k: pytest.fail("recovery called model"))
    monkeypatch.setattr(app, "_load_context", lambda *a, **k: pytest.fail("recovery loaded native financial context"))
    original_validator = open(app.__file__, "rb").read()
    result = recovery.recover_application_references(root)
    folder, protocol, verified, fit = recovery.verify_recovered_application_declaration(root)
    assert verified == result and len(paid) == 1
    declaration = app.read(folder / "application_declaration.json")
    assert declaration["factor_assessments"] == proposed["factor_assessments"]
    assert [r["proposal"] for r in declaration["proposal_records"]] == proposed["portfolios"]
    receipt = app.read(folder / recovery.RECEIPT)
    assert receipt["model_calls"] == receipt["account_executions"] == receipt["new_financial_observations"] == receipt["candidate_modifications"] == 0
    assert receipt["original_validator_sha256"] == recovery.ORIGINAL_VALIDATOR_SHA256
    assert app.file_hash(folder / "application_declaration.json") == result["application_declaration_sha256"]
    assert {key: (root / key).read_bytes() for key in before} == before
    assert open(app.__file__, "rb").read() == original_validator
    assert recovery.recover_application_references(root) == result


@pytest.mark.parametrize("problem", ["intent", "receipt", "complete_refs", "economic_field", "original_failure", "source_pin"])
def test_readonly_recovery_verifier_rejects_changed_evidence(failed_reference_stage, problem):
    root, *_ = failed_reference_stage
    recovery.recover_application_references(root)
    folder = root / "cycles" / app.CYCLE
    if problem == "intent": edit(folder / recovery.INTENT, lambda x: x.update(projection_sha256="wrong"))
    elif problem == "receipt": edit(folder / recovery.RECEIPT, lambda x: x.update(model_calls=1))
    elif problem == "complete_refs": edit(folder / "application_declaration.json", lambda x: x["factor_assessments"][0]["evidence_refs"].pop())
    elif problem == "economic_field": edit(folder / "combination_declaration.json", lambda x: x["specs"][0].update(top_n=60))
    elif problem == "original_failure": edit(folder / "application_validation_failure.json", lambda x: x.update(error="other failure"))
    elif problem == "source_pin": edit(folder / "protocol.json", lambda x: x["source_sha256"].update({"information_application.py": "wrong"}))
    with pytest.raises(ValueError): recovery.verify_recovered_application_declaration(root)


def test_new_economic_failure_is_retained_without_retry(failed_reference_stage, monkeypatch):
    root, *_ = failed_reference_stage
    def fail(*args, **kwargs): raise ValueError("synthetic old compiler economic violation")
    monkeypatch.setattr(recovery, "_outputs", fail)
    with pytest.raises(ValueError, match="economic violation"): recovery.recover_application_references(root)
    folder = root / "cycles" / app.CYCLE
    assert app.read(folder / "reference_recovery_failure.json")["automatic_retry"] is False
    assert not (folder / recovery.RECEIPT).exists()
    with pytest.raises(ValueError, match="unfinished offline recovery"): recovery.recover_application_references(root)


def test_existing_declaration_cannot_be_overwritten(failed_reference_stage):
    root, *_ = failed_reference_stage
    path = root / "cycles" / app.CYCLE / "combination_declaration.json"
    app.save_once(path, {"original": "preserve"})
    with pytest.raises(ValueError, match="replace an existing"): recovery.recover_application_references(root)
    assert app.read(path) == {"original": "preserve"}
