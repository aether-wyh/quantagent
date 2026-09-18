# 因子日历插件

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-f92f278fd0edea4d"></a>

## cal_additional_价差偏离度

- ID：`f92f278fd0edea4d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0217 / 0.0067。

登记表达式或插件说明：

```text
按250日相关性选择最多10只相似股票，使用标准化价格构造参考组合，再计算60日标准分。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:价差偏离度
```

- 插件：`calendar:additional:价差偏离度`；变换链：`[]`。

<a id="f-1b6c00ad5ce951c3"></a>

## cal_additional_价格时滞

- ID：`1b6c00ad5ce951c3`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0347 / 0.0230。

登记表达式或插件说明：

```text
按自然月回归当期及5阶滞后市场收益；无dates时每21日近似一个月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:价格时滞
```

- 插件：`calendar:additional:价格时滞`；变换链：`[]`。

<a id="f-f6fb509014aec999"></a>

## cal_additional_价量相关性因子 CPV

- ID：`f6fb509014aec999`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
均值和波动先剔除20日收益关系，再与趋势分项标准化相加。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:价量相关性因子 CPV
```

- 插件：`calendar:additional:价量相关性因子 CPV`；变换链：`[]`。

<a id="f-9aff87d75e98056c"></a>

## cal_additional_价量相关性波动性因子 PV_corr_std

- ID：`9aff87d75e98056c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
每日分钟价量相关系数的20日标准差；有市值字段时再剔除对数市值关系。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:价量相关性波动性因子 PV_corr_std
```

- 插件：`calendar:additional:价量相关性波动性因子 PV_corr_std`；变换链：`[]`。

<a id="f-720e0e7dbfdb3ef7"></a>

## cal_additional_价量相关性综合因子 PV_corr

- ID：`720e0e7dbfdb3ef7`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
20日均值和标准差逐日标准化后等权相加。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:价量相关性综合因子 PV_corr
```

- 插件：`calendar:additional:价量相关性综合因子 PV_corr`；变换链：`[]`。

<a id="f-02cf45c523f273b7"></a>

## cal_additional_价量相关性趋势因子 PV_corr_trend

- ID：`02cf45c523f273b7`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
每日分钟价量相关系数的20日时间斜率。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:价量相关性趋势因子 PV_corr_trend
```

- 插件：`calendar:additional:价量相关性趋势因子 PV_corr_trend`；变换链：`[]`。

<a id="f-b20c59d05c7a0272"></a>

## cal_additional_信噪比增强反转

- ID：`b20c59d05c7a0272`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
将每日信噪比做横截面0至1缩放后乘20日反转。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:信噪比增强反转
```

- 插件：`calendar:additional:信噪比增强反转`；变换链：`[]`。

<a id="f-8fc6125a577e0198"></a>

## cal_additional_区域指数 RI

- ID：`8fc6125a577e0198`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0031 / -0.0122。

登记表达式或插件说明：

```text
按原式N1=20、N2=5。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:区域指数 RI
```

- 插件：`calendar:additional:区域指数 RI`；变换链：`[]`。

<a id="f-9c6b56ce9e3d551d"></a>

## cal_additional_协偏度（朱剑涛版）

- ID：`9c6b56ce9e3d551d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0068 / -0.0146。

登记表达式或插件说明：

```text
20日窗口，至少15个有效收益。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:协偏度（朱剑涛版）
```

- 插件：`calendar:additional:协偏度（朱剑涛版）`；变换链：`[]`。

<a id="f-756d8a7dff12a3b3"></a>

## cal_additional_基于排序的动量

- ID：`756d8a7dff12a3b3`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0281 / 0.0074。

登记表达式或插件说明：

```text
每日横截面排名标准化；默认取跳过最近1个月的过去12个月均值。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:基于排序的动量
```

- 插件：`calendar:additional:基于排序的动量`；变换链：`[]`。

<a id="f-4fef8b2a896d33a3"></a>

## cal_additional_基于月度收益的市场 Beta

- ID：`4fef8b2a896d33a3`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0124 / 0.0011。

登记表达式或插件说明：

```text
传dates时使用真实月收益；无dates时每21日近似一个月。60月窗口、至少24月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:基于月度收益的市场 Beta
```

- 插件：`calendar:additional:基于月度收益的市场 Beta`；变换链：`[]`。

<a id="f-94bde4d3e21583cb"></a>

## cal_additional_市值调整换手率

- ID：`94bde4d3e21583cb`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0852 / 0.0737。

登记表达式或插件说明：

```text
逐日回归ln(换手率)对ln(流通市值)，取残差。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:市值调整换手率
```

- 插件：`calendar:additional:市值调整换手率`；变换链：`[]`。

<a id="f-ddc002fb3a1f2b20"></a>

## cal_additional_带条件的流动性冲击

- ID：`ddc002fb3a1f2b20`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0315 / 0.0019。

登记表达式或插件说明：

```text
用滚动60月AR(1)残差近似原文ARMA(1,1)，至少24月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:带条件的流动性冲击
```

- 插件：`calendar:additional:带条件的流动性冲击`；变换链：`[]`。

<a id="f-6decb2d45af8d280"></a>

## cal_additional_异常尾部概率 E

- ID：`6decb2d45af8d280`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0315 / 0.0240。

登记表达式或插件说明：

```text
63日二次市场模型特质收益标准化，k=1.5。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:异常尾部概率 E
```

- 插件：`calendar:additional:异常尾部概率 E`；变换链：`[]`。

<a id="f-3a5910dc24562477"></a>

## cal_additional_异常尾部概率 S

- ID：`3a5910dc24562477`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0198 / 0.0111。

登记表达式或插件说明：

```text
用左右尾直方分布的Hellinger距离近似原文高斯核积分。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:异常尾部概率 S
```

- 插件：`calendar:additional:异常尾部概率 S`；变换链：`[]`。

<a id="f-ebeaa375d790daec"></a>

## cal_additional_摇摆指数 SWI

- ID：`ebeaa375d790daec`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0361 / 0.0281。

登记表达式或插件说明：

```text
按扫描页分段公式逐项计算。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:摇摆指数 SWI
```

- 插件：`calendar:additional:摇摆指数 SWI`；变换链：`[]`。

<a id="f-03c2cf1683d6bdad"></a>

## cal_additional_收益季节性

- ID：`03c2cf1683d6bdad`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0050 / -0.0248。

登记表达式或插件说明：

```text
取去年同月超额收益；无dates时每21日近似一个月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:收益季节性
```

- 插件：`calendar:additional:收益季节性`；变换链：`[]`。

<a id="f-c23a182a7f8874d3"></a>

## cal_additional_收益季节性反转

- ID：`c23a182a7f8874d3`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0081 / -0.0037。

登记表达式或插件说明：

```text
取前1至11个月超额收益均值；无dates时每21日近似一个月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:收益季节性反转
```

- 插件：`calendar:additional:收益季节性反转`；变换链：`[]`。

<a id="f-0a897078996c4998"></a>

## cal_additional_时间序列动量 TSMOM

- ID：`0a897078996c4998`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0047 / -0.0106。

登记表达式或插件说明：

