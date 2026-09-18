# Alpha158 简化集

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-7fbffdd044687a8a"></a>

## BETA10

- ID：`7fbffdd044687a8a`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0004 / -0.0204。

登记表达式或插件说明：

```text
rolling_beta(close / lag(close, 1) - 1, mkt_ret, 10)
```


<a id="f-3fe86a03ef488789"></a>

## BETA20

- ID：`3fe86a03ef488789`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0021 / -0.0145。

登记表达式或插件说明：

```text
rolling_beta(close / lag(close, 1) - 1, mkt_ret, 20)
```


<a id="f-467f5154dde6dde1"></a>

## BETA30

- ID：`467f5154dde6dde1`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0004 / -0.0163。

登记表达式或插件说明：

```text
rolling_beta(close / lag(close, 1) - 1, mkt_ret, 30)
```


<a id="f-1e5e634531c48436"></a>

## BETA5

- ID：`1e5e634531c48436`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0039 / -0.0167。

登记表达式或插件说明：

```text
rolling_beta(close / lag(close, 1) - 1, mkt_ret, 5)
```


<a id="f-80f857e58a46b257"></a>

## BETA60

- ID：`80f857e58a46b257`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0090 / -0.0027。

登记表达式或插件说明：

```text
rolling_beta(close / lag(close, 1) - 1, mkt_ret, 60)
```


<a id="f-ab138ebfba1538e2"></a>

## CNTP10

- ID：`ab138ebfba1538e2`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0207 / 0.0099。

登记表达式或插件说明：

```text
rolling_mean(where(close > lag(close, 1), 1, 0), 10)
```


<a id="f-3f21291d84c5aba9"></a>

## CNTP20

- ID：`3f21291d84c5aba9`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0238 / 0.0093。

登记表达式或插件说明：

```text
rolling_mean(where(close > lag(close, 1), 1, 0), 20)
```


<a id="f-c93ed30702fbeda3"></a>

## CNTP30

- ID：`c93ed30702fbeda3`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0252 / 0.0169。

登记表达式或插件说明：

```text
rolling_mean(where(close > lag(close, 1), 1, 0), 30)
```


<a id="f-ccba33d171a7f72e"></a>

## CNTP5

- ID：`ccba33d171a7f72e`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0183 / 0.0115。

登记表达式或插件说明：

```text
rolling_mean(where(close > lag(close, 1), 1, 0), 5)
```


<a id="f-2e40f75d080beba4"></a>

## CNTP60

- ID：`2e40f75d080beba4`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0237 / 0.0101。

登记表达式或插件说明：

```text
rolling_mean(where(close > lag(close, 1), 1, 0), 60)
```


<a id="f-f093e783971a421d"></a>

## CORD10

- ID：`f093e783971a421d`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0367 / 0.0209。

登记表达式或插件说明：

```text
rolling_corr(close / lag(close, 1), log(volume / lag(volume, 1) + 1), 10)
```


<a id="f-686b80a78e332a4b"></a>

## CORD20

- ID：`686b80a78e332a4b`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0439 / 0.0305。

登记表达式或插件说明：

```text
rolling_corr(close / lag(close, 1), log(volume / lag(volume, 1) + 1), 20)
```


<a id="f-119b65bd0b2e19a8"></a>

## CORD30

- ID：`119b65bd0b2e19a8`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0439 / 0.0353。

登记表达式或插件说明：

```text
rolling_corr(close / lag(close, 1), log(volume / lag(volume, 1) + 1), 30)
```


<a id="f-8497ea13338f7e94"></a>

## CORD5

- ID：`8497ea13338f7e94`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0276 / 0.0115。

登记表达式或插件说明：

```text
rolling_corr(close / lag(close, 1), log(volume / lag(volume, 1) + 1), 5)
```


<a id="f-aa962775d5f31f70"></a>

## CORD60

- ID：`aa962775d5f31f70`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0370 / 0.0263。

登记表达式或插件说明：

```text
rolling_corr(close / lag(close, 1), log(volume / lag(volume, 1) + 1), 60)
```


<a id="f-a85fe4eb6df04f8f"></a>

## CORR10

- ID：`a85fe4eb6df04f8f`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0465 / 0.0308。

登记表达式或插件说明：

```text
rolling_corr(close, log(volume + 1), 10)
```


