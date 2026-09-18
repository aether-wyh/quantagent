# 模型提案

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-74f835c2d0c1b5b0"></a>

## abn_turn_20_250_sizeneutral

- ID：`74f835c2d0c1b5b0`；归属：active_396, research_597, pool_current。
- 机制：异常换手（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把异常换手的基准线从 120 日拉到 250 日：当前一个月的换手相对整整一年的常态越高，说明这只票正处在关注度冲击里，冲击回落后收益更低。年度基准比季度基准更稳定，也把这一格从短窗口挪到长窗口。
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0525 / 0.0395。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_mean(turnover, 20) / rolling_mean(turnover, 250), log_cap)
```

- 父因子：[0a38584bd0558cdb](classic.md#f-0a38584bd0558cdb)、[6b95eea15d64187e](classic.md#f-6b95eea15d64187e)。

<a id="f-15973d83eec9b319"></a>

## abn_turnover_z_sizeneutral

- ID：`15973d83eec9b319`；归属：active_396, research_597, pool_current。
- 机制：异常换手（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把近5日平均换手相对该股自身过去120日的分布做时序标准化，再剔除市值。用z分数而非比值，可以让换手波动大的股票不会仅因基数低就被判为异常，度量的是相对自己历史有多反常的关注度冲击。
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0504 / 0.0397。

登记表达式或插件说明：

```text
-cs_neutralize(ts_zscore(rolling_mean(turnover, 5), 120), log_cap)
```


<a id="f-44f2c7e4f77b3ae6"></a>

## amihud250_sizeneutral

- ID：`44f2c7e4f77b3ae6`；归属：历史候选，未列入上述集合。
- 机制：非流动性(Amihud)（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：上轮把 illiquidity 从 medium 升到 high 的理由是 amihud20 在 2021 年 RankIC +0.048、相对自身六年均值 +0.0114，是全池 2021 相对表现第二好的成员。本条把同一机制拉到 250 日并只做市值中性化：单位成交额引起的价格冲击是股票的结构性属性，用一年的均值估计比一个月稳定得多，流动性溢价也是长期定价的。
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0065 / -0.0042。

登记表达式或插件说明：

```text
cs_neutralize(rolling_mean(abs(ret) / amount, 250), log_cap)
```

- 父因子：[a85fe4eb6df04f8f](alpha158.md#f-a85fe4eb6df04f8f)。

<a id="f-061f77d11e76937a"></a>

## amount_change_direction20

- ID：`061f77d11e76937a`；归属：active_396, research_597, pool_current。
- 机制：成交量趋势（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：口径审计的第二半：把病态表达式拆成幅度列与方向列，让下游模型自己组合，而不是丢弃。方向列单独就有信息——20 日成交额净增加的股票未来五日收益更低，是关注度冲击后的回落。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0310 / 0.0093。

登记表达式或插件说明：

```text
-sign(delta(amount, 20))
```

- 父因子：[fc0e18ea5741dcc1](gp.md#f-fc0e18ea5741dcc1)。

<a id="f-10fffd16b2033bf2"></a>

## amount_cv250_sizeneutral

- ID：`10fffd16b2033bf2`；归属：历史候选，未列入上述集合。
- 机制：new:amount_dispersion（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：年度成交额的相对离散度：同市值下成交额越不稳定，说明这只票是被间断的题材/资金脉冲驱动的，关注度不可持续，未来收益越低；成交额平稳的票有持续的机构参与。上一批的 amount_dispersion60 用的是 log 水平的标准差、与成交额簇相关 0.593，本条改成变异系数并拉到 250 日，把量级维度构造性地除掉。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0249 / 0.0035。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_std(amount, 250) / rolling_mean(amount, 250), log_cap)
```

