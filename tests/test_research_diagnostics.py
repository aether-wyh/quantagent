from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import quanta_agents.research_diagnostics as research_diagnostics
from quanta_agents.agents.research_diagnostics_agent import ResearchDiagnosticsAgent
from quanta_agents.research_diagnostics import (
    DEFAULT_EVENT_DIAGNOSTICS,
    build_diagnostic_request,
    normalize_diagnostic_items,
    run_research_diagnostics,
)
from quanta_agents.state import init_state


def _row(
    candidate_id: str,
    timestamp: str,
    *,
    gross: float | None,
    past_up_count: int = 4,
    no_early_spike: bool = True,
    pre_window_up: bool = True,
    session_no: int = 0,
    trigger_position: int = 20,
    volume_hit: bool | None = None,
    next_up: bool | None = None,
    pulse_return_sum: float | None = None,
    pulse5_return: float | None = None,
    target_minute_return: float | None = None,
) -> dict[str, object]:
    ts = pd.Timestamp(timestamp)
    volume_hit_value = (
        bool(gross is not None and gross > 0) if volume_hit is None else volume_hit
    )
    next_up_value = (
        bool(gross is not None and gross > 0) if next_up is None else next_up
    )
    return {
        "candidate_id": candidate_id,
        "date": ts.normalize(),
        "code": "sz000001",
        "session_no": session_no,
        "trigger_ts": ts,
        "predicted_ts": ts + pd.Timedelta(minutes=2),
        "trigger_position": trigger_position,
        "predicted_position": trigger_position + 2,
        "next_spike_position": trigger_position + 2,
        "past_up_count": past_up_count,
        "step_up_count": max(past_up_count - 1, 0),
        "gap_min": 2,
        "gap_max": 2,
        "return_stability": 0.2,
        "amount_cv": 0.2,
        "volume_z_mean": 2.5,
        "volume_z_cv": 0.2,
        "no_early_spike": no_early_spike,
        "pre_window_up": pre_window_up,
        "pulse_return_sum": gross if pulse_return_sum is None else pulse_return_sum,
        "pulse5_return": gross if pulse5_return is None else pulse5_return,
        "pulse_close_position_mean": 0.7,
        "target_minute_return": (
            gross if target_minute_return is None else target_minute_return
        ),
        "forward_5m": gross,
        "forward_10m": gross * 2 if gross is not None else None,
        "forward_20m": gross * 3 if gross is not None else None,
        "volume_hit": volume_hit_value,
        "next_up": next_up_value,
        "joint_minute_hit": bool(volume_hit_value and next_up_value),
    }


def _state(tmp_path: Path, monkeypatch):
    event_path = tmp_path / "events.parquet"
    pd.DataFrame(
        [
            _row(
                "train_1",
                "2022-01-04 09:40:00",
                gross=0.01,
                volume_hit=False,
                next_up=True,
            ),
            _row(
                "train_2",
                "2022-01-04 09:45:00",
                gross=-0.005,
                volume_hit=True,
                next_up=False,
            ),
            _row("train_3", "2022-02-04 09:40:00", gross=0.03, past_up_count=3),
            _row("train_4", "2023-01-04 09:40:00", gross=0.02),
            _row("dev_unselected", "2024-04-17 10:18:00", gross=0.02, no_early_spike=False),
            _row("dev_selected", "2024-04-17 10:18:00", gross=0.02),
            _row(
                "dev_boundary",
                "2024-05-06 11:28:00",
                gross=None,
                trigger_position=118,
            ),
            _row("dev_2", "2024-06-03 10:00:00", gross=-0.01),
            _row("FINAL_SECRET_MARKER", "2025-01-06 09:40:00", gross=9.9),
        ]
    ).to_parquet(event_path, index=False)
    monkeypatch.setenv("QUANTA_EVENT_FEATURES_PATH", str(event_path))
    state = init_state(
        "分钟事件",
        max_epochs=3,
        experiment_spec={
            "experiment_id": "exp_diagnostic_test",
            "backtest_mode": "event_parquet",
            "train_start": "2022-01-01",
            "train_end": "2023-12-31",
            "validate_start": "2024-01-01",
            "validate_end": "2024-12-31",
            "backtest_start": "2025-01-01",
            "backtest_end": "2025-12-31",
            "event_horizon_minutes": 5,
            "event_cooldown_minutes": 20,
            "buy_cost": 0.0003,
            "sell_cost": 0.0008,
            "slippage": 0.00025,
        },
    )
    state["epoch_index"] = 2
    state["current_candidate_id"] = "candidate_002"
    state["candidate_records"] = [
        {"candidate_id": "candidate_001", "period_kind": "development"}
    ]
    state["research_trial_count"] = 1
    state["strategy_result"] = {
        "params": {
            "minimum_past_up_count": 4,
            "required_no_early_spike": True,
            "required_pre_window_up": True,
        }
    }
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": value, "reason": "test", "parameters": {}}
            for value in DEFAULT_EVENT_DIAGNOSTICS
        ],
    )
    return state


def test_event_diagnostics_use_only_train_and_development(tmp_path, monkeypatch) -> None:
    state = _state(tmp_path, monkeypatch)

    report = run_research_diagnostics(state)

    assert report["period_access"]["final_period_read"] is False
    assert "2025" not in str(report)
    results = {item["id"]: item for item in report["results"]}
    waterfall = results["rule_waterfall"]
    train_steps = waterfall["periods"]["train"]["steps"]
    counts = [step["event_count"] for step in train_steps]
    assert counts == sorted(counts, reverse=True)
    assert waterfall["outcome_fields_used_for_selection"] == []
    screening = results["feature_screening"]
    assert "forward_5m" not in screening["selection_fields"]
    assert "joint_minute_hit" not in screening["selection_fields"]
    assert "forward_5m" in screening["forbidden_outcome_fields"]

    flow = results["flow_reconciliation"]
    assert flow["selected_signal_count"] == 3
    assert flow["matched_unique_signal_count"] == 2
    assert flow["unmatched_signal_count"] == 1
    assert flow["extra_event_rows_from_same_stock_time"] == 1
    assert flow["duplicate_stock_time_details"][0]["candidate_ids"] == [
        "dev_unselected",
        "dev_selected",
    ]

    price = results["execution_price_audit"]
    assert price["periods"]["development"]["session_boundary_count"] == 1


