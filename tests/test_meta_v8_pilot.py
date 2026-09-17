"""Generated pilot and explicitly fake transport; never dispatch a real model.

Fake runtime verification here tests orchestration only, not model identity.
Real market evidence loading is replaced with a generated strategy fixture.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import time

import numpy as np
import pytest

from quanta_agents.research_kernel.compiler import validate_strategy
from quanta_agents.research_kernel.store import exclusive_lock, serial


def test_future_real_prompt_example_uses_the_actual_revision_language(prepared):
    from quanta_agents.meta_v7.revisions import ALLOWED_PATHS
    prompt = (prepared / "cells/03_real_v8/frozen_prompt.txt").read_text(encoding="utf-8")
    match = re.search(r"Example array: (\[.*?\])\.", prompt)
    assert match, "The real interface pilot must declare the patch grammar it scores"
    example = json.loads(match.group(1))
    assert all(set(change) == {"path", "value"} and change["path"] in ALLOWED_PATHS for change in example)
    assert {change["path"]: change["value"] for change in example} == {
        "/allocation/weighting": "equal", "/risk_score": None}


@pytest.fixture(scope="module")
def pilot():
    source = Path(__file__).resolve().parents[1] / "scripts/validate_meta_v8.py"
    spec = importlib.util.spec_from_file_location("v8_pilot_generated_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generated(pilot):
    return {(seed, kind): pilot._generated(seed, kind) for seed in pilot.SEEDS for kind in pilot.KINDS}


def common_fixture():
    spec = validate_strategy({"name": "generated control; no real market result",
        "score": {"op": "weighted_sum", "args": [{"op": "rank", "args": [{"op": "factor", "id": "F1"}]}],
                  "weights": [.5]},
        "allocation": {"top_n": 40, "weighting": "inverse_volatility", "max_stock_weight": .05},
        "risk_score": {"op": "add", "args": [{"op": "factor", "id": "F7"}, {"op": "constant", "value": 1e-6}]},
        "metadata": {"synthetic_only": True, "kernel_control_role": "omit_2"}})
    return {"scope": {"start": "2016-01-01", "end": "2020-12-31", "exposed": True},
            "arms": [{"run_id": "generated_parent", "strategy": spec, "summary": {"mean_exposure": .8}}],
            "requested_parent_run_id": "generated_parent", "source_hashes": {},
            "account_policy": {"synthetic_only": True}, "account_executions_requested": 0,
            "later_period_values_present": False}


@pytest.fixture
def prepared(pilot, generated, tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "_generated", lambda seed, kind: deepcopy(generated[(seed, kind)]))
    monkeypatch.setattr(pilot, "_real_common", common_fixture)
    output = tmp_path / "generated_pilot"
    result = pilot.prepare(output, project_root=tmp_path / "generated_project")
    assert result["calls"] == 0
    return output


def _response(schema, mode):
    if "tasks" in schema["properties"]:
        ids = schema["properties"]["tasks"]["items"]["properties"]["task_id"]["enum"]
        return {"tasks": [{"task_id": key, "candidate_id": "abstain", "direction": 1,
                           "reason": "explicit fake transport response"} for key in ids],
                "limitations": "Fake response: no research result or runtime certification"}
    parent = common_fixture()["arms"][0]["strategy"]
    expected = deepcopy(parent)
    expected["allocation"]["weighting"], expected["risk_score"] = "equal", None
    patch = [{"path": "/allocation/weighting", "value": "equal"}, {"path": "/risk_score", "value": None}]
    return {"risk_increment_identified": False, "cross_round_single_change": False,
            "changed_domains": ["risk", "selection_scope"], "parent_run_id": "generated_parent",
            "strategy_json": serial(expected if mode == "v7" else {}),
            "changes_json": serial([] if mode == "v7" else patch), "reason": "explicit fake spec materialization"}


def fake_transport(monkeypatch, *, verified=True, usage=None):
    from quanta_agents.meta_v6 import gateway
    state = {"calls": 0, "verified": verified}

    class FakeGateway:
        def __init__(self, **kwargs):
            assert 1 <= kwargs["timeout_seconds"] <= 900

        def run(self, **kwargs):
            state["calls"] += 1
            folder = Path(kwargs["workdir"])
            folder.mkdir(parents=True, exist_ok=True)
            folder.joinpath("prompt.txt").write_text(kwargs["prompt"], encoding="utf-8", newline="\n")
            mode = folder.parent.name.rsplit("_", 1)[1]
            receipt = {"model": "gpt-6-astra", "effort": "xhigh",
                "runtime_identity": {"verified": state["verified"], "level": "fake_fixture_only"},
                "response": _response(kwargs["schema"], mode),
                "usage": {"input_tokens": 11, "output_tokens": 3, "reasoning_output_tokens": 1,
                          "cached_input_tokens": 0} if usage is None else usage}
            folder.joinpath("fake_receipt.json").write_text(serial(receipt), encoding="utf-8")
            return deepcopy(receipt)

    def saved(folder):
        receipt = json.loads(Path(folder).joinpath("fake_receipt.json").read_text(encoding="utf-8"))
        receipt["runtime_identity"]["verified"] = state["verified"]
        return receipt

    def capture(*args, **kwargs):
        if not state["verified"]:
            raise ValueError("fake identity capture temporarily unavailable")

    monkeypatch.setattr(gateway, "CodexGateway", FakeGateway)
    monkeypatch.setattr(gateway, "verify_saved_completion", saved)
    monkeypatch.setattr(gateway, "capture_saved_session", capture)
    return state


def test_sparse_has_exactly_one_predeclared_training_day_not_all_missing(pilot, generated):
    for seed in pilot.SEEDS:
        _, report, hidden, _ = generated[(seed, "sparse")]
        for row in report["factors"].values():
            assert row["coverage"]["observed_cells"] == 32
            assert row["horizons"]["1"]["observed_days"] == 1
        assert report["interactions"][0]["horizons"]["1"]["raw_ic"]["observed_days"] == 1
        assert hidden["a"].shape == (120, 32)
        assert np.isfinite(hidden["a"]).all()
        assert np.isnan(hidden["labels"][-2:]).all()


def test_prepared_prompts_share_candidates_sources_and_exclude_hidden_truth(pilot, generated, prepared):
    intent = pilot.read(prepared / "intent.json")
    assert len(intent["cells"]) == 4
    assert intent["protocol"]["maximum_calls"] == 4 and intent["protocol"]["retries"] == 0
    assert intent["protocol"]["market_account_executions"] == 0
    schemas = []
    for cell in intent["cells"]:
        path = prepared / "cells" / cell["cell"]
        prompt = path.joinpath("frozen_prompt.txt").read_text(encoding="utf-8")
        assert len(prompt.encode("utf-8")) <= 32000
        assert not any(token in prompt for token in ('"expected":', '"seed":', '"kind":',
            '"labels":', '"weak_product_coefficient":', '"noise_sd":', "hidden_truth.json", ".npz"))
        if cell["kind"] == "generated":
            schema = pilot.read(path / "schema.json")
            schemas.append(schema)
            body = json.loads(prompt.rsplit("\n", 1)[1])
            assert {row["task_id"] for row in body} == {item[0] for item in generated.values()}
            for row in body:
                original = pilot.read(prepared / "common" / (row["task_id"] + ".json"))
                source = next(item[1] for item in generated.values() if item[0] == row["task_id"])
                assert original == source
    assert schemas[0] == schemas[1]
    assert not list(prepared.rglob("call_started.json"))


def test_generated_truth_direction_and_validation_value_are_separate(pilot, prepared):
    truths = pilot.read(prepared / "hidden_truth.json")
    rows = [{"task_id": truth["task_id"], "candidate_id": truth["expected"][0] if truth["expected"] else "abstain",
             "direction": 1, "reason": "known-truth test fixture, never sent to a model"} for truth in truths]
    positive = pilot._score_generated({"tasks": rows}, truths, prepared)
    negative = pilot._score_generated({"tasks": [{**r, "direction": -1} for r in rows]}, truths, prepared)
    for good, reversed_direction in zip(positive, negative):
        if good["expected"]:
            assert good["structural_source_match"] and reversed_direction["structural_source_match"]
            assert good["direction_correct"] and not reversed_direction["direction_correct"]
            assert good["discovery"] and not reversed_direction["discovery"]
            assert good["signed_validation_ic"] == pytest.approx(-reversed_direction["signed_validation_ic"])
        else:
            assert good["correct_abstention"] and good["signed_validation_ic"] is None
    malformed = deepcopy(rows)
    malformed[0]["task_id"] = malformed[1]["task_id"]
    with pytest.raises(ValueError, match="Missing/duplicate"):
        pilot._score_generated({"tasks": malformed}, truths, prepared)
    assert not list(prepared.rglob("call_started.json"))


def test_fake_transport_starts_four_calls_and_repeated_run_starts_none(pilot, prepared, monkeypatch):
    state = fake_transport(monkeypatch)
    first = pilot.run(prepared)
    assert state["calls"] == first["actual_calls_started"] == 4
    assert all(row["status"] == "admitted" for row in first["outcomes"])
    original = {p: p.read_bytes() for p in prepared.glob("cells/*/result.json")}
    second = pilot.run(prepared)
    assert state["calls"] == second["actual_calls_started"] == 4
    assert all(path.read_bytes() == raw for path, raw in original.items())
    report = pilot.read(prepared / "report.json")
    assert report["financial_success"] is False and report["new_market_accounts"] == 0
    assert all(t["usage_totals_are_complete"] for t in report["usage_totals"].values())


def test_failed_fake_identity_recovers_offline_and_preserves_original_failures(pilot, prepared, monkeypatch):
    state = fake_transport(monkeypatch, verified=False)
    first = pilot.run(prepared)
    assert state["calls"] == 4 and all(row["status"] == "failed" for row in first["outcomes"])
    originals = {p: p.read_bytes() for p in prepared.glob("cells/*/result.json")}
    state["verified"] = True
    recovered = pilot.recover(prepared)
    assert state["calls"] == 4 and all(row["status"] == "admitted" for row in recovered["outcomes"])
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    for path in prepared.glob("cells/*/recovery_result.json"):
        assert pilot.read(path)["new_model_calls"] == 0
        assert pilot.read(path)["initial_failure_retained"] is True
    assert len(list(prepared.glob("cells/*/recovery_result.json"))) == 4
    pilot.recover(prepared)
    pilot.run(prepared)
    assert state["calls"] == 4


def test_saved_verified_receipt_without_terminal_result_resumes_without_dispatch(pilot, prepared, monkeypatch):
    state = fake_transport(monkeypatch)
    original_once = pilot.once

    class SimulatedCrash(BaseException):
        pass

    def crash_before_terminal(path, value):
        path = Path(path)
        if path.name == "result.json" and path.parent.name == "01_generated_v7":
            raise SimulatedCrash("generated crash after verified receipt, before terminal persistence")
        return original_once(path, value)

    monkeypatch.setattr(pilot, "once", crash_before_terminal)
    with pytest.raises(SimulatedCrash):
        pilot.run(prepared)
    folder = prepared / "cells" / "01_generated_v7"
    assert state["calls"] == 1 and not folder.joinpath("result.json").exists()
    before = folder.joinpath("verified_receipt.json").read_bytes()
    monkeypatch.setattr(pilot, "once", original_once)
    result = pilot.run(prepared)
    assert state["calls"] == 4 and all(row["status"] == "admitted" for row in result["outcomes"])
    assert folder.joinpath("verified_receipt.json").read_bytes() == before
    resumed = pilot.read(folder / "result.json")
    assert resumed["seconds"] is None and resumed["offline_recovery_seconds"] >= 0


def test_exclusive_runner_lock_prevents_second_dispatch(pilot, prepared, monkeypatch):
    state = fake_transport(monkeypatch)
    with exclusive_lock(prepared / "pilot.lock"):
        with pytest.raises(RuntimeError, match="live owner"):
            pilot.run(prepared)
    assert state["calls"] == 0


def test_unknown_usage_is_marked_incomplete_not_presented_as_free(pilot, prepared, monkeypatch):
    state = fake_transport(monkeypatch, usage={})
    pilot.run(prepared)
    assert state["calls"] == 4
    totals = pilot.read(prepared / "report.json")["usage_totals"]
    for value in totals.values():
        assert value["unknown_usage_cells"] == 2
        assert value["usage_totals_are_complete"] is False
        assert "known subtotal" in value["token_sum_semantics"]


def test_edited_frozen_prompt_blocks_before_any_fake_transport(pilot, prepared, monkeypatch):
    state = fake_transport(monkeypatch)
    path = prepared / "cells/01_generated_v7/frozen_prompt.txt"
    path.write_text(path.read_text(encoding="utf-8") + "changed fixture", encoding="utf-8")
    with pytest.raises(ValueError, match="Frozen source/input changed"):
        pilot.run(prepared)
    assert state["calls"] == 0


def test_report_cannot_reveal_validation_before_all_cells_are_terminal(pilot, prepared):
    with pytest.raises(ValueError, match="terminal"):
        pilot.report(prepared)
    assert not prepared.joinpath("report.json").exists()
