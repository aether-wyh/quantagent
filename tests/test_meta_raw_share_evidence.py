from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("revision2_execution_fixtures", HERE / "test_meta_ashare_execution.py")
assert SPEC is not None and SPEC.loader is not None
FIXTURES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURES)
MODULE = FIXTURES.MODULE


def test_fractional_raw_share_evidence_does_not_hide_the_order():
    result = FIXTURES.run(FIXTURES.market((0.5, 0.5, 0.501234)))
    evidence = result["raw_share_execution_evidence"]
    assert result["raw_share_inventory_cash_ledger_valid"] is False
    assert evidence["measurement_available"] is True
    assert evidence["observed_orders"] == 2
    assert evidence["non_integer_order_count"] == 1
    assert evidence["non_integer_buy_order_count"] == 0
    assert evidence["non_integer_sell_order_count"] == 1
    assert evidence["max_distance_to_integer_shares"] == pytest.approx(0.2468)
    assert evidence["total_distance_to_integer_shares"] == pytest.approx(0.2468)
    sell = result["_trades_df"].iloc[-1]
    assert sell.raw_shares == pytest.approx(100.2468)
    assert evidence["fractional_order_examples"][0]["raw_shares"] == sell.raw_shares
    assert result["_backtest_debug"]["raw_share_execution_evidence"] == evidence


def test_float_roundoff_is_not_classified_as_fractional_inventory():
    row = {"date": "2020-01-02", "code": "sh600000", "side": "sell", "raw_shares": 1999.9999999999998}
    evidence = MODULE._raw_share_execution_evidence([row], True)
    assert evidence["non_integer_order_count"] == 0
    assert evidence["max_distance_to_integer_shares"] < evidence["integer_tolerance_shares"]
    assert evidence["raw_share_inventory_cash_ledger_valid"] is False


@pytest.mark.parametrize("capital, observed", [(1005.0, 2), (1004.99, 0)])
def test_absence_of_observed_fractional_shares_never_validates_approximation(capital, observed):
    result = FIXTURES.run(capital=capital)
    evidence = result["raw_share_execution_evidence"]
    assert evidence["measurement_available"] is True
    assert evidence["observed_orders"] == observed
    assert evidence["non_integer_order_count"] == 0
    assert result["raw_share_inventory_cash_ledger_valid"] is False
    assert result["_backtest_debug"]["raw_share_inventory_cash_ledger_valid"] is False


def test_legacy_absent_raw_measurements_are_unknown_not_zero():
    result = FIXTURES.run(raw_share_lots=False, min_commission=0.0)
    evidence = result["raw_share_execution_evidence"]
    assert evidence["measurement_available"] is False
    assert evidence["non_integer_order_count"] is None
    assert evidence["max_distance_to_integer_shares"] is None
    assert result["raw_share_inventory_cash_ledger_valid"] is False


# Four deterministic before/after fixture comparisons were run against the
# frozen first-run engine during revision development. They are documented in
# the engineering journal, rather than depending on a local staging directory
# or checking the new implementation against itself after merging.