```text
自然月收益采用delta=0.9的指数均值和波动率；无dates时每21日近似一个月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:时间序列动量 TSMOM
```

- 插件：`calendar:additional:时间序列动量 TSMOM`；变换链：`[]`。

<a id="f-5cc81d1ba888281b"></a>

## cal_additional_流动性冲击 LIQU

- ID：`5cc81d1ba888281b`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0300 / 0.0143。

登记表达式或插件说明：

```text
当月Amihud相对过去12月均值的负变化；无dates时每21日近似一个月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:流动性冲击 LIQU
```

- 插件：`calendar:additional:流动性冲击 LIQU`；变换链：`[]`。

<a id="f-183d40585725ab8c"></a>

## cal_additional_资本收益过剩 CGO

- ID：`183d40585725ab8c`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0431 / 0.0127。

登记表达式或插件说明：

```text
复用现有日度CGO算法，采用100日持有存续权重；不是原文260周版本。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:资本收益过剩 CGO
```

- 插件：`calendar:additional:资本收益过剩 CGO`；变换链：`[]`。

<a id="f-e767df3d83db1cb7"></a>

## cal_additional_趋势动量

- ID：`e767df3d83db1cb7`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0397 / 0.0104。

登记表达式或插件说明：

```text
把原文11个时间尺度的信号等权平均；有换手率和流通股占比时再逐日剔除其一次关系。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:趋势动量
```

- 插件：`calendar:additional:趋势动量`；变换链：`[]`。

<a id="f-1bf8ed6029fbea33"></a>

## cal_additional_趋势因子

- ID：`1bf8ed6029fbea33`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0601 / 0.0322。

登记表达式或插件说明：

```text
保留原文多尺度均线/最新价信号并等权平均；未复现12个月因子收益预测回归。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:趋势因子
```

- 插件：`calendar:additional:趋势因子`；变换链：`[]`。

<a id="f-e2964fa844d24a5e"></a>

## cal_additional_非流动性因子 Gammar

- ID：`e2964fa844d24a5e`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0142 / -0.0019。

登记表达式或插件说明：

```text
按月回归下一日超额收益，取成交额项系数的负绝对值；无dates时每21日近似一个月。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:非流动性因子 Gammar
```

- 插件：`calendar:additional:非流动性因子 Gammar`；变换链：`[]`。

<a id="f-f73a0a6c56c7d0f2"></a>

## cal_additional_非线性市值

- ID：`f73a0a6c56c7d0f2`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0313 / 0.0095。

登记表达式或插件说明：

```text
按根号总市值加权回归；残差以3倍MAD去极值后逐日标准化。
```

规范式 / 计算标识：

```text
plugin:calendar:additional:非线性市值
```

- 插件：`calendar:additional:非线性市值`；变换链：`[]`。

<a id="f-1ca651648c2b12a1"></a>

## cal_risk_Amihud非流动性

- ID：`1ca651648c2b12a1`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0368 / 0.0160。

登记表达式或插件说明：

```text
calendar:risk:Amihud非流动性
```

规范式 / 计算标识：

```text
plugin:calendar:risk:Amihud非流动性
```

- 插件：`calendar:risk:Amihud非流动性`；变换链：`[]`。

<a id="f-a0e09cc470401df0"></a>

## cal_risk_Dimson贝塔

- ID：`a0e09cc470401df0`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
原文未统一给出回归窗口；默认252日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:Dimson贝塔
```

- 插件：`calendar:risk:Dimson贝塔`；变换链：`[]`。

<a id="f-74edba17b2be6788"></a>

## cal_risk_Frazzini-Pedersen贝塔

- ID：`74edba17b2be6788`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:Frazzini-Pedersen贝塔
```

规范式 / 计算标识：

```text
plugin:calendar:risk:Frazzini-Pedersen贝塔
```

- 插件：`calendar:risk:Frazzini-Pedersen贝塔`；变换链：`[]`。

<a id="f-1204bd2880e49aca"></a>

## cal_risk_SemiBeta正市场收益负资产收益

- ID：`1204bd2880e49aca`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:SemiBeta正市场收益负资产收益
```

规范式 / 计算标识：

```text
plugin:calendar:risk:SemiBeta正市场收益负资产收益
```

- 插件：`calendar:risk:SemiBeta正市场收益负资产收益`；变换链：`[]`。

<a id="f-09177d039010ee97"></a>

## cal_risk_SemiBeta负市场收益正资产收益

- ID：`09177d039010ee97`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:SemiBeta负市场收益正资产收益
```

规范式 / 计算标识：

```text
plugin:calendar:risk:SemiBeta负市场收益正资产收益
```

- 插件：`calendar:risk:SemiBeta负市场收益正资产收益`；变换链：`[]`。

<a id="f-6cb469049dae631a"></a>

## cal_risk_SemiBeta负市场收益负资产收益

- ID：`6cb469049dae631a`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:SemiBeta负市场收益负资产收益
```

规范式 / 计算标识：

```text
plugin:calendar:risk:SemiBeta负市场收益负资产收益
```

- 插件：`calendar:risk:SemiBeta负市场收益负资产收益`；变换链：`[]`。

<a id="f-e3f9357824ef476d"></a>

## cal_risk_上下行波动率DUVOL

- ID：`e3f9357824ef476d`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0404 / 0.0243。

登记表达式或插件说明：

```text
原文未统一给出窗口；默认252日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:上下行波动率DUVOL
```

- 插件：`calendar:risk:上下行波动率DUVOL`；变换链：`[]`。

<a id="f-c5bb029aa2048243"></a>

## cal_risk_下行贝塔

- ID：`c5bb029aa2048243`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0051 / -0.0068。

登记表达式或插件说明：

```text
calendar:risk:下行贝塔
```

规范式 / 计算标识：

```text
plugin:calendar:risk:下行贝塔
```

- 插件：`calendar:risk:下行贝塔`；变换链：`[]`。

<a id="f-5645827703c303e3"></a>

## cal_risk_价量相关性平均数

- ID：`5645827703c303e3`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:价量相关性平均数
```

规范式 / 计算标识：

```text
plugin:calendar:risk:价量相关性平均数
```

- 插件：`calendar:risk:价量相关性平均数`；变换链：`[]`。

<a id="f-c64346f8a309087d"></a>

## cal_risk_价量相关性波动性

- ID：`c64346f8a309087d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:价量相关性波动性
```

规范式 / 计算标识：

```text
plugin:calendar:risk:价量相关性波动性
```

- 插件：`calendar:risk:价量相关性波动性`；变换链：`[]`。

<a id="f-4a46ff39eb2fce8c"></a>

## cal_risk_价量相关性趋势

- ID：`4a46ff39eb2fce8c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:价量相关性趋势
```

规范式 / 计算标识：

```text
plugin:calendar:risk:价量相关性趋势
```

- 插件：`calendar:risk:价量相关性趋势`；变换链：`[]`。

<a id="f-8237bfbfbf557427"></a>

## cal_risk_价量相关性趋势行业中性

- ID：`8237bfbfbf557427`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格计算需要行业分类与完整中性化字段。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:价量相关性趋势行业中性
```

- 插件：`calendar:risk:价量相关性趋势行业中性`；变换链：`[]`。

<a id="f-af1d1f8638acef6e"></a>

## cal_risk_公告跳跃

- ID：`af1d1f8638acef6e`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格计算需要公告日期。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:公告跳跃
```

