from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

import quanta_agents.workflow_v2 as workflow_v2
from quanta_agents.state import init_state
from quanta_agents.strategy_future_data_check import (
    FutureDataInfluenceError,
    check_generated_daily_strategy,
    check_output_weights_truncation_consistency,
)
from quanta_agents.workflow_v2 import ResearchLoopV2


def _long_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-02", periods=12, freq="B"),
            "close": [10.0, 10.2, 10.1, 10.4, 10.5, 10.3, 10.6, 10.8, 10.7, 11.0, 11.1, 11.2],
        }
    )


def _safe_long_output(_train, validate, _params):
    prices = validate["daily"].sort_values("trade_date").copy()
    change = prices["close"].pct_change().fillna(0.0)
    asset = np.where(change > 0, 0.2, 0.0)
    return pd.DataFrame(
        {
            "trade_date": prices["trade_date"].to_numpy(),
            "000001.SZ": asset,
            "cash": 1.0 - asset,
        }
    )


def _bad_long_output(_train, validate, _params):
    prices = validate["daily"].sort_values("trade_date").copy()
    future_dependent_weight = float(prices["close"].iloc[-1] / 100.0)
    return pd.DataFrame(
        {
            "trade_date": prices["trade_date"].to_numpy(),
            "000001.SZ": future_dependent_weight,
            "cash": 1.0 - future_dependent_weight,
        }
    )


def test_truncation_check_passes_causal_long_table_with_date_column() -> None:
    report = check_output_weights_truncation_consistency(
        _safe_long_output,
        {},
        {"daily": _long_prices()},
        {},
        datetime_column="trade_date",
    )

    assert report["passed"] is True
    assert len(report["checked_cutoffs"]) >= 2


def test_truncation_check_rejects_future_dependent_long_table() -> None:
    with pytest.raises(FutureDataInfluenceError, match="未来数据影响了过去权重"):
        check_output_weights_truncation_consistency(
            _bad_long_output,
            {},
            {"daily": _long_prices()},
            {},
            datetime_column="trade_date",
        )


def test_truncation_check_allows_inclusive_membership_on_decision_date() -> None:
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2020-01-01"],
            "end_date": ["2024-12-31"],
        }
    )

    def output(_train, validate, _params):
        dates = pd.to_datetime(validate["daily"]["trade_date"])
        intervals = validate["membership"]
        starts = pd.to_datetime(intervals["start_date"])
        ends = pd.to_datetime(intervals["end_date"])
        asset = [
            0.2 if bool(((starts <= date) & (ends >= date)).any()) else 0.0
            for date in dates
        ]
        return pd.DataFrame(
            {
                "trade_date": dates,
                "000001.SZ": asset,
                "cash": 1.0 - np.asarray(asset),
            }
        )

    report = check_output_weights_truncation_consistency(
        output,
        {},
        {"daily": _long_prices(), "membership": membership},
        {},
        datetime_column="trade_date",
    )

    assert report["passed"] is True


def test_truncation_check_rejects_using_future_membership_end() -> None:
    membership = pd.DataFrame(
        {
            "code": ["000001.SZ"],
            "start_date": ["2020-01-01"],
            "end_date": ["2024-12-31"],
        }
    )

    def output(_train, validate, _params):
        dates = pd.to_datetime(validate["daily"]["trade_date"])
        future_end = pd.to_datetime(validate["membership"]["end_date"]).max()
        asset = np.asarray([0.2 if date < future_end else 0.0 for date in dates])
        return pd.DataFrame(
            {
                "trade_date": dates,
                "000001.SZ": asset,
                "cash": 1.0 - asset,
            }
        )

    with pytest.raises(FutureDataInfluenceError, match="未来数据影响了过去权重"):
        check_output_weights_truncation_consistency(
            output,
            {},
            {"daily": _long_prices(), "membership": membership},
            {},
            datetime_column="trade_date",
        )


