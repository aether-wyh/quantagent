from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_open_research_prompts_do_not_seed_named_answers() -> None:
    files = [
        ROOT / "src/quanta_agents/prompts/agents/input_interpreter_v2.yaml",
        ROOT / "src/quanta_agents/prompts/agents/baseline_builder_v2.yaml",
        ROOT / "src/quanta_agents/prompts/agents/research_planner_v2.yaml",
        ROOT / "src/quanta_agents/prompts/agents/result_judge_v2.yaml",
        ROOT / "src/quanta_agents/prompts/agents/strategy_agent.yaml",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)

    for seeded_answer in (
        "沪深300",
        "中证500",
        "中证1000",
        "游资",
        "机构吸筹",
        "1.5%",
        "2.5倍",
    ):
        assert seeded_answer not in text


def test_example_yaml_contains_only_version_and_original_idea() -> None:
    import yaml

    path = ROOT / "experiments/consolidation_volume_box_research_v2.yaml"
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert set(parsed) == {"workflow_version", "user_idea"}
    assert "30天盘整" in parsed["user_idea"]
