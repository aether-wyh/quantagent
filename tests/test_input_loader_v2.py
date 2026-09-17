from __future__ import annotations

from pathlib import Path

import pytest

from quanta_agents.input_loader_v2 import load_v2_request
from quanta_agents.research_evaluation import build_development_folds
from quanta_agents.v2_runtime import build_stage_spec, default_cn_daily_v2_profile


def test_v2_yaml_can_contain_only_one_sentence(tmp_path: Path) -> None:
    path = tmp_path / "idea.yaml"
    path.write_text("user_idea: 30天盘整后连续放量\n", encoding="utf-8")

    result = load_v2_request(path)

    assert result["source_text"] == "30天盘整后连续放量"
    assert result["source_kind"] == "plain_text"
    assert len(result["source_sha256"]) == 64


def test_v2_yaml_can_point_to_a_report(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("# 研究想法\n价量现象", encoding="utf-8")
    request = tmp_path / "request.yaml"
    request.write_text("workflow_version: v2\nsource_file: report.md\n", encoding="utf-8")

    result = load_v2_request(request)

    assert "价量现象" in result["source_text"]
    assert result["source_kind"] == "report_file"


def test_v2_request_rejects_text_and_file_at_same_time(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("user_idea: A\nsource_file: a.md\n", encoding="utf-8")

    with pytest.raises(ValueError, match="只能选一种"):
        load_v2_request(path)


def test_runtime_separates_research_confirmation_and_final_periods() -> None:
    profile = default_cn_daily_v2_profile()
    research = build_stage_spec(profile, experiment_id="x", stage="research")
    confirmation = build_stage_spec(profile, experiment_id="x", stage="confirmation")
    final = build_stage_spec(profile, experiment_id="x", stage="final")

    assert research["train_end"] == "2017-12-29"
    assert research["development_start"] == "2018-01-02"
    assert research["development_end"] == "2021-12-31"
    assert confirmation["train_end"] == "2021-12-31"
    assert confirmation["development_start"] == "2022-01-04"
    assert confirmation["development_end"] == "2024-12-31"
    assert final["train_end"] == "2024-12-31"
    assert final["development_start"] == "2025-01-02"
    assert final["development_end"] == "2025-12-31"
    assert research["run_final_test"] is False
    assert research["universe"][0]["type"] == "dataset_defined"
    assert research["position_plan_contract"] == {
        "mode": "fixed_target_until_exit",
        "single_stock_weight": 0.10,
        "position_rule": (
            "旧计划比例保持到各自退出；当日新计划少于10只且现金足够时每只10%，"
            "否则只在当日新计划之间平均分配剩余现金"
        ),
    }
    assert profile["baseline_defaults"]["consecutive_high_volume_days"] == 2
    assert research["market_day_continuity_contract"] == {
        "mode": "consecutive_market_trading_days",
        "consecutive_days": 2,
        "condition_field": "consecutive_high_volume_days",
        "missing_bar_action": "condition_false",
    }


def test_runtime_fixes_daily_entry_and_exit_execution() -> None:
    execution = default_cn_daily_v2_profile()["execution"]

    assert execution["signal_to_trade"] == "信号日收盘确认，下一实际交易日开盘执行"
    assert execution["default_holding_days"] == 5
    assert execution["exit_execution"] == (
        "买入日记为T，完整持有5个实际交易日后，在T+5开盘卖出"
    )
    assert execution["missing_bar_policy"] == (
        "某股票当日缺少K线时不成交；已有计划持仓目标继续到原退出日，"
        "不得因缺K清零；恢复K线后按当日仍有效的计划执行；"
        "未买到不顺延原计划退出日；不得读取或推断下一交易日是否有K线"
    )
    assert execution["buy_cost"] == 0.0003
    assert execution["sell_cost_before_change"] == 0.0013
    assert execution["sell_cost_change_date"] == "2023-08-28"
    assert execution["sell_cost"] == 0.0008
    assert execution["cost_rule"] == (
        "买入费0.0003；2018-01-01至2023-08-27卖出费0.0013；"
        "2023-08-28起卖出费0.0008"
    )

    research = build_stage_spec(
        default_cn_daily_v2_profile(), experiment_id="fees", stage="research"
    )
    assert research["sell_cost_before_change"] == 0.0013
    assert research["sell_cost_change_date"] == "2023-08-28"
    assert research["sell_cost"] == 0.0008
    assert research["cost_rule"] == execution["cost_rule"]


def test_runtime_does_not_add_fixed_plan_check_without_declaration() -> None:
    profile = default_cn_daily_v2_profile()
    del profile["baseline_defaults"]["position_plan_contract"]

    research = build_stage_spec(profile, experiment_id="dynamic", stage="research")

    assert "position_plan_contract" not in research


def test_runtime_does_not_add_continuous_day_check_without_declaration() -> None:
    profile = default_cn_daily_v2_profile()
    del profile["baseline_defaults"]["market_day_continuity_contract"]

    research = build_stage_spec(profile, experiment_id="no_continuity", stage="research")

    assert "market_day_continuity_contract" not in research


def test_confirmation_folds_only_add_dates_before_each_test_fold() -> None:
    profile = default_cn_daily_v2_profile()
    confirmation = build_stage_spec(
        profile,
        experiment_id="x",
        stage="confirmation",
    )
    confirmation["min_development_fold_days"] = 1
    trading_dates = [
        "2022-01-04",
        "2022-06-01",
        "2022-12-30",
        "2023-01-03",
        "2023-06-01",
        "2023-12-29",
        "2024-01-02",
        "2024-06-03",
        "2024-12-31",
    ]

    folds = build_development_folds(
        confirmation,
        trading_dates=trading_dates,
    )

    assert [fold.train_end for fold in folds] == [
        "2021-12-31",
        "2022-12-30",
        "2023-12-29",
    ]
    assert [fold.test_start for fold in folds] == [
        "2022-01-04",
        "2023-01-03",
        "2024-01-02",
    ]
    assert all(fold.train_end < fold.test_start for fold in folds)
