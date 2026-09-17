# 研究循环 V2：从一句话开始

V2 的输入不再是一份塞满时期、股票范围和候选答案的复杂 YAML。YAML 可以只写一句想法，也可以指向一份 Markdown、TXT、PDF 或 Word 研报。

运行顺序：

1. 原文整理：区分用户明确说过的条件、含糊词和运行所需但没说明的内容。临时决定都标明来源。
2. 回测前解释：在看收益以前，提出至少三个竞争解释和一个“没有稳定规律”的解释，并自己拟搜索词查公开资料。
3. 忠实基准：只把原话和临时决定写成第一版，不在这里增加改善条件。
4. 研究循环：依次正式检查数值与定义、解释推导出的新信号、适用对象或环境、原条件是否必要、交易与持有时点。
5. 数值问题：先比较三到五个相邻值。只有一段较宽范围方向一致，才把其中一个值送入正式回测。
6. 每次正式回测只回答一个研究问题。候选失败后，程序恢复最近采用版本；相对改善可以成为下一轮起点，但不能冒充稳定策略。
7. 通过一次不会立刻停止。至少把规定的几类问题都实际检查过，再进入确认期。
8. 研究期用于选择，确认期只检查选中的版本。确认期通过后，最终期最多运行一次，结果不会返回前面继续改规则。
9. 旁观审查只认实际运行记录，不把“想到了”当成“测过了”。

本次示例输入在 `experiments/consolidation_volume_box_research_v2.yaml`。运行：

```powershell
$env:QUANTA_LLM_PROVIDER='codex_exec'
$env:CODEX_EXEC_MODEL='gpt-5.6-sol'
$env:CODEX_EXEC_REASONING_EFFORT='ultra'
.\.venv\Scripts\python.exe scripts\run_research_loop_v2.py experiments\consolidation_volume_box_research_v2.yaml
```

结果保存在该次实验的 `experiment_traces/<实验编号>/.../research_loop_v2_result.json`。网页资料的查询词、网址、发布日期和摘要另存为 `web_sources.jsonl`。
