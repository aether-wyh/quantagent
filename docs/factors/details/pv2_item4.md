# A15 隔夜日内探索

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-f93616ae3b674a09"></a>

## pv2_id_minus_on20

- ID：`f93616ae3b674a09`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 4: 20-day intraday minus overnight
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0483 / 0.0268。

登记表达式或插件说明：

```text
rolling_sum(log(close / open) - log(open / prev_close), 20)
```


<a id="f-09ccc187efaab6e1"></a>

## pv2_id_minus_on5

- ID：`09ccc187efaab6e1`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 4: 5-day intraday minus overnight
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0353 / 0.0206。

登记表达式或插件说明：

```text
rolling_sum(log(close / open) - log(open / prev_close), 5)
```


<a id="f-d84ed46f00d15622"></a>

## pv2_id_minus_on60

- ID：`d84ed46f00d15622`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 4: 60-day intraday minus overnight
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0517 / 0.0360。

登记表达式或插件说明：

```text
rolling_sum(log(close / open) - log(open / prev_close), 60)
```


<a id="f-e4105b832c56ba13"></a>

## pv2_intraday20

- ID：`e4105b832c56ba13`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 4: 20-day cumulative intraday return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0565 / 0.0328。

登记表达式或插件说明：

```text
rolling_sum(log(close / open), 20)
```


<a id="f-c6b4ca62fa0cc3b6"></a>

## pv2_intraday5

- ID：`c6b4ca62fa0cc3b6`；归属：pool_current。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 4: 5-day cumulative intraday return
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0372 / 0.0257。

登记表达式或插件说明：

```text
rolling_sum(log(close / open), 5)
```


<a id="f-f53a1cf2f9dd85c0"></a>

## pv2_intraday60

- ID：`f53a1cf2f9dd85c0`；归属：pool_current。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：A15 item 4: 60-day cumulative intraday return
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0599 / 0.0407。

登记表达式或插件说明：

```text
rolling_sum(log(close / open), 60)
```


<a id="f-0b40720ac555a7cd"></a>

## pv2_on_share20

- ID：`0b40720ac555a7cd`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 4: 20-day overnight share of absolute moves
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0151 / 0.0009。

登记表达式或插件说明：

```text
rolling_sum(log(open / prev_close), 20) / rolling_sum(abs(log(open / prev_close)) + abs(log(close / open)), 20)
```


<a id="f-d5d44e0869a72779"></a>

## pv2_on_share5

- ID：`d5d44e0869a72779`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 4: 5-day overnight share of absolute moves
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0126 / -0.0030。

登记表达式或插件说明：

```text
rolling_sum(log(open / prev_close), 5) / rolling_sum(abs(log(open / prev_close)) + abs(log(close / open)), 5)
```


<a id="f-ae3bcd189d3c8292"></a>

## pv2_on_share60

- ID：`ae3bcd189d3c8292`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 4: 60-day overnight share of absolute moves
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0196 / 0.0057。

登记表达式或插件说明：

```text
rolling_sum(log(open / prev_close), 60) / rolling_sum(abs(log(open / prev_close)) + abs(log(close / open)), 60)
```


<a id="f-57b3ad047eb152d3"></a>

## pv2_overnight20

- ID：`57b3ad047eb152d3`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 4: 20-day cumulative overnight return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0159 / 0.0060。

登记表达式或插件说明：

```text
rolling_sum(log(open / prev_close), 20)
```


<a id="f-95f43a3e25664b1c"></a>

## pv2_overnight5

- ID：`95f43a3e25664b1c`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 4: 5-day cumulative overnight return
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0157 / 0.0030。

登记表达式或插件说明：

```text
rolling_sum(log(open / prev_close), 5)
```


<a id="f-90d60bff5ed04594"></a>

## pv2_overnight60

- ID：`90d60bff5ed04594`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：A15 item 4: 60-day cumulative overnight return
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0228 / 0.0081。

登记表达式或插件说明：

```text
rolling_sum(log(open / prev_close), 60)
```
