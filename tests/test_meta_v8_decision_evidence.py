"""Saved-evidence and generated-signal checks; no model or market-data access."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta_v7.benchmarks import make_synthetic_task
from quanta_agents.meta_v7.decision_evidence import compact_factors_v8
from quanta_agents.meta_v7.factor_lab import evaluate_factors
from quanta_agents.meta_v7.protocol import compact_factors


def _stats(mean=.02, n=98, deficient=None):
    row = {"mean_ic": mean, "observed_days": n, "calendar_days": 100,
           "missing_days": 100 - n, "paired_cells": n * 20, "daily_ic_std": .15,
           "annual": [{"year": 2019, "mean_ic": mean, "observed_days": n, "calendar_days": 100}],
           "coverage": {"fraction": n / 100, "observed_cells": n * 20,
                        "pool_cells": 2000, "missing_cells": (100 - n) * 20}}
    if deficient is not None:
        row["rank_deficient_days"] = deficient
    return row


def _report():
    risk = _stats(.04)
    return {"status": "completed", "scope": {"role": "training_development", "start": "2019-01-01", "end": "2019-12-31"},
        "factors": {
            "weak": {"roles": ["return", "condition"], "coverage": _stats()["coverage"],
                     "horizons": {"5": _stats(.0001)}, "risk": {}},
            "risk": {"roles": ["risk"], "coverage": risk["coverage"],
                     "horizons": {"5": _stats(0)}, "risk": {"5": {"future_vol": risk}}}},
        "correlations": [{"left": "weak", "right": "risk", **_stats(.01)}],
        "conditions": [{"left": "weak", "right": "risk", "horizon": 5, "condition": "low",
                        "condition_uses_future": False, **_stats(-.02)},
                       {"left": "weak", "right": "risk", "horizon": 5, "condition": "high",
                        "condition_uses_future": False, **_stats(.03)}],
        "interactions": [{"left": "weak", "right": "risk", "status": "evaluated",
                          "horizons": {"5": {"raw_ic": _stats(.01), "partial_ic": _stats(.015),
                                             "coverage": _stats()["coverage"]}}}],
        "limitations": ["Generated saved-statistic fixture, no alpha claim."],
        "semantics": {"conditions": "right factor daily rank <=.5 and >.5"}}


def _row(view, table, values):
    return dict(zip(view["table_schema"][table], values))


def _support(view, row):
    return _row(view, "evidence_support", view["evidence_support"][row["support"]])


def _assert_metrics_same(source, view):
    """Check all saved values/support independently of the encoder's layout."""
    for name, factor in source["factors"].items():
        for values in view["factors"][name]["ic"]:
            row = _row(view, "ic", values)
            original = factor["horizons"][row["horizon"]]
            assert row["mean_ic"] == original["mean_ic"]
            assert _support(view, row)["observed_days"] == original["observed_days"]
        for values in view["factors"][name]["risk"]:
            row = _row(view, "risk", values)
            original = factor["risk"][row["horizon"]][row["metric"]]
            assert row["mean_ic"] == original["mean_ic"]
            for key in ("observed_days", "calendar_days", "missing_days", "paired_cells"):
                assert _support(view, row)[key] == original[key]
    assert len(view["interactions"]) == len(source["interactions"])
    for before, after in zip(source["interactions"], view["interactions"]):
        assert view["table_schema"]["factor_ids"][after["left"]] == before["left"]
        assert view["table_schema"]["factor_ids"][after["right"]] == before["right"]
        for values in after["ic"]:
            row = _row(view, "interaction_ic", values)
            original = before["horizons"][row["horizon"]][row["metric"]]
            assert row["mean_ic"] == original["mean_ic"]
            assert _support(view, row)["rank_deficient_days"] == original.get("rank_deficient_days")
    for before, after in zip(source["conditions"], view["conditions"]):
        row = _row(view, "conditions", after)
        assert row["mean_ic"] == before["mean_ic"]
        assert row["condition"] == before["condition"]
        assert row["condition_uses_future"] == before["condition_uses_future"]


def test_single_day_and_many_day_risk_means_are_distinguishable_without_recomputation():
    before, altered = _report(), _report()
    altered["factors"]["risk"]["risk"]["5"]["future_vol"] = _stats(.04, 1)
    assert compact_factors(before) == compact_factors(altered)  # Confirm V7 information loss.
    a, b = compact_factors_v8(before), compact_factors_v8(altered)
    ra = _row(a, "risk", a["factors"]["risk"]["risk"][0])
    rb = _row(b, "risk", b["factors"]["risk"]["risk"][0])
    assert ra["mean_ic"] == rb["mean_ic"] == .04
    assert _support(a, ra)["observed_days"] == 98
    assert _support(b, rb)["observed_days"] == 1
    assert b["table_schema"]["status_codes"][rb["status"]] == "single_observed_day"
    assert a != b