@pytest.mark.parametrize(
    ("candidate_horizon", "expected_horizon", "expected_multiplier", "source"),
    [
        (10, 10, 2.0, "strategy_result.params"),
        (20, 20, 3.0, "strategy_result.params"),
        (None, 5, 1.0, "experiment_spec.event_horizon_minutes"),
    ],
)
def test_diagnostics_use_candidate_event_horizon(
    tmp_path,
    monkeypatch,
    candidate_horizon,
    expected_horizon,
    expected_multiplier,
    source,
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    if candidate_horizon is not None:
        state["strategy_result"]["params"]["event_horizon_minutes"] = (
            candidate_horizon
        )
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [{"id": "period_metrics", "reason": "test", "parameters": {}}],
    )

    report = run_research_diagnostics(state)

    overall = report["results"][0]["periods"]["train"]["overall"]
    assert report["event_horizon_minutes"] == expected_horizon
    assert report["event_horizon_source"] == source
    assert overall["gross_mean_return"] == pytest.approx(
        expected_multiplier * (0.01 - 0.005 + 0.02) / 3
    )


def test_diagnostics_reject_unsupported_candidate_event_horizon(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["strategy_result"]["params"]["event_horizon_minutes"] = 15
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [{"id": "period_metrics", "reason": "test", "parameters": {}}],
    )

    with pytest.raises(ValueError, match="5、10 或 20"):
        run_research_diagnostics(state)


def test_execution_price_audit_uses_current_rule_and_explains_unmatched_signals(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    event_path = tmp_path / "events.parquet"
    events = pd.read_parquet(event_path)
    events["pulse1_position"] = 223
    selected_ids = [
        "train_1",
        "train_2",
        "train_3",
        "dev_selected",
        "dev_boundary",
        "dev_2",
    ]
    events.loc[events["candidate_id"].isin(selected_ids), "pulse1_position"] = 224
    boundary_ids = ["train_2", "dev_boundary"]
    other_unmatched_ids = ["train_3", "dev_2"]
    events.loc[
        events["candidate_id"].isin([*boundary_ids, *other_unmatched_ids]),
        "forward_5m",
    ] = float("nan")
    events.loc[events["candidate_id"].isin(boundary_ids), "session_no"] = 0
    events.loc[events["candidate_id"].isin(boundary_ids), "trigger_position"] = 118
    events.loc[events["candidate_id"].isin(other_unmatched_ids), "session_no"] = 0
    events.loc[
        events["candidate_id"].isin(other_unmatched_ids), "trigger_position"
    ] = 50
    events.to_parquet(event_path, index=False)

    read_upper_bounds: list[pd.Timestamp] = []
    real_read_parquet = pd.read_parquet

    def tracked_read_parquet(*args, **kwargs):
        filters = kwargs.get("filters", [])
        if len(filters) >= 2:
            read_upper_bounds.append(pd.Timestamp(filters[1][2]))
        return real_read_parquet(*args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", tracked_read_parquet)
    state["strategy_result"]["params"] = {"pulse1_position_threshold": 224}
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [{"id": "execution_price_audit", "reason": "test", "parameters": {}}],
    )

    report = run_research_diagnostics(state)

    audit = report["results"][0]
    assert audit["selection_fields_only"] == ["pulse1_position"]
    assert audit["count_unit"] == "按 trigger_ts + code 去重后的唯一信号"
    for period_name in ("train", "development"):
        period = audit["periods"][period_name]
        assert period["source_event_row_count"] == 4
        assert period["selected_event_row_count"] == 3
        assert period["selected_signal_count"] == 3
        assert period["valid_price_signal_count"] == 1
        assert period["valid_price_ratio"] == pytest.approx(1 / 3)
        assert period["unmatched_signal_count"] == 2
        assert period["unmatched_signal_ratio"] == pytest.approx(2 / 3)
        assert period["boundary_invalid_signal_count"] == 1
        assert period["other_unmatched_signal_count"] == 1
        assert period["boundary_share_of_unmatched"] == pytest.approx(1 / 2)
        assert period["other_share_of_unmatched"] == pytest.approx(1 / 2)
        by_position = {
            item["trigger_position"]: item
            for item in period["unmatched_by_trigger_position"]
        }
        assert by_position[118]["boundary_invalid_signal_count"] == 1
        assert by_position[50]["other_unmatched_signal_count"] == 1

    assert report["period_access"]["final_period_read"] is False
    assert read_upper_bounds
    assert max(read_upper_bounds) <= pd.Timestamp("2025-01-01")
    assert "2025" not in str(audit)


def test_diagnostic_agent_returns_to_same_research_epoch(tmp_path, monkeypatch) -> None:
    state = _state(tmp_path, monkeypatch)
    before = (
        state["epoch_index"],
        state["current_candidate_id"],
        state["research_trial_count"],
        len(state["candidate_records"]),
    )

    result = ResearchDiagnosticsAgent().run(state)

    assert result["phase"] == "hypothesis"
    assert result["diagnostic_round"] == 1
    assert len(result["diagnostic_records"]) == 1
    after = (
        result["epoch_index"],
        result["current_candidate_id"],
        result["research_trial_count"],
        len(result["candidate_records"]),
    )
    assert after == before


def test_diagnostic_request_uses_latest_completed_candidate() -> None:
    state = init_state("test", max_epochs=3)
    state["epoch_index"] = 2
    state["current_candidate_id"] = "candidate_002"
    state["candidate_records"] = [
        {"candidate_id": "candidate_001", "period_kind": "development"}
    ]

    request = build_diagnostic_request(
        state,
        [{"id": "period_metrics", "reason": "test", "parameters": {}}],
    )

    assert request["source_candidate_id"] == "candidate_001"
    assert request["research_epoch"] == 2


def test_unknown_diagnostic_id_is_not_accepted() -> None:
    assert normalize_diagnostic_items(
        [{"id": "read_final_test", "reason": "bad", "parameters": {}}]
    ) == []


def test_response_curve_and_next_pulse_mechanism_are_separate(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
        ],
    )

    report = run_research_diagnostics(state)

    results = {item["id"]: item for item in report["results"]}
    curve = results["event_response_curve"]
    assert curve["status"] == "completed"
    assert curve["outcome_fields_used_for_selection"] == []
    train_horizons = curve["periods"]["train"]["horizons"]
    assert set(train_horizons) == {"5m", "10m", "20m"}
    assert train_horizons["10m"]["overall"]["gross_mean_return"] == pytest.approx(
        2 * train_horizons["5m"]["overall"]["gross_mean_return"]
    )
    assert train_horizons["20m"]["overall"]["gross_mean_return"] == pytest.approx(
        3 * train_horizons["5m"]["overall"]["gross_mean_return"]
    )

    mechanism = results["next_pulse_mechanism"]
    train = mechanism["periods"]["train"]
    assert train["volume_hit"]["rate"] == pytest.approx(2 / 3)
    assert train["next_up"]["rate"] == pytest.approx(2 / 3)
    assert train["next_up_given_volume_hit"]["rate"] == pytest.approx(1 / 2)
    assert train["joint"]["rate"] == pytest.approx(1 / 3)
    assert train["stored_joint_mismatch_count"] == 0


