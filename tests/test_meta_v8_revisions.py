"""Generated ledger/spec fixtures only: no model, market arrays or account run."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from quanta_agents.meta_v7.revisions import (ALLOWED_PATHS, control_identifiability,
                                            derive_revision, freeze_revision_plan)
from quanta_agents.research_kernel.compiler import validate_strategy
from quanta_agents.research_kernel.store import Store, serial


def original():
    # The public V7 drift values are reproduced in a generated ledger fixture.
    return validate_strategy({"name": "generated pure momentum control",
        "score": {"op": "rank", "args": [{"op": "factor", "id": "F1"}]},
        "allocation": {"top_n": 40, "gross_exposure": 1., "max_stock_weight": .05,
                       "weighting": "inverse_volatility", "rebalance_sessions": 5},
        "risk_score": {"op": "add", "args": [{"op": "factor", "id": "F7"},
                                                {"op": "constant", "value": 1e-6}]},
        "metadata": {"synthetic": True, "kernel_control_role": "omit_2"}})


@pytest.fixture
def kernel(tmp_path):
    store = Store(tmp_path / "synthetic")
    with store.connect() as db:
        db.executescript("CREATE TABLE batch_reviews(batch_id TEXT PRIMARY KEY,review TEXT);"
                         "CREATE TABLE validation_jobs(id TEXT PRIMARY KEY);")
        db.execute("INSERT INTO runs(id,spec,status,evidence_id,updated) VALUES (?,?,?,?,?)",
                   ("parent", serial({"strategy": original(), "scope": ["2016-01-01", "2020-12-31"],
                                     "account_policy": {"capital": 1000000}}), "completed", "ev_generated", 1.))
        db.execute("INSERT INTO attempts(id,batch_id,run_id,name,role,status,created) VALUES (?,?,?,?,?,?,?)",
                   ("attempt", "first", "parent", "generated control", "omit_2", "completed", 1.))
    return SimpleNamespace(store=store)


def plan(kernel, paths=None):
    return freeze_revision_plan(kernel, "first", {"parent_run_id": "parent",
        "allowed_paths": paths or ["/allocation/weighting", "/risk_score"],
        "hypothesis": "generated weighting question", "falsifier": "no matching evidence implies no claim"})


def reviewed(kernel, paths=None):
    frozen = plan(kernel, paths)
    with kernel.store.connect() as db:
        db.execute("INSERT INTO batch_reviews VALUES (?,?)", ("first", serial({"batch_id": "first",
            "verdict": "revise", "conclusion": "generated review", "revision_plan": frozen,
            "evidence_id": "ev_review_generated"})))
    return frozen


def equal_patch():
    return [{"path": "/allocation/weighting", "value": "equal"}, {"path": "/risk_score", "value": None}]


def test_control_parent_revision_preserves_undeclared_identity_and_produces_explicit_diff(kernel):
    frozen = reviewed(kernel)
    before = kernel.store.rows("SELECT * FROM runs")
    result = derive_revision(kernel, "parent", "first", equal_patch())
    spec, report = result["spec"], result["report"]
    assert spec["allocation"]["top_n"] == 40
    assert spec["allocation"]["gross_exposure"] == 1
    assert spec["metadata"] == original()["metadata"]
    assert spec["score"] == original()["score"]
    assert report["parent_strategy_sha256"] == frozen["parent_strategy_sha256"]
    assert {row["path"] for row in report["actual_changes"]} == {"/risk_score", "/allocation/weighting"}
    assert report["domains"] == ["exposure", "risk"] and report["causal_claim"] is False
    assert report["parent_evidence_id"] == "ev_generated"
    assert kernel.store.rows("SELECT * FROM runs") == before
    assert derive_revision(kernel, "parent", "first", equal_patch()) == result


def test_real_drift_shape_top_n_is_rejected_unless_predeclared(kernel):
    reviewed(kernel)
    with pytest.raises(ValueError, match="outside"):
        derive_revision(kernel, "parent", "first", equal_patch() + [{"path": "/allocation/top_n", "value": 20}])


def test_real_drift_shape_epsilon_requires_declared_risk_tree(kernel):
    reviewed(kernel, ["/allocation/top_n"])
    risk = deepcopy(original()["risk_score"])
    risk["args"][1]["value"] = 1e-8
    with pytest.raises(ValueError, match="outside"):
        derive_revision(kernel, "parent", "first", [{"path": "/risk_score", "value": risk}])


def test_predeclared_multiple_changes_are_reported_without_single_cause_claim(kernel):
    reviewed(kernel, ["/allocation/top_n", "/risk_score"])
    risk = deepcopy(original()["risk_score"])
    risk["args"][1]["value"] = 1e-8
    result = derive_revision(kernel, "parent", "first", [{"path": "/allocation/top_n", "value": 20},
        {"path": "/risk_score", "value": risk}], name="explicit composite experiment")
    assert {row["path"] for row in result["report"]["actual_changes"]} == {
        "/allocation/top_n", "/risk_score/args/1/value"}
    assert result["report"]["domains"] == ["risk", "selection_scope"]
    assert result["report"]["name_change"]["after"] == "explicit composite experiment"
    assert result["report"]["causal_claim"] is False


@pytest.mark.parametrize("path", ["/metadata", "/version", "/allocation", "/risk_score/args/1/value",
                                   "/account_policy/capital", "/score/../metadata", "/allocation~1top_n"])
def test_no_arbitrary_json_pointer_write_surface(kernel, path):
    with pytest.raises(ValueError, match="supported JSON pointers"):
        plan(kernel, [path])


@pytest.mark.parametrize("change", [[], [{"path": "/allocation/top_n", "value": 40}],
    [{"path": "/allocation/top_n", "value": 20}, {"path": "/allocation/top_n", "value": 21}],
    [{"path": "/allocation/top_n", "value": 20, "extra": True}],
    [{"path": "/allocation/top_n", "value": 20}] * (len(ALLOWED_PATHS) + 1)])
def test_empty_duplicate_noop_unknown_and_oversize_change_lists_fail(kernel, change):
    reviewed(kernel, ["/allocation/top_n"])
    with pytest.raises(ValueError):
        derive_revision(kernel, "parent", "first", change, name="renaming alone cannot count")


def test_each_declared_patch_must_have_effect_and_final_strategy_is_valid(kernel):
    reviewed(kernel, ["/allocation/top_n", "/allocation/gross_exposure"])
    with pytest.raises(ValueError, match="ineffective"):
        derive_revision(kernel, "parent", "first", [{"path": "/allocation/top_n", "value": 20},
            {"path": "/allocation/gross_exposure", "value": 1}])
    with pytest.raises(ValueError, match="positive bounded integer"):
        derive_revision(kernel, "parent", "first", [{"path": "/allocation/top_n", "value": True}])
    with pytest.raises(ValueError, match="finite bounded JSON"):
        derive_revision(kernel, "parent", "first", [{"path": "/allocation/gross_exposure", "value": float("nan")}])


def test_wrong_parent_unfinished_parent_and_wrong_batch_fail(kernel):
    with pytest.raises(ValueError, match="completed run"):
        freeze_revision_plan(kernel, "other", {"parent_run_id": "parent", "allowed_paths": ["/score"],
                                               "hypothesis": "x", "falsifier": "y"})
    reviewed(kernel)
    with pytest.raises(ValueError, match="match the frozen"):
        derive_revision(kernel, "other", "first", equal_patch())
    with kernel.store.connect() as db:
        db.execute("UPDATE runs SET status='failed' WHERE id='parent'")
    with pytest.raises(ValueError, match="completed run"):
        derive_revision(kernel, "parent", "first", equal_patch())


def test_legacy_reviews_are_readable_but_cannot_be_assumed_bound(kernel):
    with kernel.store.connect() as db:
        db.execute("INSERT INTO batch_reviews VALUES (?,?)", ("first", serial({"verdict": "revise",
                                                                              "conclusion": "old text"})))
    with pytest.raises(ValueError, match="frozen review plan"):
        derive_revision(kernel, "parent", "first", equal_patch())
    assert json.loads(kernel.store.rows("SELECT review FROM batch_reviews")[0]["review"])["conclusion"] == "old text"


def test_superseded_or_nonrevise_review_cannot_be_used(kernel):
    reviewed(kernel)
    with kernel.store.connect() as db:
        db.execute("INSERT INTO batch_reviews VALUES (?,?)", ("newer", serial({"verdict": "reject"})))
    with pytest.raises(ValueError, match="latest batch review"):
        derive_revision(kernel, "parent", "first", equal_patch())
    with pytest.raises(ValueError, match="explicitly request revise"):
        derive_revision(kernel, "parent", "newer", equal_patch())


@pytest.mark.parametrize("field", ["strategy", "scope", "account_policy"])
def test_changed_parent_frozen_identity_is_not_reblessed(kernel, field):
    reviewed(kernel)
    frozen = json.loads(kernel.store.rows("SELECT spec FROM runs")[0]["spec"])
    if field == "strategy":
        frozen[field]["allocation"]["top_n"] = 20
    elif field == "scope":
        frozen[field][0] = "2017-01-01"
    else:
        frozen[field]["capital"] = 2000000
    with kernel.store.connect() as db:
        db.execute("UPDATE runs SET spec=?", (serial(frozen),))
    with pytest.raises(ValueError, match="differs from the review"):
        derive_revision(kernel, "parent", "first", equal_patch())


@pytest.mark.parametrize("state", ["stopped", "validation"])
def test_closed_or_validation_frozen_study_blocks_revision(kernel, state):
    reviewed(kernel)
    with kernel.store.connect() as db:
        if state == "stopped":
            kernel.store.set_meta(db, "stopped", True)
        else:
            db.execute("INSERT INTO validation_jobs VALUES ('frozen')")
    with pytest.raises(ValueError, match="Closed research|frozen for validation"):
        derive_revision(kernel, "parent", "first", equal_patch())


def test_plan_is_bounded_exact_and_independent_of_input_mutations(kernel):
    raw = {"parent_run_id": "parent", "allowed_paths": ["/score"], "hypothesis": "x", "falsifier": "y"}
    frozen = freeze_revision_plan(kernel, "first", raw)
    raw["allowed_paths"].append("/gate")
    assert frozen["allowed_paths"] == ["/score"]
    for invalid in ({**raw, "extra": 1}, {**raw, "falsifier": ""},
                    {**raw, "allowed_paths": ["/score", "/score"]}, {**raw, "hypothesis": "x" * 2001}):
        with pytest.raises(ValueError):
            freeze_revision_plan(kernel, "first", invalid)


def test_generated_cap_counterexample_and_observed_exposure_do_not_become_causal_claims():
    spec = original()
    spec["allocation"]["top_n"] = 20
    control = deepcopy(spec)
    control["allocation"]["weighting"] = "equal"
    control["risk_score"] = None
    report = control_identifiability(spec, {"mean_exposure": .8846}, control, {"mean_exposure": .9878})
    assert report["cap_can_reduce_gross_exposure"] is True
    assert report["nonuniform_weights_at_or_below_full_allocation_cap"] is True
    assert report["mean_exposure_difference_control_minus_proposal"] == pytest.approx(.1032)
    assert report["status"] == "not_identified"
    assert report["risk_information_gain_identified"] is False
    # Independent algebraic two-stock instance of normalize-then-cap.
    coefficients = [1., 2.]
    targets = [min(value / sum(coefficients), .5) for value in coefficients]
    assert sum(targets) == pytest.approx(5 / 6)
    assert control_identifiability(spec)["observed_exposure_difference"] is None
    assert control_identifiability(control)["cap_can_reduce_gross_exposure"] is False
    looser = control_identifiability(original())
    assert looser["cap_can_reduce_gross_exposure"] is True
    assert looser["nonuniform_weights_at_or_below_full_allocation_cap"] is False
