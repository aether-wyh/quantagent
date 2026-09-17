from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quanta_agents.meta.factor_algebra import (
    MAX_DEPTH, MAX_EXPRESSION_LENGTH, evaluate_expression, expression_guide, validate_expression,
)


@pytest.fixture
def fields():
    index = pd.date_range("2020-01-01", periods=140, name="date")
    columns = pd.Index(["600001", "000001", "300001"], name="stock")
    values = np.arange(1, 421, dtype=float).reshape(140, 3)
    return {"close": pd.DataFrame(values, index=index, columns=columns),
            "volume": pd.DataFrame(values[::-1].copy(), index=index, columns=columns)}


def test_rank_universe_excludes_future_members_without_discarding_single_stock_history(fields):
    mask = fields['close'].notna()
    mask.iloc[:, 2] = False
    mask.iloc[:70, 0] = False
    expression = 'cs_rank(rolling_mean(close, 3))'
    result = evaluate_expression(expression, fields, rank_universe=mask)
    changed = {k: v.copy() for k, v in fields.items()}
    changed['close'].iloc[:, 2] *= -1_000_000
    after = evaluate_expression(expression, changed, rank_universe=mask)
    assert_frame_equal(result, after)
    assert result.iloc[:, 2].isna().all()
    assert pd.notna(result.iloc[70, 0])  # historical observations survive outside rank universe
    with pytest.raises(ValueError, match='coordinates'):
        evaluate_expression('cs_rank(close)', fields, rank_universe=mask.iloc[1:])


def test_nested_factors_preserve_axes_and_do_not_mutate_inputs(fields):
    original = {key: value.copy(deep=True) for key, value in fields.items()}
    result = evaluate_expression(
        "where((close > lag(close, 2)) & (cs_rank(volume) > 0.4), "
        "clip(log(close / rolling_mean(close, 7)), -0.5, 0.5), 0)", fields)
    assert result.index.equals(fields["close"].index)
    assert result.columns.equals(fields["close"].columns)
    for key in fields:
        assert_frame_equal(fields[key], original[key])
    bare = evaluate_expression("close", fields)
    bare.iloc[0, 0] = -999
    assert_frame_equal(fields["close"], original["close"])


@pytest.mark.parametrize("expression", [
    "lag(close, 3)", "pct_change(close, 7)", "rolling_mean(close, 11)",
    "rolling_std(close, 11)", "rolling_min(close, 11)", "rolling_max(close, 11)",
    "rolling_sum(close, 11)", "cs_rank(close)",
    "where((close > rolling_mean(close, 9)) and not (volume < lag(volume, 2)), "
    "cs_rank(abs(pct_change(close, 3))), 0)",
])
def test_future_row_perturbation_never_changes_earlier_output(fields, expression):
    before = evaluate_expression(expression, fields)
    modified = {key: value.copy() for key, value in fields.items()}
    for value in modified.values():
        value.iloc[81:] = -100_000 * value.iloc[81:]
    after = evaluate_expression(expression, modified)
    assert_frame_equal(before.iloc[:81], after.iloc[:81])


@pytest.mark.parametrize("expression", [
    "close.iloc[0]", "close.__class__", "close['x']", "__import__('os')",
    "open('secret')", "np.log(close)", "close.mean()", "mean(close)",
    "[x for x in close]", "(lambda: 1)()", "(x := close)", "{'x': close}",
    "lag(close, -1)", "lag(close, 0)", "rolling_mean(close, 1)",
    "rolling_mean(close, 121)", "lag(close, 121)", "pct_change(close, -3)",
    "lag(close, 2.0)", "lag(close, True)", "lag(close, 1 + 1)",
    "rolling_mean(close, window=2)", "rolling_mean(close, close)",
    "close ** 100000000", "close << 2", "close is close", "close in volume",
    "clip(close, volume, 1)", "clip(close, 2, 1)", "1e309", "'close'", "None",
    "unknown + close", "abs(close, 2)",
])
def test_invalid_or_injected_expressions_are_rejected(fields, expression):
    with pytest.raises(ValueError):
        validate_expression(expression, fields.keys())
    with pytest.raises(ValueError):
        evaluate_expression(expression, fields)