def test_horizon_diagnostics_remove_boundary_invalid_before_cooldown(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    event_path = tmp_path / "events.parquet"
    rows: list[dict[str, object]] = []
    for year in (2022, 2024):
        rows.extend(
            [
                _row(
                    f"boundary_{year}",
                    f"{year}-01-04 11:28:00",
                    gross=None,
                    session_no=0,
                    trigger_position=117,
                    volume_hit=False,
                    next_up=False,
                ),
                _row(
                    f"kept_{year}",
                    f"{year}-01-04 13:01:00",
                    gross=0.02,
                    session_no=1,
                    trigger_position=120,
                    volume_hit=True,
                    next_up=True,
                ),
            ]
        )
    pd.DataFrame(rows).to_parquet(event_path, index=False)
    state["experiment_spec"]["event_cooldown_minutes"] = 120
    state["strategy_result"]["params"]["event_horizon_minutes"] = 5
    variants = [
        {
            "name": "all_selected_events",
            "conditions": [
                {"field": "past_up_count", "operator": ">=", "value": 4}
            ],
        }
    ]
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
            {
                "id": "core_variant_comparison",
                "reason": "test",
                "parameters": {"variants": variants},
            },
        ],
    )

    report = run_research_diagnostics(state)
    results = {item["id"]: item for item in report["results"]}

    curve = results["event_response_curve"]
    expected_flow = {
        "selected_event_count_before_return_availability": 2,
        "valid_return_event_count": 1,
        "invalid_return_event_count": 1,
        "boundary_invalid_return_count": 1,
        "other_invalid_return_count": 0,
        "duplicate_removed_count": 0,
        "before_cooldown_count": 1,
        "cooldown_removed_count": 0,
        "final_event_count": 1,
    }
    for label, expected_mean in (("5m", 0.02), ("10m", 0.04), ("20m", 0.06)):
        horizon = curve["periods"]["train"]["horizons"][label]
        assert horizon["flow_counts"] == expected_flow
        assert horizon["overall"]["gross_mean_return"] == pytest.approx(
            expected_mean
        )

    paired = curve["periods"]["train"]["paired_comparisons"]["5m_vs_20m"]
    assert paired["flow_counts"]["paired_event_count"] == 1
    assert paired["flow_counts"]["cooldown_removed_count"] == 0
    assert paired["right_minus_left"]["mean_return"] == pytest.approx(0.04)

    mechanism = results["next_pulse_mechanism"]
    train_mechanism = mechanism["periods"]["train"]
    assert mechanism["event_horizon_minutes"] == 5
    assert mechanism["current_return_column"] == "forward_5m"
    assert train_mechanism["flow_counts"] == expected_flow
    assert train_mechanism["event_count"] == 1
    assert train_mechanism["volume_hit"]["rate"] == pytest.approx(1.0)

    comparison = results["core_variant_comparison"]
    selected_variant = comparison["training_selection"]["variants"][0]
    assert comparison["training_selection"]["reference_flow_counts"] == (
        expected_flow
    )
    assert comparison["training_selection"]["selected_variant_name"] == (
        "all_selected_events"
    )
    assert selected_variant["flow_counts"] == expected_flow
    assert selected_variant["overall"]["gross_mean_return"] == pytest.approx(0.02)
    assert comparison["fixed_evaluation"]["flow_counts"] == expected_flow


def test_response_curve_paired_comparison_uses_same_available_events(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    event_path = tmp_path / "events.parquet"
    events = pd.read_parquet(event_path)
    events.loc[events["candidate_id"].eq("train_4"), "forward_20m"] = float(
        "nan"
    )
    events.to_parquet(event_path, index=False)
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    state["strategy_result"]["params"]["event_horizon_minutes"] = 20
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
        ],
    )

    report = run_research_diagnostics(state)
    results = {item["id"]: item for item in report["results"]}
    curve = results["event_response_curve"]
    train = curve["periods"]["train"]
    independent_5m = train["horizons"]["5m"]["overall"]
    independent_20m = train["horizons"]["20m"]["overall"]
    paired = train["paired_comparisons"]["5m_vs_20m"]

    assert independent_5m["event_count"] == 3
    assert independent_20m["event_count"] == 2
    assert paired["flow_counts"]["paired_event_count"] == 2
    assert paired["left"]["gross_mean_return"] == pytest.approx(0.0025)
    assert paired["right"]["gross_mean_return"] == pytest.approx(0.0075)
    assert paired["left"]["gross_mean_return"] != pytest.approx(
        independent_5m["gross_mean_return"]
    )

    mechanism = results["next_pulse_mechanism"]
    assert mechanism["event_horizon_minutes"] == 20
    assert mechanism["current_return_column"] == "forward_20m"
    assert mechanism["periods"]["train"]["event_count"] == 2
    assert (
        mechanism["periods"]["train"]["flow_counts"][
            "invalid_return_event_count"
        ]
        == 1
    )


