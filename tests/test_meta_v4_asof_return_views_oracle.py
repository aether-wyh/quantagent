"""Independent generated-only oracles for signal-time return version views.

No real market file, account, saved audit backend, or network is used. These
generated dates are fixture coordinates, not an assertion of exchange sessions.
The production API tests are added after its schema is confirmed.
"""
from datetime import date, timedelta
from fractions import Fraction as F
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
import json

import pytest


def generated_calendar(count=66):
    days, day = [], date(2018, 1, 2)
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day.isoformat())
        day += timedelta(days=1)
    return days


def exact_entitlement_return(previous, current, *, cash="0", increment="0"):
    return ((1 + F(increment)) * F(current) + F(cash)) / F(previous) - 1


def test_generated_correction_is_between_two_original_signal_anchors():
    calendar = generated_calendar()
    early, arrival, late = calendar[60], calendar[62], calendar[65]
    assert early < arrival < late
    assert len(calendar[1:61]) == len(calendar[6:66]) == 60
    assert calendar[30] in calendar[1:61] and calendar[30] in calendar[6:66]


def test_cash_revision_changes_the_past_return_in_later_information_without_changing_original_math():
    assert exact_entitlement_return("10", "9.9", cash="0.1") == 0
    assert exact_entitlement_return("10", "9.9", cash="0.2") == F(1, 100)


def test_original_actual_close_versus_reference_double_adjustment_has_opposite_sign():
    assert exact_entitlement_return("17.55", "17.24", cash="0.17") == F(-14, 1755)
    assert exact_entitlement_return("17.38", "17.24", cash="0.17") == F(3, 1738)


SYMBOL = "sh600000"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def identity(label):
    return hashlib.sha256(("generated-asof-oracle:" + label).encode()).hexdigest()


def independent_seal(version):
    """Implement the documented receipt identity independently of its helper."""
    version = deepcopy(version)
    version.pop("evidence_id", None)
    receipt = {
        "evidence_class": "generated_engineering", "version_sha256": digest(version),
        "source_sha256": version["source_id"], "observed_arrival_at": version["observed_arrival_at"],
        "arrival_basis": version["arrival_basis"],
    }
    receipt["receipt_id"] = digest(receipt)
    version["evidence_id"] = receipt["receipt_id"]
    return version, receipt


def packet():
    calendar = generated_calendar()
    prices, coverage, receipts = [], [], []
    for index, day in enumerate(calendar):
        for kind, fields in (
            ("price", {"session": day, "close": "10" if index < 30 else "9.9", "reference_previous_close": "10" if index < 30 else "9.9"}),
            ("coverage", {"session": day, "status": "generated_complete", "action_ids": ["cash-action"] if index == 30 else []}),
        ):
            version, receipt = independent_seal({
                "version_id": kind + ":" + day + ":v1", "symbol": SYMBOL,
                "effective_at": day + "T15:00:00+08:00", "observed_arrival_at": day + "T15:05:00+08:00",
                "arrival_basis": "generated", "source_id": identity(kind + ":" + day), **fields,
            })
            (prices if kind == "price" else coverage).append(version)
            receipts.append(receipt)
    action, receipt = independent_seal({
        "version_id": "cash-notice:v1", "symbol": SYMBOL,
        "effective_at": calendar[25] + "T08:00:00+08:00", "observed_arrival_at": calendar[25] + "T08:05:00+08:00",
        "arrival_basis": "generated", "source_id": identity("cash-notice:v1"),
        "action_id": "cash-action", "kind": "cash", "announcement_date": calendar[25],
        "record_date": calendar[29], "ex_date": calendar[30], "payment_date": calendar[32], "listing_date": None,
        "share_increment_per_original_share": "0", "gross_cash_per_original_share": "0.1",
        "basis": "per_original_pre_ex_share", "status": "implementation",
    })
    receipts.append(receipt)
    return {
        "calendar": calendar, "symbols": [SYMBOL], "signal_dates": [calendar[60], calendar[65]],
        "price_versions": prices, "action_versions": [action], "coverage_versions": coverage,
        "evidence_receipts": receipts, "evidence_class": "generated_engineering",
    }


