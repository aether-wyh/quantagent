from __future__ import annotations

import math

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quanta_agents.daily_research import (
    horizon_response,
    parameter_response,
    rule_removal,
    signal_increment,
)


def test_parameter_response_reports_thresholds_bands_years_and_daily_weighting() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": [
                "2020-01-02",
                "2020-01-02",
                "2021-01-04",
                "2021-01-05",
            ],
            "code": ["A", "B", "C", "D"],
            "future_return": [0.10, 0.30, -0.10, 0.50],
            "feature": [0.10, 0.20, 0.30, 0.40],
            "keep": [True, True, True, False],
        }
    )
    original = frame.copy(deep=True)

    report = parameter_response(
        frame,
        feature_column="feature",
        thresholds=[0.30, 0.20, 0.30],
        operator="<=",
        rule_columns=["keep"],
        current_value=0.30,
    )

    assert report["threshold_order"] == [0.2, 0.3]
    assert report["return_handling"] == "aggregate_provided_column_only"
    assert report["group_order"] == ["feature<=0.2", "feature<=0.3"]
    assert report["strictness_order"] == report["group_order"]
    assert report["band_order"] == ["(-inf,0.2]", "(0.2,0.3]", "(0.3,inf)"]

    first = report["groups"][0]["summary"]
    assert first["sample_count"] == 2
    assert first["mean_return"] == pytest.approx(0.20)
    assert first["daily_equal_weight_mean"] == pytest.approx(0.20)
    assert first["year_order"] == ["2020"]

    second = report["groups"][1]["summary"]
    assert second["sample_count"] == 3
    assert second["mean_return"] == pytest.approx(0.10)
    # 2020 信号日均值为 0.20，2021 信号日均值为 -0.10；两个日期等权。
    assert second["daily_equal_weight_mean"] == pytest.approx(0.05)
    assert second["year_order"] == ["2020", "2021"]
    assert [row["year"] for row in second["yearly"]] == ["2020", "2021"]

    assert report["bands"][0]["summary"]["sample_count"] == 2
    assert report["bands"][1]["summary"]["sample_count"] == 1
    assert report["bands"][2]["summary"]["sample_count"] == 0
    assert_frame_equal(frame, original)


def test_parameter_response_reports_invalid_future_returns_without_calculating_them() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04", "2022-01-05", "2022-01-06"],
            "code": ["A", "B", "C"],
            "future_return": [0.1, None, math.inf],
            "feature": [1.0, 1.0, 1.0],
        }
    )

    report = parameter_response(
        frame,
        feature_column="feature",
        thresholds=[1.0],
    )

    summary = report["groups"][0]["summary"]
    assert summary["selected_row_count"] == 3
    assert summary["sample_count"] == 1
    assert summary["invalid_return_count"] == 2
    assert summary["mean_return"] == pytest.approx(0.1)


def test_parameter_response_greater_operator_has_explicit_strictness_order() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04", "2022-01-05"],
            "code": ["A", "B"],
            "future_return": [0.1, 0.2],
            "feature": [1.0, 2.0],
        }
    )

    report = parameter_response(
        frame,
        feature_column="feature",
        thresholds=[1.0, 2.0],
        operator=">=",
    )

    assert report["group_order"] == ["feature>=1", "feature>=2"]
    assert report["strictness_order"] == ["feature>=2", "feature>=1"]


def test_rule_removal_keeps_eligibility_fixed_and_reports_new_samples() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04"] * 5,
            "code": ["A", "B", "C", "D", "E"],
            "future_return": [0.1, 0.2, -0.1, 0.8, 1.0],
            "eligible": [True, True, True, True, False],
            "rule_a": [True, True, False, False, True],
            "rule_b": [True, False, True, False, True],
        }
    )

    report = rule_removal(
        frame,
        rule_columns=["rule_a", "rule_b"],
        eligibility_column="eligible",
    )

    assert report["group_order"] == [
        "baseline",
        "without:rule_a",
        "without:rule_b",
    ]
    baseline, without_a, without_b = report["variants"]
    assert baseline["summary"]["sample_count"] == 1
    assert without_a["summary"]["sample_count"] == 2
    assert without_a["newly_included_summary"]["sample_count"] == 1
    assert without_a["newly_included_summary"]["mean_return"] == pytest.approx(-0.1)
    assert without_b["summary"]["sample_count"] == 2
    assert without_b["newly_included_summary"]["mean_return"] == pytest.approx(0.2)
    # E 不符合固定资格，删除任何策略规则都不能把它放进来。
    assert all(variant["summary"]["sample_count"] < 3 for variant in report["variants"])