def test_requested_d1_condition_overrides_d5_for_three_diagnostics(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    event_path = tmp_path / "events.parquet"
    events = pd.read_parquet(event_path)
    events["pulse5_return"] = 0.0
    requested_values = {
        "train_1": -0.005,
        "train_2": -0.007,
        "dev_unselected": -0.005,
        "dev_selected": -0.007,
        "dev_2": -0.005,
    }
    for candidate_id, value in requested_values.items():
        events.loc[events["candidate_id"].eq(candidate_id), "pulse5_return"] = value
    events.to_parquet(event_path, index=False)

    current_threshold = -0.004851349670356973
    requested_threshold = -0.006113537117903958
    state["strategy_result"]["params"] = {
        "generic_selection_conditions": [
            {
                "feature": "pulse5_return",
                "operator": "<=",
                "value": current_threshold,
            }
        ]
    }
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    diagnostic_ids = (
        "event_response_curve",
        "execution_price_audit",
        "return_cost_distribution",
    )

    def run_with_condition(condition: str | None) -> dict[str, dict[str, object]]:
        state["diagnostic_request"] = build_diagnostic_request(
            state,
            [
                {
                    "id": diagnostic_id,
                    "reason": "test",
                    "parameters": (
                        {"selection_condition": condition}
                        if condition is not None
                        else {}
                    ),
                }
                for diagnostic_id in diagnostic_ids
            ],
        )
        report = run_research_diagnostics(state)
        return {item["id"]: item for item in report["results"]}

    baseline = run_with_condition(None)
    requested = run_with_condition(
        f"pulse5_return<={requested_threshold}"
    )
    same_as_current = run_with_condition(
        f"pulse5_return<={current_threshold}"
    )

    requested_condition = [
        {
            "feature": "pulse5_return",
            "operator": "<=",
            "value": requested_threshold,
        }
    ]
    request_source = "diagnostic_request.parameters.selection_condition"
    for diagnostic_id in diagnostic_ids:
        assert requested[diagnostic_id]["rule_source"] == request_source
        assert requested[diagnostic_id]["selection_conditions"] == (
            requested_condition
        )

    baseline_curve = baseline["event_response_curve"]
    requested_curve = requested["event_response_curve"]
    assert baseline_curve["periods"]["train"][
        "selected_event_count_before_return_availability"
    ] == 2
    assert requested_curve["periods"]["train"][
        "selected_event_count_before_return_availability"
    ] == 1
    assert requested_curve["candidate_scope"]["rule_source"] == request_source

    baseline_audit = baseline["execution_price_audit"]
    requested_audit = requested["execution_price_audit"]
    assert baseline_audit["periods"]["development"]["selected_signal_count"] == 2
    assert requested_audit["periods"]["development"]["selected_signal_count"] == 1

    baseline_cost = baseline["return_cost_distribution"]
    requested_cost = requested["return_cost_distribution"]
    assert baseline_cost["event_count"] == 2
    assert requested_cost["event_count"] == 1

    assert same_as_current["event_response_curve"]["periods"] == (
        baseline_curve["periods"]
    )
    assert same_as_current["execution_price_audit"]["periods"] == (
        baseline_audit["periods"]
    )
    assert same_as_current["return_cost_distribution"]["event_count"] == (
        baseline_cost["event_count"]
    )
    assert same_as_current["return_cost_distribution"]["gross_mean_return"] == (
        baseline_cost["gross_mean_return"]
    )


@pytest.mark.parametrize(
    "selection_condition",
    [
        "pulse5_return<=__import__('os')",
        "forward_5m>=0",
    ],
)
def test_invalid_requested_selection_condition_does_not_run_diagnostics(
    tmp_path, monkeypatch, selection_condition
) -> None:
    state = _state(tmp_path, monkeypatch)
    diagnostic_ids = (
        "event_response_curve",
        "execution_price_audit",
        "return_cost_distribution",
    )
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": diagnostic_id,
                "reason": "test",
                "parameters": {"selection_condition": selection_condition},
            }
            for diagnostic_id in diagnostic_ids
        ],
    )

    report = run_research_diagnostics(state)
    results = {item["id"]: item for item in report["results"]}

    assert report["status"] == "completed_with_limits"
    assert report["unsupported_requests"]
    for diagnostic_id in diagnostic_ids:
        result = results[diagnostic_id]
        assert result["status"] == "partial"
        assert result["rule_source"] == (
            "diagnostic_request.parameters.selection_condition"
        )
        assert result["selection_conditions"] == []
        assert result["unsupported_requests"]
    assert results["event_response_curve"]["periods"] == {}
    assert results["execution_price_audit"]["periods"] == {}
    assert "event_count" not in results["return_cost_distribution"]


def test_requested_boolean_selection_condition_is_parsed_strictly(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "event_response_curve",
                "reason": "test",
                "parameters": {"selection_condition": "no_early_spike==false"},
            }
        ],
    )

    curve = run_research_diagnostics(state)["results"][0]

    assert curve["selection_conditions"] == [
        {"feature": "no_early_spike", "operator": "==", "value": False}
    ]
    assert curve["periods"]["train"][
        "selected_event_count_before_return_availability"
    ] == 0
    assert curve["periods"]["development"][
        "selected_event_count_before_return_availability"
    ] == 1


def test_response_curve_reads_predicted_anchor_prices_for_requested_candidate(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    event_path = tmp_path / "events.parquet"
    rows = [
        _row(
            "event_2022",
            "2022-01-04 09:40:00",
            gross=0.01,
            trigger_position=9,
            pulse5_return=-0.01,
        ),
        _row(
            "event_2023",
            "2023-01-04 09:40:00",
            gross=0.03,
            trigger_position=9,
            pulse5_return=-0.01,
        ),
        _row(
            "event_2024",
            "2024-01-04 09:40:00",
            gross=0.02,
            trigger_position=9,
            pulse5_return=-0.01,
        ),
    ]
    pd.DataFrame(rows).to_parquet(event_path, index=False)

    raw_directory = tmp_path / "raw_minute"
    raw_directory.mkdir()
    raw_rows: list[dict[str, object]] = []
    prices_by_year = {
        2022: (101.0, 102.0),
        2023: (103.0, 101.0),
        2024: (102.0, 104.0),
    }
    for year, (trigger_exit, predicted_exit) in prices_by_year.items():
        date = pd.Timestamp(year=year, month=1, day=4)
        raw_rows.extend(
            [
                {"datetime": date + pd.Timedelta(hours=9, minutes=41), "open": 100.0, "close": 100.0},
                {"datetime": date + pd.Timedelta(hours=9, minutes=43), "open": 100.0, "close": 100.0},
                {"datetime": date + pd.Timedelta(hours=9, minutes=45), "open": 100.0, "close": trigger_exit},
                {"datetime": date + pd.Timedelta(hours=9, minutes=47), "open": 100.0, "close": predicted_exit},
            ]
        )
    pd.DataFrame(raw_rows).to_parquet(
        raw_directory / "sz000001.parquet", index=False
    )
    monkeypatch.setenv("QUANTA_RAW_MINUTE_DATA_DIR", str(raw_directory))

    d5_params = {
        "pulse5_return_threshold": -0.004851349670356973,
        "generic_selection_conditions": [
            {
                "feature": "pulse5_return",
                "operator": "<=",
                "value": -0.004851349670356973,
            }
        ],
    }
    state["candidate_records"] = [
        {
            "candidate_id": "candidate_005",
            "period_kind": "development",
            "strategy_params": d5_params,
        },
        {
            "candidate_id": "candidate_006",
            "period_kind": "development",
            "strategy_params": {"minimum_past_up_count": 4},
        },
    ]
    state["strategy_result"]["params"] = {"minimum_past_up_count": 4}
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "event_response_curve",
                "reason": "test",
                "parameters": {
                    "candidate_ids": ["candidate_005"],
                    "anchor_field": "predicted_ts",
                    "comparison_anchor_field": "trigger_ts",
                    "entry_offset_minutes": 1,
                    "return_horizons_minutes": [1, 3, 5],
                    "cooldown_minutes": 20,
                    "report_by_year": True,
                },
            }
        ],
    )

    report = run_research_diagnostics(state)

    result = report["results"][0]
    assert result["status"] == "completed"
    assert result["candidate_scope"]["evaluated_candidate_id"] == "candidate_005"
    assert result["candidate_scope"]["rule_source"] == "candidate_records.strategy_params"
    assert result["selection_conditions"] == d5_params["generic_selection_conditions"]
    assert result["applied_cooldown_minutes"] == 20
    anchor = result["anchor_comparison"]
    assert anchor["status"] == "completed"
    assert anchor["raw_price_read"]["requested_stock_file_count"] == 1
    assert anchor["raw_price_read"]["loaded_stock_file_count"] == 1

    train = anchor["periods"]["train"]
    assert train["trigger_anchor_5m"]["gross_mean_return"] == pytest.approx(0.02)
    assert train["predicted_anchor_5m"]["gross_mean_return"] == pytest.approx(0.015)
    assert train["predicted_minus_trigger_5m"]["mean_return"] == pytest.approx(-0.005)
    assert [row["year"] for row in train["by_year"]] == [2022, 2023]
    assert train["by_year"][0]["trigger_anchor_5m"]["gross_mean_return"] == pytest.approx(0.01)
    assert train["by_year"][1]["predicted_anchor_5m"]["gross_mean_return"] == pytest.approx(0.01)
    development = anchor["periods"]["development"]
    assert development["trigger_anchor_5m"]["gross_mean_return"] == pytest.approx(0.02)
    assert development["predicted_anchor_5m"]["gross_mean_return"] == pytest.approx(0.04)
    assert development["predicted_minus_trigger_5m"]["mean_return"] == pytest.approx(0.02)
    assert [row["year"] for row in development["by_year"]] == [2024]
    assert report["period_access"]["final_period_read"] is False


