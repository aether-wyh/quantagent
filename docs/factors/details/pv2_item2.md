# A15 动量探索

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-9cbd76e9d1326466"></a>

## pv2_mom120

- ID：`9cbd76e9d1326466`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 120-day momentum
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0426 / 0.0098。

登记表达式或插件说明：

```text
close / lag(close, 120) - 1
```


<a id="f-2667c64617abeb0c"></a>

## pv2_mom120_q5turn

- ID：`2667c64617abeb0c`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 120-day momentum ranked inside turnover quintiles
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0244 / -0.0104。

登记表达式或插件说明：

```text
cs_rank_within(close / lag(close, 120) - 1, rolling_mean(turnover, 20), 5)
```


<a id="f-99218cc8a00e08da"></a>

## pv2_mom120_tn

- ID：`99218cc8a00e08da`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 120-day momentum, turnover-neutralised
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0318 / -0.0022。

登记表达式或插件说明：

```text
cs_neutralize(close / lag(close, 120) - 1, cs_rank(rolling_mean(turnover, 120)))
```


<a id="f-5e67d75c71201db2"></a>

## pv2_mom120_xlim

- ID：`5e67d75c71201db2`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 2: 120-day momentum with limit-up-sized days zeroed
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0190 / 0.0002。

登记表达式或插件说明：

```text
rolling_sum(where(ret > 0.095, 0, log(1 + ret)), 120)
```


<a id="f-ecac1ed6c75a5263"></a>

## pv2_mom20_tn

- ID：`ecac1ed6c75a5263`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 20-day momentum, turnover-neutralised
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0410 / 0.0191。

登记表达式或插件说明：

```text
cs_neutralize(close / lag(close, 20) - 1, cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-9296005cb7f62cdd"></a>

## pv2_mom20_xlim

- ID：`9296005cb7f62cdd`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 20-day momentum with limit-up-sized days zeroed
- 原判定：no_signal+style:mom20；历史均值 / 最差年 RankIC：0.0062 / -0.0132。

登记表达式或插件说明：

```text
rolling_sum(where(ret > 0.095, 0, log(1 + ret)), 20)
```


<a id="f-8176bba1b9f4b77f"></a>

## pv2_mom250_20

- ID：`8176bba1b9f4b77f`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 2: 12-1 month momentum
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0066 / -0.0252。

登记表达式或插件说明：

```text
lag(close, 20) / lag(close, 250) - 1
```


<a id="f-f9fa1f3a7939a7fc"></a>

## pv2_mom60

- ID：`f9fa1f3a7939a7fc`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 60-day momentum
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0521 / 0.0294。

登记表达式或插件说明：

```text
close / lag(close, 60) - 1
```


<a id="f-c664561e1cbd4aad"></a>

## pv2_mom60_tn

- ID：`c664561e1cbd4aad`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 60-day momentum, turnover-neutralised
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0392 / 0.0146。

登记表达式或插件说明：

```text
cs_neutralize(close / lag(close, 60) - 1, cs_rank(rolling_mean(turnover, 60)))
```


<a id="f-a00eff7ac00d38fa"></a>

## pv2_mom60_xlim

- ID：`a00eff7ac00d38fa`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 2: 60-day momentum with limit-up-sized days zeroed
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0072 / -0.0150。

登记表达式或插件说明：

```text
rolling_sum(where(ret > 0.095, 0, log(1 + ret)), 60)
```


<a id="f-b9aa56566ec63c32"></a>

## pv2_mom60_xlim_tn

- ID：`b9aa56566ec63c32`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 2: 60-day ex-limit momentum, turnover-neutralised
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0074 / -0.0201。

登记表达式或插件说明：

```text
cs_neutralize(rolling_sum(where(ret > 0.095, 0, log(1 + ret)), 60), cs_rank(rolling_mean(turnover, 60)))
```
