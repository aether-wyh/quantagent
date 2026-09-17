"""Synthetic counterexamples for the V5 evidence screen; no market reads."""
from copy import deepcopy
import pytest

from quanta_agents.meta_v5.analytics import evaluate_bundle, compare_profiles, digest


def policy():
    return {"version": "v5_stability_policy_v1", "expected_years": [2020, 2021],
        "annualization": 252, "risk_free_rate": .02, "min_sessions_per_year": 2,
        "min_paired_cell_fraction": 1., "min_unit_coverage_fraction": 1.,
        "min_positive_excess_year_fraction": .5, "min_positive_excess_unit_fraction": .5,
        "max_worst_year_excess_loss": .05, "max_drawdown": .5,
        "max_positive_pnl_concentration": 1., "max_stale_fraction": 0.,
        "require_known_fees": True, "require_exposure": True, "require_execution_certified": False}


def series(nav):
    return {"nav": nav, "exposure": [.8] * len(nav), "fees": [0.] * len(nav), "stale": [0] * len(nav)}


def bundle():
    return {"version": "v5_stability_bundle_v1", "candidate_id": "candidate", "program_hash": "a" * 64,
        "scope_id": "scope", "split": "development", "expected_units": ["one", "two"],
        "provenance": {"accounting_mode": "synthetic_full_cash", "execution_certified": False,
            "account_currency": "CNY", "fee_unit": "CNY", "external_cash_flows": "none_after_initial",
            "exposed": True, "source_hashes": {"synthetic": "b" * 64}, "cost_policy": {"mode": "explicit_zero_synthetic"}},
        "pairs": [{"unit_id": u, "unit_kind": "stock", "initial_nav": 100.,
            "calendar": ["2020-01-02", "2020-12-31", "2021-01-04", "2021-12-31"],
            "candidate": series([110., 120., 130., 140.]), "benchmark": series([100., 110., 115., 120.])}
            for u in ("one", "two")]}


def test_continuous_year_boundaries_and_full_capital():
    p = evaluate_bundle(bundle(), policy())
    assert p["development_eligible"] and not p["formal_target_success"]
    second = p["cells"][1]
    assert second["candidate_metrics"]["starting_nav"] == 120
    assert second["candidate_metrics"]["return"] == pytest.approx(140 / 120 - 1)
    assert p["full_period"][0]["candidate_metrics"]["return"] == pytest.approx(.4)
    assert digest({k: v for k, v in p.items() if k != "profile_hash"}) == p["profile_hash"]


def test_aggregate_peak_cannot_hide_bad_year_or_revision_damage():
    b = bundle();old = evaluate_bundle(b, policy())
    revised = deepcopy(b);revised["program_hash"] = "c" * 64
    revised["pairs"][0]["candidate"] = series([150., 300., 280., 260.])
    new = evaluate_bundle(revised, policy())
    assert new["full_period"][0]["candidate_metrics"]["return"] > old["full_period"][0]["candidate_metrics"]["return"]
    assert not new["development_eligible"]
    assert new["summary"]["statuses"]["heterogeneity"] == "fail"
    comparison = compare_profiles(old, new)
    assert "one:2021" in comparison["degraded_cell_ids"]
    assert comparison["heterogeneity_review_required"] and not comparison["adoption_recommended"]


def test_better_returns_with_new_drawdown_still_require_review():
    before = bundle()
    after = deepcopy(before)
    after["program_hash"] = "d" * 64
    after["pairs"][0]["candidate"] = series([140., 130., 145., 160.])
    comparison = compare_profiles(evaluate_bundle(before, policy()), evaluate_bundle(after, policy()))
    assert not comparison["degraded_cell_ids"]
    assert comparison["drawdown_degraded_cell_ids"] == ["one:2020"]
    assert comparison["heterogeneity_review_required"]


def test_missing_year_and_unit_do_not_reduce_denominator():
    b = bundle();b["pairs"].pop()
    pair = b["pairs"][0];pair["calendar"] = pair["calendar"][:2]
    for side in ("candidate", "benchmark"):
        pair[side] = {k: v[:2] for k, v in pair[side].items()}
    p = evaluate_bundle(b, policy())
    assert len(p["cells"]) == p["summary"]["expected_cells"] == 4
    assert p["summary"]["paired_cells"] == 1
    assert p["full_period"][0]["candidate_metrics"]["return"] is None
    assert p["cells"][1]["excess_return"] is None
    assert p["summary"]["positive_excess_year_fraction"] is None
    assert not p["development_eligible"]


@pytest.mark.parametrize("fault", ["benchmark", "risk", "fees", "stale"])
def test_missing_information_stays_unknown(fault):
    b = bundle()
    if fault == "benchmark": b["pairs"][0]["benchmark"] = None
    elif fault == "risk": b["pairs"][0]["candidate"]["nav"][1] = None
    elif fault == "fees": del b["pairs"][0]["candidate"]["fees"]
    else: del b["pairs"][0]["candidate"]["stale"]
    p = evaluate_bundle(b, policy())
    assert not p["development_eligible"]
    if fault == "benchmark": assert p["cells"][0]["excess_return"] is None
    elif fault == "risk":
        assert p["cells"][0]["candidate_metrics"]["max_drawdown"] is None
        assert p["summary"]["statuses"]["risk"] == "not_evaluable"
    else: assert p["summary"]["statuses"]["source_quality"] == "not_evaluable"