def test_response_curve_marks_missing_raw_price_files_partial(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    empty_raw_directory = tmp_path / "empty_raw"
    empty_raw_directory.mkdir()
    monkeypatch.setenv("QUANTA_RAW_MINUTE_DATA_DIR", str(empty_raw_directory))
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "event_response_curve",
                "reason": "test",
                "parameters": {
                    "anchor_field": "predicted_ts",
                    "comparison_anchor_field": "trigger_ts",
                    "return_horizons_minutes": [5],
                },
            }
        ],
    )

    report = run_research_diagnostics(state)

    result = report["results"][0]
    assert result["status"] == "partial"
    assert result["periods"]["train"]["horizons"]
    assert result["anchor_comparison"]["status"] == "partial"
    assert result["anchor_comparison"]["raw_price_read"]["missing_stock_file_count"] == 1
    assert report["status"] == "completed_with_limits"


def test_next_pulse_reports_post_event_return_groups_and_request_limits(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    current_candidate_id = state["candidate_records"][-1]["candidate_id"]
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "next_pulse_mechanism",
                "reason": "test",
                "parameters": {
                    "candidate_ids": [current_candidate_id, "candidate_999"],
                    "anchor_field": "predicted_ts",
                    "holding_minutes": 5,
                    "cooldown_minutes": 0,
                    "compare_scheduled_entry_with_trigger_entry": True,
                    "actual_next_pulse_evaluation_only": True,
                    "report_by_year": True,
                },
            }
        ],
    )

    report = run_research_diagnostics(state)

    result = report["results"][0]
    assert result["status"] == "partial"
    assert report["status"] == "completed_with_limits"
    assert result["candidate_scope"] == {
        "current_candidate_id": current_candidate_id,
        "requested_candidate_ids": [current_candidate_id, "candidate_999"],
        "evaluated_candidate_ids": [current_candidate_id],
        "unsupported_candidate_ids": ["candidate_999"],
    }
    assert result["requested_anchor_evaluation"]["status"] == "unavailable"
    assert "原始分钟开盘价" in result["requested_anchor_evaluation"]["required_data"]
    assert len(report["unsupported_requests"]) == 2
    assert "不能作为策略信号" in result["post_event_grouping_warning"]

    comparison = result["periods"]["train"]["post_event_return_comparison"]
    groups = comparison["groups"]
    assert set(groups) == {"volume_hit_true", "volume_hit_false"}
    true_5m = groups["volume_hit_true"]["returns"]["forward_5m"]
    assert true_5m == {
        "sample_count": 2,
        "mean_return": pytest.approx(0.0075),
        "median_return": pytest.approx(0.0075),
        "up_rate": pytest.approx(0.5),
    }
    false_5m = groups["volume_hit_false"]["returns"]["forward_5m"]
    assert false_5m["sample_count"] == 1
    assert false_5m["mean_return"] == pytest.approx(0.01)
    assert set(groups["volume_hit_true"]["returns"]) == {
        "target_minute_return",
        "forward_5m",
        "forward_10m",
        "forward_20m",
    }
    by_year = comparison["by_year"]
    assert [row["year"] for row in by_year] == [2022, 2023]
    assert (
        by_year[0]["groups"]["volume_hit_true"]["returns"]["forward_5m"][
            "sample_count"
        ]
        == 1
    )
    assert report["period_access"]["final_period_read"] is False
    assert "2025" not in str(result)


def test_next_pulse_rejects_request_for_only_noncurrent_candidate(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "next_pulse_mechanism",
                "reason": "test",
                "parameters": {"candidate_ids": ["candidate_999"]},
            }
        ],
    )

    report = run_research_diagnostics(state)

    result = report["results"][0]
    assert result["status"] == "unsupported"
    assert result["periods"] == {}
    assert result["candidate_scope"]["unsupported_candidate_ids"] == [
        "candidate_999"
    ]
    assert report["status"] == "completed_with_limits"
    assert report["unsupported_requests"]


def test_pulse5_threshold_selects_events_for_all_strategy_diagnostics(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["strategy_result"]["params"] = {"pulse5_return_threshold": -0.001}
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "rule_waterfall", "reason": "test", "parameters": {}},
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
        ],
    )

    report = run_research_diagnostics(state)

    results = {item["id"]: item for item in report["results"]}
    waterfall = results["rule_waterfall"]
    train_steps = waterfall["periods"]["train"]["steps"]
    assert waterfall["selection_fields_only"] == ["pulse5_return"]
    assert [step["rule"] for step in train_steps] == [
        "all_candidates",
        "pulse5_return<=-0.001",
    ]
    assert train_steps[-1]["event_count"] == 1

    curve = results["event_response_curve"]
    assert curve["selection_fields_only"] == ["pulse5_return"]
    assert (
        curve["periods"]["train"][
            "selected_event_count_before_return_availability"
        ]
        == 1
    )
    assert (
        curve["periods"]["development"][
            "selected_event_count_before_return_availability"
        ]
        == 1
    )

    mechanism = results["next_pulse_mechanism"]
    assert mechanism["selection_fields_only"] == ["pulse5_return"]
    assert mechanism["periods"]["train"]["event_count"] == 1
    assert mechanism["periods"]["development"]["event_count"] == 1