- 父因子：[fa8f3b9c8f131558](gp.md#f-fa8f3b9c8f131558)。

<a id="f-75e1cab21b4c27c8"></a>

## amount_dispersion60_sizeneutral

- ID：`75e1cab21b4c27c8`；归属：active_396, research_597, pool_current。
- 机制：new:amount_dispersion（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：成交额对数在 60 日内的时序离散度度量的是'这只股票的资金关注度有多不稳定'：离散度高说明成交由零星的关注冲击驱动、参与者进出频繁、定价噪声大；离散度低说明存在稳定的持有人结构与连续的做市。对数化后离散度与成交额绝对水平解耦，再对 log_cap 做横截面残差化去掉规模维度，剩下的是纯粹的'资金流稳定性'。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0463 / 0.0326。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_std(log(1 + amount), 60), log_cap)
```


<a id="f-63f82f8b3d5b23a7"></a>

## amount_expansion_size_fullcover20

- ID：`63f82f8b3d5b23a7`；归属：历史候选，未列入上述集合。
- 机制：成交量趋势（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：全池第一名 gp2_02 的口径审计。原式 log_cap / log(delta(amount, 20)) 只在 20 日成交额净增加的那一半股票上有定义，等于在有偏子样本上测量，也因此被组合层的覆盖率规则整体剔除、对组合贡献为零。把分母换成恒正写法 log(1 + abs(delta(amount, 20)))，机制不变——同市值下成交额绝对变动越大（关注度越拥挤、越被反复交易），未来收益越低——但横截面恢复全覆盖。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0652 / 0.0586。

登记表达式或插件说明：

```text
log_cap / log(1 + abs(delta(amount, 20)))
```

- 父因子：[fc0e18ea5741dcc1](gp.md#f-fc0e18ea5741dcc1)、[94f9b8ef07881462](gp.md#f-94f9b8ef07881462)。

<a id="f-82de9bf5154e6054"></a>

## amount_spike_share20_sizeneutral

- ID：`82de9bf5154e6054`；归属：active_396, research_597, pool_current。
- 机制：new:amount_spike_concentration（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：过去 20 日里单日最大成交额占总成交额的比例，度量的是'最近一次关注冲击有多极端'。占比高说明成交高度集中于某一天的事件性脉冲（游资、公告、题材炒作），这类筹码的持有期短、后续抛压大；占比低说明成交均匀分布、换手由结构性持有人贡献。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0362 / 0.0200。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_max(amount, 20) / rolling_sum(amount, 20), log_cap)
```


<a id="f-06141f8aec5d525f"></a>

## beta60_volneutral

- ID：`06141f8aec5d525f`；归属：active_396, research_597, pool_current。
- 机制：市场贝塔（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：覆盖图上唯一有强文献基础却 tried = 0 的格子。把总波动中性化后剩下的是'相同波动水平下，收益里有多少是随市场共动的'。探针结果**反驳**了上一批复盘 H7 的低 beta 先验：训练期高 beta（给定波动）对应更高的后续收益，即残差 beta 是正向的。可能的机制是：给定同样的总波动，高 beta 意味着特质波动占比低、信息环境更干净，而 A 股的低特质波动溢价本身就很强。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0216 / 0.0055。

登记表达式或插件说明：

```text
cs_neutralize(rolling_beta(ret, mkt_ret, 60), cs_rank(rolling_std(ret, 20)))
```


<a id="f-a4d3b8cb79c93bd6"></a>

## consecutive_moves10_retneutral

- ID：`a4d3b8cb79c93bd6`；归属：active_396, research_597, pool_current。
- 机制：连续涨跌天数（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：路径形状里唯一与幅度天然正交的维度是方向计数：同样的 10 日涨幅，靠 8 涨 2 跌的连续小阳堆出来（信息缓慢扩散、机构分批建仓）与靠一两根大阳拉出来（脉冲炒作）后续应该不同。把 10 日累计收益残差化掉，留下纯方向计数。训练期显示上涨天数多者后续更好，即缓慢扩散段延续。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0163 / 0.0074。

登记表达式或插件说明：

```text
cs_neutralize(rolling_sum(sign(ret), 10), close / lag(close, 10) - 1)
```


<a id="f-a44a0095ff775b7e"></a>

## cost_anchor120_revneutral

- ID：`a44a0095ff775b7e`；归属：active_396, research_597, pool_current。
- 机制：new:cost_basis_deviation（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：同一成本锚机制的中期尺度版，并且把短期反转残差化掉。近期跌得多的股票自然也离成本锚更远，所以必须先扣掉 20 日反转，剩下的才是真正的'浮盈/浮亏深度'。120 日大致对应半年换手一轮，是处置效应最可能起作用的持有期。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0302 / 0.0125。

登记表达式或插件说明：

```text
-cs_neutralize(cs_neutralize(close * rolling_sum(volume, 120) / rolling_sum(amount, 120) - 1, log_cap), close / lag(close, 20) - 1)
```

