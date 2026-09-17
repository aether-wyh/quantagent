from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from quanta_agents.experiment_runner import load_experiment_ideas


def _write_experiment(path: Path, name: str, *, horizon: int) -> None:
    (path / name).write_text(
        f"""
user_idea: 测试分钟量能策略
train_start: "2022-01-01"
train_end: "2023-12-31"
validate_start: "2024-01-01"
validate_end: "2024-12-31"
backtest_start: "2025-01-01"
backtest_end: "2025-12-31"
bar_interval: "1m"
backtest_mode: "event_parquet"
event_horizon_minutes: {horizon}
buy_cost: 0.0003
sell_cost: 0.0008
sell_cost_before_change: 0.0013
sell_cost_change_date: "2023-08-28"
slippage: 0.0002
capital: 2000000
run_final_test: false
allow_final_test: "false"
development_folds: "4"
gap_trading_days: 10
run_cost_stress: true
run_delay_stress: "true"
walk_forward_development: true
min_fold_pass_ratio: 0.75
initial_research_before_strategy: true
max_diagnostic_rounds: 4
min_formal_candidates_before_stop: 2
research_selection_start: "2022-01-01"
research_selection_end: "2022-12-31"
research_confirmation_start: "2023-01-01"
research_confirmation_end: "2023-12-31"
stop_required_diagnostics: [event_response_curve, next_pulse_mechanism]
evaluation:
  min_trade_count: 20
  min_event_success_rate: 0.35
  event_success_metric: gross_up_rate
universe:
  - symbols: ["600000.SH"]
    asset: "中国股票"
    description: "测试股票"
""".strip(),
        encoding="utf-8",
    )


def test_load_experiment_keeps_runtime_options(tmp_path: Path) -> None:
    _write_experiment(tmp_path, "minute.yaml", horizon=5)

    ideas = load_experiment_ideas(tmp_path)

    assert len(ideas) == 1
    payload = ideas[0][2]
    assert payload["bar_interval"] == "1m"
    assert payload["backtest_mode"] == "event_parquet"
    assert payload["event_horizon_minutes"] == 5
    assert payload["buy_cost"] == 0.0003
    assert payload["sell_cost"] == 0.0008
    assert payload["sell_cost_before_change"] == 0.0013
    assert payload["sell_cost_change_date"] == "2023-08-28"
    assert payload["slippage"] == 0.0002
    assert payload["capital"] == 2_000_000
    assert payload["run_final_test"] is False
    assert payload["allow_final_test"] is False
    assert payload["development_folds"] == 4
    assert payload["gap_trading_days"] == 10
    assert payload["run_cost_stress"] is True
    assert payload["run_delay_stress"] is True
    assert payload["walk_forward_development"] is True
    assert payload["min_fold_pass_ratio"] == 0.75
    assert payload["initial_research_before_strategy"] is True
    assert payload["max_diagnostic_rounds"] == 4
    assert payload["min_formal_candidates_before_stop"] == 2
    assert payload["research_selection_start"] == "2022-01-01"
    assert payload["research_confirmation_end"] == "2023-12-31"
    assert payload["stop_required_diagnostics"] == [
        "event_response_curve",
        "next_pulse_mechanism",
    ]
    assert payload["evaluation"] == {
        "min_trade_count": 20.0,
        "min_event_success_rate": 0.35,
        "event_success_metric": "gross_up_rate",
    }


def test_load_experiment_can_select_one_file(tmp_path: Path) -> None:
    _write_experiment(tmp_path, "first.yaml", horizon=5)
    _write_experiment(tmp_path, "second.yaml", horizon=10)

    with patch.dict("os.environ", {"QUANTA_EXPERIMENT_FILE": "second.yaml"}):
        ideas = load_experiment_ideas(tmp_path)

    assert [item[0] for item in ideas] == ["second.yaml"]
    assert ideas[0][2]["event_horizon_minutes"] == 10


