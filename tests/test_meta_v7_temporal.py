from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.research_kernel.execution import execute_strategy as legacy_execute
from quanta_agents.meta_v7.temporal import scope_panel, scope_frames
from quanta_agents.meta_v7.execution import execute_strategy, execution_pool


def panel(stocks=8):
    dates = pd.bdate_range("2019-01-02", periods=180)
    t, j = np.arange(len(dates))[:, None], np.arange(stocks)[None, :]
    close = pd.DataFrame((10 + j) * np.exp(.001 * t + .002 * np.sin(t / 11 + j)),
                         index=dates, columns=[f"sh{600000 + i}" for i in range(stocks)])
    opening = close.shift(1).fillna(close.iloc[0])
    fields = {"open": opening, "close": close, "high": np.maximum(opening, close) * 1.001,
        "low": np.minimum(opening, close) * .999, "raw_open": opening.copy(), "raw_prev_close": opening.copy(),
        "adjustment_factor": close * 0 + 1, "volume": close * 0 + 1e6, "amount": close * 0 + 1e8,
        "is_st": close * 0, "is_delisting": close * 0, "open_observed": close * 0 + 1}
    return MarketPanel(fields, close.notna(), {"kind": "generated_only"})


def scores(p):
    return {"F1": p.fields["close"].copy(), "guard": p.fields["close"] * 0 + 1}


def spec():
    return {"name": "prefix", "score": {"op": "factor", "id": "F1"},
        "allocation": {"top_n": 3, "max_stock_weight": .3},
        "gate": {"op": "where", "args": [{"op": "factor", "id": "guard"},
                      {"op": "constant", "value": 1}, {"op": "constant", "value": 0}]}}


def test_scope_preserves_history_source_bindings_and_derived_identity(tmp_path):
    p = panel()
    source = tmp_path / "membership.txt"
    source.write_text("sh600000 2010-01-01 2025-12-31", encoding="utf-8")
    p.provenance["request"] = {"membership_path": str(source), "membership_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    cutoff = p.dates[140]
    original = p.fields["close"].copy()
    scoped = scope_panel(p, end=str(cutoff.date()))
    assert scoped.dates.equals(p.dates[:141])
    assert scoped.provenance["request"] == p.provenance["request"]
    assert scoped.provenance["temporal_scope"]["future_numeric_rows_read"] is False
    assert_frame_equal(scoped.fields["close"], original.iloc[:141])
    scoped.fields["close"].iloc[0, 0] += 1
    assert_frame_equal(p.fields["close"], original)
    changed = deepcopy(p)
    changed.fields["close"].iloc[141:] = np.inf
    assert scope_panel(p, end=str(cutoff.date())).fingerprint() == scope_panel(changed, end=str(cutoff.date())).fingerprint()


@pytest.mark.parametrize("corruption", ["where", "adjustment", "infinite_market", "object_score"])
def test_future_illegal_values_do_not_change_prefix_success_targets_or_account(corruption):
    p = panel()
    f = scores(p)
    start, end = str(p.dates[125].date()), str(p.dates[145].date())
    baseline = execute_strategy(p, f, spec(), start=start, end=end)
    changed = deepcopy(p)
    future = {key: value.copy() for key, value in f.items()}
    if corruption == "where":
        future["guard"].iloc[146:] = 2
        with pytest.raises(ValueError, match="where"):
            legacy_execute(changed, future, spec(), start=start, end=end)
    elif corruption == "adjustment":
        changed.fields["adjustment_factor"].iloc[146:] *= 99
        with pytest.raises(ValueError, match="disagree"):
            legacy_execute(changed, future, spec(), start=start, end=end)
    elif corruption == "infinite_market":
        changed.fields["close"].iloc[146:] = np.inf
    else:
        future["F1"] = future["F1"].astype(object)
        future["F1"].iloc[146:] = "not-a-number"
    result = execute_strategy(changed, future, spec(), start=start, end=end)
    for key in ("targets", "daily", "trades", "annual"):
        assert_frame_equal(result[key], baseline[key], check_exact=True)


def test_scope_rejects_corruption_inside_consumed_history_and_does_not_fill_axes():
    p = panel()
    p.fields["close"].iloc[130, 0] = np.inf
    with pytest.raises(ValueError, match="infinite"):
        scope_panel(p, end=str(p.dates[140].date()))
    p = scope_panel(panel(), end="2019-07-31")
    with pytest.raises(ValueError, match="axes"):
        scope_frames({"F1": p.fields["close"].iloc[1:]}, p)
    with pytest.raises(ValueError):
        scope_panel(p, end="2000-01-01")


def test_future_malformed_eligibility_does_not_upcast_valid_prefix_into_failure():
    p = panel()
    cutoff = str(p.dates[140].date())
    expected = scope_panel(p, end=cutoff)
    p.eligible = p.eligible.astype(object)
    p.eligible.iloc[141:] = "invalid future membership"
    actual = scope_panel(p, end=cutoff)
    assert_frame_equal(actual.eligible, expected.eligible)
    assert actual.fingerprint() == expected.fingerprint()
    p.eligible.iloc[130, 0] = "invalid past membership"
    with pytest.raises(ValueError, match="eligibility"):
        scope_panel(p, end=cutoff)


def test_shared_execution_pool_masks_history_st_delisting_and_liquidity():
    p = panel()
    day = p.dates[140]
    p.fields["is_st"].loc[day, p.symbols[0]] = 1
    p.fields["is_delisting"].loc[day, p.symbols[1]] = 1
    p.fields["close"].iloc[25:130, 2] = np.nan
    p.fields["amount"].iloc[121:141, 3] = 0
    found = execution_pool(p)
    assert not found.iloc[:119].to_numpy().any()
    assert found.loc[day].tolist() == [False, False, False, False, True, True, True, True]
