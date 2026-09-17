from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from quanta_agents.prompt_loader import load_agent_prompt


def test_translation_prompt_defines_research_structure_and_result_field_usage() -> None:
    system_prompt = load_agent_prompt(
        "strategy_translation_agent",
        "system_prompt",
        scenario="A股分钟事件研究",
        required_data_format="数据格式要求",
    )
    user_prompt = load_agent_prompt(
        "strategy_translation_agent",
        "user_prompt",
        user_idea="研究规律放量后的价格表现",
    )

    for field_name in (
        "core_hypothesis",
        "fixed_parts",
        "changeable_parts",
        "candidate_dimensions",
        "hard_constraints",
    ):
        assert f'"{field_name}"' in system_prompt

    assert "结果字段可以用于训练期和开发期的汇总评价与下一轮规则选择" in system_prompt
    assert "最终回测期只能在规则冻结后使用一次" in system_prompt
    assert "不得作为单个事件的实时输入" in system_prompt
    assert "结果字段不得进入单个事件的筛选、排序、目标比例、特征、阈值计算" in system_prompt
    assert "开发期结果字段计算该候选规则" in system_prompt
    assert "且不得再用于选择规则" in system_prompt
    assert "必须明确截断到 `trigger_ts`" in system_prompt
    assert "完整交易日最低价和最终收盘价只能写成事后说明变量" in system_prompt
    assert "不得放入 `decision_time_fields`" in system_prompt
    assert "不得替研究 Agent 选择最终规则" in user_prompt
