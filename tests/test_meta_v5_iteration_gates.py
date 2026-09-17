"""Independent V5 iteration gates using pinned generated evidence, no model.

Catalog NAV paths are explicit controller-admitted engineering fixtures. The
small V4 executions use generated flat bars and test routing/accountability;
neither fixture is evidence of financial performance or mechanism discovery.
"""
from copy import deepcopy
import json

import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.research_tools import ResearchTools, save_once
from quanta_agents.meta_v5.registry import Catalog, prepare_catalog, write_catalog
from quanta_agents.meta_v5.tools import ACTIONS, V5ResearchTools
from test_meta_v3_batch_research import configured, declaration as batch_declaration
from test_meta_v3_research_entry import program
from test_meta_v5_workflow import DEMO


SCOPE = "synthetic_shared_development"


def proposal(weight="0.3"):
    value = program()
    value["target_weight_expression"] = str(weight)
    return {"program": value}


def setup_tools(tmp_path, entries=(("original", "0.4"),), *, gaps=(),
                foreign=(), explicit=None):
    """Freeze catalog before tool calls; there is no model profile injection."""
    root = tmp_path / "stage"
    root.mkdir(parents=True)
    source = root / "generated_source.json"
    save_once(source, {"source_class": "generated_engineering", "market_reads": 0,
                       "purpose": "fixed iteration gate fixture, not research evidence"})
    bundles = []
    for name, weight in entries:
        bundle = DEMO.fixture_bundle(source)
        bundle.update(candidate_id=name, program_hash=digest(proposal(weight)["program"]))
        if name in gaps:
            bundle["pairs"][0]["candidate"]["fees"] = [None] * 4
        if name in foreign:
            bundle["scope_id"] = "unrelated_task_development"
        bundles.append(bundle)
    prepared = prepare_catalog(bundles, DEMO.fixture_policy())
    catalog = Catalog(root, write_catalog(root, prepared))
    case = configured(tmp_path)
    contract = {"action_limits": dict.fromkeys(ACTIONS, 64),
                "required_scope_id": SCOPE, "execution_scope_id": SCOPE,
                "execution_unit_id": "synthetic_v4", "benchmark_program_hashes": [],
                "revision_baseline_profile_id": explicit, "priority": 0}
    return V5ResearchTools(root, "iteration", case, [], catalog=catalog,
                           v5_contract=contract)


def call(tools, action, arguments, call_id=None):
    return DEMO.saved_call(tools, action, arguments, call_id=call_id)


def reflection(tools, profile_id="original", *, stopped=False, read=True):
    if read:
        DEMO.read_pages(tools, profile_id, limit=16)
    declaration = DEMO.fixture_reflection(tools._profile(profile_id))
    if stopped:
        for response in declaration["issue_responses"]:
            response.update(status="stopped", explanations=[],
                next_step={"kind": "stop", "reason": "Generated measurement unavailable; retain this failure."})
        declaration["experiments"] = []
    result = call(tools, "record_stability_reflection",
                  {"profile_id": profile_id, "declaration": declaration})
    return result["evidence_id"], declaration


def registration_args(reflection_id, *, profile_id="original", action="develop_strategy",
                      native=None, experiment_id="test_0"):
    return {"baseline_profile_id": profile_id, "reflection_evidence_id": reflection_id,
            "experiment_id": experiment_id, "proposal_action": action,
            "proposal_arguments": deepcopy(native if native is not None else proposal())}


def register(tools, reflection_id, **kwargs):
    result = call(tools, "register_stability_revision", registration_args(reflection_id, **kwargs))
    return result["evidence_id"]


