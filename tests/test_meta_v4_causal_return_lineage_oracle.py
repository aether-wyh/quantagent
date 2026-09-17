"""Generated-only independent economic-return oracles.

No production lineage module is imported until its public API is agreed. These
are numerical feature identities, not account PnL, source authentication, tax
assessment, entitlement rounding, or execution certification.
"""
from fractions import Fraction as F
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib

import pytest


def oracle(previous, current, *, cash="0", bonus="0", capitalization="0"):
    """One original-share economic entitlement, before taxes and execution."""
    p0, p1 = F(previous), F(current)
    q, c = 1 + F(bonus) + F(capitalization), F(cash)
    return (q * p1 + c) / p0 - 1


NUMERICAL_CASES = [
    # Names intentionally describe generated arithmetic, not historical events.
    ("no_action", "10", "10.1", "0", "0", "0", F(1, 100)),
    ("cash_ex", "10", "9.9", "0.1", "0", "0", F(0)),
    ("bonus_ex", "12", "10", "0", "0.2", "0", F(0)),
    ("capitalization_ex", "14", "10", "0", "0", "0.4", F(0)),
    ("mixed_ex", "16", "9.9375", "0.1", "0.2", "0.4", F(0)),
    ("mixed_ex_price_rise", "16", "10.0375", "0.1", "0.2", "0.4", F(1, 100)),
]


@pytest.mark.parametrize("name,previous,current,cash,bonus,capitalization,expected", NUMERICAL_CASES)
def test_independent_exact_feature_identity(name, previous, current, cash, bonus, capitalization, expected):
    assert oracle(previous, current, cash=cash, bonus=bonus, capitalization=capitalization) == expected


def test_payment_and_listing_transfer_assets_without_creating_a_second_return():
    # On ex-date one original share has become 1.6 economic shares plus a .1
    # cash receivable. Payment moves that receivable into cash; listing moves
    # pending shares into sellable inventory. Neither creates another benefit.
    assert oracle("16", "9.9375", cash="0.1", bonus="0.2", capitalization="0.4") == 0
    assert oracle("9.9375", "9.9375") == 0
    assert oracle("9.9375", "9.9375", cash="0.1", bonus="0.2", capitalization="0.4") != 0


def test_gross_cash_is_not_tax_net_cash_or_bonus_par_tax_income():
    assert oracle("10", "9.9", cash="0.1") == 0
    assert oracle("10", "9.9", cash="0.08") == F(-1, 500)
    assert oracle("16", "9.9375", cash="0.1", bonus="0.2", capitalization="0.4") == 0
    # Adding bonus par value to cash fabricates an extra .2 per original share.
    assert oracle("16", "9.9375", cash="0.3", bonus="0.2", capitalization="0.4") == F(1, 80)


def test_qfq_price_plus_explicit_cash_would_double_count_the_dividend():
    # An adjusted prior close of 9.9 hides the original raw 10.0. Such a basis
    # must be rejected upstream, not accepted as a profitable generated return.
    assert oracle("9.9", "9.9", cash="0.1") == F(1, 99)
    assert oracle("10", "9.9", cash="0.1") == 0


def test_per_ten_announcement_must_be_normalized_to_the_same_original_share_unit():
    assert oracle("16", "9.9375", cash="0.1", bonus="0.2", capitalization="0.4") == 0
    assert oracle("16", "9.9375", cash="1", bonus="2", capitalization="4") != 0


def test_previous_actual_close_cannot_be_replaced_by_ex_reference_then_add_cash_again():
    # Fixed values supplied for the regression; this test reads no market file.
    correct = oracle("17.55", "17.24", cash="0.17")
    double_adjusted = oracle("17.38", "17.24", cash="0.17")
    assert correct == F(-14, 1755)
    assert double_adjusted == F(3, 1738)
    assert correct < 0 < double_adjusted


CALENDAR = ["2018-05-16", "2018-05-17", "2018-05-18", "2018-05-21"]
SYMBOL = "sh600000"


def identity(label):
    return hashlib.sha256(("generated-lineage-oracle:" + label).encode()).hexdigest()


