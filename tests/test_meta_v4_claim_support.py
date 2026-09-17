"""Offline counterexamples with hand-calculated answers, not model evaluation."""
from copy import deepcopy
from decimal import localcontext

import pytest

from quanta_agents.meta_v3.claim_support import contract, review_claims


SCOPE = "real_saved_development"


def evidence():
    # Independently chosen arithmetic: 10000 -> 9500 is -5%; 8%-5%=3 pp.
    return {
        "account": {"action": "develop_strategy", "public": {"account_summary": {
            "initial_cash": "10000", "final_net_asset_value": "9500",
            "net_return_on_full_initial_cash": "-0.05", "maximum_daily_drawdown": "0.10",
            "cash_days_including_no_position_days": 12}}},
        "horizon": {"action": "diagnose_horizons", "public": {"horizon_summary": {
            "descriptive_conditioning": [{"horizon": 3, "high_mean": "0.08", "low_mean": "0.05",
                "matched_mean_difference": "0.03", "matched_pairs": 7}]}}},
        "partial": {"action": "diagnose_execution", "public": {"causal_root_cause_identified": False,
            "accounts": [{"final_nav": None, "return_on_full_initial_cash": None,
                "fees_on_recorded_trades": "17.08", "saved_cash_days": 4}]}},
    }


def claim(**changes):
    return {"claim_id": "net_return", "kind": "numeric", "evidence_id": "account",
        "path": ["account_summary", "net_return_on_full_initial_cash"],
        "relation": "eq", "value": "-5", "unit": "percent", "research_class": SCOPE, **changes}


def check(item, sources=None, **kwargs):
    return review_claims([item], evidence() if sources is None else sources, research_class=SCOPE, **kwargs)


@pytest.mark.parametrize('kind, metric, unit, value, expected', [
    ('whole_input_scope', 'sessions', 'count', '244', 'supported'),
    ('whole_input_scope', 'initial_cash', 'CNY', '1000000', 'supported'),
    ('whole_input_scope', 'sessions', 'CNY', '244', 'unsupported'),
    ('whole_input_scope', 'initial_cash', 'count', '1000000', 'unsupported'),
    ('whole_input_scope', 'sessions', 'count', '245', 'contradicted'),
    ('whole_input_scope', 'initial_cash', 'CNY', '500000', 'contradicted'),
    ('field_coverage', 'sessions', 'count', '244', 'needs_review'),
    (None, 'initial_cash', 'CNY', '1000000', 'needs_review'),
])
def test_input_coverage_units_require_the_saved_row_kind(kind, metric, unit, value, expected):
    row = {'sessions': 244, 'initial_cash': '1000000'}
    if kind is not None:
        row['kind'] = kind
    sources = {'inputs': {'action': 'inspect_inputs', 'public': {'rows': [row]}}}
    result = check(claim(evidence_id='inputs', path=['rows', 0, metric], unit=unit, value=value), sources)
    assert result['claims'][0]['status'] == expected
    assert result['general_report_truth_verified'] is False


@pytest.mark.parametrize("changes, expected", [
    ({}, "supported"),
    ({"value": "5"}, "contradicted"),  # Sign reversal.
    ({"value": "-0.05"}, "contradicted"),  # Fraction displayed as percent.
    ({"value": "-0.05", "unit": "fraction"}, "supported"),
    ({"relation": "gt", "value": "0"}, "contradicted"),
    ({"relation": "lt", "value": "0"}, "supported"),
    ({"relation": "between", "value": ["-6", "-4"]}, "supported"),
    ({"relation": "between", "value": ["0", "6"]}, "contradicted"),
    ({"relation": "between", "value": ["-4", "-6"]}, "invalid"),
    ({"unit": "CNY"}, "unsupported"),
    ({"research_class": "certified_OOS"}, "unsupported"),
    ({"evidence_id": "other_task_account"}, "unsupported"),
    ({"path": ["account_summary", "annualized_sharpe"]}, "unsupported"),
])
def test_known_account_truth_and_counterexamples(changes, expected):
    result = check(claim(**changes))
    assert result["claims"][0]["status"] == expected
    assert result["evidence_support_accepted"] is (expected == "supported")


