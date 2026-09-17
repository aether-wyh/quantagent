from copy import deepcopy
import json

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v7.factor_lab import evaluate_factors, semantics
from quanta_agents.meta_v7.execution import execution_pool
from quanta_agents.research_kernel.compiler import evaluate_expression


def fixture():
    dates = pd.bdate_range("2019-01-02", periods=180)
    columns = [f"sh{600000+i}" for i in range(40)]
    a = np.repeat([-1., -1., 1., 1.], 10)
    b = np.repeat([-1., 1., -1., 1.], 10)
    cross = a * b
    opening = pd.DataFrame(10 * np.exp(np.arange(180)[:, None] * .002 * cross), index=dates, columns=columns)
    close = opening * 1.0001
    fields = {"open": opening, "close": close, "high": close * 1.01, "low": opening * .99,
        "volume": close * 0 + 1e6, "amount": close * 0 + 1e8, "is_st": close * 0,
        "is_delisting": close * 0, "open_observed": close * 0 + 1}
    p = MarketPanel(fields, close.notna(), {"source": "generated_interaction_not_real_alpha"})
    frames = {"A": pd.DataFrame(np.tile(a, (180, 1)), index=dates, columns=columns),
              "B": pd.DataFrame(np.tile(b, (180, 1)), index=dates, columns=columns)}
    return p, frames, str(dates[125].date()), str(dates[165].date())


def test_two_zero_ic_marginals_form_explicit_incremental_interaction_without_promotion():
    p, frames, start, end = fixture()
    originals = {key: value.copy() for key, value in frames.items()}
    result = evaluate_factors(p, frames, start=start, end=end, horizons=(1, 5), pairs=[{"left": "A", "right": "B"}])
    assert result["factors"]["A"]["horizons"]["1"]["mean_ic"] == pytest.approx(0, abs=1e-12)
    assert result["factors"]["B"]["horizons"]["1"]["mean_ic"] == pytest.approx(0, abs=1e-12)
    pair = result["interactions"][0]
    assert pair["horizons"]["1"]["raw_ic"]["mean_ic"] > .9
    assert pair["horizons"]["1"]["partial_ic"]["mean_ic"] > .99
    assert pair["automatic_admission"] is False
    assert len(result["candidate_expressions"]) == 1
    candidate = result["candidate_expressions"][0]
    assert candidate["automatically_admitted"] is False
    actual = evaluate_expression(candidate["expression"], frames, execution_pool(p))
    expected = (frames["A"].where(execution_pool(p)).rank(axis=1, pct=True) - .5) * (frames["B"].where(execution_pool(p)).rank(axis=1, pct=True) - .5)
    assert_frame_equal(actual, expected)
    low, high = [r for r in result["conditions"] if r["horizon"] == 1]
    assert low["mean_ic"] < -.99 and high["mean_ic"] > .99
    for key in frames:
        assert_frame_equal(frames[key], originals[key])
    json.dumps(result, allow_nan=False)


def test_same_execution_pool_and_terminal_purge_preserve_coverage_denominator():
    p, frames, start, end = fixture()
    selected = (p.dates >= start) & (p.dates <= end)
    p.fields["is_st"].iloc[:, :10] = 1
    p.fields["is_delisting"].iloc[:, 10:20] = 1
    frames["A"].iloc[130, 20:25] = np.nan
    result = evaluate_factors(p, frames, start=start, end=end, horizons=(5, 20))
    expected_pool = execution_pool(p).loc[selected]
    coverage = result["factors"]["A"]["coverage"]
    assert coverage["pool_cells"] == int(expected_pool.to_numpy().sum()) == 41 * 20
    assert coverage["missing_cells"] == 5
    for horizon in (5, 20):
        row = result["factors"]["A"]["horizons"][str(horizon)]
        assert row["calendar_days"] == 41
        assert row["coverage"]["missing_cells"] >= (horizon + 1) * 20
        assert row["observed_days"] <= 41 - horizon - 1
    assert result["shared_computation"] == {"label_horizons": 2, "rank_frames": 2, "account_executions": 0}


def test_future_price_score_and_eligibility_changes_cannot_change_training_report():
    p, frames, start, end = fixture()
    args = {"start": start, "end": end, "horizons": (1, 5), "pairs": [{"left": "A", "right": "B"}]}
    before = evaluate_factors(p, frames, **args)
    changed = deepcopy(p)
    changed.fields["open"].iloc[166:] = np.inf
    changed.eligible.iloc[166:] = False
    altered = {key: value.astype(object) for key, value in frames.items()}
    for value in altered.values():
        value.iloc[166:] = "illegal future score"
    assert evaluate_factors(changed, altered, **args) == before