<a id="f-7a27cf4d56acc6c1"></a>

## CORR20

- ID：`7a27cf4d56acc6c1`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0490 / 0.0254。

登记表达式或插件说明：

```text
rolling_corr(close, log(volume + 1), 20)
```


<a id="f-42e4929ffaff9082"></a>

## CORR30

- ID：`42e4929ffaff9082`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0437 / 0.0244。

登记表达式或插件说明：

```text
rolling_corr(close, log(volume + 1), 30)
```


<a id="f-1f2c516c4d75fa67"></a>

## CORR5

- ID：`1f2c516c4d75fa67`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0356 / 0.0199。

登记表达式或插件说明：

```text
rolling_corr(close, log(volume + 1), 5)
```


<a id="f-748cfa40fb17ffd7"></a>

## CORR60

- ID：`748cfa40fb17ffd7`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0228 / 0.0073。

登记表达式或插件说明：

```text
rolling_corr(close, log(volume + 1), 60)
```


<a id="f-68433eac3e8c938b"></a>

## KLEN

- ID：`68433eac3e8c938b`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0689 / 0.0583。

登记表达式或插件说明：

```text
(high - low) / open
```


<a id="f-9df8a01359690d9b"></a>

## KLOW

- ID：`9df8a01359690d9b`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0333 / 0.0222。

登记表达式或插件说明：

```text
(min(open, close) - low) / open
```


<a id="f-9c87d7ee86ab67f5"></a>

## KMID

- ID：`9c87d7ee86ab67f5`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0185 / 0.0091。

登记表达式或插件说明：

```text
(close - open) / open
```


<a id="f-f5ff61a146a6a3ae"></a>

## KMID2

- ID：`f5ff61a146a6a3ae`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0151 / 0.0085。

登记表达式或插件说明：

```text
(close - open) / (high - low + 1e-12)
```


<a id="f-2b5f6357829958cf"></a>

## KSFT

- ID：`2b5f6357829958cf`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0114 / -0.0028。

登记表达式或插件说明：

```text
(2 * close - high - low) / open
```


<a id="f-9df000fc679a3d26"></a>

## KUP

- ID：`9df000fc679a3d26`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0281 / 0.0170。

登记表达式或插件说明：

```text
(high - max(open, close)) / open
```


<a id="f-305430ae780c9927"></a>

## MA10

- ID：`305430ae780c9927`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0346 / 0.0253。

登记表达式或插件说明：

```text
rolling_mean(close, 10) / close
```


<a id="f-8856b025a235b657"></a>

## MA20

- ID：`8856b025a235b657`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0474 / 0.0314。

登记表达式或插件说明：

```text
rolling_mean(close, 20) / close
```


<a id="f-f0fa5ea02fff0251"></a>

## MA30

- ID：`f0fa5ea02fff0251`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0536 / 0.0325。

登记表达式或插件说明：

```text
rolling_mean(close, 30) / close
```


<a id="f-1c0e9535dd74ca15"></a>

## MA5

- ID：`1c0e9535dd74ca15`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0232 / 0.0097。

登记表达式或插件说明：

```text
rolling_mean(close, 5) / close
```


<a id="f-e8ee3bf4a239105c"></a>

## MA60

- ID：`e8ee3bf4a239105c`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0612 / 0.0362。

登记表达式或插件说明：

```text
rolling_mean(close, 60) / close
```


<a id="f-eaa34f1e2b3c837f"></a>

## MAX10

- ID：`eaa34f1e2b3c837f`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0201 / 0.0076。

登记表达式或插件说明：

```text
rolling_max(high, 10) / close
```


<a id="f-c6402d22da40c933"></a>

## MAX20

- ID：`c6402d22da40c933`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0101 / -0.0201。

登记表达式或插件说明：

```text
rolling_max(high, 20) / close
```


<a id="f-042e2f3b312215c7"></a>

## MAX30

- ID：`042e2f3b312215c7`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal+style:mom20；历史均值 / 最差年 RankIC：-0.0016 / -0.0147。

登记表达式或插件说明：

```text
rolling_max(high, 30) / close
```


<a id="f-9db8c3316b9bbbee"></a>

## MAX5

- ID：`9db8c3316b9bbbee`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0273 / 0.0185。

登记表达式或插件说明：