- 父因子：[df081b65f2e74a4b](llm.md#f-df081b65f2e74a4b)、[0a59417e689c8096](classic.md#f-0a59417e689c8096)。

<a id="f-0b5e56339da50a86"></a>

## cost_anchor250_sizeneutral

- ID：`0b5e56339da50a86`；归属：active_396, research_597, pool_current。
- 机制：new:cost_basis_deviation（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：上上轮 H1、上轮 H2，两轮提出从未执行，本批补执行。用 250 日成交额加权均价作为持仓成本锚，当前价相对成本锚的溢价越高、浮盈越大、获利了结压力越重，未来收益越低（处置效应）。250 日尺度正对上池内最缺的窗口格：109 个成员里只有 4 个用到 &gt;60 日。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0458 / 0.0302。

登记表达式或插件说明：

```text
-cs_neutralize(close * rolling_sum(volume, 250) / rolling_sum(amount, 250) - 1, log_cap)
```

- 父因子：[df081b65f2e74a4b](llm.md#f-df081b65f2e74a4b)、[e8ee3bf4a239105c](alpha158.md#f-e8ee3bf4a239105c)。

<a id="f-df081b65f2e74a4b"></a>

## cost_basis_dev60

- ID：`df081b65f2e74a4b`；归属：active_396, research_597, pool_current。
- 机制：new:cost_basis_deviation（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：用过去60日成交额除以成交量得到资金加权平均成本，再看当前收盘价相对该成本的偏离。处置效应下，持仓普遍浮盈的股票面临兑现抛压，浮亏的股票持有者不愿割肉、供给收缩；偏离度越高未来收益越低。这是持仓成本分布的粗粒度代理，只有同时用成交额和成交量才能构造。
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0519 / 0.0352。

登记表达式或插件说明：

```text
-cs_neutralize(close * rolling_sum(volume, 60) / rolling_sum(amount, 60) - 1, log_cap)
```


<a id="f-31283d05280a2a65"></a>

## downside_share250_sizeneutral

- ID：`31283d05280a2a65`；归属：历史候选，未列入上述集合。
- 机制：下行波动占比（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把下行波动占比从 20 日拉到 250 日。年度口径下，总波动里下行部分占比越高，说明这只票的风险是偏向左尾的、投资者要求的补偿越高，未来收益越高。20 日版是 moderate（+0.031），而上轮的窗口族诊断显示这一类风险度量在 60 日以上才稳定。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0410 / 0.0260。

登记表达式或插件说明：

```text
cs_neutralize(rolling_sum(where(ret < 0, ret * ret, 0), 250) / rolling_sum(ret * ret, 250), log_cap)
```

- 父因子：[83685fe52892abc9](classic.md#f-83685fe52892abc9)。

<a id="f-ab8333b5c06ff972"></a>

## downside_var_share_volneutral

- ID：`ab8333b5c06ff972`；归属：历史候选，未列入上述集合。
- 机制：下行波动占比（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：下行方差占总方差的比例，衡量波动的不对称性：波动主要来自下跌日的股票已经被恐慌定价、要求更高的风险溢价；波动主要来自上涨日的股票带有博彩属性被高估。再对总波动率做中性化，只保留波动的方向构成这一维。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0313 / 0.0152。

登记表达式或插件说明：

```text
cs_neutralize(rolling_sum(where(ret < 0, ret * ret, 0), 20) / rolling_sum(ret * ret, 20), cs_rank(rolling_std(ret, 20)))
```


<a id="f-1343673f8c8aac13"></a>

## idio_skew20_residvol_neutral

- ID：`1343673f8c8aac13`；归属：历史候选，未列入上述集合。
- 机制：收益偏度（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把偏度从总收益换成对市场回归后的特质残差收益，并对残差波动做中性化。彩票偏好假说针对的是特质层面的右偏（投资者为'小概率大涨'付溢价），市场共同成分带来的偏度不属于这个机制，只是噪声。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0114 / 0.0035。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_skew(rolling_residual(ret, mkt_ret, 60), 20), rolling_std(rolling_residual(ret, mkt_ret, 60), 20))
```

- 父因子：[fed5477153a935a8](classic.md#f-fed5477153a935a8)。

<a id="f-694a548c2c2bbef9"></a>

## impact_per_turnover60

- ID：`694a548c2c2bbef9`；归属：active_396, research_597, pool_current。
- 机制：new:impact_per_turnover（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：真实价格冲击的另一种写法：单位换手换来多少日内振幅。同样的换手水平下振幅越大，说明盘口越薄、深度越差，投资者要求的流动性补偿越高、未来收益越高。这条把'流动性'从成交活跃度（换手水平）改写成流动性成本（深度），是覆盖图上 illiquidity 与 low_volatility 之间缺的那一格。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0469 / 0.0313。

登记表达式或插件说明：

```text
cs_neutralize(rolling_mean(log(high / low), 60) / rolling_mean(turnover, 60), log_cap)
```

- 父因子：[a85fe4eb6df04f8f](alpha158.md#f-a85fe4eb6df04f8f)、[974250cf2f6bbb65](classic.md#f-974250cf2f6bbb65)。

<a id="f-a6a6f10a1be676d6"></a>

## intraday_reversal_turnweighted20_volneutral

- ID：`a6a6f10a1be676d6`；归属：active_396, research_597, pool_current。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把日收益拆成日内段 log(close/open) 与隔夜段 log(open/prev_close)，只取日内段，并按当日换手率加权（放量日的日内涨跌权重更高，代表更多筹码是在那个价位换手的）。日内段是散户与游资的博弈区间，情绪冲击集中在这里，因此日内累计涨幅应当反转；换手加权让'有多少人真的在这个涨幅上接盘'进入因子。
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0348 / 0.0217。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_sum(log(close / open) * turnover, 20) / rolling_sum(turnover, 20), rolling_std(ret, 20))
```

- 父因子：[34eda56cb006729b](classic.md#f-34eda56cb006729b)。

<a id="f-d2c37a2ad4f7d7b5"></a>

## min_ret250_sizeneutral

- ID：`d2c37a2ad4f7d7b5`；归属：历史候选，未列入上述集合。
- 机制：new:long_horizon_tail_risk（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：上轮 2021 年相对赢家名单里 minimum_return 排第三（+0.0095）。本条把它拉到 250 日：过去一年最差单日收益越接近零，说明这只票没有过崩塌式的尾部事件，属于结构性稳健标的，未来收益更高。这是 lottery_maxret（最大单日收益）的镜像维度，覆盖图上只测过最大值一侧。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0291 / 0.0139。

登记表达式或插件说明：

```text
cs_neutralize(rolling_min(ret, 250), log_cap)
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)、[83685fe52892abc9](classic.md#f-83685fe52892abc9)。

<a id="f-a747b1d2bd39262e"></a>

## mw_reversal250_resid20

- ID：`a747b1d2bd39262e`；归属：历史候选，未列入上述集合。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：上一条的纯长窗口增量版：把 20 日换手加权收益残差化掉之后，剩下的只有 20—250 日之间那一段筹码的盈亏状态。这正是上轮诊断里'池子 77% 挤在 30 日以内'所缺的那一段，也是唯一能直接检验'长窗口是独立信息还是短窗口平滑'的写法。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0297 / 0.0215。

登记表达式或插件说明：

```text
-cs_neutralize(cs_neutralize(rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 250) / rolling_sum(turnover, 250), log_cap), rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20))
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-340962041fa34053"></a>

## mw_reversal250_sizeneutral

- ID：`340962041fa34053`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把'筹码实际经历过的平均收益'从 20 日拉到 250 日。20 日版 mw_reversal_vwap20 恰恰是 2021 年全池相对表现最差的成员之一（-0.0193），而同族的长窗口版本按上轮的窗口族单调性诊断应当反向：换手加权的年度累计收益越高，意味着大部分在场筹码都已获利，卖压越重。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0495 / 0.0319。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 250) / rolling_sum(turnover, 250), log_cap)
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-5d0c8acd0c2a6fdf"></a>