- 插件：`calendar:risk:公告跳跃`；变换链：`[]`。

<a id="f-3910d8de6c0145ab"></a>

## cal_risk_前K个月动量

- ID：`3910d8de6c0145ab`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0517 / 0.0315。

登记表达式或插件说明：

```text
K未固定；默认20个交易日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:前K个月动量
```

- 插件：`calendar:risk:前K个月动量`；变换链：`[]`。

<a id="f-3284a2712f929768"></a>

## cal_risk_协偏度

- ID：`3284a2712f929768`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:协偏度
```

规范式 / 计算标识：

```text
plugin:calendar:risk:协偏度
```

- 插件：`calendar:risk:协偏度`；变换链：`[]`。

<a id="f-7630d0cee324f825"></a>

## cal_risk_在险价值

- ID：`7630d0cee324f825`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0424 / 0.0280。

登记表达式或插件说明：

```text
原文未统一给出置信水平；默认左尾5%。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:在险价值
```

- 插件：`calendar:risk:在险价值`；变换链：`[]`。

<a id="f-de317a266edccf63"></a>

## cal_risk_基于月度收益的市场Beta

- ID：`de317a266edccf63`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格计算需要月收益矩阵或月份标记。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:基于月度收益的市场Beta
```

- 插件：`calendar:risk:基于月度收益的市场Beta`；变换链：`[]`。

<a id="f-c4335f5d648bad51"></a>

## cal_risk_尾部Beta

- ID：`c4335f5d648bad51`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:尾部Beta
```

规范式 / 计算标识：

```text
plugin:calendar:risk:尾部Beta
```

- 插件：`calendar:risk:尾部Beta`；变换链：`[]`。

<a id="f-9ed2c158cff083a5"></a>

## cal_risk_尾部风险

- ID：`9ed2c158cff083a5`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
目录公式先构造月度市场尾部风险；本模块没有月份标记，不能用日度左尾均值替代。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:尾部风险
```

- 插件：`calendar:risk:尾部风险`；变换链：`[]`。

<a id="f-3083e78c6666dc51"></a>

## cal_risk_市场Beta

- ID：`3083e78c6666dc51`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
calendar:risk:市场Beta
```

规范式 / 计算标识：

```text
plugin:calendar:risk:市场Beta
```

- 插件：`calendar:risk:市场Beta`；变换链：`[]`。

<a id="f-ba93cfc876d41078"></a>

## cal_risk_总偏度

- ID：`ba93cfc876d41078`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0313 / 0.0177。

登记表达式或插件说明：

```text
原文以K个月表示窗口；默认按252个交易日试算，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:总偏度
```

- 插件：`calendar:risk:总偏度`；变换链：`[]`。

<a id="f-1cdf082f5d1ed433"></a>

## cal_risk_总波动率

- ID：`1cdf082f5d1ed433`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0510 / 0.0368。

登记表达式或插件说明：

```text
原文以K个月表示窗口；默认按252个交易日试算，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:总波动率
```

- 插件：`calendar:risk:总波动率`；变换链：`[]`。

<a id="f-671b00d399e39ab5"></a>

## cal_risk_成交额波动

- ID：`671b00d399e39ab5`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0749 / 0.0517。

登记表达式或插件说明：

```text
K个月未固定；默认20个交易日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:成交额波动
```

- 插件：`calendar:risk:成交额波动`；变换链：`[]`。

<a id="f-69c16d39e2939800"></a>

## cal_risk_成交额波动系数

- ID：`69c16d39e2939800`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0466 / 0.0229。

登记表达式或插件说明：

```text
calendar:risk:成交额波动系数
```

规范式 / 计算标识：

```text
plugin:calendar:risk:成交额波动系数
```

- 插件：`calendar:risk:成交额波动系数`；变换链：`[]`。

<a id="f-6d9f8befec16850b"></a>

## cal_risk_换手波动

- ID：`6d9f8befec16850b`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0698 / 0.0599。

登记表达式或插件说明：

```text
K个月未固定；默认20个交易日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:换手波动
```

- 插件：`calendar:risk:换手波动`；变换链：`[]`。

<a id="f-2136c2983b0ed76d"></a>

## cal_risk_换手率

- ID：`2136c2983b0ed76d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0644 / 0.0573。

登记表达式或插件说明：

```text
K个月未固定；默认20个交易日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:换手率
```

- 插件：`calendar:risk:换手率`；变换链：`[]`。

<a id="f-e422c0e6ef05337b"></a>

## cal_risk_换手率变异系数

- ID：`e422c0e6ef05337b`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0396 / 0.0176。

登记表达式或插件说明：

```text
calendar:risk:换手率变异系数
```

规范式 / 计算标识：

```text
plugin:calendar:risk:换手率变异系数
```

- 插件：`calendar:risk:换手率变异系数`；变换链：`[]`。

<a id="f-881c8a190dbc8c4e"></a>

## cal_risk_最大收益率

- ID：`881c8a190dbc8c4e`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0719 / 0.0595。

登记表达式或插件说明：

```text
原文允许最高1日或最高n日均值；默认20日内最高1日。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:最大收益率
```

- 插件：`calendar:risk:最大收益率`；变换链：`[]`。

<a id="f-e8b601e67e5194f2"></a>

## cal_risk_月均换手率

- ID：`e8b601e67e5194f2`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格月均值需要月份标记，不能固定用20日代替自然月。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:月均换手率
```

- 插件：`calendar:risk:月均换手率`；变换链：`[]`。

<a id="f-c311294d8ba8d03a"></a>

## cal_risk_月度异常换手率

- ID：`c311294d8ba8d03a`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0563 / 0.0421。

登记表达式或插件说明：

```text
calendar:risk:月度异常换手率
```

规范式 / 计算标识：

```text
plugin:calendar:risk:月度异常换手率
```

- 插件：`calendar:risk:月度异常换手率`；变换链：`[]`。

<a id="f-04e8ce9e11bb170b"></a>

## cal_risk_月度特质波动率

- ID：`04e8ce9e11bb170b`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格计算需要FF3的MKT、SMB、HML及月度分组。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:月度特质波动率
```

- 插件：`calendar:risk:月度特质波动率`；变换链：`[]`。

<a id="f-203fbb0e60a02b34"></a>

## cal_risk_极端下行风险

- ID：`203fbb0e60a02b34`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
三年目录定义不一致，2024版本还严格依赖FF3残差。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:极端下行风险
```

- 插件：`calendar:risk:极端下行风险`；变换链：`[]`。

<a id="f-a0fdfa6e00148ed8"></a>

## cal_risk_流动性冲击

- ID：`a0fdfa6e00148ed8`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格公式使用当月Amihud及过去12个自然月，需要月份标记。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:流动性冲击
```

- 插件：`calendar:risk:流动性冲击`；变换链：`[]`。

<a id="f-276cd0115d5170ca"></a>

## cal_risk_特质偏度