@pytest.mark.parametrize("stopped,gap", [(True, False), (False, True)])
def test_stopped_or_evidence_blocked_reflection_cannot_register_revision(tmp_path, stopped, gap):
    tools = setup_tools(tmp_path, gaps=("original",) if gap else ())
    reflection_id, _ = reflection(tools, stopped=stopped)
    state = tools.research_state()["candidates"][0]
    if stopped:
        assert all(a["action"] == "abstain" for a in state["next_actions"])
    else:
        assert state["next_actions"][0]["action"] == "complete_evidence"
        assert any(a["action"] == "run_discriminating_experiment" and not a["ready"]
                   for a in state["next_actions"])
    with pytest.raises(AdmissionBlocked, match="stopped or blocked by missing evidence"):
        register(tools, reflection_id)
    assert not list(tools._saved("register_stability_revision"))


def test_missing_and_superseded_reflection_ids_do_not_authorize_revision(tmp_path):
    tools = setup_tools(tmp_path)
    DEMO.read_pages(tools, "original", limit=16)
    with pytest.raises(AdmissionBlocked, match="latest bound reflection"):
        register(tools, "invented_reflection")
    previous, _ = reflection(tools, read=False)
    latest, _ = reflection(tools, read=False)
    assert previous != latest
    with pytest.raises(AdmissionBlocked, match="latest bound reflection"):
        register(tools, previous)
    assert register(tools, latest)


@pytest.mark.parametrize("mutation", [
    lambda args: args.update(experiment_id="invented_experiment"),
    lambda args: args.update(proposal_action="inspect_inputs"),
    lambda args: args["proposal_arguments"].update(v5_revision_evidence_id="nested"),
    lambda args: args.update(programs=[]),
])
def test_registration_rejects_forged_experiment_or_non_native_envelope(tmp_path, mutation):
    tools = setup_tools(tmp_path)
    rid, _ = reflection(tools)
    args = registration_args(rid)
    mutation(args)
    with pytest.raises(AdmissionBlocked):
        call(tools, "register_stability_revision", args)


def test_revision_cannot_bind_foreign_scope_even_with_valid_reflection(tmp_path):
    tools = setup_tools(tmp_path, entries=(("original", "0.4"), ("foreign", "0.5")), foreign=("foreign",))
    rid, _ = reflection(tools, "foreign")
    with pytest.raises(AdmissionBlocked, match="switch required scope"):
        register(tools, rid, profile_id="foreign")
    assert [r["profile_id"] for r in tools.research_state()["candidates"]] == ["original"]


def test_second_unbound_develop_cannot_bypass_first_missing_profile(tmp_path):
    tools = setup_tools(tmp_path, entries=())
    first = call(tools, "develop_strategy", proposal("0.4"), call_id="first")
    assert first["public"]["raw_status"] == "completed_mechanical"
    pending = tools.research_state()["pending_execution_profiles"]
    assert pending == [{"execution_evidence_id": "first", "program_hash": digest(proposal("0.4")["program"]),
                        "next_action": "profile_execution"}]
    for name, native in (("develop_strategy", proposal()), ("register_batch", batch_declaration())):
        with pytest.raises(AdmissionBlocked, match="all executed candidates"):
            call(tools, name, native)


@pytest.mark.parametrize("action", ["develop_strategy", "register_batch"])
def test_complete_read_and_reflection_still_require_second_round_binding(tmp_path, action):
    tools = setup_tools(tmp_path)
    call(tools, "develop_strategy", proposal("0.4"), call_id="first")
    reflection(tools)
    native = proposal() if action == "develop_strategy" else batch_declaration()
    with pytest.raises(AdmissionBlocked, match="bound V5 reflection experiment"):
        call(tools, action, native)


@pytest.mark.parametrize("alteration", ["program", "action", "extra"])
def test_registered_exact_proposal_cannot_be_changed_before_delegation(tmp_path, monkeypatch, alteration):
    tools = setup_tools(tmp_path, explicit="original")
    rid, _ = reflection(tools)
    bound = register(tools, rid)
    native, action = proposal(), "develop_strategy"
    if alteration == "program":
        native = proposal("0.7")
    elif alteration == "action":
        action, native = "register_batch", batch_declaration()
    else:
        native["experiment_evidence_id"] = "unbound_v4_experiment"
    monkeypatch.setattr(ResearchTools, "_execute", lambda *a, **k: pytest.fail("forged proposal reached V4"))
    with pytest.raises(AdmissionBlocked, match="differs from its frozen"):
        call(tools, action, {**native, "v5_revision_evidence_id": bound})