## mw_reversal_resid20

- ID：`5d0c8acd0c2a6fdf`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：上一条的纯增量版本：先算资金加权收益，再在截面上对普通20日涨幅做回归取残差。剩下的只有同样涨幅究竟是在放量中完成还是在缩量中完成这一维信息，对应筹码结构的差异。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0389 / 0.0232。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_sum(ret * turnover, 20) / rolling_sum(turnover, 20), cs_rank(close / lag(close, 20) - 1))
```


<a id="f-ba970f639369393e"></a>

## mw_reversal_vwap20

- ID：`ba970f639369393e`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把过去20日收益按当日换手率加权求均值，得到真正被资金承接的那部分涨跌。普通反转把无量的涨跌和放量的涨跌同等看待，但只有伴随大量换手的上涨才意味着大批投资者在高位建仓、随后有解套抛压；用日内均价收益替代收盘价收益还能剔除尾盘拉抬造成的假涨幅。
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0627 / 0.0402。

登记表达式或插件说明：

```text
-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20)
```


<a id="f-5e5d65a6b09efa12"></a>

## overnight_continuation20_sizeneutral

- ID：`5e5d65a6b09efa12`；归属：active_396, research_597, pool_current。
- 机制：日内-隔夜收益差（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：隔夜段是信息段而不是情绪段：A 股的隔夜跳空主要由收盘后的公告、海外市场与基本面消息定价，没有日内的流动性噪声。因此 20 日累计隔夜收益应当延续（正向预测），与日内段的反转方向相反。这条明确**反驳**了上一批复盘 H6 的先验（原假设是隔夜段代表散户情绪、应为负向）。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0183 / 0.0089。

登记表达式或插件说明：

```text
cs_neutralize(rolling_sum(log(open / prev_close), 20), log_cap)
```

- 父因子：[34eda56cb006729b](classic.md#f-34eda56cb006729b)。

<a id="f-2ffa8dc337ff1379"></a>

## overnight_gap_share20

- ID：`2ffa8dc337ff1379`；归属：历史候选，未列入上述集合。
- 机制：隔夜跳空风险（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：隔夜跳空的绝对幅度占全部价格变动的比例，衡量价格调整中有多少发生在没有连续竞价的时段。该比例高说明信息以非交易时段的冲击方式到达、定价不确定性高、散户隔夜情绪主导；比例低说明价格在连续交易中被充分消化。除以总波动是关键——原始的跳空绝对值与20日波动率相关性高达0.72，取比例后才是纯结构信息。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0123 / -0.0062。

登记表达式或插件说明：

```text
-rolling_sum(abs(log(open / prev_close)), 20) / rolling_sum(abs(ret), 20)
```


<a id="f-b1919e60788238e7"></a>

## path_efficiency20

- ID：`b1919e60788238e7`；归属：历史候选，未列入上述集合。
- 机制：路径效率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：净涨幅除以路径总长度，再乘以涨跌方向，度量20日价格移动的效率。平稳单边上行意味着趋势已被充分定价、后续空间有限，而同样涨幅靠反复震荡完成的股票分歧仍在。相比单纯的涨幅，它把怎么涨的纳入了定价。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0439 / 0.0221。

登记表达式或插件说明：

```text
-abs(close / lag(close, 20) - 1) / rolling_sum(abs(ret), 20) * sign(close / lag(close, 20) - 1)
```


<a id="f-d645669a1d681cc4"></a>

## pv_rank_divergence60

- ID：`d645669a1d681cc4`；归属：active_396, research_597, pool_current。
- 机制：量价背离（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把价格和换手各自转成过去20日内的时序分位，再看两者在60日内的同步程度。价格创出相对高位时换手也同步创高，说明上涨靠增量情绪推动而非稳定持有，趋势不可持续；用分位数而非原始值可以剔除各自的量纲和趋势，只保留同步性。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0341 / 0.0176。

登记表达式或插件说明：

```text
-rolling_corr(ts_rank(close, 20), ts_rank(turnover, 20), 60)
```


<a id="f-c2bd16b4ed59759d"></a>

## range_instability60_levelneutral

- ID：`c2bd16b4ed59759d`；归属：active_396, research_597, pool_current。
- 机制：波幅压缩后突破（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：给定相同的近期振幅水平，60 日里振幅本身的波动（振幅的波动，即 vol-of-vol 的价格区间版本）度量的是'这只股票的活跃度有多不稳定'：忽冷忽热者定价环境不连续、存在未消化的事件风险；振幅稳定者定价环境连续。对 20 日振幅均值做横截面残差化，确保不退化成 range20_low。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0155 / 0.0029。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_std(log(high / low), 60), rolling_mean(log(high / low), 20))
```

