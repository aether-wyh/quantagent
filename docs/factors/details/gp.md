# 遗传规划

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-eb2bb8242d2892f8"></a>

## gp1_00

- ID：`eb2bb8242d2892f8`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.99
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0739 / 0.0589。

登记表达式或插件说明：

```text
rolling_cov(high, volume, 5)
```


<a id="f-74a789b75300ff60"></a>

## gp1_01

- ID：`74a789b75300ff60`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.43
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0858 / 0.0725。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open
```


<a id="f-4f890698d6058eb4"></a>

## gp1_02

- ID：`4f890698d6058eb4`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.42
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0858 / 0.0725。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5) + log(low)
```


<a id="f-0943bdb572aa6765"></a>

## gp1_03

- ID：`0943bdb572aa6765`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.42
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0858 / 0.0725。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5)
```


<a id="f-811bd41513b681c9"></a>

## gp1_04

- ID：`811bd41513b681c9`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.42
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0858 / 0.0725。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5) + log(ema(amount, 3))
```


<a id="f-8ae3bebfc01770ad"></a>

## gp1_05

- ID：`8ae3bebfc01770ad`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.42
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0858 / 0.0725。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5) + log(amount)
```


<a id="f-3b16b04e62c50cf9"></a>

## gp1_06

- ID：`3b16b04e62c50cf9`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -26.42
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0858 / 0.0725。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5) + ema(rolling_beta(high, high, 10), 20)
```


<a id="f-84574dce52d8d254"></a>

## gp1_07

- ID：`84574dce52d8d254`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.79
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0284 / 0.0218。

登记表达式或插件说明：

```text
rolling_beta(sign(cs_neutralize(ema(amount, 3), log_cap)), prev_close, 10)
```


<a id="f-62310cb495194b5e"></a>

## gp1_08

- ID：`62310cb495194b5e`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t 23.62
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0678 / 0.0592。

登记表达式或插件说明：

```text
rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5))
```


<a id="f-de6b19da202fdaf2"></a>

## gp1_09

- ID：`de6b19da202fdaf2`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.33
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0804 / 0.0625。

登记表达式或插件说明：

```text
rolling_std(abs(prev_close * (volume + (close + close))), 10)
```


<a id="f-c2ec148986c8b1ab"></a>

## gp1_10

- ID：`c2ec148986c8b1ab`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.33
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0804 / 0.0625。

登记表达式或插件说明：

```text
rolling_std(abs(prev_close * (volume - low + volume)), 10)
```


<a id="f-f9fbb91f87665fcf"></a>

## gp1_11

- ID：`f9fbb91f87665fcf`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.33
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0804 / 0.0625。

登记表达式或插件说明：

```text
rolling_std(abs(prev_close * (volume + volume)), 10)
```


<a id="f-24d557d4617883d7"></a>

## gp1_12

- ID：`24d557d4617883d7`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.30
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0786 / 0.0672。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 20), 5) + log(amount)
```


<a id="f-52ce0824074a2165"></a>

## gp1_13

- ID：`52ce0824074a2165`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.06
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0789 / 0.0679。

登记表达式或插件说明：

```text
volume * rolling_max(rolling_cov(high, volume, 5), 5)
```


<a id="f-c606d9cd1247efea"></a>

## gp1_14

- ID：`c606d9cd1247efea`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -22.85
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0802 / 0.0622。

登记表达式或插件说明：

```text
rolling_std(abs(prev_close * (volume - low + (rolling_sum(high, 10) + turnover))), 10)
```


<a id="f-a637179836f6e9a9"></a>

## gp1_15

- ID：`a637179836f6e9a9`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -23.53
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0646 / 0.0529。

登记表达式或插件说明：

```text
rolling_cov(volume - low, ret, 40) * (rolling_cov(high, amount, 5) - rolling_corr(amount, amount, 10) + rolling_std(vwap, 5))
```


<a id="f-2cc41646ed869a82"></a>

## gp1_16

- ID：`2cc41646ed869a82`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -22.98
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0258 / 0.0205。

登记表达式或插件说明：

```text
rolling_beta(sign(cs_neutralize(amount, (close - amount) / (log_cap / volume))), log(log_cap * open), 10)
```


<a id="f-5647e44d90eb07f6"></a>

## gp1_17

- ID：`5647e44d90eb07f6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -22.93
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0317 / 0.0239。

