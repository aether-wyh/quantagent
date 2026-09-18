# Alpha101 插件

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-4ce245e119d93c52"></a>

## alpha101_001

- ID：`4ce245e119d93c52`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0145 / 0.0064。

登记表达式或插件说明：

```text
(rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) -0.5)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_001
```

- 插件：`alpha101:alpha_001`；变换链：`[]`。

<a id="f-b86e574d9ad2fcca"></a>

## alpha101_002

- ID：`b86e574d9ad2fcca`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0139 / 0.0060。

登记表达式或插件说明：

```text
(-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_002
```

- 插件：`alpha101:alpha_002`；变换链：`[]`。

<a id="f-ab4a43967f68b45f"></a>

## alpha101_003

- ID：`ab4a43967f68b45f`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0289 / 0.0155。

登记表达式或插件说明：

```text
(-1 * correlation(rank(open), rank(volume), 10))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_003
```

- 插件：`alpha101:alpha_003`；变换链：`[]`。

<a id="f-436518a7cff54f32"></a>

## alpha101_004

- ID：`436518a7cff54f32`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0380 / 0.0313。

登记表达式或插件说明：

```text
(-1 * Ts_Rank(rank(low), 9))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_004
```

- 插件：`alpha101:alpha_004`；变换链：`[]`。

<a id="f-e0809db6f91b1a96"></a>

## alpha101_005

- ID：`e0809db6f91b1a96`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0027 / -0.0159。

登记表达式或插件说明：

```text
(rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_005
```

- 插件：`alpha101:alpha_005`；变换链：`[]`。

<a id="f-5c20a5604c5b5774"></a>

## alpha101_006

- ID：`5c20a5604c5b5774`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0277 / 0.0118。

登记表达式或插件说明：

```text
(-1 * correlation(open, volume, 10))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_006
```

- 插件：`alpha101:alpha_006`；变换链：`[]`。

<a id="f-adfe6f296aea49f3"></a>

## alpha101_007

- ID：`adfe6f296aea49f3`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0100 / 0.0032。

登记表达式或插件说明：

```text
((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1* 1))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_007
```

- 插件：`alpha101:alpha_007`；变换链：`[]`。

<a id="f-d853f649a36d13b3"></a>

## alpha101_008

- ID：`d853f649a36d13b3`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0163 / -0.0008。

登记表达式或插件说明：

```text
(-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)),10))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_008
```

- 插件：`alpha101:alpha_008`；变换链：`[]`。

<a id="f-14a32a72d0ee8ab5"></a>

## alpha101_009

- ID：`14a32a72d0ee8ab5`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0077 / -0.0003。

登记表达式或插件说明：

```text
((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ?delta(close, 1) : (-1 * delta(close, 1))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_009
```

- 插件：`alpha101:alpha_009`；变换链：`[]`。

<a id="f-9657c19e16240359"></a>

## alpha101_010

- ID：`9657c19e16240359`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0043 / -0.0017。

登记表达式或插件说明：

```text
rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0)? delta(close, 1) : (-1 * delta(close, 1)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_010
```

- 插件：`alpha101:alpha_010`；变换链：`[]`。

<a id="f-bff243a7aea75a4f"></a>

## alpha101_011

- ID：`bff243a7aea75a4f`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0144 / 0.0058。

登记表达式或插件说明：

```text
((rank(ts_max((vwap - close), 3)) + rank(ts_min((vwap - close), 3))) *rank(delta(volume, 3)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_011
```

- 插件：`alpha101:alpha_011`；变换链：`[]`。

<a id="f-414246f6505b30b7"></a>

## alpha101_012

- ID：`414246f6505b30b7`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0317 / 0.0208。

登记表达式或插件说明：

```text
(sign(delta(volume, 1)) * (-1 * delta(close, 1)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_012
```

- 插件：`alpha101:alpha_012`；变换链：`[]`。

<a id="f-ca2734cd0008812b"></a>

## alpha101_013

- ID：`ca2734cd0008812b`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0441 / 0.0310。

登记表达式或插件说明：

```text
(-1 * rank(covariance(rank(close), rank(volume), 5)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_013
```

- 插件：`alpha101:alpha_013`；变换链：`[]`。

<a id="f-faa4c1ab8b5ea06a"></a>

## alpha101_014

- ID：`faa4c1ab8b5ea06a`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0199 / 0.0076。

登记表达式或插件说明：

```text
((-1 * rank(delta(returns, 3))) * correlation(open, volume, 10))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_014
```

- 插件：`alpha101:alpha_014`；变换链：`[]`。

<a id="f-009c44c78dfc08bb"></a>

## alpha101_015

- ID：`009c44c78dfc08bb`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0301 / 0.0195。

登记表达式或插件说明：

```text
(-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_015
```

- 插件：`alpha101:alpha_015`；变换链：`[]`。

<a id="f-f1e3dd61377c84d5"></a>

## alpha101_016

