from __future__ import annotations

import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from quanta_agents.prompt_loader import load_agent_prompt


def test_translation_and_optimizer_use_separate_system_prompts() -> None:
    translation = load_agent_prompt(
        "strategy_translation_agent",
        "system_prompt",
        scenario="沪深300日线",
        required_data_format="数据格式",
    )
    optimizer = load_agent_prompt(
        "research_optimizer_agent",
        "system_prompt",
        scenario="沪深300日线",
        required_data_format="数据格式",
    )

    assert "唯一任务是把用户提供的 YAML" in translation
    assert "不分析回测结果" in translation
    assert "至少提出两个有实质区别的可能原因" in optimizer
    assert "不能读取或推测最终测试时期" in optimizer
    assert "diagnose_only" in optimizer
    assert "compare_core_variants" in optimizer
    assert "test_candidate" in optimizer
    assert "branch_hypothesis" in optimizer
    assert "request_data" in optimizer
    assert translation != optimizer


def test_optimizer_separates_research_goals_and_requires_a_real_candidate_test() -> None:
    optimizer = load_agent_prompt(
        "research_optimizer_agent",
        "system_prompt",
        scenario="A股分钟事件研究",
        required_data_format="数据格式",
    )

    assert "价格现象" in optimizer
    assert "费用可行性" in optimizer
    assert "实际可交易性" in optimizer
    assert "不得用费用未覆盖或暂时不能真实交易，直接否定价格现象" in optimizer
    assert "费用是否覆盖是验收结果之一，不是运行候选的前提" in optimizer
    assert "单字段筛选只用于提名候选" in optimizer
    assert "固定诊断不算正式策略试验" in optimizer
    assert "一次只检验一个主要研究判断" in optimizer
    assert "每轮必须给出至少两个不同方向的候选" in optimizer
    assert "每轮必须列出尚未正式测试的方案" in optimizer
    assert "event_horizon_minutes=Y" in optimizer
    assert "只写“比较 5/10/20 分钟”不表示批准修改" in optimizer
    assert "low_ma5_distance_screening" in optimizer
    assert "完整日最低价与五日均线距离表现强" in optimizer
    assert "必须判断为“事后分组现象”" in optimizer
    assert "缺少逐事件明细、按日期等权附表或更细的费用分解不算关键数据缺失" in optimizer
    assert "必须先完成至少一个正式候选" in optimizer
    assert "time_series` 不得改写成 `panel" in optimizer
    assert "完整开发报告 `passed=false` 的候选不能成为下一轮策略起点" in optimizer


def test_optimizer_stop_requires_exhausted_official_tests_or_hard_impossibility() -> None:
    optimizer = load_agent_prompt(
        "research_optimizer_agent",
        "system_prompt",
        scenario="A股分钟事件研究",
        required_data_format="数据格式",
    )

    assert "【严格停止条件】" in optimizer
    assert "只有一个基准候选时" in optimizer
    assert "否则不得停止" in optimizer
    assert "不得仅因费用未覆盖、T+1 限制、诊断次数达到上限" in optimizer
    assert "停止前必须列出所有尚未正式测试的方案及不测试理由" in optimizer
    assert '"candidate_directions"' in optimizer
    assert '"untested_plans"' in optimizer
    assert '"stop_eligibility"' in optimizer
    assert "modify_one_rule | simpler_comparison" not in optimizer


def test_code_writer_prompt_does_not_choose_research_direction() -> None:
    system_prompt = load_agent_prompt("strategy_agent", "system_prompt")
    user_prompt = load_agent_prompt(
        "strategy_agent",
        "user_prompt_template",
        hypothesis="完整策略说明",
        strategy_modification="只改一项",
        required_data_descriptions="数据说明",
        previous_strategy_source="上一版",
        code_change_summary="修改说明",
        previous_strategy_code="",
        previous_code_diff="",
        validation_summary_json="{}",
    )

    assert "不解释回测失败原因" in system_prompt
    assert "不选择下一项研究方向" in system_prompt
    assert "禁止调用或引用 `globals`" in system_prompt
    assert "dataset_defined" in system_prompt
    assert "symbols` 可以为空" in system_prompt
    assert "判断统计验证建议是否合理" not in user_prompt
    assert "只修复其中明确指出" in user_prompt


def test_code_writer_records_exact_event_selection_conditions_in_params() -> None:
    system_prompt = load_agent_prompt("strategy_agent", "system_prompt")

    assert '"generic_selection_conditions"' in system_prompt
    assert '{"feature": "past_up_count", "operator": ">=", "value": 4}' in system_prompt
    assert "必须且只能包含 `feature`、`operator`、`value`" in system_prompt
    assert "必须与 `output_weights` 实际执行的全部通用字段筛选完全一致" in system_prompt
    assert '"generic_selection_conditions": []' in system_prompt
    assert "只供固定分析程序按相同条件复算" in system_prompt
    assert "仍然只能实现已批准的【完整策略说明】或【本轮单项修改】" in system_prompt
    assert "持有/评价时间从 X 分钟改为 Y 分钟" in system_prompt
    assert "明确否决某个期限，都不算批准" in system_prompt
    assert "任何以 `analysis_only_` 开头的完整日字段" in system_prompt
    assert "禁止读取、计算替代值或用于筛选" in system_prompt


def test_code_writer_preserves_planned_holding_when_daily_bar_is_missing() -> None:
    system_prompt = load_agent_prompt("strategy_agent", "system_prompt")

    assert "当日缺少K线时，只表示当日不能成交" in system_prompt
    assert "已经开始的计划持仓目标必须继续保留到原退出日" in system_prompt
    assert "因当日缺K把它改成0" in system_prompt
    assert "不得把原退出日向后顺延" in system_prompt
    assert "禁止读取、移动或推断下一交易日是否有K线" in system_prompt


def test_code_writer_requires_exact_market_dates_for_consecutive_days() -> None:
    system_prompt = load_agent_prompt("strategy_agent", "system_prompt")

    assert "N指全市场日历中连续的N个实际交易日" in system_prompt
    assert "consecutive_market_day_sample" in system_prompt
    assert "缺口前后的两条股票记录当成连续" in system_prompt


def test_old_model_review_prompts_are_marked_inactive() -> None:
    prompt_dir = SRC_DIR / "quanta_agents" / "prompts" / "agents"
    for name in ("hypothesis_agent.yaml", "validate_agent.yaml", "analysis_agent.yaml"):
        data = yaml.safe_load((prompt_dir / name).read_text(encoding="utf-8"))
        assert data["active_in_main_workflow"] is False
        assert data["inactive_reason"]