```text
rolling_max(high, 5) / close
```


<a id="f-e3d7dd9293340c04"></a>

## MAX60

- ID：`e3d7dd9293340c04`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0077 / -0.0175。

登记表达式或插件说明：

```text
rolling_max(high, 60) / close
```


<a id="f-ffbe143644b9ffa7"></a>

## MIN10

- ID：`ffbe143644b9ffa7`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0561 / 0.0415。

登记表达式或插件说明：

```text
rolling_min(low, 10) / close
```


<a id="f-5835c779ac09bccb"></a>

## MIN20

- ID：`5835c779ac09bccb`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0580 / 0.0415。

登记表达式或插件说明：

```text
rolling_min(low, 20) / close
```


<a id="f-8d739b585da6211a"></a>

## MIN30

- ID：`8d739b585da6211a`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0604 / 0.0386。

登记表达式或插件说明：

```text
rolling_min(low, 30) / close
```


<a id="f-2e17e56025c94a6a"></a>

## MIN5

- ID：`2e17e56025c94a6a`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0535 / 0.0421。

登记表达式或插件说明：

```text
rolling_min(low, 5) / close
```


<a id="f-90490c808bf7bc6a"></a>

## MIN60

- ID：`90490c808bf7bc6a`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0657 / 0.0446。

登记表达式或插件说明：

```text
rolling_min(low, 60) / close
```


<a id="f-80800fc9e7f2080f"></a>

## ROC10

- ID：`80800fc9e7f2080f`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0422 / 0.0269。

登记表达式或插件说明：

```text
lag(close, 10) / close
```


<a id="f-3755d5ab08f0444f"></a>

## ROC20

- ID：`3755d5ab08f0444f`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0520 / 0.0313。

登记表达式或插件说明：

```text
lag(close, 20) / close
```


<a id="f-bca33c6ac985e7ff"></a>

## ROC30

- ID：`bca33c6ac985e7ff`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0567 / 0.0370。

登记表达式或插件说明：

```text
lag(close, 30) / close
```


<a id="f-8e77c019b015690a"></a>

## ROC5

- ID：`8e77c019b015690a`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0306 / 0.0176。

登记表达式或插件说明：

```text
lag(close, 5) / close
```


<a id="f-4ba26da7b2eb9eb8"></a>

## ROC60

- ID：`4ba26da7b2eb9eb8`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0521 / 0.0294。

登记表达式或插件说明：

```text
lag(close, 60) / close
```


<a id="f-17f7fa9c45cdd919"></a>

## RSV10

- ID：`17f7fa9c45cdd919`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0191 / 0.0016。

登记表达式或插件说明：

```text
(close - rolling_min(low, 10)) / (rolling_max(high, 10) - rolling_min(low, 10) + 1e-12)
```


<a id="f-eafe2ff7398f0383"></a>

## RSV20

- ID：`eafe2ff7398f0383`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0255 / 0.0040。

登记表达式或插件说明：

```text
(close - rolling_min(low, 20)) / (rolling_max(high, 20) - rolling_min(low, 20) + 1e-12)
```


<a id="f-a2f5c6843f84a9a8"></a>

## RSV30

- ID：`a2f5c6843f84a9a8`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0315 / 0.0060。

登记表达式或插件说明：

```text
(close - rolling_min(low, 30)) / (rolling_max(high, 30) - rolling_min(low, 30) + 1e-12)
```


<a id="f-29cd5f01126b8392"></a>

## RSV5

- ID：`29cd5f01126b8392`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0131 / -0.0006。

登记表达式或插件说明：

```text
(close - rolling_min(low, 5)) / (rolling_max(high, 5) - rolling_min(low, 5) + 1e-12)
```


<a id="f-e8e3f07e045f395e"></a>

## RSV60

- ID：`e8e3f07e045f395e`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0401 / 0.0093。

登记表达式或插件说明：

```text
(close - rolling_min(low, 60)) / (rolling_max(high, 60) - rolling_min(low, 60) + 1e-12)
```


<a id="f-9724ae42a7a2a76a"></a>

## STD10

- ID：`9724ae42a7a2a76a`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0612 / 0.0497。

登记表达式或插件说明：

```text
rolling_std(close, 10) / close
```


<a id="f-542fd07091c671a2"></a>