def test_risk_role_has_risk_targets_missing_path_propagates_and_no_labels_escape():
    p, frames, start, end = fixture()
    frames["A"].attrs["roles"] = ["risk_information"]
    p.fields["open_observed"].iloc[140, :10] = 0
    before = {key: value.copy() for key, value in frames.items()}
    result = evaluate_factors(p, frames, start=start, end=end, horizons=(1, 5))
    risk = result["factors"]["A"]["risk"]
    assert set(risk["5"]) == {"future_vol", "future_downside", "future_entry_max_loss", "future_loss_event"}
    assert risk["1"]["future_vol"]["mean_ic"] is None
    assert risk["5"]["future_vol"]["coverage"]["missing_cells"] >= 6 * 40 + 6 * 10
    assert result["factors"]["A"]["return_ic_is_not_role_admission"] is True
    assert result["factors"]["B"]["risk"] == {}
    assert result["candidate_expressions"] == []
    assert not any("future" in key or "label" in key for key in p.fields)
    for key in frames:
        assert_frame_equal(frames[key], before[key])


@pytest.mark.parametrize("kwargs", [
    {"controls": {"regression": "whole_sample"}}, {"controls": {"roles": {"missing": ["risk"]}}},
    {"controls": {"roles": {"A": ["future"]}}}, {"horizons": (0,)},
    {"pairs": [{"left": "A", "right": "missing"}]}, {"pairs": [{"left": "A", "right": "A"}]},
])
def test_unknown_controls_roles_horizons_and_pairs_fail_explicitly(kwargs):
    p, frames, start, end = fixture()
    with pytest.raises(ValueError):
        evaluate_factors(p, frames, start=start, end=end, **kwargs)


def test_duplicate_pair_is_retained_but_does_not_create_second_candidate():
    p, frames, start, end = fixture()
    pair = {"left": "A", "right": "B"}
    result = evaluate_factors(p, frames, start=start, end=end, horizons=(1,), pairs=[pair, pair])
    assert [r["status"] for r in result["interactions"]] == ["evaluated", "duplicate"]
    assert len(result["candidate_expressions"]) == 1
    assert semantics((1,))["multiple_testing_corrected"] is False


def test_label_role_cannot_be_overridden_into_a_signal_and_all_missing_is_retained():
    p, frames, start, end = fixture()
    frames["A"].attrs["is_label"] = True
    with pytest.raises(ValueError, match="label-role"):
        evaluate_factors(p, frames, start=start, end=end, controls={"roles": {"A": ["return"]}})
    frames["A"].attrs.clear()
    frames["A"][:] = np.nan
    result = evaluate_factors(p, frames, start=start, end=end, horizons=(1,))
    found = result["factors"]["A"]
    assert found["coverage"]["observed_cells"] == 0
    assert found["horizons"]["1"]["mean_ic"] is None
    assert found["horizons"]["1"]["missing_days"] == 41
    assert "A" in result["factors"]


def test_risk_path_has_exact_endpoints_and_stable_sample_standard_deviation():
    from quanta_agents.meta_v7.factor_lab import _labels
    p, _, _, _ = fixture()
    # Signal 125 enters at open126 and consumes exactly 127/126..131/130.
    path = np.array([100., 98., 99., 96., 102., 101.])
    p.fields["open"].iloc[126:132, 0] = path
    labels = _labels(p, (5,))[5]
    expected = path[1:] / path[:-1] - 1
    assert labels["future_vol"].iloc[125, 0] == pytest.approx(expected.std(ddof=1) * np.sqrt(252))
    assert labels["future_downside"].iloc[125, 0] == pytest.approx(np.sqrt(np.mean(np.minimum(expected, 0) ** 2)) * np.sqrt(252))
    assert labels["future_entry_max_loss"].iloc[125, 0] == pytest.approx(.04)
    assert labels["future_loss_event"].iloc[125, 0] == 0
    before = {key: value.iloc[125, 0] for key, value in labels.items()}
    p.fields["open"].iloc[132:, 0] *= 1000
    after = _labels(p, (5,))[5]
    assert {key: value.iloc[125, 0] for key, value in after.items()} == before
