"""Independent, generated-only oracles for the unfrozen sixth-case kernel.

These fixtures are constructed as exact paired residual vectors; they do not
load market observations, account returns, or old research outputs.  Production
matrix/selector tests are appended after its public interface is fixed.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction as F
from copy import deepcopy
import math

import numpy as np
import pytest

from quanta_agents.meta_v3 import conditional_risk as subject


def paired_oracle(count=12, *, reorder=False):
    """60 rows, 36 common downside rows and up to 16 nonzero columns.

    S00..S09 have orthogonal two-row residuals; S10 and S11 share
    their first three directions.  Reordering S11's third same-market pair
    changes dependence but preserves its marginal multiset and market loading.
    """
    assert 10 <= count <= 16
    market = [F(v, 100) for v in [-3, -3, -2, -2, -1, -1] * 6 + [1, 2, 3, 4] * 6]
    directions = []
    for position in range(10):
        directions.append([int(j == position) for j in range(18)])
    directions.extend([
        [int(j < 3) for j in range(18)],
        [-1 if j == 0 or (reorder and j == 2) else int(j < 3) for j in range(18)],
    ])
    for position in range(10, 14):
        directions.append([int(j == position) for j in range(18)])
    columns, residuals = {}, {}
    for index, direction in enumerate(directions[:count]):
        code = f"S{index:02}"
        paired = [F(sign * value, 1000) for value in direction for sign in (1, -1)]
        residuals[code] = paired
        columns[code] = [F(1, 500) + F(3, 5) * m + u for m, u in zip(market, paired + [F(0)] * 24)]
        assert sum(paired) == 0
        assert sum((u * m for u, m in zip(paired, market)), F(0)) == 0
    return market, columns, residuals


def exact_gram(residuals):
    """Normalize exact hand-constructed vectors using 80-digit arithmetic."""
    with localcontext() as context:
        context.prec = 80
        norm2 = {code: sum((v * v for v in values), F(0)) for code, values in residuals.items()}
        def decimal(value):
            return Decimal(value.numerator) / Decimal(value.denominator)
        return {
            left: {
                right: float(decimal(sum((x * y for x, y in zip(lv, rv)), F(0)))
                             / decimal(norm2[left] * norm2[right]).sqrt())
                for right, rv in residuals.items()
            }
            for left, lv in residuals.items()
        }


def test_generated_fixture_pair_reorder_preserves_marginals_and_loading():
    market, before, residuals = paired_oracle()
    after_market, after, changed_residuals = paired_oracle(reorder=True)
    assert market == after_market
    for code in before:
        assert sorted(before[code]) == sorted(after[code])
        assert sum((m * r for m, r in zip(market, before[code])), F(0)) == sum(
            (m * r for m, r in zip(market, after[code])), F(0))
    assert exact_gram(residuals)["S10"]["S11"] == 1 / 3
    assert exact_gram(changed_residuals)["S10"]["S11"] == -1 / 3


def evaluate(market, columns, **kwargs):
    return subject.evaluate_window(
        [float(value) for value in market],
        {code: [float(value) for value in values] for code, values in columns.items()},
        eligible={code: True for code in columns},
        **kwargs,
    )


def assert_matrix_matches(matrix, expected, *, atol=5e-12):
    assert set(matrix) == set(expected)
    for left in expected:
        assert set(matrix[left]) == set(expected[left])
        for right in expected[left]:
            assert matrix[left][right] == pytest.approx(expected[left][right], rel=0, abs=atol)


@pytest.mark.parametrize("count", [10, 12, 16])
def test_full_matrix_matches_independent_exact_gram_and_is_psd(count):
    market, columns, residuals = paired_oracle(count)
    result = evaluate(market, columns)
    assert result["status"] == "ready"
    assert_matrix_matches(result["matrix"], exact_gram(residuals))
    order = sorted(residuals)
    matrix = np.array([[result["matrix"][left][right] for right in order] for left in order])
    assert np.max(np.abs(matrix - matrix.T)) <= 2e-14
    assert np.max(np.abs(matrix.diagonal() - 1)) <= 2e-14
    assert np.linalg.eigvalsh(matrix).min() >= -2e-12
    assert len(result["selected"]) == 10
    assert len(set(result["selected"])) == 10


@pytest.mark.parametrize("reorder,expected,energy", [
    (False, ["S00", "S11", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S01"], F(24, 10**6)),
    (True, ["S00", "S11", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09"], F(16, 10**6)),
])
def test_selector_has_hand_derived_ten_stock_sequence_and_risk(reorder, expected, energy):
    market, columns, _ = paired_oracle(reorder=reorder)
    result = evaluate(market, columns)
    assert result["selected"] == expected
    assert result["status"] == "ready"
    weights = {code: Decimal(value) for code, value in result["target_weights"].items()}
    assert weights == {code: Decimal("0.08") for code in expected}
    assert Decimal(result["target_gross_weight"]) == Decimal("0.8")
    mean_pair = -2 / (45 * math.sqrt(3)) if reorder else 0.0
    assert result["risk"]["mean_pair_correlation"] == pytest.approx(mean_pair, abs=1e-13)
    assert result["risk"]["standardized_equal_variance"] == pytest.approx(0.1 + 0.9 * mean_pair, abs=1e-13)
    variance = float(energy * F(8, 100)**2 / 35)
    assert result["risk"]["target_residual_variance"] == pytest.approx(variance, rel=1e-11, abs=1e-20)
    assert (result["risk"]["diagonal_residual_variance"] + result["risk"]["off_diagonal_residual_variance"]) == pytest.approx(variance, rel=1e-11, abs=1e-20)


def test_same_market_pair_reordering_changes_the_actual_selected_set():
    market, before, _ = paired_oracle()
    after_market, after, _ = paired_oracle(reorder=True)
    left, right = evaluate(market, before), evaluate(after_market, after)
    assert set(left["selected"]) - set(right["selected"]) == {"S01"}
    assert set(right["selected"]) - set(left["selected"]) == {"S02"}


@pytest.mark.parametrize("count", [12, 16])
def test_column_order_cannot_change_tie_breaks_or_outputs(count):
    market, columns, _ = paired_oracle(count)
    forward = evaluate(market, columns)
    backward = evaluate(market, dict(reversed(list(columns.items()))))
    for key in ("symbols", "estimable_symbols", "excluded", "matrix", "selected", "target_weights", "risk", "work_units"):
        assert forward[key] == backward[key]


def test_d_only_distinct_affine_transform_preserves_matrix_and_selected_set():
    market, columns, residuals = paired_oracle(16)
    changed = {}
    for index, (code, values) in enumerate(columns.items()):
        a, b, scale = F(index - 4, 500), F(3 - index, 7), F(index + 1, 8)
        changed[code] = [a + b * m + scale * r if m < 0 else r for m, r in zip(market, values)]
    baseline, transformed = evaluate(market, columns), evaluate(market, changed)
    assert transformed["status"] == "ready"
    assert_matrix_matches(transformed["matrix"], exact_gram(residuals), atol=8e-12)
    assert transformed["selected"] == baseline["selected"]


@pytest.mark.parametrize("scale", [F(1, 10**120), F(10**120)])
def test_positive_scaling_across_orders_of_magnitude_has_no_absolute_epsilon(scale):
    market, columns, residuals = paired_oracle()
    scaled = {code: [scale * value for value in values] for code, values in columns.items()}
    baseline, changed = evaluate(market, columns), evaluate(market, scaled)
    assert changed["status"] == "ready"
    assert_matrix_matches(changed["matrix"], exact_gram(residuals))
    assert changed["selected"] == baseline["selected"]
    assert math.isfinite(changed["risk"]["target_residual_variance"])


def test_floating_pure_linear_column_is_excluded_with_reason_without_poisoning_other_eleven():
    market, columns, _ = paired_oracle()
    columns["S10"] = [F(1, 500) + F(3, 5) * value for value in market]
    result = evaluate(market, columns)
    assert result["status"] == "ready"
    assert len(result["estimable_symbols"]) == 11
    assert "S10" not in result["matrix"]
    reasons = {row["symbol"]: row["reason"] for row in result["excluded"]}
    assert "residual" in reasons["S10"]
    assert "S10" not in result["selected"]


@pytest.mark.parametrize("amplitude,estimable", [(F(1, 10**15), False), (F(1, 10**8), True)])
def test_near_linear_columns_respect_scale_aware_numerical_zero(amplitude, estimable):
    market, columns, residuals = paired_oracle()
    # One exactly known direction on top of a much larger affine component.
    columns["S10"] = [F(1, 500) + F(3, 5) * m + amplitude * (residuals["S00"][index] * 1000 if index < 36 else 0)
                      for index, m in enumerate(market)]
    result = evaluate(market, columns)
    assert result["status"] == "ready"
    assert ("S10" in result["estimable_symbols"]) is estimable
    if estimable:
        assert result["matrix"]["S10"]["S00"] == pytest.approx(1, abs=2e-10)
        assert result["matrix"]["S10"]["S01"] == pytest.approx(0, abs=2e-10)
    else:
        assert any(row["symbol"] == "S10" and "residual" in row["reason"] for row in result["excluded"])


def test_nine_estimable_columns_keep_original_decision_with_cash_target():
    market, columns, _ = paired_oracle()
    for code in ("S09", "S10", "S11"):
        columns[code] = [F(1, 500) + F(3, 5) * value for value in market]
    result = evaluate(market, columns)
    assert result["status"] == "target_cash"
    assert len(result["estimable_symbols"]) == 9
    assert {row["symbol"] for row in result["excluded"]} == {"S09", "S10", "S11"}
    assert result["selected"] == []
    assert result["target_weights"] == {}
    assert Decimal(result["target_gross_weight"]) == 0


@pytest.mark.parametrize("missing", [None, math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("row", [0, 59])
def test_any_common_window_gap_goes_to_cash_even_outside_downside_rows(missing, row):
    market, columns, _ = paired_oracle()
    returns = {code: list(map(float, values)) for code, values in columns.items()}
    returns["S11"][row] = missing
    result = subject.evaluate_window(list(map(float, market)), returns, eligible={code: True for code in columns})
    assert result["status"] == "target_cash"
    assert result["selected"] == []
    assert result["target_weights"] == {}
    assert result["reason"]


def test_unknown_eligibility_is_not_treated_as_known_ineligibility():
    market, columns, _ = paired_oracle()
    eligible = {code: True for code in columns}
    eligible["S11"] = None
    result = subject.evaluate_window(list(map(float, market)), {code: list(map(float, values)) for code, values in columns.items()}, eligible=eligible)
    assert result["status"] == "target_cash"
    assert result["selected"] == []
    assert result["reason"]


def test_known_ineligibility_does_not_hide_missing_common_source_input():
    market, columns, _ = paired_oracle()
    eligible = {code: code != "S11" for code in columns}
    returns = {code: list(map(float, values)) for code, values in columns.items()}
    returns["S11"][59] = None
    result = subject.evaluate_window(list(map(float, market)), returns, eligible=eligible)
    assert result["status"] == "target_cash"
    assert result["selected"] == []
    assert result["reason"]


def test_known_ineligibility_is_retained_and_cannot_be_replaced_to_fill_ten():
    market, columns, _ = paired_oracle()
    eligible = {code: code not in {"S09", "S10", "S11"} for code in columns}
    result = subject.evaluate_window(list(map(float, market)), {code: list(map(float, values)) for code, values in columns.items()}, eligible=eligible)
    assert result["status"] == "target_cash"
    assert len(result["estimable_symbols"]) == 9
    assert result["selected"] == []
    assert {row["symbol"] for row in result["excluded"]} == {"S09", "S10", "S11"}


@pytest.mark.parametrize("downside,expected_status", [(19, "target_cash"), (20, "ready")])
def test_minimum_common_downside_count_is_fixed_and_inclusive(downside, expected_status):
    market, columns, _ = paired_oracle()
    market = [value if index < downside else abs(value) for index, value in enumerate(market)]
    result = evaluate(market, columns)
    assert result["status"] == expected_status


def test_zero_downside_market_variance_is_a_common_cash_decision():
    _, columns, _ = paired_oracle()
    market = [F(-1, 100)] * 36 + [F(1, 100)] * 24
    result = evaluate(market, columns)
    assert result["status"] == "target_cash"
    assert result["selected"] == []
    assert result["reason"]


def test_original_single_name_cap_retains_cash_without_renormalization():
    market, columns, _ = paired_oracle()
    baseline = evaluate(market, columns)
    capped = evaluate(market, columns, single_name_cap="0.03")
    assert capped["status"] == "ready"
    assert capped["selected"] == baseline["selected"]
    assert {Decimal(value) for value in capped["target_weights"].values()} == {Decimal("0.03")}
    assert Decimal(capped["target_gross_weight"]) == Decimal("0.3")
    assert capped["risk"]["target_residual_variance"] == pytest.approx(baseline["risk"]["target_residual_variance"] * (0.03 / 0.08)**2, rel=1e-12)


def test_reported_spectral_concentration_matches_independent_eigendecomposition():
    market, columns, _ = paired_oracle()
    result = evaluate(market, columns)
    selected = result["selected"]
    matrix = np.array([[result["matrix"][left][right] for right in selected] for left in selected])
    expected = float(np.linalg.eigvalsh(matrix)[-1]) / len(selected)
    assert result["risk"]["largest_correlation_share"] == pytest.approx(expected, abs=1e-10)


def test_evaluation_is_repeatable_and_does_not_mutate_the_shared_input_snapshot():
    market, columns, _ = paired_oracle()
    values = list(map(float, market))
    returns = {code: list(map(float, entries)) for code, entries in columns.items()}
    eligible = {code: True for code in columns}
    snapshot = deepcopy((values, returns, eligible))
    first = subject.evaluate_window(values, returns, eligible=eligible)
    assert (values, returns, eligible) == snapshot
    second = subject.evaluate_window(values, returns, eligible=eligible)
    assert first == second
    assert (values, returns, eligible) == snapshot


@pytest.mark.parametrize("cap", ["1e-1000", "1e-1000000", "0.0000000000001", "0." + "0" * 24 + "1"])
def test_cap_precision_and_text_bounds_reject_underflowing_or_unbounded_weights(cap):
    market, columns, _ = paired_oracle()
    with pytest.raises(ValueError, match="cap"):
        evaluate(market, columns, single_name_cap=cap)


@pytest.mark.parametrize("scale", [F(1, 10**170), F(1, 10**300)])
def test_nonzero_residual_variance_underflow_cannot_be_reported_as_zero_risk(scale):
    market, columns, _ = paired_oracle()
    scaled = {code: [scale * value for value in values] for code, values in columns.items()}
    result = evaluate(market, scaled)
    assert result["status"] == "target_cash"
    assert result["reason"] == "target_residual_variance_numeric_underflow"
    assert len(result["estimable_symbols"]) == 12
    assert result["selected"] == []
    assert result["target_weights"] == {}
    assert result["risk"] is None


def test_nonzero_decimal_observation_lost_during_float_conversion_is_common_unknown():
    market, columns, _ = paired_oracle()
    returns = {code: list(map(float, values)) for code, values in columns.items()}
    returns["S11"][59] = Decimal("1e-1000")
    result = subject.evaluate_window(list(map(float, market)), returns, eligible={code: True for code in columns})
    assert result["status"] == "target_cash"
    assert result["reason"] == "common_window_missing_or_nonfinite"
    assert result["selected"] == []


def test_zero_weight_cap_is_distinguished_from_numeric_underflow():
    market, columns, _ = paired_oracle()
    result = evaluate(market, columns, single_name_cap="0")
    assert result["status"] == "ready"
    assert Decimal(result["target_gross_weight"]) == 0
    assert all(Decimal(value) == 0 for value in result["target_weights"].values())
    assert result["risk"]["target_residual_variance"] == 0


def test_mutated_public_policy_cannot_change_accepted_fixed_policy(monkeypatch):
    market, columns, _ = paired_oracle()
    baseline = evaluate(market, columns)
    monkeypatch.setitem(subject.POLICY, "selection_count", 9)
    assert evaluate(market, columns) == baseline
    with pytest.raises(ValueError, match="policy"):
        evaluate(market, columns, policy=subject.POLICY)


def test_original_sixteen_symbol_resource_limit_cannot_be_raised_by_policy():
    market, columns, _ = paired_oracle(16)
    columns["S16"] = list(columns["S00"])
    with pytest.raises(ValueError, match="symbol count"):
        evaluate(market, columns)
    changed_policy = dict(subject.POLICY, max_symbols=17)
    with pytest.raises(ValueError, match="policy"):
        evaluate(market, columns, policy=changed_policy)


@pytest.mark.parametrize("epsilon,expected", [(0.0, "ready"), (1e-163, "target_cash")])
def test_exact_zero_portfolio_is_distinct_from_underflow_after_near_cancellation(epsilon, expected):
    market, _, _ = paired_oracle()
    columns = {}
    for index in range(5):
        positive, negative = [0.0] * 60, [0.0] * 60
        positive[2 * index], positive[2 * index + 1] = 1e-153, -1e-153
        negative[2 * index], negative[2 * index + 1] = -1e-153, 1e-153
        negative[2 * (index + 5)], negative[2 * (index + 5) + 1] = epsilon, -epsilon
        columns[f"S{2 * index:02}"] = positive
        columns[f"S{2 * index + 1:02}"] = negative
    # Every individual weighted variance is representable. The ten stocks must
    # all be selected; the remaining portfolio variance is positive iff eps>0.
    result = evaluate(market, columns)
    assert result["status"] == expected
    if epsilon:
        assert result["reason"] == "portfolio_residual_variance_numeric_underflow"
        assert result["risk"] is None
        assert result["selected"] == []
    else:
        assert len(result["selected"]) == 10
        assert result["risk"]["target_residual_variance"] == 0
        assert result["risk"]["diagonal_residual_variance"] > 0