登记表达式或插件说明：

```text
rolling_beta(sign(cs_neutralize(amount + (low - high), rolling_skew(vwap * vwap, 120))), prev_close, 10)
```


<a id="f-c74477606c584fdb"></a>

## gp1_18

- ID：`c74477606c584fdb`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -22.38
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0733 / 0.0567。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 5), 5) + log(cs_neutralize(low, log_cap))
```


<a id="f-9cd762fa35943623"></a>

## gp1_19

- ID：`9cd762fa35943623`；归属：research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 1; train t -22.19
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0722 / 0.0508。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 3), 5) + log(cs_neutralize(low, log_cap))
```


<a id="f-bdc9424dcd4476c3"></a>

## gp2_00

- ID：`bdc9424dcd4476c3`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -24.41
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0655 / 0.0536。

登记表达式或插件说明：

```text
rolling_cov(rolling_cov(amount, vwap, 3), amount, 10)
```


<a id="f-10e930c0fdb91d55"></a>

## gp2_01

- ID：`10e930c0fdb91d55`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -24.41
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0655 / 0.0536。

登记表达式或插件说明：

```text
rolling_cov(log_cap + amount, rolling_cov(amount, vwap, 3) + open / turnover, 10)
```


<a id="f-fc0e18ea5741dcc1"></a>

## gp2_02

- ID：`fc0e18ea5741dcc1`；归属：research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t 23.74
- 原判定：pass_worst+style:turnover20；历史均值 / 最差年 RankIC：0.0936 / 0.0760。

登记表达式或插件说明：

```text
log_cap / log(delta(amount, 20))
```


<a id="f-f522e95209110c5c"></a>

## gp2_03

- ID：`f522e95209110c5c`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -23.73
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0650 / 0.0518。

登记表达式或插件说明：

```text
rolling_cov(rolling_cov(amount, vwap, 3) + open / turnover, volume - low, 10)
```


<a id="f-399a52f00401bd8a"></a>

## gp2_04

- ID：`399a52f00401bd8a`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -23.60
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0656 / 0.0474。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - low, 10)
```


<a id="f-c5db27ead08c6825"></a>

## gp2_05

- ID：`c5db27ead08c6825`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -23.60
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0656 / 0.0474。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - vwap, 10)
```


<a id="f-6fc31b4d00c93ac3"></a>

## gp2_06

- ID：`6fc31b4d00c93ac3`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -23.60
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0656 / 0.0474。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - close * close, 10)
```


<a id="f-7ed8adfb1ced15f8"></a>

## gp2_07

- ID：`7ed8adfb1ced15f8`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -23.40
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0655 / 0.0472。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - rolling_mean(cs_neutralize(vwap, log_cap), 5), 10)
```


<a id="f-94f9b8ef07881462"></a>

## gp2_08

- ID：`94f9b8ef07881462`；归属：research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t 22.81
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0802 / 0.0654。

登记表达式或插件说明：

```text
log_cap / log(delta(amount, 3))
```


<a id="f-01455b795cbbee70"></a>

## gp2_09

- ID：`01455b795cbbee70`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -22.82
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0650 / 0.0465。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - rolling_mean(cs_neutralize(vwap, log_cap), 60), 10)
```


<a id="f-80321c4a0d32ea1b"></a>

## gp2_10

- ID：`80321c4a0d32ea1b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -22.40
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0584 / 0.0468。

登记表达式或插件说明：

```text
(rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low))
```


<a id="f-047c1a82764b10af"></a>

## gp2_11

- ID：`047c1a82764b10af`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -22.73
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0584 / 0.0476。

登记表达式或插件说明：

```text
(rolling_cov(amount, vwap, 3) + open / turnover) / (rolling_cov(open, log_cap, 20) / turnover + sign(low))
```


<a id="f-bbf52754f9f16d2a"></a>

## gp2_12

- ID：`bbf52754f9f16d2a`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.98
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0792 / 0.0560。

登记表达式或插件说明：

```text
rolling_cov(prev_close + amount, amount, 10)
```


<a id="f-1cf073171e5c2801"></a>

## gp2_13