- 父因子：[974250cf2f6bbb65](classic.md#f-974250cf2f6bbb65)。

<a id="f-e13f3be5870618bf"></a>

## ret_amount_change_corr20_volneutral

- ID：`e13f3be5870618bf`；归属：历史候选，未列入上述集合。
- 机制：量价相关（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：把量价相关性的量方换成'成交额的日度增量'而不是成交额水平：涨的时候放量、跌的时候缩量（相关性高）是典型的追涨情绪结构，后续反转；涨跌都不改变成交额（相关性低）说明存在稳定的对手盘与信息驱动的定价。再对 20 日波动残差化，剥掉波动簇。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0265 / 0.0171。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_corr(ret, delta(log(1 + amount), 1), 20), rolling_std(ret, 20))
```


<a id="f-148e2f00481a616c"></a>

## ret_turnover_corr20

- ID：`148e2f00481a616c`；归属：历史候选，未列入上述集合。
- 机制：量价相关（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：涨时放量、跌时缩量意味着买盘由追涨情绪驱动而非价值判断，这类量价同向的股票随后回落。用换手率而非成交量做相关，等于先按流通股本归一化，消除了股本规模带来的成交量量纲差异，使截面可比。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0295 / 0.0055。

登记表达式或插件说明：

```text
-rolling_corr(ret, turnover, 20)
```


<a id="f-77d726db8cf4dc36"></a>

## size_cond_reversal20

- ID：`77d726db8cf4dc36`；归属：active_396, research_597, pool_current。
- 机制：市值条件反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：小市值股票的投资者结构更散户化、套利资本更受限，过度反应后的修正更彻底，因此反转效应应当随市值下降而增强。用市值截面分位作为反转强度的权重，而不是把市值当独立因子（覆盖图显示 size 单独使用 weak +0.015 且方向会翻转）。
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0444 / 0.0245。

登记表达式或插件说明：

```text
-(close / lag(close, 20) - 1) * (1 - cs_rank(log_cap))
```


<a id="f-0467170e72e97b91"></a>

## size_conditioned_reversal20_centered

- ID：`0467170e72e97b91`；归属：历史候选，未列入上述集合。
- 机制：市值条件反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：反转强度随市值单调变化：小市值股票的 20 日涨幅更多由散户与题材驱动（应更强反转），大市值股票的涨幅更接近基本面重定价。用居中的市值秩（cs_rank − 0.5，正负各半）做乘子，再把基准反转项残差化掉，分离出纯交互项。
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0050 / -0.0213。

登记表达式或插件说明：

```text
-cs_neutralize((close / lag(close, 20) - 1) * (cs_rank(log_cap) - 0.5), close / lag(close, 20) - 1)
```

- 父因子：[77d726db8cf4dc36](llm.md#f-77d726db8cf4dc36)。

<a id="f-2a25201afd560518"></a>

## turn_cond_reversal60

- ID：`2a25201afd560518`；归属：active_396, research_597, pool_current。
- 机制：换手条件反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：同一交互机制搬到 60 日尺度。上轮诊断指出 2021 是长窗口年、短窗口反转集体失效，所以如果换手条件化的反转有价值，它应当在 60 日而不是 20 日尺度上出现：60 日的换手水平刻画的是筹码换手一轮的完整程度，比 20 日更接近'套牢盘是否已经离场'。
- 原判定：weak_signal+style:turnover20；历史均值 / 最差年 RankIC：0.0483 / 0.0372。

登记表达式或插件说明：

```text
-cs_neutralize(cs_rank(close / lag(close, 60) - 1) * (cs_rank(rolling_mean(turnover, 60)) - 0.5), cs_rank(close / lag(close, 60) - 1))
```

- 父因子：[0467170e72e97b91](llm.md#f-0467170e72e97b91)、[0a38584bd0558cdb](classic.md#f-0a38584bd0558cdb)。

<a id="f-48c34d81d9a5a78a"></a>

## turn_cond_reversal_pure20

- ID：`48c34d81d9a5a78a`；归属：历史候选，未列入上述集合。
- 机制：换手条件反转（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：上上轮 H5、上轮 H4，两轮提出从未执行，本批补执行。假设是高换手股票的 20 日反转更强（散户追涨、注意力驱动的过度反应），低换手股票的涨跌更接近信息驱动。写法上把涨跌幅与换手都放到秩空间，再对母因子与换手水平双重残差化，只留下纯交互项。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0140 / -0.0028。

登记表达式或插件说明：

```text
-cs_neutralize(cs_neutralize(cs_rank(close / lag(close, 20) - 1) * (cs_rank(rolling_mean(turnover, 20)) - 0.5), cs_rank(close / lag(close, 20) - 1)), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[0a59417e689c8096](classic.md#f-0a59417e689c8096)、[0a38584bd0558cdb](classic.md#f-0a38584bd0558cdb)。

<a id="f-956dc8377e2b3a5f"></a>

## turnover_autocorr60_levelneutral

- ID：`956dc8377e2b3a5f`；归属：历史候选，未列入上述集合。
- 机制：new:turnover_persistence（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：换手率的一阶自相关度量的是成交的时序形态而非水平：自相关高说明换手是连续的存量博弈、持有人结构被持续搅动；自相关低说明换手由零星事件脉冲驱动、平时无人问津。对 20 日换手水平做横截面残差化后，剩下的是纯形态。训练期显示自相关**低**的股票后续更好，与'脉冲后回归平静 = 关注冲击已消化'一致。
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0077 / -0.0119。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_corr(turnover, lag(turnover, 1), 60), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-02a910e2e61a853c"></a>

## turnover_concentration20

- ID：`02a910e2e61a853c`；归属：历史候选，未列入上述集合。
- 机制：new:turnover_concentration（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：过去20日换手率的赫芬达尔集中度：换手集中在少数几天说明存在关注度冲击（事件、异动、游资脉冲），这类脉冲后的股票被短期情绪定价过高；换手平滑分布说明是持续的机构性交易。取负号后偏好换手分布均匀的股票。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0396 / 0.0176。

登记表达式或插件说明：

```text
-rolling_sum(turnover * turnover, 20) / power(rolling_sum(turnover, 20), 2)
```


<a id="f-c5c09e2de8a450db"></a>

## turnover_concentration_levelfree20

- ID：`c5c09e2de8a450db`；归属：历史候选，未列入上述集合。
- 机制：new:turnover_concentration（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：换手集中度在截面上对换手水平做回归后的残差。高换手股票天然更容易出现集中脉冲，剥掉这一层后剩下的是同等活跃度下交易节奏是否突兀。
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0164 / 0.0014。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_sum(turnover * turnover, 20) / power(rolling_sum(turnover, 20), 2), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-b61a314e9b608564"></a>

## turnover_skew60_levelneutral

- ID：`b61a314e9b608564`；归属：历史候选，未列入上述集合。
- 机制：new:turnover_distribution_shape（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：换手率分布的偏度：右偏严重说明 60 日里多数交易日冷清、少数几天爆量（典型的题材脉冲/游资打板形态）；偏度低说明换手分布均匀。这是与自相关正交的第二个形态统计量——前者管'时序顺序'，后者管'幅度分布'。
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0002 / -0.0161。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_skew(turnover, 60), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-2957b894504948da"></a>

## up_turnover_share20_levelneutral

- ID：`2957b894504948da`；归属：active_396, research_597, pool_current。
- 机制：new:directional_turnover_asymmetry（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：20 日内换手集中在上涨日还是下跌日，度量的是买盘驱动还是卖盘驱动：换手大量发生在上涨日说明筹码是被追涨接走的（高成本筹码堆积，后续抛压），发生在下跌日说明是恐慌出清（低成本筹码换手，后续压力小）。对换手水平残差化，确保测的是方向不对称性本身。
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0255 / 0.0117。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_sum(where(ret > 0, turnover, 0), 20) / rolling_sum(turnover, 20), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-21f1082904b7784e"></a>

## vwap_close_gap20

- ID：`21f1082904b7784e`；归属：active_396, research_597, pool_current。
- 机制：收盘相对均价偏离（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：收盘价持续高于当日成交均价，说明买盘集中在尾盘（拉抬收盘、博弈次日情绪），这部分溢价在次日开盘后回吐；把单日噪声大的偏离在20日上平均后才能提取出稳定的行为倾向。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0269 / 0.0196。

登记表达式或插件说明：

```text
-rolling_mean(close / vwap - 1, 20)
```


<a id="f-53ff5160d7242874"></a>

## vwap_range_position20_amountweighted

- ID：`53ff5160d7242874`；归属：历史候选，未列入上述集合。
- 机制：单笔金额代理（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：没有逐笔数据，但 vwap 在当日 [low, high] 区间中的相对位置直接度量'当天绝大部分成交发生在高位还是低位'，即当日新增筹码的平均成本位置；用成交额加权做 20 日聚合，让放量日的位置权重更高。持续在区间高位成交 = 追高接盘、套牢盘在上方；持续在低位成交 = 承接盘在下方。
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0176 / 0.0075。

登记表达式或插件说明：

```text
-cs_neutralize(rolling_sum(where(high > low, (2 * vwap - high - low) / (high - low), 0) * amount, 20) / rolling_sum(amount, 20), log_cap)
```