- ID：`f1e3dd61377c84d5`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0447 / 0.0281。

登记表达式或插件说明：

```text
(-1 * rank(covariance(rank(high), rank(volume), 5)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_016
```

- 插件：`alpha101:alpha_016`；变换链：`[]`。

<a id="f-09a605d42b07bf64"></a>

## alpha101_017

- ID：`09a605d42b07bf64`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0036 / -0.0112。

登记表达式或插件说明：

```text
(((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1))) *rank(ts_rank((volume / adv20), 5)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_017
```

- 插件：`alpha101:alpha_017`；变换链：`[]`。

<a id="f-97afeafe39c6c72a"></a>

## alpha101_018

- ID：`97afeafe39c6c72a`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0329 / 0.0219。

登记表达式或插件说明：

```text
(-1 * rank(((stddev(abs((close - open)), 5) + (close - open)) + correlation(close, open,10))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_018
```

- 插件：`alpha101:alpha_018`；变换链：`[]`。

<a id="f-63a04a2fb3bc787d"></a>

## alpha101_019

- ID：`63a04a2fb3bc787d`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0247 / 0.0163。

登记表达式或插件说明：

```text
((-1 * sign(((close - delay(close, 7)) + delta(close, 7)))) * (1 + rank((1 + sum(returns,250)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_019
```

- 插件：`alpha101:alpha_019`；变换链：`[]`。

<a id="f-0b95607f2f805fcd"></a>

## alpha101_020

- ID：`0b95607f2f805fcd`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0208 / 0.0083。

登记表达式或插件说明：

```text
(((-1 * rank((open - delay(high, 1)))) * rank((open - delay(close, 1)))) * rank((open -delay(low, 1))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_020
```

- 插件：`alpha101:alpha_020`；变换链：`[]`。

<a id="f-f07ae02234afd3ad"></a>

## alpha101_021

- ID：`f07ae02234afd3ad`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0113 / 0.0037。

登记表达式或插件说明：

```text
((((sum(close, 8) / 8) + stddev(close, 8)) < (sum(close, 2) / 2)) ? (-1 * 1) : (((sum(close,2) / 2) < ((sum(close, 8) / 8) - stddev(close, 8))) ? 1 : (((1 < (volume / adv20)) || ((volume /adv20) == 1)) ? 1 : (-1 * 1))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_021
```

- 插件：`alpha101:alpha_021`；变换链：`[]`。

<a id="f-97884411c19c3f21"></a>

## alpha101_022

- ID：`97884411c19c3f21`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0054 / -0.0016。

登记表达式或插件说明：

```text
(-1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_022
```

- 插件：`alpha101:alpha_022`；变换链：`[]`。

<a id="f-4d7429516da18893"></a>

## alpha101_023

- ID：`4d7429516da18893`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0221 / 0.0148。

登记表达式或插件说明：

```text
(((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_023
```

- 插件：`alpha101:alpha_023`；变换链：`[]`。

<a id="f-100aa894dd1c971f"></a>

## alpha101_024

- ID：`100aa894dd1c971f`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0276 / 0.0186。

登记表达式或插件说明：

```text
((((delta((sum(close, 100) / 100), 100) / delay(close, 100)) < 0.05) ||((delta((sum(close, 100) / 100), 100) / delay(close, 100)) == 0.05)) ? (-1 * (close - ts_min(close,100))) : (-1 * delta(close, 3)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_024
```

- 插件：`alpha101:alpha_024`；变换链：`[]`。

<a id="f-5946651b458ba7aa"></a>

## alpha101_025

- ID：`5946651b458ba7aa`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0065 / -0.0030。

登记表达式或插件说明：

```text
rank(((((-1 * returns) * adv20) * vwap) * (high - close)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_025
```

- 插件：`alpha101:alpha_025`；变换链：`[]`。

<a id="f-8a2d0a950d8e5b31"></a>

## alpha101_026

- ID：`8a2d0a950d8e5b31`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0316 / 0.0227。

登记表达式或插件说明：

```text
(-1 * ts_max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_026
```

- 插件：`alpha101:alpha_026`；变换链：`[]`。

<a id="f-a600476eff01f754"></a>

## alpha101_027

- ID：`a600476eff01f754`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0300 / 0.0218。

登记表达式或插件说明：

```text
((0.5 < rank((sum(correlation(rank(volume), rank(vwap), 6), 2) / 2.0))) ? (-1 * 1) : 1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_027
```

- 插件：`alpha101:alpha_027`；变换链：`[]`。

<a id="f-aa1e7724f5470500"></a>

## alpha101_028

- ID：`aa1e7724f5470500`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0095 / 0.0027。

登记表达式或插件说明：

```text
scale(((correlation(adv20, low, 5) + ((high + low) / 2)) - close))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_028
```

- 插件：`alpha101:alpha_028`；变换链：`[]`。

<a id="f-3f1f4b9129a01700"></a>

## alpha101_029

- ID：`3f1f4b9129a01700`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0406 / 0.0222。

