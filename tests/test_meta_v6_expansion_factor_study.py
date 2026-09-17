"""Temporary generated panels, source files and library only; no real research."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quanta_agents.meta_v6 import expansion_factor_study as study
from quanta_agents.meta_v6.auxiliary import HF0280_FIELDS, register_auxiliary_source
from quanta_agents.meta_v6.data import BASE_FIELDS, MarketPanel, PanelError
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec
from quanta_agents.meta_v6.library import FactorLibrary
from quanta_agents.meta_v6.portfolio_study import file_hash, read
from quanta_agents.meta_v6.research import PROTOCOL, save_once


@pytest.fixture(autouse=True)
def forbid_real_work(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("test attempted real market/model/account access")
    monkeypatch.setattr(study, "load_panel", forbidden)
    from quanta_agents.meta_v6 import research, expansion, portfolio
    monkeypatch.setattr(research, "call_researcher", forbidden)
    monkeypatch.setattr(expansion, "call_researcher", forbidden)
    monkeypatch.setattr(portfolio.DailyAccount, "run", forbidden)


def hypothesis(name="new_risk", expression="rolling_std(pct_change(close,1),20)", direction=-1, role="return_prediction"):
    return {"name": name, "expression": expression, "direction": direction, "primary_horizon": 5,
        "role": role, "hypothesis": "generated mechanism", "incremental_role": "generated increment",
        "falsification": "generated falsification"}


def fixture(tmp_path, monkeypatch, *, models=None, missing_aux=False, future=False):
    root = tmp_path / "generated"
    folder = root / "cycles" / study.CYCLE
    library_path = root / "generated_library.sqlite"
    models = models if models is not None else [hypothesis(), hypothesis("new_timing", "rolling_mean(close/open-1,3)", 1)]
    dates = pd.DatetimeIndex(np.concatenate([
        pd.bdate_range("2015-11-02", periods=100).to_numpy(),
        pd.bdate_range("2020-10-01", "2020-12-31").to_numpy(),
        pd.bdate_range("2021-01-04", periods=25).to_numpy(),
        pd.bdate_range("2024-12-02", "2024-12-31").to_numpy(),
    ]), name="date")
    if future:
        dates = dates.append(pd.DatetimeIndex(["2025-01-02"]))
    columns = pd.Index([f"sh{600000+i}" for i in range(64)], name="symbol")
    rng = np.random.default_rng(3719)
    close = 20 * np.exp(np.cumsum(rng.normal(0, .01, (len(dates), 64)), axis=0))
    opening = close * np.exp(rng.normal(0, .003, close.shape))
    values = {"close": close, "open": opening, "high": np.maximum(close, opening) + .2,
              "low": np.minimum(close, opening) - .2, "volume": rng.uniform(1e5, 1e6, close.shape),
              "amount": rng.uniform(1e7, 1e8, close.shape), "open_observed": np.ones(close.shape)}
    panel = MarketPanel({k: pd.DataFrame(v, index=dates, columns=columns) for k, v in values.items()},
        pd.DataFrame(True, index=dates, columns=columns), {"source_class": "previously_exposed_development",
        "request": {"start": study.START, "end": study.END}, "causal_fields": list(BASE_FIELDS),
        "execution_only_fields": ["open_observed"], "generated": True})
    loaded = []
    def load(request_root):
        assert Path(request_root) == root
        loaded.append(str(request_root))
        return panel.copy()
    monkeypatch.setattr(study, "load_panel", load)
    save_once(root / "protocol.json", PROTOCOL)
    old_factors, old_fit = [], []
    with FactorLibrary(library_path) as library:
        for i in range(9):
            key = f"OLD{i+1}"
            spec = FactorSpec(key, f"pct_change(close,{i+1})")
            score = pd.DataFrame(rng.normal(size=close.shape), index=dates, columns=columns)
            path = root / "factors" / key / "scores.parquet"
            path.parent.mkdir(parents=True)
            score.to_parquet(path)
            attempt = library.record_attempt(spec, status="evaluated", scope={"generated_previous": True})
            library.record_exposure(attempt_id=attempt, scope={"generated_previous": True}, purpose="prior exposed evidence")
            old_factors.append({"factor_key": key, "factor_id": spec.factor_id, "name": key, "status": "evaluated",
                "data_fingerprint": "generated-original-engine", "scores_path": str(path),
                "artifacts": [{"path": str(path), "sha256": file_hash(path)}]})
            old_fit.append({"factor_key": key, "factor_id": spec.factor_id, "name": key, "status": "evaluated",
                            "direction": 1, "expression": spec.expression, "generated_prior_fit_marker": i})
        snapshot = library.create_snapshot(scope={"generated_previous": True})
        old_events = deepcopy(library.events())
    save_once(root / "fit_factor_view.json", {"factors": old_fit, "2021_2024_result_values_included": False})
    save_once(root / "factor_declaration.json", {"generated_prior_declaration": True})
    index = {"factors": old_factors, "scope": {"data_fingerprint": "generated-original-engine", "panel_fingerprint": panel.fingerprint()},
             "fit_factor_view_sha256": file_hash(root / "fit_factor_view.json"), "library_snapshot_id": snapshot,
             "factor_declaration_sha256": file_hash(root / "factor_declaration.json")}
    save_once(root / "factor_index.json", index)
    source_root = root / "auxiliary_generated_sources"
    source_root.mkdir()
    auxiliary_dates = dates if future else dates.append(pd.DatetimeIndex(["2025-01-02"]))
    for j, code in enumerate(columns):
        if j == len(columns) - 1 or missing_aux:
            continue
        frame = pd.DataFrame(rng.normal(size=(len(auxiliary_dates), 7)), columns=HF0280_FIELDS)
        frame["date"], frame["code"] = auxiliary_dates, code
        frame.loc[frame.date.ge("2025-01-01"), list(HF0280_FIELDS)] = 9e25
        frame.to_parquet(source_root / (code + ".parquet"), index=False)
    registry = register_auxiliary_source(source_root, symbols=list(columns), start=study.START, end=study.END,
        authorized_start=study.START, authorized_end=study.END, source_notes="generated fixture, no actual market observations")
    save_once(root / "preparation/hf0280_source_registration.json", registry)
    previous = root / "cycles" / study.PRIOR_CYCLE
    save_once(previous / "selection.json", {"generated_closed_previous_selection": True})
    save_once(previous / "temporal_stage_result.json", {"generated_closed_previous_temporal": True})
    save_once(folder / "model_exposure.json", {"generated_previous_exposure_preserved": True})
    save_once(folder / "prior_account_observations.json", {"generated_previous_results": True})
    archive = root / "preparation/source_archive_before_target_serialization_fix"
    archive.mkdir(parents=True, exist_ok=True)
    archived_source = archive / "generated_previous_source.py"
    archived_source.write_text("# generated preserved source\n", encoding="utf-8")
    save_once(archive / "manifest.json", {"source_files": [
        {"archive_path": str(archived_source), "sha256": file_hash(archived_source)}]})
    protocol = {"cycle_id": study.CYCLE, "prior_factors_evaluated": 9, "new_original_seed": study.HF0280_SEED,
        "new_model_factor_hypotheses_max": 3, "factor_evaluations_max": 4,
        "new_portfolio_proposals_before_factor_results": 0, "new_factor_windows_or_direction_sweeps": False,
        "numeric_scope": [study.START, study.END], "model_factor_selection_view": [study.FIT_START, study.FIT_END],
        "purge_signal_sessions_at_fit_end": 21, "factor_screen": PROTOCOL["factor_screen"],
        "new_2025_numeric_data_allowed": False, "independent_holdout": False, "automatic_retry": False, "financial_success": False,
        "prior_factor_index_sha256": file_hash(root / "factor_index.json"),
        "prior_fit_view_sha256": file_hash(root / "fit_factor_view.json"), "prior_library_snapshot_id": snapshot,
        "auxiliary_registration_id": registry["registration_id"],
        "auxiliary_registration_sha256": file_hash(root / "preparation/hf0280_source_registration.json"),
        "hf0280_operator_sha256": file_hash(Path(study.__file__).with_name("cross_sectional.py")),
        "seed_formula_sha256": file_hash(study.ROOT / "experiments/factor_calendar_daily_hf0280_research_sharpe15.yaml"),
        "generation_source_sha256": {name: file_hash(Path(study.__file__).with_name(name))
                                     for name in ("expansion.py", "factors.py", "research.py", "gateway.py")},
        "prior_source_archive_sha256": file_hash(archive / "manifest.json"),
        "prior_observations": {"selection_sha256": file_hash(previous / "selection.json"),
                               "temporal_result_sha256": file_hash(previous / "temporal_stage_result.json")},
        "all_data_exposure": "all generated 2015-2024 data treated as previously exposed development"}
    save_once(folder / "protocol.json", protocol)
    response = {"factors": models, "generated": True}
    call = root / "model_calls" / study.CALL
    save_once(call / "response.json", response)
    (call / "runtime_session.jsonl").write_text("GENERATED VERIFIED-IDENTITY FIXTURE, NOT A REAL MODEL\n", encoding="utf-8")
    (call / "prompt.txt").write_text("generated frozen hypothesis request", encoding="utf-8")
    receipt = {"model": "gpt-6-astra", "effort": "xhigh", "response": response,
        "runtime_identity": {"verified": True, "model": "gpt-6-astra", "effort": "xhigh", "generated": True},
        "artifact_sha256": {name: file_hash(call / name) for name in ("response.json", "runtime_session.jsonl", "prompt.txt")}}
    save_once(call / "admitted_receipt.json", receipt)
    trials, new_ids = [], {}
    for i, item in enumerate(models):
        factor_id = FactorSpec(item["name"], item["expression"]).factor_id
        old_duplicates = [row["factor_key"] for row in old_fit if row["factor_id"] == factor_id]
        new_duplicates = list(new_ids.get(factor_id, []))
        trials.append({"declaration_index": i, "factor_id": factor_id,
            "duplicate_of_prior_factor_keys": old_duplicates, "duplicate_of_new_indices": new_duplicates,
            "status": "duplicate" if old_duplicates or new_duplicates else "new_expression",
            "new_evaluation_results_seen_before_declaration": False,
            "prior_expression_evidence_already_seen": bool(old_duplicates), "counts_as_hypothesis_attempt": True})
        new_ids.setdefault(factor_id, []).append(i)
    declaration = {"cycle_id": study.CYCLE, "fixed_seeds": [study.HF0280_SEED], "model_factors": models,
        "protocol_sha256": file_hash(folder / "protocol.json"), "source_receipt_sha256": file_hash(call / "admitted_receipt.json"),
        "new_model_factor_hypotheses": len(models), "cumulative_model_factor_hypotheses": 6+len(models),
        "prior_model_factor_hypotheses_retained": 6, "new_portfolio_proposals": 0,
        "new_evaluation_results_seen_before_declaration": False, "trial_registration": trials}
    save_once(folder / "factor_declaration.json", declaration)
    return root, folder, library_path, panel, loaded, old_events


def test_generated_full_stage_reuses_nine_scores_freezes_fit_and_keeps_missing_axis(tmp_path, monkeypatch):
    root, folder, library, panel, loaded, prior_events = fixture(tmp_path, monkeypatch)
    original_fingerprint = panel.fingerprint()
    calls = []
    original_compute = FactorEngine.compute
    def compute(self, spec):
        calls.append(spec.name)
        assert not spec.name.startswith("OLD"), "old factors must only load their saved score arrays"
        return original_compute(self, spec)
    monkeypatch.setattr(FactorEngine, "compute", compute)
    result = study.evaluate_expansion_factors(root, library_path=library)
    assert result["evaluated"] == 3 and result["failed"] == 0
    assert result["prior_scores_recomputed"] == 0 and len(result["prior_factors"]) == 9
    assert result["shape"] == list(panel.eligible.shape) and panel.fingerprint() == original_fingerprint
    assert result["model_calls"] == result["account_executions"] == 0 and result["financial_success"] is False
    view = read(folder / "fit_factor_view.json")
    assert len(view["factors"]) == 12 and view["new_factor_keys"] == ["HF0280", "F7", "F8"]
    assert view["factors"][:9] == read(root / "fit_factor_view.json")["factors"]
    assert view["2021_2024_result_values_included"] is False
    fit_candidates = panel.dates[(panel.dates >= "2016-01-01") & (panel.dates <= "2020-12-31")]
    assert view["fit_signal_sessions"] == len(fit_candidates) - 21
    assert view["scope"]["last_allowed_signal_date"] == str(fit_candidates[-22].date())
    for row in view["factors"][9:]:
        assert set(row["comparison_factor_keys"]) == set(view["prior_factor_keys"] + view["new_factor_keys"]) - {row["factor_key"]}
        assert {r["horizon"] for r in row["by_horizon_and_year"]} == {1, 5, 20}
        assert {r["year"] for r in row["by_horizon_and_year"]} == {None, 2016, 2017, 2018, 2019, 2020}
        assert row["comparison_complete"] is True and row["incremental_status"] == "complete_controls"
        assert all(value["same_stock_date_label_pairs"] is True and 0 <= value["common_sample_coverage"] <= 1
                   for value in row["incremental"] if value["common_sample_coverage"] is not None)
    hf = pd.read_parquet(folder / "hf0280_operator/scores.parquet")
    assert hf.index.equals(panel.dates) and hf.columns.equals(panel.eligible.columns)
    assert hf.iloc[:, -1].isna().all() and hf.iloc[20:, :-1].notna().any().any()
    auxiliary = read(folder / "auxiliary_load_receipt.json")
    assert auxiliary["scope"] == ["2015-01-01", "2024-12-31"]
    assert all(row["returned_rows"] == len(panel.dates) for row in auxiliary["provenance"]["source_quality"].values() if row["status"] == "present")
    assert read(folder / "auxiliary_admission.json")["fields"] == list(HF0280_FIELDS)
    with FactorLibrary(library) as lib:
        assert lib.events()[:len(prior_events)] == prior_events
        snapshot = lib.load_snapshot(result["library_snapshot_id"])
        assert set(e["event_id"] for e in prior_events if e["kind"] == "exposure") <= set(snapshot["exposure_ids"])
        assert lib.verify_integrity()
    before_calls = list(calls)
    assert study.evaluate_expansion_factors(root, library_path=library) == result
    assert calls == before_calls and len(loaded) == 1


@pytest.mark.parametrize("failure", ["load_error", "missing_all", "operator_error"])
def test_auxiliary_or_hf_failure_is_local_and_fixed_ohlc_sibling_still_evaluates(tmp_path, monkeypatch, failure):
    root, folder, library, panel, _, _ = fixture(tmp_path, monkeypatch, models=[hypothesis()], missing_aux=failure == "missing_all")
    def fail(*args, **kwargs):
        raise PanelError("generated unavailable HF source or operator")
    if failure == "load_error":
        monkeypatch.setattr(study, "load_auxiliary_panel", fail)
    elif failure == "operator_error":
        monkeypatch.setattr(study, "compute_hf0280", fail)
    result = study.evaluate_expansion_factors(root, library_path=library)
    assert [(r["factor_key"], r["status"]) for r in result["factors"]] == [("HF0280", "failed"), ("F7", "evaluated")]
    assert result["comparison_complete"] is False
    assert result["factors"][1]["incremental_status"] == "partial_controls"
    assert read(folder / "hf0280_failure.json")["independent_ohlc_factors_may_continue"] is True
    assert result["shape"] == list(panel.eligible.shape)
    assert read(folder / "factor_panel_identity.json")["auxiliary_available"] is False
    assert study.evaluate_expansion_factors(root, library_path=library) == result


def test_duplicate_old_expression_is_retained_without_recomputation(tmp_path, monkeypatch):
    root, folder, library, _, _, _ = fixture(tmp_path, monkeypatch, models=[hypothesis("repeated", "pct_change(close,1)")])
    original_compute = FactorEngine.compute
    def compute(self, spec):
        assert spec.name != "repeated"
        return original_compute(self, spec)
    monkeypatch.setattr(FactorEngine, "compute", compute)
    result = study.evaluate_expansion_factors(root, library_path=library)
    repeated = result["factors"][1]
    assert repeated["status"] == "duplicate" and repeated["duplicate_of"] == "OLD1"
    assert repeated["scores_path"] is None and result["duplicate"] == 1
    with FactorLibrary(library) as lib:
        assert lib.get_event(repeated["attempt_id"])["payload"]["duplicate_of"] is not None


def test_forbidden_new_operand_is_local_failure_not_auxiliary_substitution(tmp_path, monkeypatch):
    root, folder, library, _, _, _ = fixture(tmp_path, monkeypatch,
        models=[hypothesis("forbidden", "gu_1m"), hypothesis("independent", "rolling_mean(close/open-1,3)")])
    result = study.evaluate_expansion_factors(root, library_path=library)
    assert [r["status"] for r in result["factors"]] == ["evaluated", "failed", "evaluated"]
    failure = next((folder / "factors").glob("F7_*/failure.json"))
    assert "gu_1m" in read(failure)["error"]


@pytest.mark.parametrize("change", ["receipt", "declaration", "scope", "prior_score", "operator", "registry"])
def test_frozen_input_drift_refuses_before_market_or_library_attempts(tmp_path, monkeypatch, change):
    root, folder, library, _, loaded, _ = fixture(tmp_path, monkeypatch, models=[])
    if change == "prior_score":
        path = root / "factors/OLD1/scores.parquet"
        path.write_bytes(path.read_bytes() + b"changed")
    else:
        path = {"receipt": root / "model_calls" / study.CALL / "response.json",
                "declaration": folder / "factor_declaration.json", "scope": folder / "protocol.json",
                "operator": folder / "protocol.json", "registry": root / "preparation/hf0280_source_registration.json"}[change]
        value = read(path)
        if change == "scope": value["numeric_scope"][-1] = "2025-12-31"
        elif change == "operator": value["hf0280_operator_sha256"] = "wrong"
        elif change == "declaration": value["fixed_seeds"][0]["direction"] = -1
        else: value["changed"] = True
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises((ValueError, KeyError)):
        study.evaluate_expansion_factors(root, library_path=library)
    assert not loaded and not (folder / "factor_execution_intent.json").exists()


def test_base_2025_scope_violation_keeps_failed_intent_and_never_retries(tmp_path, monkeypatch):
    root, folder, library, _, loaded, _ = fixture(tmp_path, monkeypatch, models=[], future=True)
    with pytest.raises(study.ExpansionIntegrityError, match="scope"):
        study.evaluate_expansion_factors(root, library_path=library)
    assert (folder / "factor_stage_failure.json").exists()
    with pytest.raises(study.ExpansionIntegrityError, match="unfinished"):
        study.evaluate_expansion_factors(root, library_path=library)
    assert len(loaded) == 1


def test_cancelled_stage_is_retained_and_exclusive_intent_rejects_second_writer(tmp_path, monkeypatch):
    root, folder, library, _, loaded, _ = fixture(tmp_path, monkeypatch, models=[])
    (folder / "cancel.request").write_text("generated cancellation", encoding="utf-8")
    with pytest.raises(InterruptedError):
        study.evaluate_expansion_factors(root, library_path=library)
    assert not loaded and (folder / "factor_stage_failure.json").exists()
    with pytest.raises(study.ExpansionIntegrityError, match="unfinished"):
        study.evaluate_expansion_factors(root, library_path=library)
    with pytest.raises(FileExistsError):
        study._claim(folder / "factor_execution_intent.json", {"second": True})


def test_changed_saved_factor_artifact_cannot_be_reused(tmp_path, monkeypatch):
    root, folder, library, _, loaded, _ = fixture(tmp_path, monkeypatch, models=[])
    result = study.evaluate_expansion_factors(root, library_path=library)
    path = Path(result["factors"][0]["scores_path"])
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(study.ExpansionIntegrityError, match="changed"):
        study.evaluate_expansion_factors(root, library_path=library)
    assert len(loaded) == 1


@pytest.mark.parametrize("change", ["generation_source", "archive_source", "duplicate_exposure"])
def test_generation_archive_and_trial_exposure_bindings_are_not_refrozen_on_worker_start(tmp_path, monkeypatch, change):
    root, folder, library, _, loaded, _ = fixture(tmp_path, monkeypatch,
        models=[hypothesis("repeated", "pct_change(close,1)")])
    if change == "archive_source":
        path = root / "preparation/source_archive_before_target_serialization_fix/generated_previous_source.py"
        path.write_text("changed archived original", encoding="utf-8")
    else:
        path = folder / ("protocol.json" if change == "generation_source" else "factor_declaration.json")
        value = read(path)
        if change == "generation_source":
            value["generation_source_sha256"]["factors.py"] = "changed"
        else:
            value["trial_registration"][0]["prior_expression_evidence_already_seen"] = False
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(study.ExpansionIntegrityError):
        study.evaluate_expansion_factors(root, library_path=library)
    assert not loaded and not (folder / "factor_execution_intent.json").exists()


def test_prior_missing_score_that_appears_later_is_verified_before_numeric_read(tmp_path, monkeypatch):
    root, _, library, panel, _, _ = fixture(tmp_path, monkeypatch, models=[])
    index, fit = read(root / "factor_index.json"), read(root / "fit_factor_view.json")
    path = Path(index["factors"][0]["scores_path"])
    original = path.read_bytes()
    path.unlink()
    study._prepare(root, library)  # Missing comparison can be disclosed locally.
    path.write_bytes(original + b"unregistered changed reappearance")
    actual_read = pd.read_parquet
    def read_guard(candidate, *args, **kwargs):
        assert Path(candidate) != path, "must validate newly appeared bytes before reading numeric values"
        return actual_read(candidate, *args, **kwargs)
    monkeypatch.setattr(pd, "read_parquet", read_guard)
    with pytest.raises(study.ExpansionIntegrityError, match="before read"):
        study._existing(root, panel, index, fit)


def test_prior_score_replacement_during_read_is_detected(tmp_path, monkeypatch):
    root, _, _, panel, _, _ = fixture(tmp_path, monkeypatch, models=[])
    index, fit = read(root / "factor_index.json"), read(root / "fit_factor_view.json")
    path = Path(index["factors"][0]["scores_path"])
    actual_read = pd.read_parquet
    def replacing_read(candidate, *args, **kwargs):
        result = actual_read(candidate, *args, **kwargs)
        if Path(candidate) == path:
            path.write_bytes(path.read_bytes() + b"changed during read")
        return result
    monkeypatch.setattr(pd, "read_parquet", replacing_read)
    with pytest.raises(study.ExpansionIntegrityError, match="during read"):
        study._existing(root, panel, index, fit)


def test_missing_saved_prior_score_stays_disclosed_without_substitution(tmp_path, monkeypatch):
    root, _, _, panel, _, _ = fixture(tmp_path, monkeypatch, models=[])
    index, fit = read(root / "factor_index.json"), read(root / "fit_factor_view.json")
    path = Path(index["factors"][0]["scores_path"])
    path.unlink()
    previous, directions, unavailable = study._existing(root, panel, index, fit)
    assert len(previous) == len(directions) == 8
    assert unavailable == [{"factor_key": "OLD1", "status": "missing_saved_score", "path": str(path)}]
    assert all(frame.index.equals(panel.dates) and frame.columns.equals(panel.eligible.columns) for frame in previous.values())


def test_complete_worker_and_model_view_degrade_missing_old_control(tmp_path, monkeypatch):
    root, folder, library, _, _, prior_events = fixture(tmp_path, monkeypatch, models=[hypothesis()])
    (root / "factors/OLD1/scores.parquet").unlink()
    result = study.evaluate_expansion_factors(root, library_path=library)
    view = read(folder / "fit_factor_view.json")
    assert result["evaluated"] == 2 and result["prior_scores_recomputed"] == 0
    for top in (view, result):
        assert top["comparison_complete"] is False
        assert top["expected_previous_factor_count"] == 9 and top["available_previous_factor_count"] == 8
        assert top["unavailable_prior_scores"][0]["factor_key"] == "OLD1"
    for row in view["factors"][9:]:
        assert row["incremental_status"] == "partial_controls" and row["comparison_complete"] is False
        assert row["missing_previous_factor_keys"] == ["OLD1"]
        assert "OLD1" in row["expected_control_keys"] and "OLD1" not in row["available_control_keys"]
        assert all(r["incremental_status"] == "partial_controls" for r in row["incremental"])
        assert all("candidate_mean_rank_ic_common_oriented" in r and "common_sample_coverage" in r for r in row["incremental"])
    with FactorLibrary(library) as lib:
        assert lib.events()[:len(prior_events)] == prior_events


def test_no_available_control_is_explicitly_not_evaluable():
    result = study._comparison(["old1", "old2"], {}, ["old1", "old2"])
    assert result["incremental_status"] == "not_evaluable" and result["comparison_complete"] is False


def test_role_risk_predeclared_before_load_and_separate_purged_statistics_never_feed_scores(tmp_path, monkeypatch):
    item = hypothesis("generated_risk20", role="risk_information")
    item["primary_horizon"] = 20
    root, folder, library, panel, loaded, _ = fixture(tmp_path, monkeypatch, models=[item])
    original_load = study.load_panel
    def load_after_risk_freeze(path):
        intent = read(folder / "factor_execution_intent.json")
        assert intent["risk_information_predeclaration"]["F7"]["status"] == "declared"
        assert any(Path(proof["path"]).name == "risk_diagnostics.py" for proof in intent["source_proofs"])
        assert intent["risk_labels_as_alpha_operands"] is False
        return original_load(path)
    monkeypatch.setattr(study, "load_panel", load_after_risk_freeze)
    original_compute = FactorEngine.compute
    def no_forward_fields(self, spec):
        assert not any(name.startswith("future_") for name in self.feature_names)
        return original_compute(self, spec)
    monkeypatch.setattr(FactorEngine, "compute", no_forward_fields)
    calls = []
    def generated_risk(scores, prices, eligible, dates, **kwargs):
        calls.append(dates.copy())
        assert scores.index.equals(panel.dates) and prices.index.equals(panel.dates)
        assert kwargs["direction"] == -1 and kwargs["horizon"] == 20
        assert kwargs["observed_price_mask"].equals(panel.fields["open_observed"].eq(1))
        assert set(kwargs["controls"]) == {"HF0280", study.LOG_AMOUNT_CONTROL, *[f"OLD{i+1}" for i in range(9)]}
        pd.testing.assert_frame_equal(kwargs["controls"][study.LOG_AMOUNT_CONTROL], np.log(panel.fields["amount"]))
        semantics = study.risk_information_semantics(direction=-1, horizon=20, minimum=30, quantiles=5,
            control_names=kwargs["controls"], observed_price_mask_supplied=True)
        metrics = ("future_vol", "future_downside", "future_entry_max_loss")
        raw = pd.DataFrame([{"date": date, "metric": metric, "paired_n": 64, "common_n": 63,
            "common_oriented_rank_ic": .25, "partial_oriented_rank_ic": .15, "control_rank_deficient": False}
            for date in dates for metric in metrics])
        quantiles = pd.DataFrame([{"date": date, "metric": metric, "quantile": q,
            "risk_mean": .3-q*.02, "common_risk_mean": .3-q*.02, "coverage": 1., "labeled_members": 12}
            for date in dates for metric in metrics for q in range(1, 6)])
        return {"summary": {"semantics": semantics, "risk_labels_registered_as_signal_fields": False,
                    "marker": "ARCHIVE_FUTURE_RISK_MARKER" if dates.max().year > 2020 else "FIT_RISK_ONLY",
                    "signal_dates": len(dates)},
            "daily_ic": raw, "common_sample": raw, "coverage": raw,
            "quantile_risk": quantiles,
            "annual": pd.DataFrame({"year": sorted(set(dates.year)), "generated_risk": .3}),
            "bootstrap": pd.DataFrame({"metric": metrics, "statistic": "oriented_ic", "mean": .25}),
            "labels": {name: pd.DataFrame(.1, index=dates, columns=scores.columns) for name in metrics}}
    monkeypatch.setattr(study, "evaluate_risk_information", generated_risk)
    result = study.evaluate_expansion_factors(root, library_path=library)
    assert result["evaluated"] == 2 and len(loaded) == 1 and len(calls) == 2
    expected = panel.dates[(panel.dates >= "2016-01-01") & (panel.dates <= "2020-12-31")][:-21]
    assert calls[0].equals(panel.dates) and calls[1].equals(expected)
    text = (folder / "fit_factor_view.json").read_text(encoding="utf-8")
    assert "ARCHIVE_FUTURE_RISK_MARKER" not in text and "FIT_RISK_ONLY" in text
    risk = read(folder / "fit_factor_view.json")["factors"][-1]["risk_information"]
    assert risk["return_ic_is_not_risk_admission_gate"] is True and risk["full_range_aggregates_reused"] is False
    assert risk["risk_labels_registered_as_signal_fields"] is False
    assert all(row["year"] <= 2020 for row in risk["annual"])
    proof_paths = [Path(proof["path"]) for proof in result["factors"][-1]["artifacts"]]
    assert any("risk_archive" in path.parts and path.name == "summary.json" for path in proof_paths)
    assert any("risk_fit" in path.parts and path.name == "common_sample.parquet" for path in proof_paths)