def build(inputs):
    from quanta_agents.meta_v3.asof_return_views import build as production
    return production(**inputs)


def append_version(inputs, field, base, **updates):
    changed, receipt = independent_seal(dict(base, **updates))
    inputs[field].append(changed)
    inputs["evidence_receipts"].append(receipt)
    return changed


def replace_version(inputs, field, index, **updates):
    original = inputs[field][index]
    changed, receipt = independent_seal(dict(original, **updates))
    inputs[field][index] = changed
    inputs["evidence_receipts"].append(receipt)
    return changed


def cell(view, session, symbol=SYMBOL):
    return next(row for row in view["rows"] if (row["session"], row["symbol"]) == (session, symbol))


def assert_number(value, expected):
    assert value is not None
    with localcontext() as context:
        context.prec = 70
        wanted = Decimal(expected.numerator) / Decimal(expected.denominator)
        assert abs(Decimal(str(value)) - wanted) <= Decimal("1e-40")


def test_complete_windows_preserve_all_original_sixty_return_coordinates():
    inputs = packet()
    output = build(inputs)
    for index, view in zip((60, 65), output["views"]):
        assert view["status"] == "complete_window"
        assert view["window_sessions"] == inputs["calendar"][index-59:index+1]
        assert view["first_previous_session"] == inputs["calendar"][index-60]
        assert [(row["session"], row["symbol"]) for row in view["rows"]] == [(day, SYMBOL) for day in view["window_sessions"]]
        assert len(view["rows"]) == 60
        for row in view["rows"]:
            assert row["qualified_return"] is None
            assert_number(row["generated_qualified_return"], F(0))
            assert_number(row["diagnostic_return"], F(0))
            assert row["blockers"] == []
    assert output["source_authenticated"] is False and output["formal_target_success"] is False


def test_future_action_revision_does_not_change_early_view_but_is_usable_at_later_signal():
    inputs = packet(); calendar = inputs["calendar"]
    before = build(inputs)
    append_version(inputs, "action_versions", inputs["action_versions"][0], version_id="cash-notice:v2",
        effective_at=calendar[62]+"T08:00:00+08:00", observed_arrival_at=calendar[62]+"T08:05:00+08:00",
        source_id=identity("cash-notice:v2"), gross_cash_per_original_share="0.2")
    after = build(inputs)
    assert after["views"][0] == before["views"][0]
    assert after["views"][0]["view_sha256"] == before["views"][0]["view_sha256"]
    assert after["submitted_input_sha256"] != before["submitted_input_sha256"]
    assert_number(cell(after["views"][0], calendar[30])["generated_qualified_return"], F(0))
    assert_number(cell(after["views"][1], calendar[30])["generated_qualified_return"], F(1,100))


def test_future_price_revision_updates_both_historical_return_endpoints_only_in_later_view():
    inputs = packet(); calendar = inputs["calendar"]
    before = build(inputs)
    append_version(inputs, "price_versions", inputs["price_versions"][30], version_id="price-correction:v2",
        effective_at=calendar[62]+"T08:00:00+08:00", observed_arrival_at=calendar[62]+"T08:05:00+08:00",
        source_id=identity("price-correction:v2"), close="9.8")
    after = build(inputs)
    assert after["views"][0] == before["views"][0]
    late = after["views"][1]
    assert_number(cell(late,calendar[30])["generated_qualified_return"], F(-1,100))
    assert_number(cell(late,calendar[31])["generated_qualified_return"], F(1,98))


@pytest.mark.parametrize("field", ["price_versions", "coverage_versions", "action_versions"])
def test_future_version_arriving_after_all_signals_does_not_change_any_view_or_view_hash(field):
    inputs = packet(); before=build(inputs)
    base=inputs[field][30] if field != "action_versions" else inputs[field][0]
    updates={"version_id":"future:"+field,"effective_at":"2019-01-02T08:00:00+08:00",
             "observed_arrival_at":"2019-01-02T08:05:00+08:00","source_id":identity("future:"+field)}
    if field == "price_versions": updates["close"]="88"
    elif field == "action_versions": updates["status"]="withdrawn"
    else: updates["status"]="unknown"
    append_version(inputs,field,base,**updates)
    after=build(inputs)
    assert after["views"]==before["views"]
    assert after["views_sha256"]==before["views_sha256"]
    assert after["submitted_input_sha256"]!=before["submitted_input_sha256"]


