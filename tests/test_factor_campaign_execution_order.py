"""Registration-only coverage scheduling, including failed dense controls."""
from collections import Counter
from copy import deepcopy
from itertools import product
import json
import random

import pytest

from quanta_agents.factor_campaign.combination import CombinationSpec
from quanta_agents.factor_campaign.selection import execution_order

SIZES = (4, 8, 12, 24)
TARGETS = ("raw_return_demeaned", "rank_return_demeaned")
UPDATES = ("fixed", "quarterly_rolling3y", "quarterly_expanding")


def registered():
    result = []
    for size, route in product(SIZES, ("quality", "role_balanced", "diversity")):
        keys = tuple(f"{route}_{size}_{i}" for i in range(size))
        for target, update, regularizer in product(TARGETS, UPDATES, (.001, .01, .1, 1.)):
            result.append(CombinationSpec(route, keys, target=target, update_rule=update,
                ridge_lambda=regularizer, selection_rule=route))
        result.append(CombinationSpec(route, keys, method="equal_direction", selection_rule=route))
    dense = tuple("dense_"+str(i) for i in range(46))
    for target, update, regularizer in product(TARGETS, UPDATES, (.001, .01, .1, 1.)):
        result.append(CombinationSpec("dense_control", dense, target=target, update_rule=update,
                                      ridge_lambda=regularizer))
    return result


def report(spec, status="evaluated", duplicate=None):
    return {"status": status, "numeric_duplicate_of": duplicate, "spec": spec.to_dict(),
            "annual": [{"year": 2019, "mean_pearson_ic": -123.}],
            "summary": {"mean_pearson_ic": 123.}}


def successful_prefix(order, history=None, count=40):
    # All non-dense, unattempted specifications succeed in this availability
    # fixture. Dense failure is deliberately excluded from the success quota.
    previous = set(history or {})
    return [s for s in order if len(s.feature_ids) in SIZES and s.combination_id not in previous][:count]


def coverage(specs):
    return {(len(s.feature_ids), s.target, s.update_rule) for s in specs if s.method == "ridge"}


def test_first40_successes_cover_every_size_target_update_equal_and_lambda():
    declarations = registered()
    order = execution_order(declarations, {})
    prefix = successful_prefix(order)
    assert len(prefix) == 40
    assert coverage(prefix) == set(product(SIZES, TARGETS, UPDATES))
    equal = [s for s in prefix if s.method == "equal_direction"]
    assert Counter(len(s.feature_ids) for s in equal) == {n: 1 for n in SIZES}
    for size in SIZES:
        assert {s.ridge_lambda for s in prefix if len(s.feature_ids) == size and s.method == "ridge"} == {.001, .01, .1, 1.}
        assert len({s.feature_ids for s in prefix if len(s.feature_ids) == size}) >= 2
    assert len(order[8].feature_ids) == 46
    assert len(order) == len(declarations)


def test_dense_failures_never_fill_normal_coverage_or_success_quota():
    declarations = registered()
    dense = next(s for s in declarations if len(s.feature_ids) == 46 and s.target == TARGETS[0]
                 and s.update_rule == "fixed" and s.ridge_lambda == .1)
    history = {dense.combination_id: report(dense, "fit_unavailable")}
    order = execution_order(declarations, history)
    assert coverage(successful_prefix(order, history)) == set(product(SIZES, TARGETS, UPDATES))
    assert all(len(s.feature_ids) != 46 for s in order[:40])
    assert len([s for s in order if len(s.feature_ids) == 46]) == 24
    assert order[-1].combination_id == dense.combination_id
    assert len(order) == len(declarations)


def test_existing_size24_successes_prioritize_missing_sizes_and_preserve_attempts():
    declarations = registered()
    old = [s for s in declarations if len(s.feature_ids) == 24 and s.selection_rule == "quality"
           and (s.method == "equal_direction" or s.ridge_lambda == .1)]
    assert len(old) == 7
    history = {s.combination_id: report(s) for s in old}
    order = execution_order(declarations, history)
    remaining = successful_prefix(order, history)
    assert {len(s.feature_ids) for s in remaining[:3]} == {4, 8, 12}
    assert all(len(s.feature_ids) != 24 for s in remaining[:18])
    assert coverage(old+remaining) == set(product(SIZES, TARGETS, UPDATES))
    assert {s.combination_id for s in order[-7:]} == set(history)