def test_unknown_and_rank_deficient_partial_evidence_remain_distinct_from_zero():
    source = _report()
    source["interactions"][0]["horizons"]["5"]["partial_ic"] = _stats(None, 0, 98)
    source["factors"]["risk"]["risk"]["5"]["future_vol"] = _stats(None, 0)
    before = deepcopy(source)
    view = compact_factors_v8(source)
    partial = next(_row(view, "interaction_ic", r) for r in view["interactions"][0]["ic"] if r[1] == "partial_ic")
    risk = _row(view, "risk", view["factors"]["risk"]["risk"][0])
    zero = _row(view, "ic", view["factors"]["risk"]["ic"][0])
    assert partial["mean_ic"] is None and partial["status"] == "rd"
    assert _support(view, partial)["rank_deficient_days"] == 98
    assert risk["mean_ic"] is None and risk["status"] == "na"
    assert zero["mean_ic"] == 0 and zero["status"] == "d"
    assert source == before
    json.dumps(view, allow_nan=False)


def test_weak_conditions_and_interactions_are_not_filtered_and_roles_can_be_targeted():
    source = _report()
    view = compact_factors_v8(source)
    _assert_metrics_same(source, view)
    assert set(view["factors"]) == {"weak", "risk"}
    assert view["selection"]["filtered_by_efficacy"] is False
    assert view["interpretation"]["automatic_admission"] is False
    assert [r[3] for r in view["conditions"]] == ["low", "high"]
    scoped = compact_factors_v8(source, roles=["risk"])
    assert set(scoped["factors"]) == {"risk"}
    assert len(scoped["conditions"]) == 2  # Keep named partner and direction.
    assert scoped["selection"]["total_factors"] == 2
    assert scoped["selection"]["returned_factors"] == 1
    assert compact_factors_v8(source, ids=["weak"], roles=["risk"])["factors"] == {}


def test_annual_sign_changes_and_one_day_year_are_visible_and_review_recovers_exact_years():
    source = _report()
    years = [{"year": 2016, "mean_ic": .2, "observed_days": 1, "calendar_days": 240},
             {"year": 2017, "mean_ic": -.1, "observed_days": 97, "calendar_days": 240},
             {"year": 2018, "mean_ic": None, "observed_days": 0, "calendar_days": 240}]
    source["factors"]["risk"]["risk"]["5"]["future_vol"]["annual"] = years
    view = compact_factors_v8(source)
    row = _row(view, "risk", view["factors"]["risk"]["risk"][0])
    assert row["annual_summary"] == [-.1, .2, 1, 1, 0, 1]
    assert _support(view, row)["min_observed_days_per_known_year"] == 1
    review = compact_factors_v8(source, detail="review")
    row = _row(review, "risk", review["factors"]["risk"]["risk"][0])
    assert row["annual"] == [[2016, .2], [2017, -.1], [2018, None]]
    assert _support(review, row)["annual_days"] == [[2016, 1, 240], [2017, 97, 240], [2018, 0, 240]]


@pytest.mark.parametrize("kind", ["interaction", "redundancy", "null"])
@pytest.mark.parametrize("seed", [17, 39])
def test_generated_weak_interaction_redundancy_and_null_all_saved_means_are_preserved(seed, kind):
    task = make_synthetic_task(seed, kind, train_sessions=60, validation_sessions=20, stocks=32)
    if kind == "interaction":
        # Freeze a weaker effect than the V7 strong-signal benchmark, without
        # changing opaque candidate identities or using validation for choice.
        ids = task["truth"]["discovery_groups"][0]["candidate_ids"][0].split(":")[1:]
        a, b = (task["frames"][identity] for identity in ids)
        rng = np.random.default_rng(seed + 101)
        returns = .001 * a * b + rng.normal(0, .02, size=a.shape)
        daily = returns.shift(2).fillna(0)
        opening = 10 * (1 + daily).cumprod()
        task["panel"].fields.update({"open": opening, "close": opening.copy(),
            "high": opening * 1.002, "low": opening * .998})
    ids = sorted(task["frames"])
    source = evaluate_factors(task["panel"], task["frames"],
        start=task["split_plan"]["train_start"], end=task["split_plan"]["train_end"], horizons=(1,),
        pairs=[{"left": ids[i], "right": ids[j]} for i in range(4) for j in range(i + 1, 4)])
    original = deepcopy(source)
    view = compact_factors_v8(source)
    _assert_metrics_same(source, view)
    assert source == original
    assert len(view["factors"]) == 4 and len(view["interactions"]) == 6
    assert view["interpretation"]["automatic_admission"] is False
    assert all(not row["automatic_admission"] for row in source["interactions"])


@pytest.mark.parametrize("options", [{"detail": "adaptive"}, {"ids": ["unknown"]},
                                      {"roles": ["alpha"]}, {"roles": []}, {"ids": "weak"}])
def test_invalid_requested_scope_is_explicit(options):
    with pytest.raises(ValueError):
        compact_factors_v8(_report(), **options)


def test_partial_missing_support_is_unknown_and_malformed_statistics_are_not_silently_repaired():
    source = _report()
    target = source["factors"]["risk"]["risk"]["5"]["future_vol"]
    target.pop("observed_days")
    view = compact_factors_v8(source)
    row = _row(view, "risk", view["factors"]["risk"]["risk"][0])
    assert row["status"] == "u" and _support(view, row)["observed_days"] is None
    for invalid in [float("nan"), float("inf"), True, "0.04"]:
        target["mean_ic"] = invalid
        with pytest.raises(ValueError, match="saved IC"):
            compact_factors_v8(source)