@pytest.mark.parametrize("fault", ["benchmark", "capital", "units", "calendar", "cost", "unit_kind", "source", "policy"])
def test_revision_requires_identical_comparison_identity(fault):
    b = bundle();old = evaluate_bundle(b, policy());newb = deepcopy(b);newp = policy()
    newb["program_hash"] = "c" * 64
    if fault == "benchmark": newb["pairs"][0]["benchmark"]["nav"][0] += 1
    elif fault == "capital": newb["pairs"][0]["initial_nav"] = 101
    elif fault == "units": newb["expected_units"].append("three")
    elif fault == "calendar": newb["pairs"][0]["calendar"][0] = "2020-01-03"
    elif fault == "cost": newb["provenance"]["cost_policy"]["mode"] = "different"
    elif fault == "unit_kind": newb["pairs"][0]["unit_kind"] = "portfolio"
    elif fault == "source": newb["provenance"]["source_hashes"]["synthetic"] = "d" * 64
    else: newp["expected_years"] = [2020, 2021, 2022]
    new = evaluate_bundle(newb, newp)
    with pytest.raises(ValueError): compare_profiles(old, new)


def test_profile_hash_and_program_scope_guards():
    p = evaluate_bundle(bundle(), policy());q = deepcopy(p);q["cells"][0]["excess_return"] = 999
    with pytest.raises(ValueError, match="hash drift"): compare_profiles(p, q)
    for field, value in (("program_hash", "wrong"), ("scope_id", "different")):
        b = bundle();b["pairs"][0][field] = value
        with pytest.raises(ValueError): evaluate_bundle(b, policy())
    b = bundle();b["split"] = "final"
    with pytest.raises(ValueError): evaluate_bundle(b, policy())
    p = policy();p.pop("max_stale_fraction")
    with pytest.raises(ValueError): evaluate_bundle(bundle(), p)


def test_negative_year_can_pass_when_relative_evidence_is_good():
    b = bundle()
    for pair in b["pairs"]:
        pair["candidate"] = series([110., 120., 115., 110.])
        pair["benchmark"] = series([105., 110., 95., 90.])
    p = evaluate_bundle(b, policy())
    assert p["cells"][1]["candidate_metrics"]["return"] < 0
    assert p["cells"][1]["excess_return"] > 0
    assert p["development_eligible"]


@pytest.mark.parametrize("field,bad_value", [("account_currency", "USD"), ("fee_unit", "fraction"),
    ("external_cash_flows", "deposits_included"), ("external_cash_flows", None)])
def test_unknown_currency_fee_unit_or_external_flows_cannot_be_nav_returns(field, bad_value):
    b = bundle(); b["provenance"][field] = bad_value
    with pytest.raises(ValueError, match="supported provenance"):
        evaluate_bundle(b, policy())


def test_distinct_result_hashes_allowed_only_with_explicit_common_scope_identity():
    b = bundle()
    b["provenance"]["source_scope_identity"] = {"market_input_sha256": "e" * 64, "scope": "frozen"}
    old = evaluate_bundle(b, policy())
    revised = deepcopy(b); revised["program_hash"] = "c" * 64
    revised["provenance"]["source_hashes"]["candidate_result"] = "f" * 64
    revised["pairs"][0]["candidate"]["nav"][-1] = 145.
    new = evaluate_bundle(revised, policy())
    assert compare_profiles(old, new)["paired"]
    assert old["provenance"]["source_hashes"] != new["provenance"]["source_hashes"]
    revised["provenance"]["source_scope_identity"]["market_input_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="source identity"):
        compare_profiles(old, evaluate_bundle(revised, policy()))


def test_all_failure_states_have_bound_issues_and_profile_does_not_alias_inputs():
    b = bundle(); pol = policy(); pol["require_execution_certified"] = True
    for pair in b["pairs"]:
        pair["candidate"] = series([80., 70., 60., 40.])
    p = evaluate_bundle(b, pol)
    codes = {i["code"] for i in p["issues"]}
    assert {"annual_increment_insufficient", "cross_unit_increment_insufficient",
            "risk_limit_exceeded", "execution_not_certified"}.issubset(codes)
    actual_ids = {c["cell_id"] for c in p["cells"]}
    assert all(set(i["cell_ids"]) <= actual_ids for i in p["issues"])
    assert p["expected_units"] == ["one", "two"]
    assert p["public_contract"]["development_policy_only"]
    b["expected_units"].append("new"); pol["max_drawdown"] = .9
    assert digest({k: v for k, v in p.items() if k != "profile_hash"}) == p["profile_hash"]


def test_missing_units_also_make_quality_unknown():
    b = bundle(); b["pairs"].pop()
    p = evaluate_bundle(b, policy())
    assert p["summary"]["statuses"]["source_quality"] == "not_evaluable"
    assert "coverage_below_policy" in {i["code"] for i in p["issues"]}


def test_missing_first_year_cannot_reset_next_year_to_scope_initial_capital():
    b = bundle()
    for pair in b["pairs"]:
        pair["calendar"] = pair["calendar"][2:]
        for side in ("candidate", "benchmark"):
            pair[side] = {k: v[2:] for k, v in pair[side].items()}
    p = evaluate_bundle(b, policy())
    assert p["cells"][1]["candidate_metrics"]["starting_nav"] is None
    assert p["cells"][1]["candidate_metrics"]["return"] is None
    assert p["cells"][1]["candidate_metrics"]["max_drawdown"] is None
    pol = policy(); pol["expected_years"] = [2020, 2022]
    with pytest.raises(ValueError, match="intervening"):
        evaluate_bundle(b, pol)