def test_legacy_pulse1_position_threshold_selects_events_for_all_diagnostics(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    event_path = tmp_path / "events.parquet"
    events = pd.read_parquet(event_path)
    events["pulse1_position"] = 223
    events.loc[
        events["candidate_id"].isin(["train_2", "dev_2"]),
        "pulse1_position",
    ] = 224
    events.to_parquet(event_path, index=False)
    state["strategy_result"]["params"] = {"pulse1_position_threshold": 224}
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "rule_waterfall", "reason": "test", "parameters": {}},
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
        ],
    )

    report = run_research_diagnostics(state)

    results = {item["id"]: item for item in report["results"]}
    waterfall = results["rule_waterfall"]
    train_steps = waterfall["periods"]["train"]["steps"]
    assert waterfall["selection_fields_only"] == ["pulse1_position"]
    assert [step["rule"] for step in train_steps] == [
        "all_candidates",
        "pulse1_position>=224",
    ]
    assert train_steps[-1]["event_count"] == 1

    curve = results["event_response_curve"]
    assert curve["selection_fields_only"] == ["pulse1_position"]
    assert (
        curve["periods"]["train"][
            "selected_event_count_before_return_availability"
        ]
        == 1
    )
    assert (
        curve["periods"]["development"][
            "selected_event_count_before_return_availability"
        ]
        == 1
    )

    mechanism = results["next_pulse_mechanism"]
    assert mechanism["selection_fields_only"] == ["pulse1_position"]
    assert mechanism["periods"]["train"]["event_count"] == 1
    assert mechanism["periods"]["development"]["event_count"] == 1


def test_generic_selection_conditions_take_priority_for_all_strategy_diagnostics(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["strategy_result"]["params"] = {
        "minimum_past_up_count": 99,
        "pulse5_return_threshold": -99.0,
        "generic_selection_conditions": [
            {"feature": "past_up_count", "operator": ">=", "value": 4},
            {"feature": "pulse5_return", "operator": "<=", "value": -0.001},
        ],
    }
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "rule_waterfall", "reason": "test", "parameters": {}},
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
        ],
    )

    report = run_research_diagnostics(state)

    results = {item["id"]: item for item in report["results"]}
    waterfall = results["rule_waterfall"]
    train_steps = waterfall["periods"]["train"]["steps"]
    assert waterfall["selection_fields_only"] == [
        "past_up_count",
        "pulse5_return",
    ]
    assert [step["rule"] for step in train_steps] == [
        "all_candidates",
        "past_up_count>=4",
        "pulse5_return<=-0.001",
    ]
    assert train_steps[-1]["event_count"] == 1

    curve = results["event_response_curve"]
    assert curve["selection_fields_only"] == [
        "past_up_count",
        "pulse5_return",
    ]
    assert (
        curve["periods"]["train"][
            "selected_event_count_before_return_availability"
        ]
        == 1
    )
    assert (
        curve["periods"]["development"][
            "selected_event_count_before_return_availability"
        ]
        == 1
    )

    mechanism = results["next_pulse_mechanism"]
    assert mechanism["selection_fields_only"] == [
        "past_up_count",
        "pulse5_return",
    ]
    assert mechanism["periods"]["train"]["event_count"] == 1
    assert mechanism["periods"]["development"]["event_count"] == 1


def test_empty_generic_selection_conditions_override_legacy_params(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["strategy_result"]["params"] = {
        "minimum_past_up_count": 99,
        "generic_selection_conditions": [],
    }
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [{"id": "rule_waterfall", "reason": "test", "parameters": {}}],
    )

    waterfall = run_research_diagnostics(state)["results"][0]

    assert waterfall["selection_fields_only"] == []
    train_steps = waterfall["periods"]["train"]["steps"]
    assert [step["rule"] for step in train_steps] == ["all_candidates"]
    assert train_steps[0]["event_count"] == 4


@pytest.mark.parametrize(
    "conditions",
    [
        None,
        ["past_up_count>=4"],
        [{"feature": "past_up_count", "operator": ">="}],
        [
            {
                "feature": "past_up_count",
                "operator": ">=",
                "value": 4,
                "note": "extra",
            }
        ],
        [{"feature": "forward_5m", "operator": ">=", "value": 0.0}],
        [{"feature": "past_up_count", "operator": ">", "value": 4}],
        [{"feature": "no_early_spike", "operator": "<=", "value": True}],
    ],
)
def test_generic_selection_conditions_reject_invalid_rules(
    tmp_path, monkeypatch, conditions
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["strategy_result"]["params"] = {
        "generic_selection_conditions": conditions
    }
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [{"id": "account_separation", "reason": "test", "parameters": {}}],
    )

    with pytest.raises(ValueError):
        run_research_diagnostics(state)