def test_signal_increment_compares_baseline_new_intersection_and_replacement() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04"] * 5,
            "code": ["A", "B", "C", "D", "E"],
            "future_return": [0.1, -0.2, 0.3, 0.4, 0.5],
            "rule_a": [True, True, True, False, False],
            "rule_b": [True, True, False, True, False],
            "new_signal": [True, False, True, True, False],
        }
    )

    report = signal_increment(
        frame,
        base_rule_columns=["rule_a", "rule_b"],
        new_signal_column="new_signal",
        replace_rule_column="rule_b",
    )

    assert report["group_order"] == [
        "baseline",
        "new_signal_only",
        "baseline_plus_new",
        "replace:rule_b:with:new_signal",
    ]
    counts = [row["summary"]["sample_count"] for row in report["variants"]]
    assert counts == [2, 3, 1, 2]
    assert report["partition_order"] == [
        "baseline_passes_new",
        "baseline_fails_new",
        "new_outside_baseline",
    ]
    partition_counts = [
        row["summary"]["sample_count"] for row in report["partitions"]
    ]
    assert partition_counts == [1, 1, 2]
    assert report["baseline_retention_rate"] == pytest.approx(0.5)


def test_horizon_response_preserves_requested_order_and_uses_common_sample() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": [
                "2021-01-04",
                "2021-01-04",
                "2021-01-04",
                "2021-01-04",
                "2021-01-05",
                "2021-01-05",
            ],
            "code": ["A", "A", "B", "B", "C", "C"],
            "horizon_days": [1, 3, 1, 3, 1, 3],
            "future_return": [0.1, 0.3, -0.1, 0.1, 0.2, None],
            "base_rule": [True] * 6,
        }
    )

    report = horizon_response(
        frame,
        horizons=[3, 1],
        rule_columns=["base_rule"],
    )

    assert report["group_order"] == [3, 1]
    horizon_three, horizon_one = report["groups"]
    assert horizon_three["summary"]["selected_row_count"] == 3
    assert horizon_three["summary"]["sample_count"] == 2
    assert horizon_three["summary"]["daily_equal_weight_mean"] == pytest.approx(0.2)
    assert horizon_three["valid_coverage_rate"] == pytest.approx(2 / 3)
    assert horizon_one["summary"]["sample_count"] == 3
    # 1日：首日 A/B 等权为0，次日 C 为0.2；两个信号日再等权为0.1。
    assert horizon_one["summary"]["daily_equal_weight_mean"] == pytest.approx(0.1)
    assert report["union_signal_count"] == 3

    assert report["common_signal_count"] == 2
    common_counts = [
        row["summary"]["sample_count"] for row in report["common_groups"]
    ]
    assert common_counts == [2, 2]
    assert report["common_groups"][0]["summary"]["mean_return"] == pytest.approx(0.2)
    assert report["common_groups"][1]["summary"]["mean_return"] == pytest.approx(0.0)


def test_horizon_response_rejects_duplicate_signal_horizon_rows() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04", "2022-01-04"],
            "code": ["A", "A"],
            "horizon_days": [1, 1],
            "future_return": [0.1, 0.2],
        }
    )

    with pytest.raises(ValueError, match="只能有一行"):
        horizon_response(frame)


def test_rule_columns_reject_text_truth_values() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04"],
            "code": ["A"],
            "future_return": [0.1],
            "rule_a": ["yes"],
        }
    )

    with pytest.raises(ValueError, match="布尔值或 0/1"):
        rule_removal(frame, rule_columns=["rule_a"])


def test_missing_required_column_is_reported() -> None:
    frame = pd.DataFrame(
        {
            "decision_date": ["2022-01-04"],
            "code": ["A"],
            "future_return": [0.1],
        }
    )

    with pytest.raises(ValueError, match="feature"):
        parameter_response(
            frame,
            feature_column="feature",
            thresholds=[1.0],
        )
