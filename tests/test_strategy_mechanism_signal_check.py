from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest

from quanta_agents.strategy_mechanism_signal_check import (
    MechanismSignalValidationError,
    check_generated_mechanism_signal,
    mechanism_signal_reference,
)


_GOOD_CODE = """
def build_mechanism_signal(train_data_bundle, validate_data_bundle):
    frame = validate_data_bundle["daily"]
    return (
        (frame["d1_high"] >= frame["upper"])
        & (frame["d1_close"] <= frame["upper"])
        & (frame["d2_close"] > frame["upper"])
    )

def output_weights(train_data_bundle, validate_data_bundle, params):
    frame = validate_data_bundle["daily"]
    new_signal = build_mechanism_signal(train_data_bundle, validate_data_bundle)
    stock_weight = new_signal.astype(float)
    return pd.DataFrame({
        "trade_date": frame["trade_date"],
        "AAA": stock_weight,
        "cash": 1.0 - stock_weight,
    })
"""


def _strategy_result() -> dict[str, object]:
    frame = pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-02", periods=3, freq="B"),
            "upper": [10.0, 10.0, 10.0],
            # 等于上沿时应通过；第二行收盘站上上沿，应被 D1.close <= U 排除。
            "d1_high": [10.0, 10.2, 10.2],
            "d1_close": [10.0, 10.1, 9.9],
            "d2_close": [10.1, 10.3, 10.1],
        }
    )
    return {
        "train_data_bundle": {"daily": frame.iloc[0:0].copy()},
        "validate_data_bundle": {"daily": frame},
        "params": {},
        "universe": ["AAA"],
    }


def test_mechanism_signal_check_accepts_identical_reference() -> None:
    reference = mechanism_signal_reference(_GOOD_CODE)
    report = check_generated_mechanism_signal(
        _GOOD_CODE,
        _strategy_result(),
        reference_source=str(reference["source"]),
    )

    assert report["passed"] is True
    assert report["definition_matches_added_to_base"] is True
    assert report["runtime_usage"]["all_false_produces_zero_stock_weights"] is True


@pytest.mark.parametrize(
    "bad_code",
    [
        _GOOD_CODE.replace(
            'frame["d1_high"] >= frame["upper"]',
            'frame["d1_high"] > frame["upper"]',
        ),
        _GOOD_CODE.replace(
            '        & (frame["d1_close"] <= frame["upper"])\n',
            "",
        ),
    ],
    ids=["greater_instead_of_greater_equal", "missing_d1_close_condition"],
)
def test_mechanism_signal_check_catches_candidate_007_changes(
    bad_code: str,
) -> None:
    reference = mechanism_signal_reference(_GOOD_CODE)

    with pytest.raises(
        MechanismSignalValidationError,
        match="改写了主版本的新信号函数",
    ):
        check_generated_mechanism_signal(
            bad_code,
            _strategy_result(),
            reference_source=str(reference["source"]),
        )


def test_mechanism_signal_check_compares_called_helper_dependencies() -> None:
    reference_code = _GOOD_CODE.replace(
        "def build_mechanism_signal(train_data_bundle, validate_data_bundle):\n"
        '    frame = validate_data_bundle["daily"]\n'
        "    return (\n"
        '        (frame["d1_high"] >= frame["upper"])\n'
        '        & (frame["d1_close"] <= frame["upper"])\n'
        '        & (frame["d2_close"] > frame["upper"])\n'
        "    )",
        "def _edge_signal(frame):\n"
        "    return (\n"
        '        (frame["d1_high"] >= frame["upper"])\n'
        '        & (frame["d1_close"] <= frame["upper"])\n'
        '        & (frame["d2_close"] > frame["upper"])\n'
        "    )\n\n"
        "def build_mechanism_signal(train_data_bundle, validate_data_bundle):\n"
        '    return _edge_signal(validate_data_bundle["daily"])',
    )
    changed_dependency = reference_code.replace(
        'frame["d1_close"] <= frame["upper"]',
        'frame["d1_close"] < frame["upper"]',
    )
    reference = mechanism_signal_reference(reference_code)

    with pytest.raises(MechanismSignalValidationError, match="改写了主版本"):
        check_generated_mechanism_signal(
            changed_dependency,
            _strategy_result(),
            reference_source=str(reference["source"]),
        )


def test_mechanism_signal_call_cannot_be_discarded() -> None:
    ignored_code = _GOOD_CODE.replace(
        "    new_signal = build_mechanism_signal(train_data_bundle, validate_data_bundle)\n"
        "    stock_weight = new_signal.astype(float)",
        "    build_mechanism_signal(train_data_bundle, validate_data_bundle)\n"
        "    stock_weight = pd.Series(1.0, index=frame.index)",
    )

    with pytest.raises(MechanismSignalValidationError, match="丢弃了返回结果"):
        check_generated_mechanism_signal(ignored_code, _strategy_result())


def test_mechanism_signal_assigned_but_not_used_for_weights_fails_runtime_check() -> None:
    ignored_code = _GOOD_CODE.replace(
        "    stock_weight = new_signal.astype(float)",
        "    print(new_signal.sum())\n"
        "    stock_weight = pd.Series(1.0, index=frame.index)",
    )

    with pytest.raises(
        MechanismSignalValidationError,
        match="没有真正参与最终信号",
    ):
        check_generated_mechanism_signal(ignored_code, _strategy_result())


def test_mechanism_signal_reference_is_not_tied_to_breakout_formula() -> None:
    arbitrary_code = _GOOD_CODE.replace(
        "    return (\n"
        '        (frame["d1_high"] >= frame["upper"])\n'
        '        & (frame["d1_close"] <= frame["upper"])\n'
        '        & (frame["d2_close"] > frame["upper"])\n'
        "    )",
        '    return frame["d2_close"] > frame["d2_close"].median()',
    )
    result = _strategy_result()

    report = check_generated_mechanism_signal(arbitrary_code, deepcopy(result))

    assert report["passed"] is True