def packet(previous="16", current="9.9375", *, cash="0.1", increment="0.6", include_action=True):
    """Plain generated source rows; hashes identify fixture labels, not sources."""
    prices = [
        {"session": day, "symbol": SYMBOL, "close": previous if index == 0 else current,
         "reference_previous_close": previous if index == 0 else current,
         "source_id": identity("price:" + day)}
        for index, day in enumerate(CALENDAR)
    ]
    action = {
        "action_id": "generated-action", "symbol": SYMBOL,
        "kind": "stock_distribution" if F(increment) else "cash",
        "announcement_date": "2018-05-14", "record_date": "2018-05-16",
        "ex_date": "2018-05-17", "payment_date": "2018-05-18", "listing_date": "2018-05-21",
        "available_at": "2018-05-15T08:00:00+08:00", "availability_basis": "generated",
        "share_increment_per_original_share": increment, "gross_cash_per_original_share": cash,
        "basis": "per_original_pre_ex_share", "status": "implementation", "source_id": identity("notice"),
    }
    return {
        "calendar": list(CALENDAR), "symbols": [SYMBOL], "prices": prices,
        "actions": [action] if include_action else [],
        "coverage": [{"session": day, "symbol": SYMBOL, "status": "generated_complete", "source_id": identity("coverage:" + day)}
                     for day in CALENDAR],
        "input_kind": "generated_engineering", "as_of": "2018-05-21T16:00:00+08:00",
        "previous_anchors": [{"session": "2018-05-15", "symbol": SYMBOL, "close": previous,
                              "reference_previous_close": previous, "source_id": identity("previous-anchor")}],
    }


def analyze(inputs):
    # Production module is intentionally imported only once its API exists.
    from quanta_agents.meta_v3.causal_return_lineage import analyze as production
    return production(**inputs)


def row(report, day="2018-05-17", symbol=SYMBOL):
    return next(item for item in report["rows"] if (item["session"], item["symbol"]) == (day, symbol))


def assert_exact_number(actual, expected):
    assert actual is not None
    with localcontext() as context:
        context.prec = 70
        expected_decimal = Decimal(expected.numerator) / Decimal(expected.denominator)
        assert abs(Decimal(actual) - expected_decimal) <= Decimal("1e-47")


@pytest.mark.parametrize("name,previous,current,cash,bonus,capitalization,expected", NUMERICAL_CASES)
def test_production_recomputes_economic_components_against_exact_oracle(name, previous, current, cash, bonus, capitalization, expected):
    increment = F(bonus) + F(capitalization)
    inputs = packet(previous, current, cash=cash, increment=str(float(increment)), include_action=name != "no_action")
    report = analyze(inputs)
    assert_exact_number(row(report)["diagnostic_return"], expected)
    assert all(item["qualified_return"] is None for item in report["rows"])


def test_production_uses_actual_close_and_reports_the_reference_double_adjustment_counterfactual():
    inputs = packet("17.55", "17.24", cash="0.17", increment="0")
    inputs["prices"][1]["reference_previous_close"] = "17.38"
    result = row(analyze(inputs))
    assert_exact_number(result["diagnostic_return"], F(-14, 1755))
    assert_exact_number(result["reference_denominator_counterfactual"], F(3, 1738))
    assert_exact_number(result["raw_price_only_return"], F(-31, 1755))
    assert_exact_number(result["reference_previous_close_delta"], F(-17, 100))
    assert result["qualified_return"] is None


def test_production_does_not_reaccrue_rights_on_payment_or_listing_day():
    report = analyze(packet())
    for day in ("2018-05-17", "2018-05-18", "2018-05-21"):
        assert_exact_number(row(report, day)["diagnostic_return"], F(0))


def test_changing_reference_price_cannot_change_the_diagnostic_numerator_or_denominator():
    inputs = packet()
    before = analyze(inputs)
    inputs["prices"][1]["reference_previous_close"] = "888"
    after = analyze(inputs)
    assert row(before)["diagnostic_return"] == row(after)["diagnostic_return"]
    assert row(before)["reference_denominator_counterfactual"] != row(after)["reference_denominator_counterfactual"]
    assert row(before)["inputs_sha256"] != row(after)["inputs_sha256"]


