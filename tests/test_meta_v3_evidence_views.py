"""Regression checks for the exhausted real-research context, no model calls."""
from copy import deepcopy
from dataclasses import asdict
import json
from types import SimpleNamespace

from quanta_agents.meta_v3.closing import BudgetState, ClosingPolicy, decide
from quanta_agents.meta_v3.evidence_views import compact_events, horizon_summary
from quanta_agents.meta_v3.ledger import digest, serial
from quanta_agents.meta_v3.runtime import make_prompt


def test_prompt_exposes_frozen_limits_and_shared_remaining_opportunities():
    policy = ClosingPolicy(task_calls=12, stage_calls=24, stage_tokens=1200000)
    state = BudgetState(300000, 900000, 3, 17, 1, 1000, 10000)
    task = {"idea": "ordinary research", "documents": []}
    tools = SimpleNamespace(contract=lambda: {})
    prompt = json.loads(make_prompt(task, tools, [], ("submit_research_report",),
                                   asdict(state), decide(policy, state), asdict(policy)))
    r = prompt["resources"]
    assert r["frozen_policy"] == asdict(policy)
    assert r["call_slots_including_this_call_and_final"] == 7
    assert r["exploration_call_slots_including_this_call"] == 6
    assert r["nominal_token_room_after_final_reserve"] == 220000
    last = BudgetState(300000, 900000, 11, 23, 1, 1000, 10000)
    prompt = json.loads(make_prompt(task, tools, [], ("submit_research_report",),
                                   asdict(last), decide(policy, last), asdict(policy)))
    assert prompt["mode"] == "close_only"
    assert prompt["resources"]["exploration_call_slots_including_this_call"] == 0


def test_compact_events_preserve_losses_missing_outcomes_and_order():
    rows = [{"event_id": str(i), "symbol": "stock", "signal_date": "2019-07-10",
             "feature": i/10, "included_common_sample": False, "entry_date": "2019-07-11",
             "entry_open": 10., "exclusion_reasons": ["cutoff"],
             "outcomes": {"1": {"horizon_sessions": 1, "exit_date": "2019-07-12",
                 "exit_open": 9., "gross_return": -0.1, "individually_available": True,
                 "exclusion_reasons": []},
                 "2": {"horizon_sessions": 2, "exit_date": None, "exit_open": None,
                 "gross_return": None, "individually_available": False, "exclusion_reasons": ["cutoff"]}}}
            for i in range(13)]
    page = {"rows": rows, "offset": 0, "total_rows": 13, "next_offset": None}
    before = deepcopy(page)
    view = compact_events(page)
    assert page == before and view["source_page_sha256"] == digest(page)
    assert len(serial(view).encode()) < 8000
    assert view["returned_rows"] == 13 and view["next_offset"] is None
    for i, row in enumerate(view["rows"]):
        decoded = dict(zip(view["columns"], row))
        assert decoded["event_id"] == str(i) and decoded["included_common_sample"] is False
        outcomes = [dict(zip(view["outcome_columns"], r)) for r in decoded["outcomes"]]
        assert outcomes[0]["gross_return"] == -0.1
        assert outcomes[1]["gross_return"] is None and outcomes[1]["exclusion_reasons"] == ["cutoff"]


def test_horizon_aggregate_projection_keeps_all_group_results():
    report = {k: [] for k in ("horizons", "curve", "denominators", "scope", "limitations", "policy")}
    report.update(status="computed", descriptive_conditioning=[{"horizon": 1, "high_mean": -.2,
        "low_mean": .1, "matched_pairs": 0, "matched_mean_difference": None, "rows": [{"return": -.2}]}])
    before = deepcopy(report)
    summary = horizon_summary(report)
    assert report == before
    assert summary["descriptive_conditioning"] == [{"horizon": 1, "high_mean": -.2,
        "low_mean": .1, "matched_pairs": 0, "matched_mean_difference": None}]
    assert summary["limitations"] == report["limitations"]
