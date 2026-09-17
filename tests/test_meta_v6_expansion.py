"""Synthetic closure files and mocked library/gateway; no real research calls."""
from copy import deepcopy
from pathlib import Path
import json

import pandas as pd
import pytest

from quanta_agents.meta_v6 import expansion, gateway


def write(path, value):
    expansion.save_once(path, value)


def change(path, operation):
    value = expansion.read(path)
    operation(value)
    path.write_text(expansion.dump(value), encoding="utf8")


def proof(path):
    return {"path": str(path), "sha256": expansion.file_hash(path), "bytes": path.stat().st_size}


def factor(name="synthetic_new", **changes):
    return {"name": name, "expression": "rolling_std(pct_change(close,1),20)",
        "direction": -1, "primary_horizon": 5, "role": "risk_information",
        "hypothesis": "SYNTHETIC hypothesis before factor values", "incremental_role": "SYNTHETIC distinct risk information",
        "falsification": "SYNTHETIC no increment or unstable effect", **changes}


@pytest.fixture(autouse=True)
def never_dispatch_real_gateway(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("unmocked real model call is forbidden")
    monkeypatch.setattr(gateway, "CodexGateway", forbidden)


def setup(tmp_path, monkeypatch, factors=None):
    workspace = tmp_path / "workspace"
    root = workspace / "synthetic_research"
    old = root / "cycles" / expansion.PRIOR_CYCLE
    monkeypatch.setattr(expansion, "ROOT", workspace)
    write(workspace / "experiments/factor_calendar_daily_hf0280_research_sharpe15.yaml", {"synthetic": "original formula"})
    write(root / "protocol.json", deepcopy(expansion.PROTOCOL))
    declarations = [{"factor_key": "HF" + str(i), "origin": "original_seed",
        "original": {"name": "seed" + str(i), "expression": f"rolling_mean(close,{10+i})", "direction": 1}}
        for i in range(3)] + [{"factor_key": "F" + str(i), "origin": "admitted_model_hypothesis",
        "original": {"name": "old" + str(i), "expression": f"pct_change(close,{i})", "direction": 1}}
        for i in range(1, 7)]
    write(root / "factor_declaration.json", {"declarations": declarations, "input_library_snapshot_id": "old-library"})
    view = {"2021_2024_result_values_included": False, "marker": "SYNTHETIC_FIT_FACTOR_VIEW",
        "scope": {"date_range": ["2016-01-01", "2020-12-31"], "purged_signal_sessions": 21},
        "factors": [{"factor_key": row["factor_key"], "name": row["original"]["name"],
            "expression": row["original"]["expression"], "direction": row["original"]["direction"],
            "status": "evaluated"} for row in declarations]}
    write(root / "fit_factor_view.json", view)
    write(root / "factor_index.json", {"status": "completed", "factor_count": 9, "evaluated": 9, "failed": 0,
        "factors": deepcopy(view["factors"]), "library_snapshot_id": "old-library", "source_proofs": [],
        "factor_declaration_sha256": expansion.file_hash(root / "factor_declaration.json"),
        "fit_factor_view_sha256": expansion.file_hash(root / "fit_factor_view.json")})
    write(root / "preparation/hf0280_source_registration.json", {"market_value_arrays_read": False,
        "registration_id": "synthetic-metadata-registration", "fields": ["gu_1m", "gd_1m", "rbar_up17", "rbar_down17", "r_0931_1000", "r_1001_1030", "overnight_return"],
        "start": "2015-01-01", "end": "2024-12-31", "metadata_summary": {"universe_symbols": 648,
            "files_containing_each_field": {"gu_1m": 626}}, "numeric_admission_required": True})
    reject = {"runtime_identity": {"verified": True}, "response": {"decisions": [
        {"candidate": key, "decision": "reject", "reason": "SYNTHETIC original failure"} for key in "ABCD"]}}
    write(root / "model_calls/02_combination_admission/admitted_receipt.json", reject)
    write(root / "account_stage_result.json", {"status": "no_admitted_combination", "decisions": reject["response"]["decisions"]})
    archive = root / "preparation/source_archive_before_target_serialization_fix"
    archived = []
    for name in ("cycle_execution.py", "cycles.py", "portfolio.py", "portfolio_study.py", "data.py", "research.py", "temporal.py"):
        original, saved = workspace / "old_sources" / name, archive / name
        write(original, {"synthetic_source": name})
        write(saved, {"synthetic_source": name})
        archived.append({"original_path": str(original), "archive_path": str(saved), "sha256": expansion.file_hash(original), "bytes": original.stat().st_size})
    write(archive / "manifest.json", {"source_files": archived, "financial_outputs_modified": False})
    inputs = [proof(root / name) for name in ("protocol.json", "factor_declaration.json", "factor_index.json", "fit_factor_view.json", "account_stage_result.json", "model_calls/02_combination_admission/admitted_receipt.json")]
    inputs += [proof(Path(row["original_path"])) for row in archived]
    policies = {key: {k: val for k, val in expansion.PROTOCOL["account"].items() if k not in ("signal", "execution", "accounting", "missing", "terminal")}
                for key in ("base", "slippage_x2", "capacity_half")}
    policies["slippage_x2"]["slippage"] *= 2
    policies["capacity_half"]["max_prior_day_amount_fraction"] /= 2
    write(old / "account_execution_intent.json", {"scope": ["2016-01-01", "2020-12-31"],
        "input_artifacts": inputs, "policies": policies, "maximum_new_accounts": 6})
    write(old / "raw_fit.json", {"synthetic_retained_failure": "R1 failed slippage, R2 passed training"})
    fit_artifacts = [proof(old / "raw_fit.json")]
    for stress in policies:
        fit_daily = old / "accounts/fit/R2" / stress / "daily.parquet"
        write(fit_daily, {"synthetic_only_hash_artifact": stress})
        fit_artifacts.append(proof(fit_daily))
    training = [{"candidate": "R1", "stress_feasible": False}, {"candidate": "R2", "stress_feasible": True}]
    selection = {"status": "completed", "selected": "R2", "cumulative_portfolio_proposals": 6,
        "training_observations": training, "artifacts": fit_artifacts,
        "intent_sha256": expansion.file_hash(old / "account_execution_intent.json"),
        "frozen_before_temporal_results": True, "financial_success": False}
    write(old / "selection.json", selection)
    write(old / "account_stage_result.json", selection)
    temporal_intent = {"scope": ["2016-01-01", "2024-12-31"], "fit_comparison": ["2016-01-01", "2020-12-31"],
        "temporal_segment": ["2021-01-01", "2024-12-31"], "selected": "R2", "policies": policies,
        "selection_sha256": expansion.file_hash(old / "selection.json"),
        "input_artifacts": inputs + [proof(old / "selection.json"), proof(old / "account_execution_intent.json")],
        "maximum_new_accounts": 3, "winner_reselected": False, "annual_account_reset": False}
    write(old / "temporal_intent.json", temporal_intent)
    write(old / "raw_temporal.json", {"synthetic_retained_failure": "SYNTHETIC_LATER_FAILURE_MARKER"})
    observations = {stress: {"fit_prefix_check": {"passed": True, "all_fields_exact": True, "sessions": 1218},
        "full_continuous_account": {"formal_target_success": False, "sessions": 2187, "full_years": 9,
            "all_full_year_sharpes_available": True, "mean_full_year_sharpe": .1, "threshold_exceeded_on_supplied_simulation": False},
        "annual": [{"year": y, "sharpe": .1, "full_calendar_year": True, "calendar_complete": True} for y in range(2016, 2025)],
        "temporal_2021_2024": {"summary": {"marker": "SYNTHETIC_LATER_FAILURE_MARKER", "mean_full_year_sharpe": -.3,
            "account_restarted": False, "independent_holdout": False, "sessions": 969}, "annual": []}}
        for stress in ("base", "slippage_x2", "capacity_half")}
    temporal_artifacts = [proof(old / "raw_temporal.json")]
    for stress, observation in observations.items():
        account = old / "accounts/temporal/R2" / stress
        observation["fit_prefix_check"]["saved_fit_daily_sha256"] = expansion.file_hash(old / "accounts/fit/R2" / stress / "daily.parquet")
        write(account / "prefix_check.json", observation["fit_prefix_check"])
        write(account / "summary.json", observation["full_continuous_account"])
        write(account / "policy.json", policies[stress])
        pd.DataFrame(observation["annual"]).to_parquet(account / "annual.parquet")
        temporal_artifacts += [proof(account / name) for name in ("prefix_check.json", "summary.json", "policy.json", "annual.parquet")]
    write(old / "temporal_stage_result.json", {"status": "completed", "selected": "R2", "winner_reselected": False,
        "selection_sha256": expansion.file_hash(old / "selection.json"), "intent_sha256": expansion.file_hash(old / "temporal_intent.json"),
        "annual_account_reset": False, "new_account_executions": 3, "financial_success": False,
        "formal_target_success": False, "independent_holdout": False, "artifacts": temporal_artifacts, "observations": observations})
    for name in ("01_account_execution", "02_temporal_execution"):
        write(old / "jobs" / name / "job_result.json", {"status": "completed", "all_owned_processes_exited": True, "primary_exit_code": 0})
    original_bytes = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    exposures, calls, paid = [], [], []
    class Library:
        def __init__(self, path):
            assert Path(path).is_relative_to(workspace)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def record_exposure(self, **kwargs):
            exposures.append(kwargs)
            return "synthetic-exposure-1"
    monkeypatch.setattr(expansion, "FactorLibrary", Library)
    proposed = [factor()] if factors is None else factors
    def researcher(path, stage, prompt, schema):
        assert path == root and stage == expansion.CALL
        calls.append({"prompt": prompt, "schema": deepcopy(schema)})
        folder = root / "model_calls" / stage
        binding = {"prompt": prompt, "schema": schema}
        if (folder / "admitted_receipt.json").exists():
            assert expansion.read(folder / "synthetic_binding.json") == binding
            return expansion.read(folder / "admitted_receipt.json")
        paid.append(stage)
        response = {"diagnosis": "SYNTHETIC failure diagnosis", "competing_explanations": "SYNTHETIC competing hypotheses",
            "factors": deepcopy(proposed), "hf0280_review": "original fixed seed, no observed alpha",
            "application_diagnostics_to_run": "future tests, not run", "future_combination_principles": "factor evidence first",
            "selection_and_stopping": "fixed stage controls"}
        receipt = {"runtime_identity": {"verified": True}, "model": "gpt-6-astra", "effort": "xhigh", "response": response}
        write(folder / "synthetic_binding.json", binding)
        write(folder / "admitted_receipt.json", receipt)
        return receipt
    monkeypatch.setattr(expansion, "call_researcher", researcher)
    return root, old, calls, paid, exposures, original_bytes


def assert_originals(root, original):
    assert {name: (root / name).read_bytes() for name in original} == original


@pytest.mark.parametrize("count", [0, 1, 3])
def test_prior_failures_counts_hf_seed_exposure_and_factor_first_contract(tmp_path, monkeypatch, count):
    values = [factor("new" + str(i), expression=f"rolling_std(pct_change(close,1),{20+i})") for i in range(count)]
    root, old, calls, paid, exposures, original = setup(tmp_path, monkeypatch, values)
    declaration = expansion.propose_expansion(root)
    protocol = expansion.read(root / "cycles" / expansion.CYCLE / "protocol.json")
    assert declaration["fixed_seeds"] == [expansion.HF0280_SEED]
    assert declaration["new_model_factor_hypotheses"] == count
    assert declaration["prior_model_factor_hypotheses_retained"] == 6
    assert declaration["cumulative_model_factor_hypotheses"] == 6 + count
    assert declaration["new_portfolio_proposals"] == 0
    assert declaration["new_evaluation_results_seen_before_declaration"] is False
    assert protocol["prior_observations"]["previous_proposals_retained"] == 6
    assert protocol["prior_factors_evaluated"] == 9 and protocol["prior_model_factor_hypotheses"] == 6
    assert protocol["factor_evaluations_max"] == 4 and protocol["new_model_factor_hypotheses_max"] == 3
    assert protocol["new_portfolio_proposals_before_factor_results"] == 0
    assert protocol["new_2025_numeric_data_allowed"] is False and protocol["independent_holdout"] is False
    assert protocol["numeric_scope"] == ["2015-01-01", "2024-12-31"]
    assert protocol["model_factor_selection_view"] == ["2016-01-01", "2020-12-31"]
    assert protocol["purge_signal_sessions_at_fit_end"] == 21
    assert len(exposures) == len(paid) == 1
    assert exposures[0]["results_revealed"] is True and exposures[0]["used_for_selection"] is True
    assert "SYNTHETIC_LATER_FAILURE_MARKER" in calls[0]["prompt"]
    assert "SYNTHETIC_FIT_FACTOR_VIEW" in calls[0]["prompt"]
    assert "not" in calls[0]["prompt"] and "independent" in calls[0]["prompt"]
    assert "TIME-SERIES" in calls[0]["prompt"] and "2025" in calls[0]["prompt"]
    assert declaration["source_receipt_sha256"] == expansion.file_hash(root / "model_calls" / expansion.CALL / "admitted_receipt.json")
    assert_originals(root, original)


def test_schema_has_only_factor_declaration_and_fixed_bounded_choices():
    assert expansion.SCHEMA["additionalProperties"] is False
    assert expansion.SCHEMA["properties"]["factors"]["maxItems"] == 3
    fields = expansion.NEW_FACTOR_SCHEMA["properties"]
    assert fields["primary_horizon"]["enum"] == [1, 5, 20]
    assert fields["direction"]["enum"] == [-1, 1]
    assert set(fields["role"]["enum"]) == {"return_prediction", "risk_information", "conditional_gate"}
    assert "portfolios" not in expansion.SCHEMA["properties"]


def test_repeat_proposal_uses_same_gateway_binding_and_one_paid_dispatch(tmp_path, monkeypatch):
    root, _, calls, paid, exposures, original = setup(tmp_path, monkeypatch)
    first = expansion.propose_expansion(root)
    second = expansion.propose_expansion(root)
    assert first == second and len(paid) == len(exposures) == 1
    assert calls[0] == calls[-1]
    assert_originals(root, original)


@pytest.mark.parametrize("problem", ["job_running", "job_child_live", "winner", "reselected", "stresses", "prefix", "raw_changed", "fit_changed", "protocol_2025", "registration_numeric"])
def test_invalid_closed_evidence_refuses_before_gateway(tmp_path, monkeypatch, problem):
    root, old, calls, paid, _, _ = setup(tmp_path, monkeypatch)
    if problem == "job_running": change(old / "jobs/02_temporal_execution/job_result.json", lambda x: x.update(status="running"))
    elif problem == "job_child_live": change(old / "jobs/02_temporal_execution/job_result.json", lambda x: x.update(all_owned_processes_exited=False))
    elif problem == "winner": change(old / "temporal_stage_result.json", lambda x: x.update(selected="R1"))
    elif problem == "reselected": change(old / "temporal_stage_result.json", lambda x: x.update(winner_reselected=True))
    elif problem == "stresses": change(old / "temporal_stage_result.json", lambda x: x["observations"].pop("capacity_half"))
    elif problem == "prefix": change(old / "temporal_stage_result.json", lambda x: x["observations"]["base"]["fit_prefix_check"].update(all_fields_exact=False))
    elif problem == "raw_changed": (old / "raw_temporal.json").write_text("changed synthetic bytes", encoding="utf8")
    elif problem == "fit_changed": change(root / "fit_factor_view.json", lambda x: x.update(marker="changed"))
    elif problem == "protocol_2025": change(root / "protocol.json", lambda x: x["data"].update(end="2025-12-31"))
    elif problem == "registration_numeric": change(root / "preparation/hf0280_source_registration.json", lambda x: x.update(market_value_arrays_read=True))
    with pytest.raises(ValueError): expansion.propose_expansion(root)
    assert calls == paid == []


def test_more_than_three_preserves_original_response_without_admitting(tmp_path, monkeypatch):
    root, _, _, paid, _, original = setup(tmp_path, monkeypatch, [factor(str(i)) for i in range(4)])
    with pytest.raises(ValueError): expansion.propose_expansion(root)
    assert len(paid) == 1
    assert len(expansion.read(root / "model_calls" / expansion.CALL / "admitted_receipt.json")["response"]["factors"]) == 4
    assert not (root / "cycles" / expansion.CYCLE / "factor_declaration.json").exists()
    assert_originals(root, original)


@pytest.mark.parametrize("expression", ["gu_1m", expansion.HF0280_FIELD, "unknown_signal", "stock_id", "calendar_year", "raw_close", "lag(close,-1)"])
def test_new_factors_cannot_bypass_six_field_contract_or_rename_fixed_hf(tmp_path, monkeypatch, expression):
    root, _, _, _, _, original = setup(tmp_path, monkeypatch, [factor(expression=expression)])
    with pytest.raises(ValueError): expansion.propose_expansion(root)
    assert not (root / "cycles" / expansion.CYCLE / "factor_declaration.json").exists()
    assert_originals(root, original)


@pytest.mark.parametrize("problem", ["intent", "reset", "prefix_passed", "prefix_count", "old_factor_count"])
def test_semantic_closure_bindings_and_trial_counts_cannot_be_self_reported(tmp_path, monkeypatch, problem):
    root, old, calls, _, _, _ = setup(tmp_path, monkeypatch)
    if problem == "intent": change(old / "temporal_intent.json", lambda x: x.update(scope=["2021-01-01", "2024-12-31"]))
    elif problem == "reset": change(old / "temporal_stage_result.json", lambda x: x.update(annual_account_reset=True))
    elif problem == "prefix_passed": change(old / "temporal_stage_result.json", lambda x: x["observations"]["base"]["fit_prefix_check"].update(passed=False))
    elif problem == "prefix_count": change(old / "temporal_stage_result.json", lambda x: x["observations"]["base"]["fit_prefix_check"].update(sessions=1217))
    elif problem == "old_factor_count": change(root / "factor_declaration.json", lambda x: x["declarations"].pop())
    with pytest.raises(ValueError): expansion.propose_expansion(root)
    assert calls == []


def test_frozen_source_change_refuses_without_touching_real_source_or_gateway(tmp_path, monkeypatch):
    root, _, calls, paid, _, _ = setup(tmp_path, monkeypatch)
    expansion.initialize_expansion(root)
    original_hash = expansion.file_hash
    def changed_hash(path):
        return "a" * 64 if Path(path).name == "cross_sectional.py" else original_hash(path)
    monkeypatch.setattr(expansion, "file_hash", changed_hash)
    with pytest.raises(ValueError): expansion.propose_expansion(root)
    assert calls == paid == []


def test_prior_and_same_generation_duplicates_are_explicit_trials_not_new_discovery(tmp_path, monkeypatch):
    proposed = [factor("repeated_old", expression="pct_change( close, 1 )"),
                factor("repeated_again", expression="pct_change(close,1)")]
    root, _, _, paid, _, original = setup(tmp_path, monkeypatch, proposed)
    declaration = expansion.propose_expansion(root)
    attempts = declaration["trial_registration"]
    assert [row["status"] for row in attempts] == ["duplicate", "duplicate"]
    assert all(row["duplicate_of_prior_factor_keys"] == ["F1"] for row in attempts)
    assert attempts[0]["duplicate_of_new_indices"] == []
    assert attempts[1]["duplicate_of_new_indices"] == [0]
    assert attempts[0]["factor_id"] == attempts[1]["factor_id"]
    assert all(row["counts_as_hypothesis_attempt"] is True and row["prior_expression_evidence_already_seen"] is True for row in attempts)
    assert declaration["cumulative_model_factor_hypotheses"] == 8
    assert declaration["new_evaluation_results_seen_before_declaration"] is False
    assert declaration["model_factors"] == proposed and len(paid) == 1
    assert_originals(root, original)


@pytest.mark.parametrize("changes", [{"direction": True}, {"primary_horizon": True}, {"primary_horizon": 2}, {"role": "portfolio"}])
def test_application_guard_keeps_direction_horizon_and_role_inside_schema(tmp_path, monkeypatch, changes):
    root, _, _, _, _, original = setup(tmp_path, monkeypatch, [factor(**changes)])
    with pytest.raises(ValueError): expansion.propose_expansion(root)
    assert not (root / "cycles" / expansion.CYCLE / "factor_declaration.json").exists()
    assert_originals(root, original)


def test_repeated_new_names_cannot_alias_distinct_factor_attempts(tmp_path, monkeypatch):
    root, _, _, _, _, _ = setup(tmp_path, monkeypatch, [factor(), factor(expression="pct_change(close,10)")])
    with pytest.raises(ValueError, match="unique"):
        expansion.propose_expansion(root)


def test_changed_live_previous_source_is_allowed_only_with_exact_preserved_archive(tmp_path, monkeypatch):
    root, _, _, paid, _, _ = setup(tmp_path, monkeypatch)
    manifest = expansion.read(root / "preparation/source_archive_before_target_serialization_fix/manifest.json")
    Path(manifest["source_files"][0]["original_path"]).write_text("SYNTHETIC newly refactored live implementation", encoding="utf8")
    result = expansion.propose_expansion(root)
    assert result["new_portfolio_proposals"] == 0 and len(paid) == 1


def test_changed_archived_execution_source_is_rejected_before_model(tmp_path, monkeypatch):
    root, _, calls, paid, _, _ = setup(tmp_path, monkeypatch)
    manifest = expansion.read(root / "preparation/source_archive_before_target_serialization_fix/manifest.json")
    Path(manifest["source_files"][0]["archive_path"]).write_text("SYNTHETIC archive corruption", encoding="utf8")
    with pytest.raises(ValueError, match="archive"):
        expansion.propose_expansion(root)
    assert calls == paid == []