- ID：`276cd0115d5170ca`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
目录定义可能依赖FF3；不能静默改为CAPM。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:特质偏度
```

- 插件：`calendar:risk:特质偏度`；变换链：`[]`。

<a id="f-dba52b73077deaf2"></a>

## cal_risk_特质波动率

- ID：`dba52b73077deaf2`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
目录定义可能依赖FF3；不能把CAPM版本冒充为同一公式。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:特质波动率
```

- 插件：`calendar:risk:特质波动率`；变换链：`[]`。

<a id="f-aa5a4477663010ad"></a>

## cal_risk_负偏度系数NCSKEW

- ID：`aa5a4477663010ad`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0313 / 0.0177。

登记表达式或插件说明：

```text
原文未统一给出n；默认252日，可显式传window。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:负偏度系数NCSKEW
```

- 插件：`calendar:risk:负偏度系数NCSKEW`；变换链：`[]`。

<a id="f-e8cf7d531fb123cf"></a>

## cal_risk_负收益非流动性

- ID：`e8cf7d531fb123cf`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0412 / 0.0211。

登记表达式或插件说明：

```text
calendar:risk:负收益非流动性
```

规范式 / 计算标识：

```text
plugin:calendar:risk:负收益非流动性
```

- 插件：`calendar:risk:负收益非流动性`；变换链：`[]`。

<a id="f-b863f64ba133f2ca"></a>

## cal_risk_非流动性的变异系数

- ID：`b863f64ba133f2ca`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0066 / -0.0289。

登记表达式或插件说明：

```text
calendar:risk:非流动性的变异系数
```

规范式 / 计算标识：

```text
plugin:calendar:risk:非流动性的变异系数
```

- 插件：`calendar:risk:非流动性的变异系数`；变换链：`[]`。

<a id="f-209da9c7a8db4bae"></a>

## cal_risk_非线性高频波动率

- ID：`209da9c7a8db4bae`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格计算需要多因子回归得到的特异率。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:非线性高频波动率
```

- 插件：`calendar:risk:非线性高频波动率`；变换链：`[]`。

<a id="f-4eccc7d4eedff83c"></a>

## cal_risk_高频特异波动率

- ID：`4eccc7d4eedff83c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`未知`；评价状态：`error`。
- 原假设：external library factor
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
严格计算需要市场、规模、价值、反转和流动性因子。
```

规范式 / 计算标识：

```text
plugin:calendar:risk:高频特异波动率
```

- 插件：`calendar:risk:高频特异波动率`；变换链：`[]`。

<a id="f-3aa4b75a9f230a93"></a>

## cal_standard_Amihud 非流动性因子

- ID：`3aa4b75a9f230a93`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0368 / 0.0160。

登记表达式或插件说明：

```text
按原文取近 20 日 abs(日收益)/成交额均值。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:Amihud 非流动性因子
```

- 插件：`calendar:standard:Amihud 非流动性因子`；变换链：`[]`。

<a id="f-f3e23adb931e4bde"></a>

## cal_standard_Q 棒指标 QST

- ID：`f3e23adb931e4bde`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0531 / 0.0287。

登记表达式或插件说明：

```text
N 未定；按 N=20 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:Q 棒指标 QST
```

- 插件：`calendar:standard:Q 棒指标 QST`；变换链：`[]`。

<a id="f-41a9372dd0ea7770"></a>

## cal_standard_三角移动均线 TMA

- ID：`41a9372dd0ea7770`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0312 / -0.0067。

登记表达式或插件说明：

```text
N 未定；按 N=20，先 10 日再 11 日均线试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:三角移动均线 TMA
```

- 插件：`calendar:standard:三角移动均线 TMA`；变换链：`[]`。

<a id="f-3b15043cb34c71df"></a>

## cal_standard_三重指数移动平均指标 TEMA

- ID：`3b15043cb34c71df`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0355 / -0.0009。

登记表达式或插件说明：

```text
N 未定；按 N=20 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:三重指数移动平均指标 TEMA
```

- 插件：`calendar:standard:三重指数移动平均指标 TEMA`；变换链：`[]`。

<a id="f-14e7ad8fa0744734"></a>

## cal_standard_乖离率 BIAS

- ID：`14e7ad8fa0744734`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0474 / 0.0314。

登记表达式或插件说明：

```text
N 未定；按 N=20 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:乖离率 BIAS
```

- 插件：`calendar:standard:乖离率 BIAS`；变换链：`[]`。

<a id="f-f317ed1269004d3a"></a>

## cal_standard_买卖意愿指标 BR

- ID：`f317ed1269004d3a`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0452 / 0.0256。

登记表达式或插件说明：

```text
N 未定；按常用 N=26 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:买卖意愿指标 BR
```

- 插件：`calendar:standard:买卖意愿指标 BR`；变换链：`[]`。

<a id="f-bfb593d2b760feec"></a>

## cal_standard_人气指数 AR

- ID：`bfb593d2b760feec`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0541 / 0.0275。

登记表达式或插件说明：

```text
N 未定；按常用 N=26 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:人气指数 AR
```

- 插件：`calendar:standard:人气指数 AR`；变换链：`[]`。

<a id="f-d120b479efb10c08"></a>

## cal_standard_价量趋势指标 PVT

- ID：`d120b479efb10c08`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0085 / -0.0189。

登记表达式或插件说明：

```text
按原式累计收益率×成交量。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:价量趋势指标 PVT
```

- 插件：`calendar:standard:价量趋势指标 PVT`；变换链：`[]`。

<a id="f-2fbd71b330bdf327"></a>

## cal_standard_优瑟指数 UI

- ID：`2fbd71b330bdf327`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0130 / -0.0092。

登记表达式或插件说明：

```text
N 未定；按 N=14 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:优瑟指数 UI
```

- 插件：`calendar:standard:优瑟指数 UI`；变换链：`[]`。

<a id="f-31ed1e06bdd2711c"></a>

## cal_standard_估波指标 Coppock

- ID：`31ed1e06bdd2711c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：low_coverage；历史均值 / 最差年 RankIC：-0.0121 / -0.0288。

登记表达式或插件说明：

```text
原文窗口未定；按常用 ROC 11、14 月与 10 期加权均线试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:估波指标 Coppock
```

- 插件：`calendar:standard:估波指标 Coppock`；变换链：`[]`。

<a id="f-af05fb56801d4443"></a>

## cal_standard_佳庆指标 CHO

- ID：`af05fb56801d4443`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0123 / 0.0017。

登记表达式或插件说明：

```text
N1、N2 未定；按常用 3、10 日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:佳庆指标 CHO
```

- 插件：`calendar:standard:佳庆指标 CHO`；变换链：`[]`。

<a id="f-28b755dacdb7d939"></a>

## cal_standard_佳庆离散指标 CV

- ID：`28b755dacdb7d939`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0447 / 0.0297。

登记表达式或插件说明：

```text
按总表默认 N=20，比较 20 日前值。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:佳庆离散指标 CV
```

- 插件：`calendar:standard:佳庆离散指标 CV`；变换链：`[]`。

<a id="f-56fb52a484d6ea5c"></a>

## cal_standard_信息离散度 ID