def test_late_required_price_stays_missing_at_early_signal_and_arrives_for_later_signal():
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,"price_versions",30,observed_arrival_at=calendar[62]+"T08:05:00+08:00")
    output=build(inputs)
    for day in (calendar[30],calendar[31]):
        early=cell(output["views"][0],day)
        assert early["generated_qualified_return"] is None and early["diagnostic_return"] is None
        assert early["blockers"]
        assert_number(cell(output["views"][1],day)["generated_qualified_return"],F(0))
    assert len(output["views"][0]["rows"])==60


@pytest.mark.parametrize("field,index", [("price_versions",30),("coverage_versions",30),("action_versions",0)])
def test_unknown_arrival_never_creates_generated_or_real_qualified_returns(field,index):
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,field,index,observed_arrival_at=None)
    output=build(inputs)
    for view in output["views"]:
        affected=cell(view,calendar[30])
        assert affected["generated_qualified_return"] is None and affected["qualified_return"] is None
        assert affected["blockers"]


@pytest.mark.parametrize("field,index,updates", [
    ("price_versions",30,{"close":"88"}),
    ("coverage_versions",30,{"status":"unknown"}),
    ("action_versions",0,{"gross_cash_per_original_share":"88"}),
])
def test_same_instant_conflicts_are_not_arbitrarily_resolved(field,index,updates):
    inputs=packet(); calendar=inputs["calendar"]
    append_version(inputs,field,inputs[field][index],version_id="same-time-conflict",source_id=identity("same-time-conflict"),**updates)
    output=build(inputs)
    for view in output["views"]:
        affected=cell(view,calendar[30])
        assert affected["generated_qualified_return"] is None
        assert affected["blockers"]
        if field != "coverage_versions": assert affected["diagnostic_return"] is None


def test_unknown_and_known_action_versions_do_not_fall_back_to_the_known_version():
    inputs=packet(); calendar=inputs["calendar"]
    append_version(inputs,"action_versions",inputs["action_versions"][0],version_id="unknown-correction",
                   observed_arrival_at=None,source_id=identity("unknown-correction"),gross_cash_per_original_share="88")
    result=cell(build(inputs)["views"][0],calendar[30])
    assert result["generated_qualified_return"] is None and result["diagnostic_return"] is None
    assert result["blockers"]


def test_withdrawn_latest_visible_action_does_not_revive_an_old_version_or_become_no_action():
    inputs=packet(); calendar=inputs["calendar"]
    baseline=build(inputs)
    append_version(inputs,"action_versions",inputs["action_versions"][0],version_id="withdrawal:v2",
        effective_at=calendar[62]+"T08:00:00+08:00",observed_arrival_at=calendar[62]+"T08:05:00+08:00",
        source_id=identity("withdrawal:v2"),status="withdrawn")
    output=build(inputs)
    assert output["views"][0]==baseline["views"][0]
    changed=cell(output["views"][1],calendar[30])
    assert changed["generated_qualified_return"] is None and changed["diagnostic_return"] is None
    assert changed["blockers"]


def test_actual_previous_close_and_gross_cash_are_used_instead_of_adjusted_reference():
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,"price_versions",29,close="17.55")
    replace_version(inputs,"price_versions",30,close="17.24",reference_previous_close="17.38")
    replace_version(inputs,"action_versions",0,gross_cash_per_original_share="0.17")
    affected=cell(build(inputs)["views"][0],calendar[30])
    assert_number(affected["generated_qualified_return"],F(-14,1755))
    assert_number(affected["diagnostic_return"],F(-14,1755))
    assert affected["qualified_return"] is None


