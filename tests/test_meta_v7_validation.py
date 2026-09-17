"""Synthetic and mocked validation boundaries; no model or real-data calls."""
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v7 import validation as v


def calendar():
    return pd.bdate_range("2020-01-01", periods=100)


def plan(gap=0):
    dates = calendar()
    return dict(train_start=str(dates[1].date()), train_end=str(dates[59].date()),
                validation_start=str(dates[60+gap].date()), validation_end=str(dates[-1].date()),
                embargo_sessions=gap, max_label_horizon=20)


def spec(factor):
    return {"version": 1, "name": factor, "score": {"op": "factor", "id": factor}, "allocation": {}}


def account(sharpe, turnover=1.):
    daily = pd.DataFrame({"exposure": [.5], "turnover": [turnover], "blocked_orders": [0], "stale_fraction": [0.]},
                         index=pd.DatetimeIndex(["2020-01-02"]))
    return {"summary": {"sharpe": sharpe, "turnover": turnover}, "daily": daily,
            "annual": pd.DataFrame({"sharpe": [sharpe]}, index=pd.Index([2020], name="year")),
            "trades": pd.DataFrame({"quantity": [1.]}), "policy": {"capital": 1_000_000.}}


def test_purge_is_horizon_plus_entry_lag_not_mandatory_embargo():
    result = v.validate_split_plan(plan(), calendar())
    assert result["actual_embargo_sessions"] == 0
    assert len(result["purged_train_signal_dates"]) == 21
    assert result["label_safe_train_end"] == str(calendar()[38].date())
    assert result["validation_previous_signal_session"] == str(calendar()[59].date())
    assert result["account_training_days_purged"] is False


def test_gap_separate_from_purge():
    result = v.validate_split_plan(plan(3), calendar())
    assert result["actual_embargo_sessions"] == 3
    assert len(result["purged_train_signal_dates"]) == 21
    invalid = plan()
    invalid["embargo_sessions"] = 1
    with pytest.raises(ValueError, match="gap"):
        v.validate_split_plan(invalid, calendar())


@pytest.mark.parametrize("change", [{"max_label_horizon": True}, {"max_label_horizon": 0},
                                    {"embargo_sessions": -1}, {"extra": 1},
                                    {"validation_start": "2020-01-01"}, {"train_end": "2020-01-08"}])
def test_malformed_plans_rejected(change):
    with pytest.raises(ValueError):
        v.validate_split_plan({**plan(), **change}, calendar())


def test_bad_calendars_rejected():
    for dates in (calendar()[::-1], calendar().append(calendar()[:1]), calendar().tz_localize("UTC")):
        with pytest.raises(ValueError):
            v.validate_split_plan(plan(), dates)


def test_training_selection_fixed_before_all_validation_and_specs_immutable(monkeypatch):
    calls = []
    original = [spec("A"), spec("B")]
    untouched = deepcopy(original)
    def execute(panel, frames, declared, **kwargs):
        phase = "train" if kwargs["end"] == plan()["train_end"] else "validation"
        calls.append((phase, declared["name"]))
        sharpe = {("train", "A"): 1., ("train", "B"): .5,
                  ("validation", "A"): -4., ("validation", "B"): 8.}[phase, declared["name"]]
        declared["metadata"]["mutated_by_engine"] = True
        return account(sharpe)
    monkeypatch.setattr(v, "execute_strategy", execute)
    result = v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, original, plan())
    assert calls == [("train", "A"), ("train", "B"), ("validation", "A"), ("validation", "B")]
    assert result["selection"]["strategy_id"] == result["candidates"][0]["strategy_id"]
    assert original == untouched
    assert all(row["normalized_spec"]["metadata"] == {} for row in result["candidates"])
    assert result["formal_financial_success"] is False


def test_failure_is_retained_not_zero_return(monkeypatch):
    def execute(panel, frames, declared, **kwargs):
        if declared["name"] == "A":
            raise RuntimeError("real failure evidence")
        return account(None)
    monkeypatch.setattr(v, "execute_strategy", execute)
    result = v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, [spec("A"), spec("B")], plan())
    assert result["selection"]["strategy_id"] is None
    assert result["candidates"][0]["train"] is None
    assert result["candidates"][0]["validation"] is None
    assert result["candidates"][0]["error"]["message"] == "real failure evidence"


def test_compact_json_and_exclusive_raw_artifacts_preserve_calendar_bounds(monkeypatch, tmp_path):
    bounds = plan()
    bounds["train_start"] = "2019-12-31"
    calls = []
    raw = account(1.)
    raw["daily"].attrs = {"source": "original"}
    def execute(panel, frames, spec, **kwargs):
        calls.append(kwargs)
        return raw
    monkeypatch.setattr(v, "execute_strategy", execute)
    folder = tmp_path / "validation"
    result = v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, [spec("A")], bounds, artifact_dir=folder)
    assert calls[0]["start"] == "2019-12-31"
    json.dumps(result, allow_nan=False)
    for phase in ("train", "validation"):
        compact = result["candidates"][0][phase]
        assert compact["raw_retained"]
        manifest = json.loads(open(compact["raw_artifacts"]["manifest_path"], encoding="utf-8").read())
        for proof in manifest["artifacts"]:
            assert hashlib.sha256(__import__("pathlib").Path(proof["path"]).read_bytes()).hexdigest() == proof["sha256"]
        assert any(proof["path"].endswith("daily_attributes.json") for proof in manifest["artifacts"])
    assert raw["daily"].attrs == {"source": "original"}
    with pytest.raises(FileExistsError):
        v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, [spec("A")], bounds, artifact_dir=folder)
    assert len(calls) == 2