- ID：`1cf073171e5c2801`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.98
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0792 / 0.0560。

登记表达式或插件说明：

```text
rolling_cov(log_cap + amount, amount, 10)
```


<a id="f-512106d1582cc5de"></a>

## gp2_14

- ID：`512106d1582cc5de`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.98
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0792 / 0.0560。

登记表达式或插件说明：

```text
rolling_std(amount, 10)
```


<a id="f-fa8f3b9c8f131558"></a>

## gp2_15

- ID：`fa8f3b9c8f131558`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.98
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0792 / 0.0542。

登记表达式或插件说明：

```text
rolling_std(amount, 5)
```


<a id="f-791a83fff8b15524"></a>

## gp2_16

- ID：`791a83fff8b15524`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.97
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0618 / 0.0541。

登记表达式或插件说明：

```text
rolling_cov(rolling_mean(log(turnover), 5), amount, 10)
```


<a id="f-6ab501401d690670"></a>

## gp2_17

- ID：`6ab501401d690670`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t 21.95
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0787 / 0.0567。

登记表达式或插件说明：

```text
rolling_cov(abs(high) - (volume + amount), amount, 10)
```


<a id="f-eddff1845edd7886"></a>

## gp2_18

- ID：`eddff1845edd7886`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.98
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0792 / 0.0560。

登记表达式或插件说明：

```text
rolling_cov(cs_zscore(prev_close) + cs_neutralize(open, log_cap) + amount, amount, 10)
```


<a id="f-2c86bd1f54c10b50"></a>

## gp2_19

- ID：`2c86bd1f54c10b50`；归属：research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 2; train t -21.73
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0666 / 0.0502。

登记表达式或插件说明：

```text
log(cs_neutralize(rolling_cov(turnover, ret, 3), delta(prev_close, 10)))
```


<a id="f-5f66b19823a5e49e"></a>

## gp3_00

- ID：`5f66b19823a5e49e`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -25.89
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0877 / 0.0760。

登记表达式或插件说明：

```text
rolling_cov(turnover * close, volume, 10)
```


<a id="f-71a391aaaafe4e8a"></a>

## gp3_01

- ID：`71a391aaaafe4e8a`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -17.63
- 原判定：pass_worst+style:turnover20；历史均值 / 最差年 RankIC：0.0890 / 0.0550。

登记表达式或插件说明：

```text
(log_cap + amount * turnover) * close
```


<a id="f-de73ab8aa9f1e5d9"></a>

## gp3_02

- ID：`de73ab8aa9f1e5d9`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -14.32
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0849 / 0.0493。

登记表达式或插件说明：

```text
rolling_std(turnover * close * delta(vwap, 3), 5) * amount
```


<a id="f-b0ad0bdd0e9772b2"></a>

## gp3_03

- ID：`b0ad0bdd0e9772b2`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -21.20
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0681 / 0.0536。

登记表达式或插件说明：

```text
rolling_cov(delta(vwap, 3), volume, 10)
```


<a id="f-dffb2a7e0ae3b1e0"></a>

## gp3_04

- ID：`dffb2a7e0ae3b1e0`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -21.69
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0639 / 0.0498。

登记表达式或插件说明：

```text
rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10)
```


<a id="f-0d85ae97a74ed695"></a>

## gp3_05

- ID：`0d85ae97a74ed695`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -22.82
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0662 / 0.0575。

登记表达式或插件说明：

```text
rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3)
```


<a id="f-fff2c93bc8ad4d27"></a>

## gp3_06

- ID：`fff2c93bc8ad4d27`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -20.20
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0830 / 0.0592。

登记表达式或插件说明：

```text
(log_cap + amount * turnover) * ema(amount, 60)
```


<a id="f-499117c942f7bd77"></a>

## gp3_07

- ID：`499117c942f7bd77`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -17.68
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0834 / 0.0475。

登记表达式或插件说明：

```text
rolling_std(log_cap * close, 5) * amount
```


<a id="f-e59c73c0970f73e6"></a>

## gp3_08

