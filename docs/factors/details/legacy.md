# 旧框架因子

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-40bd87bc5d21be61"></a>

## legacy.F1

- ID：`40bd87bc5d21be61`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0130 / -0.0408。

登记表达式或插件说明：

```text
pct_change(lag(close, 20), 100)
```


<a id="f-af73470d325fcd95"></a>

## legacy.F2

- ID：`af73470d325fcd95`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0306 / 0.0176。

登记表达式或插件说明：

```text
pct_change(close, 5)
```


<a id="f-044240984b55ae34"></a>

## legacy.F3

- ID：`044240984b55ae34`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0483 / 0.0267。

登记表达式或插件说明：

```text
rolling_mean(log(close / open) - log(open / lag(close, 1)), 20)
```


<a id="f-b854c6a709e4cea7"></a>

## legacy.F4

- ID：`b854c6a709e4cea7`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0098 / -0.0029。

登记表达式或插件说明：

```text
rolling_mean(where(high > low, (2 * close - high - low) / (high - low), 0), 5)
```


<a id="f-caf6409f75d391ad"></a>

## legacy.F5

- ID：`caf6409f75d391ad`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0502 / 0.0255。

登记表达式或插件说明：

```text
rolling_sum(where(pct_change(close, 1) < 0, pct_change(close, 1) * pct_change(close, 1), 0), 20) / rolling_sum(pct_change(close, 1) * pct_change(close, 1), 20)
```


<a id="f-29797f42bb682365"></a>

## legacy.F6

- ID：`29797f42bb682365`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0494 / 0.0292。

登记表达式或插件说明：

```text
rolling_mean(volume, 5) / lag(rolling_mean(volume, 60), 5)
```


<a id="f-937d09538df875b6"></a>

## legacy.F7

- ID：`937d09538df875b6`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：risk
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0735 / 0.0654。

登记表达式或插件说明：

```text
rolling_std(pct_change(close, 1), 20)
```


<a id="f-9cae09fc6e29fbbc"></a>

## legacy.F8

- ID：`9cae09fc6e29fbbc`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0313 / 0.0007。

登记表达式或插件说明：

```text
rolling_corr(pct_change(close, 1), log(volume), 20)
```


<a id="f-118cf5fd6441b5dd"></a>

## legacy.HF0017

- ID：`118cf5fd6441b5dd`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：unstable_years；历史均值 / 最差年 RankIC：0.0355 / -0.0009。

登记表达式或插件说明：

```text
3 * ema(close, 20) - 3 * ema(ema(close, 20), 20) + ema(ema(ema(close, 20), 20), 20)
```


<a id="f-457600a38b4cd8e5"></a>

## legacy.HF0091

- ID：`457600a38b4cd8e5`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0368 / 0.0160。

登记表达式或插件说明：

```text
rolling_mean(abs(pct_change(close, 1)) / amount, 20)
```


<a id="f-576917ff4c934fe9"></a>

## legacy.HF0219

- ID：`576917ff4c934fe9`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0605 / 0.0255。

登记表达式或插件说明：

```text
ema(where(high - low > abs(high - lag(close, 1)), where(high - low > abs(low - lag(close, 1)), high - low, abs(low - lag(close, 1))), where(abs(high - lag(close, 1)) > abs(low - lag(close, 1)), abs(high - lag(close, 1)), abs(low - lag(close, 1)))), 14)
```


<a id="f-edc7d8448f2a3ada"></a>

## legacy.calendar.standard.acd

- ID：`edc7d8448f2a3ada`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0471 / 0.0307。

登记表达式或插件说明：

```text
rolling_sum(where(close > lag(close, 1), close - where(low <= lag(close, 1), low, lag(close, 1)), where(close < lag(close, 1), close - where(high >= lag(close, 1), high, lag(close, 1)), 0)), 20)
```


<a id="f-de49f7f3c6aee442"></a>

## legacy.calendar.standard.amihud

- ID：`de49f7f3c6aee442`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0368 / 0.0160。

登记表达式或插件说明：

```text
rolling_mean(where(abs(amount) > 1e-12, abs(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1) / amount, 0 / 0), 20)
```


<a id="f-9e4f8905c2e37803"></a>

## legacy.calendar.standard.ar

- ID：`9e4f8905c2e37803`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0541 / 0.0275。

登记表达式或插件说明：

```text
100 * where(abs(rolling_sum(open - low, 26)) > 1e-12, rolling_sum(high - open, 26) / rolling_sum(open - low, 26), 0 / 0)
```


<a id="f-84448fd002975429"></a>

## legacy.calendar.standard.bbi

- ID：`84448fd002975429`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0338 / -0.0030。

登记表达式或插件说明：