def test_new_stop_reflection_invalidates_previously_registered_ready_proposal(tmp_path, monkeypatch):
    tools = setup_tools(tmp_path, explicit="original")
    rid, _ = reflection(tools)
    bound = register(tools, rid)
    reflection(tools, stopped=True, read=False)
    monkeypatch.setattr(ResearchTools, "_execute", lambda *a, **k: pytest.fail("superseded binding reached V4"))
    with pytest.raises(AdmissionBlocked, match="superseded"):
        call(tools, "develop_strategy", {**proposal(), "v5_revision_evidence_id": bound})


def test_correct_binding_strips_v5_envelope_and_runs_normal_v4_development(tmp_path, monkeypatch):
    tools = setup_tools(tmp_path)
    call(tools, "develop_strategy", proposal("0.4"), call_id="first")
    rid, _ = reflection(tools)
    bound = register(tools, rid)
    delegated = []
    original = ResearchTools._execute

    def observed(self, call_id, action, arguments):
        delegated.append((action, deepcopy(arguments)))
        return original(self, call_id, action, arguments)

    monkeypatch.setattr(ResearchTools, "_execute", observed)
    result = call(tools, "develop_strategy", {**proposal(), "v5_revision_evidence_id": bound}, call_id="revision")
    assert delegated == [("develop_strategy", proposal())]
    assert result["public"]["raw_status"] == "completed_mechanical"
    saved_request = json.loads((tools.folder / "revision/request.json").read_text(encoding="utf-8"))
    assert saved_request["arguments"] == proposal()
    state = tools.research_state()
    assert state["iteration_experiments"][0]["applied_proposal_ids"] == ["revision"]
    assert state["iteration_experiments"][0]["status"] == "executed_results_require_assessment"
    assert state["iteration_experiments"][0]["execution_evidence_ids"] == ["revision"]
    assert state["iteration_experiments"][0]["unassessed_execution_ids"] == ["revision"]
    assert state["pending_execution_profiles"][0]["execution_evidence_id"] == "revision"
    assert not state["formal_target_success"] and not state["causal_mechanism_identified"]


def test_correct_batch_binding_preserves_v4_declaration_and_all_candidates(tmp_path):
    tools = setup_tools(tmp_path, explicit="original")
    rid, _ = reflection(tools)
    native = batch_declaration((.2, .3))
    bound = register(tools, rid, action="register_batch", native=native)
    registered = call(tools, "register_batch", {**native, "v5_revision_evidence_id": bound}, call_id="batch")
    assert registered["public"]["reserved_candidates"] == 2
    artifact = tools._prior("batch", "register_batch")
    assert artifact["declaration"] == native
    assert tools.research_state()["iteration_experiments"][0]["status"] == "batch_registered_not_executed"
    with pytest.raises(AdmissionBlocked, match="already applied"):
        call(tools, "register_batch", {**native, "v5_revision_evidence_id": bound})
    executed = call(tools, "execute_batch", {"registration_evidence_id": "batch"}, call_id="batch_run")
    assert executed["public"]["status_counts"] == {"completed": 2}
    assert {r["execution_evidence_id"] for r in tools.research_state()["pending_execution_profiles"]} == {
        "batch_run/c001", "batch_run/c002"}


def test_batch_execution_rechecks_binding_after_a_new_stop_reflection(tmp_path, monkeypatch):
    tools = setup_tools(tmp_path, explicit="original")
    rid, _ = reflection(tools)
    native = batch_declaration((.2,))
    bound = register(tools, rid, action="register_batch", native=native)
    call(tools, "register_batch", {**native, "v5_revision_evidence_id": bound}, call_id="batch")
    reflection(tools, stopped=True, read=False)
    monkeypatch.setattr(ResearchTools, "_execute", lambda *a, **k: pytest.fail("stopped batch dispatched"))
    with pytest.raises(AdmissionBlocked, match="superseded"):
        call(tools, "execute_batch", {"registration_evidence_id": "batch"})