- ID：`e59c73c0970f73e6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -19.51
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0498 / 0.0339。

登记表达式或插件说明：

```text
rolling_cov(rolling_max(log(log_cap), 5), volume, 10)
```


<a id="f-fd67a30d49cbfb03"></a>

## gp3_09

- ID：`fd67a30d49cbfb03`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -21.71
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0521 / 0.0435。

登记表达式或插件说明：

```text
rolling_corr(amount, cs_neutralize(turnover, log_cap) * abs(cs_zscore(high)), 3)
```


<a id="f-e6e2edc89bdda3e1"></a>

## gp3_10

- ID：`e6e2edc89bdda3e1`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -17.14
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0823 / 0.0463。

登记表达式或插件说明：

```text
rolling_std(log_cap * delta(vwap, 3), 5) * amount
```


<a id="f-5069c32deee54111"></a>

## gp3_11

- ID：`5069c32deee54111`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -20.26
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0681 / 0.0515。

登记表达式或插件说明：

```text
rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low)))
```


<a id="f-8b1414e8bfc23cd2"></a>

## gp3_12

- ID：`8b1414e8bfc23cd2`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -19.60
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0532 / 0.0372。

登记表达式或插件说明：

```text
rolling_cov(turnover, ret, 5) + rolling_corr(close, amount, 10) + ret
```


<a id="f-cc8dfe762074a03b"></a>

## gp3_13

- ID：`cc8dfe762074a03b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -17.39
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0417 / 0.0311。

登记表达式或插件说明：

```text
rolling_cov(delta(vwap, 3), volume, 3)
```


<a id="f-890db2a867d903cc"></a>

## gp3_14

- ID：`890db2a867d903cc`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -15.14
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0523 / 0.0349。

登记表达式或插件说明：

```text
ts_zscore(ema(amount, 60), 20)
```


<a id="f-aae82322d141ceb3"></a>

## gp3_15

- ID：`aae82322d141ceb3`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -11.65
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0508 / 0.0366。

登记表达式或插件说明：

```text
rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / volume)
```


<a id="f-06c2b71eb028435c"></a>

## gp3_16

- ID：`06c2b71eb028435c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -19.06
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0420 / 0.0230。

登记表达式或插件说明：

```text
rolling_cov(turnover, ret, 5) + rolling_corr(close, amount, 10) + abs(cs_zscore(high))
```


<a id="f-476feccf178173ae"></a>

## gp3_17

- ID：`476feccf178173ae`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -13.93
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0449 / 0.0303。

登记表达式或插件说明：

```text
cs_neutralize(delta(turnover * close, 120), log_cap) * (open + amount)
```


<a id="f-0df2f2b5066d45e6"></a>

## gp3_18

- ID：`0df2f2b5066d45e6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -14.37
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0376 / 0.0095。

登记表达式或插件说明：

```text
delta(rolling_max(cs_rank(volume), 3), 20)
```


<a id="f-17ee9ece3170bcbf"></a>

## gp3_19

- ID：`17ee9ece3170bcbf`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 3; train t -15.38
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0501 / 0.0342。

登记表达式或插件说明：

```text
ts_zscore(ema(amount, 60), 10) - ema(rolling_corr(log_cap, vwap, 5), 5)
```


<a id="f-d66064ce03d13976"></a>

## gp4_00

- ID：`d66064ce03d13976`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -18.52
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0740 / 0.0598。

登记表达式或插件说明：

```text
rolling_std(rolling_sum(rolling_sum(turnover * amount, 10), 5), 10)
```


<a id="f-b52c5d865efe72fb"></a>

## gp4_01

- ID：`b52c5d865efe72fb`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -21.24
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0870 / 0.0707。

登记表达式或插件说明：

```text
rolling_max(cs_rank(turnover * amount), 10)
```


<a id="f-a8b79c5984868524"></a>

## gp4_02

- ID：`a8b79c5984868524`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -25.17
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0810 / 0.0622。

登记表达式或插件说明：

```text
rolling_max(cs_rank(ret), 10)
```


<a id="f-e4359fc7e14de2d0"></a>

## gp4_03

- ID：`e4359fc7e14de2d0`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -18.97
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0876 / 0.0661。

登记表达式或插件说明：

```text
turnover * amount
```


<a id="f-739e112e65ed767d"></a>

## gp4_04

- ID：`739e112e65ed767d`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -20.15
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0775 / 0.0510。

登记表达式或插件说明：

