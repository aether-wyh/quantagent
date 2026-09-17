"""Fixed-seed synthetic benchmarks; no model or market-data calls."""
from copy import deepcopy

import numpy as np
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v7.benchmarks import make_synthetic_task, run_deterministic_benchmark, score_discovery


@pytest.mark.parametrize("kind", ["interaction", "redundancy", "null"])
def test_fixture_reproducible_isolated_and_return_timing(kind):
    task = make_synthetic_task(7, kind=kind, train_sessions=30, validation_sessions=20)
    again = make_synthetic_task(7, kind=kind, train_sessions=30, validation_sessions=20)
    assert task["task_id"] == again["task_id"]
    assert task["public"]["hidden_truth_included"] is False
    assert "kind" not in task["public"]
    assert "truth" not in task["panel"].provenance
    for key in task["frames"]:
        assert_frame_equal(task["frames"][key], again["frames"][key], check_exact=True)
    assert task["train_labels"].iloc[-2:].isna().all().all()
    assert task["validation_labels"].iloc[-2:].isna().all().all()
    assert task["train_labels"].index[-1] < task["validation_labels"].index[0]
    expected = task["panel"].fields["open"].shift(-2) / task["panel"].fields["open"].shift(-1) - 1
    assert_frame_equal(task["train_labels"].iloc[:-2], expected.loc[task["train_labels"].index[:-2]])


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_interaction_has_low_marginals_and_discovery_oos_for_registered_seeds(seed):
    task = make_synthetic_task(seed)
    linear = run_deterministic_benchmark(task, "fixed_soft")
    product = run_deterministic_benchmark(task, "factor_lab")
    assert linear["training_evaluations"] == product["training_evaluations"] == 10
    singles = [row["mean_ic"] for row in product["training_candidates"] if row["candidate_id"].startswith("factor:")]
    assert max(abs(value) for value in singles) < .08
    assert linear["discovery"]["discovered_sources"] == 0
    assert product["discovery"]["discovered_sources"] == 1
    assert product["validation"]["mean_ic"] > .6
    assert product["model_calls"] is None and product["model_tokens"] is None
    assert product["formal_financial_success"] is False


def test_redundant_predictions_count_one_source():
    task = make_synthetic_task(2, "redundancy")
    ids = task["truth"]["discovery_groups"][0]["candidate_ids"]
    result = score_discovery(ids, task["truth"])
    assert result["discovered_sources"] == 1
    assert result["redundant_discoveries"] == 2
    assert result["false_positive_count"] == 0
    for mode in ("fixed_soft", "factor_lab"):
        evaluated = run_deterministic_benchmark(task, mode)
        assert evaluated["discovery"]["discovered_sources"] == 1
        assert evaluated["validation"]["mean_ic"] > .6


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_null_rejection_and_explicit_false_positives(seed):
    task = make_synthetic_task(seed, "null")
    for mode in ("fixed_soft", "factor_lab"):
        result = run_deterministic_benchmark(task, mode)
        assert result["discovery"]["correct_null_rejection"]
        assert result["validation_evaluations"] == 0
    forced = score_discovery([task["truth"]["candidate_universe"][0]], task["truth"])
    assert forced["false_positive_count"] == 1
    assert not forced["correct_null_rejection"]


def test_validation_numeric_perturbation_cannot_change_frozen_training_selection():
    task = make_synthetic_task(4)
    first = run_deterministic_benchmark(task, "factor_lab")
    task["validation_labels"][:] *= -100.
    for frame in task["frames"].values():
        frame.loc[task["split_plan"]["validation_start"]:] = np.nan
    second = run_deterministic_benchmark(task, "factor_lab")
    assert first["frozen_selection"] == second["frozen_selection"]
    assert first["training_candidates"] == second["training_candidates"]
    assert second["validation"]["mean_ic"] is None


def test_same_budget_enforced_and_unknown_modes_fail():
    task = make_synthetic_task(0, train_sessions=30, validation_sessions=20)
    budget = {"max_evaluations": 4, "max_discoveries": 1, "min_absolute_train_ic": .08}
    for mode in ("fixed_soft", "factor_lab"):
        result = run_deterministic_benchmark(task, mode, budget)
        assert result["training_evaluations"] == 4
        assert result["budget"] == budget
    with pytest.raises(ValueError):
        run_deterministic_benchmark(task, "model")
    with pytest.raises(ValueError):
        run_deterministic_benchmark(task, budget={**budget, "max_evaluations": 11})


def test_fixture_bad_arguments_and_unknown_prediction_reported():
    with pytest.raises(ValueError):
        make_synthetic_task(True)
    with pytest.raises(ValueError):
        make_synthetic_task(0, stocks=17)
    task = make_synthetic_task(0)
    result = score_discovery(["unknown:formula"], task["truth"])
    assert result["false_positive_ids"] == ["unknown:formula"]
    assert result["missed_sources"] == 1
