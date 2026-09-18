# 程序改造

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-7ba6292066737e87"></a>

## KLEN~ema5

- ID：`7ba6292066737e87`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 68433eac3e8c938b (ema5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0829 / 0.0709。

登记表达式或插件说明：

```text
ema(((high - low) / open), 5)
```

规范式 / 计算标识：

```text
ema((high - low) / open, 5)
```

- 父因子：[68433eac3e8c938b](alpha158.md#f-68433eac3e8c938b)。

<a id="f-c1ec19445a99fbe6"></a>

## MIN10~ema5

- ID：`c1ec19445a99fbe6`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ffbe143644b9ffa7 (ema5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0633 / 0.0420。

登记表达式或插件说明：

```text
ema((rolling_min(low, 10) / close), 5)
```

规范式 / 计算标识：

```text
ema(rolling_min(low, 10) / close, 5)
```

- 父因子：[ffbe143644b9ffa7](alpha158.md#f-ffbe143644b9ffa7)。

<a id="f-de081f770fdf85dc"></a>

## MIN10~resid_rev20

- ID：`de081f770fdf85dc`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ffbe143644b9ffa7 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0384 / 0.0244。

登记表达式或插件说明：

```text
cs_neutralize((rolling_min(low, 10) / close), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_min(low, 10) / close, close / lag(close, 20) - 1)
```

- 父因子：[ffbe143644b9ffa7](alpha158.md#f-ffbe143644b9ffa7)。

<a id="f-c3c92cef89b0ef03"></a>

## MIN20~ema10

- ID：`c3c92cef89b0ef03`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 5835c779ac09bccb (ema10)
- 原判定：pass_mean+style:vol20,mom20；历史均值 / 最差年 RankIC：0.0633 / 0.0382。

登记表达式或插件说明：

```text
ema((rolling_min(low, 20) / close), 10)
```

规范式 / 计算标识：

```text
ema(rolling_min(low, 20) / close, 10)
```

- 父因子：[5835c779ac09bccb](alpha158.md#f-5835c779ac09bccb)。

<a id="f-3f66f7889da7b6db"></a>

## MIN5~delta5

- ID：`3f66f7889da7b6db`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 2e17e56025c94a6a (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0141 / -0.0136。

登记表达式或插件说明：

```text
delta((rolling_min(low, 5) / close), 5)
```

规范式 / 计算标识：

```text
delta(rolling_min(low, 5) / close, 5)
```

- 父因子：[2e17e56025c94a6a](alpha158.md#f-2e17e56025c94a6a)。

<a id="f-1b489067a189a2ca"></a>

## MIN5~neut_turn

- ID：`1b489067a189a2ca`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 2e17e56025c94a6a (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0334 / 0.0183。

登记表达式或插件说明：

```text
cs_neutralize((rolling_min(low, 5) / close), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_min(low, 5) / close, cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[2e17e56025c94a6a](alpha158.md#f-2e17e56025c94a6a)。

<a id="f-623b23ae30c6ef9b"></a>

## MIN5~resid_rev20

- ID：`623b23ae30c6ef9b`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 2e17e56025c94a6a (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0361 / 0.0186。

登记表达式或插件说明：

```text
cs_neutralize((rolling_min(low, 5) / close), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_min(low, 5) / close, close / lag(close, 20) - 1)
```

- 父因子：[2e17e56025c94a6a](alpha158.md#f-2e17e56025c94a6a)。

<a id="f-ab1b4d19b5df4a46"></a>

## MIN5~tsrank60

- ID：`ab1b4d19b5df4a46`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 2e17e56025c94a6a (tsrank60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0246 / 0.0150。

登记表达式或插件说明：

```text
ts_rank((rolling_min(low, 5) / close), 60)
```

规范式 / 计算标识：

```text
ts_rank(rolling_min(low, 5) / close, 60)
```

- 父因子：[2e17e56025c94a6a](alpha158.md#f-2e17e56025c94a6a)。

<a id="f-75cb313bae316ad2"></a>

## MIN5~w0.5

- ID：`75cb313bae316ad2`；归属：active_396, research_597, pool_current。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 2e17e56025c94a6a (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0509 / 0.0439。

登记表达式或插件说明：

```text
rolling_min(low, 2) / close
```

- 父因子：[2e17e56025c94a6a](alpha158.md#f-2e17e56025c94a6a)。

<a id="f-ede631d6f3dbbfc7"></a>

## MIN60~delta5

- ID：`ede631d6f3dbbfc7`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 90490c808bf7bc6a (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0197 / 0.0028。

登记表达式或插件说明：

```text
delta((rolling_min(low, 60) / close), 5)
```

规范式 / 计算标识：

```text
delta(rolling_min(low, 60) / close, 5)
```

- 父因子：[90490c808bf7bc6a](alpha158.md#f-90490c808bf7bc6a)。

<a id="f-c1adf785094fac49"></a>

## ROC30~delta5

- ID：`c1adf785094fac49`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of bca33c6ac985e7ff (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0201 / 0.0059。

登记表达式或插件说明：

```text
delta((lag(close, 30) / close), 5)
```

规范式 / 计算标识：

```text
delta(lag(close, 30) / close, 5)
```

- 父因子：[bca33c6ac985e7ff](alpha158.md#f-bca33c6ac985e7ff)。

<a id="f-4f8c69294e5fafbc"></a>

## STD20~neut_turn

- ID：`4f8c69294e5fafbc`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 542fd07091c671a2 (neut_turn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0150 / -0.0233。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(close, 20) / close), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(close, 20) / close, cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[542fd07091c671a2](alpha158.md#f-542fd07091c671a2)。

<a id="f-8385bb2ad9d1be2e"></a>

## STD20~neut_vol

- ID：`8385bb2ad9d1be2e`；归属：历史候选，未列入上述集合。
- 机制：alpha158（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 542fd07091c671a2 (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0121 / -0.0020。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(close, 20) / close), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(close, 20) / close, cs_rank(rolling_std(ret, 20)))
```

- 父因子：[542fd07091c671a2](alpha158.md#f-542fd07091c671a2)。

<a id="f-72208174b67604ef"></a>

## amihud~ema10~delta5

- ID：`72208174b67604ef`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of f7d7b129d6cecf3d (delta5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0356 / 0.0173。

登记表达式或插件说明：

```text
delta((ema(im_amihud, 10)), 5)
```

规范式 / 计算标识：

```text
delta(ema(im_amihud, 10), 5)
```

- 父因子：[f7d7b129d6cecf3d](minute.md#f-f7d7b129d6cecf3d)。

<a id="f-00c305ed0527261d"></a>

## amihud~ema10~neut_cap

- ID：`00c305ed0527261d`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of f7d7b129d6cecf3d (neut_cap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0671 / 0.0499。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_amihud, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_amihud, 10), log_cap)
```

- 父因子：[f7d7b129d6cecf3d](minute.md#f-f7d7b129d6cecf3d)。

<a id="f-332a710c76455985"></a>

## amihud~ema10~tsz60

- ID：`332a710c76455985`；归属：research_597, pool_current。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of f7d7b129d6cecf3d (tsz60)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0547 / 0.0354。

登记表达式或插件说明：

```text
ts_zscore((ema(im_amihud, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_amihud, 10), 60)
```

- 父因子：[f7d7b129d6cecf3d](minute.md#f-f7d7b129d6cecf3d)。

<a id="f-ec5237e8ee48a95a"></a>

## amihud~ema10~w0.5

- ID：`ec5237e8ee48a95a`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of f7d7b129d6cecf3d (w0.5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0645 / 0.0365。

登记表达式或插件说明：

```text
ema(im_amihud, 5)
```

- 父因子：[f7d7b129d6cecf3d](minute.md#f-f7d7b129d6cecf3d)。

<a id="f-ab74d9a58372fa6d"></a>

## big_vwap_dev~ema10~delta5

- ID：`ab74d9a58372fa6d`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 761c35fb95139218 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0152 / 0.0060。

登记表达式或插件说明：

```text
delta((ema(im_big_vwap_dev, 10)), 5)
```

规范式 / 计算标识：

```text
delta(ema(im_big_vwap_dev, 10), 5)
```

- 父因子：[761c35fb95139218](minute.md#f-761c35fb95139218)。

<a id="f-08273374bcaf4bc7"></a>

## big_vwap_dev~ema10~tsz60

- ID：`08273374bcaf4bc7`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 761c35fb95139218 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0296 / 0.0151。

登记表达式或插件说明：

```text
ts_zscore((ema(im_big_vwap_dev, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_big_vwap_dev, 10), 60)
```

- 父因子：[761c35fb95139218](minute.md#f-761c35fb95139218)。

<a id="f-b7470cd13bc34985"></a>

## big_vwap_dev~s20~delta5

- ID：`b7470cd13bc34985`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0b193b55a101b661 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0193 / 0.0058。

登记表达式或插件说明：

```text
delta((rolling_std(im_big_vwap_dev, 20)), 5)
```

规范式 / 计算标识：

```text
delta(rolling_std(im_big_vwap_dev, 20), 5)
```

- 父因子：[0b193b55a101b661](minute.md#f-0b193b55a101b661)。

<a id="f-9af46799e470442b"></a>

## big_vwap_dev~s20~neut_turn

- ID：`9af46799e470442b`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0b193b55a101b661 (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0382 / 0.0218。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_big_vwap_dev, 20)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_big_vwap_dev, 20), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[0b193b55a101b661](minute.md#f-0b193b55a101b661)。

<a id="f-af3a9bc36d6a3c90"></a>

## big_vwap_dev~s20~neut_vol

- ID：`af3a9bc36d6a3c90`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0b193b55a101b661 (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0175 / 0.0089。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_big_vwap_dev, 20)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_big_vwap_dev, 20), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[0b193b55a101b661](minute.md#f-0b193b55a101b661)。

<a id="f-b02e083b644c61ff"></a>

## big_vwap_dev~s20~w0.5

- ID：`b02e083b644c61ff`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`未知`；评价状态：`error`。
- 原假设：variant of 0b193b55a101b661 (w0.5)
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
rolling_std(im_big_vwap_dev, 10)
```

- 父因子：[0b193b55a101b661](minute.md#f-0b193b55a101b661)。

<a id="f-75410164bac81d1a"></a>

## big_vwap_dev~s20~w2

- ID：`75410164bac81d1a`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0b193b55a101b661 (w2)
- 原判定：pass_mean+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0657 / 0.0464。

登记表达式或插件说明：

```text
rolling_std(im_big_vwap_dev, 40)
```

- 父因子：[0b193b55a101b661](minute.md#f-0b193b55a101b661)。

<a id="f-49da770302477f6e"></a>

## gp1_00~ema5

- ID：`49da770302477f6e`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of eb2bb8242d2892f8 (ema5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0852 / 0.0704。

登记表达式或插件说明：

```text
ema((rolling_cov(high, volume, 5)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(high, volume, 5), 5)
```

- 父因子：[eb2bb8242d2892f8](gp.md#f-eb2bb8242d2892f8)。

<a id="f-9a1a33ee1392bfc7"></a>

## gp1_00~resid_rev20

- ID：`9a1a33ee1392bfc7`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of eb2bb8242d2892f8 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0235 / 0.0013。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(high, volume, 5)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(high, volume, 5), close / lag(close, 20) - 1)
```

- 父因子：[eb2bb8242d2892f8](gp.md#f-eb2bb8242d2892f8)。

<a id="f-920a6be693ca2579"></a>

## gp1_00~tsz60

- ID：`920a6be693ca2579`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of eb2bb8242d2892f8 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0323 / 0.0150。

登记表达式或插件说明：

```text
ts_zscore((rolling_cov(high, volume, 5)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_cov(high, volume, 5), 60)
```

- 父因子：[eb2bb8242d2892f8](gp.md#f-eb2bb8242d2892f8)。

<a id="f-89a89ff0ef7d0ba5"></a>

## gp1_00~w0.5

- ID：`89a89ff0ef7d0ba5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of eb2bb8242d2892f8 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0450 / 0.0373。

登记表达式或插件说明：

```text
rolling_cov(high, volume, 2)
```

- 父因子：[eb2bb8242d2892f8](gp.md#f-eb2bb8242d2892f8)。

<a id="f-fbe7d7bcc05e0476"></a>

## gp1_01~neut_cap

- ID：`fbe7d7bcc05e0476`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 74a789b75300ff60 (neut_cap)
- 原判定：pass_mean+style:turnover20；历史均值 / 最差年 RankIC：0.0557 / 0.0317。

登记表达式或插件说明：

```text
cs_neutralize((rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open, log_cap)
```

- 父因子：[74a789b75300ff60](gp.md#f-74a789b75300ff60)。

<a id="f-a10a67a464005550"></a>

## gp1_01~resid_rev20

- ID：`a10a67a464005550`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 74a789b75300ff60 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0278 / 0.0044。

登记表达式或插件说明：

```text
cs_neutralize((rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open, close / lag(close, 20) - 1)
```

- 父因子：[74a789b75300ff60](gp.md#f-74a789b75300ff60)。

<a id="f-a065a95480875ed6"></a>

## gp1_01~tsz60

- ID：`a065a95480875ed6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 74a789b75300ff60 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0387 / 0.0203。

登记表达式或插件说明：

```text
ts_zscore((rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_max(rolling_cov(high, volume, 5), 5) + log_cap * open, 60)
```

- 父因子：[74a789b75300ff60](gp.md#f-74a789b75300ff60)。

<a id="f-93830ecb8a157438"></a>

## gp1_01~w0.5

- ID：`93830ecb8a157438`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 74a789b75300ff60 (w0.5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0708 / 0.0566。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 2), 2) + log_cap * open
```

- 父因子：[74a789b75300ff60](gp.md#f-74a789b75300ff60)。

<a id="f-74a7e412b41a2320"></a>

## gp1_01~w2

- ID：`74a7e412b41a2320`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 74a789b75300ff60 (w2)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0823 / 0.0666。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 10), 10) + log_cap * open
```

- 父因子：[74a789b75300ff60](gp.md#f-74a789b75300ff60)。

<a id="f-0d84cc4049d02f05"></a>

## gp1_01~wmax2

- ID：`0d84cc4049d02f05`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 74a789b75300ff60 (wmax2)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0827 / 0.0689。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 10), 5) + log_cap * open
```

- 父因子：[74a789b75300ff60](gp.md#f-74a789b75300ff60)。

<a id="f-b448e4b4e861b023"></a>

## gp1_08~neut_cap

- ID：`b448e4b4e861b023`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 62310cb495194b5e (neut_cap)
- 原判定：pass_mean+style:turnover20；历史均值 / 最差年 RankIC：0.0520 / 0.0389。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5))), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5)), log_cap)
```

- 父因子：[62310cb495194b5e](gp.md#f-62310cb495194b5e)。

<a id="f-87f366d3f4629130"></a>

## gp1_08~neut_turn

- ID：`87f366d3f4629130`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 62310cb495194b5e (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0237 / 0.0171。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5))), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5)), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[62310cb495194b5e](gp.md#f-62310cb495194b5e)。

<a id="f-a8657647b6839998"></a>

## gp1_08~neut_vol

- ID：`a8657647b6839998`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 62310cb495194b5e (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0137 / 0.0076。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5))), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5)), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[62310cb495194b5e](gp.md#f-62310cb495194b5e)。

<a id="f-560aa47f8077302d"></a>

## gp1_08~resid_rev20

- ID：`560aa47f8077302d`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 62310cb495194b5e (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0409 / 0.0192。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5))), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 40) * (vwap + rolling_std(vwap, 5)), close / lag(close, 20) - 1)
```

- 父因子：[62310cb495194b5e](gp.md#f-62310cb495194b5e)。

<a id="f-cf76408ec71b46ef"></a>

## gp1_08~w0.5

- ID：`cf76408ec71b46ef`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 62310cb495194b5e (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0505 / 0.0453。

登记表达式或插件说明：

```text
rolling_cov(volume, ts_zscore(log_cap - prev_close, 2), 20) * (vwap + rolling_std(vwap, 2))
```

- 父因子：[62310cb495194b5e](gp.md#f-62310cb495194b5e)。

<a id="f-97494575e7a4670b"></a>

## gp1_08~wmax0.5

- ID：`97494575e7a4670b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 62310cb495194b5e (wmax0.5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0608 / 0.0543。

登记表达式或插件说明：

```text
rolling_cov(volume, ts_zscore(log_cap - prev_close, 5), 20) * (vwap + rolling_std(vwap, 5))
```

- 父因子：[62310cb495194b5e](gp.md#f-62310cb495194b5e)。

<a id="f-e5dbd91106d68a33"></a>

## gp1_09~neut_cap

- ID：`e5dbd91106d68a33`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of de6b19da202fdaf2 (neut_cap)
- 原判定：pass_mean+style:turnover20；历史均值 / 最差年 RankIC：0.0526 / 0.0338。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(abs(prev_close * (volume + (close + close))), 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(abs(prev_close * (volume + (close + close))), 10), log_cap)
```

- 父因子：[de6b19da202fdaf2](gp.md#f-de6b19da202fdaf2)。

<a id="f-e6be858bbc0a8ef4"></a>

## gp1_09~resid_rev20

- ID：`e6be858bbc0a8ef4`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of de6b19da202fdaf2 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0434 / 0.0131。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(abs(prev_close * (volume + (close + close))), 10)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(abs(prev_close * (volume + (close + close))), 10), close / lag(close, 20) - 1)
```

- 父因子：[de6b19da202fdaf2](gp.md#f-de6b19da202fdaf2)。

<a id="f-7f229761d61a4e20"></a>

## gp1_12~delta5

- ID：`7f229761d61a4e20`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 24d557d4617883d7 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0199 / 0.0026。

登记表达式或插件说明：

```text
delta((rolling_max(rolling_cov(high, volume, 20), 5) + log(amount)), 5)
```

规范式 / 计算标识：

```text
delta(rolling_max(rolling_cov(high, volume, 20), 5) + log(amount), 5)
```

- 父因子：[24d557d4617883d7](gp.md#f-24d557d4617883d7)。

<a id="f-bb5b13593960ccc5"></a>

## gp1_12~neut_cap

- ID：`bb5b13593960ccc5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 24d557d4617883d7 (neut_cap)
- 原判定：pass_mean+style:turnover20；历史均值 / 最差年 RankIC：0.0550 / 0.0346。

登记表达式或插件说明：

```text
cs_neutralize((rolling_max(rolling_cov(high, volume, 20), 5) + log(amount)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_max(rolling_cov(high, volume, 20), 5) + log(amount), log_cap)
```

- 父因子：[24d557d4617883d7](gp.md#f-24d557d4617883d7)。

<a id="f-e36a2226c0c8cc19"></a>

## gp1_12~resid_rev20

- ID：`e36a2226c0c8cc19`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 24d557d4617883d7 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0216 / -0.0082。

登记表达式或插件说明：

```text
cs_neutralize((rolling_max(rolling_cov(high, volume, 20), 5) + log(amount)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_max(rolling_cov(high, volume, 20), 5) + log(amount), close / lag(close, 20) - 1)
```

- 父因子：[24d557d4617883d7](gp.md#f-24d557d4617883d7)。

<a id="f-06a2c6a41e9520c6"></a>

## gp1_12~w0.5

- ID：`06a2c6a41e9520c6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 24d557d4617883d7 (w0.5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0822 / 0.0686。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 10), 2) + log(amount)
```

- 父因子：[24d557d4617883d7](gp.md#f-24d557d4617883d7)。

<a id="f-63d86344ded7bd6d"></a>

## gp1_12~w2

- ID：`63d86344ded7bd6d`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 24d557d4617883d7 (w2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0670 / 0.0598。

登记表达式或插件说明：

```text
rolling_max(rolling_cov(high, volume, 40), 10) + log(amount)
```

- 父因子：[24d557d4617883d7](gp.md#f-24d557d4617883d7)。

<a id="f-e4e102b69aeef119"></a>

## gp1_15~ema5

- ID：`e4e102b69aeef119`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of a637179836f6e9a9 (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0723 / 0.0562。

登记表达式或插件说明：

```text
ema((rolling_cov(volume - low, ret, 40) * (rolling_cov(high, amount, 5) - rolling_corr(amount, amount, 10) + rolling_std(vwap, 5))), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(volume - low, ret, 40) * (rolling_cov(high, amount, 5) - rolling_corr(amount, amount, 10) + rolling_std(vwap, 5)), 5)
```

- 父因子：[a637179836f6e9a9](gp.md#f-a637179836f6e9a9)。

<a id="f-ce5640d769501a86"></a>

## gp1_15~w0.5

- ID：`ce5640d769501a86`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of a637179836f6e9a9 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0388 / 0.0300。

登记表达式或插件说明：

```text
rolling_cov(volume - low, ret, 20) * (rolling_cov(high, amount, 2) - rolling_corr(amount, amount, 5) + rolling_std(vwap, 2))
```

- 父因子：[a637179836f6e9a9](gp.md#f-a637179836f6e9a9)。

<a id="f-705aeec9745fee6b"></a>

## gp1_15~wmax0.5

- ID：`705aeec9745fee6b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of a637179836f6e9a9 (wmax0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0574 / 0.0454。

登记表达式或插件说明：

```text
rolling_cov(volume - low, ret, 20) * (rolling_cov(high, amount, 5) - rolling_corr(amount, amount, 10) + rolling_std(vwap, 5))
```

- 父因子：[a637179836f6e9a9](gp.md#f-a637179836f6e9a9)。

<a id="f-d87d5593a1881af5"></a>

## gp2_00~ema10

- ID：`d87d5593a1881af5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (ema10)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0733 / 0.0599。

登记表达式或插件说明：

```text
ema((rolling_cov(rolling_cov(amount, vwap, 3), amount, 10)), 10)
```

规范式 / 计算标识：

```text
ema(rolling_cov(rolling_cov(amount, vwap, 3), amount, 10), 10)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-dfdc86db7cd0949c"></a>

## gp2_00~ema5

- ID：`dfdc86db7cd0949c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0726 / 0.0609。

登记表达式或插件说明：

```text
ema((rolling_cov(rolling_cov(amount, vwap, 3), amount, 10)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(rolling_cov(amount, vwap, 3), amount, 10), 5)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-1cb18d7c85d0b3a7"></a>

## gp2_00~neut_cap

- ID：`1cb18d7c85d0b3a7`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (neut_cap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0023 / -0.0577。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(rolling_cov(amount, vwap, 3), amount, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(rolling_cov(amount, vwap, 3), amount, 10), log_cap)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-ce4fd6965ed514a1"></a>

## gp2_00~tsrank60

- ID：`ce4fd6965ed514a1`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (tsrank60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0367 / 0.0158。

登记表达式或插件说明：

```text
ts_rank((rolling_cov(rolling_cov(amount, vwap, 3), amount, 10)), 60)
```

规范式 / 计算标识：

```text
ts_rank(rolling_cov(rolling_cov(amount, vwap, 3), amount, 10), 60)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-c0ab983f5d9f3241"></a>

## gp2_00~tsz60

- ID：`c0ab983f5d9f3241`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0312 / 0.0128。

登记表达式或插件说明：

```text
ts_zscore((rolling_cov(rolling_cov(amount, vwap, 3), amount, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_cov(rolling_cov(amount, vwap, 3), amount, 10), 60)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-0a92cdfa0b14853c"></a>

## gp2_00~w0.5

- ID：`0a92cdfa0b14853c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0476 / 0.0378。

登记表达式或插件说明：

```text
rolling_cov(rolling_cov(amount, vwap, 2), amount, 5)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-0690820f94c36289"></a>

## gp2_00~w2

- ID：`0690820f94c36289`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (w2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0717 / 0.0563。

登记表达式或插件说明：

```text
rolling_cov(rolling_cov(amount, vwap, 5), amount, 20)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-97ab3eab14a60d47"></a>

## gp2_00~wmax0.5

- ID：`97ab3eab14a60d47`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (wmax0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0475 / 0.0361。

登记表达式或插件说明：

```text
rolling_cov(rolling_cov(amount, vwap, 3), amount, 5)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-68a6b88dab684fe6"></a>

## gp2_00~wmax2

- ID：`68a6b88dab684fe6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bdc9424dcd4476c3 (wmax2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0732 / 0.0590。

登记表达式或插件说明：

```text
rolling_cov(rolling_cov(amount, vwap, 3), amount, 20)
```

- 父因子：[bdc9424dcd4476c3](gp.md#f-bdc9424dcd4476c3)。

<a id="f-12f0c305adce143e"></a>

## gp2_04~ema5

- ID：`12f0c305adce143e`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 399a52f00401bd8a (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0667 / 0.0506。

登记表达式或插件说明：

```text
ema((rolling_cov(abs(log_cap), volume - low, 10)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(abs(log_cap), volume - low, 10), 5)
```

- 父因子：[399a52f00401bd8a](gp.md#f-399a52f00401bd8a)。

<a id="f-7e8d0424ce0d2420"></a>

## gp2_04~resid_rev20

- ID：`7e8d0424ce0d2420`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 399a52f00401bd8a (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0129 / -0.0034。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(abs(log_cap), volume - low, 10)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(abs(log_cap), volume - low, 10), close / lag(close, 20) - 1)
```

- 父因子：[399a52f00401bd8a](gp.md#f-399a52f00401bd8a)。

<a id="f-15865256e493d946"></a>

## gp2_04~tsz60

- ID：`15865256e493d946`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 399a52f00401bd8a (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0301 / 0.0143。

登记表达式或插件说明：

```text
ts_zscore((rolling_cov(abs(log_cap), volume - low, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_cov(abs(log_cap), volume - low, 10), 60)
```

- 父因子：[399a52f00401bd8a](gp.md#f-399a52f00401bd8a)。

<a id="f-dda8f4ab327f2e89"></a>

## gp2_04~w0.5

- ID：`dda8f4ab327f2e89`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 399a52f00401bd8a (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0569 / 0.0387。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - low, 5)
```

- 父因子：[399a52f00401bd8a](gp.md#f-399a52f00401bd8a)。

<a id="f-a76b71519c629027"></a>

## gp2_04~w2

- ID：`a76b71519c629027`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 399a52f00401bd8a (w2)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0643 / 0.0468。

登记表达式或插件说明：

```text
rolling_cov(abs(log_cap), volume - low, 20)
```

- 父因子：[399a52f00401bd8a](gp.md#f-399a52f00401bd8a)。

<a id="f-fa0efa1b6661d9ae"></a>

## gp2_10~ema5

- ID：`fa0efa1b6661d9ae`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0815 / 0.0664。

登记表达式或插件说明：

```text
ema(((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low))), 5)
```

规范式 / 计算标识：

```text
ema((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low)), 5)
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-d1ce09f05c64d66b"></a>

## gp2_10~neut_cap

- ID：`d1ce09f05c64d66b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0414 / 0.0190。

登记表达式或插件说明：

```text
cs_neutralize(((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low))), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low)), log_cap)
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-dd3b7432cc43e4c2"></a>

## gp2_10~resid_rev20

- ID：`dd3b7432cc43e4c2`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0121 / -0.0065。

登记表达式或插件说明：

```text
cs_neutralize(((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low))), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low)), close / lag(close, 20) - 1)
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-d073b2b94d1cf4d1"></a>

## gp2_10~tsrank60

- ID：`d073b2b94d1cf4d1`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (tsrank60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0319 / 0.0183。

登记表达式或插件说明：

```text
ts_rank(((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low))), 60)
```

规范式 / 计算标识：

```text
ts_rank((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low)), 60)
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-9663d78908af0ea4"></a>

## gp2_10~tsz60

- ID：`9663d78908af0ea4`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0224 / 0.0100。

登记表达式或插件说明：

```text
ts_zscore(((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low))), 60)
```

规范式 / 计算标识：

```text
ts_zscore((rolling_cov(amount, vwap, 3) + open / turnover) / (close * (low / low) + sign(low)), 60)
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-f3fcc382e7a09aea"></a>

## gp2_10~w0.5

- ID：`f3fcc382e7a09aea`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0428 / 0.0343。

登记表达式或插件说明：

```text
(rolling_cov(amount, vwap, 2) + open / turnover) / (close * (low / low) + sign(low))
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-210ef8f7a61a03d2"></a>

## gp2_10~w2

- ID：`210ef8f7a61a03d2`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 80321c4a0d32ea1b (w2)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0703 / 0.0544。

登记表达式或插件说明：

```text
(rolling_cov(amount, vwap, 5) + open / turnover) / (close * (low / low) + sign(low))
```

- 父因子：[80321c4a0d32ea1b](gp.md#f-80321c4a0d32ea1b)。

<a id="f-3733af6e90ea4966"></a>

## gp2_15~neut_cap

- ID：`3733af6e90ea4966`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of fa8f3b9c8f131558 (neut_cap)
- 原判定：weak_signal+style:turnover20；历史均值 / 最差年 RankIC：0.0477 / 0.0297。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(amount, 5)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(amount, 5), log_cap)
```

- 父因子：[fa8f3b9c8f131558](gp.md#f-fa8f3b9c8f131558)。

<a id="f-cae5c6fc49b01dc1"></a>

## gp2_15~resid_rev20

- ID：`cae5c6fc49b01dc1`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of fa8f3b9c8f131558 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0396 / 0.0123。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(amount, 5)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(amount, 5), close / lag(close, 20) - 1)
```

- 父因子：[fa8f3b9c8f131558](gp.md#f-fa8f3b9c8f131558)。

<a id="f-083bf4ce6e51fdfb"></a>

## gp2_15~tsz60

- ID：`083bf4ce6e51fdfb`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of fa8f3b9c8f131558 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0466 / 0.0337。

登记表达式或插件说明：

```text
ts_zscore((rolling_std(amount, 5)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_std(amount, 5), 60)
```

- 父因子：[fa8f3b9c8f131558](gp.md#f-fa8f3b9c8f131558)。

<a id="f-e7b87c29659615af"></a>

## gp2_15~w0.5

- ID：`e7b87c29659615af`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of fa8f3b9c8f131558 (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0672 / 0.0435。

登记表达式或插件说明：

```text
rolling_std(amount, 2)
```

- 父因子：[fa8f3b9c8f131558](gp.md#f-fa8f3b9c8f131558)。

<a id="f-80beb4cfc6548fd0"></a>

## gp2_16~ema5

- ID：`80beb4cfc6548fd0`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0693 / 0.0564。

登记表达式或插件说明：

```text
ema((rolling_cov(rolling_mean(log(turnover), 5), amount, 10)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(rolling_mean(log(turnover), 5), amount, 10), 5)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-dc45c0bf869ec463"></a>

## gp2_16~neut_cap

- ID：`dc45c0bf869ec463`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0377 / 0.0172。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(rolling_mean(log(turnover), 5), amount, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(rolling_mean(log(turnover), 5), amount, 10), log_cap)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-325a632c826f2e94"></a>

## gp2_16~tsz60

- ID：`325a632c826f2e94`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0307 / 0.0175。

登记表达式或插件说明：

```text
ts_zscore((rolling_cov(rolling_mean(log(turnover), 5), amount, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_cov(rolling_mean(log(turnover), 5), amount, 10), 60)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-d3c0bd345c48d22c"></a>

## gp2_16~w0.5

- ID：`d3c0bd345c48d22c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (w0.5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0704 / 0.0538。

登记表达式或插件说明：

```text
rolling_cov(rolling_mean(log(turnover), 2), amount, 5)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-0adc14fc8af454dc"></a>

## gp2_16~w2

- ID：`0adc14fc8af454dc`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (w2)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0538 / 0.0381。

登记表达式或插件说明：

```text
rolling_cov(rolling_mean(log(turnover), 10), amount, 20)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-983eb320faf26388"></a>

## gp2_16~wmax0.5

- ID：`983eb320faf26388`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (wmax0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0391 / 0.0302。

登记表达式或插件说明：

```text
rolling_cov(rolling_mean(log(turnover), 5), amount, 5)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-6bdb81873a1ce6f0"></a>

## gp2_16~wmax2

- ID：`6bdb81873a1ce6f0`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 791a83fff8b15524 (wmax2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0710 / 0.0546。

登记表达式或插件说明：

```text
rolling_cov(rolling_mean(log(turnover), 5), amount, 20)
```

- 父因子：[791a83fff8b15524](gp.md#f-791a83fff8b15524)。

<a id="f-a5a0f601c12ef003"></a>

## gp3_00~neut_cap

- ID：`a5a0f601c12ef003`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5f66b19823a5e49e (neut_cap)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0607 / 0.0348。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(turnover * close, volume, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(turnover * close, volume, 10), log_cap)
```

- 父因子：[5f66b19823a5e49e](gp.md#f-5f66b19823a5e49e)。

<a id="f-0b66277c52bc6ef1"></a>

## gp3_00~resid_rev20

- ID：`0b66277c52bc6ef1`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5f66b19823a5e49e (resid_rev20)
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0182 / -0.0097。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(turnover * close, volume, 10)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(turnover * close, volume, 10), close / lag(close, 20) - 1)
```

- 父因子：[5f66b19823a5e49e](gp.md#f-5f66b19823a5e49e)。

<a id="f-b3c81c483240c531"></a>

## gp3_00~tsrank60

- ID：`b3c81c483240c531`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5f66b19823a5e49e (tsrank60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0456 / 0.0292。

登记表达式或插件说明：

```text
ts_rank((rolling_cov(turnover * close, volume, 10)), 60)
```

规范式 / 计算标识：

```text
ts_rank(rolling_cov(turnover * close, volume, 10), 60)
```

- 父因子：[5f66b19823a5e49e](gp.md#f-5f66b19823a5e49e)。

<a id="f-62e52f98802ec8b2"></a>

## gp3_00~tsz60

- ID：`62e52f98802ec8b2`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5f66b19823a5e49e (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0430 / 0.0259。

登记表达式或插件说明：

```text
ts_zscore((rolling_cov(turnover * close, volume, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_cov(turnover * close, volume, 10), 60)
```

- 父因子：[5f66b19823a5e49e](gp.md#f-5f66b19823a5e49e)。

<a id="f-71bec9ab955c3642"></a>

## gp3_00~w0.5

- ID：`71bec9ab955c3642`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5f66b19823a5e49e (w0.5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0862 / 0.0711。

登记表达式或插件说明：

```text
rolling_cov(turnover * close, volume, 5)
```

- 父因子：[5f66b19823a5e49e](gp.md#f-5f66b19823a5e49e)。

<a id="f-0746521a55c7e9bf"></a>

## gp3_00~w2

- ID：`0746521a55c7e9bf`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5f66b19823a5e49e (w2)
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0842 / 0.0728。

登记表达式或插件说明：

```text
rolling_cov(turnover * close, volume, 20)
```

- 父因子：[5f66b19823a5e49e](gp.md#f-5f66b19823a5e49e)。

<a id="f-a5b42f22354fecac"></a>

## gp3_01~delta5

- ID：`a5b42f22354fecac`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 71a391aaaafe4e8a (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0146 / 0.0074。

登记表达式或插件说明：

```text
delta(((log_cap + amount * turnover) * close), 5)
```

规范式 / 计算标识：

```text
delta((log_cap + amount * turnover) * close, 5)
```

- 父因子：[71a391aaaafe4e8a](gp.md#f-71a391aaaafe4e8a)。

<a id="f-032aa2d3326eb968"></a>

## gp3_01~neut_cap

- ID：`032aa2d3326eb968`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 71a391aaaafe4e8a (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0357 / 0.0095。

登记表达式或插件说明：

```text
cs_neutralize(((log_cap + amount * turnover) * close), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize((log_cap + amount * turnover) * close, log_cap)
```

- 父因子：[71a391aaaafe4e8a](gp.md#f-71a391aaaafe4e8a)。

<a id="f-7897b3e492476017"></a>

## gp3_01~tsz60

- ID：`7897b3e492476017`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 71a391aaaafe4e8a (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0451 / 0.0279。

登记表达式或插件说明：

```text
ts_zscore(((log_cap + amount * turnover) * close), 60)
```

规范式 / 计算标识：

```text
ts_zscore((log_cap + amount * turnover) * close, 60)
```

- 父因子：[71a391aaaafe4e8a](gp.md#f-71a391aaaafe4e8a)。

<a id="f-52a269b522b25ef0"></a>

## gp3_03~ema5

- ID：`52a269b522b25ef0`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b0ad0bdd0e9772b2 (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0723 / 0.0600。

登记表达式或插件说明：

```text
ema((rolling_cov(delta(vwap, 3), volume, 10)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(delta(vwap, 3), volume, 10), 5)
```

- 父因子：[b0ad0bdd0e9772b2](gp.md#f-b0ad0bdd0e9772b2)。

<a id="f-eb037a1a5ec4428f"></a>

## gp3_03~resid_rev20

- ID：`eb037a1a5ec4428f`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b0ad0bdd0e9772b2 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0250 / 0.0132。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(delta(vwap, 3), volume, 10)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(delta(vwap, 3), volume, 10), close / lag(close, 20) - 1)
```

- 父因子：[b0ad0bdd0e9772b2](gp.md#f-b0ad0bdd0e9772b2)。

<a id="f-6978170eeae3fd1e"></a>

## gp3_03~tsz60

- ID：`6978170eeae3fd1e`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b0ad0bdd0e9772b2 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0293 / 0.0111。

登记表达式或插件说明：

```text
ts_zscore((rolling_cov(delta(vwap, 3), volume, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_cov(delta(vwap, 3), volume, 10), 60)
```

- 父因子：[b0ad0bdd0e9772b2](gp.md#f-b0ad0bdd0e9772b2)。

<a id="f-21db1696ed9f69a6"></a>

## gp3_03~w0.5

- ID：`21db1696ed9f69a6`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b0ad0bdd0e9772b2 (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0550 / 0.0414。

登记表达式或插件说明：

```text
rolling_cov(delta(vwap, 2), volume, 5)
```

- 父因子：[b0ad0bdd0e9772b2](gp.md#f-b0ad0bdd0e9772b2)。

<a id="f-acc5853e34928901"></a>

## gp3_03~w2

- ID：`acc5853e34928901`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b0ad0bdd0e9772b2 (w2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0723 / 0.0629。

登记表达式或插件说明：

```text
rolling_cov(delta(vwap, 5), volume, 20)
```

- 父因子：[b0ad0bdd0e9772b2](gp.md#f-b0ad0bdd0e9772b2)。

<a id="f-fd5144fa71123549"></a>

## gp3_03~wmax0.5

- ID：`fd5144fa71123549`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b0ad0bdd0e9772b2 (wmax0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0556 / 0.0413。

登记表达式或插件说明：

```text
rolling_cov(delta(vwap, 3), volume, 5)
```

- 父因子：[b0ad0bdd0e9772b2](gp.md#f-b0ad0bdd0e9772b2)。

<a id="f-bb1e3977858a6b6b"></a>

## gp3_04~ema10

- ID：`bb1e3977858a6b6b`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (ema10)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0716 / 0.0650。

登记表达式或插件说明：

```text
ema((rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10)), 10)
```

规范式 / 计算标识：

```text
ema(rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10), 10)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-a2f6c0b3a9ae693f"></a>

## gp3_04~ema5

- ID：`a2f6c0b3a9ae693f`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (ema5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0707 / 0.0598。

登记表达式或插件说明：

```text
ema((rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10), 5)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-c507f56dafe3c112"></a>

## gp3_04~neut_cap

- ID：`c507f56dafe3c112`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0169 / -0.0116。

登记表达式或插件说明：

```text
cs_neutralize((rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10), log_cap)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-a8aae9e7a69a9b0f"></a>

## gp3_04~tsrank60

- ID：`a8aae9e7a69a9b0f`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (tsrank60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0338 / 0.0145。

登记表达式或插件说明：

```text
ts_rank((rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10)), 60)
```

规范式 / 计算标识：

```text
ts_rank(rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 10), 60)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-605fd690e2d26e5c"></a>

## gp3_04~w0.5

- ID：`605fd690e2d26e5c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0439 / 0.0326。

登记表达式或插件说明：

```text
rolling_cov(turnover * rolling_cov(ret + low, amount, 2), volume, 5)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-a0fe19d2557f83b5"></a>

## gp3_04~w2

- ID：`a0fe19d2557f83b5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (w2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0719 / 0.0616。

登记表达式或插件说明：

```text
rolling_cov(turnover * rolling_cov(ret + low, amount, 10), volume, 20)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-ebda31e88da7a6a7"></a>

## gp3_04~wmax0.5

- ID：`ebda31e88da7a6a7`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (wmax0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0510 / 0.0385。

登记表达式或插件说明：

```text
rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 5)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-4a5b6cfbc586700e"></a>

## gp3_04~wmax2

- ID：`4a5b6cfbc586700e`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dffb2a7e0ae3b1e0 (wmax2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0704 / 0.0612。

登记表达式或插件说明：

```text
rolling_cov(turnover * rolling_cov(ret + low, amount, 5), volume, 20)
```

- 父因子：[dffb2a7e0ae3b1e0](gp.md#f-dffb2a7e0ae3b1e0)。

<a id="f-901864d54f7b3870"></a>

## gp3_05~ema5

- ID：`901864d54f7b3870`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (ema5)
- 原判定：pass_worst+style:turnover20；历史均值 / 最差年 RankIC：0.0751 / 0.0650。

登记表达式或插件说明：

```text
ema((rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3), 5)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-e33001d39df1bfcd"></a>

## gp3_05~neut_cap

- ID：`e33001d39df1bfcd`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (neut_cap)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0537 / 0.0414。

登记表达式或插件说明：

```text
cs_neutralize((rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3), log_cap)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-c98bb1600c84fc16"></a>

## gp3_05~resid_rev20

- ID：`c98bb1600c84fc16`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0296 / 0.0231。

登记表达式或插件说明：

```text
cs_neutralize((rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3), close / lag(close, 20) - 1)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-1831762b264d2d5c"></a>

## gp3_05~tsrank60

- ID：`1831762b264d2d5c`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (tsrank60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0342 / 0.0263。

登记表达式或插件说明：

```text
ts_rank((rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3)), 60)
```

规范式 / 计算标识：

```text
ts_rank(rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3), 60)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-1f2566031ecd7583"></a>

## gp3_05~tsz60

- ID：`1f2566031ecd7583`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0154 / 0.0034。

登记表达式或插件说明：

```text
ts_zscore((rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 3), 60)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-4264978063261d9d"></a>

## gp3_05~w0.5

- ID：`4264978063261d9d`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0213 / 0.0169。

登记表达式或插件说明：

```text
rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 2)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-d60347432a506c0f"></a>

## gp3_05~w2

- ID：`d60347432a506c0f`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d85ae97a74ed695 (w2)
- 原判定：pass_worst+style:turnover20；历史均值 / 最差年 RankIC：0.0813 / 0.0728。

登记表达式或插件说明：

```text
rolling_corr(amount, cs_neutralize(turnover, log_cap) * (open + turnover * close), 5)
```

- 父因子：[0d85ae97a74ed695](gp.md#f-0d85ae97a74ed695)。

<a id="f-5512a50398296566"></a>

## gp3_11~ema5

- ID：`5512a50398296566`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (ema5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0694 / 0.0550。

登记表达式或插件说明：

```text
ema((rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low)))), 5)
```

规范式 / 计算标识：

```text
ema(rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low))), 5)
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-0908b7ccfca981cb"></a>

## gp3_11~neut_cap

- ID：`0908b7ccfca981cb`；归属：历史候选，未列入上述集合。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0252 / -0.0149。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low)))), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low))), log_cap)
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-ab357d54c99fef9f"></a>

## gp3_11~resid_rev20

- ID：`ab357d54c99fef9f`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (resid_rev20)
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0315 / 0.0125。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low)))), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low))), close / lag(close, 20) - 1)
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-b09db0de00a811f1"></a>

## gp3_11~tsrank60

- ID：`b09db0de00a811f1`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (tsrank60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0338 / 0.0203。

登记表达式或插件说明：

```text
ts_rank((rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low)))), 60)
```

规范式 / 计算标识：

```text
ts_rank(rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low))), 60)
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-1d599e6728c0fef5"></a>

## gp3_11~tsz60

- ID：`1d599e6728c0fef5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0265 / 0.0131。

登记表达式或插件说明：

```text
ts_zscore((rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low)))), 60)
```

规范式 / 计算标识：

```text
ts_zscore(rolling_std(log_cap * close, 5) * (rolling_cov(prev_close, volume, 20) / (prev_close * prev_close / (amount * low))), 60)
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-5864ed596d386838"></a>

## gp3_11~w0.5

- ID：`5864ed596d386838`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0559 / 0.0300。

登记表达式或插件说明：

```text
rolling_std(log_cap * close, 2) * (rolling_cov(prev_close, volume, 10) / (prev_close * prev_close / (amount * low)))
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-7a8967758c19ccc5"></a>

## gp3_11~w2

- ID：`7a8967758c19ccc5`；归属：active_396, research_597, pool_current。
- 机制：gp_search（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5069c32deee54111 (w2)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0699 / 0.0571。

登记表达式或插件说明：

```text
rolling_std(log_cap * close, 10) * (rolling_cov(prev_close, volume, 40) / (prev_close * prev_close / (amount * low)))
```

- 父因子：[5069c32deee54111](gp.md#f-5069c32deee54111)。

<a id="f-816b2195405802d9"></a>

## idio_vol20_low~w0.5

- ID：`816b2195405802d9`；归属：active_396, research_597, pool_current。
- 机制：特质波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of fed5477153a935a8 (w0.5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0871 / 0.0688。

登记表达式或插件说明：

```text
-rolling_std(rolling_residual(ret, mkt_ret, 30), 10)
```

- 父因子：[fed5477153a935a8](classic.md#f-fed5477153a935a8)。

<a id="f-18cb6666d924437c"></a>

## legacy.calendar.standard~w0.5

- ID：`18cb6666d924437c`；归属：active_396, research_597, pool_current。
- 机制：legacy（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 9e4f8905c2e37803 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0479 / 0.0260。

登记表达式或插件说明：

```text
40 * where(abs(rolling_sum(open - low, 15)) > 1e-5, rolling_sum(high - open, 15) / rolling_sum(open - low, 15), 0 / 0)
```

规范式 / 计算标识：

```text
40 * where(abs(rolling_sum(open - low, 15)) > 1e-05, rolling_sum(high - open, 15) / rolling_sum(open - low, 15), 0 / 0)
```

- 父因子：[9e4f8905c2e37803](legacy.md#f-9e4f8905c2e37803)。

<a id="f-52e9b66098bd48c4"></a>

## maxret20_low~delta5

- ID：`52e9b66098bd48c4`；归属：active_396, research_597, pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 1b0aae8536ac6327 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0199 / 0.0041。

登记表达式或插件说明：

```text
delta((-rolling_max(ret, 20)), 5)
```

规范式 / 计算标识：

```text
delta(-rolling_max(ret, 20), 5)
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)。

<a id="f-35066cc27de48141"></a>

## maxret20_low~ema10

- ID：`35066cc27de48141`；归属：历史候选，未列入上述集合。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 1b0aae8536ac6327 (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0677 / 0.0551。

登记表达式或插件说明：

```text
ema((-rolling_max(ret, 20)), 10)
```

规范式 / 计算标识：

```text
ema(-rolling_max(ret, 20), 10)
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)。

<a id="f-59504b48e1d795e4"></a>

## maxret20_low~neut_turn

- ID：`59504b48e1d795e4`；归属：active_396, research_597, pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 1b0aae8536ac6327 (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0417 / 0.0294。

登记表达式或插件说明：

```text
cs_neutralize((-rolling_max(ret, 20)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(-rolling_max(ret, 20), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)。

<a id="f-fb9f8b523f6a90d1"></a>

## maxret20_low~neut_vol

- ID：`fb9f8b523f6a90d1`；归属：历史候选，未列入上述集合。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 1b0aae8536ac6327 (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0113 / -0.0009。

登记表达式或插件说明：

```text
cs_neutralize((-rolling_max(ret, 20)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(-rolling_max(ret, 20), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)。

<a id="f-f2da0be86dda5ecd"></a>

## maxret20_low~tsz60

- ID：`f2da0be86dda5ecd`；归属：active_396, research_597, pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 1b0aae8536ac6327 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0324 / 0.0187。

登记表达式或插件说明：

```text
ts_zscore((-rolling_max(ret, 20)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(-rolling_max(ret, 20), 60)
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)。

<a id="f-9f9d131e789018b8"></a>

## maxret20_low~w0.5

- ID：`9f9d131e789018b8`；归属：active_396, research_597, pool_current。
- 机制：彩票效应/最大单日收益（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 1b0aae8536ac6327 (w0.5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0721 / 0.0610。

登记表达式或插件说明：

```text
-rolling_max(ret, 10)
```

- 父因子：[1b0aae8536ac6327](classic.md#f-1b0aae8536ac6327)。

<a id="f-2775170276e9dc47"></a>

## maxret~d1~delta5

- ID：`2775170276e9dc47`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 4394db693cbf2288 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0115 / 0.0062。

登记表达式或插件说明：

```text
delta((im_maxret), 5)
```

规范式 / 计算标识：

```text
delta(im_maxret, 5)
```

- 父因子：[4394db693cbf2288](minute.md#f-4394db693cbf2288)。

<a id="f-fd38373d4d7dfb8f"></a>

## maxret~d1~neut_vol

- ID：`fd38373d4d7dfb8f`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 4394db693cbf2288 (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0263 / 0.0125。

登记表达式或插件说明：

```text
cs_neutralize((im_maxret), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(im_maxret, cs_rank(rolling_std(ret, 20)))
```

- 父因子：[4394db693cbf2288](minute.md#f-4394db693cbf2288)。

<a id="f-705ec06a3b7fc117"></a>

## maxret~ema10~neut_cap

- ID：`705ec06a3b7fc117`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`未知`；评价状态：`error`。
- 原假设：variant of 56d314292c98f620 (neut_cap)
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_maxret, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_maxret, 10), log_cap)
```

- 父因子：[56d314292c98f620](minute.md#f-56d314292c98f620)。

<a id="f-f1f8a06d1958680f"></a>

## maxret~ema10~neut_turn

- ID：`f1f8a06d1958680f`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`未知`；评价状态：`error`。
- 原假设：variant of 56d314292c98f620 (neut_turn)
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_maxret, 10)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_maxret, 10), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[56d314292c98f620](minute.md#f-56d314292c98f620)。

<a id="f-a7d4a03edc88ad3f"></a>

## maxret~ema10~neut_vol

- ID：`a7d4a03edc88ad3f`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`未知`；评价状态：`error`。
- 原假设：variant of 56d314292c98f620 (neut_vol)
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_maxret, 10)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_maxret, 10), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[56d314292c98f620](minute.md#f-56d314292c98f620)。

<a id="f-65d17aa66eb60a7e"></a>

## maxret~ema10~tsz60

- ID：`65d17aa66eb60a7e`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`未知`；评价状态：`error`。
- 原假设：variant of 56d314292c98f620 (tsz60)
- 原判定：implementation_error；历史均值 / 最差年 RankIC：— / —。

登记表达式或插件说明：

```text
ts_zscore((ema(im_maxret, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_maxret, 10), 60)
```

- 父因子：[56d314292c98f620](minute.md#f-56d314292c98f620)。

<a id="f-386cfaee4dccef2e"></a>

## maxret~m20_ncap~delta5

- ID：`386cfaee4dccef2e`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dd64347d71dbdfba (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0280 / 0.0106。

登记表达式或插件说明：

```text
delta((cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap)), 5)
```

规范式 / 计算标识：

```text
delta(cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap), 5)
```

- 父因子：[dd64347d71dbdfba](minute.md#f-dd64347d71dbdfba)。

<a id="f-09336d38fe423645"></a>

## maxret~m20_ncap~neut_vol

- ID：`09336d38fe423645`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dd64347d71dbdfba (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0369 / 0.0247。

登记表达式或插件说明：

```text
cs_neutralize((cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[dd64347d71dbdfba](minute.md#f-dd64347d71dbdfba)。

<a id="f-96d5a68a744b7c4e"></a>

## maxret~m20_ncap~resid_rev20

- ID：`96d5a68a744b7c4e`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dd64347d71dbdfba (resid_rev20)
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0619 / 0.0449。

登记表达式或插件说明：

```text
cs_neutralize((cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap), close / lag(close, 20) - 1)
```

- 父因子：[dd64347d71dbdfba](minute.md#f-dd64347d71dbdfba)。

<a id="f-c0be65dc26305479"></a>

## maxret~m20_ncap~w2

- ID：`c0be65dc26305479`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of dd64347d71dbdfba (w2)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0696 / 0.0529。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_maxret, 40)), log_cap)
```

- 父因子：[dd64347d71dbdfba](minute.md#f-dd64347d71dbdfba)。

<a id="f-a5836b4acfef116b"></a>

## maxret~m5~w0.5

- ID：`a5836b4acfef116b`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of b00253b4d35a6c95 (w0.5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0710 / 0.0624。

登记表达式或插件说明：

```text
rolling_mean(im_maxret, 2)
```

- 父因子：[b00253b4d35a6c95](minute.md#f-b00253b4d35a6c95)。

<a id="f-e9b07fbe9f95b577"></a>

## maxret~s20~delta5

- ID：`e9b07fbe9f95b577`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 8795402becec7009 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0177 / 0.0078。

登记表达式或插件说明：

```text
delta((rolling_std(im_maxret, 20)), 5)
```

规范式 / 计算标识：

```text
delta(rolling_std(im_maxret, 20), 5)
```

- 父因子：[8795402becec7009](minute.md#f-8795402becec7009)。

<a id="f-52dbd14f659ce978"></a>

## maxret~s20~neut_cap

- ID：`52dbd14f659ce978`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 8795402becec7009 (neut_cap)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0659 / 0.0529。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_maxret, 20)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_maxret, 20), log_cap)
```

- 父因子：[8795402becec7009](minute.md#f-8795402becec7009)。

<a id="f-9563515eff701edd"></a>

## maxret~s20~neut_turn

- ID：`9563515eff701edd`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 8795402becec7009 (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0283 / 0.0119。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_maxret, 20)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_maxret, 20), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[8795402becec7009](minute.md#f-8795402becec7009)。

<a id="f-eb9fa1000b40f8e2"></a>

## maxret~s20~neut_vol

- ID：`eb9fa1000b40f8e2`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 8795402becec7009 (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0166 / -0.0018。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_maxret, 20)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_maxret, 20), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[8795402becec7009](minute.md#f-8795402becec7009)。

<a id="f-f4d594d98bddc2b2"></a>

## maxret~s20~w0.5

- ID：`f4d594d98bddc2b2`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 8795402becec7009 (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0619 / 0.0491。

登记表达式或插件说明：

```text
rolling_std(im_maxret, 10)
```

- 父因子：[8795402becec7009](minute.md#f-8795402becec7009)。

<a id="f-4a4f2d78e1705a5d"></a>

## minret~ema10~neut_cap

- ID：`4a4f2d78e1705a5d`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of dd8b34062ba8014d (neut_cap)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0754 / 0.0626。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_minret, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_minret, 10), log_cap)
```

- 父因子：[dd8b34062ba8014d](minute.md#f-dd8b34062ba8014d)。

<a id="f-60426d58de142051"></a>

## minret~ema10~tsz60

- ID：`60426d58de142051`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of dd8b34062ba8014d (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0370 / 0.0301。

登记表达式或插件说明：

```text
ts_zscore((ema(im_minret, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_minret, 10), 60)
```

- 父因子：[dd8b34062ba8014d](minute.md#f-dd8b34062ba8014d)。

<a id="f-04206c454713b57f"></a>

## minret~m20_ncap~delta5

- ID：`04206c454713b57f`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of de041c3f3f1a3918 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0234 / 0.0120。

登记表达式或插件说明：

```text
delta((cs_neutralize(cs_rank(rolling_mean(im_minret, 20)), log_cap)), 5)
```

规范式 / 计算标识：

```text
delta(cs_neutralize(cs_rank(rolling_mean(im_minret, 20)), log_cap), 5)
```

- 父因子：[de041c3f3f1a3918](minute.md#f-de041c3f3f1a3918)。

<a id="f-b98ea0bb39acfdef"></a>

## minret~m20_ncap~neut_cap

- ID：`b98ea0bb39acfdef`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of de041c3f3f1a3918 (neut_cap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0656 / 0.0469。

登记表达式或插件说明：

```text
cs_neutralize((cs_neutralize(cs_rank(rolling_mean(im_minret, 20)), log_cap)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(cs_neutralize(cs_rank(rolling_mean(im_minret, 20)), log_cap), log_cap)
```

- 父因子：[de041c3f3f1a3918](minute.md#f-de041c3f3f1a3918)。

<a id="f-b6f814e389d7b37d"></a>

## minret~m20_ncap~w2

- ID：`b6f814e389d7b37d`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of de041c3f3f1a3918 (w2)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0602 / 0.0362。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_minret, 40)), log_cap)
```

- 父因子：[de041c3f3f1a3918](minute.md#f-de041c3f3f1a3918)。

<a id="f-6c2662403bb884aa"></a>

## mw_reversal_vwap20~ema10

- ID：`6c2662403bb884aa`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ba970f639369393e (ema10)
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0642 / 0.0407。

登记表达式或插件说明：

```text
ema((-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20)), 10)
```

规范式 / 计算标识：

```text
ema(-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20), 10)
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-41bf32b93d30a009"></a>

## mw_reversal_vwap20~neut_vol

- ID：`41bf32b93d30a009`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ba970f639369393e (neut_vol)
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0357 / 0.0193。

登记表达式或插件说明：

```text
cs_neutralize((-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-43028c700b4631a9"></a>

## mw_reversal_vwap20~resid_rev20

- ID：`43028c700b4631a9`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ba970f639369393e (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0414 / 0.0314。

登记表达式或插件说明：

```text
cs_neutralize((-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 20) / rolling_sum(turnover, 20), close / lag(close, 20) - 1)
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-24341cb159d15c4f"></a>

## mw_reversal_vwap20~w0.5

- ID：`24341cb159d15c4f`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ba970f639369393e (w0.5)
- 原判定：pass_mean+style:mom20；历史均值 / 最差年 RankIC：0.0512 / 0.0310。

登记表达式或插件说明：

```text
-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 10) / rolling_sum(turnover, 10)
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-7209420695329af7"></a>

## mw_reversal_vwap20~w2

- ID：`7209420695329af7`；归属：active_396, research_597, pool_current。
- 机制：new:money_weighted_reversal（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of ba970f639369393e (w2)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0698 / 0.0496。

登记表达式或插件说明：

```text
-rolling_sum((vwap / lag(vwap, 1) - 1) * turnover, 40) / rolling_sum(turnover, 40)
```

- 父因子：[ba970f639369393e](llm.md#f-ba970f639369393e)。

<a id="f-825df634fd3d9d30"></a>

## range20_low~tsz60

- ID：`825df634fd3d9d30`；归属：active_396, research_597, pool_current。
- 机制：低波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 974250cf2f6bbb65 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0369 / 0.0276。

登记表达式或插件说明：

```text
ts_zscore((-rolling_mean(log(high / low), 20)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(-rolling_mean(log(high / low), 20), 60)
```

- 父因子：[974250cf2f6bbb65](classic.md#f-974250cf2f6bbb65)。

<a id="f-f0b79428ced7dd9c"></a>

## ret_am~ema10~ema5

- ID：`f0b79428ced7dd9c`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 2f5fe26c8cb04ec4 (ema5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0479 / 0.0233。

登记表达式或插件说明：

```text
ema((ema(im_ret_am, 10)), 5)
```

规范式 / 计算标识：

```text
ema(ema(im_ret_am, 10), 5)
```

- 父因子：[2f5fe26c8cb04ec4](minute.md#f-2f5fe26c8cb04ec4)。

<a id="f-bb8c69a28ae6c7b1"></a>

## ret_am~m20_ncap~ema10

- ID：`bb8c69a28ae6c7b1`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 5a6045aa9d2d2013 (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0439 / 0.0228。

登记表达式或插件说明：

```text
ema((cs_neutralize(cs_rank(rolling_mean(im_ret_am, 20)), log_cap)), 10)
```

规范式 / 计算标识：

```text
ema(cs_neutralize(cs_rank(rolling_mean(im_ret_am, 20)), log_cap), 10)
```

- 父因子：[5a6045aa9d2d2013](minute.md#f-5a6045aa9d2d2013)。

<a id="f-1dd2c2de87d14349"></a>

## ret_am~m20~w2

- ID：`1dd2c2de87d14349`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 06f23077fdc7a6e6 (w2)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0503 / 0.0258。

登记表达式或插件说明：

```text
rolling_mean(im_ret_am, 40)
```

- 父因子：[06f23077fdc7a6e6](minute.md#f-06f23077fdc7a6e6)。

<a id="f-39baf62b55cbdbc0"></a>

## ret_am~m60~w0.5

- ID：`39baf62b55cbdbc0`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of a1f29a9f163744b8 (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0501 / 0.0282。

登记表达式或插件说明：

```text
rolling_mean(im_ret_am, 30)
```

- 父因子：[a1f29a9f163744b8](minute.md#f-a1f29a9f163744b8)。

<a id="f-9b78ccbcba2c49b3"></a>

## ret_close30~d1~delta5

- ID：`9b78ccbcba2c49b3`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 21f290eb3d9adbd1 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0149 / 0.0097。

登记表达式或插件说明：

```text
delta((im_ret_close30), 5)
```

规范式 / 计算标识：

```text
delta(im_ret_close30, 5)
```

- 父因子：[21f290eb3d9adbd1](minute.md#f-21f290eb3d9adbd1)。

<a id="f-6bb2becb175ffa53"></a>

## ret_close30~d1~ema5

- ID：`6bb2becb175ffa53`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 21f290eb3d9adbd1 (ema5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0178 / 0.0058。

登记表达式或插件说明：

```text
ema((im_ret_close30), 5)
```

规范式 / 计算标识：

```text
ema(im_ret_close30, 5)
```

- 父因子：[21f290eb3d9adbd1](minute.md#f-21f290eb3d9adbd1)。

<a id="f-f4ef613309fc03bc"></a>

## ret_close30~d5_20~delta5

- ID：`f4ef613309fc03bc`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7d2b45d8b91ecfa3 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0111 / 0.0056。

登记表达式或插件说明：

```text
delta((rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20)), 5)
```

规范式 / 计算标识：

```text
delta(rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20), 5)
```

- 父因子：[7d2b45d8b91ecfa3](minute.md#f-7d2b45d8b91ecfa3)。

<a id="f-857b527011ebeafd"></a>

## ret_close30~d5_20~ema5

- ID：`857b527011ebeafd`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7d2b45d8b91ecfa3 (ema5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0129 / 0.0061。

登记表达式或插件说明：

```text
ema((rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20), 5)
```

- 父因子：[7d2b45d8b91ecfa3](minute.md#f-7d2b45d8b91ecfa3)。

<a id="f-7f7425a43a63c204"></a>

## ret_close30~d5_20~neut_cap

- ID：`7f7425a43a63c204`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7d2b45d8b91ecfa3 (neut_cap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0151 / 0.0107。

登记表达式或插件说明：

```text
cs_neutralize((rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20), log_cap)
```

- 父因子：[7d2b45d8b91ecfa3](minute.md#f-7d2b45d8b91ecfa3)。

<a id="f-e92e847a9ffa3463"></a>

## ret_close30~d5_20~w0.5

- ID：`e92e847a9ffa3463`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7d2b45d8b91ecfa3 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0161 / 0.0098。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 2) - rolling_mean(im_ret_close30, 10)
```

- 父因子：[7d2b45d8b91ecfa3](minute.md#f-7d2b45d8b91ecfa3)。

<a id="f-3a47d25df9030d9a"></a>

## ret_close30~d5_20~w2

- ID：`3a47d25df9030d9a`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7d2b45d8b91ecfa3 (w2)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0136 / 0.0075。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 10) - rolling_mean(im_ret_close30, 40)
```

- 父因子：[7d2b45d8b91ecfa3](minute.md#f-7d2b45d8b91ecfa3)。

<a id="f-56c79f13b60b5597"></a>

## ret_close30~d5_20~wmax2

- ID：`56c79f13b60b5597`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7d2b45d8b91ecfa3 (wmax2)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0166 / 0.0103。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 40)
```

- 父因子：[7d2b45d8b91ecfa3](minute.md#f-7d2b45d8b91ecfa3)。

<a id="f-6ded2844f499556b"></a>

## ret_close30~ema10~delta5

- ID：`6ded2844f499556b`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of ba3d6af128536bd8 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0160 / 0.0099。

登记表达式或插件说明：

```text
delta((ema(im_ret_close30, 10)), 5)
```

规范式 / 计算标识：

```text
delta(ema(im_ret_close30, 10), 5)
```

- 父因子：[ba3d6af128536bd8](minute.md#f-ba3d6af128536bd8)。

<a id="f-c3e42e9e3cb84e91"></a>

## ret_close30~ema10~tsz60

- ID：`c3e42e9e3cb84e91`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of ba3d6af128536bd8 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0168 / 0.0094。

登记表达式或插件说明：

```text
ts_zscore((ema(im_ret_close30, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_ret_close30, 10), 60)
```

- 父因子：[ba3d6af128536bd8](minute.md#f-ba3d6af128536bd8)。

<a id="f-4accd50952155290"></a>

## ret_close30~ema10~w2

- ID：`4accd50952155290`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of ba3d6af128536bd8 (w2)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0120 / -0.0052。

登记表达式或插件说明：

```text
ema(im_ret_close30, 20)
```

- 父因子：[ba3d6af128536bd8](minute.md#f-ba3d6af128536bd8)。

<a id="f-98e2f35edbf97bdb"></a>

## ret_close30~s20~neut_turn

- ID：`98e2f35edbf97bdb`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bbd791f76da738bd (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0275 / 0.0168。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_ret_close30, 20)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_ret_close30, 20), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[bbd791f76da738bd](minute.md#f-bbd791f76da738bd)。

<a id="f-9294b7b581be91e3"></a>

## ret_close30~s20~w0.5

- ID：`9294b7b581be91e3`；归属：research_597, pool_current。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bbd791f76da738bd (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0619 / 0.0471。

登记表达式或插件说明：

```text
rolling_std(im_ret_close30, 10)
```

- 父因子：[bbd791f76da738bd](minute.md#f-bbd791f76da738bd)。

<a id="f-6498f2bba96408c0"></a>

## ret_close30~tsz20~ema5

- ID：`6498f2bba96408c0`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 76275a9b6fb2e1ef (ema5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0170 / 0.0063。

登记表达式或插件说明：

```text
ema((ts_zscore(im_ret_close30, 20)), 5)
```

规范式 / 计算标识：

```text
ema(ts_zscore(im_ret_close30, 20), 5)
```

- 父因子：[76275a9b6fb2e1ef](minute.md#f-76275a9b6fb2e1ef)。

<a id="f-d0d0f0cc6fdaf21b"></a>

## ret_close30~tsz20~w0.5

- ID：`d0d0f0cc6fdaf21b`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 76275a9b6fb2e1ef (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0145 / 0.0069。

登记表达式或插件说明：

```text
ts_zscore(im_ret_close30, 10)
```

- 父因子：[76275a9b6fb2e1ef](minute.md#f-76275a9b6fb2e1ef)。

<a id="f-e53db75c8414f7f4"></a>

## ret_mid~ema10~neut_turn

- ID：`e53db75c8414f7f4`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of c9d657a9921ad331 (neut_turn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0246 / 0.0132。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_ret_mid, 10)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_ret_mid, 10), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[c9d657a9921ad331](minute.md#f-c9d657a9921ad331)。

<a id="f-cd4ffe74b0e971e6"></a>

## ret_mid~ema10~tsz60

- ID：`cd4ffe74b0e971e6`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of c9d657a9921ad331 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0170 / 0.0047。

登记表达式或插件说明：

```text
ts_zscore((ema(im_ret_mid, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_ret_mid, 10), 60)
```

- 父因子：[c9d657a9921ad331](minute.md#f-c9d657a9921ad331)。

<a id="f-c4dfc40c2176b56f"></a>

## ret_mid~ema10~w0.5

- ID：`c4dfc40c2176b56f`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of c9d657a9921ad331 (w0.5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0199 / 0.0063。

登记表达式或插件说明：

```text
ema(im_ret_mid, 5)
```

- 父因子：[c9d657a9921ad331](minute.md#f-c9d657a9921ad331)。

<a id="f-bc1eefc723359d50"></a>

## ret_mid~ema10~w2

- ID：`bc1eefc723359d50`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of c9d657a9921ad331 (w2)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0398 / 0.0239。

登记表达式或插件说明：

```text
ema(im_ret_mid, 20)
```

- 父因子：[c9d657a9921ad331](minute.md#f-c9d657a9921ad331)。

<a id="f-5745e01e925075b1"></a>

## ret_mid~m20~delta5

- ID：`5745e01e925075b1`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d0c9c20be2725941 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0103 / -0.0019。

登记表达式或插件说明：

```text
delta((rolling_mean(im_ret_mid, 20)), 5)
```

规范式 / 计算标识：

```text
delta(rolling_mean(im_ret_mid, 20), 5)
```

- 父因子：[d0c9c20be2725941](minute.md#f-d0c9c20be2725941)。

<a id="f-8aaa6ee114c3cbff"></a>

## ret_mid~m20~ema10

- ID：`8aaa6ee114c3cbff`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d0c9c20be2725941 (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0392 / 0.0268。

登记表达式或插件说明：

```text
ema((rolling_mean(im_ret_mid, 20)), 10)
```

规范式 / 计算标识：

```text
ema(rolling_mean(im_ret_mid, 20), 10)
```

- 父因子：[d0c9c20be2725941](minute.md#f-d0c9c20be2725941)。

<a id="f-91ca5aeb02e2e57e"></a>

## ret_mid~m20~w0.5

- ID：`91ca5aeb02e2e57e`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d0c9c20be2725941 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0312 / 0.0098。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 10)
```

- 父因子：[d0c9c20be2725941](minute.md#f-d0c9c20be2725941)。

<a id="f-ef05b5bfda0dfa5f"></a>

## ret_mid~m20~w2

- ID：`ef05b5bfda0dfa5f`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d0c9c20be2725941 (w2)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0407 / 0.0250。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 40)
```

- 父因子：[d0c9c20be2725941](minute.md#f-d0c9c20be2725941)。

<a id="f-23d382d82824b77d"></a>

## ret_mid~m5~ema5

- ID：`23d382d82824b77d`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 70f9df5636a15d54 (ema5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0294 / 0.0109。

登记表达式或插件说明：

```text
ema((rolling_mean(im_ret_mid, 5)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_mean(im_ret_mid, 5), 5)
```

- 父因子：[70f9df5636a15d54](minute.md#f-70f9df5636a15d54)。

<a id="f-6f9e46485def95ad"></a>

## ret_mid~m5~neut_cap

- ID：`6f9e46485def95ad`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 70f9df5636a15d54 (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0226 / 0.0076。

登记表达式或插件说明：

```text
cs_neutralize((rolling_mean(im_ret_mid, 5)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_mean(im_ret_mid, 5), log_cap)
```

- 父因子：[70f9df5636a15d54](minute.md#f-70f9df5636a15d54)。

<a id="f-2db4c622998221c0"></a>

## ret_mid~m5~w0.5

- ID：`2db4c622998221c0`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 70f9df5636a15d54 (w0.5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0094 / -0.0055。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 2)
```

- 父因子：[70f9df5636a15d54](minute.md#f-70f9df5636a15d54)。

<a id="f-6b2cdf90dc5428ef"></a>

## ret_pm~ema10~delta5

- ID：`6b2cdf90dc5428ef`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 9c2c4ddbb212620d (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0125 / -0.0051。

登记表达式或插件说明：

```text
delta((ema(im_ret_pm, 10)), 5)
```

规范式 / 计算标识：

```text
delta(ema(im_ret_pm, 10), 5)
```

- 父因子：[9c2c4ddbb212620d](minute.md#f-9c2c4ddbb212620d)。

<a id="f-08e0e5841ac84741"></a>

## ret_pm~ema10~tsz60

- ID：`08e0e5841ac84741`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 9c2c4ddbb212620d (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0149 / -0.0023。

登记表达式或插件说明：

```text
ts_zscore((ema(im_ret_pm, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_ret_pm, 10), 60)
```

- 父因子：[9c2c4ddbb212620d](minute.md#f-9c2c4ddbb212620d)。

<a id="f-5da2b1fed48d31aa"></a>

## ret_pm~ema10~w0.5

- ID：`5da2b1fed48d31aa`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 9c2c4ddbb212620d (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0174 / -0.0024。

登记表达式或插件说明：

```text
ema(im_ret_pm, 5)
```

- 父因子：[9c2c4ddbb212620d](minute.md#f-9c2c4ddbb212620d)。

<a id="f-5fc16d245b12931e"></a>

## ret_pm~ema10~w2

- ID：`5fc16d245b12931e`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 9c2c4ddbb212620d (w2)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0227 / 0.0069。

登记表达式或插件说明：

```text
ema(im_ret_pm, 20)
```

- 父因子：[9c2c4ddbb212620d](minute.md#f-9c2c4ddbb212620d)。

<a id="f-2e68c1b3fe0a63f9"></a>

## ret_pm~m20_nturn~delta5

- ID：`2e68c1b3fe0a63f9`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bf9495c0abbbfeb2 (delta5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0092 / 0.0015。

登记表达式或插件说明：

```text
delta((cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20)))), 5)
```

规范式 / 计算标识：

```text
delta(cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20))), 5)
```

- 父因子：[bf9495c0abbbfeb2](minute.md#f-bf9495c0abbbfeb2)。

<a id="f-b6ee187bf2dca424"></a>

## ret_pm~m20_nturn~ema10

- ID：`b6ee187bf2dca424`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bf9495c0abbbfeb2 (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0201 / 0.0081。

登记表达式或插件说明：

```text
ema((cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20)))), 10)
```

规范式 / 计算标识：

```text
ema(cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20))), 10)
```

- 父因子：[bf9495c0abbbfeb2](minute.md#f-bf9495c0abbbfeb2)。

<a id="f-92d9efe99f86fb79"></a>

## ret_pm~m20_nturn~neut_cap

- ID：`92d9efe99f86fb79`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bf9495c0abbbfeb2 (neut_cap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0241 / 0.0096。

登记表达式或插件说明：

```text
cs_neutralize((cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20)))), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20))), log_cap)
```

- 父因子：[bf9495c0abbbfeb2](minute.md#f-bf9495c0abbbfeb2)。

<a id="f-b0d206f7bddb100d"></a>

## ret_pm~m20_nturn~w0.5

- ID：`b0d206f7bddb100d`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bf9495c0abbbfeb2 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0173 / 0.0055。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 10)), cs_rank(rolling_mean(turnover, 10)))
```

- 父因子：[bf9495c0abbbfeb2](minute.md#f-bf9495c0abbbfeb2)。

<a id="f-41fde7848526d455"></a>

## ret_pm~m20_nturn~w2

- ID：`41fde7848526d455`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of bf9495c0abbbfeb2 (w2)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0250 / 0.0122。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 40)), cs_rank(rolling_mean(turnover, 40)))
```

- 父因子：[bf9495c0abbbfeb2](minute.md#f-bf9495c0abbbfeb2)。

<a id="f-fccfbf6bfa1f60c6"></a>

## ret_pm~m5~ema5

- ID：`fccfbf6bfa1f60c6`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7ffb73b194b713c9 (ema5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0133 / 0.0023。

登记表达式或插件说明：

```text
ema((rolling_mean(im_ret_pm, 5)), 5)
```

规范式 / 计算标识：

```text
ema(rolling_mean(im_ret_pm, 5), 5)
```

- 父因子：[7ffb73b194b713c9](minute.md#f-7ffb73b194b713c9)。

<a id="f-68a17a9f21da5140"></a>

## ret_pm~m5~w0.5

- ID：`68a17a9f21da5140`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 7ffb73b194b713c9 (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0141 / -0.0047。

登记表达式或插件说明：

```text
rolling_mean(im_ret_pm, 2)
```

- 父因子：[7ffb73b194b713c9](minute.md#f-7ffb73b194b713c9)。

<a id="f-9274a3ce1a9a0ae4"></a>

## ret_pm~m60~w0.5

- ID：`9274a3ce1a9a0ae4`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of c4d415dd1e7232bf (w0.5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0248 / 0.0166。

登记表达式或插件说明：

```text
rolling_mean(im_ret_pm, 30)
```

- 父因子：[c4d415dd1e7232bf](minute.md#f-c4d415dd1e7232bf)。

<a id="f-84699c8144e66581"></a>

## ret_pm~s20~w0.5

- ID：`84699c8144e66581`；归属：research_597, pool_current。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 4f9de2867b8880e2 (w0.5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0626 / 0.0507。

登记表达式或插件说明：

```text
rolling_std(im_ret_pm, 10)
```

- 父因子：[4f9de2867b8880e2](minute.md#f-4f9de2867b8880e2)。

<a id="f-8552a6ae35fe40fb"></a>

## rv~d1~neut_cap

- ID：`8552a6ae35fe40fb`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 405777b8030fb38a (neut_cap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0668 / 0.0558。

登记表达式或插件说明：

```text
cs_neutralize((im_rv), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(im_rv, log_cap)
```

- 父因子：[405777b8030fb38a](minute.md#f-405777b8030fb38a)。

<a id="f-9e24e5bb528cb157"></a>

## rv~ema10~neut_cap

- ID：`9e24e5bb528cb157`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d52d1e858c01f1f (neut_cap)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0750 / 0.0602。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_rv, 10)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_rv, 10), log_cap)
```

- 父因子：[0d52d1e858c01f1f](minute.md#f-0d52d1e858c01f1f)。

<a id="f-4651e87b885c748e"></a>

## rv~ema10~neut_turn

- ID：`4651e87b885c748e`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d52d1e858c01f1f (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0416 / 0.0272。

登记表达式或插件说明：

```text
cs_neutralize((ema(im_rv, 10)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(ema(im_rv, 10), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[0d52d1e858c01f1f](minute.md#f-0d52d1e858c01f1f)。

<a id="f-446c43c8245f9dd1"></a>

## rv~ema10~tsz60

- ID：`446c43c8245f9dd1`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 0d52d1e858c01f1f (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0410 / 0.0281。

登记表达式或插件说明：

```text
ts_zscore((ema(im_rv, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_rv, 10), 60)
```

- 父因子：[0d52d1e858c01f1f](minute.md#f-0d52d1e858c01f1f)。

<a id="f-ae99ebd50cdf4e7c"></a>

## rv~m20_ncap~delta5

- ID：`ae99ebd50cdf4e7c`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 76e81713794c14cd (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0259 / 0.0061。

登记表达式或插件说明：

```text
delta((cs_neutralize(cs_rank(rolling_mean(im_rv, 20)), log_cap)), 5)
```

规范式 / 计算标识：

```text
delta(cs_neutralize(cs_rank(rolling_mean(im_rv, 20)), log_cap), 5)
```

- 父因子：[76e81713794c14cd](minute.md#f-76e81713794c14cd)。

<a id="f-721c024adee0c7eb"></a>

## rv~m20_ncap~neut_vol

- ID：`721c024adee0c7eb`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 76e81713794c14cd (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0300 / 0.0163。

登记表达式或插件说明：

```text
cs_neutralize((cs_neutralize(cs_rank(rolling_mean(im_rv, 20)), log_cap)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(cs_neutralize(cs_rank(rolling_mean(im_rv, 20)), log_cap), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[76e81713794c14cd](minute.md#f-76e81713794c14cd)。

<a id="f-d86d589784e2a4f0"></a>

## rv~m20_ncap~w2

- ID：`d86d589784e2a4f0`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 76e81713794c14cd (w2)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0582 / 0.0500。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rv, 40)), log_cap)
```

- 父因子：[76e81713794c14cd](minute.md#f-76e81713794c14cd)。

<a id="f-4cd540c152878a87"></a>

## rv~s20~delta5

- ID：`4cd540c152878a87`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 6979cda1e5b3866a (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0180 / 0.0025。

登记表达式或插件说明：

```text
delta((rolling_std(im_rv, 20)), 5)
```

规范式 / 计算标识：

```text
delta(rolling_std(im_rv, 20), 5)
```

- 父因子：[6979cda1e5b3866a](minute.md#f-6979cda1e5b3866a)。

<a id="f-9fa49cdb1e35062d"></a>

## rv~s20~neut_cap

- ID：`9fa49cdb1e35062d`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 6979cda1e5b3866a (neut_cap)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0742 / 0.0508。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_rv, 20)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_rv, 20), log_cap)
```

- 父因子：[6979cda1e5b3866a](minute.md#f-6979cda1e5b3866a)。

<a id="f-e53d837b763a5ea3"></a>

## rv~s20~neut_turn

- ID：`e53d837b763a5ea3`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 6979cda1e5b3866a (neut_turn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0252 / 0.0061。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_rv, 20)), cs_rank(rolling_mean(turnover, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_rv, 20), cs_rank(rolling_mean(turnover, 20)))
```

- 父因子：[6979cda1e5b3866a](minute.md#f-6979cda1e5b3866a)。

<a id="f-8caab15aafd09550"></a>

## rv~s20~neut_vol

- ID：`8caab15aafd09550`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 6979cda1e5b3866a (neut_vol)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0089 / -0.0052。

登记表达式或插件说明：

```text
cs_neutralize((rolling_std(im_rv, 20)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(rolling_std(im_rv, 20), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[6979cda1e5b3866a](minute.md#f-6979cda1e5b3866a)。

<a id="f-5e19f1925bd88f27"></a>

## rv~s20~w0.5

- ID：`5e19f1925bd88f27`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 6979cda1e5b3866a (w0.5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0747 / 0.0614。

登记表达式或插件说明：

```text
rolling_std(im_rv, 10)
```

- 父因子：[6979cda1e5b3866a](minute.md#f-6979cda1e5b3866a)。

<a id="f-994bbc864c127e0c"></a>

## size_neutral_turn20~delta5

- ID：`994bbc864c127e0c`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 6b95eea15d64187e (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0385 / 0.0142。

登记表达式或插件说明：

```text
delta((-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap)), 5)
```

规范式 / 计算标识：

```text
delta(-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap), 5)
```

- 父因子：[6b95eea15d64187e](classic.md#f-6b95eea15d64187e)。

<a id="f-e6f24a98bc0b8bc4"></a>

## size_neutral_turn20~neut_vol

- ID：`e6f24a98bc0b8bc4`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 6b95eea15d64187e (neut_vol)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0312 / 0.0181。

登记表达式或插件说明：

```text
cs_neutralize((-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap)), cs_rank(rolling_std(ret, 20)))
```

规范式 / 计算标识：

```text
cs_neutralize(-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap), cs_rank(rolling_std(ret, 20)))
```

- 父因子：[6b95eea15d64187e](classic.md#f-6b95eea15d64187e)。

<a id="f-a1e10694416f9fa4"></a>

## size_neutral_turn20~tsz60

- ID：`a1e10694416f9fa4`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 6b95eea15d64187e (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0418 / 0.0298。

登记表达式或插件说明：

```text
ts_zscore((-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(-cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap), 60)
```

- 父因子：[6b95eea15d64187e](classic.md#f-6b95eea15d64187e)。

<a id="f-94b3bfd4d4f45b9e"></a>

## turn20_low~delta5

- ID：`94b3bfd4d4f45b9e`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 0a38584bd0558cdb (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0320 / 0.0068。

登记表达式或插件说明：

```text
delta((-rolling_mean(turnover, 20)), 5)
```

规范式 / 计算标识：

```text
delta(-rolling_mean(turnover, 20), 5)
```

- 父因子：[0a38584bd0558cdb](classic.md#f-0a38584bd0558cdb)。

<a id="f-3d25d60c43c2fdcd"></a>

## turn20_low~neut_cap

- ID：`3d25d60c43c2fdcd`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 0a38584bd0558cdb (neut_cap)
- 原判定：pass_worst+style:turnover20；历史均值 / 最差年 RankIC：0.0733 / 0.0518。

登记表达式或插件说明：

```text
cs_neutralize((-rolling_mean(turnover, 20)), log_cap)
```

规范式 / 计算标识：

```text
cs_neutralize(-rolling_mean(turnover, 20), log_cap)
```

- 父因子：[0a38584bd0558cdb](classic.md#f-0a38584bd0558cdb)。

<a id="f-9a953c9d5f08ae17"></a>

## turn20_low~tsz60

- ID：`9a953c9d5f08ae17`；归属：active_396, research_597, pool_current。
- 机制：换手率（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 0a38584bd0558cdb (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0455 / 0.0343。

登记表达式或插件说明：

```text
ts_zscore((-rolling_mean(turnover, 20)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(-rolling_mean(turnover, 20), 60)
```

- 父因子：[0a38584bd0558cdb](classic.md#f-0a38584bd0558cdb)。

<a id="f-3863ace55113aea2"></a>

## updown~ema10~delta5

- ID：`3863ace55113aea2`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 09b4c488d8ec8072 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0134 / -0.0016。

登记表达式或插件说明：

```text
delta((ema(im_updown, 10)), 5)
```

规范式 / 计算标识：

```text
delta(ema(im_updown, 10), 5)
```

- 父因子：[09b4c488d8ec8072](minute.md#f-09b4c488d8ec8072)。

<a id="f-7e413ade1294d762"></a>

## updown~ema10~tsz60

- ID：`7e413ade1294d762`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of 09b4c488d8ec8072 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0301 / 0.0135。

登记表达式或插件说明：

```text
ts_zscore((ema(im_updown, 10)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(ema(im_updown, 10), 60)
```

- 父因子：[09b4c488d8ec8072](minute.md#f-09b4c488d8ec8072)。

<a id="f-e69c94a3dd0094b6"></a>

## updown~m20_ncap~delta5

- ID：`e69c94a3dd0094b6`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d7bcfe51dcfc0c17 (delta5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0168 / 0.0047。

登记表达式或插件说明：

```text
delta((cs_neutralize(cs_rank(rolling_mean(im_updown, 20)), log_cap)), 5)
```

规范式 / 计算标识：

```text
delta(cs_neutralize(cs_rank(rolling_mean(im_updown, 20)), log_cap), 5)
```

- 父因子：[d7bcfe51dcfc0c17](minute.md#f-d7bcfe51dcfc0c17)。

<a id="f-8e2eddcbcd8090cd"></a>

## updown~m20_ncap~resid_rev20

- ID：`8e2eddcbcd8090cd`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d7bcfe51dcfc0c17 (resid_rev20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0384 / 0.0292。

登记表达式或插件说明：

```text
cs_neutralize((cs_neutralize(cs_rank(rolling_mean(im_updown, 20)), log_cap)), close / lag(close, 20) - 1)
```

规范式 / 计算标识：

```text
cs_neutralize(cs_neutralize(cs_rank(rolling_mean(im_updown, 20)), log_cap), close / lag(close, 20) - 1)
```

- 父因子：[d7bcfe51dcfc0c17](minute.md#f-d7bcfe51dcfc0c17)。

<a id="f-73d87313c82767a0"></a>

## updown~m20_ncap~w0.5

- ID：`73d87313c82767a0`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d7bcfe51dcfc0c17 (w0.5)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0547 / 0.0368。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_updown, 10)), log_cap)
```

- 父因子：[d7bcfe51dcfc0c17](minute.md#f-d7bcfe51dcfc0c17)。

<a id="f-fab4baad5b11b3b3"></a>

## updown~m20_ncap~w2

- ID：`fab4baad5b11b3b3`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：variant of d7bcfe51dcfc0c17 (w2)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0566 / 0.0454。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_updown, 40)), log_cap)
```

- 父因子：[d7bcfe51dcfc0c17](minute.md#f-d7bcfe51dcfc0c17)。

<a id="f-2ac39953a9113543"></a>

## vol20_low~tsz60

- ID：`2ac39953a9113543`；归属：active_396, research_597, pool_current。
- 机制：低波动（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：variant of 2102e7b0aa51c223 (tsz60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0336 / 0.0242。

登记表达式或插件说明：

```text
ts_zscore((-rolling_std(ret, 20)), 60)
```

规范式 / 计算标识：

```text
ts_zscore(-rolling_std(ret, 20), 60)
```

- 父因子：[2102e7b0aa51c223](classic.md#f-2102e7b0aa51c223)。