def test_resource_limits_are_enforced_before_execution(fields):
    for expression in [" " * (MAX_EXPRESSION_LENGTH + 1),
                       "abs(" * (MAX_DEPTH + 1) + "close" + ")" * (MAX_DEPTH + 1),
                       " + ".join(["close"] * 100)]:
        with pytest.raises(ValueError):
            evaluate_expression(expression, fields)


def test_rolling_and_lag_window_boundaries(fields):
    for window in (2, 120):
        result = evaluate_expression(f"rolling_mean(close, {window})", fields)
        assert_frame_equal(result, fields["close"].rolling(window, min_periods=window).mean())
        assert result.iloc[:window - 1].isna().all().all()
    for periods in (1, 120):
        assert_frame_equal(evaluate_expression(f"lag(close, {periods})", fields),
                           fields["close"].shift(periods))


def test_rolling_is_per_stock_and_rank_is_same_day_cross_section():
    frame = pd.DataFrame([[1., 100., 1.], [5., 10., 30.], [9., np.nan, 12.]],
                         index=pd.date_range("2021-01-01", periods=3), columns=["a", "b", "c"])
    data = {"x": frame}
    assert_frame_equal(evaluate_expression("rolling_std(x, 2)", data),
                       frame.rolling(2, min_periods=2).std(ddof=1))
    expected = pd.DataFrame([[0.5, 1., 0.5], [1 / 3, 2 / 3, 1.], [0.5, np.nan, 1.]],
                            index=frame.index, columns=frame.columns)
    assert_frame_equal(evaluate_expression("cs_rank(x)", data), expected)


def test_missing_and_invalid_values_are_not_filled_or_allowed_by_filters():
    frame = pd.DataFrame({"a": [1., np.nan, 3., 0., -1., np.inf]})
    data = {"x": frame}
    assert evaluate_expression("pct_change(x, 1)", data).iloc[2, 0] != 2.0
    assert evaluate_expression("pct_change(x, 1)", data).iloc[[0, 1, 2, 4, 5], 0].isna().all()
    assert evaluate_expression("log(x)", data).iloc[[1, 3, 4, 5], 0].isna().all()
    assert evaluate_expression("1 / x", data).iloc[[1, 3, 5], 0].isna().all()
    assert evaluate_expression("~(x > 0)", data).iloc[[1, 5], 0].isna().all()
    assert evaluate_expression("where(x > 0, 1, 0)", data).iloc[[1, 5], 0].isna().all()
    assert evaluate_expression("rolling_sum(x, 2)", data).iloc[:3, 0].isna().all()
    assert evaluate_expression("(x > 0) & False", data).eq(0).all().all()
    assert evaluate_expression("(x > 0) | True", data).eq(1).all().all()


def test_scalar_and_chained_comparison_semantics(fields):
    expected = ((fields["close"] > 10) & (fields["close"] < 20)).astype(float)
    assert_frame_equal(evaluate_expression("10 < close < 20", fields), expected)
    assert evaluate_expression("True", fields).eq(1).all().all()
    assert evaluate_expression("1 / 0", fields).isna().all().all()
    assert evaluate_expression("log(-1)", fields).isna().all().all()


def test_input_axis_and_type_contract_fails_closed(fields):
    with pytest.raises(ValueError, match="different index"):
        evaluate_expression("close", {**fields, "volume": fields["volume"].iloc[::-1]})
    with pytest.raises(ValueError, match="chronological"):
        evaluate_expression("close", {"close": fields["close"].iloc[::-1]})
    with pytest.raises(ValueError, match="unique"):
        evaluate_expression("close", {"close": pd.concat([fields["close"], fields["close"]])})
    with pytest.raises(ValueError, match="numeric"):
        evaluate_expression("close", {"close": fields["close"].astype(str)})
    with pytest.raises(ValueError, match="shadow"):
        evaluate_expression("abs", {"abs": fields["close"]})
    with pytest.raises(ValueError):
        evaluate_expression("1", {})


def test_guide_describes_missing_values_and_causal_bounds():
    guide = expression_guide()
    assert "1..120" in guide["functions"]["lag(x, periods)"]
    assert "same" in guide["functions"]["cs_rank(x)"].lower()
    assert "NaN" in guide["semantics"]["booleans"]
    assert "point-in-time" in guide["semantics"]["timing"]