- ID：`56fb52a484d6ea5c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0082 / -0.0156。

登记表达式或插件说明：

```text
按原文用过去 12 月、跳过最近 1 月；交易日近似为 252 日和 21 日。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:信息离散度 ID
```

- 插件：`calendar:standard:信息离散度 ID`；变换链：`[]`。

<a id="f-8d48d752e2f9c05c"></a>

## cal_standard_克林格成交量摆动指标 KVO

- ID：`8d48d752e2f9c05c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0218 / 0.0051。

登记表达式或插件说明：

```text
按总表重复页明确给出的 34、55 日 EMA 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:克林格成交量摆动指标 KVO
```

- 插件：`calendar:standard:克林格成交量摆动指标 KVO`；变换链：`[]`。

<a id="f-b5012a0ee258a0c3"></a>

## cal_standard_前 K 个月动量

- ID：`b5012a0ee258a0c3`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0437 / 0.0122。

登记表达式或插件说明：

```text
K 未定；按 6 个月、126 个交易日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:前 K 个月动量
```

- 插件：`calendar:standard:前 K 个月动量`；变换链：`[]`。

<a id="f-f61be5d61f4e7928"></a>

## cal_standard_加速度动量

- ID：`f61be5d61f4e7928`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0182 / 0.0081。

登记表达式或插件说明：

```text
n 未定；按 20 日二次回归的 t² 系数试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:加速度动量
```

- 插件：`calendar:standard:加速度动量`；变换链：`[]`。

<a id="f-1261ec89d1569490"></a>

## cal_standard_动态买卖气指标 ADTM

- ID：`1261ec89d1569490`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0487 / 0.0257。

登记表达式或插件说明：

```text
原文窗口未定；按常用 N=23 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:动态买卖气指标 ADTM
```

- 插件：`calendar:standard:动态买卖气指标 ADTM`；变换链：`[]`。

<a id="f-f64194cbc869bbf9"></a>

## cal_standard_动态动量指标 DMI

- ID：`f64194cbc869bbf9`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0256 / 0.0131。

登记表达式或插件说明：

```text
原文 N1、N2 未定；均按 20 日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:动态动量指标 DMI
```

- 插件：`calendar:standard:动态动量指标 DMI`；变换链：`[]`。

<a id="f-8395e7a07bd0f9bd"></a>

## cal_standard_动量加速度

- ID：`8395e7a07bd0f9bd`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0410 / 0.0099。

登记表达式或插件说明：

```text
按总表将后 6 个月累计收益减前 6 个月累计收益，半年按 126 日。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:动量加速度
```

- 插件：`calendar:standard:动量加速度`；变换链：`[]`。

<a id="f-af433aac4684648b"></a>

## cal_standard_动量指标 MTM

- ID：`af433aac4684648b`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0441 / 0.0295。

登记表达式或插件说明：

```text
N 未定；按常用 N=12 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:动量指标 MTM
```

- 插件：`calendar:standard:动量指标 MTM`；变换链：`[]`。

<a id="f-0e4483c2256e7497"></a>

## cal_standard_反向日内逆转的频率

- ID：`0e4483c2256e7497`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0286 / 0.0174。

登记表达式或插件说明：

```text
月度按 20 个交易日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:反向日内逆转的频率
```

- 插件：`calendar:standard:反向日内逆转的频率`；变换链：`[]`。

<a id="f-12b07416874576be"></a>

## cal_standard_变动速率 ROC

- ID：`12b07416874576be`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0430 / 0.0255。

登记表达式或插件说明：

```text
按常用 N=12、M=6，输出 ROC 的 6 日均值。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:变动速率 ROC
```

- 插件：`calendar:standard:变动速率 ROC`；变换链：`[]`。

<a id="f-6cf9064b506a027c"></a>

## cal_standard_商品通道指标 CCI

- ID：`6cf9064b506a027c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0395 / 0.0178。

登记表达式或插件说明：

```text
按原文默认 N=20。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:商品通道指标 CCI
```

- 插件：`calendar:standard:商品通道指标 CCI`；变换链：`[]`。

<a id="f-a5415bc9049583bf"></a>

## cal_standard_在险价值 VaR

- ID：`a5415bc9049583bf`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:vol20；历史均值 / 最差年 RankIC：0.0466 / 0.0273。

登记表达式或插件说明：

```text
置信水平未定；按 20 日 5% 收益分位数的相反数试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:在险价值 VaR
```

- 插件：`calendar:standard:在险价值 VaR`；变换链：`[]`。

<a id="f-fdac4055c21dd78a"></a>

## cal_standard_垂直水平过滤指标 VHF

- ID：`fdac4055c21dd78a`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0011 / -0.0177。

登记表达式或插件说明：

```text
N 未定；按常用 N=28 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:垂直水平过滤指标 VHF
```

- 插件：`calendar:standard:垂直水平过滤指标 VHF`；变换链：`[]`。

<a id="f-f68926dbec0e313d"></a>

## cal_standard_基于振幅切割的动量

- ID：`f68926dbec0e313d`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0291 / 0.0092。

登记表达式或插件说明：

```text
按原文 160 日窗口，保留振幅最低 70% 日期。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:基于振幅切割的动量
```

- 插件：`calendar:standard:基于振幅切割的动量`；变换链：`[]`。

<a id="f-3a5c3552aef8b2ec"></a>

## cal_standard_多空指数 BBI

- ID：`3a5c3552aef8b2ec`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0338 / -0.0030。

登记表达式或插件说明：

```text
按原文取 3、6、12、20 日均线的平均。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:多空指数 BBI
```

- 插件：`calendar:standard:多空指数 BBI`；变换链：`[]`。

<a id="f-d716dccffef25398"></a>

## cal_standard_对数总市值

- ID：`d716dccffef25398`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0288 / 0.0048。

登记表达式或插件说明：

```text
按原式取总市值自然对数。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:对数总市值
```

- 插件：`calendar:standard:对数总市值`；变换链：`[]`。

<a id="f-50adb9a2d71d5d52"></a>

## cal_standard_对数流通市值

- ID：`50adb9a2d71d5d52`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0181 / 0.0006。

登记表达式或插件说明：

```text
用数据中的流通股本计算并取自然对数。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:对数流通市值
```

- 插件：`calendar:standard:对数流通市值`；变换链：`[]`。

<a id="f-c693ca762eb80aee"></a>

## cal_standard_平均真实波幅 ATR

- ID：`c693ca762eb80aee`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0604 / 0.0255。

登记表达式或插件说明：

```text
N 未定；按常用 N=14 的 EMA 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:平均真实波幅 ATR
```

- 插件：`calendar:standard:平均真实波幅 ATR`；变换链：`[]`。

<a id="f-46e8024d56335109"></a>

## cal_standard_平滑异同均线指标 MACD

- ID：`46e8024d56335109`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0274 / 0.0064。

登记表达式或插件说明：

```text
按原文 12、26、9，输出 2×(DIF-DEA)。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:平滑异同均线指标 MACD
```

- 插件：`calendar:standard:平滑异同均线指标 MACD`；变换链：`[]`。

<a id="f-ae9de2b4949238ed"></a>

## cal_standard_异同离差乖离率 DBCD

- ID：`ae9de2b4949238ed`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0166 / 0.0058。

登记表达式或插件说明：

```text
按常用 N1=6、N2=16、N3=3 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:异同离差乖离率 DBCD
```

- 插件：`calendar:standard:异同离差乖离率 DBCD`；变换链：`[]`。

<a id="f-a997122785643de1"></a>

## cal_standard_心理线 PSY

- ID：`a997122785643de1`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0223 / 0.0093。

登记表达式或插件说明：

```text
按原文默认 N=12。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:心理线 PSY
```

- 插件：`calendar:standard:心理线 PSY`；变换链：`[]`。

<a id="f-3540ab5b9fe42378"></a>

## cal_standard_总偏度

- ID：`3540ab5b9fe42378`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0324 / 0.0118。

登记表达式或插件说明：

```text
K 未定；按 20 日日收益偏度试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:总偏度
```

- 插件：`calendar:standard:总偏度`；变换链：`[]`。

<a id="f-2c125198aaf6cf6c"></a>

## cal_standard_总市值

- ID：`2c125198aaf6cf6c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0288 / 0.0048。

