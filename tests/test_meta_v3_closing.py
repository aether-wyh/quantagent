from dataclasses import replace
import pytest

from quanta_agents.meta_v3.closing import BudgetState, ClosingPolicy, allowed_actions, decide

P = ClosingPolicy()
S = BudgetState(0, 0, 0, 0, 1, 1000, 8200)
ACTIONS = ("inspect_inputs", "diagnose_horizons", "submit_research_report")


def test_saved_stop_trajectory_closes_before_last_affordable_query():
    expected = ((185198, "explore"), (136090, "close_only"),
                (83978, "close_only"), (28046, "terminal_without_submission"))
    prior = "explore"
    for room, mode in expected:
        result = decide(P, replace(S, task_exposure=600000-room, stage_exposure=600000-room), prior)
        assert result.mode == mode
        if mode == "close_only": assert allowed_actions(result, ACTIONS) == ("submit_research_report",)
        if mode == "terminal_without_submission": assert allowed_actions(result, ACTIONS) == ()
        prior = result.mode


def test_exact_reserves_and_shared_stage_boundary():
    for room, mode in ((160000, "explore"), (159999, "close_only"), (80000, "close_only"), (79999, "terminal_without_submission")):
        assert decide(P, replace(S, task_exposure=600000-room, stage_exposure=600000-room)).mode == mode
        assert decide(P, replace(S, stage_exposure=2400000-room)).mode == mode


def test_call_and_deadline_reserve_are_independent_of_token_room():
    assert decide(P, replace(S, task_calls_used=16, stage_calls_used=16)).mode == "close_only"
    assert decide(P, replace(S, stage_calls_used=68)).mode == "terminal_without_submission"
    assert decide(P, replace(S, deadline_epoch=4600)).mode == "close_only"
    assert decide(P, replace(S, deadline_epoch=1000)).mode == "terminal_without_submission"


def test_prior_close_cannot_reopen_and_unresolved_work_does_not_become_terminal():
    assert decide(P, S, "close_only").mode == "close_only"
    assert decide(P, S, "blocked").mode == "blocked"
    assert decide(P, S, "terminal_without_submission").mode == "terminal_without_submission"
    for flags in ({"unknown": True}, {"pending": True}, {"evidence_valid": False}):
        assert decide(P, replace(S, finals_remaining=0, **flags), "terminal_without_submission").mode == "blocked"


def test_policy_is_explicit_and_has_no_old_unknown_exception():
    policy = ClosingPolicy(task_tokens=100, stage_tokens=400, call_reserve=10, closing_reserve=20, closing_seconds=100)
    assert decide(policy, replace(S, task_exposure=71, stage_exposure=71)).mode == "close_only"
    assert decide(policy, replace(S, unknown=True)).mode == "blocked"
    with pytest.raises(ValueError): ClosingPolicy(closing_reserve=1)
    with pytest.raises(ValueError): ClosingPolicy(task_tokens=True)


def test_malformed_state_is_rejected_instead_of_releasing_budget():
    for changes in ({"task_exposure": True}, {"task_exposure": 1}, {"now_epoch": float("nan")},
                    {"unknown": 1}, {"finals_remaining": 2}):
        assert decide(P, replace(S, **changes)).mode == "blocked"
    assert decide(P, S, []).mode == "blocked"


def test_menu_requires_final_and_never_adds_unregistered_tools():
    decision = decide(P, S)
    assert allowed_actions(decision, ACTIONS) == ACTIONS
    for invalid in (("inspect_inputs",), ("submit_research_report", "submit_research_report"), []):
        with pytest.raises(ValueError): allowed_actions(decision, invalid)
