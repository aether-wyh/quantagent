# 因子定义、计算语义与阅读口径

[目录总览](README.md) · [日频396](ACTIVE_396.md) · [研究597](RESEARCH_597.md)

## 三种因子定义

1. **DSL 表达式**：`canonical` 是当前计算器实际求值的规范式，`expression` 是登记原式。字段与算子定义见 [dsl.py](../../src/quanta_agents/factor_lab_a/dsl.py)。
2. **外部插件**：`plugin` 指向 Alpha101、Alpha191 或因子日历函数；`expression` 保存原公式或说明，`transform` 保存按顺序执行的后续变换。它不是可直接传给 DSL 的公式。外部库不随本目录提供，计算语义还取决于 [external.py](../../src/quanta_agents/factor_lab_a/external.py) 的适配。
3. **交叉复合**：`composite` 保存算子和有序父因子 ID。父因子可能继续依赖其他父因子，全部登记定义均收录在 [catalog.json](../../research/factors/catalog.json) 中，详情页可沿父代链接查看。不要把 `composite:sum(...)` 当成直接可运行的 Python。

`source` 是生成来源，`mechanism_id` 是登记时的研究标签。遗传规划、Alpha101/191、交叉复合的标签并不等于单一经济机制；本次没有根据因子名称猜测并重分类。

## 方向和排名

单因子评价用 2016—2018 训练年确定方向。冻结方向是 `+1` 或 `-1`，作用于完整公式的输出；公式本身已有负号时也仍须按记录执行，不能再凭名称人工改方向。

日频模型读取在可选池内逐日计算的百分位排名。当前日更脚本给 396 成员生成全 A 排名；之后组合规则才限制具体指数范围。目录没有把这两种股票池口径混为一谈。

交叉因子先递归计算父因子，每个父因子乘自己的冻结方向、在当日评价池内排名，得到 `rx`、`ry`；复合结果在作为模型输入时再应用该子因子的方向和排名。准确路径见 [compute_candidate](../../src/quanta_agents/factor_lab_a/cli.py) 与 [live.py](../../src/quanta_agents/factor_lab_a/live.py)。

## 交叉算子的准确含义

以下按照实际函数体整理，而非只抄模块注释。`NaN` 表示缺失。

| 算子 | 对父因子百分位排名的运算 | 含义 |
|---|---|---|
| `sum` | `rx + ry` | 两个排名相加；函数本身不除以2 |
| `prod` | `(rx-0.5)*(ry-0.5)` | 中心化排名交互 |
| `gate_hi` | `ry > 0.5` 时保留 `rx`，其余为 `NaN` | 高位条件门控；其余不是零 |
| `gate_lo` | `ry <= 0.5` 时保留 `rx`，其余为 `NaN` | 低位条件门控；其余不是零 |
| `min` | `min(rx, ry)` | 两个排名取较小者 |
| `diff` | `rx - ry` | 两个排名的差 |
| `resid` | 当日共同有效样本上，`(rx-mean(rx)) - beta*(ry-mean(ry))` | 带截距单变量回归残差；分母有数值下限 |

原实现：[crossover.py](../../src/quanta_agents/factor_lab_a/crossover.py)。

## 程序改造与变换链

| 变换 | 作用 |
|---|---|
| `neut_cap` | 对对数流通市值做截面中性化 |
| `neut_turn` | 对20日平均换手率的截面排名中性化 |
| `neut_vol` | 对20日收益波动率的截面排名中性化 |
| `ema5` / `ema10` | 5日 / 10日指数平滑 |
| `tsz60` | 60日时序标准化 |
| `slog` | 保留符号的对数压缩 |
| `rank` | 截面百分位排名 |
| `resid_rev20` | 剥离20日价格涨幅的截面线性影响 |
| `delta5` | 5日变化 |
| `tsrank60` | 60日时序排名 |

精确模板见 [transforms.json](../../research/factors/transforms.json)；计算函数见 [expand.py](../../src/quanta_agents/factor_lab_a/expand.py)。窗口变体已写进各成员的表达式，不需要再凭父代名称推断窗口。

## 日频字段

| 字段 | 当前面板定义 |
|---|---|
| `open/high/low/close` | 研究面板价格字段；需与所用复权口径一致 |
| `volume/amount` | 成交量 / 成交额；单位由数据适配保持一致 |
| `vwap` | 面板的 `vwap_qfq` 字段 |
| `turnover` | `volume / float_shares` |
| `ret` | `close / prev_close - 1` |
| `float_shares/total_shares` | 流通股本 / 总股本 |
| `float_market_cap/total_market_cap` | 流通市值 / 总市值 |
| `log_cap/log_total_cap` | 对应市值取自然对数 |
| `mkt_ret` | 当日可选股池收益的等权均值，广播至股票列 |

具体定义见 [panel.py](../../src/quanta_agents/factor_lab_a/panel.py)。`mkt_ret` 不是某个官方指数的收益。时间窗口作用于交易日面板的行，不是自然日。

## 分钟聚合字段

研究扩展版使用的 `im_` 字段由分钟数据聚合成日频特征，再经过均值、平滑、标准化或交叉等变换。分钟基础字段数量、由其生成的候选数量、最终模型成员数量是三个不同概念。

- 时段收益：开盘半小时、收盘半小时、上午、下午、中间时段、最后一分钟。
- 成交分布：各时段量占比、成交时间重心、集中度、离散度。
- 路径与风险：已实现方差、上下行半方差比、偏度、峰度、极端分钟收益、回撤、路径效率。
- 量价关系：分钟收益与成交量的同期/滞后相关、收盘相对均价偏离。
- 大成交分钟代理：按分钟成交额分组后的收益差、均价偏离与成交额占比；它们不是逐笔大单或 Level 2 真实资金流。

字段和过滤规则见 [minute_features.py](../../src/quanta_agents/factor_lab_a/minute_features.py)。研究扩展版的存在不表示当前日频链路具备完整分钟数据更新能力。

## 外部公式与本项目实现的区别

Alpha101/191 的公式保留来源标识；因子日历的登记文本可能只是说明，不是完整公式。带插件的变体必须同时保留插件标识和变换链。

当前适配器的 `INDNEUTRALIZE` 用截面去均值近似，并非真实行业中性化；`ADVn` 取成交额的滚动均值；基准收益代理来自本项目 `mkt_ret`。这些实现差异意味着不能把本项目结果直接称为原论文或原库的严格复现。详情记录保留 `approx_indneutralize`，交叉成员还需沿父代检查差异。

外部实现依赖见 [仓库范围与迁移说明](../REPOSITORY_CONTENTS.md)。本次整理没有新增第三方实现源码，也没有改变既有许可范围。

## 评价指标与研究结论

`evaluation` 是保存结果的摘录，不是本次重算。主要单因子标签是次日开盘起五日收益 `open[t+6]/open[t+1]-1`；组合训练另有5/10/20日标签融合，两者不要混用。

- 历史均值 / 最差年 RankIC：已保存的2019—2024逐年截面统计，且这些历史已反复用于筛选。
- `train_t`：原程序保存的训练期统计量；未在本次整理中增加自相关或多重比较校正。
- `failure_class`、原假设和机制解释：保留研究当时的记录，不代表该因果机制已获证实。
- `evaluation.in_pool`：历史评价标记；`membership.pool_current`：本次按照实际池文件取得的身份。
- 缺失评价与缺失指标保留为空；未把登记时的 `pending` 当作现在仍未评价。

不能用这些单因子 IC 排名替代家族删减、组合增量、指数内部表现或独立样本外验证。本次没有新增策略收益结论。