@pytest.mark.parametrize("field,index", [("price_versions",30),("coverage_versions",30),("action_versions",0)])
def test_missing_receipt_blocks_locally_without_deleting_dates(field,index):
    inputs=packet(); calendar=inputs["calendar"]
    identity=inputs[field][index]["evidence_id"]
    inputs["evidence_receipts"]=[r for r in inputs["evidence_receipts"] if r["receipt_id"]!=identity]
    view=build(inputs)["views"][0]
    assert len(view["rows"])==60
    assert cell(view,calendar[30])["generated_qualified_return"] is None
    assert cell(view,calendar[30])["blockers"]
    assert_number(cell(view,calendar[20])["generated_qualified_return"],F(0))


def test_a_changed_price_with_an_old_receipt_cannot_become_generated_qualified():
    inputs=packet(); calendar=inputs["calendar"]
    inputs["price_versions"][30]["close"]="88"
    view=build(inputs)["views"][0]
    assert cell(view,calendar[30])["generated_qualified_return"] is None
    assert cell(view,calendar[31])["generated_qualified_return"] is None
    assert cell(view,calendar[30])["blockers"]


def test_generated_receipts_cannot_authenticate_caller_bound_real_inputs():
    inputs=packet(); inputs["evidence_class"]="caller_bound_exposed_development"
    with pytest.raises(ValueError,match="generated timing"):
        build(inputs)


def test_unverified_real_input_timing_cannot_be_upgraded_by_generated_receipt_metadata():
    inputs=packet(); inputs["evidence_class"]="caller_bound_exposed_development"
    inputs["evidence_receipts"]=[]
    for field in ("price_versions","action_versions","coverage_versions"):
        for index,version in enumerate(inputs[field]):
            changed=dict(version,arrival_basis="unverified")
            if field=="coverage_versions": changed["status"]="unknown"
            sealed,receipt=independent_seal(changed)
            inputs[field][index]=sealed
            inputs["evidence_receipts"].append(receipt)
    output=build(inputs)
    assert output["source_authenticated"] is False and output["formal_target_success"] is False
    for view in output["views"]:
        for result in view["rows"]:
            assert result["qualified_return"] is None
            assert result["generated_qualified_return"] is None
            assert result["blockers"]


@pytest.mark.parametrize("updates", [{"status":"unknown"},{"action_ids":[]}])
def test_coverage_unknown_or_omitted_action_identity_is_not_a_no_action_certificate(updates):
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,"coverage_versions",30,**updates)
    affected=cell(build(inputs)["views"][0],calendar[30])
    assert affected["generated_qualified_return"] is None and affected["qualified_return"] is None
    assert affected["blockers"]


def test_unsupported_rights_scenario_does_not_use_cash_only_or_no_action_fallback():
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,"action_versions",0,kind="unsupported",share_increment_per_original_share="0.2",gross_cash_per_original_share="0")
    affected=cell(build(inputs)["views"][0],calendar[30])
    assert affected["generated_qualified_return"] is None and affected["diagnostic_return"] is None
    assert affected["blockers"]


def test_insufficient_history_keeps_original_anchor_and_all_available_coordinates():
    inputs=packet(); calendar=inputs["calendar"]
    inputs["signal_dates"]=[calendar[1],calendar[5],calendar[60]]
    output=build(inputs)
    assert [v["signal_date"] for v in output["views"]]==inputs["signal_dates"]
    for index,view in zip((1,5),output["views"][:2]):
        assert view["status"]=="insufficient_history"
        assert view["available_return_sessions"]==index
        assert [r["session"] for r in view["rows"]]==calendar[1:index+1]
        assert all(r["generated_qualified_return"] is None and r["qualified_return"] is None for r in view["rows"])
    assert output["views"][2]["status"]=="complete_window"


def test_version_list_order_does_not_change_visible_view_order_or_hashes():
    inputs=packet(); before=build(inputs)
    for field in ("price_versions","action_versions","coverage_versions","evidence_receipts"):
        inputs[field]=list(reversed(inputs[field]))
    after=build(inputs)
    assert after["views"]==before["views"]
    assert after["views_sha256"]==before["views_sha256"]


