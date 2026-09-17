from __future__ import annotations

import sqlite3

import pytest

from quanta_agents.meta_v6.factors import FactorSpec
from quanta_agents.meta_v6.library import FactorLibrary, Library


SCOPE = {"data_fingerprint": "synthetic-a", "dates": ["2019-01-01", "2020-12-31"], "role": "development"}


def test_all_seeds_and_failures_survive_deduplication_with_unknown_costs(tmp_path):
    path = tmp_path / "library.sqlite"
    with Library(path) as library:
        a = FactorSpec("A", "cs_rank(close)")
        b = FactorSpec("B", " cs_rank((close)) ", parents=(a.spec_id,))
        first = library.record_attempt(a, status="failed", scope=SCOPE, seed=1, model="model-a",
                                       error="missing coverage", cost={"usd": 0.1, "known": True})
        second = library.record_attempt(b, status="evaluated", scope=SCOPE, seed=2, model="model-b")
        invalid = library.record_attempt(expression="lag(close,-1)", status="invalid", scope=SCOPE,
                                         seed=3, error="future lookup rejected")
        attempts = library.events(kind="attempt")
        assert len(attempts) == 3
        assert attempts[1]["payload"]["duplicate_of"] == first
        assert attempts[1]["payload"]["parents"] == [a.spec_id]
        assert attempts[1]["payload"]["cost"] is None
        assert attempts[1]["payload"]["independent_market_replication"] is False
        assert library.get_event(invalid)["payload"]["expression"] == "lag(close,-1)"
        assert second != first
        assert library.verify_integrity()
    with FactorLibrary(path) as reopened:
        assert len(reopened.events(kind="attempt")) == 3
        assert reopened.verify_integrity()


def test_frozen_snapshot_keeps_evidence_and_entire_trial_history(tmp_path):
    with Library(tmp_path / "library.sqlite") as library:
        spec = FactorSpec("A", "close")
        attempt = library.record_attempt(spec, status="evaluated", scope=SCOPE, seed=1)
        evidence = library.record_evidence(attempt, scope=SCOPE, status="supported_in_scope", metrics={"ic": 0.1})
        invalid = library.record_attempt(expression="future_close", status="invalid", scope=SCOPE)
        exposure = library.record_exposure(attempt_id=attempt, scope=SCOPE, purpose="candidate_selection",
                                            results_revealed=True, used_for_selection=True)
        snapshot_id = library.create_snapshot(scope=SCOPE)
        frozen = library.load_snapshot(snapshot_id)
        assert frozen["trial_history_ids"] == [attempt, invalid]
        assert frozen["exposure_ids"] == [exposure]
        assert frozen["evidence_ids"] == [evidence]
        new_attempt = library.record_attempt(spec, status="evaluated", scope=SCOPE, seed=2,
                                              library_snapshot_id=snapshot_id)
        library.record_evidence(new_attempt, scope=SCOPE, status="contradicted_in_scope", metrics={"ic": -0.2})
        assert library.load_snapshot(snapshot_id) == frozen
        assert len(library.evidence_for(spec.factor_id, snapshot_id=snapshot_id)) == 1
        assert len(library.evidence_for(spec.factor_id)) == 2
        assert library.get_event(new_attempt)["payload"]["duplicate_of"] == attempt
        assert library.verify_integrity()


def test_scope_specific_evidence_never_overwrites_old_validity(tmp_path):
    with Library(tmp_path / "library.sqlite") as library:
        spec = FactorSpec("A", "close")
        attempt = library.record_attempt(spec, status="evaluated", scope=SCOPE)
        other_scope = {**SCOPE, "data_fingerprint": "synthetic-b"}
        library.record_evidence(attempt, scope=SCOPE, status="supported_in_scope")
        library.record_evidence(attempt, scope=other_scope, status="contradicted_in_scope")
        assert library.evidence_for(spec.factor_id, scope=SCOPE)[0]["payload"]["status"] == "supported_in_scope"
        assert library.evidence_for(spec.factor_id, scope=other_scope)[0]["payload"]["status"] == "contradicted_in_scope"
        with pytest.raises(ValueError, match="scope"):
            library.record_evidence(attempt, scope={}, status="observed")
        with pytest.raises(ValueError, match="scope"):
            library.record_evidence(attempt, scope=SCOPE, status="permanently_profitable")


def test_sqlite_enforces_append_only_and_loaded_payloads_are_independent(tmp_path):
    path = tmp_path / "library.sqlite"
    with Library(path) as library:
        event_id = library.record_attempt(FactorSpec("A", "close"), status="failed", scope=SCOPE)
        loaded = library.get_event(event_id)
        loaded["payload"]["status"] = "evaluated"
        assert library.get_event(event_id)["payload"]["status"] == "failed"
        with sqlite3.connect(path) as connection:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute("UPDATE factor_library_events SET payload='{}'")
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute("DELETE FROM factor_library_events")
        assert library.verify_integrity()


def test_references_and_exposure_are_explicit(tmp_path):
    with Library(tmp_path / "library.sqlite") as library:
        with pytest.raises(KeyError):
            library.record_evidence("unknown", scope=SCOPE, status="observed")
        with pytest.raises(ValueError):
            library.create_snapshot(scope=SCOPE, factor_ids=["unknown"])
        attempt = library.record_attempt(FactorSpec("A", "close"), status="evaluated", scope=SCOPE)
        with pytest.raises(ValueError, match="revealed"):
            library.record_exposure(attempt_id=attempt, scope=SCOPE, purpose="selection",
                                     results_revealed=False, used_for_selection=True)
        with pytest.raises(ValueError, match="snapshot"):
            library.record_attempt(FactorSpec("B", "volume"), status="planned", scope=SCOPE,
                                   library_snapshot_id=attempt)
        with pytest.raises(ValueError, match="unvalidated"):
            library.record_attempt(expression="close", status="evaluated", scope=SCOPE)