def test_known_failed_or_duplicate_cell_gets_real_unattempted_alternative():
    declarations = registered()
    failed = next(s for s in declarations if len(s.feature_ids) == 4 and s.target == TARGETS[0]
                  and s.update_rule == "fixed" and s.ridge_lambda == .1 and s.selection_rule == "quality")
    twin = next(s for s in declarations if len(s.feature_ids) == 8 and s.target == TARGETS[0]
                and s.update_rule == "fixed" and s.ridge_lambda == .1)
    history = {failed.combination_id: report(failed, "fit_unavailable"),
               twin.combination_id: report(twin, duplicate="some_other_prediction")}
    order = execution_order(declarations, history)
    first = order[0]
    assert (len(first.feature_ids), first.target, first.update_rule) == (4, TARGETS[0], "fixed")
    assert first.feature_ids != failed.feature_ids
    assert coverage(successful_prefix(order, history)) == set(product(SIZES, TARGETS, UPDATES))
    assert {s.combination_id for s in order[-2:]} == set(history)


def test_shuffle_score_changes_and_report_order_cannot_change_execution_order():
    declarations = registered()
    history = {s.combination_id: report(s) for s in declarations[:6]}
    expected = [s.combination_id for s in execution_order(declarations, history)]
    original = deepcopy([s.to_dict() for s in declarations])
    shuffled = list(declarations)
    random.Random(57).shuffle(shuffled)
    other = deepcopy(history)
    for row in other.values():
        row["annual"] = [{"mean_pearson_ic": float("nan")}]
        row["summary"] = {"mean_pearson_ic": -1e300}
        row["paired_delta_pearson_ic"] = 1e300
    other = dict(reversed(list(other.items())))
    assert [s.combination_id for s in execution_order(shuffled, other)] == expected
    assert [s.to_dict() for s in declarations] == original


def test_score_fields_are_not_even_read():
    class Guard(dict):
        def get(self, key, default=None):
            if key not in ("status", "numeric_duplicate_of", "spec"):
                raise AssertionError("scheduling read forbidden evidence " + key)
            return super().get(key, default)
    declarations = registered()
    history = {s.combination_id: Guard(report(s)) for s in declarations[:3]}
    execution_order(declarations, history)


def test_equal_aliases_and_unsupported_registered_sizes_are_retained_once():
    members = tuple("x"+str(i) for i in range(4))
    first = CombinationSpec("first", members, method="equal_direction")
    alias = CombinationSpec("alias", members, method="equal_direction", target=TARGETS[1], ridge_lambda=1.)
    extended = CombinationSpec("future_registered_size", tuple("z"+str(i) for i in range(5)))
    declarations = [first, alias, first, extended]
    order = execution_order(declarations, {})
    assert len(order) == 2
    assert {s.combination_id for s in order} == {first.combination_id, extended.combination_id}
    assert [s.to_dict() for s in execution_order(list(reversed(declarations)), {})] == [s.to_dict() for s in order]
    assert [s.combination_id for s in execution_order(iter(declarations), {})] == [s.combination_id for s in order]
    assert all(s in declarations for s in order)


def test_previous_pool_coverage_and_invalid_history_identity():
    declarations = registered()
    previous = CombinationSpec("older_pool", tuple("past"+str(i) for i in range(4)))
    history = {previous.combination_id: report(previous)}
    prefix = execution_order(declarations, history)
    # The already-covered 4/raw/fixed cell is not falsely reset by a new pool.
    assert len(prefix[0].feature_ids) == 8
    assert coverage([previous]+successful_prefix(prefix, history)) == set(product(SIZES, TARGETS, UPDATES))
    with pytest.raises(ValueError, match="identity"):
        execution_order(declarations, {"wrong_identity": report(previous)})