```text
rolling_max(cs_rank(close - rolling_cov(abs(prev_close), ret - amount, 5)), 10)
```


<a id="f-c50f5fbc854a53ad"></a>

## gp4_05

- ID：`c50f5fbc854a53ad`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -20.54
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0619 / 0.0483。

登记表达式或插件说明：

```text
turnover * (rolling_beta(amount, open, 20) / rolling_corr(log_cap, prev_close, 20))
```


<a id="f-ea1d042e8d3b72f6"></a>

## gp4_06

- ID：`ea1d042e8d3b72f6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -21.37
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0790 / 0.0444。

登记表达式或插件说明：

```text
rolling_std(rolling_cov(rolling_residual(low, vwap, 5), ret - amount, 5), 10)
```


<a id="f-430baf8234d7f598"></a>

## gp4_07

- ID：`430baf8234d7f598`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -20.29
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0690 / 0.0353。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(prev_close, vwap, 5)), 10)
```


<a id="f-13726edfa537bfff"></a>

## gp4_08

- ID：`13726edfa537bfff`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -21.32
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0626 / 0.0497。

登记表达式或插件说明：

```text
turnover * (rolling_beta(amount, open, 20) / rolling_corr(close * log(volume), prev_close, 20))
```


<a id="f-a764d0ad5b671f03"></a>

## gp4_09

- ID：`a764d0ad5b671f03`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -24.93
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0721 / 0.0598。

登记表达式或插件说明：

```text
cs_rank(abs(close)) / rolling_beta(ts_zscore(amount, 10), volume, 10)
```


<a id="f-f22bc5eef7eeb756"></a>

## gp4_10

- ID：`f22bc5eef7eeb756`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -23.04
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0637 / 0.0468。

登记表达式或插件说明：

```text
turnover * (rolling_beta(amount, open, 20) / rolling_corr(amount, prev_close, 20))
```


<a id="f-9357ef3a7e1aa3e8"></a>

## gp4_11

- ID：`9357ef3a7e1aa3e8`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -22.08
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0706 / 0.0393。

登记表达式或插件说明：

```text
rolling_max(cs_rank(close - vwap), 10)
```


<a id="f-ab0abf78488d9860"></a>

## gp4_12

- ID：`ab0abf78488d9860`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -17.54
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0771 / 0.0445。

登记表达式或插件说明：

```text
rolling_std(rolling_cov(abs(prev_close), ret - amount, 5), 10)
```


<a id="f-15a6836cee5e4bdc"></a>

## gp4_13

- ID：`15a6836cee5e4bdc`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -17.44
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0669 / 0.0328。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(prev_close, abs(volume) - high, 5)), 10)
```


<a id="f-6bcdb3cdf012b680"></a>

## gp4_14

- ID：`6bcdb3cdf012b680`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -18.16
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0617 / 0.0374。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(close, vwap, 5)), 10)
```


<a id="f-2cd73887274a0b23"></a>

## gp4_15

- ID：`2cd73887274a0b23`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -20.47
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0484 / 0.0319。

登记表达式或插件说明：

```text
rolling_corr(log_cap, turnover * log_cap - abs(turnover), 10)
```


<a id="f-ade5bb8c70c97f53"></a>

## gp4_16

- ID：`ade5bb8c70c97f53`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -20.09
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0533 / 0.0385。

登记表达式或插件说明：

```text
rolling_corr(log_cap, log(high / low), 10)
```


<a id="f-a46bd9c9fc0b3a87"></a>

## gp4_17

- ID：`a46bd9c9fc0b3a87`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -14.06
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0603 / 0.0279。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(abs(prev_close) * (close * turnover), vwap, 5)), 10)
```


<a id="f-f3767536a89c1bdd"></a>

## gp4_18

- ID：`f3767536a89c1bdd`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -23.59
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0601 / 0.0416。

登记表达式或插件说明：

```text
rolling_max(cs_rank(turnover * (rolling_beta(amount, open, 20) / rolling_corr(amount, prev_close, 20))), 10)
```


<a id="f-aa1192ee3046314b"></a>

## gp4_19

- ID：`aa1192ee3046314b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -19.81
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0708 / 0.0375。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(prev_close, ret, 5)), 10)
```


<a id="f-cc841c05faf9a55b"></a>

## gp4_20

- ID：`cc841c05faf9a55b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -17.91
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0550 / 0.0332。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(abs(log_cap) * (close * cs_neutralize(turnover, rolling_min(volume, 5))), vwap, 20)), 10)
```


<a id="f-355a58c63b65ea77"></a>

## gp4_21

- ID：`355a58c63b65ea77`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -15.66
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0568 / 0.0295。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(high, vwap, 5)), 10)
```