@pytest.mark.parametrize("omitted", ["0.1", "0.2", "2"])
def test_omitting_any_completed_or_failed_batch_candidate_profile_blocks_next_search(tmp_path, omitted):
    # V4 expansion preserves explicit parentheses in the frozen program JSON.
    entries = tuple(("p" + str(i), "(" + weight + ")") for i, weight in enumerate(("0.1", "0.2", "2")) if weight != omitted)
    tools = setup_tools(tmp_path, entries=entries)
    call(tools, "register_batch", batch_declaration((.1, .2, 2)), call_id="batch")
    result = call(tools, "execute_batch", {"registration_evidence_id": "batch"}, call_id="batch_run")
    assert result["public"]["status_counts"] == {"completed": 2, "failed": 1}
    for profile_id, _ in entries:
        reflection(tools, profile_id)
    pending = tools._pending_profiles()
    assert len(pending) == 1
    assert pending[0]["program_hash"] == digest(proposal("(" + omitted + ")")["program"])
    for action, native in (("develop_strategy", proposal()), ("register_batch", batch_declaration((.3,)))):
        with pytest.raises(AdmissionBlocked, match="all executed candidates"):
            call(tools, action, native)
    rid = tools._reflection(tools._profile(entries[0][0]))[0]
    with pytest.raises(AdmissionBlocked, match="all executed candidates"):
        register(tools, rid, profile_id=entries[0][0])
    # Selecting an attractive completed candidate cannot hide the failed arm.
    with pytest.raises(AdmissionBlocked, match="all executed candidates"):
        tools.final({"outcome": "strategy_for_development", "program_evidence_id": "batch_run",
                     "batch_candidate_id": "c002", "evidence_ids": ["batch", "batch_run", rid],
                     "conclusion": "Generated selected candidate", "limitations": ["Engineering only"],
                     "next_step": "Retain all candidates", "falsifiers": ["Missing assessment"]})


def test_every_batch_candidate_requires_reflection_and_first_execution_stays_baseline(tmp_path):
    tools = setup_tools(tmp_path, entries=(("first", "(0.1)"), ("second", "(0.2)")))
    call(tools, "register_batch", batch_declaration((.1, .2)), call_id="batch")
    call(tools, "execute_batch", {"registration_evidence_id": "batch"}, call_id="batch_run")
    # Read/reflect the second result first, to reproduce winner-first behavior.
    rid, _ = reflection(tools, "second")
    DEMO.read_pages(tools, "first", limit=16)
    assert not tools._pending_profiles()
    assert tools._development_baseline()["candidate_id"] == "first"
    with pytest.raises(AdmissionBlocked, match="every executed candidate requires"):
        register(tools, rid, profile_id="second")
    reflection(tools, "first", read=False)
    assert register(tools, rid, profile_id="second")


def test_unfinished_registered_batch_blocks_opening_another_search(tmp_path):
    tools = setup_tools(tmp_path, entries=())
    call(tools, "register_batch", batch_declaration((.2,)), call_id="unexecuted")
    for action, native in (("develop_strategy", proposal()), ("register_batch", batch_declaration((.3,)))):
        with pytest.raises(AdmissionBlocked, match="assess or finish registered batch"):
            call(tools, action, native)


def test_reflection_binding_cannot_override_native_v4_argument_validation(tmp_path):
    tools = setup_tools(tmp_path, explicit="original")
    rid, _ = reflection(tools)
    malformed = {**proposal(), "unadmitted_scope": "discarded_failures"}
    bound = register(tools, rid, native=malformed)
    with pytest.raises(AdmissionBlocked, match="develop exact arguments"):
        call(tools, "develop_strategy", {**malformed, "v5_revision_evidence_id": bound})
    assert tools.research_state()["iteration_experiments"][0]["status"] == "registered_not_applied"