def test_later_payment_and_listing_dates_do_not_shift_ex_date_economic_return():
    inputs = packet()
    baseline = analyze(inputs)
    inputs["actions"][0]["payment_date"] = "2018-05-23"
    inputs["actions"][0]["listing_date"] = "2018-05-25"
    delayed = analyze(inputs)
    assert [entry["diagnostic_return"] for entry in baseline["rows"]] == [entry["diagnostic_return"] for entry in delayed["rows"]]


@pytest.mark.parametrize("status", ["unknown", "declared_complete", "generated_complete"])
@pytest.mark.parametrize("kind", ["generated_engineering", "caller_bound_exposed_development"])
def test_declared_coverage_and_input_label_cannot_create_qualified_or_authenticated_returns(status, kind):
    inputs = packet(include_action=False)
    inputs["input_kind"] = kind
    for coverage in inputs["coverage"]:
        coverage["status"] = status
    if kind == "caller_bound_exposed_development" and status == "generated_complete":
        with pytest.raises(ValueError, match="generated coverage"):
            analyze(inputs)
        return
    result = analyze(inputs)
    assert all(item["qualified_return"] is None for item in result["rows"])
    assert_exact_number(row(result)["diagnostic_return"], oracle("16", "9.9375"))
    for key in ("byte_origin_authenticated", "source_arrival_verified", "action_coverage_verified", "signal_admissible", "formal_target_success"):
        assert result[key] is False
    if status == "unknown":
        assert "action_coverage_unknown_no_absence_claim" in row(result)["reasons"]


@pytest.mark.parametrize("update", [
    {"kind": "unsupported"},
    {"status": "unresolved"},
    {"basis": "unknown"},
    {"record_date": None},
    {"announcement_date": None},
    {"record_date": "2018-05-15"},
])
def test_unsupported_or_incomplete_action_cannot_be_used_as_no_action(update):
    inputs = packet()
    inputs["actions"][0].update(update)
    result = row(analyze(inputs))
    assert result["diagnostic_return"] is None
    assert result["qualified_return"] is None
    assert result["reasons"]


def test_two_different_actions_on_the_same_ex_date_are_not_blindly_added_or_multiplied():
    inputs = packet()
    second = dict(inputs["actions"][0], action_id="second-action", source_id=identity("second-notice"))
    inputs["actions"].append(second)
    result = row(analyze(inputs))
    assert result["diagnostic_return"] is None
    assert result["reasons"]


def test_appending_future_correction_changes_submission_binding_but_not_visible_rows():
    inputs = packet()
    before = analyze(inputs)
    inputs["actions"].append(dict(inputs["actions"][0], gross_cash_per_original_share="99",
                                  available_at="2018-05-22T08:00:00+08:00", source_id=identity("future-correction")))
    after = analyze(inputs)
    assert after["rows"] == before["rows"]
    assert after["input_sha256"] == before["input_sha256"]
    assert after["submitted_input_sha256"] != before["submitted_input_sha256"]


def test_known_and_unknown_arrival_versions_cannot_silently_select_a_favorable_revision():
    inputs = packet()
    inputs["actions"].append(dict(inputs["actions"][0], gross_cash_per_original_share="99",
                                  available_at=None, availability_basis="unverified", source_id=identity("unknown-correction")))
    result = row(analyze(inputs))
    assert result["diagnostic_return"] is None
    assert result["qualified_return"] is None
    assert result["reasons"]


def test_same_timestamp_conflicting_revisions_remain_unresolved():
    inputs = packet()
    inputs["actions"].append(dict(inputs["actions"][0], gross_cash_per_original_share="99", source_id=identity("conflicting-correction")))
    result = row(analyze(inputs))
    assert result["diagnostic_return"] is None
    assert result["qualified_return"] is None
    assert result["reasons"]


def test_single_unknown_arrival_is_only_a_retrospective_scenario_not_a_qualified_return():
    inputs = packet()
    inputs["actions"][0].update(available_at=None, availability_basis="unverified")
    result = row(analyze(inputs))
    assert_exact_number(result["diagnostic_return"], F(0))
    assert result["qualified_return"] is None
    assert result["reasons"]