```text
(rolling_mean(close, 3) + rolling_mean(close, 6) + rolling_mean(close, 12) + rolling_mean(close, 20)) / 4
```


<a id="f-0ea786d6cb08dda7"></a>

## legacy.calendar.standard.bias

- ID：`0ea786d6cb08dda7`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0474 / 0.0314。

登记表达式或插件说明：

```text
100 * where(abs(rolling_mean(close, 20)) > 1e-12, (close - rolling_mean(close, 20)) / rolling_mean(close, 20), 0 / 0)
```


<a id="f-a3cd1c83860f3b11"></a>

## legacy.calendar.standard.br

- ID：`a3cd1c83860f3b11`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0452 / 0.0256。

登记表达式或插件说明：

```text
100 * where(abs(rolling_sum(where(lag(close, 1) - low >= 0, lag(close, 1) - low, 0), 26)) > 1e-12, rolling_sum(where(high - lag(close, 1) >= 0, high - lag(close, 1), 0), 26) / rolling_sum(where(lag(close, 1) - low >= 0, lag(close, 1) - low, 0), 26), 0 / 0)
```


<a id="f-703aefcfc7d6c281"></a>

## legacy.calendar.standard.cmf

- ID：`703aefcfc7d6c281`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0182 / 0.0034。

登记表达式或插件说明：

```text
where(abs(rolling_sum(volume, 20)) > 1e-12, rolling_sum(where(abs(high - low) > 1e-12, (2 * close - high - low) / (high - low), 0 / 0) * volume, 20) / rolling_sum(volume, 20), 0 / 0)
```


<a id="f-a8863f655af9226f"></a>

## legacy.calendar.standard.cmo

- ID：`a8863f655af9226f`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0376 / 0.0187。

登记表达式或插件说明：

```text
100 * where(abs(rolling_sum(where(close - lag(close, 1) >= 0, close - lag(close, 1), 0), 14) + rolling_sum(where(-(close - lag(close, 1)) >= 0, -(close - lag(close, 1)), 0), 14)) > 1e-12, (rolling_sum(where(close - lag(close, 1) >= 0, close - lag(close, 1), 0), 14) - rolling_sum(where(-(close - lag(close, 1)) >= 0, -(close - lag(close, 1)), 0), 14)) / (rolling_sum(where(close - lag(close, 1) >= 0, close - lag(close, 1), 0), 14) + rolling_sum(where(-(close - lag(close, 1)) >= 0, -(close - lag(close, 1)), 0), 14)), 0 / 0)
```


<a id="f-9e54eb7600b87dbd"></a>

## legacy.calendar.standard.cr

- ID：`9e54eb7600b87dbd`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0490 / 0.0221。

登记表达式或插件说明：

```text
100 * where(abs(rolling_sum(where(lag((high + low + close) / 3, 1) - low >= 0, lag((high + low + close) / 3, 1) - low, 0), 26)) > 1e-12, rolling_sum(where(high - lag((high + low + close) / 3, 1) >= 0, high - lag((high + low + close) / 3, 1), 0), 26) / rolling_sum(where(lag((high + low + close) / 3, 1) - low >= 0, lag((high + low + close) / 3, 1) - low, 0), 26), 0 / 0)
```


<a id="f-59a6041b46656d3c"></a>

## legacy.calendar.standard.cv_illiquidity

- ID：`59a6041b46656d3c`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：risk
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0066 / -0.0289。

登记表达式或插件说明：

```text
where(abs(rolling_mean(where(abs(amount) > 1e-12, abs(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1) / amount, 0 / 0), 20)) > 1e-12, rolling_std(where(abs(amount) > 1e-12, abs(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1) / amount, 0 / 0), 20) * 0.9746794344808963 / rolling_mean(where(abs(amount) > 1e-12, abs(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1) / amount, 0 / 0), 20), 0 / 0)
```


<a id="f-5d1d7c79ea3ab9b1"></a>

## legacy.calendar.standard.dynamic_momentum_indicator

- ID：`5d1d7c79ea3ab9b1`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0256 / 0.0131。

登记表达式或插件说明：

```text
14 * where(abs(rolling_std(close, 20) * 0.9746794344808963) > 1e-12, rolling_mean(rolling_std(close, 20) * 0.9746794344808963, 20) / (rolling_std(close, 20) * 0.9746794344808963), 0 / 0)
```


<a id="f-f5add0cf76936a6f"></a>

## legacy.calendar.standard.emv

- ID：`f5add0cf76936a6f`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0297 / 0.0125。

登记表达式或插件说明：

```text
rolling_mean(where(abs(where(abs(high - low) > 1e-12, volume / (high - low), 0 / 0)) > 1e-12, (high + low - lag(high, 1) - lag(low, 1)) / 2 / where(abs(high - low) > 1e-12, volume / (high - low), 0 / 0), 0 / 0), 14)
```