登记表达式或插件说明：

```text
(min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1 * rank(delta((close - 1),5))))), 2), 1))))), 1), 5) + ts_rank(delay((-1 * returns), 6), 5))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_029
```

- 插件：`alpha101:alpha_029`；变换链：`[]`。

<a id="f-897a9d49eb1bdbbe"></a>

## alpha101_030

- ID：`897a9d49eb1bdbbe`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0008 / -0.0120。

登记表达式或插件说明：

```text
(((1.0 - rank(((sign((close - delay(close, 1))) + sign((delay(close, 1) - delay(close, 2)))) +sign((delay(close, 2) - delay(close, 3)))))) * sum(volume, 5)) / sum(volume, 20))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_030
```

- 插件：`alpha101:alpha_030`；变换链：`[]`。

<a id="f-99f5739918f7c642"></a>

## alpha101_031

- ID：`99f5739918f7c642`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0081 / -0.0019。

登记表达式或插件说明：

```text
((rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 *delta(close, 3)))) + sign(scale(correlation(adv20, low, 12))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_031
```

- 插件：`alpha101:alpha_031`；变换链：`[]`。

<a id="f-25c6c0dfa7394771"></a>

## alpha101_032

- ID：`25c6c0dfa7394771`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0057 / -0.0248。

登记表达式或插件说明：

```text
(scale(((sum(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5),230))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_032
```

- 插件：`alpha101:alpha_032`；变换链：`[]`。

<a id="f-ac1aee5f33684bc2"></a>

## alpha101_033

- ID：`ac1aee5f33684bc2`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0185 / 0.0091。

登记表达式或插件说明：

```text
rank((-1 * ((1 - (open / close))^1)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_033
```

- 插件：`alpha101:alpha_033`；变换链：`[]`。

<a id="f-98c5961b1c417c14"></a>

## alpha101_034

- ID：`98c5961b1c417c14`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0094 / -0.0022。

登记表达式或插件说明：

```text
rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_034
```

- 插件：`alpha101:alpha_034`；变换链：`[]`。

<a id="f-a97f7ec751dc049b"></a>

## alpha101_035

- ID：`a97f7ec751dc049b`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0129 / 0.0066。

登记表达式或插件说明：

```text
((Ts_Rank(volume, 32) * (1 - Ts_Rank(((close + high) - low), 16))) * (1 -Ts_Rank(returns, 32)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_035
```

- 插件：`alpha101:alpha_035`；变换链：`[]`。

<a id="f-fbd8389bcd16559e"></a>

## alpha101_036

- ID：`fbd8389bcd16559e`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0013 / -0.0137。

登记表达式或插件说明：

```text
(((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open- close)))) + (0.73 * rank(Ts_Rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap,adv20, 6)))) + (0.6 * rank((((sum(close, 200) / 200) - open) * (close - open)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_036
```

- 插件：`alpha101:alpha_036`；变换链：`[]`。

<a id="f-5aa2dd010b05ddda"></a>

## alpha101_037

- ID：`5aa2dd010b05ddda`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0211 / 0.0029。

登记表达式或插件说明：

```text
(rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_037
```

- 插件：`alpha101:alpha_037`；变换链：`[]`。

<a id="f-0d1a6e4d0cde6227"></a>

## alpha101_038

- ID：`0d1a6e4d0cde6227`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0179 / 0.0114。

登记表达式或插件说明：

```text
((-1 * rank(Ts_Rank(close, 10))) * rank((close / open)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_038
```

- 插件：`alpha101:alpha_038`；变换链：`[]`。

<a id="f-3fbb9b7e1c8809f8"></a>

## alpha101_039

- ID：`3fbb9b7e1c8809f8`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0276 / 0.0161。

登记表达式或插件说明：

```text
((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 +rank(sum(returns, 250))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_039
```

- 插件：`alpha101:alpha_039`；变换链：`[]`。

<a id="f-324f38013c042024"></a>

## alpha101_040

- ID：`324f38013c042024`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0685 / 0.0560。

登记表达式或插件说明：

```text
((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_040
```

- 插件：`alpha101:alpha_040`；变换链：`[]`。

<a id="f-aecebfa10bec7646"></a>

## alpha101_041

- ID：`aecebfa10bec7646`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0045 / -0.0088。

登记表达式或插件说明：

```text
(((high * low)^0.5) - vwap)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_041
```

- 插件：`alpha101:alpha_041`；变换链：`[]`。

<a id="f-7cc5c328eac92852"></a>

## alpha101_042

- ID：`7cc5c328eac92852`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0420 / 0.0194。

登记表达式或插件说明：

```text
(rank((vwap - close)) / rank((vwap + close)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_042
```

- 插件：`alpha101:alpha_042`；变换链：`[]`。

<a id="f-0ddcf537798db3f9"></a>

## alpha101_043

- ID：`0ddcf537798db3f9`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0128 / -0.0104。

登记表达式或插件说明：