def test_load_experiment_accepts_dataset_defined_universe(tmp_path: Path) -> None:
    path = tmp_path / "minute.yaml"
    _write_experiment(tmp_path, path.name, horizon=5)
    text = path.read_text(encoding="utf-8").replace(
        'symbols: ["600000.SH"]',
        "symbols: dataset:periodic_minute_events",
    )
    path.write_text(text, encoding="utf-8")

    payload = load_experiment_ideas(tmp_path)[0][2]

    assert payload.get("symbols", []) == []
    assert payload["universe"][0]["type"] == "dataset_defined"
    assert payload["universe"][0]["dataset"] == "periodic_minute_events"


def test_load_experiment_rejects_invalid_research_runtime_options(tmp_path: Path) -> None:
    path = tmp_path / "minute.yaml"
    _write_experiment(tmp_path, path.name, horizon=5)
    text = path.read_text(encoding="utf-8").replace(
        'development_folds: "4"',
        "development_folds: 0",
    )
    path.write_text(text, encoding="utf-8")

    assert load_experiment_ideas(tmp_path) == []


def test_load_experiment_defaults_to_no_final_test(tmp_path: Path) -> None:
    path = tmp_path / "minute.yaml"
    _write_experiment(tmp_path, path.name, horizon=5)
    text = path.read_text(encoding="utf-8")
    text = text.replace("run_final_test: false\n", "")
    text = text.replace('allow_final_test: "false"\n', "")
    path.write_text(text, encoding="utf-8")

    payload = load_experiment_ideas(tmp_path)[0][2]

    assert payload["run_final_test"] is False
    assert payload["allow_final_test"] is False


def test_load_experiment_rejects_invalid_event_success_metric(tmp_path: Path) -> None:
    path = tmp_path / "minute.yaml"
    _write_experiment(tmp_path, path.name, horizon=5)
    text = path.read_text(encoding="utf-8").replace(
        "event_success_metric: gross_up_rate",
        "event_success_metric: unknown_rate",
    )
    path.write_text(text, encoding="utf-8")

    assert load_experiment_ideas(tmp_path) == []


def test_load_low_ma5_research_experiment_is_development_only() -> None:
    experiments_dir = Path(__file__).resolve().parents[1] / "experiments"
    experiment_name = "periodic_volume_minute_low_ma5_research.yaml"

    with patch.dict("os.environ", {"QUANTA_EXPERIMENT_FILE": experiment_name}):
        ideas = load_experiment_ideas(experiments_dir)

    assert len(ideas) == 1
    payload = ideas[0][2]
    assert "2025" not in payload["user_idea"]
    assert payload["run_final_test"] is False
    assert payload["allow_final_test"] is False
    assert payload["research_selection_start"] == "2022-01-01"
    assert payload["research_selection_end"] == "2022-12-31"
    assert payload["research_confirmation_start"] == "2023-01-01"
    assert payload["research_confirmation_end"] == "2023-12-31"
    assert payload["validate_start"] == "2024-01-01"
    assert payload["validate_end"] == "2024-12-31"
    assert payload["event_horizon_minutes"] == 20
    assert payload["event_cooldown_minutes"] == 20
    assert payload["buy_cost"] == 0.0003
    assert payload["sell_cost"] == 0.0008
    assert payload["slippage"] == 0.00025
    assert payload["min_formal_candidates_before_stop"] >= 12
    assert "low_ma5_distance_screening" in payload["stop_required_diagnostics"]
    assert "trigger_low_to_prev5_close_ma5_distance" in payload["user_idea"]
    assert "trigger_low_to_live_close_ma5_distance" in payload["user_idea"]
    assert "analysis_only_full_day_low_to_close_ma5_distance" in payload["user_idea"]
    assert "严禁把它写入策略" in payload["user_idea"]
    assert payload["evaluation"] == {
        "min_trade_count": 100.0,
        "min_event_net_mean": 0.0,
        "min_event_success_rate": 0.35,
        "event_success_metric": "gross_up_rate",
    }