<a id="f-fb16533594970b35"></a>

## legacy.calendar.standard.high_52_week

- ID：`fb16533594970b35`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0147 / -0.0151。

登记表达式或插件说明：

```text
where(abs(where(where(rolling_max(close, 120) >= lag(rolling_max(close, 120), 120), rolling_max(close, 120), lag(rolling_max(close, 120), 120)) >= lag(lag(rolling_max(close, 12), 120), 120), where(rolling_max(close, 120) >= lag(rolling_max(close, 120), 120), rolling_max(close, 120), lag(rolling_max(close, 120), 120)), lag(lag(rolling_max(close, 12), 120), 120))) > 1e-12, close / where(where(rolling_max(close, 120) >= lag(rolling_max(close, 120), 120), rolling_max(close, 120), lag(rolling_max(close, 120), 120)) >= lag(lag(rolling_max(close, 12), 120), 120), where(rolling_max(close, 120) >= lag(rolling_max(close, 120), 120), rolling_max(close, 120), lag(rolling_max(close, 120), 120)), lag(lag(rolling_max(close, 12), 120), 120)), 0 / 0)
```


<a id="f-bedda5bd8e8475d7"></a>

## legacy.calendar.standard.imi

- ID：`bedda5bd8e8475d7`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0451 / 0.0203。

登记表达式或插件说明：

```text
100 * where(abs(rolling_sum(where(close - open >= 0, close - open, 0), 14) + rolling_sum(where(-(close - open) >= 0, -(close - open), 0), 14)) > 1e-12, rolling_sum(where(close - open >= 0, close - open, 0), 14) / (rolling_sum(where(close - open >= 0, close - open, 0), 14) + rolling_sum(where(-(close - open) >= 0, -(close - open), 0), 14)), 0 / 0)
```


<a id="f-991c666693bce959"></a>

## legacy.calendar.standard.intraday_return

- ID：`991c666693bce959`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0185 / 0.0091。

登记表达式或插件说明：

```text
where(abs(open) > 1e-12, close / open, 0 / 0) - 1
```


<a id="f-6d6d0410240dc1dd"></a>

## legacy.calendar.standard.long_reversal