@pytest.mark.parametrize("target", ["current", "previous"])
@pytest.mark.parametrize("value", [None, "0"])
def test_missing_or_zero_original_prices_do_not_use_reference_previous_as_a_fallback(target, value):
    inputs = packet()
    index = 1 if target == "current" else 0
    inputs["prices"][index]["close"] = value
    inputs["prices"][index]["reference_previous_close"] = "10"
    result = row(analyze(inputs))
    assert result["diagnostic_return"] is None
    assert result["qualified_return"] is None


def test_lineage_analysis_does_not_mutate_original_price_action_or_coverage_inputs():
    inputs = packet()
    prior = deepcopy(inputs)
    first = analyze(inputs)
    assert inputs == prior
    assert analyze(inputs) == first
    assert inputs == prior


def test_equivalent_timezone_instants_have_the_same_visible_rows_and_calendar_scope():
    inputs = packet()
    china = analyze(inputs)
    inputs["as_of"] = "2018-05-20T22:00:00-10:00"
    other_zone = analyze(inputs)
    assert other_zone["rows"] == china["rows"]
    assert other_zone["rows_sha256"] == china["rows_sha256"]
    assert other_zone["as_of"] != china["as_of"]


def test_latest_visible_correction_updates_only_the_explicit_retrospective_scenario():
    inputs = packet()
    before = analyze(inputs)
    inputs["actions"].append(dict(inputs["actions"][0], gross_cash_per_original_share="0.2",
                                  available_at="2018-05-20T08:00:00+08:00", source_id=identity("visible-correction")))
    after = analyze(inputs)
    assert_exact_number(row(before)["diagnostic_return"], F(0))
    assert_exact_number(row(after)["diagnostic_return"], F(1, 160))
    assert row(before)["inputs_sha256"] != row(after)["inputs_sha256"]
    assert row(after)["qualified_return"] is None
    for day in ("2018-05-16", "2018-05-18", "2018-05-21"):
        assert row(after, day) == row(before, day)


@pytest.mark.parametrize("field", ["payment_date", "listing_date"])
def test_payment_or_listing_before_ex_date_is_an_explicit_unresolved_scenario(field):
    inputs = packet()
    inputs["actions"][0][field] = "2018-05-16"
    result = row(analyze(inputs))
    assert result["diagnostic_return"] is None
    assert "payment_or_listing_before_ex_date" in result["reasons"]


def test_previous_anchor_is_optional_but_missing_actual_price_is_never_reconstructed():
    inputs = packet()
    inputs["previous_anchors"] = []
    report = analyze(inputs)
    first = row(report, "2018-05-16")
    assert first["diagnostic_return"] is None
    assert first["previous_session"] is None
    assert "actual_previous_close_missing_no_reference_substitution" in first["reasons"]
    assert_exact_number(row(report)["diagnostic_return"], F(0))


def test_complete_original_price_and_coverage_denominators_cannot_drop_a_date():
    for field in ("prices", "coverage"):
        inputs = packet()
        inputs[field].pop(1)
        with pytest.raises(ValueError, match="complete original"):
            analyze(inputs)


def test_sealed_calendar_is_rejected_before_any_price_or_action_traversal():
    inputs = packet()
    inputs["calendar"] = ["2024-05-16", "2024-05-17", "2024-05-20"]
    inputs["as_of"] = "2024-05-20T16:00:00+08:00"
    inputs["prices"], inputs["actions"] = object(), object()
    with pytest.raises(ValueError, match="sealed or non-development calendar"):
        analyze(inputs)


def test_report_hashes_bind_source_identity_changes_without_authenticating_them():
    inputs = packet()
    before = analyze(inputs)
    inputs["prices"][1]["source_id"] = identity("different-unverified-price-source")
    after = analyze(inputs)
    assert row(before)["diagnostic_return"] == row(after)["diagnostic_return"]
    assert row(before)["inputs_sha256"] != row(after)["inputs_sha256"]
    assert after["input_sha256"] != before["input_sha256"]
    assert after["byte_origin_authenticated"] is False