def test_low_ma5_distance_screening_keeps_current_rule_and_locks_thresholds() -> None:
    selection_rows: list[dict[str, object]] = []
    confirmation_rows: list[dict[str, object]] = []
    for index in range(1_100):
        selected_by_current_rule = index < 1_000
        distance = -0.10 + 0.20 * index / 1_099
        gross = 0.004 - 0.02 * distance
        selection_date = pd.Timestamp(
            "2022-06-01" if index < 500 else "2022-07-01"
        )
        confirmation_date = pd.Timestamp(
            "2023-06-01" if index < 500 else "2023-07-01"
        )
        common = {
            "candidate_id": f"event_{index:04d}",
            "code": f"stock_{index:04d}",
            "trigger_ts": selection_date + pd.Timedelta(hours=10),
            "date": selection_date,
            "pulse5_return": -0.01 if selected_by_current_rule else 0.01,
            "gross_return": gross if selected_by_current_rule else 1.0,
            "trigger_low_to_prev5_close_ma5_distance": distance,
            "trigger_low_to_live_close_ma5_distance": distance * 0.8,
            "analysis_only_full_day_low_to_close_ma5_distance": distance * 1.5,
        }
        selection_rows.append(common)
        confirmation_rows.append(
            {
                **common,
                "candidate_id": f"confirm_{index:04d}",
                "trigger_ts": confirmation_date + pd.Timedelta(hours=10),
                "date": confirmation_date,
                "gross_return": gross * 0.75 if selected_by_current_rule else 1.0,
            }
        )

    params = {
        "event_horizon_minutes": 20,
        "generic_selection_conditions": [
            {
                "feature": "pulse5_return",
                "operator": "<=",
                "value": -0.006,
            }
        ],
    }
    result = research_diagnostics._low_ma5_distance_screening(
        {
            "selection": pd.DataFrame(selection_rows),
            "internal_check": pd.DataFrame(confirmation_rows),
        },
        params,
        cost_rate=0.0016,
        cooldown_minutes=20,
        horizon_minutes=20,
        source_candidate_id="candidate_011",
    )

    assert result["status"] == "completed"
    assert result["source_candidate_id"] == "candidate_011"
    assert result["baseline"]["selection"]["event_count"] == 1_000
    assert result["baseline"]["confirmation"]["event_count"] == 1_000
    assert result["minimum_selection_event_count"] == 100
    assert result["minimum_selection_event_count_rule"] == (
        "max(100, ceil(selection_baseline_event_count * 0.05))"
    )
    assert result["fixed_selection_quantile_levels"] == [
        0.10,
        0.25,
        0.50,
        0.75,
        0.90,
    ]
    candidates = result["training_ranked_candidates"]
    assert candidates
    assert {
        item["condition"]["feature"] for item in candidates
    } == {
        "trigger_low_to_prev5_close_ma5_distance",
        "trigger_low_to_live_close_ma5_distance",
    }
    assert all(item["selection"]["event_count"] >= 100 for item in candidates)
    assert all("changes_from_baseline" in item for item in candidates)
    assert {
        item["condition"]["feature"]
        for item in candidates
        if item["selection_quantile_level"] == 0.10
        and item["condition"]["operator"] == "<="
    } == set(research_diagnostics.LOW_MA5_SAFE_FEATURES)
    assert result["outcome_or_post_trigger_fields_used_for_selection"] == []

    monthly_keys = {
        "month_count",
        "gross_positive_month_count",
        "net_positive_month_count",
        "gross_mean_return_min",
        "gross_mean_return_median",
        "gross_mean_return_max",
        "net_mean_return_min",
        "net_mean_return_median",
        "net_mean_return_max",
    }

    def assert_monthly(metrics: dict[str, object]) -> None:
        stability = metrics["monthly_stability"]
        assert isinstance(stability, dict)
        assert set(stability) == monthly_keys
        assert stability["month_count"] >= 1
        assert (
            stability["gross_mean_return_min"]
            <= stability["gross_mean_return_median"]
            <= stability["gross_mean_return_max"]
        )
        assert (
            stability["net_mean_return_min"]
            <= stability["net_mean_return_median"]
            <= stability["net_mean_return_max"]
        )

    assert_monthly(result["baseline"]["selection"])
    assert_monthly(result["baseline"]["confirmation"])
    assert result["baseline"]["selection"]["monthly_stability"][
        "month_count"
    ] == 2
    for candidate in candidates:
        assert_monthly(candidate["selection"])
        assert_monthly(candidate["confirmation"])

    full_day = result["full_day_descriptive_analysis"]
    assert full_day["status"] == "descriptive_only"
    assert full_day["strategy_eligible"] is False
    assert full_day["can_nominate_candidate"] is False
    assert full_day["bins"]
    assert all(item["strategy_eligible"] is False for item in full_day["bins"])
    for item in full_day["bins"]:
        assert_monthly(item["selection"])
        assert_monthly(item["confirmation"])


def test_low_ma5_iteration_uses_configured_selection_and_confirmation_only(
    tmp_path, monkeypatch
) -> None:
    rows: list[dict[str, object]] = []
    for year, distance_offset in ((2022, 0.0), (2023, 10.0), (2024, 100.0)):
        for index in range(1_000):
            distance = distance_offset + index / 999
            if year == 2022:
                gross = 0.01 - 0.005 * distance
            elif year == 2023:
                gross = 0.002
            else:
                gross = 5.0 + distance
            date = pd.Timestamp(year=year, month=6, day=1)
            rows.append(
                {
                    "candidate_id": f"event_{year}_{index:04d}",
                    "code": f"stock_{index:04d}",
                    "trigger_ts": date + pd.Timedelta(hours=10),
                    "date": date,
                    "pulse5_return": -0.01,
                    "gross_return": gross,
                    "forward_20m": gross,
                    "trigger_low_to_prev5_close_ma5_distance": distance,
                    "trigger_low_to_live_close_ma5_distance": distance * 0.8,
                    "analysis_only_full_day_low_to_close_ma5_distance": (
                        distance * 1.5
                    ),
                }
            )
    all_events = pd.DataFrame(rows)
    read_periods: list[tuple[str, str]] = []

    def fake_read_event_frame(
        paths, *, start: str, end: str, horizon_minutes: int
    ) -> pd.DataFrame:
        del paths, horizon_minutes
        read_periods.append((start, end))
        start_date = pd.Timestamp(start)
        end_date = pd.Timestamp(end)
        return all_events.loc[
            all_events["date"].between(start_date, end_date)
        ].copy()

    monkeypatch.setattr(
        research_diagnostics,
        "_resolve_event_paths",
        lambda: ["unused.parquet"],
    )
    monkeypatch.setattr(
        research_diagnostics,
        "_read_event_frame",
        fake_read_event_frame,
    )
    state = _state(tmp_path, monkeypatch)
    state["experiment_spec"].update(
        {
            "research_selection_start": "2022-01-01",
            "research_selection_end": "2022-12-31",
            "research_confirmation_start": "2023-01-01",
            "research_confirmation_end": "2023-12-31",
        }
    )
    state["research_stage"] = "iteration"
    state["strategy_result"]["params"] = {
        "event_horizon_minutes": 20,
        "generic_selection_conditions": [
            {"feature": "pulse5_return", "operator": "<=", "value": -0.006}
        ],
    }
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "low_ma5_distance_screening", "parameters": {}},
            {"id": "period_metrics", "parameters": {}},
        ],
    )

    report = run_research_diagnostics(state)

    assert read_periods == [
        ("2022-01-01", "2022-12-31"),
        ("2023-01-01", "2023-12-31"),
    ]
    assert report["period_access"] == {
        "research_stage": "iteration",
        "period_source": "experiment_spec.research_selection_confirmation",
        "selection": {"start": "2022-01-01", "end": "2022-12-31"},
        "confirmation": {"start": "2023-01-01", "end": "2023-12-31"},
        "development_read": False,
        "final_period_read": False,
    }
    results = {item["id"]: item for item in report["results"]}
    screening = results["low_ma5_distance_screening"]
    assert screening["selection_period_name"] == "selection"
    assert screening["confirmation_period_name"] == "confirmation"
    assert screening["baseline"]["confirmation"]["gross_mean_return"] == pytest.approx(
        0.002
    )
    assert max(
        item["condition"]["value"]
        for item in screening["training_ranked_candidates"]
        if item["condition"]["feature"]
        == "trigger_low_to_prev5_close_ma5_distance"
    ) < 1.0
    assert any(
        item["selection_quantile_level"] == 0.10
        and item["condition"]["operator"] == "<="
        and item["selection"]["event_count"] == 100
        for item in screening["training_ranked_candidates"]
    )
    assert set(results["period_metrics"]["periods"]) == {
        "selection",
        "confirmation",
    }
    assert "2024" not in str(report)