- ID：`6d6d0410240dc1dd`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`0`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
where(abs(lag(lag(lag(lag(lag(lag(lag(lag(lag(lag(lag(close, 120), 120), 120), 120), 120), 120), 120), 120), 120), 120), 60)) > 1e-12, lag(lag(lag(close, 120), 120), 12) / lag(lag(lag(lag(lag(lag(lag(lag(lag(lag(lag(close, 120), 120), 120), 120), 120), 120), 120), 120), 120), 120), 60), 0 / 0) - 1
```


<a id="f-2fd8620971a6520e"></a>

## legacy.calendar.standard.maximum_return

- ID：`2fd8620971a6520e`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：risk
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0719 / 0.0595。

登记表达式或插件说明：

```text
rolling_max(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1, 20)
```


<a id="f-bf28a03cb7ad7135"></a>

## legacy.calendar.standard.medium_momentum

- ID：`bf28a03cb7ad7135`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0437 / 0.0122。

登记表达式或插件说明：

```text
where(abs(lag(lag(close, 120), 6)) > 1e-12, close / lag(lag(close, 120), 6), 0 / 0) - 1
```


<a id="f-f59e9b9b196f5036"></a>

## legacy.calendar.standard.minimum_return

- ID：`f59e9b9b196f5036`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：risk
- 原判定：weak_signal+style:vol20；历史均值 / 最差年 RankIC：0.0412 / 0.0269。

登记表达式或插件说明：

```text
-rolling_min(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1, 20)
```


<a id="f-8af4b0aa50977946"></a>

## legacy.calendar.standard.momentum_acceleration

- ID：`8af4b0aa50977946`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0410 / 0.0099。

登记表达式或插件说明：

```text
where(abs(lag(lag(close, 120), 6)) > 1e-12, close / lag(lag(close, 120), 6), 0 / 0) - 1 - (where(abs(lag(lag(lag(close, 120), 120), 12)) > 1e-12, lag(lag(close, 120), 6) / lag(lag(lag(close, 120), 120), 12), 0 / 0) - 1)
```


<a id="f-ca01efd5bccc7d24"></a>

## legacy.calendar.standard.mtm

- ID：`ca01efd5bccc7d24`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0441 / 0.0295。

登记表达式或插件说明：

```text
close - lag(close, 12)
```


<a id="f-c396d5d0aa587ad8"></a>

## legacy.calendar.standard.overnight_gap

- ID：`c396d5d0aa587ad8`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：risk
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0659 / 0.0539。

登记表达式或插件说明：

```text
rolling_sum(abs(log(where(abs(lag(close, 1)) > 1e-12, open / lag(close, 1), 0 / 0))), 20)
```


<a id="f-0d86eeba3ae03ee4"></a>

## legacy.calendar.standard.overnight_return

- ID：`0d86eeba3ae03ee4`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0158 / 0.0065。

登记表达式或插件说明：

```text
where(abs(lag(close, 1)) > 1e-12, open / lag(close, 1), 0 / 0) - 1
```


<a id="f-0fb87d4eaef1e0ac"></a>

## legacy.calendar.standard.psy

- ID：`0fb87d4eaef1e0ac`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0223 / 0.0093。

登记表达式或插件说明：

```text
100 * rolling_mean(where(close > lag(close, 1), 1, 0), 12)
```


<a id="f-7011171d1671846a"></a>

## legacy.calendar.standard.qst

- ID：`7011171d1671846a`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0531 / 0.0287。

登记表达式或插件说明：

```text
rolling_mean(close - open, 20)
```


<a id="f-bcddad738055f070"></a>

## legacy.calendar.standard.roc

- ID：`bcddad738055f070`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0430 / 0.0255。

登记表达式或插件说明：

```text
rolling_mean(where(abs(lag(close, 12)) > 1e-12, close / lag(close, 12), 0 / 0) - 1, 6)
```


<a id="f-d54b210bc6f8d955"></a>

## legacy.calendar.standard.short_reversal

- ID：`d54b210bc6f8d955`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0520 / 0.0313。

登记表达式或插件说明：

```text
where(abs(lag(close, 20)) > 1e-12, close / lag(close, 20), 0 / 0) - 1
```


<a id="f-db0c11ef484229a5"></a>

## legacy.calendar.standard.tma

- ID：`db0c11ef484229a5`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0312 / -0.0067。

登记表达式或插件说明：

```text
rolling_mean(rolling_mean(close, 10), 11)
```


<a id="f-5065601e1be8e38c"></a>

## legacy.calendar.standard.total_volatility

- ID：`5065601e1be8e38c`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：risk
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0735 / 0.0654。

登记表达式或插件说明：

```text
rolling_std(where(abs(lag(close, 1)) > 1e-12, close / lag(close, 1), 0 / 0) - 1, 20) * 0.9746794344808963
```


<a id="f-a17945f078ecf976"></a>

## legacy.calendar.standard.trend_score

- ID：`a17945f078ecf976`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0132 / -0.0045。

登记表达式或插件说明：

```text
rolling_sum(where(close >= lag(close, 1), 1, -1), 20)
```


<a id="f-8a869a6bb7f083ce"></a>

## legacy.calendar.standard.true_range

- ID：`8a869a6bb7f083ce`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0663 / 0.0319。

登记表达式或插件说明：

```text
where(high - low >= where(abs(high - lag(close, 1)) >= abs(low - lag(close, 1)), abs(high - lag(close, 1)), abs(low - lag(close, 1))), high - low, where(abs(high - lag(close, 1)) >= abs(low - lag(close, 1)), abs(high - lag(close, 1)), abs(low - lag(close, 1))))
```


<a id="f-fd01e5c4ecc2d612"></a>

## legacy.calendar.standard.vama

- ID：`fd01e5c4ecc2d612`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0331 / -0.0042。

登记表达式或插件说明：

```text
where(abs(rolling_sum(volume, 20)) > 1e-12, rolling_sum(close * volume, 20) / rolling_sum(volume, 20), 0 / 0)
```


<a id="f-2db5764b61b3d723"></a>

## legacy.calendar.standard.vhf

- ID：`2db5764b61b3d723`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0011 / -0.0177。

登记表达式或插件说明：

```text
where(abs(rolling_sum(abs(close - lag(close, 1)), 28)) > 1e-12, (rolling_max(high, 28) - rolling_min(low, 28)) / rolling_sum(abs(close - lag(close, 1)), 28), 0 / 0)
```


<a id="f-7e8a6065be03aa81"></a>

## legacy.calendar.standard.volume_oscillator

- ID：`7e8a6065be03aa81`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0211 / 0.0121。

登记表达式或插件说明：

```text
100 * where(abs(rolling_mean(volume, 10)) > 1e-12, (rolling_mean(volume, 5) - rolling_mean(volume, 10)) / rolling_mean(volume, 10), 0 / 0)
```


<a id="f-b7ff638edefc63e8"></a>

## legacy.calendar.standard.vroc

- ID：`b7ff638edefc63e8`；归属：历史候选，未列入上述集合。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：return,condition
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0305 / 0.0067。

登记表达式或插件说明：

```text
100 * where(abs(lag(volume, 12)) > 1e-12, (volume - lag(volume, 12)) / lag(volume, 12), 0 / 0)
```
