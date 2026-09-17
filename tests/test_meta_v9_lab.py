"""Generated panels exercise temporal isolation, real account flow and recovery."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v7 import combination_lab as lab


def fixture():
    rng = np.random.default_rng(909)
    dates = pd.bdate_range("2017-01-02", periods=330)
    columns = [f"sh{600000+i}" for i in range(12)]
    a = np.tile(np.linspace(-1, 1, 12), (330, 1)) + rng.normal(0, .08, (330, 12))
    b = rng.normal(size=a.shape)
    steps = .001 * a + .0003 * b + rng.normal(0, .0003, a.shape)
    close = pd.DataFrame(20 * np.exp(np.cumsum(steps, axis=0)), index=dates, columns=columns)
    opening = close.shift(1).fillna(close.iloc[0])
    fields = {"open": opening, "close": close, "high": np.maximum(opening, close) * 1.001,
        "low": np.minimum(opening, close) * .999, "raw_open": opening.copy(),
        "raw_prev_close": opening.copy(), "adjustment_factor": close * 0 + 1,
        "volume": close * 0 + 1e6, "amount": close * 0 + 1e8,
        "is_st": close * 0, "is_delisting": close * 0, "open_observed": close * 0 + 1}
    panel = MarketPanel(fields, close.notna(), {"kind": "generated_v9_workflow_only"})
    frames = {"A": pd.DataFrame(a, index=dates, columns=columns),
              "B": pd.DataFrame(b, index=dates, columns=columns)}
    day = lambda index: str(dates[index].date())
    args = {"train_start": day(125), "train_end": day(280),
        "folds": [{"fit_end": day(220), "validation_start": day(221), "validation_end": day(250)}],
        "selection": {"min_ic_days": 30, "min_annual_days": 10,
                      "min_stable_year_fraction": 0., "max_abs_correlation": .99},
        "allocation": {"top_n": 4, "max_stock_weight": .25},
        "return_candidate_ids": ["A"], "interaction_pairs": [("A", "B")]}
    return panel, frames, args


def test_real_generated_accounts_have_explicit_five_arm_denominator_and_raw_reuse(tmp_path):
    panel, frames, args = fixture()
    calls, events = [], []
    result = lab.evaluate_combination_lab(panel, frames, **args, artifact_dir=tmp_path,
        before_account=lambda phase, identity: calls.append((phase, identity)), on_event=events.append)
    assert result["status"] == "completed", result["folds"]
    assert len(calls) == 5
    assert result["account_denominator"]["declared"] == 5
    assert result["account_denominator"]["completed"] == 5
    assert set(result["final_strategy_specs"]) == {"equal_rank", "ridge", "ridge_augmented", "ridge_interactions"}
    assert result["selected_method"] is None
    assert result["fold_results_used_for_final_fit"] is False
    assert result["folds"][0]["fit"]["configuration"]["return_candidate_ids"] == ["A"]
    assert result["folds"][0]["interaction_control"]["exact_calendar_alignment"]
    assert all(row["metrics"]["sharpe"]["available_folds"] == 1 for row in result["methods"].values())
    for method in [*result["methods"], "equal_pool_benchmark"]:
        folder = tmp_path / "fold_00" / method
        assert all((folder / (name + ".parquet")).exists() for name in ("daily", "trades", "annual", "targets"))
        assert (folder / "frozen.json").exists()
    assert any(event["event"] == "fold_completed" for event in events)
    finished = [event for event in events if event["event"] == "account_finished"]
    assert len(finished) == 5 and all(event["status"] == "completed" for event in finished)
    json.dumps(result, allow_nan=False)
    second = lab.evaluate_combination_lab(panel, frames, **args, artifact_dir=tmp_path,
        before_account=lambda *_: pytest.fail("verified successful reuse must not reserve a new account"))
    assert second["account_denominator"]["reused_successes"] == 5
    assert second["final_fit"] == result["final_fit"]


@pytest.mark.parametrize("kind", ["overlap_fit", "after_train", "overlap_folds", "reverse_fits", "empty_fold"])
def test_invalid_fold_contract_stops_before_fitting_or_budget_reservation(monkeypatch, kind):
    panel, frames, args = fixture()
    fold = args["folds"][0]
    if kind == "overlap_fit":
        fold["fit_end"] = fold["validation_start"]
    elif kind == "after_train":
        fold["validation_end"] = str(panel.dates[300].date())
    elif kind == "empty_fold":
        args["folds"] = []
    else:
        new = deepcopy(fold)
        if kind == "reverse_fits":
            new.update(fit_end=str(panel.dates[210].date()), validation_start=str(panel.dates[251].date()),
                       validation_end=str(panel.dates[270].date()))
        args["folds"].append(new)
    monkeypatch.setattr(lab, "_fit", lambda *_: pytest.fail("invalid folds must be checked before fit"))
    with pytest.raises(ValueError):
        lab.evaluate_combination_lab(panel, frames, **args,
            before_account=lambda *_: pytest.fail("invalid folds must not reserve account"))


def test_future_numeric_poison_cannot_change_fits_or_account_summary():
    panel, frames, args = fixture()
    baseline = lab.evaluate_combination_lab(panel, frames, **args)
    changed = deepcopy(panel)
    for key, value in changed.fields.items():
        changed.fields[key] = value.astype(object)
        changed.fields[key].iloc[281:] = "forbidden future data"
    future = {name: value.astype(object) for name, value in frames.items()}
    for value in future.values():
        value.iloc[281:] = "forbidden future factor"
    actual = lab.evaluate_combination_lab(changed, future, **args)
    assert actual["final_fit"] == baseline["final_fit"]
    assert actual["folds"][0]["fit"] == baseline["folds"][0]["fit"]
    assert actual["methods"] == baseline["methods"]


def test_fold_validation_labels_do_not_change_prior_fit():
    panel, frames, args = fixture()
    baseline = lab.evaluate_combination_lab(panel, frames, **args)
    changed = deepcopy(panel)
    # Unseen fold prices alter accounts/final fit, but cannot alter the earlier fit.
    changed.fields["open"].iloc[221:] *= 1.01
    changed.fields["raw_open"].iloc[221:] *= 1.01
    actual = lab.evaluate_combination_lab(changed, frames, **args)
    assert actual["folds"][0]["fit"] == baseline["folds"][0]["fit"]
    assert actual["final_fit"] != baseline["final_fit"]


def test_budget_refusals_are_failed_unknown_accounts_and_not_implicit_retries(tmp_path):
    panel, frames, args = fixture()
    calls = []
    def refuse(phase, identity):
        calls.append(identity)
        raise RuntimeError("frozen total execution budget exhausted")
    result = lab.evaluate_combination_lab(panel, frames, **args, artifact_dir=tmp_path, before_account=refuse)
    assert len(calls) == 5
    assert result["account_denominator"]["failed_or_unavailable"] == 5
    assert result["final_fit_status"] == "fitted"
    assert all(row["summary"] is None for row in result["folds"][0]["accounts"].values())
    assert all(row["metrics"]["return"]["arithmetic_mean_across_separate_accounts"] is None
               for row in result["methods"].values())
    assert all(row["status"] == "not_evaluable" for row in result["folds"][0]["attribution"].values())
    again = lab.evaluate_combination_lab(panel, frames, **args, artifact_dir=tmp_path,
        before_account=lambda *_: pytest.fail("prior failures require explicit new attempt directory"))
    assert again["account_denominator"]["completed"] == 0


def test_corrupted_success_is_rejected_before_new_account_budget(tmp_path):
    panel, frames, args = fixture()
    lab.evaluate_combination_lab(panel, frames, **args, artifact_dir=tmp_path)
    raw = tmp_path / "fold_00" / "equal_rank" / "daily.parquet"
    with raw.open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="hash differs"):
        lab.evaluate_combination_lab(panel, frames, **args, artifact_dir=tmp_path,
            before_account=lambda *_: pytest.fail("corrupted artifact must not cause automatic retry"))


def test_no_supported_fit_still_preserves_benchmark_and_full_method_denominator():
    panel, frames, args = fixture()
    for value in frames.values():
        value.iloc[:] = np.nan
    result = lab.evaluate_combination_lab(panel, frames, **args)
    assert result["status"] == "completed_with_failures"
    assert result["final_fit_status"] == "failed"
    assert result["final_strategy_specs"] == {}
    assert result["account_denominator"]["declared"] == 5
    assert result["account_denominator"]["completed"] == 1
    assert "fit_error" in result["folds"][0]
    assert all(result["folds"][0]["accounts"][method]["status"] == "not_run_fit_failed" for method in result["methods"])


def test_pairs_omitted_produce_two_methods_and_benchmark_without_synthetic_extra_arm():
    panel, frames, args = fixture()
    args["interaction_pairs"] = None
    result = lab.evaluate_combination_lab(panel, frames, **args)
    assert set(result["methods"]) == {"equal_rank", "ridge"}
    assert result["account_denominator"]["declared"] == 3
    assert result["account_denominator"]["completed"] == 3


def test_expanding_folds_do_not_change_final_fit_and_keep_separate_account_capital():
    panel, frames, args = fixture()
    args["interaction_pairs"] = None
    one = lab.evaluate_combination_lab(panel, frames, **args)
    args["folds"].append({"fit_end": str(panel.dates[250].date()),
        "validation_start": str(panel.dates[251].date()), "validation_end": str(panel.dates[270].date())})
    two = lab.evaluate_combination_lab(panel, frames, **args)
    assert two["account_denominator"]["declared"] == 6
    assert two["account_denominator"]["completed"] == 6
    assert two["final_fit"] == one["final_fit"]
    assert two["final_strategy_specs"] == one["final_strategy_specs"]
    for method, row in two["methods"].items():
        values = [fold["accounts"][method]["summary"]["return"] for fold in two["folds"]]
        assert row["metrics"]["return"]["arithmetic_mean_across_separate_accounts"] == pytest.approx(np.mean(values))
        assert row["metrics"]["return"]["available_folds"] == 2
        assert not row["continuous_equity_curve_created"]


def test_supported_pairs_can_run_when_no_base_return_candidate_is_admitted():
    panel, frames, args = fixture()
    args["return_candidate_ids"] = []
    calls = []
    result = lab.evaluate_combination_lab(panel, frames, **args,
        before_account=lambda phase, identity: calls.append(phase))
    assert set(result["final_strategy_specs"]) == {"ridge_augmented", "ridge_interactions"}
    assert result["account_denominator"]["declared"] == 5
    assert result["account_denominator"]["completed"] == 3
    assert len(calls) == 3
    for method in ("equal_rank", "ridge"):
        record = result["folds"][0]["accounts"][method]
        assert record["status"] == "not_run_model_unavailable"
        assert record["model_status"]["status"] == "unavailable"
        assert record["summary"] is None
    assert result["folds"][0]["interaction_control"]["exact_calendar_alignment"]
