# A15 条件反转探索

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-3d13f73c2d0c2479"></a>

## pv2_rev20_q5turn

- ID：`3d13f73c2d0c2479`；归属：历史候选，未列入上述集合。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 3: 20-day reversal ranked inside turnover quintiles
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0424 / 0.0231。

登记表达式或插件说明：

```text
cs_rank_within(-(close / lag(close, 20) - 1), rolling_mean(turnover, 20), 5)
```


<a id="f-0a2cb1f3cf3614e1"></a>

## pv2_rev20_tn

- ID：`0a2cb1f3cf3614e1`；归属：历史候选，未列入上述集合。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 3: 20-day reversal, turnover-neutralised (linear)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0410 / 0.0191。

登记表达式或插件说明：

```text
cs_neutralize(-(close / lag(close, 20) - 1), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-ef5b8ee5b30edbfa"></a>

## pv2_rev20_xlim_q5turn

- ID：`ef5b8ee5b30edbfa`；归属：历史候选，未列入上述集合。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 3: 20-day ex-limit reversal ranked inside turnover quintiles
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0152 / -0.0057。

登记表达式或插件说明：

```text
cs_rank_within(-rolling_sum(where(ret > 0.095, 0, log(1 + ret)), 20), rolling_mean(turnover, 20), 5)
```


<a id="f-4872cd62150271c9"></a>

## pv2_rev20q5_mom120_blend

- ID：`4872cd62150271c9`；归属：历史候选，未列入上述集合。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 3: equal-weight blend: turnover-quintile reversal + 6-1 momentum
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0199 / -0.0053。

登记表达式或插件说明：

```text
0.5 * cs_rank_within(-(close / lag(close, 20) - 1), rolling_mean(turnover, 20), 5) + 0.5 * cs_rank(lag(close, 20) / lag(close, 120) - 1)
```


<a id="f-c9ee781287305cb7"></a>

## pv2_rev20q5_mom250_blend

- ID：`c9ee781287305cb7`；归属：历史候选，未列入上述集合。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 3: equal-weight blend: turnover-quintile reversal + 12-1 momentum
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0243 / 0.0059。

登记表达式或插件说明：

```text
0.5 * cs_rank_within(-(close / lag(close, 20) - 1), rolling_mean(turnover, 20), 5) + 0.5 * cs_rank(lag(close, 20) / lag(close, 250) - 1)
```