def test_truncation_check_supports_wide_datetime_index_and_missing_future_asset() -> None:
    dates = pd.date_range("2024-02-01", periods=12, freq="B")
    wide = pd.DataFrame(
        {
            "000001.SZ": np.linspace(10.0, 11.1, len(dates)),
            "000002.SZ": [np.nan] * 7 + [20.0, 20.1, 20.2, 20.3, 20.4],
        },
        index=dates,
    )

    def output(_train, validate, _params):
        prices = validate["wide"].dropna(axis=1, how="all").copy()
        changes = prices.ffill().pct_change().fillna(0.0)
        weights = (changes > 0).astype(float) * 0.1
        weights["cash"] = 1.0 - weights.sum(axis=1)
        return weights

    report = check_output_weights_truncation_consistency(
        output,
        {},
        {"wide": wide},
        {},
    )

    assert report["passed"] is True


def test_truncation_check_allows_tiny_floating_point_difference() -> None:
    prices = _long_prices()

    def output(_train, validate, _params):
        frame = validate["daily"]
        rounding_noise = len(frame) * 1e-12
        asset = np.full(len(frame), 0.2 + rounding_noise)
        return pd.DataFrame(
            {
                "trade_date": frame["trade_date"].to_numpy(),
                "000001.SZ": asset,
                "cash": 1.0 - asset,
            }
        )

    report = check_output_weights_truncation_consistency(
        output,
        {},
        {"daily": prices},
        {},
        datetime_column="trade_date",
        rtol=1e-7,
        atol=1e-9,
    )

    assert report["passed"] is True


def test_generated_strategy_check_compiles_and_calls_output_weights() -> None:
    code = """
import numpy as np
import pandas as pd

def output_weights(train_data_bundle, validate_data_bundle, params):
    prices = validate_data_bundle["daily"].sort_values("trade_date").copy()
    change = prices["close"].pct_change().fillna(0.0)
    asset = np.where(change > 0, 0.2, 0.0)
    return pd.DataFrame({
        "trade_date": prices["trade_date"].to_numpy(),
        "000001.SZ": asset,
        "cash": 1.0 - asset,
    })
"""
    result = {
        "train_data_bundle": {},
        "validate_data_bundle": {"daily": _long_prices()},
        "params": {},
        "strategy_output": {
            "output_weights_df": {"datetime_column": "trade_date"},
        },
    }

    report = check_generated_daily_strategy(code, result)

    assert report["passed"] is True


class _AlwaysFutureLookingStrategyAgent:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, state):
        self.calls += 1
        state["strategy_code"] = """
import pandas as pd
def output_weights(train_data_bundle, validate_data_bundle, params):
    prices = validate_data_bundle["daily"].sort_values("trade_date").copy()
    weight = float(prices["close"].iloc[-1] / 100.0)
    return pd.DataFrame({
        "trade_date": prices["trade_date"].to_numpy(),
        "000001.SZ": weight,
        "cash": 1.0 - weight,
    })
"""
        state["strategy_result"] = {
            "train_data_bundle": {},
            "validate_data_bundle": {"daily": _long_prices()},
            "params": {},
            "strategy_output": {
                "output_weights_df": {"datetime_column": "trade_date"},
            },
        }
        state["phase"] = "validate"
        return state


class _CountingValidateAgent:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, state):
        self.calls += 1
        state["phase"] = "test"
        return state


def test_v2_rejects_future_dependent_strategy_before_regular_validation(monkeypatch) -> None:
    strategy_agent = _AlwaysFutureLookingStrategyAgent()
    validate_agent = _CountingValidateAgent()
    monkeypatch.setattr(workflow_v2, "write_trace_json", lambda *args, **kwargs: None)
    loop = ResearchLoopV2(
        strategy_agent=strategy_agent,
        validate_agent=validate_agent,
    )
    state = init_state("test")
    candidate = {
        "hypothesis": "test",
        "strategy_modification": "test",
        "required_data": [],
        "backtest_datasets": [],
    }

    with pytest.raises(RuntimeError, match="未来数据影响了过去权重"):
        loop._generate_and_validate(
            state,
            deepcopy(candidate),
            candidate_id="candidate_01",
            experiment_spec={"backtest_mode": "daily"},
            max_technical_rounds=2,
        )

    assert strategy_agent.calls == 2
    assert validate_agent.calls == 0