登记表达式或插件说明：

```text
按原式：未复权收盘价×总股本。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:总市值
```

- 插件：`calendar:standard:总市值`；变换链：`[]`。

<a id="f-7d7545cb4b50ceb5"></a>

## cal_standard_总波动率

- ID：`7d7545cb4b50ceb5`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0735 / 0.0654。

登记表达式或插件说明：

```text
K 未定；按 20 日日收益标准差试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:总波动率
```

- 插件：`calendar:standard:总波动率`；变换链：`[]`。

<a id="f-7209ed72bd8d5294"></a>

## cal_standard_成交量加权移动均线 VAMA

- ID：`7209ed72bd8d5294`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0331 / -0.0042。

登记表达式或插件说明：

```text
N 未定；以收盘价为 REAL，按 N=20 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:成交量加权移动均线 VAMA
```

- 插件：`calendar:standard:成交量加权移动均线 VAMA`；变换链：`[]`。

<a id="f-a16e6a9db3d35711"></a>

## cal_standard_成交量变动速率 VROC

- ID：`a16e6a9db3d35711`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0305 / 0.0067。

登记表达式或插件说明：

```text
N 未定；按常用 N=12 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:成交量变动速率 VROC
```

- 插件：`calendar:standard:成交量变动速率 VROC`；变换链：`[]`。

<a id="f-e728aa7f5681ad4d"></a>

## cal_standard_成交量平滑异同均线指标 VMACD

- ID：`e728aa7f5681ad4d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0160 / -0.0036。

登记表达式或插件说明：

```text
按 12、26、9 试算，输出柱值。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:成交量平滑异同均线指标 VMACD
```

- 插件：`calendar:standard:成交量平滑异同均线指标 VMACD`；变换链：`[]`。

<a id="f-0c2e7fb96ece0596"></a>

## cal_standard_成交量摆动指标 VO

- ID：`0c2e7fb96ece0596`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0211 / 0.0121。

登记表达式或插件说明：

```text
N1、N2 未定；按常用 5、10 日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:成交量摆动指标 VO
```

- 插件：`calendar:standard:成交量摆动指标 VO`；变换链：`[]`。

<a id="f-be35967595faacb3"></a>

## cal_standard_成交量比率指标 VR

- ID：`be35967595faacb3`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0320 / 0.0208。

登记表达式或插件说明：

```text
N 未定；按常用 N=26 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:成交量比率指标 VR
```

- 插件：`calendar:standard:成交量比率指标 VR`；变换链：`[]`。

<a id="f-ed3326c907dd7b33"></a>

## cal_standard_成交量相对强弱指标 VRSI

- ID：`ed3326c907dd7b33`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0270 / 0.0170。

登记表达式或插件说明：

```text
N 未定；按 N=14 的 EMA 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:成交量相对强弱指标 VRSI
```

- 插件：`calendar:standard:成交量相对强弱指标 VRSI`；变换链：`[]`。

<a id="f-f5384638d69e9955"></a>

## cal_standard_换手波动

- ID：`f5384638d69e9955`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0698 / 0.0599。

登记表达式或插件说明：

```text
原文 K 月未定；按近 20 个交易日日换手率标准差试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:换手波动
```

- 插件：`calendar:standard:换手波动`；变换链：`[]`。

<a id="f-bad1f7ebd481ffc3"></a>

## cal_standard_换手率

- ID：`bad1f7ebd481ffc3`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0644 / 0.0573。

登记表达式或插件说明：

```text
原文 K 月未定；按近 20 个交易日日换手率均值试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:换手率
```

- 插件：`calendar:standard:换手率`；变换链：`[]`。

<a id="f-45405032cf708261"></a>

## cal_standard_换手率变异系数

- ID：`45405032cf708261`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0396 / 0.0176。

登记表达式或插件说明：

```text
按近 20 日换手率标准差/均值试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:换手率变异系数
```

- 插件：`calendar:standard:换手率变异系数`；变换链：`[]`。

<a id="f-e52b2f38bb49e98d"></a>

## cal_standard_收集派发指标 ACD

- ID：`e52b2f38bb49e98d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0471 / 0.0307。

登记表达式或插件说明：

```text
N 未定；按 20 日 DIF 累计值试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:收集派发指标 ACD
```

- 插件：`calendar:standard:收集派发指标 ACD`；变换链：`[]`。

<a id="f-dc4b0572d069cadc"></a>

## cal_standard_方向标准离差指标 DDI

- ID：`dc4b0572d069cadc`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0378 / 0.0176。

登记表达式或插件说明：

```text
原文窗口未定；按常用 N=13 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:方向标准离差指标 DDI
```

- 插件：`calendar:standard:方向标准离差指标 DDI`；变换链：`[]`。

<a id="f-d17df853379fb4e2"></a>

## cal_standard_日内动量指标 IMI

- ID：`d17df853379fb4e2`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0451 / 0.0203。

登记表达式或插件说明：

```text
N 未定；按常用 N=14 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:日内动量指标 IMI
```

- 插件：`calendar:standard:日内动量指标 IMI`；变换链：`[]`。

<a id="f-953f8e9204c1b845"></a>

## cal_standard_日内收益率

- ID：`953f8e9204c1b845`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0185 / 0.0091。

登记表达式或插件说明：

```text
输出单日日内收益；周月汇总由调用方处理。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:日内收益率
```

- 插件：`calendar:standard:日内收益率`；变换链：`[]`。

<a id="f-638429cc47f1192d"></a>

## cal_standard_最大收益率

