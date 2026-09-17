"""Serialization-only guards: generated targets, no market/model/account run."""
from copy import deepcopy
from dataclasses import asdict
import json

import numpy as np
import pandas as pd
import pandas.core.generic as generic
import pyarrow.parquet as pq
import pytest

from quanta_agents.meta_v6.cycle_execution import _targets
from quanta_agents.meta_v6.portfolio import PortfolioSpec, _selection_weights
from quanta_agents.meta_v6.portfolio_study import file_hash, save_account


def generated_buffer_targets():
    # Real target_weights constructs an irregular trading calendar with no
    # inferred freq; Parquet also does not serialize pandas' cached freq hint.
    dates = pd.DatetimeIndex(pd.date_range("2016-01-01", periods=8, freq="W-FRI").to_numpy(),
                             name="signal_date")
    codes = pd.Index([f"sh{600000+i}" for i in range(64)], name="symbol")
    spec = PortfolioSpec("generated_buffer", {"generated_factor": 1.}, top_n=20,
                         max_stock_weight=.05, membership_buffer=40,
                         rebalance_schedule="weekly_last_session")
    plans, rows = {}, []
    for i, date in enumerate(dates):
        plan = {"order": np.roll(np.arange(64), -i).tolist(), "exposure": 1.,
                "coefficient": [1.] * 64, "gate": [1.] * 64}
        plans[str(date.date())] = plan
        rows.append(_selection_weights(plan, spec, np.zeros(64, dtype=bool), 64))
    targets = pd.DataFrame(rows, index=dates, columns=codes)
    targets.attrs = {"selection_plans": plans, "portfolio_spec": asdict(spec)}
    return targets, spec


@pytest.mark.parametrize("writer", ["cycle_targets", "account_frames"])
def test_export_keeps_buffer_exact_and_copies_metadata_once_per_frame_not_per_column(tmp_path, monkeypatch, writer):
    targets, spec = generated_buffer_targets()
    # Build expectations before instrumentation, without per-column attrs copies.
    expected_numbers = pd.DataFrame(targets.to_numpy(copy=True), index=targets.index.copy(),
                                    columns=targets.columns.copy())
    expected_attrs = deepcopy(targets.attrs)
    if writer == "cycle_targets":
        frames = {"targets": targets}
    else:
        frames = {name: targets.copy(deep=True) for name in ("daily", "trades", "annual")}
    original_attributes = {name: frame.attrs for name, frame in frames.items()}
    original_buffers = {name: frame.attrs["selection_plans"] for name, frame in frames.items()}
    copies = []
    actual_deepcopy = generic.deepcopy

    def counted_deepcopy(value, *args, **kwargs):
        if isinstance(value, dict) and "selection_plans" in value:
            copies.append(id(value))
        return actual_deepcopy(value, *args, **kwargs)

    monkeypatch.setattr(generic, "deepcopy", counted_deepcopy)
    if writer == "cycle_targets":
        proofs = _targets(tmp_path, targets)
        assert len(proofs) == 2
        assert all(file_hash(proof["path"]) == proof["sha256"] for proof in proofs)
    else:
        save_account(tmp_path, {**frames, "summary": {"generated": True}, "policy": {"generated": True}})
        artifacts = json.loads((tmp_path / "artifacts.json").read_text(encoding="utf-8"))
        assert all(file_hash(tmp_path / name) == digest for name, digest in artifacts.items())
        assert all(name + "_attributes.json" in artifacts for name in frames)

    # The shallow export copy incurs exactly one metadata copy per DataFrame.
    # The previous implementation incurred one for every stock column instead.
    assert len(copies) == len(frames)
    for name, frame in frames.items():
        path = tmp_path / (name + ".parquet")
        metadata = pq.read_metadata(path).metadata
        assert b"PANDAS_ATTRS" not in metadata
        assert not json.loads(metadata[b"pandas"]).get("attributes")
        restored = pd.read_parquet(path)
        assert not restored.attrs
        pd.testing.assert_frame_equal(restored, expected_numbers, check_exact=True)
        attributes_name = "target_attributes.json" if name == "targets" else name + "_attributes.json"
        restored.attrs = json.loads((tmp_path / attributes_name).read_text(encoding="utf-8"))
        assert restored.attrs == expected_attrs
        assert frame.attrs is original_attributes[name]
        assert frame.attrs["selection_plans"] is original_buffers[name]
        assert frame.attrs == expected_attrs
        np.testing.assert_array_equal(frame.to_numpy(), expected_numbers.to_numpy())

        # Restoring the sidecar preserves actual-holdings buffer decisions,
        # including retaining a held name ranked below the unbuffered top 20.
        held = np.zeros(64, dtype=bool)
        held[25:30] = True
        restored_spec = PortfolioSpec(**restored.attrs["portfolio_spec"])
        for day, plan in expected_attrs["selection_plans"].items():
            original_choice = _selection_weights(plan, spec, held, 64)
            restored_choice = _selection_weights(restored.attrs["selection_plans"][day], restored_spec, held, 64)
            np.testing.assert_array_equal(restored_choice, original_choice)
        first_plan = restored.attrs["selection_plans"][str(restored.index[0].date())]
        assert _selection_weights(first_plan, restored_spec, held, 64)[25] > 0

    # Numeric verification and sidecar reconstruction must not reintroduce
    # column-wise metadata copying either.
    assert len(copies) == len(frames)