## STD20

- ID：`542fd07091c671a2`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0528 / 0.0414。

登记表达式或插件说明：

```text
rolling_std(close, 20) / close
```


<a id="f-b131bc56daed3fda"></a>

## STD30

- ID：`b131bc56daed3fda`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal+style:vol20；历史均值 / 最差年 RankIC：0.0464 / 0.0377。

登记表达式或插件说明：

```text
rolling_std(close, 30) / close
```


<a id="f-899edb9b192e99b5"></a>

## STD5

- ID：`899edb9b192e99b5`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0595 / 0.0498。

登记表达式或插件说明：

```text
rolling_std(close, 5) / close
```


<a id="f-d5bce85a42a50730"></a>

## STD60

- ID：`d5bce85a42a50730`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0344 / 0.0220。

登记表达式或插件说明：

```text
rolling_std(close, 60) / close
```


<a id="f-a6e7b4c16a485da8"></a>

## SUMP10

- ID：`a6e7b4c16a485da8`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0329 / 0.0151。

登记表达式或插件说明：

```text
rolling_sum(max(close - lag(close, 1), 0), 10) / (rolling_sum(abs(close - lag(close, 1)), 10) + 1e-12)
```


<a id="f-19f0b9c4aaace6ed"></a>

## SUMP20

- ID：`19f0b9c4aaace6ed`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0426 / 0.0205。

登记表达式或插件说明：

```text
rolling_sum(max(close - lag(close, 1), 0), 20) / (rolling_sum(abs(close - lag(close, 1)), 20) + 1e-12)
```


<a id="f-3b02501d42b7577b"></a>

## SUMP30

- ID：`3b02501d42b7577b`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0485 / 0.0290。

登记表达式或插件说明：

```text
rolling_sum(max(close - lag(close, 1), 0), 30) / (rolling_sum(abs(close - lag(close, 1)), 30) + 1e-12)
```


<a id="f-fcbac892ac009d2e"></a>

## SUMP5

- ID：`fcbac892ac009d2e`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0230 / 0.0107。

登记表达式或插件说明：

```text
rolling_sum(max(close - lag(close, 1), 0), 5) / (rolling_sum(abs(close - lag(close, 1)), 5) + 1e-12)
```


<a id="f-24175ada2865f7d3"></a>

## SUMP60

- ID：`24175ada2865f7d3`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0472 / 0.0238。

登记表达式或插件说明：

```text
rolling_sum(max(close - lag(close, 1), 0), 60) / (rolling_sum(abs(close - lag(close, 1)), 60) + 1e-12)
```


<a id="f-e655e9bb6b1ff7aa"></a>

## VMA10

- ID：`e655e9bb6b1ff7aa`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0179 / 0.0128。

登记表达式或插件说明：

```text
rolling_mean(volume, 10) / (volume + 1e-12)
```


<a id="f-9659c69373fd08c3"></a>

## VMA20

- ID：`9659c69373fd08c3`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0284 / 0.0085。

登记表达式或插件说明：

```text
rolling_mean(volume, 20) / (volume + 1e-12)
```


<a id="f-910bffba97cda0bb"></a>

## VMA30

- ID：`910bffba97cda0bb`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0346 / 0.0101。

登记表达式或插件说明：

```text
rolling_mean(volume, 30) / (volume + 1e-12)
```


<a id="f-9c9e5f8351e962ed"></a>

## VMA5

- ID：`9c9e5f8351e962ed`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0111 / 0.0077。

登记表达式或插件说明：

```text
rolling_mean(volume, 5) / (volume + 1e-12)
```


<a id="f-bbae861781258362"></a>

## VMA60

- ID：`bbae861781258362`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0474 / 0.0290。

登记表达式或插件说明：

```text
rolling_mean(volume, 60) / (volume + 1e-12)
```


<a id="f-4db257e4bdc02fea"></a>

## VSTD10

- ID：`4db257e4bdc02fea`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0113 / -0.0011。

登记表达式或插件说明：

```text
rolling_std(volume, 10) / (volume + 1e-12)
```


<a id="f-5b03f854e141c091"></a>

## VSTD20

- ID：`5b03f854e141c091`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0021 / -0.0086。

登记表达式或插件说明：

```text
rolling_std(volume, 20) / (volume + 1e-12)
```