def test_duplicate_economic_specs_and_cancellation(monkeypatch):
    called = []
    monkeypatch.setattr(v, "execute_strategy", lambda *a, **kw: called.append(True))
    duplicate = spec("A")
    renamed = {**duplicate, "name": "renamed"}
    with pytest.raises(ValueError, match="duplicate"):
        v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, [duplicate, renamed], plan())
    with pytest.raises(InterruptedError):
        v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, [duplicate], plan(), cancelled=lambda: True)
    assert not called


@pytest.mark.parametrize("limit", [0, 1, 2])
def test_each_account_reserves_budget_before_execution_and_retains_blocked_phase(monkeypatch, tmp_path, limit):
    sequence = []
    reservations = []
    def reserve(phase, sid):
        sequence.append(("reserve", phase, sid))
        if len(reservations) >= limit:
            raise ValueError("account budget exhausted")
        reservations.append((phase, sid))
    def execute(panel, frames, declared, **kwargs):
        sequence.append(("execute", kwargs["start"]))
        return account(1.)
    monkeypatch.setattr(v, "execute_strategy", execute)
    result = v.evaluate_frozen_candidates(SimpleNamespace(dates=calendar()), {}, [spec("A")], plan(),
        artifact_dir=tmp_path / "evidence", before_account=reserve)
    record = result["candidates"][0]
    assert sum(row[0] == "execute" for row in sequence) == limit
    assert len(reservations) == limit
    assert sequence[0][0:2] == ("reserve", "train")
    if limit < 2:
        assert record["status"] == ("train_failed" if limit == 0 else "validation_failed")
        assert record["error"]["message"] == "account budget exhausted"
        assert list((tmp_path / "evidence").glob("*_failure.json"))
    else:
        assert record["status"] == "completed"
        assert [row[0] for row in sequence] == ["reserve", "execute", "reserve", "execute"]


def test_paired_bootstrap_preserves_identity_and_shared_family_dependence():
    rng = np.random.default_rng(4)
    base = pd.Series(rng.normal(.0003, .01, 100), index=calendar())
    candidates = pd.DataFrame({"same": base, "improved": base+.001, "duplicate": base+.001})
    candidates.iloc[10:20] = np.nan
    result = v.paired_sharpe_bootstrap(candidates, base, block_sessions=10, repetitions=100, seed=8)
    rows = result["contrasts"]
    assert rows[0]["sharpe_increment"] == 0.
    assert rows[0]["percentile_interval"] == [0., 0.]
    assert rows[1]["sharpe_increment"] == rows[2]["sharpe_increment"]
    assert rows[1]["simultaneous_family_interval"] == rows[2]["simultaneous_family_interval"]
    assert rows[1]["paired_sessions"] == 90
    assert result["calendar_sessions"] == 100
    assert result["independent_trial_count_used"] is None
    assert result["selection_adjusted"] is False
    assert result == v.paired_sharpe_bootstrap(candidates, base, block_sessions=10, repetitions=100, seed=8)


def test_degenerate_bootstrap_not_zero_evidence():
    zero = pd.Series(0., index=calendar())
    result = v.paired_sharpe_bootstrap(zero, zero, block_sessions=10, repetitions=20, seed=1)
    assert result["contrasts"][0]["status"] == "not_evaluable"
    assert result["contrasts"][0]["sharpe_increment"] is None


def test_bootstrap_alignment_and_short_history_rejected():
    base = pd.Series(np.arange(100)/100, index=calendar())
    with pytest.raises(ValueError, match="alignment"):
        v.paired_sharpe_bootstrap(base, base.iloc[::-1], block_sessions=10, repetitions=20, seed=1)
    with pytest.raises(ValueError, match="two blocks"):
        v.paired_sharpe_bootstrap(base, base, block_sessions=60, repetitions=20, seed=1)


def test_real_synthetic_account_validation_prefix_is_causal():
    from quanta_agents.meta_v7.benchmarks import make_synthetic_task
    from quanta_agents.meta_v7.execution import execute_strategy
    task = make_synthetic_task(2, train_sessions=30, validation_sessions=20, stocks=20)
    s = spec(sorted(task["frames"])[0])
    s["allocation"] = {"top_n": 5, "max_stock_weight": .2}
    p = task["panel"]
    split = task["split_plan"]
    before = execute_strategy(p, task["frames"], s, start=split["train_start"], end=split["train_end"])
    for frame in p.fields.values():
        frame.loc[split["validation_start"]:] = 999.
    for frame in task["frames"].values():
        frame.loc[split["validation_start"]:] = -999.
    after = execute_strategy(p, task["frames"], s, start=split["train_start"], end=split["train_end"])
    for key in ("daily", "trades", "annual"):
        assert_frame_equal(before[key], after[key], check_exact=True)
