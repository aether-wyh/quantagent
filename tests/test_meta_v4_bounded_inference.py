"""Independent generated arithmetic and custody-shape counterexamples only.

No study files, market data, strategy execution, or source certification.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math

import pytest

from quanta_agents.meta_v3.bounded_inference import VERSION, infer_frozen_blocks, lower_bound
from quanta_agents.meta_v3.formal_statistics import ARCHITECTURES


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def fixture(cases=(("A", "F1", 3, "real_research"),), *, weighting="family_equal"):
    slots, outcomes, calendars, family_dates = [], [], {}, {}
    for case, family, repeats, role in cases:
        if family not in family_dates:
            day = len(family_dates) + 1
            family_dates[family] = [f"2019-01-{day:02d}"]
        dates = family_dates[family]
        cal = digest(dates)
        if role == "real_research":
            calendars[cal] = dates
        for repeat in range(1, repeats + 1):
            for arch in ARCHITECTURES:
                sid = f"{case}.{repeat}.{arch}"
                slots.append(dict(slot_id=sid, case_id=case, family=family, repeat=repeat,
                    role=role, architecture=arch, case_definition_sha256=digest(case),
                    calendar_sha256=cal, initial_capital_cny="1000000"))
                outcomes.append(dict(slot_id=sid, classification="valid_nonsuccess",
                    reason="generated fixture; no market or strategy execution"))
    manifest = dict(version="frozen_slot_statistics_v1", input_kind="generated_fixture",
        statistical_draft_sha256="d" * 64, slots=slots,
        original_order=[row["slot_id"] for row in slots], shared_shock_ids=[])
    families = sorted({row["family"] for row in slots if row["role"] == "real_research"})
    blocks = [dict(id=family, slot_ids=[row["slot_id"] for row in slots
        if row["role"] == "real_research" and row["family"] == family]) for family in families]
    design = dict(version=VERSION, manifest_sha256=digest(manifest), primary_weighting=weighting,
        alpha_family="1/20", blocks=blocks, calendar_dates=calendars, dependency_groups=[],
        population_statement="Generated independent block vectors only; no new-market inference.",
        independence_review_reference="generated fixture assumption, not authenticated")
    return manifest, outcomes, design


def set_architecture(outcomes, architecture, classification, **fields):
    for outcome in outcomes:
        if outcome["slot_id"].endswith("." + architecture):
            outcome.update(classification=classification, **fields)


def bound(result, endpoint="v4_success"):
    return result["conditional_inference"][endpoint]


def collapse(design):
    design["blocks"] = [dict(id="all-original-slots", slot_ids=[sid
        for block in design["blocks"] for sid in block["slot_ids"]])]


@pytest.mark.parametrize("n", [1, 3, 5, 6, 18, 864])
def test_all_one_bound_matches_independent_analytic_endpoint(n):
    with localcontext() as ctx:
        ctx.prec = 70
        exact = (Decimal(1) / Decimal(60)).ln().__truediv__(Decimal(n)).exp()
    result = lower_bound([1] * n, "1/60")
    assert Decimal(str(result["lower"])) <= exact
    assert float(exact) - result["lower"] <= 2e-12
    assert abs(result["root_upper_bracket"] - float(exact)) < 2e-14
    assert result["mean_exact"] == "1" and result["blocks"] == n
    assert result["formal_accepted"] is False


@pytest.mark.parametrize("values", [[0], [0] * 18, ["0", Fraction(0)]])
def test_all_zero_lower_and_upper_are_zero(values):
    result = lower_bound(values, "1/60")
    assert result["lower"] == result["root_upper_bracket"] == 0
    assert result["mean_exact"] == "0"


@pytest.mark.parametrize("values", [[0, 1], [Fraction(1, 2)] * 2,
    [0, "1/4", "1/2", "3/4", 1]])
def test_heterogeneous_bounded_values_use_mean_without_rounding_to_bernoulli(values):
    # At mean 1/2, inversion has this separate closed form for every G.
    with localcontext() as ctx:
        ctx.prec = 70
        a = Decimal(1) / Decimal(60)
        power = (a.ln() * Decimal(2) / Decimal(len(values))).exp()
        exact = (Decimal(1) - (Decimal(1) - power).sqrt()) / Decimal(2)
    result = lower_bound(values, "1/60")
    assert result["mean_exact"] == "1/2"
    assert Decimal(str(result["lower"])) <= exact
    assert float(exact) - result["lower"] < 2e-12


def test_actual_declared_error_budget_and_power_boundary():
    assert lower_bound([1] * 3, "1/60")["lower"] < .5
    assert lower_bound([1] * 5, "1/60")["lower"] < .5
    assert lower_bound([1] * 6, "1/60")["lower"] > .5
    assert lower_bound([1] * 12 + [0] * 6, "1/60")["lower"] < .5
    assert lower_bound([1] * 14 + [0] * 4, "1/60")["lower"] < .5
    assert lower_bound([1] * 15 + [0] * 3, "1/60")["lower"] > .5


def test_strict_half_boundary_is_not_promoted_by_rounding():
    result = lower_bound([1] * 6, "1/64")
    assert result["lower"] <= .5 and .5 - result["lower"] < 2e-12


@pytest.mark.parametrize("values,alpha", [([], ".05"), ([1] * 865, ".05"), ((0, 1), ".05"),
    ([True], ".05"), ([float("nan")], ".05"), ([float("inf")], ".05"),
    (["NaN"], ".05"), (["1/0"], ".05"), (["-1/100"], ".05"), (["101/100"], ".05"),
    (["1e1000"], ".05"), ([0], 0), ([0], True), ([0], ".5"), ([0], "1e-13")])
def test_bad_numerical_inputs_are_rejected(values, alpha):
    with pytest.raises(ValueError):
        lower_bound(values, alpha)


def test_every_original_pair_and_unknown_is_preserved():
    manifest, _, design = fixture()
    result = infer_frozen_blocks(manifest, [], design)
    assert result["original_slots"] == result["original_real_slots"] == 9
    assert bound(result)["mean_exact"] == "0"
    assert bound(result)["lower"] == 0
    for architecture in ARCHITECTURES:
        descriptive = result["descriptive_architectures"][architecture]
        assert descriptive["original_real_slots"] == descriptive["missing_outcomes"] == 3
    for baseline in ARCHITECTURES[1:]:
        assert result["descriptive_paired_gains"][baseline]["original_pairs"] == 3
        assert result["descriptive_paired_gains"][baseline]["raw_mean_difference"] == "0"
        assert bound(result, baseline)["block_scores_exact"] == ["0"]
        assert bound(result, baseline)["endpoint_lower"] == -1


def test_unknown_baseline_never_creates_optimistic_gain():
    manifest, outcomes, design = fixture()
    set_architecture(outcomes, ARCHITECTURES[0], "valid_success")
    set_architecture(outcomes, ARCHITECTURES[1], "outcome_unknown")
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert result["descriptive_paired_gains"][ARCHITECTURES[1]]["raw_mean_difference"] == "1"
    assert bound(result, ARCHITECTURES[1])["block_scores_exact"] == ["1/2"]
    assert bound(result, ARCHITECTURES[1])["endpoint_lower"] <= 0
    # A baseline proved nonsuccess is a different, fully observed endpoint.
    assert bound(result, ARCHITECTURES[2])["block_scores_exact"] == ["1"]


def test_missing_saved_audit_reference_is_not_a_proven_baseline_failure():
    manifest, outcomes, design = fixture()
    manifest["input_kind"] = "caller_validated_saved_records"
    design["manifest_sha256"] = digest(manifest)
    set_architecture(outcomes, ARCHITECTURES[0], "valid_success",
        audit_binding={"reference": "generated-unread-reference", "sha256": "a" * 64})
    set_architecture(outcomes, ARCHITECTURES[1], "valid_success", outcome_unknown=False)
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert bound(result, ARCHITECTURES[1])["block_scores_exact"] == ["1/2"]
    assert result["input_authentication_performed"] is False


def test_saved_references_and_independence_claim_never_self_certify():
    manifest, outcomes, design = fixture()
    manifest["input_kind"] = "caller_validated_saved_records"
    design["manifest_sha256"] = digest(manifest)
    design["independence_review_reference"] = "I certify these units are independent"
    for outcome in outcomes:
        outcome.update(classification="valid_success",
            audit_binding={"reference": "does-not-exist-and-must-not-be-opened", "sha256": "a" * 64})
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert bound(result)["mean_exact"] == "1"
    for key in ("independence_authenticated", "input_authentication_performed",
                "formal_financial_accepted", "formal_architecture_improvement_accepted"):
        assert result[key] is False


def test_raw_case_and_family_weighting_keep_their_original_mean():
    cases = (("A", "F1", 1, "real_research"), ("B", "F2", 3, "real_research"),
             ("C", "F2", 3, "real_research"))
    expected = {"raw_start": "1/7", "case_equal": "1/3", "family_equal": "1/2"}
    for weighting in expected:
        manifest, outcomes, design = fixture(cases, weighting=weighting)
        for outcome in outcomes:
            if outcome["slot_id"] == "A.1." + ARCHITECTURES[0]:
                outcome["classification"] = "valid_success"
        collapse(design)
        result = infer_frozen_blocks(manifest, outcomes, design)
        assert bound(result)["mean_exact"] == expected[weighting]
        assert result["block_masses_exact"] == {"all-original-slots": "1"}


@pytest.mark.parametrize("weighting,masses", [("raw_start", {"F1": "1/7", "F2": "6/7"}),
    ("case_equal", {"F1": "1/3", "F2": "2/3"})])
def test_unequal_original_block_mass_is_not_silently_reweighted(weighting, masses):
    manifest, outcomes, design = fixture((("A", "F1", 1, "real_research"),
        ("B", "F2", 3, "real_research"), ("C", "F2", 3, "real_research")), weighting=weighting)
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert result["status"] == "unequal_mass_not_evaluable"
    assert result["conditional_inference"] is None
    assert result["block_masses_exact"] == masses
    assert result["original_real_slots"] == 21


def test_equal_family_mass_can_include_different_case_and_repeat_counts():
    manifest, outcomes, design = fixture((("A", "F1", 1, "real_research"),
        ("B", "F2", 3, "real_research"), ("C", "F2", 3, "real_research")))
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert result["status"] == "conditional_only"
    assert result["block_masses_exact"] == {"F1": "1/2", "F2": "1/2"}
    assert result["alpha_family_exact"] == "1/20"
    assert bound(result)["alpha_exact"] == "1/60"


@pytest.mark.parametrize("fault", ["missing", "duplicate", "extra", "control"])
def test_complete_original_real_membership_is_mandatory(fault):
    manifest, outcomes, design = fixture((("A", "F1", 3, "real_research"),
                                         ("N", "negative", 3, "negative_control")))
    ids = design["blocks"][0]["slot_ids"]
    if fault == "missing":
        ids.pop()
    elif fault == "duplicate":
        ids[1] = ids[0]
    elif fault == "extra":
        ids[1] = "not-an-original-slot"
    else:
        ids[1] = "N.1." + ARCHITECTURES[0]
    with pytest.raises(ValueError):
        infer_frozen_blocks(manifest, outcomes, design)


def test_controls_have_their_own_denominator():
    manifest, outcomes, design = fixture((("A", "F1", 3, "real_research"),
                                         ("N", "negative", 3, "negative_control")))
    for outcome in outcomes:
        if outcome["slot_id"].startswith("N."):
            outcome.update(classification="correct_abstention", sharpe_rf2="99999")
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert result["original_slots"] == 18 and result["original_real_slots"] == 9
    assert bound(result)["mean_exact"] == "0"
    assert all(row["original_control_slots"] == 3 and row["correct_abstention_rate"] == "1"
        for row in result["negative_controls"].values())


def test_changed_manifest_is_rejected_before_inference():
    manifest, outcomes, design = fixture()
    manifest["original_order"].reverse()
    with pytest.raises(ValueError, match="manifest binding drift"):
        infer_frozen_blocks(manifest, outcomes, design)


def test_same_case_cannot_be_split_into_apparent_independent_restarts():
    manifest, outcomes, design = fixture()
    design["blocks"] = [dict(id=f"repeat-{r}", slot_ids=[row["slot_id"] for row in manifest["slots"]
        if row["repeat"] == r]) for r in (1, 2, 3)]
    with pytest.raises(ValueError, match="dependent original slots split"):
        infer_frozen_blocks(manifest, outcomes, design)


def test_same_family_cannot_be_split_by_case_even_with_distinct_calendar_hashes():
    manifest, outcomes, design = fixture((("A", "F1", 3, "real_research"),
                                         ("B", "F1", 3, "real_research")))
    dates = ["2019-03-01"]
    for row in manifest["slots"]:
        if row["case_id"] == "B":
            row["calendar_sha256"] = digest(dates)
    design["calendar_dates"][digest(dates)] = dates
    design["manifest_sha256"] = digest(manifest)
    design["blocks"] = [dict(id=c, slot_ids=[row["slot_id"] for row in manifest["slots"]
        if row["case_id"] == c]) for c in ("A", "B")]
    with pytest.raises(ValueError, match="dependent original slots split"):
        infer_frozen_blocks(manifest, outcomes, design)


def test_different_calendar_hashes_with_one_shared_date_are_dependent():
    manifest, outcomes, design = fixture((("A", "F1", 3, "real_research"),
                                         ("B", "F2", 3, "real_research")))
    by_case = {"A": ["2019-03-01", "2019-03-04"], "B": ["2019-03-04", "2019-03-05"]}
    design["calendar_dates"] = {digest(days): days for days in by_case.values()}
    for row in manifest["slots"]:
        row["calendar_sha256"] = digest(by_case[row["case_id"]])
    design["manifest_sha256"] = digest(manifest)
    with pytest.raises(ValueError, match="market_date"):
        infer_frozen_blocks(manifest, outcomes, design)
    collapse(design)
    assert bound(infer_frozen_blocks(manifest, outcomes, design))["blocks"] == 1


@pytest.mark.parametrize("scope", ["manifest", "outcomes", "additional"])
def test_known_common_shock_must_keep_every_affected_slot_in_one_block(scope):
    manifest, outcomes, design = fixture((("A", "F1", 3, "real_research"),
                                         ("B", "F2", 3, "real_research")))
    if scope == "manifest":
        manifest["shared_shock_ids"] = ["shared-budget-or-provider-shock"]
        design["manifest_sha256"] = digest(manifest)
    elif scope == "outcomes":
        for outcome in outcomes:
            outcome["shared_shock_ids"] = ["same-shock"]
    else:
        design["dependency_groups"] = [dict(reason="common latent market draw",
            slot_ids=[row["slot_id"] for row in manifest["slots"]])]
    with pytest.raises(ValueError, match="dependent original slots split"):
        infer_frozen_blocks(manifest, outcomes, design)
    collapse(design)
    set_architecture(outcomes, ARCHITECTURES[0], "valid_success")
    result = infer_frozen_blocks(manifest, outcomes, design)
    assert bound(result)["blocks"] == 1 and bound(result)["lower"] < .02


@pytest.mark.parametrize("dates", [["2019-99-99"], ["2019-02-30"], ["not-a-date"], ["2019-2-003"]])
def test_calendar_hash_does_not_legitimize_invalid_dates(dates):
    manifest, outcomes, design = fixture()
    cal = digest(dates)
    for row in manifest["slots"]:
        row["calendar_sha256"] = cal
    design["manifest_sha256"] = digest(manifest)
    design["calendar_dates"] = {cal: dates}
    with pytest.raises(ValueError):
        infer_frozen_blocks(manifest, outcomes, design)


def test_inputs_and_raw_saved_status_are_not_mutated():
    manifest, outcomes, design = fixture()
    outcomes[1].update(classification="outcome_unknown", costs={"unknown_reserve": 37},
                       reason="receipt unavailable; no economic result asserted")
    before = deepcopy((manifest, outcomes, design))
    infer_frozen_blocks(manifest, outcomes, design)
    assert (manifest, outcomes, design) == before


@pytest.mark.parametrize("key", ["independence_authenticated", "formal_financial_accepted", "verified"])
def test_untrusted_extra_design_certification_flag_is_rejected(key):
    manifest, outcomes, design = fixture()
    design[key] = True
    with pytest.raises(ValueError, match="invalid frozen inference design"):
        infer_frozen_blocks(manifest, outcomes, design)