<a id="f-408547d0a0723c77"></a>

## gp4_22

- ID：`408547d0a0723c77`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -18.71
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0691 / 0.0581。

登记表达式或插件说明：

```text
turnover * (amount / rolling_corr(amount, prev_close, 20))
```


<a id="f-193b0a69f2af394c"></a>

## gp4_23

- ID：`193b0a69f2af394c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -15.85
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0634 / 0.0370。

登记表达式或插件说明：

```text
rolling_max(cs_rank(rolling_residual(abs(log_cap) * (close * cs_neutralize(turnover, rolling_min(volume, 5))), vwap, 5)), 10)
```


<a id="f-e45dd99d2f927a89"></a>

## gp4_24

- ID：`e45dd99d2f927a89`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 4; train t -16.81
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0454 / 0.0296。

登记表达式或插件说明：

```text
rolling_beta(amount, low, 20)
```


<a id="f-5508dc1eeaa98107"></a>

## gp5_00

- ID：`5508dc1eeaa98107`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t 25.89
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0875 / 0.0755。

登记表达式或插件说明：

```text
log_cap / close / rolling_cov(volume, turnover, 10)
```


<a id="f-99430a567ea52a5e"></a>

## gp5_01

- ID：`99430a567ea52a5e`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -26.21
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0730 / 0.0511。

登记表达式或插件说明：

```text
rolling_cov(volume, turnover, 10) + high / close - log_cap
```


<a id="f-57832c4d09037392"></a>

## gp5_02

- ID：`57832c4d09037392`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t 24.53
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0776 / 0.0675。

登记表达式或插件说明：

```text
(ts_rank(high, 10) - rolling_residual(open, close, 5)) / close / rolling_cov(volume, turnover, 10)
```


<a id="f-a4e53e812b1366b4"></a>

## gp5_03

- ID：`a4e53e812b1366b4`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -25.93
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0732 / 0.0522。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(volume, turnover, 5) + vwap, 3)
```


<a id="f-eebae56c9f009f14"></a>

## gp5_04

- ID：`eebae56c9f009f14`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -23.82
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0673 / 0.0497。

登记表达式或插件说明：

```text
rolling_cov(volume, vwap + rolling_std(high, 5), 5) + high / close - log_cap
```


<a id="f-0765b1e4d998d06e"></a>

## gp5_05

- ID：`0765b1e4d998d06e`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -26.03
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0723 / 0.0523。

登记表达式或插件说明：

```text
rolling_cov(volume, turnover, 5) + high / close - log_cap
```


<a id="f-95285edc7fce65c5"></a>

## gp5_06