- ID：`638429cc47f1192d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0719 / 0.0595。

登记表达式或插件说明：

```text
K、n 未定；按近 20 日最大单日收益试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:最大收益率
```

- 插件：`calendar:standard:最大收益率`；变换链：`[]`。

<a id="f-7ebcf4e736d77b7e"></a>

## cal_standard_最小收益率

- ID：`7ebcf4e736d77b7e`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0412 / 0.0269。

登记表达式或插件说明：

```text
K、n 未定；按近 20 日最小单日收益的相反数试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:最小收益率
```

- 插件：`calendar:standard:最小收益率`；变换链：`[]`。

<a id="f-1285496f6d99ea2f"></a>

## cal_standard_最近 52 周最高价因子

- ID：`1285496f6d99ea2f`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0147 / -0.0151。

登记表达式或插件说明：

```text
按 252 个交易日代表 52 周。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:最近 52 周最高价因子
```

- 插件：`calendar:standard:最近 52 周最高价因子`；变换链：`[]`。

<a id="f-8be20c0e1328f85b"></a>

## cal_standard_月度异常换手率

- ID：`8be20c0e1328f85b`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0563 / 0.0421。

登记表达式或插件说明：

```text
按原文使用 20 日均值/250 日均值。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:月度异常换手率
```

- 插件：`calendar:standard:月度异常换手率`；变换链：`[]`。

<a id="f-02646f85ec95895f"></a>

## cal_standard_条件风险价值 CVaR

- ID：`02646f85ec95895f`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0412 / 0.0269。

登记表达式或插件说明：

```text
置信水平未定；按 20 日 5% 左尾收益均值的相反数试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:条件风险价值 CVaR
```

- 插件：`calendar:standard:条件风险价值 CVaR`；变换链：`[]`。

<a id="f-7411ae995890f8e3"></a>

## cal_standard_梅斯线 Mass Index

- ID：`7411ae995890f8e3`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0396 / 0.0215。

登记表达式或插件说明：

```text
按常用 9、9、25 参数试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:梅斯线 Mass Index
```

- 插件：`calendar:standard:梅斯线 Mass Index`；变换链：`[]`。

<a id="f-52d07a5a042af334"></a>

## cal_standard_正向日内逆转的频率

- ID：`52d07a5a042af334`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0248 / 0.0148。

登记表达式或插件说明：

```text
月度按 20 个交易日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:正向日内逆转的频率
```

- 插件：`calendar:standard:正向日内逆转的频率`；变换链：`[]`。

<a id="f-953e76aa6a10dfde"></a>

## cal_standard_正量指标 PVI

- ID：`953e76aa6a10dfde`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0119 / -0.0044。

登记表达式或插件说明：

```text
按原式，初值 1000。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:正量指标 PVI
```

- 插件：`calendar:standard:正量指标 PVI`；变换链：`[]`。

<a id="f-57bec643f1649f04"></a>

## cal_standard_流通股市值

- ID：`57bec643f1649f04`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:size；历史均值 / 最差年 RankIC：0.0181 / 0.0006。

登记表达式或插件说明：

```text
用数据中的流通股本；它不一定等同于指数公司口径的自由流通股本。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:流通股市值
```

- 插件：`calendar:standard:流通股市值`；变换链：`[]`。

<a id="f-dc71d8178495a56a"></a>

## cal_standard_理想振幅因子

- ID：`dc71d8178495a56a`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0675 / 0.0534。

登记表达式或插件说明：

```text
N、λ 未定；按 20 日、上下各 20% 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:理想振幅因子
```

- 插件：`calendar:standard:理想振幅因子`；变换链：`[]`。

<a id="f-f9c61f5212ecf315"></a>

## cal_standard_相对动量指标 RMI

- ID：`f9c61f5212ecf315`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0401 / 0.0162。

登记表达式或插件说明：

```text
按常用动量间隔 4 日、平滑 14 日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:相对动量指标 RMI
```

- 插件：`calendar:standard:相对动量指标 RMI`；变换链：`[]`。

<a id="f-5c9eca68e64cb426"></a>

## cal_standard_相对强弱指标 RSI

- ID：`5c9eca68e64cb426`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0390 / 0.0187。

登记表达式或插件说明：

```text
按原文默认 N=14。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:相对强弱指标 RSI
```

- 插件：`calendar:standard:相对强弱指标 RSI`；变换链：`[]`。

<a id="f-41a2dbed727c47f3"></a>

## cal_standard_相对波动率指标 RVI

- ID：`41a2dbed727c47f3`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0144 / -0.0024。

登记表达式或插件说明：

```text
原文窗口未定；价格标准差取 10 日，方向平滑取 14 日。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:相对波动率指标 RVI
```

- 插件：`calendar:standard:相对波动率指标 RVI`；变换链：`[]`。

<a id="f-2e52c5af9acad613"></a>

## cal_standard_真实强度指数 TSI

- ID：`2e52c5af9acad613`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0484 / 0.0222。

登记表达式或插件说明：

```text
按常用 25、13 双重 EMA 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:真实强度指数 TSI
```

- 插件：`calendar:standard:真实强度指数 TSI`；变换链：`[]`。

<a id="f-9268ad1f6d0e4301"></a>

## cal_standard_真实波动范围 TR

- ID：`9268ad1f6d0e4301`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0663 / 0.0319。

登记表达式或插件说明：

```text
按原式计算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:真实波动范围 TR
```

- 插件：`calendar:standard:真实波动范围 TR`；变换链：`[]`。

<a id="f-f8967fc97dc87686"></a>

## cal_standard_短期反转

- ID：`f8967fc97dc87686`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0520 / 0.0313。

登记表达式或插件说明：

```text
按总表举例使用 20 日累计收益。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:短期反转
```

- 插件：`calendar:standard:短期反转`；变换链：`[]`。

<a id="f-b82e795456aef97b"></a>

## cal_standard_简易波动指标 EMV

- ID：`b82e795456aef97b`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0297 / 0.0125。

登记表达式或插件说明：

```text
按原式先算单日 EMV，再取 14 日均值试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:简易波动指标 EMV
```

- 插件：`calendar:standard:简易波动指标 EMV`；变换链：`[]`。

<a id="f-19d9d4e3460b93be"></a>

## cal_standard_累积/派发线 AD

- ID：`19d9d4e3460b93be`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0009 / -0.0178。

登记表达式或插件说明：

```text
按原式累计资金流量乘数×成交量。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:累积/派发线 AD
```

- 插件：`calendar:standard:累积/派发线 AD`；变换链：`[]`。

<a id="f-1b286bae3293ab98"></a>

## cal_standard_终极震荡指标 UOS

- ID：`1b286bae3293ab98`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0258 / 0.0058。

登记表达式或插件说明：

```text
按常用 7、14、28 日窗口试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:终极震荡指标 UOS
```

- 插件：`calendar:standard:终极震荡指标 UOS`；变换链：`[]`。

<a id="f-5d7f46c87f8e4f3f"></a>

## cal_standard_综合股权发行（5 年）

- ID：`5d7f46c87f8e4f3f`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
按 1260 个交易日代表五年试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:综合股权发行（5 年）
```

- 插件：`calendar:standard:综合股权发行（5 年）`；变换链：`[]`。

<a id="f-f3cd4cf0d0608111"></a>

## cal_standard_综合股权发行（年度）

- ID：`f3cd4cf0d0608111`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0095 / -0.0057。

登记表达式或插件说明：

```text
按 252 个交易日代表一年试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:综合股权发行（年度）
```

- 插件：`calendar:standard:综合股权发行（年度）`；变换链：`[]`。

<a id="f-6bc39f34e7305896"></a>

## cal_standard_股票交易周转率

- ID：`6bc39f34e7305896`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_mean+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0549 / 0.0478。

登记表达式或插件说明：

```text
原文区间未定；按 20 日成交额/期初期末平均总市值试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:股票交易周转率
```

