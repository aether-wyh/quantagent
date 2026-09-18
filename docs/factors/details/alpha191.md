# Alpha191 插件

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-0a17b44ce2f4ade0"></a>

## alpha191_001

- ID：`0a17b44ce2f4ade0`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0217 / 0.0142。

登记表达式或插件说明：

```text
(-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_001
```

- 插件：`alpha191:alpha_001`；变换链：`[]`。

<a id="f-05fe246b31abb298"></a>

## alpha191_002

- ID：`05fe246b31abb298`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0062 / -0.0005。

登记表达式或插件说明：

```text
(-1 * DELTA((((CLOSE - LOW) - (HIGH - CLOSE)) / (HIGH - LOW)), 1))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_002
```

- 插件：`alpha191:alpha_002`；变换链：`[]`。

<a id="f-32edae4ba68fd20e"></a>

## alpha191_003

- ID：`32edae4ba68fd20e`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0322 / 0.0205。

登记表达式或插件说明：

```text
SUM((CLOSE==DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_003
```

- 插件：`alpha191:alpha_003`；变换链：`[]`。

<a id="f-71acebf3dfcf3e32"></a>

## alpha191_004

- ID：`71acebf3dfcf3e32`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0048 / -0.0110。

登记表达式或插件说明：

```text
((((SUM(CLOSE, 8) / 8) + STD(CLOSE, 8)) < (SUM(CLOSE, 2) / 2)) ? (-1 * 1) : (((SUM(CLOSE, 2) / 2) < ((SUM(CLOSE, 8) / 8) - STD(CLOSE, 8))) ? 1 : (((1 < (VOLUME / MEAN(VOLUME,20))) || ((VOLUME / MEAN(VOLUME,20)) == 1)) ? 1 : (-1 * 1))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_004
```

- 插件：`alpha191:alpha_004`；变换链：`[]`。

<a id="f-8116c08461fb6809"></a>

## alpha191_005

- ID：`8116c08461fb6809`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0316 / 0.0227。

登记表达式或插件说明：

```text
(-1 * TSMAX(CORR(TSRANK(VOLUME, 5), TSRANK(HIGH, 5), 5), 3))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_005
```

- 插件：`alpha191:alpha_005`；变换链：`[]`。

<a id="f-b34ae61dc08b5ba6"></a>

## alpha191_006

- ID：`b34ae61dc08b5ba6`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0171 / 0.0072。

登记表达式或插件说明：

```text
(RANK(SIGN(DELTA((((OPEN * 0.85) + (HIGH * 0.15))), 4)))* -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_006
```

- 插件：`alpha191:alpha_006`；变换链：`[]`。

<a id="f-bc28047971353e7c"></a>

## alpha191_007