def test_view_builder_preserves_input_versions_and_receipts():
    inputs=packet(); snapshot=deepcopy(inputs)
    first=build(inputs)
    assert inputs==snapshot
    assert build(inputs)==first
    assert inputs==snapshot


def test_generated_binding_helper_agrees_with_independent_receipt_identity_without_mutation():
    from quanta_agents.meta_v3.asof_return_views import bind_generated
    original=packet()["price_versions"][0]
    original={k:v for k,v in original.items() if k!="evidence_id"}
    snapshot=deepcopy(original)
    assert bind_generated(original)==independent_seal(original)
    assert original==snapshot


@pytest.mark.parametrize("arrival_suffix,available", [("T15:10:00+08:00",True),("T15:10:00.000001+08:00",False),("T07:10:00Z",True)])
def test_signal_cutoff_is_inclusive_and_timezone_aware(arrival_suffix,available):
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,"price_versions",30,observed_arrival_at=calendar[60]+arrival_suffix)
    output=build(inputs)
    value=cell(output["views"][0],calendar[30])
    assert (value["generated_qualified_return"] is not None) is available
    if available:
        assert_number(value["generated_qualified_return"],F(0))
        assert value["maximum_available_at"]==calendar[60]+"T15:10:00+08:00"
    else:
        assert value["blockers"]
    assert_number(cell(output["views"][1],calendar[30])["generated_qualified_return"],F(0))


def test_version_claiming_arrival_before_effective_time_is_not_qualified():
    inputs=packet(); calendar=inputs["calendar"]
    replace_version(inputs,"price_versions",30,effective_at=calendar[62]+"T08:00:00+08:00",
                    observed_arrival_at=calendar[61]+"T08:00:00+08:00")
    affected=cell(build(inputs)["views"][1],calendar[30])
    assert affected["generated_qualified_return"] is None
    assert "current_price_time_order_invalid" in affected["blockers"]


def test_index_coverage_exception_is_explicit_and_preserves_original_symbol_order():
    inputs=packet(); inputs["symbols"]=["000905.SH",SYMBOL]
    for field in ("price_versions","coverage_versions"):
        for base in list(inputs[field]):
            changed={"symbol":"000905.SH","version_id":"index:"+base["version_id"],"source_id":identity("index:"+base["version_id"])}
            if field=="price_versions": changed.update(close="100",reference_previous_close="100")
            else: changed.update(status="not_applicable_price_index",action_ids=[])
            append_version(inputs,field,base,**changed)
    output=build(inputs)
    for view in output["views"]:
        assert [(r["session"],r["symbol"]) for r in view["rows"]]==[(day,code) for day in view["window_sessions"] for code in inputs["symbols"]]
        assert len(view["rows"])==120
        for day in view["window_sessions"]:
            assert_number(cell(view,day,"000905.SH")["generated_qualified_return"],F(0))


def test_index_no_action_exception_cannot_be_used_for_a_stock():
    inputs=packet()
    replace_version(inputs,"coverage_versions",30,status="not_applicable_price_index",action_ids=[])
    with pytest.raises(ValueError,match="price-index exception"):
        build(inputs)


def test_sealed_calendar_is_refused_before_version_inventory_traversal():
    inputs=packet()
    inputs["calendar"]=["2024-01-02","2024-01-03","2024-01-04"]
    inputs["signal_dates"]=["2024-01-04"]
    inputs["price_versions"]=object(); inputs["action_versions"]=object()
    with pytest.raises(ValueError,match="sealed or non-development"):
        build(inputs)


def test_declared_per_coordinate_version_budget_cannot_be_bypassed_with_new_identifiers():
    inputs=packet(); base=inputs["price_versions"][30]
    for index in range(8):
        append_version(inputs,"price_versions",base,version_id="over-budget:"+str(index),source_id=identity("over-budget:"+str(index)))
    with pytest.raises(ValueError,match="at most eight versions"):
        build(inputs)
