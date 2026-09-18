# A15 成交量结构探索

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-5cdb11d8db52ec92"></a>

## pv2_amp20

- ID：`5cdb11d8db52ec92`；归属：历史候选，未列入上述集合。
- 机制：低波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: 20-day mean amplitude
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0754 / 0.0627。

登记表达式或插件说明：

```text
rolling_mean((high - low) / prev_close, 20)
```


<a id="f-a8463f056dd4ce66"></a>

## pv2_limdn_touch20

- ID：`a8463f056dd4ce66`；归属：历史候选，未列入上述集合。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: days in 20 touching a 10% limit-down
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0277 / 0.0073。

登记表达式或插件说明：

```text
rolling_sum(low / prev_close - 1 < -0.095, 20)
```


<a id="f-df1ca5cf4e3605d3"></a>

## pv2_limup_close20

- ID：`df1ca5cf4e3605d3`；归属：pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: days in 20 closing at a 10% limit-up
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0679 / 0.0613。

登记表达式或插件说明：

```text
rolling_sum(ret > 0.095, 20)
```


<a id="f-f79217a3f8224633"></a>

## pv2_limup_touch20

- ID：`f79217a3f8224633`；归属：pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: days in 20 touching a 10% limit-up
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0733 / 0.0654。

登记表达式或插件说明：

```text
rolling_sum(high / prev_close - 1 > 0.095, 20)
```


<a id="f-f1d463e83cd0220e"></a>

## pv2_limup_touch60

- ID：`f1d463e83cd0220e`；归属：pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: days in 60 touching a 10% limit-up
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0675 / 0.0623。

登记表达式或插件说明：

```text
rolling_sum(high / prev_close - 1 > 0.095, 60)
```


<a id="f-d277a6ac8e2edaac"></a>

## pv2_lowshadow20

- ID：`d277a6ac8e2edaac`；归属：pool_current。
- 机制：收盘位置（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: 20-day mean lower shadow
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0601 / 0.0476。

登记表达式或插件说明：

```text
rolling_mean((min(open, close) - low) / prev_close, 20)
```


<a id="f-a420ca576b5560b6"></a>

## pv2_pv_div_prod20

- ID：`a420ca576b5560b6`；归属：pool_current。
- 机制：量价相关（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: price change x turnover change (20d)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0338 / 0.0199。

登记表达式或插件说明：

```text
(close / lag(close, 20) - 1) * (rolling_mean(turnover, 20) / lag(rolling_mean(turnover, 20), 20) - 1)
```


<a id="f-36d6e9149c0e561c"></a>

## pv2_pv_div_rank20

- ID：`36d6e9149c0e561c`；归属：历史候选，未列入上述集合。
- 机制：量价相关（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: rank(price change) - rank(turnover change), 20d
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0152 / 0.0014。

登记表达式或插件说明：

```text
cs_rank(close / lag(close, 20) - 1) - cs_rank(rolling_mean(turnover, 20) / lag(rolling_mean(turnover, 20), 20) - 1)
```


<a id="f-f4862a2be57e92a2"></a>

## pv2_shadow_diff20

- ID：`f4862a2be57e92a2`；归属：pool_current。
- 机制：收盘位置（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: 20-day mean upper minus lower shadow
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0368 / 0.0204。

登记表达式或插件说明：

```text
rolling_mean(((high - max(open, close)) - (min(open, close) - low)) / prev_close, 20)
```

规范式 / 计算标识：

```text
rolling_mean((high - max(open, close) - (min(open, close) - low)) / prev_close, 20)
```


<a id="f-2c6f5013a4591df2"></a>

## pv2_turn_10_120

- ID：`2c6f5013a4591df2`；归属：pool_current。
- 机制：异常换手（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: 10/120-day turnover ratio
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0540 / 0.0429。

登记表达式或插件说明：

```text
rolling_mean(turnover, 10) / rolling_mean(turnover, 120)
```


<a id="f-c980911693a8474b"></a>

## pv2_upshadow20

- ID：`c980911693a8474b`；归属：pool_current。
- 机制：收盘位置（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: 20-day mean upper shadow
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0687 / 0.0517。

登记表达式或插件说明：

```text
rolling_mean((high - max(open, close)) / prev_close, 20)
```


<a id="f-a5293c88f8273d76"></a>

## pv2_vol_spike20

- ID：`a5293c88f8273d76`；归属：pool_current。
- 机制：异常换手（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: days in 20 with turnover &gt; 2x trailing 60-day mean
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0495 / 0.0424。

登记表达式或插件说明：

```text
rolling_sum(turnover > 2 * lag(rolling_mean(turnover, 60), 1), 20)
```


<a id="f-ca7b460e4693f499"></a>

## pv2_vol_spike60

- ID：`ca7b460e4693f499`；归属：pool_current。
- 机制：异常换手（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 5: days in 60 with turnover &gt; 2x trailing 60-day mean
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0450 / 0.0366。

登记表达式或插件说明：

```text
rolling_sum(turnover > 2 * lag(rolling_mean(turnover, 60), 1), 60)
```