```text
(ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_043
```

- 插件：`alpha101:alpha_043`；变换链：`[]`。

<a id="f-2abda3c6c8e27785"></a>

## alpha101_044

- ID：`2abda3c6c8e27785`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0381 / 0.0236。

登记表达式或插件说明：

```text
(-1 * correlation(high, rank(volume), 5))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_044
```

- 插件：`alpha101:alpha_044`；变换链：`[]`。

<a id="f-8ab85c6c2295cf53"></a>

## alpha101_045

- ID：`8ab85c6c2295cf53`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0209 / 0.0107。

登记表达式或插件说明：

```text
(-1 * ((rank((sum(delay(close, 5), 20) / 20)) * correlation(close, volume, 2)) *rank(correlation(sum(close, 5), sum(close, 20), 2))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_045
```

- 插件：`alpha101:alpha_045`；变换链：`[]`。

<a id="f-0b0c0f5520aa51e8"></a>

## alpha101_046

- ID：`0b0c0f5520aa51e8`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0266 / 0.0202。

登记表达式或插件说明：

```text
((0.25 < (((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10))) ?(-1 * 1) : (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < 0) ? 1 :((-1 * 1) * (close - delay(close, 1)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_046
```

- 插件：`alpha101:alpha_046`；变换链：`[]`。

<a id="f-b9a120d4a79b7361"></a>

## alpha101_047

- ID：`b9a120d4a79b7361`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0230 / 0.0097。

登记表达式或插件说明：

```text
((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sum(high, 5) /5))) - rank((vwap - delay(vwap, 5))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_047
```

- 插件：`alpha101:alpha_047`；变换链：`[]`。

<a id="f-1173ddf0db546360"></a>

## alpha101_048