- 插件：`calendar:standard:股票交易周转率`；变换链：`[]`。

<a id="f-3b76ff5c469803ca"></a>

## cal_standard_能量指标 CR

- ID：`3b76ff5c469803ca`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0490 / 0.0221。

登记表达式或插件说明：

```text
N 未定；按常用 N=26 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:能量指标 CR
```

- 插件：`calendar:standard:能量指标 CR`；变换链：`[]`。

<a id="f-b6d8841200c93973"></a>

## cal_standard_能量指标 OBV

- ID：`b6d8841200c93973`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0005 / -0.0273。

登记表达式或插件说明：

```text
按原式累计涨跌方向成交量。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:能量指标 OBV
```

- 插件：`calendar:standard:能量指标 OBV`；变换链：`[]`。

<a id="f-3a2a109b048b7b08"></a>

## cal_standard_蔡金货币流量指标 CMF

- ID：`3a2a109b048b7b08`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0182 / 0.0034。

登记表达式或插件说明：

```text
N 未定；按常用 N=20 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:蔡金货币流量指标 CMF
```

- 插件：`calendar:standard:蔡金货币流量指标 CMF`；变换链：`[]`。

<a id="f-8f741a76c103b39c"></a>

## cal_standard_负偏度系数 NCSKEW

- ID：`8f741a76c103b39c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0324 / 0.0118。

登记表达式或插件说明：

```text
按总表默认 n=20。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:负偏度系数 NCSKEW
```

- 插件：`calendar:standard:负偏度系数 NCSKEW`；变换链：`[]`。

<a id="f-f7cc7c17de93032d"></a>

## cal_standard_负收益非流动性

- ID：`f7cc7c17de93032d`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0412 / 0.0211。

登记表达式或插件说明：

```text
按近 20 日下跌日 abs(日收益)/成交额均值试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:负收益非流动性
```

- 插件：`calendar:standard:负收益非流动性`；变换链：`[]`。

<a id="f-a1911c03d67f5741"></a>

## cal_standard_负量指标 NVI

- ID：`a1911c03d67f5741`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0025 / -0.0143。

登记表达式或插件说明：

```text
按原式，初值 1000。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:负量指标 NVI
```

- 插件：`calendar:standard:负量指标 NVI`；变换链：`[]`。

<a id="f-fe42faa4316de1da"></a>

## cal_standard_货币流量指标 MFI

- ID：`fe42faa4316de1da`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0320 / 0.0149。

登记表达式或插件说明：

```text
N 未定；按常用 N=14 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:货币流量指标 MFI
```

- 插件：`calendar:standard:货币流量指标 MFI`；变换链：`[]`。

<a id="f-1ef0ea7b53486b6c"></a>

## cal_standard_趋势分数指标 TS

- ID：`1ef0ea7b53486b6c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0132 / -0.0045。

登记表达式或插件说明：

```text
N 未定；按 N=20 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:趋势分数指标 TS
```

- 插件：`calendar:standard:趋势分数指标 TS`；变换链：`[]`。

<a id="f-577536b3085f1ae7"></a>

## cal_standard_钱德动量摆动平均指数 VIDYA

- ID：`577536b3085f1ae7`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0285 / -0.0084。

登记表达式或插件说明：

```text
原文参数未定；CMO 取 14 日，基础平滑取 20 日。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:钱德动量摆动平均指数 VIDYA
```

- 插件：`calendar:standard:钱德动量摆动平均指数 VIDYA`；变换链：`[]`。

<a id="f-4e6bd831a77b89ca"></a>

## cal_standard_钱德动量摆动指标 CMO

- ID：`4e6bd831a77b89ca`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0376 / 0.0187。

登记表达式或插件说明：

```text
按常用 N=14 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:钱德动量摆动指标 CMO
```

- 插件：`calendar:standard:钱德动量摆动指标 CMO`；变换链：`[]`。

<a id="f-388f6b3427f2d1b1"></a>

## cal_standard_长期反转

- ID：`388f6b3427f2d1b1`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`0`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_direction；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
按原文第 t-59 月至 t-12 月，交易日近似为 1260 日至 252 日。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:长期反转
```

- 插件：`calendar:standard:长期反转`；变换链：`[]`。

<a id="f-13c449141856e2c7"></a>

## cal_standard_阿隆指标 AROON

- ID：`13c449141856e2c7`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0361 / 0.0159。

登记表达式或插件说明：

```text
按原文默认 N=20。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:阿隆指标 AROON
```

- 插件：`calendar:standard:阿隆指标 AROON`；变换链：`[]`。

<a id="f-b98f8a5eee081c1c"></a>

## cal_standard_随机动量指标 SMI

- ID：`b98f8a5eee081c1c`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0245 / 0.0018。

登记表达式或插件说明：

```text
原文窗口未定；按 14、3、3 试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:随机动量指标 SMI
```

- 插件：`calendar:standard:随机动量指标 SMI`；变换链：`[]`。

<a id="f-43b4f5e4d0465b71"></a>

## cal_standard_随机指标 KDJ

- ID：`43b4f5e4d0465b71`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0161 / 0.0036。

登记表达式或插件说明：

```text
按常用 9、3、3，输出 J。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:随机指标 KDJ
```

- 插件：`calendar:standard:随机指标 KDJ`；变换链：`[]`。

<a id="f-368857654e75e84e"></a>

## cal_standard_随机相对强弱指标 SRSI

- ID：`368857654e75e84e`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0095 / -0.0167。

登记表达式或插件说明：

```text
RSI 与归一化窗口未定；均按 14 日试算。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:随机相对强弱指标 SRSI
```

- 插件：`calendar:standard:随机相对强弱指标 SRSI`；变换链：`[]`。

<a id="f-ae0b083058102c7a"></a>

## cal_standard_隔夜收益率

- ID：`ae0b083058102c7a`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0158 / 0.0065。

登记表达式或插件说明：

```text
输出单日隔夜收益；周月汇总由调用方处理。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:隔夜收益率
```

- 插件：`calendar:standard:隔夜收益率`；变换链：`[]`。

<a id="f-9713573be8d7641e"></a>

## cal_standard_隔夜跳空

- ID：`9713573be8d7641e`；归属：active_396, research_597, pool_current。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0659 / 0.0539。

登记表达式或插件说明：

```text
按原文累计近 20 日隔夜对数收益绝对值。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:隔夜跳空
```

- 插件：`calendar:standard:隔夜跳空`；变换链：`[]`。

<a id="f-64374e2eb8d009b7"></a>

## cal_standard_非流动性的变异系数 CVILLIQ

- ID：`64374e2eb8d009b7`；归属：历史候选，未列入上述集合。
- 机制：calendar（登记标签，不是独立信息量判定）。
- 类型：`plugin`；冻结方向：`1`；评价状态：`ok`。
- 原假设：external library factor
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0066 / -0.0289。

登记表达式或插件说明：

```text
按原文使用 20 日窗口。
```

规范式 / 计算标识：

```text
plugin:calendar:standard:非流动性的变异系数 CVILLIQ
```

- 插件：`calendar:standard:非流动性的变异系数 CVILLIQ`；变换链：`[]`。