<a id="f-8ae417fe6b339293"></a>

## VSTD30

- ID：`8ae417fe6b339293`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0115 / -0.0227。

登记表达式或插件说明：

```text
rolling_std(volume, 30) / (volume + 1e-12)
```


<a id="f-edd9a7a55cab2204"></a>

## VSTD5

- ID：`edd9a7a55cab2204`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0170 / 0.0056。

登记表达式或插件说明：

```text
rolling_std(volume, 5) / (volume + 1e-12)
```


<a id="f-8179e2b737c80ceb"></a>

## VSTD60

- ID：`8179e2b737c80ceb`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0332 / 0.0101。

登记表达式或插件说明：

```text
rolling_std(volume, 60) / (volume + 1e-12)
```


<a id="f-513572d57cc609cd"></a>

## VSUMP10

- ID：`513572d57cc609cd`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0253 / 0.0111。

登记表达式或插件说明：

```text
rolling_sum(max(volume - lag(volume, 1), 0), 10) / (rolling_sum(abs(volume - lag(volume, 1)), 10) + 1e-12)
```


<a id="f-979ffcd165399405"></a>

## VSUMP20

- ID：`979ffcd165399405`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0358 / 0.0098。

登记表达式或插件说明：

```text
rolling_sum(max(volume - lag(volume, 1), 0), 20) / (rolling_sum(abs(volume - lag(volume, 1)), 20) + 1e-12)
```


<a id="f-3bf889c05278f573"></a>

## VSUMP30

- ID：`3bf889c05278f573`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0411 / 0.0226。

登记表达式或插件说明：

```text
rolling_sum(max(volume - lag(volume, 1), 0), 30) / (rolling_sum(abs(volume - lag(volume, 1)), 30) + 1e-12)
```


<a id="f-98db26e76f8096f3"></a>

## VSUMP5

- ID：`98db26e76f8096f3`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0175 / 0.0125。

登记表达式或插件说明：

```text
rolling_sum(max(volume - lag(volume, 1), 0), 5) / (rolling_sum(abs(volume - lag(volume, 1)), 5) + 1e-12)
```


<a id="f-a56d5ae7fab087b7"></a>

## VSUMP60

- ID：`a56d5ae7fab087b7`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0499 / 0.0350。

登记表达式或插件说明：

```text
rolling_sum(max(volume - lag(volume, 1), 0), 60) / (rolling_sum(abs(volume - lag(volume, 1)), 60) + 1e-12)
```


<a id="f-46c714acefaea502"></a>

## WVMA10

- ID：`46c714acefaea502`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0120 / 0.0054。

登记表达式或插件说明：

```text
rolling_std(abs(close / lag(close, 1) - 1) * volume, 10) / (rolling_mean(abs(close / lag(close, 1) - 1) * volume, 10) + 1e-12)
```


<a id="f-7da16373b59329f1"></a>

## WVMA20

- ID：`7da16373b59329f1`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0142 / 0.0024。

登记表达式或插件说明：

```text
rolling_std(abs(close / lag(close, 1) - 1) * volume, 20) / (rolling_mean(abs(close / lag(close, 1) - 1) * volume, 20) + 1e-12)
```


<a id="f-7be333d743e8ecd8"></a>

## WVMA30

- ID：`7be333d743e8ecd8`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0154 / 0.0045。

登记表达式或插件说明：

```text
rolling_std(abs(close / lag(close, 1) - 1) * volume, 30) / (rolling_mean(abs(close / lag(close, 1) - 1) * volume, 30) + 1e-12)
```


<a id="f-afe49aa393d90d33"></a>

## WVMA5

- ID：`afe49aa393d90d33`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0064 / 0.0026。

登记表达式或插件说明：

```text
rolling_std(abs(close / lag(close, 1) - 1) * volume, 5) / (rolling_mean(abs(close / lag(close, 1) - 1) * volume, 5) + 1e-12)
```


<a id="f-479e34938bc73275"></a>

## WVMA60

- ID：`479e34938bc73275`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：Alpha158-lite feature
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0115 / 0.0011。

登记表达式或插件说明：

```text
rolling_std(abs(close / lag(close, 1) - 1) * volume, 60) / (rolling_mean(abs(close / lag(close, 1) - 1) * volume, 60) + 1e-12)
```