- ID：`95285edc7fce65c5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -25.27
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0685 / 0.0523。

登记表达式或插件说明：

```text
rolling_cov(volume, turnover, 3) + high / close - log_cap
```


<a id="f-4d6defba3591573a"></a>

## gp5_07

- ID：`4d6defba3591573a`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -27.12
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0844 / 0.0667。

登记表达式或插件说明：

```text
rolling_cov(ema(turnover, 3), cs_neutralize(amount + ret, open), 5)
```


<a id="f-ae173e3b2693c135"></a>

## gp5_08

- ID：`ae173e3b2693c135`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t 21.27
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0523 / 0.0259。

登记表达式或插件说明：

```text
close / rolling_cov(volume, turnover, 10)
```


<a id="f-93a815719e011083"></a>

## gp5_09

- ID：`93a815719e011083`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -25.63
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0767 / 0.0574。

登记表达式或插件说明：

```text
rolling_cov(volume, turnover, 5) + high / turnover - log_cap
```


<a id="f-3bccc54050801104"></a>

## gp5_10

- ID：`3bccc54050801104`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -23.16
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0770 / 0.0623。

登记表达式或插件说明：

```text
rolling_cov(ema(turnover, 3), cs_neutralize(amount + ret, log_cap), 5)
```


<a id="f-23c2247bf55e02fa"></a>

## gp5_11

- ID：`23c2247bf55e02fa`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -19.81
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0771 / 0.0575。

登记表达式或插件说明：

```text
cs_neutralize(rolling_cov(volume, turnover, 10) + high / close - log_cap, log_cap) / low
```


<a id="f-c73bf9fd416ad293"></a>

## gp5_12

- ID：`c73bf9fd416ad293`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t 24.60
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0641 / 0.0535。

登记表达式或插件说明：

```text
ret * ((rolling_beta(amount, turnover - high, 10) + ret) / ret * vwap)
```


<a id="f-63354b0882c4d2c1"></a>

## gp5_13

- ID：`63354b0882c4d2c1`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t 22.82
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0686 / 0.0453。

登记表达式或插件说明：

```text
log_cap / volume / rolling_cov(volume, turnover, 10)
```


<a id="f-6d54bf2840b207e7"></a>

## gp5_14

- ID：`6d54bf2840b207e7`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -14.96
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0771 / 0.0446。

登记表达式或插件说明：

```text
cs_zscore(rolling_cov(ema(turnover, 3), cs_neutralize(amount + ret, log_cap), 5)) / vwap
```


<a id="f-dc0589fcb1e4d29e"></a>

## gp5_15

- ID：`dc0589fcb1e4d29e`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -15.32
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0742 / 0.0467。

登记表达式或插件说明：

```text
abs(rolling_cov(amount, open, 3) - rolling_cov(low, amount, 20))
```


<a id="f-1b04f2c48fd80f59"></a>

## gp5_16

- ID：`1b04f2c48fd80f59`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -14.13
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0695 / 0.0512。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(low, amount, 20) + vwap, 3)
```


<a id="f-c8baa8bada69e77f"></a>

## gp5_17

- ID：`c8baa8bada69e77f`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -23.97
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0738 / 0.0618。

登记表达式或插件说明：

```text
(rolling_cov(open, ema(amount, 3), 5) + rolling_mean(volume, 10)) * low
```


<a id="f-fdc6dcfaf94ac7c0"></a>

## gp5_18

- ID：`fdc6dcfaf94ac7c0`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -17.07
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0748 / 0.0488。

登记表达式或插件说明：

```text
(rolling_cov(open, ema(amount, 3), 20) + rolling_mean(volume, 10)) * low
```


<a id="f-e2292091ce3c1165"></a>

## gp5_19

- ID：`e2292091ce3c1165`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -17.35
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0519 / 0.0402。

登记表达式或插件说明：

```text
(rolling_cov(open, ema(amount, 3), 5) + rolling_mean(ts_zscore(abs(low), 10), 10)) * low
```


<a id="f-e6a247052a64af3f"></a>

## gp5_20

- ID：`e6a247052a64af3f`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t 14.01
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0741 / 0.0356。

登记表达式或插件说明：

```text
log_cap - rolling_std(low, 10) * (amount * low)
```


<a id="f-97cf3d880e429cc2"></a>

## gp5_21

- ID：`97cf3d880e429cc2`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -18.73
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0741 / 0.0429。

登记表达式或插件说明：

```text
abs(rolling_cov(amount, open, 3) - rolling_std(vwap + close, 5))
```


<a id="f-df933f947021807c"></a>

## gp5_22

- ID：`df933f947021807c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -12.51
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0581 / 0.0447。

登记表达式或插件说明：

```text
cs_zscore(close / low) / vwap
```


<a id="f-60abb563a0a10cc8"></a>

## gp5_23

- ID：`60abb563a0a10cc8`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -19.67
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0842 / 0.0520。

登记表达式或插件说明：

```text
log_cap / volume / (log_cap - rolling_std(low, 10) * (amount * low))
```


<a id="f-6aa3a2144b6648ea"></a>

## gp5_24

- ID：`6aa3a2144b6648ea`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：GP search seed 5; train t -24.83
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0639 / 0.0532。

登记表达式或插件说明：

```text
rolling_cov(ema(rolling_max(turnover, 40) * ts_zscore(high, 20), 3), cs_neutralize(amount + ret, log_cap), 5)
```
