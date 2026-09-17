from __future__ import annotations

from quanta_agents.research_evaluation import (
    build_development_folds,
    build_final_fold,
    deflated_sharpe_probability,
    summarize_development_results,
)


def _spec() -> dict[str, object]:
    return {
        "train_start": "2020-01-01",
        "train_end": "2022-12-30",
        "validate_start": "2023-01-02",
        "validate_end": "2023-12-29",
        "backtest_start": "2024-01-02",
        "backtest_end": "2024-12-31",
        "development_folds": 3,
        "gap_trading_days": 10,
        "evaluation": {
            "min_sharpe_ratio": 0.5,
            "min_return_rate": 0.03,
            "max_drawdown": 0.2,
        },
    }


def _record(
    sharpe: float,
    *,
    passed: bool = True,
    annual_return: float = 0.1,
    drawdown: float = 0.1,
) -> dict[str, object]:
    return {
        "annual_return": annual_return,
        "sharpe": sharpe,
        "max_ddpercent": drawdown,
        "trade_count": 20,
        "sample_size": 80,
        "skew": 0.0,
        "kurtosis": 3.0,
        "passed": passed,
    }


def test_development_folds_never_use_final_period() -> None:
    folds = build_development_folds(_spec())

    assert len(folds) == 3
    assert folds[0].test_start == "2023-01-16"
    assert folds[-1].test_end == "2023-12-29"
    assert all(fold.test_end < "2024-01-02" for fold in folds)
    assert all(fold.period_kind == "development" for fold in folds)
    assert all(fold.seen_period is True for fold in folds)
    assert folds[0].train_end <= "2022-12-30"
    assert folds[1].train_end < folds[1].test_start


def test_final_fold_is_marked_unseen() -> None:
    fold = build_final_fold(_spec())

    assert fold.test_start == "2024-01-02"
    assert fold.test_end == "2024-12-31"
    assert fold.train_end == "2023-12-29"
    assert fold.period_kind == "final_test"
    assert fold.seen_period is False


def test_development_gap_uses_supplied_trading_dates() -> None:
    spec = _spec()
    spec["development_folds"] = 2
    spec["gap_trading_days"] = 2
    spec["min_development_fold_days"] = 2
    trading_dates = [
        "2023-01-03",
        "2023-01-04",
        "2023-01-10",
        "2023-01-11",
        "2023-01-20",
        "2023-01-30",
    ]

    folds = build_development_folds(spec, trading_dates=trading_dates)

    assert folds[0].test_start == "2023-01-10"
    assert folds[0].train_end == "2022-12-30"
    assert folds[1].test_start == "2023-01-20"
    assert folds[1].train_end == "2023-01-04"


def test_short_validation_period_reduces_fold_count() -> None:
    spec = _spec()
    spec["validate_end"] = "2023-02-10"
    spec["development_folds"] = 5
    spec["min_development_fold_days"] = 20

    folds = build_development_folds(spec)

    assert len(folds) == 1


def test_summary_rejects_a_bad_worst_fold_even_when_two_of_three_pass() -> None:
    records = [_record(1.0), _record(0.8), _record(-0.2, passed=False)]

    report = summarize_development_results(records, _spec())

    assert report["fold_pass_ratio"] == 2 / 3
    assert report["passed"] is False
    assert any("worst_fold_sharpe" in reason for reason in report["failure_reasons"])


def test_summary_includes_cost_and_delay_results() -> None:
    records = [_record(1.0), _record(0.9), _record(0.8)]
    cost_records = [_record(0.3), _record(0.2), _record(0.1)]
    delay_records = [_record(0.2), _record(-0.4), _record(-0.5)]

    report = summarize_development_results(
        records,
        _spec(),
        cost_stress_records=cost_records,
        delay_stress_records=delay_records,
    )

    assert report["cost_stress_passed"] is True
    assert report["delay_stress_passed"] is False
    assert report["passed"] is False


def test_summary_rejects_missing_required_stress_results() -> None:
    records = [_record(1.0), _record(0.9), _record(0.8)]

    report = summarize_development_results(records, _spec())

    assert report["cost_stress_complete"] is False
    assert report["delay_stress_complete"] is False
    assert report["passed"] is False


def test_summary_rejects_fold_that_loses_to_cash_comparison() -> None:
    records = [
        _record(1.0),
        _record(0.9),
        _record(0.8, annual_return=-0.01),
    ]

    report = summarize_development_results(records, _spec())

    assert report["cash_comparison_annual_return"] == 0.0
    assert report["beats_cash_in_all_folds"] is False
    assert report["passed"] is False
    assert any("cash comparison" in reason for reason in report["failure_reasons"])


def test_trial_adjusted_sharpe_probability_is_bounded() -> None:
    probability = deflated_sharpe_probability(
        1.2,
        [0.2, 0.4, 0.3, 0.5],
        252,
    )

    assert probability is not None
    assert 0.0 <= probability <= 1.0
