# 经典量价

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-fee03e18ad40838f"></a>

## abn_turn_5_60

- ID：`fee03e18ad40838f`；归属：active_396, research_597, pool_current。
- 机制：异常换手（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：abnormal turnover
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0475 / 0.0284。

登记表达式或插件说明：

```text
-(rolling_mean(turnover, 5) / rolling_mean(turnover, 60))
```


<a id="f-59dbacd205ab079f"></a>

## amihud20

- ID：`59dbacd205ab079f`；归属：active_396, research_597, pool_current。
- 机制：非流动性(Amihud)（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Amihud illiquidity
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0368 / 0.0160。

登记表达式或插件说明：

```text
rolling_mean(abs(ret) / amount, 20)
```


<a id="f-6026ba447227983b"></a>

## clv20

- ID：`6026ba447227983b`；归属：历史候选，未列入上述集合。
- 机制：收盘位置（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：close location value
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0109 / -0.0024。

登记表达式或插件说明：

```text
rolling_mean(where(high > low, (2 * close - high - low) / (high - low), 0), 20)
```


<a id="f-531b6716d5135211"></a>

## high52_prox

- ID：`531b6716d5135211`；归属：历史候选，未列入上述集合。
- 机制：52周高点（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：proximity to 52-week high
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0126 / -0.0178。

登记表达式或插件说明：

```text
close / rolling_max(high, 250)
```


<a id="f-fed5477153a935a8"></a>

## idio_vol20_low

- ID：`fed5477153a935a8`；归属：active_396, research_597, pool_current。
- 机制：特质波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：idiosyncratic vol vs market
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0854 / 0.0701。

登记表达式或插件说明：

```text
-rolling_std(rolling_residual(ret, mkt_ret, 60), 20)
```


<a id="f-34eda56cb006729b"></a>

## intra_over20

- ID：`34eda56cb006729b`；归属：active_396, research_597, pool_current。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：intraday minus overnight (reverse)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0483 / 0.0268。

登记表达式或插件说明：

```text
-rolling_mean(log(close / open) - log(open / prev_close), 20)
```


<a id="f-1b0aae8536ac6327"></a>

## maxret20_low

- ID：`1b0aae8536ac6327`；归属：active_396, research_597, pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：max daily return (low is good)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0719 / 0.0595。

登记表达式或插件说明：

```text
-rolling_max(ret, 20)
```


<a id="f-88c9fdb62c7cad2d"></a>

## mom_120_20

- ID：`88c9fdb62c7cad2d`；归属：历史候选，未列入上述集合。
- 机制：中期动量（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：6m momentum skipping 1m
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0130 / -0.0408。

登记表达式或插件说明：

```text
lag(close, 20) / lag(close, 120) - 1
```


<a id="f-ffb6e892319105f9"></a>

## overnight20

- ID：`ffb6e892319105f9`；归属：历史候选，未列入上述集合。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：overnight return persistence
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0145 / 0.0051。

登记表达式或插件说明：

```text
rolling_mean(open / prev_close - 1, 20)
```


<a id="f-45ee7f8a0faa1f42"></a>

## pv_corr20

- ID：`45ee7f8a0faa1f42`；归属：active_396, research_597, pool_current。
- 机制：量价相关（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return-volume correlation
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0313 / 0.0007。

登记表达式或插件说明：

```text
-rolling_corr(ret, log(volume), 20)
```


<a id="f-974250cf2f6bbb65"></a>

## range20_low

- ID：`974250cf2f6bbb65`；归属：active_396, research_597, pool_current。
- 机制：低波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：average log range
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0749 / 0.0625。

登记表达式或插件说明：

```text
-rolling_mean(log(high / low), 20)
```


<a id="f-0a59417e689c8096"></a>

## rev20

- ID：`0a59417e689c8096`；归属：active_396, research_597, pool_current。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：20-day reversal
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0520 / 0.0313。

登记表达式或插件说明：

```text
-(close / lag(close, 20) - 1)
```


<a id="f-2872726e183d5cb9"></a>

## rev5

- ID：`2872726e183d5cb9`；归属：active_396, research_597, pool_current。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：5-day reversal
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0306 / 0.0176。

登记表达式或插件说明：

```text
-(close / lag(close, 5) - 1)
```


<a id="f-809e7d0910929fed"></a>

## rev_vol_scaled

- ID：`809e7d0910929fed`；归属：历史候选，未列入上述集合。
- 机制：短期反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：vol-scaled reversal
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0432 / 0.0215。

登记表达式或插件说明：

```text
-(close / lag(close, 20) - 1) / rolling_std(ret, 20)
```


<a id="f-6b95eea15d64187e"></a>

## size_neutral_turn20

- ID：`6b95eea15d64187e`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：size-neutral turnover
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0724 / 0.0592。

登记表达式或插件说明：

```text
-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap)
```


<a id="f-f06787184795a25e"></a>

## size_small

- ID：`f06787184795a25e`；归属：历史候选，未列入上述集合。
- 机制：市值（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：small cap
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0146 / -0.0079。

登记表达式或插件说明：

```text
-log_cap
```


<a id="f-785620c89c1d1340"></a>

## skew20_low

- ID：`785620c89c1d1340`；归属：active_396, research_597, pool_current。
- 机制：收益偏度（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：return skewness
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0323 / 0.0118。

登记表达式或插件说明：

```text
-rolling_skew(ret, 20)
```


<a id="f-0a38584bd0558cdb"></a>

## turn20_low

- ID：`0a38584bd0558cdb`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：20-day mean turnover (low is good)
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0644 / 0.0573。

登记表达式或插件说明：

```text
-rolling_mean(turnover, 20)
```


<a id="f-2102e7b0aa51c223"></a>

## vol20_low

- ID：`2102e7b0aa51c223`；归属：active_396, research_597, pool_current。
- 机制：低波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：20-day realised vol (low is good)
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0735 / 0.0654。

登记表达式或插件说明：

```text
-rolling_std(ret, 20)
```


<a id="f-83685fe52892abc9"></a>

## vol60_low

- ID：`83685fe52892abc9`；归属：active_396, research_597, pool_current。
- 机制：低波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：60-day realised vol
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0673 / 0.0554。

登记表达式或插件说明：

```text
-rolling_std(ret, 60)
```


<a id="f-f3475b30ea61a327"></a>

## vol_of_turn20

- ID：`f3475b30ea61a327`；归属：active_396, research_597, pool_current。
- 机制：换手率波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：cv of turnover
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0396 / 0.0176。

登记表达式或插件说明：

```text
-rolling_std(turnover, 20) / rolling_mean(turnover, 20)
```


<a id="f-558f19c112e3f77b"></a>

## vwap_dev

- ID：`558f19c112e3f77b`；归属：历史候选，未列入上述集合。
- 机制：收盘相对均价偏离（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：close vs vwap
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0134 / 0.0002。

登记表达式或插件说明：

```text
-(close / vwap - 1)
```