def test_low_ma5_fields_have_separate_selection_permissions() -> None:
    safe_params = {
        "generic_selection_conditions": [
            {
                "feature": "trigger_low_to_prev5_close_ma5_distance",
                "operator": "<=",
                "value": -0.02,
            },
            {
                "feature": "trigger_low_to_live_close_ma5_distance",
                "operator": ">=",
                "value": -0.08,
            },
        ]
    }
    assert research_diagnostics._normalise_generic_selection_conditions(
        safe_params
    ) == safe_params["generic_selection_conditions"]

    with pytest.raises(ValueError, match="不允许的条件字段"):
        research_diagnostics._normalise_generic_selection_conditions(
            {
                "generic_selection_conditions": [
                    {
                        "feature": "analysis_only_full_day_low_to_close_ma5_distance",
                        "operator": "<=",
                        "value": -0.02,
                    }
                ]
            }
        )

    normalized = normalize_diagnostic_items(
        [{"id": "low_ma5_distance_screening", "parameters": {}}]
    )
    assert normalized[0]["id"] == "low_ma5_distance_screening"


def test_low_ma5_distance_screening_is_dispatched_by_report_builder(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "low_ma5_distance_screening",
                "reason": "测试五日均线距离",
                "parameters": {},
            }
        ],
    )

    report = run_research_diagnostics(state)

    result = report["results"][0]
    assert result["id"] == "low_ma5_distance_screening"
    assert result["status"] == "partial"
    assert set(result["missing_fields"]) == {
        "trigger_low_to_prev5_close_ma5_distance",
        "trigger_low_to_live_close_ma5_distance",
        "analysis_only_full_day_low_to_close_ma5_distance",
    }


def test_core_variant_comparison_selects_on_train_then_checks_same_rule(
    tmp_path, monkeypatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    variants = [
        {
            "name": "all_core_events",
            "conditions": [
                {"field": "past_up_count", "operator": ">=", "value": 4}
            ],
        },
        {
            "name": "positive_pulses",
            "conditions": [
                {"field": "pulse_return_sum", "operator": ">=", "value": 0.0}
            ],
        },
    ]
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "core_variant_comparison",
                "reason": "test",
                "parameters": {"variants": variants},
            }
        ],
    )

    report = run_research_diagnostics(state)

    comparison = report["results"][0]
    selection = comparison["training_selection"]
    assert selection["selected_variant_name"] == "positive_pulses"
    assert selection["ranked_variant_names"][0] == "positive_pulses"
    assert len(selection["variants"][0]["by_year"]) == 2
    assert comparison["fixed_evaluation"]["name"] == "positive_pulses"
    assert comparison["fixed_evaluation"]["conditions"] == [
        {"feature": "pulse_return_sum", "operator": ">=", "value": 0.0}
    ]
    assert comparison["outcome_fields_used_for_selection"] == []


def test_core_variant_comparison_has_five_fixed_defaults(tmp_path, monkeypatch) -> None:
    state = _state(tmp_path, monkeypatch)
    state["experiment_spec"]["event_cooldown_minutes"] = 0
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "core_variant_comparison",
                "reason": "test",
                "parameters": {},
            }
        ],
    )

    comparison = run_research_diagnostics(state)["results"][0]

    variants = comparison["training_selection"]["variants"]
    assert [item["name"] for item in variants] == [
        "current_baseline",
        "positive_stable_pulses",
        "persistent_price_acceptance",
        "strong_consistent_volume",
        "exact_rhythm_confirmation",
    ]
    assert len(variants) == 5


@pytest.mark.parametrize(
    "variants",
    [
        [
            {
                "name": "uses_result",
                "conditions": [
                    {"field": "forward_5m", "operator": ">=", "value": 0.0}
                ],
            }
        ],
        [
            {
                "name": "bad_operator",
                "conditions": [
                    {"field": "past_up_count", "operator": ">", "value": 4}
                ],
            }
        ],
        [
            {
                "name": f"variant_{index}",
                "conditions": [
                    {"field": "past_up_count", "operator": ">=", "value": 4}
                ],
            }
            for index in range(6)
        ],
    ],
)
def test_core_variant_comparison_rejects_unsafe_rules(
    tmp_path, monkeypatch, variants
) -> None:
    state = _state(tmp_path, monkeypatch)
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {
                "id": "core_variant_comparison",
                "reason": "test",
                "parameters": {"variants": variants},
            }
        ],
    )

    with pytest.raises(ValueError):
        run_research_diagnostics(state)


@pytest.mark.parametrize("stage_source", ["request", "state"])
def test_initial_research_uses_only_split_training_period(
    tmp_path, monkeypatch, stage_source
) -> None:
    state = _state(tmp_path, monkeypatch)
    real_read_parquet = pd.read_parquet
    read_upper_bounds: list[pd.Timestamp] = []

    def tracked_read_parquet(*args, **kwargs):
        filters = kwargs.get("filters", [])
        if len(filters) >= 2:
            read_upper_bounds.append(pd.Timestamp(filters[1][2]))
        return real_read_parquet(*args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", tracked_read_parquet)
    state["diagnostic_request"] = build_diagnostic_request(
        state,
        [
            {"id": "event_response_curve", "reason": "test", "parameters": {}},
            {"id": "next_pulse_mechanism", "reason": "test", "parameters": {}},
        ],
    )
    if stage_source == "request":
        state["diagnostic_request"]["research_stage"] = "initial"
    else:
        state["research_stage"] = "initial_research"

    report = run_research_diagnostics(state)

    assert report["period_access"] == {
        "research_stage": "initial",
        "selection": {"start": "2022-01-01", "end": "2022-12-31"},
        "internal_check": {"start": "2023-01-01", "end": "2023-12-31"},
        "development_read": False,
        "final_period_read": False,
    }
    assert "2024" not in str(report)
    assert read_upper_bounds
    assert max(read_upper_bounds) <= pd.Timestamp("2024-01-01")
    assert {
        *report["results"][0]["periods"],
    } == {"selection", "internal_check"}


def test_new_diagnostic_ids_are_accepted() -> None:
    items = normalize_diagnostic_items(
        [
            {"id": "event_response_curve", "parameters": {}},
            {"id": "next_pulse_mechanism", "parameters": {}},
            {"id": "core_variant_comparison", "parameters": {}},
        ]
    )

    assert [item["id"] for item in items] == [
        "event_response_curve",
        "next_pulse_mechanism",
        "core_variant_comparison",
    ]


def test_diagnostic_request_preserves_decisions_and_research_stage() -> None:
    state = init_state("test", max_epochs=3)
    state["research_stage"] = "initial_research"

    request = build_diagnostic_request(
        state,
        [
            {
                "id": "event_response_curve",
                "reason": "test",
                "parameters": {},
                "decision_if_positive": "进入正式候选",
                "decision_if_negative": "停止当前方向",
            }
        ],
    )

    assert request["research_stage"] == "initial_research"
    assert request["items"][0]["decision_if_positive"] == "进入正式候选"
    assert request["items"][0]["decision_if_negative"] == "停止当前方向"