- ID：`bc28047971353e7c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0144 / 0.0058。

登记表达式或插件说明：

```text
((RANK(MAX((VWAP - CLOSE), 3)) + RANK(MIN((VWAP - CLOSE), 3))) * RANK(DELTA(VOLUME, 3)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_007
```

- 插件：`alpha191:alpha_007`；变换链：`[]`。

<a id="f-642e09abf06f619a"></a>

## alpha191_008

- ID：`642e09abf06f619a`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0257 / 0.0099。

登记表达式或插件说明：

```text
RANK(DELTA(((((HIGH + LOW) / 2) * 0.2) + (VWAP * 0.8)), 4) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_008
```

- 插件：`alpha191:alpha_008`；变换链：`[]`。

<a id="f-e6d8ba0a8651d89c"></a>

## alpha191_009

- ID：`e6d8ba0a8651d89c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0247 / 0.0092。

登记表达式或插件说明：

```text
SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,7,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_009
```

- 插件：`alpha191:alpha_009`；变换链：`[]`。

<a id="f-fb77a288ce2e6ea2"></a>

## alpha191_010

- ID：`fb77a288ce2e6ea2`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0369 / 0.0019。

登记表达式或插件说明：

```text
RANK(TSMAX(((RET < 0) ? STD(RET, 20) : CLOSE)^2, 5))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_010
```

- 插件：`alpha191:alpha_010`；变换链：`[]`。

<a id="f-78a87eb753c8e421"></a>

## alpha191_011

- ID：`78a87eb753c8e421`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0096 / -0.0057。

登记表达式或插件说明：

```text
SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME,6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_011
```

- 插件：`alpha191:alpha_011`；变换链：`[]`。

<a id="f-189ac86ffc3359ea"></a>

## alpha191_012

- ID：`189ac86ffc3359ea`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0327 / 0.0197。

登记表达式或插件说明：

```text
(RANK((OPEN - (SUM(VWAP, 10) / 10)))) * (-1 * (RANK(ABS((CLOSE - VWAP)))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_012
```

- 插件：`alpha191:alpha_012`；变换链：`[]`。

<a id="f-48060431e91937ff"></a>

## alpha191_013

- ID：`48060431e91937ff`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0045 / -0.0088。

登记表达式或插件说明：

```text
(((HIGH * LOW)^0.5) - VWAP)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_013
```

- 插件：`alpha191:alpha_013`；变换链：`[]`。

<a id="f-0a1f8ee5c4242b03"></a>

## alpha191_014

- ID：`0a1f8ee5c4242b03`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0293 / 0.0124。

登记表达式或插件说明：

```text
CLOSE-DELAY(CLOSE,5)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_014
```

- 插件：`alpha191:alpha_014`；变换链：`[]`。

<a id="f-a905bf2ffc06f712"></a>

## alpha191_015

- ID：`a905bf2ffc06f712`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0158 / 0.0065。

登记表达式或插件说明：

```text
OPEN/DELAY(CLOSE,1)-1
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_015
```

- 插件：`alpha191:alpha_015`；变换链：`[]`。

<a id="f-863e4a2e01c9ef0a"></a>

## alpha191_016

- ID：`863e4a2e01c9ef0a`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0351 / 0.0241。

登记表达式或插件说明：

```text
(-1 * TSMAX(RANK(CORR(RANK(VOLUME), RANK(VWAP), 5)), 5))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_016
```

- 插件：`alpha191:alpha_016`；变换链：`[]`。

<a id="f-2137f7c4282243eb"></a>

## alpha191_017

- ID：`2137f7c4282243eb`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0228 / 0.0084。

登记表达式或插件说明：

```text
RANK((VWAP - MAX(VWAP, 15)))^DELTA(CLOSE, 5)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_017
```

- 插件：`alpha191:alpha_017`；变换链：`[]`。

<a id="f-37612a97909fd93f"></a>

## alpha191_018

- ID：`37612a97909fd93f`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0306 / 0.0176。

登记表达式或插件说明：

```text
CLOSE/DELAY(CLOSE,5)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_018
```

- 插件：`alpha191:alpha_018`；变换链：`[]`。

<a id="f-d89a52229344e86d"></a>

## alpha191_019

- ID：`d89a52229344e86d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0306 / 0.0176。

登记表达式或插件说明：

```text
(CLOSE<DELAY(CLOSE,5)?(CLOSE-DELAY(CLOSE,5))/DELAY(CLOSE,5):(CLOSE==DELAY(CLOSE,5)?0:(CLOSE-DELAY(CLOSE,5))/CLOSE))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_019
```

- 插件：`alpha191:alpha_019`；变换链：`[]`。

<a id="f-f6f28eeabcba3982"></a>

## alpha191_020

- ID：`f6f28eeabcba3982`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0343 / 0.0259。

登记表达式或插件说明：

```text
(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_020
```

- 插件：`alpha191:alpha_020`；变换链：`[]`。

<a id="f-f6f57df6ade5cc99"></a>

## alpha191_021

- ID：`f6f57df6ade5cc99`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0332 / 0.0185。

登记表达式或插件说明：

```text
REGBETA(MEAN(CLOSE,6),SEQUENCE,6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_021
```

- 插件：`alpha191:alpha_021`；变换链：`[]`。

<a id="f-77efc9968b44c4e3"></a>

## alpha191_022

- ID：`77efc9968b44c4e3`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0148 / -0.0012。

登记表达式或插件说明：

```text
SMA(((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)-DELAY((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6),3)),12,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_022
```

- 插件：`alpha191:alpha_022`；变换链：`[]`。

<a id="f-32313c3333cc055e"></a>

## alpha191_023

- ID：`32313c3333cc055e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0219 / 0.0120。

登记表达式或插件说明：

```text
SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)/(SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1 )+SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1))*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_023
```

- 插件：`alpha191:alpha_023`；变换链：`[]`。

<a id="f-0a4c0159b99fc9a7"></a>

## alpha191_024

- ID：`0a4c0159b99fc9a7`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0390 / 0.0238。

登记表达式或插件说明：

```text
SMA(CLOSE-DELAY(CLOSE,5),5,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_024
```

- 插件：`alpha191:alpha_024`；变换链：`[]`。

<a id="f-40c252eefd12951c"></a>

## alpha191_025

- ID：`40c252eefd12951c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0212 / 0.0078。

登记表达式或插件说明：

```text
((-1 * RANK((DELTA(CLOSE, 7) * (1 - RANK(DECAYLINEAR((VOLUME / MEAN(VOLUME,20)), 9)))))) * (1 + RANK(SUM(RET, 250))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_025
```

- 插件：`alpha191:alpha_025`；变换链：`[]`。

<a id="f-2bbe0846ef2ebb03"></a>

## alpha191_026

- ID：`2bbe0846ef2ebb03`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0244 / 0.0017。

登记表达式或插件说明：

```text
((((SUM(CLOSE, 7) / 7) - CLOSE)) + ((CORR(VWAP, DELAY(CLOSE, 5), 230))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_026
```

- 插件：`alpha191:alpha_026`；变换链：`[]`。

<a id="f-761fce7fe13a113e"></a>

## alpha191_027

- ID：`761fce7fe13a113e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0456 / 0.0292。

登记表达式或插件说明：

```text
WMA((CLOSE-DELAY(CLOSE,3))/DELAY(CLOSE,3)*100+(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100,12)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_027
```

- 插件：`alpha191:alpha_027`；变换链：`[]`。

<a id="f-c5d9e9d917320a2c"></a>

## alpha191_028

- ID：`c5d9e9d917320a2c`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0179 / -0.0013。

登记表达式或插件说明：

```text
3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOSE-TSMIN(LOW,9))/(MAX(HIGH,9)-TSMAX(LOW,9))*100,3,1),3,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_028
```

- 插件：`alpha191:alpha_028`；变换链：`[]`。

<a id="f-685db0e2f98cba01"></a>

## alpha191_029

- ID：`685db0e2f98cba01`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0318 / 0.0253。

登记表达式或插件说明：

```text
(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*VOLUME
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_029
```

- 插件：`alpha191:alpha_029`；变换链：`[]`。

<a id="f-2bb2d59aed101806"></a>

## alpha191_030

- ID：`2bb2d59aed101806`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
WMA((REGRESI(CLOSE/DELAY(CLOSE)-1,MKT,SMB,HML,60))^2,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_030
```

- 插件：`alpha191:alpha_030`；变换链：`[]`。

<a id="f-cb648aab51b116bc"></a>

## alpha191_031

- ID：`cb648aab51b116bc`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0379 / 0.0258。

登记表达式或插件说明：

```text
(CLOSE-MEAN(CLOSE,12))/MEAN(CLOSE,12)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_031
```

- 插件：`alpha191:alpha_031`；变换链：`[]`。

<a id="f-08243db54410fa21"></a>

## alpha191_032

- ID：`08243db54410fa21`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0301 / 0.0195。

登记表达式或插件说明：

```text
(-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_032
```

- 插件：`alpha191:alpha_032`；变换链：`[]`。

<a id="f-8eebfe2426bec45b"></a>

## alpha191_033

- ID：`8eebfe2426bec45b`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0274 / 0.0164。

登记表达式或插件说明：

```text
((((-1 * TSMIN(LOW, 5)) + DELAY(TSMIN(LOW, 5), 5)) * RANK(((SUM(RET, 240) - SUM(RET, 20)) / 220))) * TSRANK(VOLUME, 5))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_033
```

- 插件：`alpha191:alpha_033`；变换链：`[]`。

<a id="f-56e74e4c956f5599"></a>

## alpha191_034

- ID：`56e74e4c956f5599`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0379 / 0.0258。

登记表达式或插件说明：

```text
MEAN(CLOSE,12)/CLOSE
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_034
```

- 插件：`alpha191:alpha_034`；变换链：`[]`。

<a id="f-a1e057d438a3446d"></a>

## alpha191_035

- ID：`a1e057d438a3446d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0281 / 0.0089。

登记表达式或插件说明：

```text
(MIN(RANK(DECAYLINEAR(DELTA(OPEN, 1), 15)), RANK(DECAYLINEAR(CORR((VOLUME), ((OPEN * 0.65) + (OPEN *0.35)), 17),7))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_035
```

- 插件：`alpha191:alpha_035`；变换链：`[]`。

<a id="f-9cb0586d6ebfbf71"></a>

## alpha191_036

- ID：`9cb0586d6ebfbf71`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0358 / 0.0248。

登记表达式或插件说明：

```text
RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP), 6), 2))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_036
```

- 插件：`alpha191:alpha_036`；变换链：`[]`。

<a id="f-5296f99310d3736b"></a>

## alpha191_037

- ID：`5296f99310d3736b`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0163 / -0.0008。

登记表达式或插件说明：

```text
(-1 * RANK(((SUM(OPEN, 5) * SUM(RET, 5)) - DELAY((SUM(OPEN, 5) * SUM(RET, 5)), 10))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_037
```

- 插件：`alpha191:alpha_037`；变换链：`[]`。

<a id="f-a646e27c2756c1b6"></a>

## alpha191_038

- ID：`a646e27c2756c1b6`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0221 / 0.0148。

登记表达式或插件说明：

```text
(((SUM(HIGH, 20) / 20) < HIGH) ? (-1 * DELTA(HIGH, 2)) : 0)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_038
```

- 插件：`alpha191:alpha_038`；变换链：`[]`。

<a id="f-8a5405ad7cbe63d6"></a>

## alpha191_039

- ID：`8a5405ad7cbe63d6`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0114 / 0.0003。

登记表达式或插件说明：

```text
((RANK(DECAYLINEAR(DELTA((CLOSE), 2),8)) - RANK(DECAYLINEAR(CORR(((VWAP * 0.3) + (OPEN * 0.7)), SUM(MEAN(VOLUME,180), 37), 14), 12))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_039
```

- 插件：`alpha191:alpha_039`；变换链：`[]`。

<a id="f-fc37088b142898e0"></a>

## alpha191_040

- ID：`fc37088b142898e0`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0374 / 0.0231。

登记表达式或插件说明：

```text
SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:0),26)/SUM((CLOSE<=DELAY(CLOSE,1)?VOLUME:0),26)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_040
```

- 插件：`alpha191:alpha_040`；变换链：`[]`。

<a id="f-c6ce6e12b432f6b5"></a>

## alpha191_041

- ID：`c6ce6e12b432f6b5`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0563 / 0.0310。

登记表达式或插件说明：

```text
(RANK(MAX(DELTA((VWAP), 3), 5))* -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_041
```

- 插件：`alpha191:alpha_041`；变换链：`[]`。

<a id="f-7d786ea159b7da9d"></a>

## alpha191_042

- ID：`7d786ea159b7da9d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0685 / 0.0560。

登记表达式或插件说明：

```text
((-1 * RANK(STD(HIGH, 10))) * CORR(HIGH, VOLUME, 10))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_042
```

- 插件：`alpha191:alpha_042`；变换链：`[]`。

<a id="f-e845f7b3d26d6e91"></a>

## alpha191_043

- ID：`e845f7b3d26d6e91`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0252 / 0.0169。

登记表达式或插件说明：

```text
SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_043
```

- 插件：`alpha191:alpha_043`；变换链：`[]`。

<a id="f-d5a04b1ce51e3859"></a>

## alpha191_044

- ID：`d5a04b1ce51e3859`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0161 / 0.0098。

登记表达式或插件说明：

```text
(TSRANK(DECAYLINEAR(CORR(((LOW )), MEAN(VOLUME,10), 7), 6),4) + TSRANK(DECAYLINEAR(DELTA((VWAP), 3), 10), 15))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_044
```

- 插件：`alpha191:alpha_044`；变换链：`[]`。

<a id="f-f11a0bbe59b14f4e"></a>

## alpha191_045

- ID：`f11a0bbe59b14f4e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0152 / 0.0089。

登记表达式或插件说明：

```text
(RANK(DELTA((((CLOSE * 0.6) + (OPEN *0.4))), 1)) * RANK(CORR(VWAP, MEAN(VOLUME,150), 15)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_045
```

- 插件：`alpha191:alpha_045`；变换链：`[]`。

<a id="f-52ace4acb8b452e4"></a>

## alpha191_046

- ID：`52ace4acb8b452e4`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0416 / 0.0272。

登记表达式或插件说明：

```text
(MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/(4*CLOSE)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_046
```

- 插件：`alpha191:alpha_046`；变换链：`[]`。

<a id="f-9cd9ce9f0a733d83"></a>

## alpha191_047

- ID：`9cd9ce9f0a733d83`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0203 / -0.0066。

登记表达式或插件说明：

```text
SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_047
```

- 插件：`alpha191:alpha_047`；变换链：`[]`。

<a id="f-897173a9f49287a3"></a>

## alpha191_048

- ID：`897173a9f49287a3`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0241 / 0.0085。

登记表达式或插件说明：

```text
(-1*((RANK(((SIGN((CLOSE - DELAY(CLOSE, 1))) + SIGN((DELAY(CLOSE, 1) - DELAY(CLOSE, 2)))) + SIGN((DELAY(CLOSE, 2) - DELAY(CLOSE, 3)))))) * SUM(VOLUME, 5)) / SUM(VOLUME, 20))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_048
```

- 插件：`alpha191:alpha_048`；变换链：`[]`。

<a id="f-e4b68cc83dc71afd"></a>

## alpha191_049

- ID：`e4b68cc83dc71afd`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0370 / 0.0176。

登记表达式或插件说明：

```text
SUM(((HIGH+LOW)>=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12)/(SUM(((HIGH+LOW)>=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12)+SUM(((HIGH+LOW)<=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_049
```

- 插件：`alpha191:alpha_049`；变换链：`[]`。

<a id="f-86b119f305d29ec7"></a>

## alpha191_050

- ID：`86b119f305d29ec7`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0370 / 0.0176。

登记表达式或插件说明：

```text
SUM(((HIGH+LOW)<=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12)/(SUM(((HIGH+LOW)<=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12)+SUM(((HIGH+LOW)>=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12))-SUM(((HIGH+LOW)>=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DE
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_050
```

- 插件：`alpha191:alpha_050`；变换链：`[]`。

<a id="f-de378634f1746f31"></a>

## alpha191_051

- ID：`de378634f1746f31`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0370 / 0.0176。

登记表达式或插件说明：

```text
SUM(((HIGH+LOW)<=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12)/(SUM(((HIGH+LOW)<=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12)+SUM(((HIGH+LOW)>=(DELAY(HIGH,1)+DELAY(LOW,1))?0:MAX(ABS(HIGH-DELAY(HIGH,1)),ABS(LOW-DELAY(LOW,1)))),12))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_051
```

- 插件：`alpha191:alpha_051`；变换链：`[]`。

<a id="f-bb5f395621dacd27"></a>

## alpha191_052

- ID：`bb5f395621dacd27`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0490 / 0.0221。

登记表达式或插件说明：

```text
SUM(MAX(0,HIGH-DELAY((HIGH+LOW+CLOSE)/3,1)),26)/SUM(MAX(0,DELAY((HIGH+LOW+CLOSE)/3,1)-LOW),26)* 100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_052
```

- 插件：`alpha191:alpha_052`；变换链：`[]`。

<a id="f-758576022aee3ef5"></a>

## alpha191_053

- ID：`758576022aee3ef5`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0216 / 0.0088。

登记表达式或插件说明：

```text
COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_053
```

- 插件：`alpha191:alpha_053`；变换链：`[]`。

<a id="f-5935f3657e3ce1bf"></a>

## alpha191_054

- ID：`5935f3657e3ce1bf`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0345 / 0.0229。

登记表达式或插件说明：

```text
(-1 * RANK((STD(ABS(CLOSE - OPEN), 10) + (CLOSE - OPEN)) + CORR(CLOSE, OPEN, 10)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_054
```

- 插件：`alpha191:alpha_054`；变换链：`[]`。

<a id="f-9a6f7b5e6083cc31"></a>

## alpha191_055

- ID：`9a6f7b5e6083cc31`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0470 / 0.0305。

登记表达式或插件说明：

```text
SUM(16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))/((ABS(HIGH-DELAY(CLOSE,1))>ABS(LOW-DELAY(CLOSE,1)) && ABS(HIGH-DELAY(CLOSE,1))>ABS(HIGH-DELAY(LOW,1))?ABS(HIGH-DELAY(CLOSE,1))+ABS(LOW-DELAY(CLOSE,1))/2+ABS(DELAY(CLOSE,1)-DELAY(OPEN,1))/4:(ABS(LOW-DELAY(CLOSE,1))>ABS(HIGH-DELAY(LOW,1)) && ABS(LOW-DELAY(CLOSE,1))>ABS(HIGH-DELAY(CLOSE,1))?ABS(LOW-DELAY(CLOSE,1))+ABS(HIGH-DELA
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_055
```

- 插件：`alpha191:alpha_055`；变换链：`[]`。

<a id="f-6cb9f280b5bee80c"></a>

## alpha191_056

- ID：`6cb9f280b5bee80c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0234 / 0.0011。

登记表达式或插件说明：

```text
(RANK((OPEN - TSMIN(OPEN, 12))) < RANK((RANK(CORR(SUM(((HIGH + LOW) / 2), 19), SUM(MEAN(VOLUME,40), 19), 13))^5)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_056
```

- 插件：`alpha191:alpha_056`；变换链：`[]`。

<a id="f-a0790e8153dd39c6"></a>

## alpha191_057

- ID：`a0790e8153dd39c6`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0209 / -0.0019。

登记表达式或插件说明：

```text
SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_057
```

- 插件：`alpha191:alpha_057`；变换链：`[]`。

<a id="f-2c2202dde6010dee"></a>

## alpha191_058

- ID：`2c2202dde6010dee`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0230 / 0.0085。

登记表达式或插件说明：

```text
COUNT(CLOSE>DELAY(CLOSE,1),20)/20*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_058
```

- 插件：`alpha191:alpha_058`；变换链：`[]`。

<a id="f-1e1161b98906abfd"></a>

## alpha191_059

- ID：`1e1161b98906abfd`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0471 / 0.0307。

登记表达式或插件说明：

```text
SUM((CLOSE==DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_059
```

- 插件：`alpha191:alpha_059`；变换链：`[]`。

<a id="f-a02d6df3767280af"></a>

## alpha191_060

- ID：`a02d6df3767280af`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0173 / 0.0007。

登记表达式或插件说明：

```text
SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_060
```

- 插件：`alpha191:alpha_060`；变换链：`[]`。

<a id="f-a5b2b864d25522c3"></a>

## alpha191_061

- ID：`a5b2b864d25522c3`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0420 / 0.0285。

登记表达式或插件说明：

```text
(MAX(RANK(DECAYLINEAR(DELTA(VWAP, 1), 12)), RANK(DECAYLINEAR(RANK(CORR((LOW),MEAN(VOLUME,80), 8)), 17))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_061
```

- 插件：`alpha191:alpha_061`；变换链：`[]`。

<a id="f-8de14e55f0a3be1d"></a>

## alpha191_062

- ID：`8de14e55f0a3be1d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0381 / 0.0236。

登记表达式或插件说明：

```text
(-1 * CORR(HIGH, RANK(VOLUME), 5))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_062
```

- 插件：`alpha191:alpha_062`；变换链：`[]`。

<a id="f-8aa27aa2c0a1a9af"></a>

## alpha191_063

- ID：`8aa27aa2c0a1a9af`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0354 / 0.0169。

登记表达式或插件说明：

```text
SMA(MAX(CLOSE-DELAY(CLOSE,1),0),6,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),6,1)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_063
```

- 插件：`alpha191:alpha_063`；变换链：`[]`。

<a id="f-77552c583cf7ff5e"></a>

## alpha191_064

- ID：`77552c583cf7ff5e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0292 / 0.0229。

登记表达式或插件说明：

```text
(MAX(RANK(DECAYLINEAR(CORR(RANK(VWAP), RANK(VOLUME), 4), 4)), RANK(DECAYLINEAR(MAX(CORR(RANK(CLOSE), RANK(MEAN(VOLUME,60)), 4), 13), 14))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_064
```

- 插件：`alpha191:alpha_064`；变换链：`[]`。

<a id="f-9db242ba20c3f3a2"></a>

## alpha191_065

- ID：`9db242ba20c3f3a2`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0257 / 0.0122。

登记表达式或插件说明：

```text
MEAN(CLOSE,6)/CLOSE
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_065
```

- 插件：`alpha191:alpha_065`；变换链：`[]`。

<a id="f-200675c87792f489"></a>

## alpha191_066

- ID：`200675c87792f489`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0257 / 0.0122。

登记表达式或插件说明：

```text
(CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_066
```

- 插件：`alpha191:alpha_066`；变换链：`[]`。

<a id="f-966994e02d4017d5"></a>

## alpha191_067

- ID：`966994e02d4017d5`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0541 / 0.0273。

登记表达式或插件说明：

```text
SMA(MAX(CLOSE-DELAY(CLOSE,1),0),24,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),24,1)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_067
```

- 插件：`alpha191:alpha_067`；变换链：`[]`。

<a id="f-b3e78f63cb9d810b"></a>

## alpha191_068

- ID：`b3e78f63cb9d810b`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0324 / 0.0119。

登记表达式或插件说明：

```text
SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_068
```

- 插件：`alpha191:alpha_068`；变换链：`[]`。

<a id="f-4ea41754b23b105e"></a>

## alpha191_069

- ID：`4ea41754b23b105e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0449 / 0.0193。

登记表达式或插件说明：

```text
(SUM(DTM,20)>SUM(DBM,20) ? (SUM(DTM,20)-SUM(DBM,20))/SUM(DTM,20) : (SUM(DTM,20)==SUM(DBM,20) ? 0:(SUM(DTM,20)-SUM(DBM,20))/SUM(DBM,20)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_069
```

- 插件：`alpha191:alpha_069`；变换链：`[]`。

<a id="f-735a9503270b489e"></a>

## alpha191_070

- ID：`735a9503270b489e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0797 / 0.0554。

登记表达式或插件说明：

```text
STD(AMOUNT,6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_070
```

- 插件：`alpha191:alpha_070`；变换链：`[]`。

<a id="f-150cb08ddac5db9c"></a>

## alpha191_071

- ID：`150cb08ddac5db9c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0503 / 0.0324。

登记表达式或插件说明：

```text
(CLOSE-MEAN(CLOSE,24))/MEAN(CLOSE,24)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_071
```

- 插件：`alpha191:alpha_071`；变换链：`[]`。

<a id="f-578a2914dcc78baf"></a>

## alpha191_072

- ID：`578a2914dcc78baf`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0212 / -0.0076。

登记表达式或插件说明：

```text
SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,15,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_072
```

- 插件：`alpha191:alpha_072`；变换链：`[]`。

<a id="f-843d5385ad58f19e"></a>

## alpha191_073

- ID：`843d5385ad58f19e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0013 / -0.0084。

登记表达式或插件说明：

```text
((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE), VOLUME, 10), 16), 4), 5) - RANK(DECAYLINEAR(CORR(VWAP, MEAN(VOLUME,30), 4),3))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_073
```

- 插件：`alpha191:alpha_073`；变换链：`[]`。

<a id="f-124aaf4c128dafce"></a>

## alpha191_074

- ID：`124aaf4c128dafce`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0347 / 0.0249。

登记表达式或插件说明：

```text
(RANK(CORR(SUM(((LOW * 0.35) + (VWAP * 0.65)), 20), SUM(MEAN(VOLUME,40), 20), 7)) + RANK(CORR(RANK(VWAP), RANK(VOLUME), 6)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_074
```

- 插件：`alpha191:alpha_074`；变换链：`[]`。

<a id="f-aae3d75fe1821b53"></a>

## alpha191_075

- ID：`aae3d75fe1821b53`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0441 / 0.0263。

登记表达式或插件说明：

```text
COUNT(CLOSE>OPEN && BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)/COUNT(BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_075
```

- 插件：`alpha191:alpha_075`；变换链：`[]`。

<a id="f-2c10192bc34fe921"></a>

## alpha191_076

- ID：`2c10192bc34fe921`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0063 / -0.0305。

登记表达式或插件说明：

```text
STD(ABS((CLOSE/DELAY(CLOSE,1)-1))/VOLUME,20)/MEAN(ABS((CLOSE/DELAY(CLOSE,1)-1))/VOLUME,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_076
```

- 插件：`alpha191:alpha_076`；变换链：`[]`。

<a id="f-328447d58e5425ba"></a>

## alpha191_077

- ID：`328447d58e5425ba`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0203 / 0.0080。

登记表达式或插件说明：

```text
MIN(RANK(DECAYLINEAR(((((HIGH + LOW) / 2) + HIGH) - (VWAP + HIGH)), 20)), RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 3), 6)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_077
```

- 插件：`alpha191:alpha_077`；变换链：`[]`。

<a id="f-628826f09b19adfc"></a>

## alpha191_078

- ID：`628826f09b19adfc`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0333 / 0.0152。

登记表达式或插件说明：

```text
((HIGH+LOW+CLOSE)/3-MA((HIGH+LOW+CLOSE)/3,12))/(0.015*MEAN(ABS(CLOSE-MEAN((HIGH+LOW+CLOSE)/3,12)),12))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_078
```

- 插件：`alpha191:alpha_078`；变换链：`[]`。

<a id="f-be3d5fec546dc608"></a>

## alpha191_079

- ID：`be3d5fec546dc608`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0464 / 0.0231。

登记表达式或插件说明：

```text
SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_079
```

- 插件：`alpha191:alpha_079`；变换链：`[]`。

<a id="f-7555deda7a135195"></a>

## alpha191_080

- ID：`7555deda7a135195`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0180 / 0.0129。

登记表达式或插件说明：

```text
(VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_080
```

- 插件：`alpha191:alpha_080`；变换链：`[]`。

<a id="f-d868bc0aff5b6e63"></a>

## alpha191_081

- ID：`d868bc0aff5b6e63`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0421 / 0.0130。

登记表达式或插件说明：

```text
SMA(VOLUME,21,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_081
```

- 插件：`alpha191:alpha_081`；变换链：`[]`。

<a id="f-04ecacd7da6162f6"></a>

## alpha191_082

- ID：`04ecacd7da6162f6`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0208 / -0.0082。

登记表达式或插件说明：

```text
SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_082
```

- 插件：`alpha191:alpha_082`；变换链：`[]`。

<a id="f-a6e2e129222f7650"></a>

## alpha191_083

- ID：`a6e2e129222f7650`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0447 / 0.0281。

登记表达式或插件说明：

```text
(-1 * RANK(COV(RANK(HIGH), RANK(VOLUME), 5)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_083
```

- 插件：`alpha191:alpha_083`；变换链：`[]`。

<a id="f-402265e3d1b944a3"></a>

## alpha191_084

- ID：`402265e3d1b944a3`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0354 / 0.0159。

登记表达式或插件说明：

```text
SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_084
```

- 插件：`alpha191:alpha_084`；变换链：`[]`。

<a id="f-ac68d1b5ac19ff7d"></a>

## alpha191_085

- ID：`ac68d1b5ac19ff7d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0086 / -0.0135。

登记表达式或插件说明：

```text
(TSRANK((VOLUME / MEAN(VOLUME,20)), 20) * TSRANK((-1 * DELTA(CLOSE, 7)), 8))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_085
```

- 插件：`alpha191:alpha_085`；变换链：`[]`。

<a id="f-c7a1530a07182e7f"></a>

## alpha191_086

- ID：`c7a1530a07182e7f`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0266 / 0.0202。

登记表达式或插件说明：

```text
((0.25 < (((DELAY(CLOSE, 20) - DELAY(CLOSE, 10)) / 10) - ((DELAY(CLOSE, 10) - CLOSE) / 10))) ? (-1 * 1) : (((((DELAY(CLOSE, 20) - DELAY(CLOSE, 10)) / 10) - ((DELAY(CLOSE, 10) - CLOSE) / 10)) < 0) ? 1 : ((-1 * 1) * (CLOSE - DELAY(CLOSE, 1)))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_086
```

- 插件：`alpha191:alpha_086`；变换链：`[]`。

<a id="f-d235070a98eed456"></a>

## alpha191_087

- ID：`d235070a98eed456`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0212 / 0.0110。

登记表达式或插件说明：

```text
((RANK(DECAYLINEAR(DELTA(VWAP, 4), 7)) + TSRANK(DECAYLINEAR(((((LOW * 0.9) + (LOW * 0.1)) - VWAP) / (OPEN - ((HIGH + LOW) / 2))), 11), 7)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_087
```

- 插件：`alpha191:alpha_087`；变换链：`[]`。

<a id="f-3792b3c881bea460"></a>

## alpha191_088

- ID：`3792b3c881bea460`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0520 / 0.0313。

登记表达式或插件说明：

```text
(CLOSE-DELAY(CLOSE,20))/DELAY(CLOSE,20)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_088
```

- 插件：`alpha191:alpha_088`；变换链：`[]`。

<a id="f-143f44e3eb3813aa"></a>

## alpha191_089

- ID：`143f44e3eb3813aa`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0274 / 0.0064。

登记表达式或插件说明：

```text
2*(SMA(CLOSE,13,2)-SMA(CLOSE,27,2)-SMA(SMA(CLOSE,13,2)-SMA(CLOSE,27,2),10,2))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_089
```

- 插件：`alpha191:alpha_089`；变换链：`[]`。

<a id="f-7a26fd5cdc7eb75c"></a>

## alpha191_090

- ID：`7a26fd5cdc7eb75c`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0329 / 0.0223。

登记表达式或插件说明：

```text
(RANK(CORR(RANK(VWAP), RANK(VOLUME), 5)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_090
```

- 插件：`alpha191:alpha_090`；变换链：`[]`。

<a id="f-f489a633bc3a6863"></a>

## alpha191_091

- ID：`f489a633bc3a6863`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0005 / -0.0119。

登记表达式或插件说明：

```text
((RANK((CLOSE - MAX(CLOSE, 5)))*RANK(CORR((MEAN(VOLUME,40)), LOW, 5))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_091
```

- 插件：`alpha191:alpha_091`；变换链：`[]`。

<a id="f-8b6f1e8a247d38d8"></a>

## alpha191_092

- ID：`8b6f1e8a247d38d8`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0197 / 0.0164。

登记表达式或插件说明：

```text
(MAX(RANK(DECAYLINEAR(DELTA(((CLOSE * 0.35) + (VWAP *0.65)), 2), 3)), TSRANK(DECAYLINEAR(ABS(CORR((MEAN(VOLUME,180)), CLOSE, 13)), 5), 15)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_092
```

- 插件：`alpha191:alpha_092`；变换链：`[]`。

<a id="f-832dc07f9126ba4c"></a>

## alpha191_093

- ID：`832dc07f9126ba4c`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：unstable_years；历史均值 / 最差年 RankIC：0.0338 / -0.0069。

登记表达式或插件说明：

```text
SUM((OPEN>=DELAY(OPEN,1)?0:MAX((OPEN-LOW),(OPEN-DELAY(OPEN,1)))),20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_093
```

- 插件：`alpha191:alpha_093`；变换链：`[]`。

<a id="f-9139440997a29fd1"></a>

## alpha191_094

- ID：`9139440997a29fd1`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0389 / 0.0268。

登记表达式或插件说明：

```text
SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),30)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_094
```

- 插件：`alpha191:alpha_094`；变换链：`[]`。

<a id="f-91b0ec2ce1a48ca6"></a>

## alpha191_095

- ID：`91b0ec2ce1a48ca6`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0749 / 0.0517。

登记表达式或插件说明：

```text
STD(AMOUNT,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_095
```

- 插件：`alpha191:alpha_095`；变换链：`[]`。

<a id="f-c75aa0df9e97f3ec"></a>

## alpha191_096

- ID：`c75aa0df9e97f3ec`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0206 / -0.0036。

登记表达式或插件说明：

```text
SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1),3,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_096
```

- 插件：`alpha191:alpha_096`；变换链：`[]`。

<a id="f-a80f126f9b3519df"></a>

## alpha191_097

- ID：`a80f126f9b3519df`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0531 / 0.0281。

登记表达式或插件说明：

```text
STD(VOLUME,10)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_097
```

- 插件：`alpha191:alpha_097`；变换链：`[]`。

<a id="f-9271b8bee9f28746"></a>

## alpha191_098

- ID：`9271b8bee9f28746`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0276 / 0.0186。

登记表达式或插件说明：

```text
((((DELTA((SUM(CLOSE, 100) / 100), 100) / DELAY(CLOSE, 100)) < 0.05) || ((DELTA((SUM(CLOSE, 100) / 100), 100) / DELAY(CLOSE, 100)) == 0.05)) ? (-1 * (CLOSE - TSMIN(CLOSE, 100))) : (-1 * DELTA(CLOSE, 3)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_098
```

- 插件：`alpha191:alpha_098`；变换链：`[]`。

<a id="f-3de8f78056e61693"></a>

## alpha191_099

- ID：`3de8f78056e61693`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0441 / 0.0310。

登记表达式或插件说明：

```text
(-1 * RANK(COV(RANK(CLOSE), RANK(VOLUME), 5)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_099
```

- 插件：`alpha191:alpha_099`；变换链：`[]`。

<a id="f-4fd89514913729f3"></a>

## alpha191_100

- ID：`4fd89514913729f3`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0488 / 0.0221。

登记表达式或插件说明：

```text
STD(VOLUME,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_100
```

- 插件：`alpha191:alpha_100`；变换链：`[]`。

<a id="f-270397dab5b8a491"></a>

## alpha191_101

- ID：`270397dab5b8a491`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0153 / 0.0105。

登记表达式或插件说明：

```text
((RANK(CORR(CLOSE, SUM(MEAN(VOLUME,30), 37), 15)) < RANK(CORR(RANK(((HIGH * 0.1) + (VWAP * 0.9))), RANK(VOLUME), 11))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_101
```

- 插件：`alpha191:alpha_101`；变换链：`[]`。

<a id="f-7fea6a22144885e2"></a>

## alpha191_102

- ID：`7fea6a22144885e2`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0222 / 0.0111。

登记表达式或插件说明：

```text
SMA(MAX(VOLUME-DELAY(VOLUME,1),0),6,1)/SMA(ABS(VOLUME-DELAY(VOLUME,1)),6,1)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_102
```

- 插件：`alpha191:alpha_102`；变换链：`[]`。

<a id="f-6a503e396535a603"></a>

## alpha191_103

- ID：`6a503e396535a603`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0277 / 0.0154。

登记表达式或插件说明：

```text
((20-LOWDAY(LOW,20))/20)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_103
```

- 插件：`alpha191:alpha_103`；变换链：`[]`。

<a id="f-afd1e167728c696c"></a>

## alpha191_104

- ID：`afd1e167728c696c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0054 / -0.0016。

登记表达式或插件说明：

```text
(-1 * (DELTA(CORR(HIGH, VOLUME, 5), 5) * RANK(STD(CLOSE, 20))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_104
```

- 插件：`alpha191:alpha_104`；变换链：`[]`。

<a id="f-55af8d77de25bdb5"></a>

## alpha191_105

- ID：`55af8d77de25bdb5`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0289 / 0.0155。

登记表达式或插件说明：

```text
(-1 * CORR(RANK(OPEN), RANK(VOLUME), 10))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_105
```

- 插件：`alpha191:alpha_105`；变换链：`[]`。

<a id="f-3deafcc19043b44a"></a>

## alpha191_106

- ID：`3deafcc19043b44a`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0478 / 0.0247。

登记表达式或插件说明：

```text
CLOSE-DELAY(CLOSE,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_106
```

- 插件：`alpha191:alpha_106`；变换链：`[]`。

<a id="f-0abd6076b9d43039"></a>

## alpha191_107

- ID：`0abd6076b9d43039`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0208 / 0.0083。

登记表达式或插件说明：

```text
(((-1 * RANK((OPEN - DELAY(HIGH, 1)))) * RANK((OPEN - DELAY(CLOSE, 1)))) * RANK((OPEN - DELAY(LOW, 1))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_107
```

- 插件：`alpha191:alpha_107`；变换链：`[]`。

<a id="f-041355608b1a9896"></a>

## alpha191_108

- ID：`041355608b1a9896`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0189 / 0.0061。

登记表达式或插件说明：

```text
((RANK((HIGH - MIN(HIGH, 2)))^RANK(CORR((VWAP), (MEAN(VOLUME,120)), 6))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_108
```

- 插件：`alpha191:alpha_108`；变换链：`[]`。

<a id="f-41b6ee55ac499a05"></a>

## alpha191_109

- ID：`41b6ee55ac499a05`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0343 / 0.0168。

登记表达式或插件说明：

```text
SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_109
```

- 插件：`alpha191:alpha_109`；变换链：`[]`。

<a id="f-ba8a773c71f6b2c2"></a>

## alpha191_110

- ID：`ba8a773c71f6b2c2`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0422 / 0.0180。

登记表达式或插件说明：

```text
SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_110
```

- 插件：`alpha191:alpha_110`；变换链：`[]`。

<a id="f-df0b52c8f3352619"></a>

## alpha191_111

- ID：`df0b52c8f3352619`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0091 / -0.0094。

登记表达式或插件说明：

```text
SMA(VOLUME*((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW),11,2)-SMA(VOLUME*((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW),4,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_111
```

- 插件：`alpha191:alpha_111`；变换链：`[]`。

<a id="f-3ffa47c7d8928068"></a>

## alpha191_112

- ID：`3ffa47c7d8928068`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0362 / 0.0173。

登记表达式或插件说明：

```text
(SUM((CLOSE-DELAY(CLOSE,1)>0?CLOSE-DELAY(CLOSE,1):0),12)-SUM((CLOSE-DELAY(CLOSE,1)<0?ABS(CLOSE-DELAY(CLOSE,1)):0),12))/(SUM((CLOSE-DELAY(CLOSE,1)>0?CLOSE-DELAY(CLOSE,1):0),12)+SUM((CLOSE-DELAY(CLOSE,1)<0?ABS(CLOSE-DELAY(CLOSE,1)):0),12))*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_112
```

- 插件：`alpha191:alpha_112`；变换链：`[]`。

<a id="f-eee3f79d4e49e732"></a>

## alpha191_113

- ID：`eee3f79d4e49e732`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0209 / 0.0107。

登记表达式或插件说明：

```text
(-1 * ((RANK((SUM(DELAY(CLOSE, 5), 20) / 20)) * CORR(CLOSE, VOLUME, 2)) * RANK(CORR(SUM(CLOSE, 5), SUM(CLOSE, 20), 2))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_113
```

- 插件：`alpha191:alpha_113`；变换链：`[]`。

<a id="f-9258fb9a1b8f3208"></a>

## alpha191_114

- ID：`9258fb9a1b8f3208`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0171 / 0.0043。

登记表达式或插件说明：

```text
((RANK(DELAY(((HIGH - LOW) / (SUM(CLOSE, 5) / 5)), 2)) * RANK(RANK(VOLUME))) / (((HIGH - LOW) / (SUM(CLOSE, 5) / 5)) / (VWAP - CLOSE)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_114
```

- 插件：`alpha191:alpha_114`；变换链：`[]`。

<a id="f-a1616935ff214657"></a>

## alpha191_115

- ID：`a1616935ff214657`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0043 / -0.0102。

登记表达式或插件说明：

```text
(RANK(CORR(((HIGH * 0.9) + (CLOSE * 0.1)), MEAN(VOLUME,30), 10))^RANK(CORR(TSRANK(((HIGH + LOW) / 2), 4), TSRANK(VOLUME, 10), 7)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_115
```

- 插件：`alpha191:alpha_115`；变换链：`[]`。

<a id="f-53bae9a8aa3e5309"></a>

## alpha191_116

- ID：`53bae9a8aa3e5309`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0428 / 0.0229。

登记表达式或插件说明：

```text
REGBETA(CLOSE,SEQUENCE,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_116
```

- 插件：`alpha191:alpha_116`；变换链：`[]`。

<a id="f-4f2207a6a75954e0"></a>

## alpha191_117

- ID：`4f2207a6a75954e0`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0129 / 0.0066。

登记表达式或插件说明：

```text
((TSRANK(VOLUME, 32) * (1 - TSRANK(((CLOSE + HIGH) - LOW), 16))) * (1 - TSRANK(RET, 32)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_117
```

- 插件：`alpha191:alpha_117`；变换链：`[]`。

<a id="f-427c4e7e56342931"></a>

## alpha191_118

- ID：`427c4e7e56342931`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0513 / 0.0261。

登记表达式或插件说明：

```text
SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_118
```

- 插件：`alpha191:alpha_118`；变换链：`[]`。

<a id="f-0b5a2c11187da1a4"></a>

## alpha191_119

- ID：`0b5a2c11187da1a4`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0044 / -0.0145。

登记表达式或插件说明：

```text
(RANK(DECAYLINEAR(CORR(VWAP, SUM(MEAN(VOLUME,5), 26), 5), 7)) - RANK(DECAYLINEAR(TSRANK(MIN(CORR(RANK(OPEN), RANK(MEAN(VOLUME,15)), 21), 9), 7), 8)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_119
```

- 插件：`alpha191:alpha_119`；变换链：`[]`。

<a id="f-f0f5f3fc49ffcb1d"></a>

## alpha191_120

- ID：`f0f5f3fc49ffcb1d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0420 / 0.0194。

登记表达式或插件说明：

```text
(RANK((VWAP - CLOSE)) / RANK((VWAP + CLOSE)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_120
```

- 插件：`alpha191:alpha_120`；变换链：`[]`。

<a id="f-32f7061278e872c9"></a>

## alpha191_121

- ID：`32f7061278e872c9`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：low_coverage；历史均值 / 最差年 RankIC：0.0469 / 0.0171。

登记表达式或插件说明：

```text
((RANK((VWAP - MIN(VWAP, 12)))^TSRANK(CORR(TSRANK(VWAP, 20), TSRANK(MEAN(VOLUME,60), 2), 18), 3)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_121
```

- 插件：`alpha191:alpha_121`；变换链：`[]`。

<a id="f-abd7f18418270dee"></a>

## alpha191_122

- ID：`abd7f18418270dee`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0467 / 0.0257。

登记表达式或插件说明：

```text
(SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2)-DELAY(SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2),1))/DELAY(SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2),1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_122
```

- 插件：`alpha191:alpha_122`；变换链：`[]`。

<a id="f-7c6c9ca1cffba9c7"></a>

## alpha191_123

- ID：`7c6c9ca1cffba9c7`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0065 / -0.0021。

登记表达式或插件说明：

```text
((RANK(CORR(SUM(((HIGH + LOW) / 2), 20), SUM(MEAN(VOLUME,60), 20), 9)) < RANK(CORR(LOW, VOLUME, 6))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_123
```

- 插件：`alpha191:alpha_123`；变换链：`[]`。

<a id="f-118153cad3839e1b"></a>

## alpha191_124

- ID：`118153cad3839e1b`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0125 / -0.0013。

登记表达式或插件说明：

```text
(CLOSE - VWAP) / DECAYLINEAR(RANK(TSMAX(CLOSE, 30)),2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_124
```

- 插件：`alpha191:alpha_124`；变换链：`[]`。

<a id="f-cf27a8f85a589887"></a>

## alpha191_125

- ID：`cf27a8f85a589887`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0070 / -0.0088。

登记表达式或插件说明：

```text
(RANK(DECAYLINEAR(CORR((VWAP), MEAN(VOLUME,80),17), 20)) / RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 3), 16)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_125
```

- 插件：`alpha191:alpha_125`；变换链：`[]`。

<a id="f-b723c6d50289fb93"></a>

## alpha191_126

- ID：`b723c6d50289fb93`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0361 / -0.0002。

登记表达式或插件说明：

```text
(CLOSE+HIGH+LOW)/3
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_126
```

- 插件：`alpha191:alpha_126`；变换链：`[]`。

<a id="f-b9e182928e70cda4"></a>

## alpha191_127

- ID：`b9e182928e70cda4`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0152 / -0.0087。

登记表达式或插件说明：

```text
(MEAN((100*(CLOSE-TSMAX(CLOSE,12))/(TSMAX(CLOSE,12)))^2, 12))^(1/2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_127
```

- 插件：`alpha191:alpha_127`；变换链：`[]`。

<a id="f-24f302612a1dda06"></a>

## alpha191_128

- ID：`24f302612a1dda06`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0321 / 0.0148。

登记表达式或插件说明：

```text
100-(100/(1+SUM(((HIGH+LOW+CLOSE)/3>DELAY((HIGH+LOW+CLOSE)/3,1)?(HIGH+LOW+CLOSE)/3*VOLUME:0),14)/SUM(((HIGH+LOW+CLOSE)/3<DELAY((HIGH+LOW+CLOSE)/3,1)?(HIGH+LOW+CLOSE)/3*VOLUME:0), 14)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_128
```

- 插件：`alpha191:alpha_128`；变换链：`[]`。

<a id="f-5e356b3feb372a31"></a>

## alpha191_129

- ID：`5e356b3feb372a31`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0434 / 0.0085。

登记表达式或插件说明：

```text
SUM((CLOSE-DELAY(CLOSE,1)<0?ABS(CLOSE-DELAY(CLOSE,1)):0),12)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_129
```

- 插件：`alpha191:alpha_129`；变换链：`[]`。

<a id="f-eb2b6a401af8fe0b"></a>

## alpha191_130

- ID：`eb2b6a401af8fe0b`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0124 / 0.0042。

登记表达式或插件说明：

```text
(RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 9), 10)) / RANK(DECAYLINEAR(CORR(RANK(VWAP), RANK(VOLUME), 7),3)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_130
```

- 插件：`alpha191:alpha_130`；变换链：`[]`。

<a id="f-f41eb4d32a37d1b8"></a>

## alpha191_131

- ID：`f41eb4d32a37d1b8`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0109 / 0.0014。

登记表达式或插件说明：

```text
(RANK(DELTA(VWAP, 1))^TSRANK(CORR(CLOSE,MEAN(VOLUME,50), 18), 18))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_131
```

- 插件：`alpha191:alpha_131`；变换链：`[]`。

<a id="f-b55261e956a65356"></a>

## alpha191_132

- ID：`b55261e956a65356`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0647 / 0.0381。

登记表达式或插件说明：

```text
MEAN(AMOUNT,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_132
```

- 插件：`alpha191:alpha_132`；变换链：`[]`。

<a id="f-b376bb50f46a78d1"></a>

## alpha191_133

- ID：`b376bb50f46a78d1`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0361 / 0.0159。

登记表达式或插件说明：

```text
((20-HIGHDAY(HIGH,20))/20)*100-((20-LOWDAY(LOW,20))/20)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_133
```

- 插件：`alpha191:alpha_133`；变换链：`[]`。

<a id="f-1c078ae0157402cd"></a>

## alpha191_134

- ID：`1c078ae0157402cd`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0433 / 0.0238。

登记表达式或插件说明：

```text
(CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_134
```

- 插件：`alpha191:alpha_134`；变换链：`[]`。

<a id="f-f9999226777b4175"></a>

## alpha191_135

- ID：`f9999226777b4175`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0512 / 0.0247。

登记表达式或插件说明：

```text
SMA(DELAY(CLOSE/DELAY(CLOSE,20),1),20,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_135
```

- 插件：`alpha191:alpha_135`；变换链：`[]`。

<a id="f-1433b6303fd7b3a5"></a>

## alpha191_136

- ID：`1433b6303fd7b3a5`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0199 / 0.0076。

登记表达式或插件说明：

```text
((-1 * RANK(DELTA(RET, 3))) * CORR(OPEN, VOLUME, 10))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_136
```

- 插件：`alpha191:alpha_136`；变换链：`[]`。

<a id="f-198613255e17164c"></a>

## alpha191_137

- ID：`198613255e17164c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0237 / 0.0099。

登记表达式或插件说明：

```text
16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))/((ABS(HIGH-DELAY(CLOSE, 1))>ABS(LOW-DELAY(CLOSE,1)) && ABS(HIGH-DELAY(CLOSE,1))>ABS(HIGH-DELAY(LOW,1))?ABS(HIGH-DELAY(CLOSE,1))+ABS(LOW-DELAY(CLOSE,1))/2+ABS(DELAY(CLOSE,1)-DELAY(OPEN,1))/4:(ABS(LOW-DELAY(CLOSE,1))>ABS(HIGH-DELAY(LOW,1)) && ABS(LOW-DELAY(CLOSE,1))>ABS(HIGH-DELAY(CLOSE,1))?ABS(LOW-DELAY(CLOSE,1))+ABS(HIGH-DELAY(C
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_137
```

- 插件：`alpha191:alpha_137`；变换链：`[]`。

<a id="f-1d0ed3e206d4465f"></a>

## alpha191_138

- ID：`1d0ed3e206d4465f`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
((RANK(DECAYLINEAR(DELTA((((LOW * 0.7) + (VWAP *0.3))), 3), 20)) - TSRANK(DECAYLINEAR(TSRANK(CORR(TSRANK(LOW, 8), TSRANK(MEAN(VOLUME,60), 17), 5), 19), 16), 7)) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_138
```

- 插件：`alpha191:alpha_138`；变换链：`[]`。

<a id="f-716ef1b7426ca77c"></a>

## alpha191_139

- ID：`716ef1b7426ca77c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0277 / 0.0118。

登记表达式或插件说明：

```text
(-1 * CORR(OPEN, VOLUME, 10))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_139
```

- 插件：`alpha191:alpha_139`；变换链：`[]`。

<a id="f-25043b09782a8834"></a>

## alpha191_140

- ID：`25043b09782a8834`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：low_coverage；历史均值 / 最差年 RankIC：0.0547 / 0.0390。

登记表达式或插件说明：

```text
MIN(RANK(DECAYLINEAR(((RANK(OPEN) + RANK(LOW)) - (RANK(HIGH) + RANK(CLOSE))), 8)), TSRANK(DECAYLINEAR(CORR(TSRANK(CLOSE, 8), TSRANK(MEAN(VOLUME,60), 20), 8), 7), 3))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_140
```

- 插件：`alpha191:alpha_140`；变换链：`[]`。

<a id="f-b890706012c10f50"></a>

## alpha191_141

- ID：`b890706012c10f50`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0157 / 0.0091。

登记表达式或插件说明：

```text
(RANK(CORR(RANK(HIGH), RANK(MEAN(VOLUME,15)), 9))* -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_141
```

- 插件：`alpha191:alpha_141`；变换链：`[]`。

<a id="f-bc235d6aacf669c1"></a>

## alpha191_142

- ID：`bc235d6aacf669c1`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0045 / -0.0121。

登记表达式或插件说明：

```text
(((-1 * RANK(TSRANK(CLOSE, 10))) * RANK(DELTA(DELTA(CLOSE, 1), 1))) * RANK(TSRANK((VOLUME /MEAN(VOLUME,20)), 5)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_142
```

- 插件：`alpha191:alpha_142`；变换链：`[]`。

<a id="f-6c27f7906d2eeeca"></a>

## alpha191_143

- ID：`6c27f7906d2eeeca`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0719 / 0.0595。

登记表达式或插件说明：

```text
CLOSE>DELAY(CLOSE,1)?(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*SELF:SELF
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_143
```

- 插件：`alpha191:alpha_143`；变换链：`[]`。

<a id="f-3170157d75332acb"></a>

## alpha191_144

- ID：`3170157d75332acb`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0412 / 0.0211。

登记表达式或插件说明：

```text
SUMIF(ABS(CLOSE/DELAY(CLOSE,1)-1)/AMOUNT,20,CLOSE<DELAY(CLOSE,1))/COUNT(CLOSE<DELAY(CLOSE, 1),20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_144
```

- 插件：`alpha191:alpha_144`；变换链：`[]`。

<a id="f-dc5b333a9de848ff"></a>

## alpha191_145

- ID：`dc5b333a9de848ff`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0342 / 0.0006。

登记表达式或插件说明：

```text
(MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_145
```

- 插件：`alpha191:alpha_145`；变换链：`[]`。

<a id="f-bd435a8844a683a5"></a>

## alpha191_146

- ID：`bd435a8844a683a5`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0102 / -0.0006。

登记表达式或插件说明：

```text
MEAN((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)-SMA((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1),61,2),20)*(( CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)-SMA((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1),61,2))/SMA(((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)-((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)-SMA((CLOSE-DELAY(CLOSE, 1))/DELAY(CLOSE,1),61,2)))^2,60)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_146
```

- 插件：`alpha191:alpha_146`；变换链：`[]`。

<a id="f-ffd8b33093fc1e81"></a>

## alpha191_147

- ID：`ffd8b33093fc1e81`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0388 / 0.0186。

登记表达式或插件说明：

```text
REGBETA(MEAN(CLOSE,12),SEQUENCE,12)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_147
```

- 插件：`alpha191:alpha_147`；变换链：`[]`。

<a id="f-6c84a08eace365ba"></a>

## alpha191_148

- ID：`6c84a08eace365ba`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0221 / 0.0067。

登记表达式或插件说明：

```text
((RANK(CORR((OPEN), SUM(MEAN(VOLUME,60), 9), 6)) < RANK((OPEN - TSMIN(OPEN, 14)))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_148
```

- 插件：`alpha191:alpha_148`；变换链：`[]`。

<a id="f-e1bf2e4ca19531ba"></a>

## alpha191_149

- ID：`e1bf2e4ca19531ba`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
REGBETA(FILTER(CLOSE/DELAY(CLOSE,1)-1,BANCHMARKINDEXCLOSE<DELAY(BANCHMARKINDEXCLOSE,1) ),FILTER(BANCHMARKINDEXCLOSE/DELAY(BANCHMARKINDEXCLOSE,1)-1,BANCHMARKINDEXCLOSE<DELAY(BANCHMARKINDEXCLOSE,1)),252)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_149
```

- 插件：`alpha191:alpha_149`；变换链：`[]`。

<a id="f-59926a470a2698b3"></a>

## alpha191_150

- ID：`59926a470a2698b3`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0801 / 0.0579。

登记表达式或插件说明：

```text
(CLOSE+HIGH+LOW)/3*VOLUME
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_150
```

- 插件：`alpha191:alpha_150`；变换链：`[]`。

<a id="f-0bf14e54e9525b72"></a>

## alpha191_151

- ID：`0bf14e54e9525b72`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0445 / 0.0247。

登记表达式或插件说明：

```text
SMA(CLOSE-DELAY(CLOSE,20),20,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_151
```

- 插件：`alpha191:alpha_151`；变换链：`[]`。

<a id="f-9691d749c078743d"></a>

## alpha191_152

- ID：`9691d749c078743d`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0235 / 0.0065。

登记表达式或插件说明：

```text
SMA(MEAN(DELAY(SMA(DELAY(CLOSE/DELAY(CLOSE,9),1),9,1),1),12)-MEAN(DELAY(SMA(DELAY(CLOSE/DELAY (CLOSE,9),1),9,1),1),26),9,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_152
```

- 插件：`alpha191:alpha_152`；变换链：`[]`。

<a id="f-a4e3c019ab789eb0"></a>

## alpha191_153

- ID：`a4e3c019ab789eb0`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0336 / -0.0035。

登记表达式或插件说明：

```text
(MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/4
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_153
```

- 插件：`alpha191:alpha_153`；变换链：`[]`。

<a id="f-7d25aedf518d5181"></a>

## alpha191_154

- ID：`7d25aedf518d5181`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0264 / 0.0099。

登记表达式或插件说明：

```text
(((VWAP - MIN(VWAP, 16))) < (CORR(VWAP, MEAN(VOLUME,180), 18)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_154
```

- 插件：`alpha191:alpha_154`；变换链：`[]`。

<a id="f-2528b2bb6599febd"></a>

## alpha191_155

- ID：`2528b2bb6599febd`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0160 / -0.0035。

登记表达式或插件说明：

```text
SMA(VOLUME,13,2)-SMA(VOLUME,27,2)-SMA(SMA(VOLUME,13,2)-SMA(VOLUME,27,2),10,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_155
```

- 插件：`alpha191:alpha_155`；变换链：`[]`。

<a id="f-4876c84affce80e7"></a>

## alpha191_156

- ID：`4876c84affce80e7`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0512 / 0.0310。

登记表达式或插件说明：

```text
(MAX(RANK(DECAYLINEAR(DELTA(VWAP, 5), 3)), RANK(DECAYLINEAR(((DELTA(((OPEN * 0.15) + (LOW *0.85)), 2) / ((OPEN * 0.15) + (LOW * 0.85))) * -1), 3))) * -1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_156
```

- 插件：`alpha191:alpha_156`；变换链：`[]`。

<a id="f-4f265bd0499ecb03"></a>

## alpha191_157

- ID：`4f265bd0499ecb03`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0406 / 0.0222。

登记表达式或插件说明：

```text
(MIN(PROD(RANK(RANK(LOG(SUM(TSMIN(RANK(RANK((-1 * RANK(DELTA((CLOSE - 1), 5))))), 2), 1)))), 1), 5) + TSRANK(DELAY((-1 * RET), 6), 5))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_157
```

- 插件：`alpha191:alpha_157`；变换链：`[]`。

<a id="f-644f214a945e3488"></a>

## alpha191_158

- ID：`644f214a945e3488`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0685 / 0.0583。

登记表达式或插件说明：

```text
((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_158
```

- 插件：`alpha191:alpha_158`；变换链：`[]`。

<a id="f-aace28a41527d21a"></a>

## alpha191_159

- ID：`aace28a41527d21a`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0828 / 0.0689。

登记表达式或插件说明：

```text
((CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),6))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),6) *12*24+(CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),12))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),12)*6*24+(CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),24))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),24)*6*24)*100/(6*12+6*24+12*24)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_159
```

- 插件：`alpha191:alpha_159`；变换链：`[]`。

<a id="f-dff1acd3e61b2f0c"></a>

## alpha191_160

- ID：`dff1acd3e61b2f0c`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0405 / 0.0057。

登记表达式或插件说明：

```text
SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_160
```

- 插件：`alpha191:alpha_160`；变换链：`[]`。

<a id="f-842d4f7e88ca4bcf"></a>

## alpha191_161

- ID：`842d4f7e88ca4bcf`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0595 / 0.0246。

登记表达式或插件说明：

```text
MEAN(MAX(MAX((HIGH-LOW),ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),12)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_161
```

- 插件：`alpha191:alpha_161`；变换链：`[]`。

<a id="f-d51d005c33c7a1a2"></a>

## alpha191_162

- ID：`d51d005c33c7a1a2`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0095 / -0.0180。

登记表达式或插件说明：

```text
(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100-MIN(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100,12))/(MAX(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100,12)-MIN(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12, 1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100,12))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_162
```

- 插件：`alpha191:alpha_162`；变换链：`[]`。

<a id="f-e1d30d6cf3835b3e"></a>

## alpha191_163

- ID：`e1d30d6cf3835b3e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0062 / -0.0027。

登记表达式或插件说明：

```text
RANK(((((-1 * RET) * MEAN(VOLUME,20)) * VWAP) * (HIGH - CLOSE)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_163
```

- 插件：`alpha191:alpha_163`；变换链：`[]`。

<a id="f-0254801326b1155d"></a>

## alpha191_164

- ID：`0254801326b1155d`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0516 / 0.0191。

登记表达式或插件说明：

```text
SMA((((CLOSE>DELAY(CLOSE,1))?1/(CLOSE-DELAY(CLOSE,1)):1)-MIN(((CLOSE>DELAY(CLOSE,1))?1/(CLOSE-DELAY(CLOSE,1)):1),12))/(HIGH-LOW)*100,13,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_164
```

- 插件：`alpha191:alpha_164`；变换链：`[]`。

<a id="f-7448ac2b724cf682"></a>

## alpha191_165

- ID：`7448ac2b724cf682`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0183 / -0.0012。

登记表达式或插件说明：

```text
TSMAX(SUM(CLOSE-MEAN(CLOSE,48),48),48)-TSMIN(SUM(CLOSE-MEAN(CLOSE,48),48),48)/STD(CLOSE,48)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_165
```

- 插件：`alpha191:alpha_165`；变换链：`[]`。

<a id="f-5e537c5e1ec4b9fe"></a>

## alpha191_166

- ID：`5e537c5e1ec4b9fe`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0276 / 0.0002。

登记表达式或插件说明：

```text
-20* ( 20-1 ) ^1.5*SUM(CLOSE/DELAY(CLOSE,1)-1-MEAN(CLOSE/DELAY(CLOSE,1)-1,20),20)/((20-1)*(20-2)*(SUM(CLOSE/DELAY(CLOSE,1),20)^2))^1.5
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_166
```

- 插件：`alpha191:alpha_166`；变换链：`[]`。

<a id="f-c9d41da6b2de86cf"></a>

## alpha191_167

- ID：`c9d41da6b2de86cf`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0695 / 0.0344。

登记表达式或插件说明：

```text
SUM((CLOSE-DELAY(CLOSE,1)>0?CLOSE-DELAY(CLOSE,1):0),12)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_167
```

- 插件：`alpha191:alpha_167`；变换链：`[]`。

<a id="f-2277a289dce4c2fb"></a>

## alpha191_168

- ID：`2277a289dce4c2fb`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0284 / 0.0085。

登记表达式或插件说明：

```text
(-1*VOLUME/MEAN(VOLUME,20))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_168
```

- 插件：`alpha191:alpha_168`；变换链：`[]`。

<a id="f-859e183ad6397c8c"></a>

## alpha191_169

- ID：`859e183ad6397c8c`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0288 / 0.0057。

登记表达式或插件说明：

```text
SMA(MEAN(DELAY(SMA(CLOSE-DELAY(CLOSE,1),9,1),1),12)-MEAN(DELAY(SMA(CLOSE-DELAY(CLOSE,1),9,1),1), 26),10,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_169
```

- 插件：`alpha191:alpha_169`；变换链：`[]`。

<a id="f-2dd82f17481fba46"></a>

## alpha191_170

- ID：`2dd82f17481fba46`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0050 / -0.0086。

登记表达式或插件说明：

```text
((((RANK((1 / CLOSE)) * VOLUME) / MEAN(VOLUME,20)) * ((HIGH * RANK((HIGH - CLOSE))) / (SUM(HIGH, 5) / 5))) - RANK((VWAP - DELAY(VWAP, 5))))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_170
```

- 插件：`alpha191:alpha_170`；变换链：`[]`。

<a id="f-4f358218cc685323"></a>

## alpha191_171

- ID：`4f358218cc685323`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0000 / -0.0089。

登记表达式或插件说明：

```text
((-1 * ((LOW - CLOSE) * (OPEN^5))) / ((CLOSE - HIGH) * (CLOSE^5)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_171
```

- 插件：`alpha191:alpha_171`；变换链：`[]`。

<a id="f-8653732d175601fd"></a>

## alpha191_172

- ID：`8653732d175601fd`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0113 / -0.0243。

登记表达式或插件说明：

```text
MEAN(ABS(SUM((LD>0 && LD>HD)?LD:0,14)*100/SUM(TR,14)-SUM((HD>0 && HD>LD)?HD:0,14)*100/SUM(TR,14))/(SUM((LD>0 && LD>HD)?LD:0,14)*100/SUM(TR,14)+SUM((HD>0 && HD>LD)?HD:0,14)*100/SUM(TR,14))*100,6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_172
```

- 插件：`alpha191:alpha_172`；变换链：`[]`。

<a id="f-eb2e2522bf0dae72"></a>

## alpha191_173

- ID：`eb2e2522bf0dae72`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0366 / -0.0001。

登记表达式或插件说明：

```text
3*SMA(CLOSE,13,2)-2*SMA(SMA(CLOSE,13,2),13,2)+SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_173
```

- 插件：`alpha191:alpha_173`；变换链：`[]`。

<a id="f-2344ea5c5e1386ad"></a>

## alpha191_174

- ID：`2344ea5c5e1386ad`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0472 / 0.0141。

登记表达式或插件说明：

```text
SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_174
```

- 插件：`alpha191:alpha_174`；变换链：`[]`。

<a id="f-8029b5be531e2885"></a>

## alpha191_175

- ID：`8029b5be531e2885`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0635 / 0.0286。

登记表达式或插件说明：

```text
MEAN(MAX(MAX((HIGH-LOW),ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_175
```

- 插件：`alpha191:alpha_175`；变换链：`[]`。

<a id="f-33bc40675a87f907"></a>

## alpha191_176

- ID：`33bc40675a87f907`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0281 / 0.0216。

登记表达式或插件说明：

```text
CORR(RANK(((CLOSE - TSMIN(LOW, 12)) / (TSMAX(HIGH, 12) - TSMIN(LOW,12)))), RANK(VOLUME), 6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_176
```

- 插件：`alpha191:alpha_176`；变换链：`[]`。

<a id="f-de288ef5e855154a"></a>

## alpha191_177

- ID：`de288ef5e855154a`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0335 / 0.0134。

登记表达式或插件说明：

```text
((20-HIGHDAY(HIGH,20))/20)*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_177
```

- 插件：`alpha191:alpha_177`；变换链：`[]`。

<a id="f-3aa16b5eb868c79a"></a>

## alpha191_178

- ID：`3aa16b5eb868c79a`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0158 / 0.0055。

登记表达式或插件说明：

```text
(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_178
```

- 插件：`alpha191:alpha_178`；变换链：`[]`。

<a id="f-7e9ce9af2a050e38"></a>

## alpha191_179

- ID：`7e9ce9af2a050e38`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0289 / 0.0163。

登记表达式或插件说明：

```text
(RANK(CORR(VWAP, VOLUME, 4)) *RANK(CORR(RANK(LOW), RANK(MEAN(VOLUME,50)), 12)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_179
```

- 插件：`alpha191:alpha_179`；变换链：`[]`。

<a id="f-2b37da435f2ea69e"></a>

## alpha191_180

- ID：`2b37da435f2ea69e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0078 / -0.0035。

登记表达式或插件说明：

```text
((MEAN(VOLUME,20) < VOLUME) ? ((-1 * TSRANK(ABS(DELTA(CLOSE, 7)), 60)) * SIGN(DELTA(CLOSE, 7))) : (-1 * VOLUME))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_180
```

- 插件：`alpha191:alpha_180`；变换链：`[]`。

<a id="f-7808f72cd378b4f0"></a>

## alpha191_181

- ID：`7808f72cd378b4f0`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0045 / -0.0150。

登记表达式或插件说明：

```text
SUM(((CLOSE/DELAY(CLOSE,1)-1)-MEAN((CLOSE/DELAY(CLOSE,1)-1),20))-(BANCHMARKINDEXCLOSE-MEAN(BANCHMARKINDEXCLOSE,20))^2,20)/SUM((BANCHMARKINDEXCLOSE-MEAN(BANCHMARKINDEXCLOSE,20))^3,20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_181
```

- 插件：`alpha191:alpha_181`；变换链：`[]`。

<a id="f-18772950f5d30983"></a>

## alpha191_182

- ID：`18772950f5d30983`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0242 / 0.0139。

登记表达式或插件说明：

```text
COUNT((CLOSE>OPEN && BANCHMARKINDEXCLOSE>BANCHMARKINDEXOPEN) ||(CLOSE<OPEN && BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN),20)/20
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_182
```

- 插件：`alpha191:alpha_182`；变换链：`[]`。

<a id="f-f18e0208a367325b"></a>

## alpha191_183

- ID：`f18e0208a367325b`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0125 / -0.0021。

登记表达式或插件说明：

```text
TSMAX(SUM(CLOSE-MEAN(CLOSE,24),24),24)-TSMIN(SUM(CLOSE-MEAN(CLOSE,24),24),24)/STD(CLOSE,24)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_183
```

- 插件：`alpha191:alpha_183`；变换链：`[]`。

<a id="f-c3a563845cb52eae"></a>

## alpha191_184

- ID：`c3a563845cb52eae`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0211 / 0.0029。

登记表达式或插件说明：

```text
(RANK(CORR(DELAY((OPEN - CLOSE), 1), CLOSE, 200)) + RANK((OPEN - CLOSE)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_184
```

- 插件：`alpha191:alpha_184`；变换链：`[]`。

<a id="f-9a6c150c76a1a761"></a>

## alpha191_185

- ID：`9a6c150c76a1a761`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0378 / 0.0312。

登记表达式或插件说明：

```text
RANK((-1 * ((1 - (OPEN / CLOSE))^2)))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_185
```

- 插件：`alpha191:alpha_185`；变换链：`[]`。

<a id="f-39e64a239c001271"></a>

## alpha191_186

- ID：`39e64a239c001271`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0103 / -0.0230。

登记表达式或插件说明：

```text
(MEAN(ABS(SUM((LD>0 && LD>HD)?LD:0,14)*100/SUM(TR,14)-SUM((HD>0 && HD>LD)?HD:0,14)*100/SUM(TR,14))/(SUM((LD>0 && LD>HD)?LD:0,14)*100/SUM(TR,14)+SUM((HD>0 && HD>LD)?HD:0,14)*100/SUM(TR,14))*100,6)+DELAY(MEAN(ABS(SUM((LD>0 && LD>HD)?LD:0,14)*100/SUM(TR,14)-SUM((HD>0 && HD>LD)?HD:0,14)*100/SUM(TR,14))/(SUM((LD>0 && LD>HD)?LD:0,14)*100/SUM(TR,14)+SUM((HD>0 && HD>LD)?HD:0,14)*100/SUM(TR,14))*100,6),6))
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_186
```

- 插件：`alpha191:alpha_186`；变换链：`[]`。

<a id="f-4d35fee1b87a32c0"></a>

## alpha191_187

- ID：`4d35fee1b87a32c0`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0645 / 0.0251。

登记表达式或插件说明：

```text
SUM((OPEN<=DELAY(OPEN,1)?0:MAX((HIGH-OPEN),(OPEN-DELAY(OPEN,1)))),20)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_187
```

- 插件：`alpha191:alpha_187`；变换链：`[]`。

<a id="f-ce1f9d79bc39468e"></a>

## alpha191_188

- ID：`ce1f9d79bc39468e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0142 / 0.0095。

登记表达式或插件说明：

```text
((HIGH - LOW - SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2))*100
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_188
```

- 插件：`alpha191:alpha_188`；变换链：`[]`。

<a id="f-4b7ea0a7eabce035"></a>

## alpha191_189

- ID：`4b7ea0a7eabce035`；归属：active_396, research_597, pool_current。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0577 / 0.0274。

登记表达式或插件说明：

```text
MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_189
```

- 插件：`alpha191:alpha_189`；变换链：`[]`。

<a id="f-a45933591038e673"></a>

## alpha191_190

- ID：`a45933591038e673`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0734 / 0.0617。

登记表达式或插件说明：

```text
LOG((COUNT(CLOSE/DELAY(CLOSE,1)-1>((CLOSE/DELAY(CLOSE,19))^(1/20)-1),20)-1)*(SUMIF(((CLOSE/DELAY(CLOSE,1)-1-(CLOSE/DELAY(CLOSE,19))^(1/20)-1))^2,20,CLOSE/DELAY(CLOSE,1)-1<(CLOSE/DELAY(CLOSE,19))^(1/20)-1))/((COUNT((CLOSE/DELAY(CLOSE,1)-1<(CLOSE/DELAY(CLOSE,19))^(1/20)-1),20))*(SUMIF((CLOSE/DELAY(CLOSE,1)-1-((CLOSE/DELAY(CLOSE,19))^(1/20)-1))^2,20,CLOSE/DELAY(CLOSE,1)-1>(CLOSE/DELAY(CLOSE,19))^(1/2
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_190
```

- 插件：`alpha191:alpha_190`；变换链：`[]`。

<a id="f-369b2140f3aeff5e"></a>

## alpha191_191

- ID：`369b2140f3aeff5e`；归属：历史候选，未列入上述集合。
- 机制：alpha191（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0096 / 0.0019。

登记表达式或插件说明：

```text
((CORR(MEAN(VOLUME,20), LOW, 5) + ((HIGH + LOW) / 2)) - CLOSE)
```

规范式 / 计算标识：

```text
plugin:alpha191:alpha_191
```

- 插件：`alpha191:alpha_191`；变换链：`[]`。