@pytest.mark.parametrize("unit, value, expected", [
    ("percentage_points", "3", "supported"), ("basis_points", "300", "supported"),
    ("fraction_difference", "0.03", "supported"), ("percent", "3", "unsupported"),
    ("percentage_points", "-3", "contradicted"),
])
def test_descriptive_difference_has_correct_units(unit, value, expected):
    result = check(claim(evidence_id="horizon",
        path=["horizon_summary", "descriptive_conditioning", 0, "matched_mean_difference"], unit=unit, value=value))
    assert result["claims"][0]["status"] == expected


def test_descriptive_comparison_cannot_establish_cause_but_cautious_prose_is_not_rejected():
    base = {"claim_id": "mechanism", "evidence_id": "horizon", "research_class": SCOPE}
    causal = check({**base, "kind": "causal", "text": "The feature caused the 3 percentage point difference."})
    cautious = check({**base, "kind": "descriptive", "text": "A 3 percentage point difference was observed; confounding remains."})
    assert causal["claims"][0]["status"] == "unsupported"
    assert cautious["claims"][0]["status"] == "needs_review"
    assert not cautious["evidence_support_accepted"]


def test_unknown_final_nav_is_never_imputed_but_recorded_fee_is_checkable():
    unknown = check(claim(evidence_id="partial", path=["accounts", 0, "final_nav"], unit="CNY", value="0"))
    fee = check(claim(evidence_id="partial", path=["accounts", 0, "fees_on_recorded_trades"], unit="CNY", value="17.08"))
    assert unknown["claims"][0]["reason"] == "saved_value_unknown_not_zero"
    assert fee["claims"][0]["status"] == "supported"


def test_prose_and_unknown_metrics_cannot_be_certified_by_correct_numeric_tuple():
    result = check(claim(text="The strategy made a profit and this proves the causal mechanism."),
        report_text="The strategy made a profit and this proves the causal mechanism.")
    assert result["claims"][0]["status"] == "supported"
    assert result["claims"][0]["text_support"] == "unverified"
    assert result["report_text_support"] == "needs_review"
    assert not result["general_report_truth_verified"]
    source = evidence()
    source["account"]["public"]["author_claim"] = {"annualized_sharpe": "2"}
    assert check(claim(path=["author_claim", "annualized_sharpe"], unit="multiple", value="2"), source)["claims"][0]["status"] == "needs_review"


def test_explicit_rounding_and_local_decimal_context_do_not_change_answer():
    source = evidence()
    source["account"]["public"]["account_summary"]["net_return_on_full_initial_cash"] = "0.126474123456789"
    with localcontext() as ctx:
        ctx.prec = 6
        rounded = check(claim(value="12.6474", decimal_places=4), source)
        exact = check(claim(value="12.6474"), source)
    assert rounded["claims"][0]["status"] == "supported"
    assert exact["claims"][0]["status"] == "contradicted"
    assert check(claim(value="12.65", decimal_places=1), source)["claims"][0]["status"] == "invalid"


@pytest.mark.parametrize("value", [True, "NaN", "Infinity", "1e999999", "0e999999999999", {"amount": 5}])
def test_nonfinite_and_malformed_values_are_not_accepted(value):
    assert check(claim(value=value))["claims"][0]["status"] == "invalid"


def test_bounds_duplicates_and_no_mutation():
    sources = evidence()
    before = deepcopy(sources)
    result = review_claims([claim(), claim()], sources, research_class=SCOPE)
    assert result["claims"][1]["reason"] == "duplicate_claim_id"
    assert not result["evidence_support_accepted"]
    assert sources == before
    with pytest.raises(ValueError, match="1..16"):
        review_claims([], sources, research_class=SCOPE)
    assert contract()["version"] == "claim_support_v1"


def test_current_legal_report_check_does_not_establish_semantic_support():
    # Reproduce the actual gap in the pre-policy path without executing a model,
    # mutating saved research, creating a ledger or hand-writing an old result.
    from quanta_agents.meta_v3.research_tools import ResearchTools
    tool = ResearchTools.__new__(ResearchTools)
    tool.case = {"research_class": SCOPE}
    tool.report_policy = None
    tool.history = [{"id": "account", "result": evidence()["account"]}]
    report = {"outcome": "abstain", "conclusion": "The saved account gained 5%.",
        "evidence_ids": ["account"], "program_evidence_id": None,
        "limitations": ["Development sample"], "next_step": "Review saved evidence.",
        "falsifiers": ["An independent account calculation differs."]}
    assert tool.final(report)["legal_submission"] is True
    result = check(claim(value="5"), report_text=report["conclusion"])
    assert result["claims"][0]["status"] == "contradicted"
    assert not result["evidence_support_accepted"]