- ID：`1173ddf0db546360`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(indneutralize(((correlation(delta(close, 1), delta(delay(close, 1), 1), 250) *delta(close, 1)) / close), IndClass.subindustry) / sum(((delta(close, 1) / delay(close, 1))^2), 250))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_048
```

- 插件：`alpha101:alpha_048`；变换链：`[]`。

<a id="f-296c55d3f5519e0f"></a>

## alpha101_049

- ID：`296c55d3f5519e0f`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0017 / -0.0122。

登记表达式或插件说明：

```text
(((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 *0.1)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_049
```

- 插件：`alpha101:alpha_049`；变换链：`[]`。

<a id="f-d72a54b3c938a32d"></a>

## alpha101_050

- ID：`d72a54b3c938a32d`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0351 / 0.0241。

登记表达式或插件说明：

```text
(-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_050
```

- 插件：`alpha101:alpha_050`；变换链：`[]`。

<a id="f-d5b01315689ab206"></a>

## alpha101_051

- ID：`d5b01315689ab206`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0044 / -0.0069。

登记表达式或插件说明：

```text
(((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 *0.05)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_051
```

- 插件：`alpha101:alpha_051`；变换链：`[]`。

<a id="f-6bf7a38e5f0f803e"></a>

## alpha101_052

- ID：`6bf7a38e5f0f803e`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0274 / 0.0164。

登记表达式或插件说明：

```text
((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * rank(((sum(returns, 240) -sum(returns, 20)) / 220))) * ts_rank(volume, 5))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_052
```

- 插件：`alpha101:alpha_052`；变换链：`[]`。

<a id="f-ce208953d75a9f45"></a>

## alpha101_053

- ID：`ce208953d75a9f45`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0058 / -0.0027。

登记表达式或插件说明：

```text
(-1 * delta((((close - low) - (high - close)) / (close - low)), 9))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_053
```

- 插件：`alpha101:alpha_053`；变换链：`[]`。

<a id="f-a37dbc2170c5de9d"></a>

## alpha101_054

- ID：`a37dbc2170c5de9d`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0002 / -0.0121。

登记表达式或插件说明：

```text
((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_054
```

- 插件：`alpha101:alpha_054`；变换链：`[]`。

<a id="f-b6cde25d8e482500"></a>

## alpha101_055

- ID：`b6cde25d8e482500`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0281 / 0.0216。

登记表达式或插件说明：

```text
(-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low,12)))), rank(volume), 6))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_055
```

- 插件：`alpha101:alpha_055`；变换链：`[]`。

<a id="f-bbdcecd396a3648e"></a>

## alpha101_056

- ID：`bbdcecd396a3648e`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0073 / -0.0123。

登记表达式或插件说明：

```text
(0 - (1 * (rank((sum(returns, 10) / sum(sum(returns, 2), 3))) * rank((returns * cap)))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_056
```

- 插件：`alpha101:alpha_056`；变换链：`[]`。

<a id="f-634a3662f2b01754"></a>

## alpha101_057

- ID：`634a3662f2b01754`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0119 / -0.0007。

登记表达式或插件说明：

```text
(0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_057
```

- 插件：`alpha101:alpha_057`；变换链：`[]`。

<a id="f-a7411f7ceebe63ff"></a>

## alpha101_058

- ID：`a7411f7ceebe63ff`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.sector), volume,3.92795), 7.89291), 5.50322))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_058
```

- 插件：`alpha101:alpha_058`；变换链：`[]`。

<a id="f-58ef880275b587ae"></a>

## alpha101_059

- ID：`58ef880275b587ae`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(((vwap * 0.728317) + (vwap *(1 - 0.728317))), IndClass.industry), volume, 4.25197), 16.2289), 8.19648))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_059
```

- 插件：`alpha101:alpha_059`；变换链：`[]`。

<a id="f-b1b1bcef2814990b"></a>

## alpha101_060

- ID：`b1b1bcef2814990b`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0018 / -0.0141。

登记表达式或插件说明：

```text
(0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) -scale(rank(ts_argmax(close, 10))))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_060
```

- 插件：`alpha101:alpha_060`；变换链：`[]`。

<a id="f-51e09b2a2072c799"></a>

## alpha101_061

- ID：`51e09b2a2072c799`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0238 / 0.0029。

登记表达式或插件说明：

```text
(rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_061
```

- 插件：`alpha101:alpha_061`；变换链：`[]`。

<a id="f-50c121351d27fe2e"></a>

## alpha101_062

- ID：`50c121351d27fe2e`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0071 / -0.0006。

登记表达式或插件说明：

```text
((rank(correlation(vwap, sum(adv20, 22.4101), 9.91009)) < rank(((rank(open) +rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_062
```

- 插件：`alpha101:alpha_062`；变换链：`[]`。

<a id="f-82f656ec032bf6a9"></a>

## alpha101_063

- ID：`82f656ec032bf6a9`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank(decay_linear(delta(IndNeutralize(close, IndClass.industry), 2.25164), 8.22237))- rank(decay_linear(correlation(((vwap * 0.318108) + (open * (1 - 0.318108))), sum(adv180,37.2467), 13.557), 12.2883))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_063
```

- 插件：`alpha101:alpha_063`；变换链：`[]`。

<a id="f-896735480eb10481"></a>

## alpha101_064

- ID：`896735480eb10481`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0016 / -0.0115。

登记表达式或插件说明：

```text
((rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054),sum(adv120, 12.7054), 16.6208)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 -0.178404))), 3.69741))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_064
```

- 插件：`alpha101:alpha_064`；变换链：`[]`。

<a id="f-4cc0e429aeaba5ff"></a>

## alpha101_065

- ID：`4cc0e429aeaba5ff`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0217 / 0.0078。

登记表达式或插件说明：

```text
((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60,8.6911), 6.40374)) < rank((open - ts_min(open, 13.635)))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_065
```

- 插件：`alpha101:alpha_065`；变换链：`[]`。

<a id="f-e3d2bdf67ed5cbd3"></a>

## alpha101_066

- ID：`e3d2bdf67ed5cbd3`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0212 / 0.0110。

登记表达式或插件说明：

```text
((rank(decay_linear(delta(vwap, 3.51013), 7.23052)) + Ts_Rank(decay_linear(((((low* 0.96633) + (low * (1 - 0.96633))) - vwap) / (open - ((high + low) / 2))), 11.4157), 6.72611)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_066
```

- 插件：`alpha101:alpha_066`；变换链：`[]`。

<a id="f-c069bbeafffeed57"></a>

## alpha101_067

- ID：`c069bbeafffeed57`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank((high - ts_min(high, 2.14593)))^rank(correlation(IndNeutralize(vwap,IndClass.sector), IndNeutralize(adv20, IndClass.subindustry), 6.02936))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_067
```

- 插件：`alpha101:alpha_067`；变换链：`[]`。

<a id="f-80b90c6087b658e6"></a>

## alpha101_068

- ID：`80b90c6087b658e6`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0048 / -0.0026。

登记表达式或插件说明：

```text
((Ts_Rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333) <rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1.06157))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_068
```

- 插件：`alpha101:alpha_068`；变换链：`[]`。

<a id="f-4e42759a09576336"></a>

## alpha101_069

- ID：`4e42759a09576336`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank(ts_max(delta(IndNeutralize(vwap, IndClass.industry), 2.72412),4.79344))^Ts_Rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416),9.0615)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_069
```

- 插件：`alpha101:alpha_069`；变换链：`[]`。

<a id="f-ff13dd3d202c55b6"></a>

## alpha101_070

- ID：`ff13dd3d202c55b6`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank(delta(vwap, 1.29456))^Ts_Rank(correlation(IndNeutralize(close,IndClass.industry), adv50, 17.8256), 17.9171)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_070
```

- 插件：`alpha101:alpha_070`；变换链：`[]`。

<a id="f-2d34ffa56e729cb5"></a>

## alpha101_071

- ID：`2d34ffa56e729cb5`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：low_coverage；历史均值 / 最差年 RankIC：-0.0058 / -0.0161。

登记表达式或插件说明：

```text
max(Ts_Rank(decay_linear(correlation(Ts_Rank(close, 3.43976), Ts_Rank(adv180,12.0647), 18.0175), 4.20501), 15.6948), Ts_Rank(decay_linear((rank(((low + open) - (vwap +vwap)))^2), 16.4662), 4.4388))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_071
```

- 插件：`alpha101:alpha_071`；变换链：`[]`。

<a id="f-0f6821f00b3c6d53"></a>

## alpha101_072

- ID：`0f6821f00b3c6d53`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0097 / 0.0016。

登记表达式或插件说明：

```text
(rank(decay_linear(correlation(((high + low) / 2), adv40, 8.93345), 10.1519)) /rank(decay_linear(correlation(Ts_Rank(vwap, 3.72469), Ts_Rank(volume, 18.5188), 6.86671),2.95011)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_072
```

- 插件：`alpha101:alpha_072`；变换链：`[]`。

<a id="f-553ea6d08c587818"></a>

## alpha101_073

- ID：`553ea6d08c587818`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0316 / 0.0209。

登记表达式或插件说明：

```text
(max(rank(decay_linear(delta(vwap, 4.72775), 2.91864)),Ts_Rank(decay_linear(((delta(((open * 0.147155) + (low * (1 - 0.147155))), 2.03608) / ((open *0.147155) + (low * (1 - 0.147155)))) * -1), 3.33829), 16.7411)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_073
```

- 插件：`alpha101:alpha_073`；变换链：`[]`。

<a id="f-1da7e76df3adbfea"></a>

## alpha101_074

- ID：`1da7e76df3adbfea`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0160 / 0.0124。

登记表达式或插件说明：

```text
((rank(correlation(close, sum(adv30, 37.4843), 15.1365)) <rank(correlation(rank(((high * 0.0261661) + (vwap * (1 - 0.0261661)))), rank(volume), 11.4791)))* -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_074
```

- 插件：`alpha101:alpha_074`；变换链：`[]`。

<a id="f-da63a38f06e8d4a1"></a>

## alpha101_075

- ID：`da63a38f06e8d4a1`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0130 / 0.0047。

登记表达式或插件说明：

```text
(rank(correlation(vwap, volume, 4.24304)) < rank(correlation(rank(low), rank(adv50),12.4413)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_075
```

- 插件：`alpha101:alpha_075`；变换链：`[]`。

<a id="f-9ed4af5ee5edc8b1"></a>

## alpha101_076

- ID：`9ed4af5ee5edc8b1`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(max(rank(decay_linear(delta(vwap, 1.24383), 11.8259)),Ts_Rank(decay_linear(Ts_Rank(correlation(IndNeutralize(low, IndClass.sector), adv81,8.14941), 19.569), 17.1543), 19.383)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_076
```

- 插件：`alpha101:alpha_076`；变换链：`[]`。

<a id="f-bc079c47b4ecfe92"></a>

## alpha101_077

- ID：`bc079c47b4ecfe92`；归属：active_396, research_597, pool_current。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0208 / 0.0091。

登记表达式或插件说明：

```text
min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20.0451)),rank(decay_linear(correlation(((high + low) / 2), adv40, 3.1614), 5.64125)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_077
```

- 插件：`alpha101:alpha_077`；变换链：`[]`。

<a id="f-a53d724274612fb1"></a>

## alpha101_078

- ID：`a53d724274612fb1`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0060 / -0.0081。

登记表达式或插件说明：

```text
(rank(correlation(sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 19.7428),sum(adv40, 19.7428), 6.83313))^rank(correlation(rank(vwap), rank(volume), 5.77492)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_078
```

- 插件：`alpha101:alpha_078`；变换链：`[]`。

<a id="f-74548d5fee2c69a6"></a>

## alpha101_079

- ID：`74548d5fee2c69a6`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(rank(delta(IndNeutralize(((close * 0.60733) + (open * (1 - 0.60733))),IndClass.sector), 1.23438)) < rank(correlation(Ts_Rank(vwap, 3.60973), Ts_Rank(adv150,9.18637), 14.6644)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_079
```

- 插件：`alpha101:alpha_079`；变换链：`[]`。

<a id="f-6073cadf1ffd4db9"></a>

## alpha101_080

- ID：`6073cadf1ffd4db9`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank(Sign(delta(IndNeutralize(((open * 0.868128) + (high * (1 - 0.868128))),IndClass.industry), 4.04545)))^Ts_Rank(correlation(high, adv10, 5.11456), 5.53756)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_080
```

- 插件：`alpha101:alpha_080`；变换链：`[]`。

<a id="f-b30ba8461bb69a95"></a>

## alpha101_081

- ID：`b30ba8461bb69a95`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0120 / 0.0041。

登记表达式或插件说明：

```text
((rank(Log(product(rank((rank(correlation(vwap, sum(adv10, 49.6054),8.47743))^4)), 14.9655))) < rank(correlation(rank(vwap), rank(volume), 5.07914))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_081
```

- 插件：`alpha101:alpha_081`；变换链：`[]`。

<a id="f-d8a4e7e5c3b8d566"></a>

## alpha101_082

- ID：`d8a4e7e5c3b8d566`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(min(rank(decay_linear(delta(open, 1.46063), 14.8717)),Ts_Rank(decay_linear(correlation(IndNeutralize(volume, IndClass.sector), ((open * 0.634196) +(open * (1 - 0.634196))), 17.4842), 6.92131), 13.4283)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_082
```

- 插件：`alpha101:alpha_082`；变换链：`[]`。

<a id="f-9963be99c79fd3b9"></a>

## alpha101_083

- ID：`9963be99c79fd3b9`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0171 / 0.0043。

登记表达式或插件说明：

```text
((rank(delay(((high - low) / (sum(close, 5) / 5)), 2)) * rank(rank(volume))) / (((high -low) / (sum(close, 5) / 5)) / (vwap - close)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_083
```

- 插件：`alpha101:alpha_083`；变换链：`[]`。

<a id="f-5f5549d80d68d0a3"></a>

## alpha101_084

- ID：`5f5549d80d68d0a3`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0270 / 0.0184。

登记表达式或插件说明：

```text
SignedPower(Ts_Rank((vwap - ts_max(vwap, 15.3217)), 20.7127), delta(close,4.96796))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_084
```

- 插件：`alpha101:alpha_084`；变换链：`[]`。

<a id="f-b7d6836880f607c0"></a>

## alpha101_085

- ID：`b7d6836880f607c0`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0036 / -0.0081。

登记表达式或插件说明：

```text
(rank(correlation(((high * 0.876703) + (close * (1 - 0.876703))), adv30,9.61331))^rank(correlation(Ts_Rank(((high + low) / 2), 3.70596), Ts_Rank(volume, 10.1595),7.11408)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_085
```

- 插件：`alpha101:alpha_085`；变换链：`[]`。

<a id="f-5936c13c3e05c433"></a>

## alpha101_086

- ID：`5936c13c3e05c433`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0005 / -0.0035。

登记表达式或插件说明：

```text
((Ts_Rank(correlation(close, sum(adv20, 14.7444), 6.00049), 20.4195) < rank(((open+ close) - (vwap + open)))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_086
```

- 插件：`alpha101:alpha_086`；变换链：`[]`。

<a id="f-7cc9d5d640e5bf1b"></a>

## alpha101_087

- ID：`7cc9d5d640e5bf1b`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(max(rank(decay_linear(delta(((close * 0.369701) + (vwap * (1 - 0.369701))),1.91233), 2.65461)), Ts_Rank(decay_linear(abs(correlation(IndNeutralize(adv81,IndClass.industry), close, 13.4132)), 4.89768), 14.4535)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_087
```

- 插件：`alpha101:alpha_087`；变换链：`[]`。

<a id="f-0007255e813c729e"></a>

## alpha101_088

- ID：`0007255e813c729e`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：low_coverage；历史均值 / 最差年 RankIC：0.0559 / 0.0365。

登记表达式或插件说明：

```text
min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))),8.06882)), Ts_Rank(decay_linear(correlation(Ts_Rank(close, 8.44728), Ts_Rank(adv60,20.6966), 8.01266), 6.65053), 2.61957))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_088
```

- 插件：`alpha101:alpha_088`；变换链：`[]`。

<a id="f-dd4e525b6a93632d"></a>

## alpha101_089

- ID：`dd4e525b6a93632d`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(Ts_Rank(decay_linear(correlation(((low * 0.967285) + (low * (1 - 0.967285))), adv10,6.94279), 5.51607), 3.79744) - Ts_Rank(decay_linear(delta(IndNeutralize(vwap,IndClass.industry), 3.48158), 10.1466), 15.3012))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_089
```

- 插件：`alpha101:alpha_089`；变换链：`[]`。

<a id="f-0322e1f14e1ac77d"></a>

## alpha101_090

- ID：`0322e1f14e1ac77d`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank((close - ts_max(close, 4.66719)))^Ts_Rank(correlation(IndNeutralize(adv40,IndClass.subindustry), low, 5.38375), 3.21856)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_090
```

- 插件：`alpha101:alpha_090`；变换链：`[]`。

<a id="f-4825c914cb068f5b"></a>

## alpha101_091

- ID：`4825c914cb068f5b`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((Ts_Rank(decay_linear(decay_linear(correlation(IndNeutralize(close,IndClass.industry), volume, 9.74928), 16.398), 3.83219), 4.8667) -rank(decay_linear(correlation(vwap, adv30, 4.01303), 2.6809))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_091
```

- 插件：`alpha101:alpha_091`；变换链：`[]`。

<a id="f-0948e72390ee6b84"></a>

## alpha101_092

- ID：`0948e72390ee6b84`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0053 / -0.0037。

登记表达式或插件说明：

```text
min(Ts_Rank(decay_linear(((((high + low) / 2) + close) < (low + open)), 14.7221),18.8683), Ts_Rank(decay_linear(correlation(rank(low), rank(adv30), 7.58555), 6.94024),6.80584))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_092
```

- 插件：`alpha101:alpha_092`；变换链：`[]`。

<a id="f-85f26bc1e6e6cdcc"></a>

## alpha101_093

- ID：`85f26bc1e6e6cdcc`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.industry), adv81,17.4193), 19.848), 7.54455) / rank(decay_linear(delta(((close * 0.524434) + (vwap * (1 -0.524434))), 2.77377), 16.2664)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_093
```

- 插件：`alpha101:alpha_093`；变换链：`[]`。

<a id="f-bd49d322fd4d62a0"></a>

## alpha101_094

- ID：`bd49d322fd4d62a0`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：low_coverage；历史均值 / 最差年 RankIC：0.0466 / 0.0160。

登记表达式或插件说明：

```text
((rank((vwap - ts_min(vwap, 11.5783)))^Ts_Rank(correlation(Ts_Rank(vwap,19.6462), Ts_Rank(adv60, 4.02992), 18.0926), 2.70756)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_094
```

- 插件：`alpha101:alpha_094`；变换链：`[]`。

<a id="f-e24b8213d0a3a1e2"></a>

## alpha101_095

- ID：`e24b8213d0a3a1e2`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0143 / 0.0015。

登记表达式或插件说明：

```text
(rank((open - ts_min(open, 12.4105))) < Ts_Rank((rank(correlation(sum(((high + low)/ 2), 19.1351), sum(adv40, 19.1351), 12.8742))^5), 11.7584))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_095
```

- 插件：`alpha101:alpha_095`；变换链：`[]`。

<a id="f-a4debdda5b937df1"></a>

## alpha101_096

- ID：`a4debdda5b937df1`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(max(Ts_Rank(decay_linear(correlation(rank(vwap), rank(volume), 3.83878),4.16783), 8.38151), Ts_Rank(decay_linear(Ts_ArgMax(correlation(Ts_Rank(close, 7.45404),Ts_Rank(adv60, 4.13242), 3.65459), 12.6556), 14.0365), 13.4143)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_096
```

- 插件：`alpha101:alpha_096`；变换链：`[]`。

<a id="f-825c584b4cc9401c"></a>

## alpha101_097

- ID：`825c584b4cc9401c`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((rank(decay_linear(delta(IndNeutralize(((low * 0.721001) + (vwap * (1 - 0.721001))),IndClass.industry), 3.3705), 20.4523)) - Ts_Rank(decay_linear(Ts_Rank(correlation(Ts_Rank(low,7.87871), Ts_Rank(adv60, 17.255), 4.97547), 18.5925), 15.7152), 6.71659)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_097
```

- 插件：`alpha101:alpha_097`；变换链：`[]`。

<a id="f-7f8cea0c1eb6ec6c"></a>

## alpha101_098

- ID：`7f8cea0c1eb6ec6c`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0121 / 0.0092。

登记表达式或插件说明：

```text
(rank(decay_linear(correlation(vwap, sum(adv5, 26.4719), 4.58418), 7.18088)) -rank(decay_linear(Ts_Rank(Ts_ArgMin(correlation(rank(open), rank(adv15), 20.8187), 8.62571),6.95668), 8.07206)))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_098
```

- 插件：`alpha101:alpha_098`；变换链：`[]`。

<a id="f-432229286e857169"></a>

## alpha101_099

- ID：`432229286e857169`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0079 / -0.0013。

登记表达式或插件说明：

```text
((rank(correlation(sum(((high + low) / 2), 19.8975), sum(adv60, 19.8975), 8.8136)) <rank(correlation(low, volume, 6.28259))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_099
```

- 插件：`alpha101:alpha_099`；变换链：`[]`。

<a id="f-d755972aa7cb5d9a"></a>

## alpha101_100

- ID：`d755972aa7cb5d9a`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
(0 - (1 * (((1.5 * scale(indneutralize(indneutralize(rank(((((close - low) - (high -close)) / (high - low)) * volume)), IndClass.subindustry), IndClass.subindustry))) -scale(indneutralize((correlation(close, rank(adv20), 5) - rank(ts_argmin(close, 30))),IndClass.subindustry))) * (volume / adv20))))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_100
```

- 插件：`alpha101:alpha_100`；变换链：`[]`。

<a id="f-18904e9b4de3423b"></a>

## alpha101_101

- ID：`18904e9b4de3423b`；归属：历史候选，未列入上述集合。
- 机制：alpha101（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0152 / 0.0085。

登记表达式或插件说明：

```text
((close - open) / ((high - low) + .001))
```

规范式 / 计算标识：

```text
plugin:alpha101:alpha_101
```

- 插件：`alpha101:alpha_101`；变换链：`[]`。
