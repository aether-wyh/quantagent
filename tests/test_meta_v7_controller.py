"""Independent V7 stage-machine checks on generated panels, never market data."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v7.controller import V7ResearchKernel
from quanta_agents.research_kernel.store import serial


def generated_panel():
    dates = pd.bdate_range("2018-01-01", periods=220, name="date")
    columns = pd.Index([f"sh{600000+i}" for i in range(8)], name="stock")
    t, j = np.arange(len(dates))[:, None], np.arange(len(columns))[None, :]
    close = pd.DataFrame((10+j)*np.exp(np.cumsum(.0003+.003*np.sin(t/9+j), axis=0)), index=dates, columns=columns)
    previous = close.shift(1).fillna(close.iloc[0])
    opening = previous*(1+.0005*np.cos(t/7+j))
    fields = {"open": opening, "close": close, "high": np.maximum(close, opening)*1.005,
              "low": np.minimum(close, opening)*.995, "raw_open": opening.copy(), "raw_close": close.copy(),
              "raw_prev_close": previous, "volume": close*0+1e6, "amount": close*0+1e8,
              "adjustment_factor": close*0+1, "open_observed": close*0+1,
              "is_st": close*0, "is_delisting": close*0}
    return MarketPanel(fields, close.notna(), {"fixture_only": True, "financial_source": "generated"})


def initialize(tmp_path, *, study="first", project=None, budget=None, mode="exposed_temporal", prior=None):
    panel = generated_panel()
    kernel = V7ResearchKernel(tmp_path / study)
    day = lambda i: str(panel.dates[i].date())
    config = {"study_id": study, "project_root": str(project or tmp_path / "project"),
        "split_plan": {"train_start": day(125), "train_end": day(179), "validation_start": day(186),
                       "validation_end": day(219), "embargo_sessions": 6, "max_label_horizon": 5},
        "budget": {"max_context_bytes": 120000, "max_model_calls": 8, **(budget or {})},
        "account_policy": {"capital": 100000., "lot_size": 1}, "validation_mode": mode,
        "prior_exposures": prior or []}
    kernel.initialize(config, panel)
    for key, expression in {"F1": "close", "F2": "pct_change(close,3)", "weak": "close*0+1",
                            "bad": "unavailable_source_field"}.items():
        kernel.assets.register({"id": key, "expression": expression, "roles": ["return", "condition"],
                                "metadata": {"fixture_only": True, "prior_ic": 0}})
    return kernel, panel, config


def strategy(name="test", factor="F1"):
    return {"name": name, "score": {"op": "factor", "id": factor},
            "allocation": {"top_n": 3, "max_stock_weight": .3, "rebalance_sessions": 5}}


def factors_done(kernel, panel, ids=None):
    registered = kernel.evaluate_factors(ids or ["F1", "weak"], horizons=[5])
    finished = kernel.execute_pending(panel)
    assert finished["stages"][0]["status"] == "completed", finished
    row = kernel.store.rows("SELECT * FROM factor_jobs WHERE id=?", (registered["job_id"],))[0]
    return row, kernel.store.evidence(row["evidence_id"], max_bytes=2000000, limit=100)["value"]


def batch_done(kernel, panel, spec=None):
    factors_done(kernel, panel)
    batch = kernel.submit_batch([spec or strategy()], controls=[])
    finished = kernel.execute_pending(panel)
    assert finished["stages"][0]["status"] == "completed", finished
    return batch, batch["attempts"][0]["run_id"]


def test_factor_stage_must_finish_before_portfolio_and_null_ic_has_no_gate(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    with pytest.raises(ValueError, match="Evaluate these factors"):
        kernel.submit_batch([strategy(factor="weak")])
    job = kernel.evaluate_factors(["weak"], horizons=[5])
    with pytest.raises(ValueError, match="Evaluate these factors"):
        kernel.submit_batch([strategy(factor="weak")])
    assert kernel.status()["executions"] == 0 and kernel.status()["attempts"] == 0
    kernel.execute_pending(panel)
    report = kernel.store.evidence(kernel.factor_evidence()["weak"], max_bytes=2000000, limit=100)["value"]
    assert report["factors"]["weak"]["horizons"]["5"]["mean_ic"] is None
    assert report["factors"]["weak"]["coverage"]["observed_cells"] > 0
    accepted = kernel.submit_batch([strategy(factor="weak")])
    assert accepted["attempts"][0]["status"] == "queued"
    assert kernel.status()["executions"] == 0  # Selection does not execute accounts inline.
    assert kernel.evaluate_factors(["weak"], horizons=[5])["reused"]
    assert len(kernel.store.rows("SELECT * FROM factor_jobs")) == 1


def test_account_failure_retains_discoverable_factor_and_failure_evidence(tmp_path, monkeypatch):
    from quanta_agents.meta_v7 import execution
    kernel, panel, _ = initialize(tmp_path)
    factor_row, report = factors_done(kernel, panel)
    batch = kernel.submit_batch([strategy()])
    run_id = batch["attempts"][0]["run_id"]
    monkeypatch.setattr(execution, "execute_strategy", lambda *a, **kw: (_ for _ in ()).throw(ValueError("generated account failure")))
    outcome = kernel.execute_pending(panel)
    assert outcome["stages"][0]["status"] == "failed"
    links = kernel.store.rows("SELECT * FROM stage_evidence WHERE stage_id=?", (run_id,))
    assert {r["kind"] for r in links} == {"factor_lab", "stage_failure"}
    assert factor_row["evidence_id"] in {r["evidence_id"] for r in links}
    row = kernel.store.rows("SELECT * FROM runs WHERE id=?", (run_id,))[0]
    failure = kernel.store.evidence(row["evidence_id"], limit=100)["value"]
    assert failure["message"] == "generated account failure"
    assert failure["retained_evidence"][0]["evidence_id"] == factor_row["evidence_id"]
    assert kernel.project.summary()["failed_attempts"] == 1


def test_batch_review_required_and_failed_branches_remain_in_next_round(tmp_path, monkeypatch):
    from quanta_agents.meta_v7 import execution
    kernel, panel, _ = initialize(tmp_path)
    factors_done(kernel, panel)
    first = kernel.submit_batch([strategy()])
    with pytest.raises(ValueError, match="Review the preceding"):
        kernel.submit_batch([strategy("second", "weak")])
    with pytest.raises(ValueError, match="finished batch"):
        kernel.review_batch(first["batch_id"], "revise", "not finished")
    monkeypatch.setattr(execution, "execute_strategy", lambda *a, **kw: (_ for _ in ()).throw(ValueError("retained branch failure")))
    kernel.execute_pending(panel)
    review = kernel.review_batch(first["batch_id"], "revise", "failure falsifies feasibility; test declared weak condition")
    assert kernel.review_batch(first["batch_id"], "revise", review["conclusion"]) == review
    with pytest.raises(ValueError, match="immutable"):
        kernel.review_batch(first["batch_id"], "reject", "rewritten conclusion")
    second = kernel.submit_batch([strategy("second", "weak")])
    assert second["attempts"][0]["status"] == "queued"
    assert kernel.store.rows("SELECT status FROM attempts WHERE batch_id=?", (first["batch_id"],))[0]["status"] == "failed"


def test_cross_project_exposure_blocks_independent_validation_before_values(tmp_path):
    kernel, panel, config = initialize(tmp_path, mode="independent_required")
    batch, run_id = batch_done(kernel, panel)
    kernel.project.register_study("older", {})
    plan = config["split_plan"]
    kernel.project.record_exposure("older", start=plan["validation_start"], end=plan["validation_end"],
        role="development", evidence_id="old-read", reason="old diagnostic observation")
    with pytest.raises(ValueError, match="Independent validation blocked"):
        kernel.review_batch(batch["batch_id"], "freeze_for_validation", "fixed training choice", run_id)
    assert kernel.store.rows("SELECT * FROM validation_jobs") == []


def test_freeze_for_validation_blocks_new_factor_tests_and_selection(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    batch, run_id = batch_done(kernel, panel)
    review = kernel.review_batch(batch["batch_id"], "freeze_for_validation", "freeze one training candidate", run_id)
    assert review["validation_job_id"]
    with pytest.raises(ValueError, match="new training|Validation is unlocked"):
        kernel.evaluate_factors(["F2"], horizons=[5])
    with pytest.raises(ValueError, match="frozen for validation"):
        kernel.submit_batch([strategy("cannot reselect", "weak")])


def test_exposure_added_after_queue_is_rechecked_before_validation_read(tmp_path, monkeypatch):
    from quanta_agents.meta_v7 import validation
    kernel, panel, config = initialize(tmp_path, mode="independent_required")
    batch, run_id = batch_done(kernel, panel)
    kernel.review_batch(batch["batch_id"], "freeze_for_validation", "candidate fixed before later exposure", run_id)
    kernel.project.register_study("concurrent", {})
    plan = config["split_plan"]
    kernel.project.record_exposure("concurrent", start=plan["validation_start"], end=plan["validation_end"],
        role="training", evidence_id="later-read", reason="intervening study exposure")
    called = []
    monkeypatch.setattr(validation, "evaluate_frozen_candidates", lambda *a, **kw: called.append(True))
    outcome = kernel.execute_pending(panel)
    assert not called
    assert outcome["stages"][0]["status"] == "failed"
    assert "Independent validation blocked" in outcome["stages"][0]["error"]["message"]


def test_training_boundary_is_frozen_despite_poisoned_later_panel_values(tmp_path):
    kernel, panel, config = initialize(tmp_path)
    modified = deepcopy(panel)
    for frame in modified.fields.values():
        frame.loc[frame.index > config["split_plan"]["train_end"]] = 99999999
    _, report = factors_done(kernel, modified, ["F1"])
    assert report["scope"]["end"] == config["split_plan"]["train_end"]
    assert report["scope"]["validation_values_returned"] is False
    assert kernel.status()["executions"] == 0


def test_changed_frozen_identity_blocks_validation_before_exposure_or_full_panel_read(tmp_path, monkeypatch):
    from quanta_agents.meta_v7 import controller, validation
    kernel, panel, config = initialize(tmp_path)
    batch, run_id = batch_done(kernel, panel)
    frozen = kernel.review_batch(batch["batch_id"], "freeze_for_validation", "frozen generated training result", run_id)
    job_id = frozen["validation_job_id"]
    exposure_count = kernel.project.summary()["exposures"]
    budgets = kernel.store.rows("SELECT * FROM account_budget")
    original_identity = kernel._identity
    def changed_identity(spec):
        value = original_identity(spec)
        value["changed_engine_fixture"] = True
        return value
    monkeypatch.setattr(kernel, "_identity", changed_identity)
    monkeypatch.setattr(kernel.project, "begin_validation",
        lambda *a, **kw: pytest.fail("identity mismatch reached exposure admission"))
    monkeypatch.setattr(validation, "evaluate_frozen_candidates",
        lambda *a, **kw: pytest.fail("identity mismatch executed validation"))
    original_scope = controller.scope_panel
    scopes = []
    def training_only(source, *, end):
        scopes.append(end)
        assert end == config["split_plan"]["train_end"], "identity mismatch read full validation panel"
        return original_scope(source, end=end)
    monkeypatch.setattr(controller, "scope_panel", training_only)
    outcome = kernel.execute_pending(panel)
    assert scopes == [config["split_plan"]["train_end"]]
    assert outcome["stages"][0]["status"] == "failed"
    assert outcome["stages"][0]["error"]["message"] == "Frozen training engine or formula changed before validation"
    row = kernel.store.rows("SELECT * FROM validation_jobs WHERE id=?", (job_id,))[0]
    assert row["status"] == "failed" and row["evidence_id"] and row["error"]
    failure = kernel.store.evidence(row["evidence_id"], limit=100)["value"]
    assert failure["message"] == json.loads(row["error"])["message"]
    assert kernel.project.summary()["exposures"] == exposure_count
    assert kernel.store.rows("SELECT * FROM account_budget") == budgets


def test_account_identity_reuse_is_preserved_but_global_attempt_count_is_not_reset(tmp_path):
    kernel, panel, _ = initialize(tmp_path)
    batch, run_id = batch_done(kernel, panel)
    kernel.review_batch(batch["batch_id"], "revise", "test a metadata-only rename to verify reuse accounting")
    reused = kernel.submit_batch([strategy("renamed")])
    assert reused["attempts"][0]["run_id"] == run_id and reused["attempts"][0]["reused"]
    summary = kernel.project.summary()
    assert summary["total_attempts"] == 3  # factor test and two portfolio attempts
    assert summary["unique_economic_trials"] == 2
    assert summary["reuse_attempts"] == 1 and summary["independent_sample_count"] is None
