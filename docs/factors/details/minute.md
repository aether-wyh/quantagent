# 分钟聚合

[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)

原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。

<a id="f-a320535175f55c65"></a>

## amihud~d1

- ID：`a320535175f55c65`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (d1)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0684 / 0.0404。

登记表达式或插件说明：

```text
im_amihud
```


<a id="f-f7cb9ae8fdc7ac2e"></a>

## amihud~d5_20

- ID：`f7cb9ae8fdc7ac2e`；归属：research_597, pool_current。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0345 / 0.0096。

登记表达式或插件说明：

```text
rolling_mean(im_amihud, 5) - rolling_mean(im_amihud, 20)
```


<a id="f-f7d7b129d6cecf3d"></a>

## amihud~ema10

- ID：`f7d7b129d6cecf3d`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0602 / 0.0321。

登记表达式或插件说明：

```text
ema(im_amihud, 10)
```


<a id="f-e23e23bd7e6e4337"></a>

## amihud~m20

- ID：`e23e23bd7e6e4337`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (m20)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0507 / 0.0252。

登记表达式或插件说明：

```text
rolling_mean(im_amihud, 20)
```


<a id="f-f3515e9d48765df6"></a>

## amihud~m20_ncap

- ID：`f3515e9d48765df6`；归属：research_597, pool_current。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (m20_ncap)
- 原判定：pass_mean+style:turnover20；历史均值 / 最差年 RankIC：0.0590 / 0.0399。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_amihud, 20)), log_cap)
```


<a id="f-64c9a96923562ebb"></a>

## amihud~m20_nturn

- ID：`64c9a96923562ebb`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0358 / 0.0058。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_amihud, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-7b0ceba3cc4768f9"></a>

## amihud~m5

- ID：`7b0ceba3cc4768f9`；归属：research_597, pool_current。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (m5)
- 原判定：pass_mean+style:size；历史均值 / 最差年 RankIC：0.0623 / 0.0344。

登记表达式或插件说明：

```text
rolling_mean(im_amihud, 5)
```


<a id="f-c0eb32a5ee72307c"></a>

## amihud~m60

- ID：`c0eb32a5ee72307c`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0386 / 0.0136。

登记表达式或插件说明：

```text
rolling_mean(im_amihud, 60)
```


<a id="f-59ec28459a98063d"></a>

## amihud~s20

- ID：`59ec28459a98063d`；归属：历史候选，未列入上述集合。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0244 / 0.0149。

登记表达式或插件说明：

```text
rolling_std(im_amihud, 20)
```


<a id="f-141d59f9bf16a3a4"></a>

## amihud~tsz20

- ID：`141d59f9bf16a3a4`；归属：research_597, pool_current。
- 机制：minute:amihud（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_amihud aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0334 / 0.0154。

登记表达式或插件说明：

```text
ts_zscore(im_amihud, 20)
```


<a id="f-2b4882466aa1a92d"></a>

## big_ret~d1

- ID：`2b4882466aa1a92d`；归属：历史候选，未列入上述集合。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0143 / 0.0067。

登记表达式或插件说明：

```text
im_big_ret
```


<a id="f-6fbbc80dfa1ae7a9"></a>

## big_ret~d5_20

- ID：`6fbbc80dfa1ae7a9`；归属：历史候选，未列入上述集合。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0120 / 0.0029。

登记表达式或插件说明：

```text
rolling_mean(im_big_ret, 5) - rolling_mean(im_big_ret, 20)
```


<a id="f-01bb298acb7af999"></a>

## big_ret~ema10

- ID：`01bb298acb7af999`；归属：research_597, pool_current。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0368 / 0.0139。

登记表达式或插件说明：

```text
ema(im_big_ret, 10)
```


<a id="f-54f0f65f70b226e0"></a>

## big_ret~m20

- ID：`54f0f65f70b226e0`；归属：research_597, pool_current。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0387 / 0.0060。

登记表达式或插件说明：

```text
rolling_mean(im_big_ret, 20)
```


<a id="f-a43c1561af62c45c"></a>

## big_ret~m20_ncap

- ID：`a43c1561af62c45c`；归属：历史候选，未列入上述集合。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0370 / 0.0101。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_big_ret, 20)), log_cap)
```


<a id="f-02621fc9b8ba9644"></a>

## big_ret~m20_nturn

- ID：`02621fc9b8ba9644`；归属：历史候选，未列入上述集合。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0276 / -0.0029。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_big_ret, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-892379b03de12e61"></a>

## big_ret~m5

- ID：`892379b03de12e61`；归属：历史候选，未列入上述集合。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0290 / 0.0113。

登记表达式或插件说明：

```text
rolling_mean(im_big_ret, 5)
```


<a id="f-20694fb59daa5a64"></a>

## big_ret~m60

- ID：`20694fb59daa5a64`；归属：research_597, pool_current。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0367 / 0.0042。

登记表达式或插件说明：

```text
rolling_mean(im_big_ret, 60)
```


<a id="f-e46aad539ea3b294"></a>

## big_ret~s20

- ID：`e46aad539ea3b294`；归属：research_597, pool_current。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (s20)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0612 / 0.0506。

登记表达式或插件说明：

```text
rolling_std(im_big_ret, 20)
```


<a id="f-fabfe12c71242eda"></a>

## big_ret~tsz20

- ID：`fabfe12c71242eda`；归属：历史候选，未列入上述集合。
- 机制：minute:big_ret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_ret aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0082 / 0.0018。

登记表达式或插件说明：

```text
ts_zscore(im_big_ret, 20)
```


<a id="f-978f7306719f0f48"></a>

## big_vwap_dev~d1

- ID：`978f7306719f0f48`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0273 / 0.0187。

登记表达式或插件说明：

```text
im_big_vwap_dev
```


<a id="f-66802849199abdb0"></a>

## big_vwap_dev~d5_20

- ID：`66802849199abdb0`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0149 / 0.0053。

登记表达式或插件说明：

```text
rolling_mean(im_big_vwap_dev, 5) - rolling_mean(im_big_vwap_dev, 20)
```


<a id="f-761c35fb95139218"></a>

## big_vwap_dev~ema10

- ID：`761c35fb95139218`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (ema10)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0546 / 0.0382。

登记表达式或插件说明：

```text
ema(im_big_vwap_dev, 10)
```


<a id="f-87f4376998539635"></a>

## big_vwap_dev~m20

- ID：`87f4376998539635`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (m20)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0544 / 0.0432。

登记表达式或插件说明：

```text
rolling_mean(im_big_vwap_dev, 20)
```


<a id="f-2bbc315b460734fb"></a>

## big_vwap_dev~m20_ncap

- ID：`2bbc315b460734fb`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0532 / 0.0430。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_big_vwap_dev, 20)), log_cap)
```


<a id="f-0d833d8b4a9a766a"></a>

## big_vwap_dev~m20_nturn

- ID：`0d833d8b4a9a766a`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0350 / 0.0232。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_big_vwap_dev, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-b705e5d2364bd026"></a>

## big_vwap_dev~m5

- ID：`b705e5d2364bd026`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0448 / 0.0313。

登记表达式或插件说明：

```text
rolling_mean(im_big_vwap_dev, 5)
```


<a id="f-c812244b62c84101"></a>

## big_vwap_dev~m60

- ID：`c812244b62c84101`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (m60)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0510 / 0.0433。

登记表达式或插件说明：

```text
rolling_mean(im_big_vwap_dev, 60)
```


<a id="f-0b193b55a101b661"></a>

## big_vwap_dev~s20

- ID：`0b193b55a101b661`；归属：research_597, pool_current。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (s20)
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0694 / 0.0544。

登记表达式或插件说明：

```text
rolling_std(im_big_vwap_dev, 20)
```


<a id="f-780fcec51feed68d"></a>

## big_vwap_dev~tsz20

- ID：`780fcec51feed68d`；归属：历史候选，未列入上述集合。
- 机制：minute:big_vwap_dev（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_big_vwap_dev aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0121 / 0.0056。

登记表达式或插件说明：

```text
ts_zscore(im_big_vwap_dev, 20)
```


<a id="f-87880bddc171875a"></a>

## bigamt_share~d1

- ID：`87880bddc171875a`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0091 / -0.0221。

登记表达式或插件说明：

```text
im_bigamt_share
```


<a id="f-b15672a05e707c34"></a>

## bigamt_share~d5_20

- ID：`b15672a05e707c34`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0054 / -0.0055。

登记表达式或插件说明：

```text
rolling_mean(im_bigamt_share, 5) - rolling_mean(im_bigamt_share, 20)
```


<a id="f-aeb8644aa253fb28"></a>

## bigamt_share~ema10

- ID：`aeb8644aa253fb28`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0066 / -0.0335。

登记表达式或插件说明：

```text
ema(im_bigamt_share, 10)
```


<a id="f-cf2f179f7ff74908"></a>

## bigamt_share~m20

- ID：`cf2f179f7ff74908`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0153 / -0.0261。

登记表达式或插件说明：

```text
rolling_mean(im_bigamt_share, 20)
```


<a id="f-b06faee47f311e4e"></a>

## bigamt_share~m20_ncap

- ID：`b06faee47f311e4e`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (m20_ncap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0102 / -0.0255。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_bigamt_share, 20)), log_cap)
```


<a id="f-651f8c9532a884fa"></a>

## bigamt_share~m20_nturn

- ID：`651f8c9532a884fa`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0048 / -0.0352。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_bigamt_share, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-462eac60d4394a00"></a>

## bigamt_share~m5

- ID：`462eac60d4394a00`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0112 / -0.0246。

登记表达式或插件说明：

```text
rolling_mean(im_bigamt_share, 5)
```


<a id="f-690f59eab73036e4"></a>

## bigamt_share~m60

- ID：`690f59eab73036e4`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0171 / -0.0198。

登记表达式或插件说明：

```text
rolling_mean(im_bigamt_share, 60)
```


<a id="f-646d8501bc07769d"></a>

## bigamt_share~s20

- ID：`646d8501bc07769d`；归属：research_597, pool_current。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0355 / 0.0216。

登记表达式或插件说明：

```text
rolling_std(im_bigamt_share, 20)
```


<a id="f-52b91ce31060109d"></a>

## bigamt_share~tsz20

- ID：`52b91ce31060109d`；归属：历史候选，未列入上述集合。
- 机制：minute:bigamt_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_bigamt_share aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0039 / -0.0010。

登记表达式或插件说明：

```text
ts_zscore(im_bigamt_share, 20)
```


<a id="f-ae0eea54e82114ef"></a>

## close_vwap~d1

- ID：`ae0eea54e82114ef`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0136 / 0.0003。

登记表达式或插件说明：

```text
im_close_vwap
```


<a id="f-33a55b477bbbd39e"></a>

## close_vwap~d5_20

- ID：`33a55b477bbbd39e`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0131 / -0.0108。

登记表达式或插件说明：

```text
rolling_mean(im_close_vwap, 5) - rolling_mean(im_close_vwap, 20)
```


<a id="f-c775849da66d5501"></a>

## close_vwap~ema10

- ID：`c775849da66d5501`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0225 / 0.0110。

登记表达式或插件说明：

```text
ema(im_close_vwap, 10)
```


<a id="f-7025d1b094d42a4e"></a>

## close_vwap~m20

- ID：`7025d1b094d42a4e`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (m20)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0240 / 0.0159。

登记表达式或插件说明：

```text
rolling_mean(im_close_vwap, 20)
```


<a id="f-d0d3fbcc8de6fe45"></a>

## close_vwap~m20_ncap

- ID：`d0d3fbcc8de6fe45`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0238 / 0.0171。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_close_vwap, 20)), log_cap)
```


<a id="f-5cd688f86c4beecd"></a>

## close_vwap~m20_nturn

- ID：`5cd688f86c4beecd`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0268 / 0.0180。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_close_vwap, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-a76e33a4d2ed203e"></a>

## close_vwap~m5

- ID：`a76e33a4d2ed203e`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0180 / -0.0014。

登记表达式或插件说明：

```text
rolling_mean(im_close_vwap, 5)
```


<a id="f-13e777889362641e"></a>

## close_vwap~m60

- ID：`13e777889362641e`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0188 / 0.0051。

登记表达式或插件说明：

```text
rolling_mean(im_close_vwap, 60)
```


<a id="f-6c3f9bb77332c860"></a>

## close_vwap~s20

- ID：`6c3f9bb77332c860`；归属：research_597, pool_current。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (s20)
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0674 / 0.0565。

登记表达式或插件说明：

```text
rolling_std(im_close_vwap, 20)
```


<a id="f-6f01aa02581e5333"></a>

## close_vwap~tsz20

- ID：`6f01aa02581e5333`；归属：历史候选，未列入上述集合。
- 机制：minute:close_vwap（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_close_vwap aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0105 / -0.0041。

登记表达式或插件说明：

```text
ts_zscore(im_close_vwap, 20)
```


<a id="f-7cd496d65f00fac5"></a>

## hl_time~d1

- ID：`7cd496d65f00fac5`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0097 / 0.0026。

登记表达式或插件说明：

```text
im_hl_time
```


<a id="f-f826d2529f1eafd7"></a>

## hl_time~d5_20

- ID：`f826d2529f1eafd7`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0061 / -0.0037。

登记表达式或插件说明：

```text
rolling_mean(im_hl_time, 5) - rolling_mean(im_hl_time, 20)
```


<a id="f-b18001437931ff69"></a>

## hl_time~ema10

- ID：`b18001437931ff69`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0173 / 0.0068。

登记表达式或插件说明：

```text
ema(im_hl_time, 10)
```


<a id="f-a0efb0ac0d23f087"></a>

## hl_time~m20

- ID：`a0efb0ac0d23f087`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0155 / 0.0030。

登记表达式或插件说明：

```text
rolling_mean(im_hl_time, 20)
```


<a id="f-83cc02e50b6cb1ee"></a>

## hl_time~m20_ncap

- ID：`83cc02e50b6cb1ee`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (m20_ncap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0164 / 0.0064。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_hl_time, 20)), log_cap)
```


<a id="f-3104049d2f2bad92"></a>

## hl_time~m20_nturn

- ID：`3104049d2f2bad92`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0145 / 0.0005。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_hl_time, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-71ddb39d200ba3da"></a>

## hl_time~m5

- ID：`71ddb39d200ba3da`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0135 / 0.0054。

登记表达式或插件说明：

```text
rolling_mean(im_hl_time, 5)
```


<a id="f-bcccf176affba54e"></a>

## hl_time~m60

- ID：`bcccf176affba54e`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0112 / -0.0041。

登记表达式或插件说明：

```text
rolling_mean(im_hl_time, 60)
```


<a id="f-05bd4f34d956891e"></a>

## hl_time~s20

- ID：`05bd4f34d956891e`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0137 / 0.0021。

登记表达式或插件说明：

```text
rolling_std(im_hl_time, 20)
```


<a id="f-aecd6ed7292931e4"></a>

## hl_time~tsz20

- ID：`aecd6ed7292931e4`；归属：历史候选，未列入上述集合。
- 机制：minute:hl_time（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_hl_time aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0056 / -0.0012。

登记表达式或插件说明：

```text
ts_zscore(im_hl_time, 20)
```


<a id="f-4394db693cbf2288"></a>

## maxret~d1

- ID：`4394db693cbf2288`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (d1)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0655 / 0.0575。

登记表达式或插件说明：

```text
im_maxret
```


<a id="f-41d1f6c390dafa85"></a>

## maxret~d5_20

- ID：`41d1f6c390dafa85`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0168 / 0.0065。

登记表达式或插件说明：

```text
rolling_mean(im_maxret, 5) - rolling_mean(im_maxret, 20)
```


<a id="f-56d314292c98f620"></a>

## maxret~ema10

- ID：`56d314292c98f620`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0811 / 0.0710。

登记表达式或插件说明：

```text
ema(im_maxret, 10)
```


<a id="f-e918dce940a1d42a"></a>

## maxret~m20

- ID：`e918dce940a1d42a`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (m20)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0712 / 0.0614。

登记表达式或插件说明：

```text
rolling_mean(im_maxret, 20)
```


<a id="f-dd64347d71dbdfba"></a>

## maxret~m20_ncap

- ID：`dd64347d71dbdfba`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0757 / 0.0642。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), log_cap)
```


<a id="f-f11600694d47df0c"></a>

## maxret~m20_nturn

- ID：`f11600694d47df0c`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0464 / 0.0347。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_maxret, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-b00253b4d35a6c95"></a>

## maxret~m5

- ID：`b00253b4d35a6c95`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (m5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0749 / 0.0656。

登记表达式或插件说明：

```text
rolling_mean(im_maxret, 5)
```


<a id="f-05a50d3de578c195"></a>

## maxret~m60

- ID：`05a50d3de578c195`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (m60)
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0588 / 0.0489。

登记表达式或插件说明：

```text
rolling_mean(im_maxret, 60)
```


<a id="f-8795402becec7009"></a>

## maxret~s20

- ID：`8795402becec7009`；归属：research_597, pool_current。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (s20)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0604 / 0.0527。

登记表达式或插件说明：

```text
rolling_std(im_maxret, 20)
```


<a id="f-c1db2c589d2f71e8"></a>

## maxret~tsz20

- ID：`c1db2c589d2f71e8`；归属：历史候选，未列入上述集合。
- 机制：minute:maxret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_maxret aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0179 / 0.0104。

登记表达式或插件说明：

```text
ts_zscore(im_maxret, 20)
```


<a id="f-0745bead804f778d"></a>

## mdd~d1

- ID：`0745bead804f778d`；归属：research_597, pool_current。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (d1)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0579 / 0.0457。

登记表达式或插件说明：

```text
im_mdd
```


<a id="f-ab6d15ad39a54483"></a>

## mdd~d5_20

- ID：`ab6d15ad39a54483`；归属：历史候选，未列入上述集合。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0132 / -0.0278。

登记表达式或插件说明：

```text
rolling_mean(im_mdd, 5) - rolling_mean(im_mdd, 20)
```


<a id="f-1b613283deb667dc"></a>

## mdd~ema10

- ID：`1b613283deb667dc`；归属：历史候选，未列入上述集合。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0728 / 0.0600。

登记表达式或插件说明：

```text
ema(im_mdd, 10)
```


<a id="f-d1684fc40121a4a9"></a>

## mdd~m20

- ID：`d1684fc40121a4a9`；归属：历史候选，未列入上述集合。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (m20)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0644 / 0.0415。

登记表达式或插件说明：

```text
rolling_mean(im_mdd, 20)
```


<a id="f-69df13b2ae1c3a22"></a>

## mdd~m20_ncap

- ID：`69df13b2ae1c3a22`；归属：历史候选，未列入上述集合。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0652 / 0.0389。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_mdd, 20)), log_cap)
```


<a id="f-f3c4b22f7ccaa830"></a>

## mdd~m20_nturn

- ID：`f3c4b22f7ccaa830`；归属：research_597, pool_current。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0357 / 0.0150。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_mdd, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-2929f2cb3c2619d6"></a>

## mdd~m5

- ID：`2929f2cb3c2619d6`；归属：research_597, pool_current。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (m5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0696 / 0.0577。

登记表达式或插件说明：

```text
rolling_mean(im_mdd, 5)
```


<a id="f-39530085bb04040c"></a>

## mdd~m60

- ID：`39530085bb04040c`；归属：历史候选，未列入上述集合。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0548 / 0.0293。

登记表达式或插件说明：

```text
rolling_mean(im_mdd, 60)
```


<a id="f-33121b879c239a1c"></a>

## mdd~s20

- ID：`33121b879c239a1c`；归属：research_597, pool_current。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (s20)
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0521 / 0.0357。

登记表达式或插件说明：

```text
rolling_std(im_mdd, 20)
```


<a id="f-48de1ec448f8e260"></a>

## mdd~tsz20

- ID：`48de1ec448f8e260`；归属：历史候选，未列入上述集合。
- 机制：minute:mdd（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_mdd aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0104 / -0.0204。

登记表达式或插件说明：

```text
ts_zscore(im_mdd, 20)
```


<a id="f-e56bccc135d9d10f"></a>

## minret~d1

- ID：`e56bccc135d9d10f`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (d1)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0563 / 0.0500。

登记表达式或插件说明：

```text
im_minret
```


<a id="f-ee2bbdf653908caf"></a>

## minret~d5_20

- ID：`ee2bbdf653908caf`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0124 / 0.0030。

登记表达式或插件说明：

```text
rolling_mean(im_minret, 5) - rolling_mean(im_minret, 20)
```


<a id="f-dd8b34062ba8014d"></a>

## minret~ema10

- ID：`dd8b34062ba8014d`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0717 / 0.0663。

登记表达式或插件说明：

```text
ema(im_minret, 10)
```


<a id="f-a0e8e0fc37508810"></a>

## minret~m20

- ID：`a0e8e0fc37508810`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (m20)
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0621 / 0.0496。

登记表达式或插件说明：

```text
rolling_mean(im_minret, 20)
```


<a id="f-de041c3f3f1a3918"></a>

## minret~m20_ncap

- ID：`de041c3f3f1a3918`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0656 / 0.0469。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_minret, 20)), log_cap)
```


<a id="f-5c7ea136dfe8dec5"></a>

## minret~m20_nturn

- ID：`5c7ea136dfe8dec5`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0378 / 0.0316。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_minret, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-7c9f31cfcb31bb97"></a>

## minret~m5

- ID：`7c9f31cfcb31bb97`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (m5)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0658 / 0.0603。

登记表达式或插件说明：

```text
rolling_mean(im_minret, 5)
```


<a id="f-1cf57eb01c77c642"></a>

## minret~m60

- ID：`1cf57eb01c77c642`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0511 / 0.0338。

登记表达式或插件说明：

```text
rolling_mean(im_minret, 60)
```


<a id="f-b2dcc8a6223234b1"></a>

## minret~s20

- ID：`b2dcc8a6223234b1`；归属：research_597, pool_current。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (s20)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0509 / 0.0463。

登记表达式或插件说明：

```text
rolling_std(im_minret, 20)
```


<a id="f-e3847a3e08a18a4c"></a>

## minret~tsz20

- ID：`e3847a3e08a18a4c`；归属：历史候选，未列入上述集合。
- 机制：minute:minret（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_minret aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0134 / 0.0045。

登记表达式或插件说明：

```text
ts_zscore(im_minret, 20)
```


<a id="f-0edaa2b068588e5c"></a>

## path_eff~d1

- ID：`0edaa2b068588e5c`；归属：历史候选，未列入上述集合。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (d1)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0158 / 0.0091。

登记表达式或插件说明：

```text
im_path_eff
```


<a id="f-a1ff8f5e2eac6006"></a>

## path_eff~d5_20

- ID：`a1ff8f5e2eac6006`；归属：历史候选，未列入上述集合。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0086 / -0.0339。

登记表达式或插件说明：

```text
rolling_mean(im_path_eff, 5) - rolling_mean(im_path_eff, 20)
```


<a id="f-2be6b510a6d32520"></a>

## path_eff~ema10

- ID：`2be6b510a6d32520`；归属：research_597, pool_current。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0438 / 0.0331。

登记表达式或插件说明：

```text
ema(im_path_eff, 10)
```


<a id="f-14e4b3eacc085fc5"></a>

## path_eff~m20

- ID：`14e4b3eacc085fc5`；归属：research_597, pool_current。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (m20)
- 原判定：weak_signal+style:vol20；历史均值 / 最差年 RankIC：0.0408 / 0.0305。

登记表达式或插件说明：

```text
rolling_mean(im_path_eff, 20)
```


<a id="f-2be908dc4eb32736"></a>

## path_eff~m20_ncap

- ID：`2be908dc4eb32736`；归属：历史候选，未列入上述集合。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0447 / 0.0300。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_path_eff, 20)), log_cap)
```


<a id="f-5fd1e99f7ea3de61"></a>

## path_eff~m20_nturn

- ID：`5fd1e99f7ea3de61`；归属：历史候选，未列入上述集合。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0173 / 0.0109。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_path_eff, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-e09e33b58242ff56"></a>

## path_eff~m5

- ID：`e09e33b58242ff56`；归属：research_597, pool_current。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0339 / 0.0180。

登记表达式或插件说明：

```text
rolling_mean(im_path_eff, 5)
```


<a id="f-0c7e65eb2c60153e"></a>

## path_eff~m60

- ID：`0c7e65eb2c60153e`；归属：research_597, pool_current。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0404 / 0.0243。

登记表达式或插件说明：

```text
rolling_mean(im_path_eff, 60)
```


<a id="f-f08105aaf8878819"></a>

## path_eff~s20

- ID：`f08105aaf8878819`；归属：research_597, pool_current。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0409 / 0.0330。

登记表达式或插件说明：

```text
rolling_std(im_path_eff, 20)
```


<a id="f-0e97250c1e3332cc"></a>

## path_eff~tsz20

- ID：`0e97250c1e3332cc`；归属：历史候选，未列入上述集合。
- 机制：minute:path_eff（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_path_eff aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0069 / 0.0004。

登记表达式或插件说明：

```text
ts_zscore(im_path_eff, 20)
```


<a id="f-59aafd535729a1ae"></a>

## pos_share~d1

- ID：`59aafd535729a1ae`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (d1)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0523 / 0.0137。

登记表达式或插件说明：

```text
im_pos_share
```


<a id="f-d2e19dced054bb4a"></a>

## pos_share~d5_20

- ID：`d2e19dced054bb4a`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0145 / 0.0013。

登记表达式或插件说明：

```text
rolling_mean(im_pos_share, 5) - rolling_mean(im_pos_share, 20)
```


<a id="f-b8b1cfb4fdb5443b"></a>

## pos_share~ema10

- ID：`b8b1cfb4fdb5443b`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0474 / 0.0052。

登记表达式或插件说明：

```text
ema(im_pos_share, 10)
```


<a id="f-a5e9e7c2bbf737e3"></a>

## pos_share~m20

- ID：`a5e9e7c2bbf737e3`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (m20)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0457 / 0.0010。

登记表达式或插件说明：

```text
rolling_mean(im_pos_share, 20)
```


<a id="f-06974701748b38e1"></a>

## pos_share~m20_ncap

- ID：`06974701748b38e1`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0431 / 0.0017。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_pos_share, 20)), log_cap)
```


<a id="f-ff5ce2fc962c9dd6"></a>

## pos_share~m20_nturn

- ID：`ff5ce2fc962c9dd6`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0237 / -0.0228。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_pos_share, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-af4dbcf6367ae7fb"></a>

## pos_share~m5

- ID：`af4dbcf6367ae7fb`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (m5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0511 / 0.0105。

登记表达式或插件说明：

```text
rolling_mean(im_pos_share, 5)
```


<a id="f-6aa8018117ce3a95"></a>

## pos_share~m60

- ID：`6aa8018117ce3a95`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0373 / -0.0093。

登记表达式或插件说明：

```text
rolling_mean(im_pos_share, 60)
```


<a id="f-ba9d4b80e59f2d19"></a>

## pos_share~s20

- ID：`ba9d4b80e59f2d19`；归属：research_597, pool_current。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0495 / 0.0299。

登记表达式或插件说明：

```text
rolling_std(im_pos_share, 20)
```


<a id="f-051aecddd976e713"></a>

## pos_share~tsz20

- ID：`051aecddd976e713`；归属：历史候选，未列入上述集合。
- 机制：minute:pos_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pos_share aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0147 / 0.0078。

登记表达式或插件说明：

```text
ts_zscore(im_pos_share, 20)
```


<a id="f-22ec2519ad056942"></a>

## pv_corr_lag~d1

- ID：`22ec2519ad056942`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0038 / -0.0127。

登记表达式或插件说明：

```text
im_pv_corr_lag
```


<a id="f-8859eff7bde74bbe"></a>

## pv_corr_lag~d5_20

- ID：`8859eff7bde74bbe`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0012 / -0.0103。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr_lag, 5) - rolling_mean(im_pv_corr_lag, 20)
```


<a id="f-888b3ac1ca468103"></a>

## pv_corr_lag~ema10

- ID：`888b3ac1ca468103`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0052 / -0.0232。

登记表达式或插件说明：

```text
ema(im_pv_corr_lag, 10)
```


<a id="f-d5be7f13828913bf"></a>

## pv_corr_lag~m20

- ID：`d5be7f13828913bf`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (m20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0056 / -0.0254。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr_lag, 20)
```


<a id="f-05a450395cab7709"></a>

## pv_corr_lag~m20_ncap

- ID：`05a450395cab7709`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (m20_ncap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0047 / -0.0239。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_pv_corr_lag, 20)), log_cap)
```


<a id="f-dade7d5e76addbf6"></a>

## pv_corr_lag~m20_nturn

- ID：`dade7d5e76addbf6`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0051 / -0.0204。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_pv_corr_lag, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-065ae4bac878cf27"></a>

## pv_corr_lag~m5

- ID：`065ae4bac878cf27`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (m5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0029 / -0.0195。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr_lag, 5)
```


<a id="f-b3e49cb4ea0ca51b"></a>

## pv_corr_lag~m60

- ID：`b3e49cb4ea0ca51b`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (m60)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0107 / -0.0258。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr_lag, 60)
```


<a id="f-0f6765a78cf23e58"></a>

## pv_corr_lag~s20

- ID：`0f6765a78cf23e58`；归属：research_597, pool_current。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0277 / 0.0224。

登记表达式或插件说明：

```text
rolling_std(im_pv_corr_lag, 20)
```


<a id="f-946ed4c1646dcd5c"></a>

## pv_corr_lag~tsz20

- ID：`946ed4c1646dcd5c`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr_lag（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr_lag aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0018 / -0.0067。

登记表达式或插件说明：

```text
ts_zscore(im_pv_corr_lag, 20)
```


<a id="f-a66fbc8d6c393875"></a>

## pv_corr~d1

- ID：`a66fbc8d6c393875`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0151 / 0.0054。

登记表达式或插件说明：

```text
im_pv_corr
```


<a id="f-4cb0e67ed343d788"></a>

## pv_corr~d5_20

- ID：`4cb0e67ed343d788`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0092 / -0.0012。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr, 5) - rolling_mean(im_pv_corr, 20)
```


<a id="f-2669cbf4cf6adf73"></a>

## pv_corr~ema10

- ID：`2669cbf4cf6adf73`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0297 / 0.0159。

登记表达式或插件说明：

```text
ema(im_pv_corr, 10)
```


<a id="f-651ca3efff24722f"></a>

## pv_corr~m20

- ID：`651ca3efff24722f`；归属：research_597, pool_current。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0308 / 0.0134。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr, 20)
```


<a id="f-e5e6e7b2851d5906"></a>

## pv_corr~m20_ncap

- ID：`e5e6e7b2851d5906`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0295 / 0.0129。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_pv_corr, 20)), log_cap)
```


<a id="f-dd5839a12e797188"></a>

## pv_corr~m20_nturn

- ID：`dd5839a12e797188`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0190 / 0.0050。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_pv_corr, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-f3d39486b912bbfa"></a>

## pv_corr~m5

- ID：`f3d39486b912bbfa`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0234 / 0.0122。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr, 5)
```


<a id="f-516eab7463232178"></a>

## pv_corr~m60

- ID：`516eab7463232178`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0300 / 0.0122。

登记表达式或插件说明：

```text
rolling_mean(im_pv_corr, 60)
```


<a id="f-ab6dd4d10377f89d"></a>

## pv_corr~s20

- ID：`ab6dd4d10377f89d`；归属：research_597, pool_current。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0391 / 0.0323。

登记表达式或插件说明：

```text
rolling_std(im_pv_corr, 20)
```


<a id="f-9a1dad06bf6b81cd"></a>

## pv_corr~tsz20

- ID：`9a1dad06bf6b81cd`；归属：历史候选，未列入上述集合。
- 机制：minute:pv_corr（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_pv_corr aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0096 / 0.0007。

登记表达式或插件说明：

```text
ts_zscore(im_pv_corr, 20)
```


<a id="f-2f8c3934c83f6527"></a>

## ret_am~d1

- ID：`2f8c3934c83f6527`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0103 / -0.0198。

登记表达式或插件说明：

```text
im_ret_am
```


<a id="f-bcf96f5e383d42f0"></a>

## ret_am~d5_20

- ID：`bcf96f5e383d42f0`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0096 / -0.0163。

登记表达式或插件说明：

```text
rolling_mean(im_ret_am, 5) - rolling_mean(im_ret_am, 20)
```


<a id="f-2f5fe26c8cb04ec4"></a>

## ret_am~ema10

- ID：`2f5fe26c8cb04ec4`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0413 / 0.0205。

登记表达式或插件说明：

```text
ema(im_ret_am, 10)
```


<a id="f-06f23077fdc7a6e6"></a>

## ret_am~m20

- ID：`06f23077fdc7a6e6`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (m20)
- 原判定：weak_signal+style:mom20；历史均值 / 最差年 RankIC：0.0465 / 0.0183。

登记表达式或插件说明：

```text
rolling_mean(im_ret_am, 20)
```


<a id="f-5a6045aa9d2d2013"></a>

## ret_am~m20_ncap

- ID：`5a6045aa9d2d2013`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0455 / 0.0199。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_am, 20)), log_cap)
```


<a id="f-8de2eca5a0f82b86"></a>

## ret_am~m20_nturn

- ID：`8de2eca5a0f82b86`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0343 / 0.0065。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_am, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-62a64fa32a23132a"></a>

## ret_am~m5

- ID：`62a64fa32a23132a`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0313 / 0.0187。

登记表达式或插件说明：

```text
rolling_mean(im_ret_am, 5)
```


<a id="f-a1f29a9f163744b8"></a>

## ret_am~m60

- ID：`a1f29a9f163744b8`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0474 / 0.0256。

登记表达式或插件说明：

```text
rolling_mean(im_ret_am, 60)
```


<a id="f-0d5bea2217fae228"></a>

## ret_am~s20

- ID：`0d5bea2217fae228`；归属：research_597, pool_current。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (s20)
- 原判定：pass_mean+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0646 / 0.0474。

登记表达式或插件说明：

```text
rolling_std(im_ret_am, 20)
```


<a id="f-f160215a6831fb46"></a>

## ret_am~tsz20

- ID：`f160215a6831fb46`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_am aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0039 / -0.0121。

登记表达式或插件说明：

```text
ts_zscore(im_ret_am, 20)
```


<a id="f-21f290eb3d9adbd1"></a>

## ret_close30~d1

- ID：`21f290eb3d9adbd1`；归属：research_597, pool_current。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0176 / 0.0084。

登记表达式或插件说明：

```text
im_ret_close30
```


<a id="f-7d2b45d8b91ecfa3"></a>

## ret_close30~d5_20

- ID：`7d2b45d8b91ecfa3`；归属：research_597, pool_current。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0160 / 0.0118。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 5) - rolling_mean(im_ret_close30, 20)
```


<a id="f-ba3d6af128536bd8"></a>

## ret_close30~ema10

- ID：`ba3d6af128536bd8`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0151 / 0.0004。

登记表达式或插件说明：

```text
ema(im_ret_close30, 10)
```


<a id="f-4adbdc194ddf2a46"></a>

## ret_close30~m20

- ID：`4adbdc194ddf2a46`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (m20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0086 / -0.0047。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 20)
```


<a id="f-086020deb9821312"></a>

## ret_close30~m20_ncap

- ID：`086020deb9821312`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (m20_ncap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0088 / -0.0035。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_close30, 20)), log_cap)
```


<a id="f-f30d732e4bca82df"></a>

## ret_close30~m20_nturn

- ID：`f30d732e4bca82df`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0106 / -0.0039。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_close30, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-c70f6bc62c2986bf"></a>

## ret_close30~m5

- ID：`c70f6bc62c2986bf`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0150 / 0.0059。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 5)
```


<a id="f-fdba0232f4c1ba08"></a>

## ret_close30~m60

- ID：`fdba0232f4c1ba08`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (m60)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0067 / -0.0061。

登记表达式或插件说明：

```text
rolling_mean(im_ret_close30, 60)
```


<a id="f-bbd791f76da738bd"></a>

## ret_close30~s20

- ID：`bbd791f76da738bd`；归属：research_597, pool_current。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (s20)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0621 / 0.0519。

登记表达式或插件说明：

```text
rolling_std(im_ret_close30, 20)
```


<a id="f-76275a9b6fb2e1ef"></a>

## ret_close30~tsz20

- ID：`76275a9b6fb2e1ef`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_close30 aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0161 / 0.0080。

登记表达式或插件说明：

```text
ts_zscore(im_ret_close30, 20)
```


<a id="f-e6296c6498cae5be"></a>

## ret_last1~d1

- ID：`e6296c6498cae5be`；归属：research_597, pool_current。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0106 / 0.0064。

登记表达式或插件说明：

```text
im_ret_last1
```


<a id="f-56388f8490e28796"></a>

## ret_last1~d5_20

- ID：`56388f8490e28796`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0055 / -0.0038。

登记表达式或插件说明：

```text
rolling_mean(im_ret_last1, 5) - rolling_mean(im_ret_last1, 20)
```


<a id="f-ca8c25283193951f"></a>

## ret_last1~ema10

- ID：`ca8c25283193951f`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0106 / 0.0086。

登记表达式或插件说明：

```text
ema(im_ret_last1, 10)
```


<a id="f-4cd3eae7833af23f"></a>

## ret_last1~m20

- ID：`4cd3eae7833af23f`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (m20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0081 / 0.0040。

登记表达式或插件说明：

```text
rolling_mean(im_ret_last1, 20)
```


<a id="f-a208c22e4096c3a6"></a>

## ret_last1~m20_ncap

- ID：`a208c22e4096c3a6`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (m20_ncap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0088 / 0.0044。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_last1, 20)), log_cap)
```


<a id="f-2645602135fa6032"></a>

## ret_last1~m20_nturn

- ID：`2645602135fa6032`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0052 / -0.0015。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_last1, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-29a7b5d2c0f311a8"></a>

## ret_last1~m5

- ID：`29a7b5d2c0f311a8`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (m5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0086 / 0.0043。

登记表达式或插件说明：

```text
rolling_mean(im_ret_last1, 5)
```


<a id="f-64803376b66939ad"></a>

## ret_last1~m60

- ID：`64803376b66939ad`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (m60)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0090 / -0.0012。

登记表达式或插件说明：

```text
rolling_mean(im_ret_last1, 60)
```


<a id="f-e9ff1a50fb0ecdfa"></a>

## ret_last1~s20

- ID：`e9ff1a50fb0ecdfa`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (s20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0094 / -0.0064。

登记表达式或插件说明：

```text
rolling_std(im_ret_last1, 20)
```


<a id="f-3959416febc06d34"></a>

## ret_last1~tsz20

- ID：`3959416febc06d34`；归属：research_597, pool_current。
- 机制：minute:ret_last1（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_last1 aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0082 / 0.0024。

登记表达式或插件说明：

```text
ts_zscore(im_ret_last1, 20)
```


<a id="f-70d92c38bea5b264"></a>

## ret_mid~d1

- ID：`70d92c38bea5b264`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0040 / -0.0070。

登记表达式或插件说明：

```text
im_ret_mid
```


<a id="f-87b8d14176461910"></a>

## ret_mid~d5_20

- ID：`87b8d14176461910`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0051 / -0.0111。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 5) - rolling_mean(im_ret_mid, 20)
```


<a id="f-c9d657a9921ad331"></a>

## ret_mid~ema10

- ID：`c9d657a9921ad331`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0301 / 0.0170。

登记表达式或插件说明：

```text
ema(im_ret_mid, 10)
```


<a id="f-d0c9c20be2725941"></a>

## ret_mid~m20

- ID：`d0c9c20be2725941`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0396 / 0.0192。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 20)
```


<a id="f-b68928bc1ff9835f"></a>

## ret_mid~m20_ncap

- ID：`b68928bc1ff9835f`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0393 / 0.0216。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_mid, 20)), log_cap)
```


<a id="f-f85dcce626842da8"></a>

## ret_mid~m20_nturn

- ID：`f85dcce626842da8`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0327 / 0.0168。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_mid, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-70f9df5636a15d54"></a>

## ret_mid~m5

- ID：`70f9df5636a15d54`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0211 / 0.0063。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 5)
```


<a id="f-60fae72c8875485c"></a>

## ret_mid~m60

- ID：`60fae72c8875485c`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0373 / 0.0211。

登记表达式或插件说明：

```text
rolling_mean(im_ret_mid, 60)
```


<a id="f-76cf67cb24e6ba98"></a>

## ret_mid~s20

- ID：`76cf67cb24e6ba98`；归属：research_597, pool_current。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (s20)
- 原判定：pass_worst+style:turnover20,vol20；历史均值 / 最差年 RankIC：0.0646 / 0.0511。

登记表达式或插件说明：

```text
rolling_std(im_ret_mid, 20)
```


<a id="f-9b6d7d371465f712"></a>

## ret_mid~tsz20

- ID：`9b6d7d371465f712`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_mid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_mid aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0008 / -0.0078。

登记表达式或插件说明：

```text
ts_zscore(im_ret_mid, 20)
```


<a id="f-6a11abbb0eb16fa8"></a>

## ret_open30~d1

- ID：`6a11abbb0eb16fa8`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0091 / -0.0180。

登记表达式或插件说明：

```text
im_ret_open30
```


<a id="f-4315529522f21c99"></a>

## ret_open30~d5_20

- ID：`4315529522f21c99`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0060 / -0.0186。

登记表达式或插件说明：

```text
rolling_mean(im_ret_open30, 5) - rolling_mean(im_ret_open30, 20)
```


<a id="f-946cfa2b551d4d1c"></a>

## ret_open30~ema10

- ID：`946cfa2b551d4d1c`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0297 / -0.0483。

登记表达式或插件说明：

```text
ema(im_ret_open30, 10)
```


<a id="f-59b9a40aa473cd65"></a>

## ret_open30~m20

- ID：`59b9a40aa473cd65`；归属：research_597, pool_current。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0343 / 0.0083。

登记表达式或插件说明：

```text
rolling_mean(im_ret_open30, 20)
```


<a id="f-1ec2c129b72010bb"></a>

## ret_open30~m20_ncap

- ID：`1ec2c129b72010bb`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0331 / 0.0098。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_open30, 20)), log_cap)
```


<a id="f-523c7d99ed2b861e"></a>

## ret_open30~m20_nturn

- ID：`523c7d99ed2b861e`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：-0.0249 / -0.0424。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_open30, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-f5bc4b063facee04"></a>

## ret_open30~m5

- ID：`f5bc4b063facee04`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (m5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0216 / -0.0427。

登记表达式或插件说明：

```text
rolling_mean(im_ret_open30, 5)
```


<a id="f-0250c301afb479b7"></a>

## ret_open30~m60

- ID：`0250c301afb479b7`；归属：research_597, pool_current。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0394 / 0.0113。

登记表达式或插件说明：

```text
rolling_mean(im_ret_open30, 60)
```


<a id="f-d46d23e63b5abf15"></a>

## ret_open30~s20

- ID：`d46d23e63b5abf15`；归属：research_597, pool_current。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (s20)
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0623 / 0.0448。

登记表达式或插件说明：

```text
rolling_std(im_ret_open30, 20)
```


<a id="f-4bb589aba7fdcda1"></a>

## ret_open30~tsz20

- ID：`4bb589aba7fdcda1`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_ret_open30 aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0043 / -0.0102。

登记表达式或插件说明：

```text
ts_zscore(im_ret_open30, 20)
```


<a id="f-359537edeeb92179"></a>

## ret_pm~d1

- ID：`359537edeeb92179`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0117 / -0.0047。

登记表达式或插件说明：

```text
im_ret_pm
```


<a id="f-c2bf3ad0efe4c1da"></a>

## ret_pm~d5_20

- ID：`c2bf3ad0efe4c1da`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0108 / -0.0019。

登记表达式或插件说明：

```text
rolling_mean(im_ret_pm, 5) - rolling_mean(im_ret_pm, 20)
```


<a id="f-9c2c4ddbb212620d"></a>

## ret_pm~ema10

- ID：`9c2c4ddbb212620d`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0194 / 0.0015。

登记表达式或插件说明：

```text
ema(im_ret_pm, 10)
```


<a id="f-1c13fdc9d22ace9e"></a>

## ret_pm~m20

- ID：`1c13fdc9d22ace9e`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0219 / 0.0071。

登记表达式或插件说明：

```text
rolling_mean(im_ret_pm, 20)
```


<a id="f-1325de79845a4053"></a>

## ret_pm~m20_ncap

- ID：`1325de79845a4053`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (m20_ncap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0227 / 0.0086。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), log_cap)
```


<a id="f-bf9495c0abbbfeb2"></a>

## ret_pm~m20_nturn

- ID：`bf9495c0abbbfeb2`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0234 / 0.0084。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_ret_pm, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-7ffb73b194b713c9"></a>

## ret_pm~m5

- ID：`7ffb73b194b713c9`；归属：research_597, pool_current。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0152 / -0.0029。

登记表达式或插件说明：

```text
rolling_mean(im_ret_pm, 5)
```


<a id="f-c4d415dd1e7232bf"></a>

## ret_pm~m60

- ID：`c4d415dd1e7232bf`；归属：research_597, pool_current。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0200 / 0.0081。

登记表达式或插件说明：

```text
rolling_mean(im_ret_pm, 60)
```


<a id="f-4f9de2867b8880e2"></a>

## ret_pm~s20

- ID：`4f9de2867b8880e2`；归属：research_597, pool_current。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (s20)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0647 / 0.0575。

登记表达式或插件说明：

```text
rolling_std(im_ret_pm, 20)
```


<a id="f-5e2495f5107c689b"></a>

## ret_pm~tsz20

- ID：`5e2495f5107c689b`；归属：历史候选，未列入上述集合。
- 机制：minute:ret_pm（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_ret_pm aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0092 / -0.0035。

登记表达式或插件说明：

```text
ts_zscore(im_ret_pm, 20)
```


<a id="f-ff423d63f6773a4e"></a>

## rkurt~d1

- ID：`ff423d63f6773a4e`；归属：research_597, pool_current。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0386 / 0.0286。

登记表达式或插件说明：

```text
im_rkurt
```


<a id="f-b90fab6156b118f3"></a>

## rkurt~d5_20

- ID：`b90fab6156b118f3`；归属：历史候选，未列入上述集合。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0111 / 0.0063。

登记表达式或插件说明：

```text
rolling_mean(im_rkurt, 5) - rolling_mean(im_rkurt, 20)
```


<a id="f-6b3107fc7cc6bad2"></a>

## rkurt~ema10

- ID：`6b3107fc7cc6bad2`；归属：历史候选，未列入上述集合。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0479 / 0.0355。

登记表达式或插件说明：

```text
ema(im_rkurt, 10)
```


<a id="f-1b05050f80ab7e23"></a>

## rkurt~m20

- ID：`1b05050f80ab7e23`；归属：research_597, pool_current。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0379 / 0.0300。

登记表达式或插件说明：

```text
rolling_mean(im_rkurt, 20)
```


<a id="f-9d57f963b6adb54d"></a>

## rkurt~m20_ncap

- ID：`9d57f963b6adb54d`；归属：历史候选，未列入上述集合。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0438 / 0.0277。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rkurt, 20)), log_cap)
```


<a id="f-a4e31523b7c7450f"></a>

## rkurt~m20_nturn

- ID：`a4e31523b7c7450f`；归属：历史候选，未列入上述集合。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0188 / 0.0089。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rkurt, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-a868e5c6649289f9"></a>

## rkurt~m5

- ID：`a868e5c6649289f9`；归属：research_597, pool_current。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0421 / 0.0345。

登记表达式或插件说明：

```text
rolling_mean(im_rkurt, 5)
```


<a id="f-4de2ae9ea44467a6"></a>

## rkurt~m60

- ID：`4de2ae9ea44467a6`；归属：research_597, pool_current。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0321 / 0.0254。

登记表达式或插件说明：

```text
rolling_mean(im_rkurt, 60)
```


<a id="f-c8b9e534d22cb8ea"></a>

## rkurt~s20

- ID：`c8b9e534d22cb8ea`；归属：历史候选，未列入上述集合。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (s20)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0297 / 0.0208。

登记表达式或插件说明：

```text
rolling_std(im_rkurt, 20)
```


<a id="f-234df9ae2cc46bdd"></a>

## rkurt~tsz20

- ID：`234df9ae2cc46bdd`；归属：历史候选，未列入上述集合。
- 机制：minute:rkurt（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rkurt aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0135 / 0.0070。

登记表达式或插件说明：

```text
ts_zscore(im_rkurt, 20)
```


<a id="f-b7a49a5a3dfb6d44"></a>

## rskew~d1

- ID：`b7a49a5a3dfb6d44`；归属：历史候选，未列入上述集合。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0274 / 0.0205。

登记表达式或插件说明：

```text
im_rskew
```


<a id="f-da4c939ce6950748"></a>

## rskew~d5_20

- ID：`da4c939ce6950748`；归属：历史候选，未列入上述集合。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0133 / 0.0087。

登记表达式或插件说明：

```text
rolling_mean(im_rskew, 5) - rolling_mean(im_rskew, 20)
```


<a id="f-4e5dd8232ee7de4a"></a>

## rskew~ema10

- ID：`4e5dd8232ee7de4a`；归属：research_597, pool_current。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (ema10)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0505 / 0.0376。

登记表达式或插件说明：

```text
ema(im_rskew, 10)
```


<a id="f-ece69bece62ccea2"></a>

## rskew~m20

- ID：`ece69bece62ccea2`；归属：research_597, pool_current。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0481 / 0.0363。

登记表达式或插件说明：

```text
rolling_mean(im_rskew, 20)
```


<a id="f-697f8d687bcd9f59"></a>

## rskew~m20_ncap

- ID：`697f8d687bcd9f59`；归属：历史候选，未列入上述集合。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0499 / 0.0403。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rskew, 20)), log_cap)
```


<a id="f-45318bb39c8a7ed4"></a>

## rskew~m20_nturn

- ID：`45318bb39c8a7ed4`；归属：历史候选，未列入上述集合。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0268 / 0.0180。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rskew, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-183d95758c52097d"></a>

## rskew~m5

- ID：`183d95758c52097d`；归属：research_597, pool_current。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0417 / 0.0298。

登记表达式或插件说明：

```text
rolling_mean(im_rskew, 5)
```


<a id="f-591602660a9cd248"></a>

## rskew~m60

- ID：`591602660a9cd248`；归属：历史候选，未列入上述集合。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0437 / 0.0359。

登记表达式或插件说明：

```text
rolling_mean(im_rskew, 60)
```


<a id="f-77a8c4c6a55e06bd"></a>

## rskew~s20

- ID：`77a8c4c6a55e06bd`；归属：research_597, pool_current。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0348 / 0.0254。

登记表达式或插件说明：

```text
rolling_std(im_rskew, 20)
```


<a id="f-7f035af6b98f6310"></a>

## rskew~tsz20

- ID：`7f035af6b98f6310`；归属：历史候选，未列入上述集合。
- 机制：minute:rskew（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rskew aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0097 / 0.0042。

登记表达式或插件说明：

```text
ts_zscore(im_rskew, 20)
```


<a id="f-405777b8030fb38a"></a>

## rv~d1

- ID：`405777b8030fb38a`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (d1)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0637 / 0.0528。

登记表达式或插件说明：

```text
im_rv
```


<a id="f-146587f9ab1fe181"></a>

## rv~d5_20

- ID：`146587f9ab1fe181`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0097 / -0.0250。

登记表达式或插件说明：

```text
rolling_mean(im_rv, 5) - rolling_mean(im_rv, 20)
```


<a id="f-0d52d1e858c01f1f"></a>

## rv~ema10

- ID：`0d52d1e858c01f1f`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0720 / 0.0570。

登记表达式或插件说明：

```text
ema(im_rv, 10)
```


<a id="f-e610766d5a892f4b"></a>

## rv~m20

- ID：`e610766d5a892f4b`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (m20)
- 原判定：pass_mean+style:vol20；历史均值 / 最差年 RankIC：0.0623 / 0.0448。

登记表达式或插件说明：

```text
rolling_mean(im_rv, 20)
```


<a id="f-76e81713794c14cd"></a>

## rv~m20_ncap

- ID：`76e81713794c14cd`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0642 / 0.0524。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rv, 20)), log_cap)
```


<a id="f-375ee47b19f8ca40"></a>

## rv~m20_nturn

- ID：`375ee47b19f8ca40`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0408 / 0.0240。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_rv, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-f801b7dc2d1f20a0"></a>

## rv~m5

- ID：`f801b7dc2d1f20a0`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (m5)
- 原判定：pass_worst；历史均值 / 最差年 RankIC：0.0670 / 0.0514。

登记表达式或插件说明：

```text
rolling_mean(im_rv, 5)
```


<a id="f-2b65474aa4f3da07"></a>

## rv~m60

- ID：`2b65474aa4f3da07`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (m60)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0507 / 0.0377。

登记表达式或插件说明：

```text
rolling_mean(im_rv, 60)
```


<a id="f-6979cda1e5b3866a"></a>

## rv~s20

- ID：`6979cda1e5b3866a`；归属：research_597, pool_current。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (s20)
- 原判定：pass_worst+style:vol20；历史均值 / 最差年 RankIC：0.0714 / 0.0572。

登记表达式或插件说明：

```text
rolling_std(im_rv, 20)
```


<a id="f-31125850f0c83a77"></a>

## rv~tsz20

- ID：`31125850f0c83a77`；归属：历史候选，未列入上述集合。
- 机制：minute:rv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_rv aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0163 / 0.0037。

登记表达式或插件说明：

```text
ts_zscore(im_rv, 20)
```


<a id="f-8cb858f9fb1a43eb"></a>

## updown~d1

- ID：`8cb858f9fb1a43eb`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0284 / 0.0208。

登记表达式或插件说明：

```text
im_updown
```


<a id="f-0b2c38a05cc9a8e1"></a>

## updown~d5_20

- ID：`0b2c38a05cc9a8e1`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0144 / 0.0074。

登记表达式或插件说明：

```text
rolling_mean(im_updown, 5) - rolling_mean(im_updown, 20)
```


<a id="f-09b4c488d8ec8072"></a>

## updown~ema10

- ID：`09b4c488d8ec8072`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (ema10)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0586 / 0.0421。

登记表达式或插件说明：

```text
ema(im_updown, 10)
```


<a id="f-a01a32b100b662c4"></a>

## updown~m20

- ID：`a01a32b100b662c4`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (m20)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0570 / 0.0407。

登记表达式或插件说明：

```text
rolling_mean(im_updown, 20)
```


<a id="f-d7bcfe51dcfc0c17"></a>

## updown~m20_ncap

- ID：`d7bcfe51dcfc0c17`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0578 / 0.0413。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_updown, 20)), log_cap)
```


<a id="f-5d31af40c89a823f"></a>

## updown~m20_nturn

- ID：`5d31af40c89a823f`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0346 / 0.0203。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_updown, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-2cc0484f80dbcfda"></a>

## updown~m5

- ID：`2cc0484f80dbcfda`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0473 / 0.0335。

登记表达式或插件说明：

```text
rolling_mean(im_updown, 5)
```


<a id="f-7cb4072b7b9b6040"></a>

## updown~m60

- ID：`7cb4072b7b9b6040`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (m60)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0525 / 0.0382。

登记表达式或插件说明：

```text
rolling_mean(im_updown, 60)
```


<a id="f-4b0405991c974286"></a>

## updown~s20

- ID：`4b0405991c974286`；归属：research_597, pool_current。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0410 / 0.0311。

登记表达式或插件说明：

```text
rolling_std(im_updown, 20)
```


<a id="f-9649e538d96dd7ce"></a>

## updown~tsz20

- ID：`9649e538d96dd7ce`；归属：历史候选，未列入上述集合。
- 机制：minute:updown（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_updown aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0117 / 0.0044。

登记表达式或插件说明：

```text
ts_zscore(im_updown, 20)
```


<a id="f-c5f4a5f122650b5e"></a>

## vol_centroid~d1

- ID：`c5f4a5f122650b5e`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0222 / 0.0103。

登记表达式或插件说明：

```text
im_vol_centroid
```


<a id="f-f5735984dfaf0e3a"></a>

## vol_centroid~d5_20

- ID：`f5735984dfaf0e3a`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0069 / -0.0156。

登记表达式或插件说明：

```text
rolling_mean(im_vol_centroid, 5) - rolling_mean(im_vol_centroid, 20)
```


<a id="f-2f155b405c001175"></a>

## vol_centroid~ema10

- ID：`2f155b405c001175`；归属：research_597, pool_current。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (ema10)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0459 / 0.0251。

登记表达式或插件说明：

```text
ema(im_vol_centroid, 10)
```


<a id="f-f9956a8dd5151582"></a>

## vol_centroid~m20

- ID：`f9956a8dd5151582`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (m20)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0417 / 0.0162。

登记表达式或插件说明：

```text
rolling_mean(im_vol_centroid, 20)
```


<a id="f-cf8cf2ad973820ba"></a>

## vol_centroid~m20_ncap

- ID：`cf8cf2ad973820ba`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0415 / 0.0168。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vol_centroid, 20)), log_cap)
```


<a id="f-068baf8272bbfb64"></a>

## vol_centroid~m20_nturn

- ID：`068baf8272bbfb64`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0175 / -0.0041。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vol_centroid, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-176084cb302814e8"></a>

## vol_centroid~m5

- ID：`176084cb302814e8`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (m5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0366 / 0.0179。

登记表达式或插件说明：

```text
rolling_mean(im_vol_centroid, 5)
```


<a id="f-cfb02f35b097cfd6"></a>

## vol_centroid~m60

- ID：`cfb02f35b097cfd6`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0364 / 0.0022。

登记表达式或插件说明：

```text
rolling_mean(im_vol_centroid, 60)
```


<a id="f-9b67785742604ca9"></a>

## vol_centroid~s20

- ID：`9b67785742604ca9`；归属：research_597, pool_current。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0333 / 0.0055。

登记表达式或插件说明：

```text
rolling_std(im_vol_centroid, 20)
```


<a id="f-cd56f44a7ca74372"></a>

## vol_centroid~tsz20

- ID：`cd56f44a7ca74372`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_centroid（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_centroid aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0012 / -0.0078。

登记表达式或插件说明：

```text
ts_zscore(im_vol_centroid, 20)
```


<a id="f-ebc26386b0c865a5"></a>

## vol_cv~d1

- ID：`ebc26386b0c865a5`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0109 / -0.0188。

登记表达式或插件说明：

```text
im_vol_cv
```


<a id="f-77e628a9dc0e835c"></a>

## vol_cv~d5_20

- ID：`77e628a9dc0e835c`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0059 / -0.0028。

登记表达式或插件说明：

```text
rolling_mean(im_vol_cv, 5) - rolling_mean(im_vol_cv, 20)
```


<a id="f-c26541e84b4bc9e0"></a>

## vol_cv~ema10

- ID：`c26541e84b4bc9e0`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0057 / -0.0345。

登记表达式或插件说明：

```text
ema(im_vol_cv, 10)
```


<a id="f-b3e8fb4d08879161"></a>

## vol_cv~m20

- ID：`b3e8fb4d08879161`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0143 / -0.0275。

登记表达式或插件说明：

```text
rolling_mean(im_vol_cv, 20)
```


<a id="f-86fab6f0c5277262"></a>

## vol_cv~m20_ncap

- ID：`86fab6f0c5277262`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (m20_ncap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0096 / -0.0264。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vol_cv, 20)), log_cap)
```


<a id="f-85d568f82629ebed"></a>

## vol_cv~m20_nturn

- ID：`85d568f82629ebed`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0047 / -0.0384。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vol_cv, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-651ed653b3062463"></a>

## vol_cv~m5

- ID：`651ed653b3062463`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0114 / -0.0238。

登记表达式或插件说明：

```text
rolling_mean(im_vol_cv, 5)
```


<a id="f-098ef6022b1ffc1e"></a>

## vol_cv~m60

- ID：`098ef6022b1ffc1e`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0160 / -0.0212。

登记表达式或插件说明：

```text
rolling_mean(im_vol_cv, 60)
```


<a id="f-dddf43b4deefcba9"></a>

## vol_cv~s20

- ID：`dddf43b4deefcba9`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0203 / 0.0013。

登记表达式或插件说明：

```text
rolling_std(im_vol_cv, 20)
```


<a id="f-c31a2e6d6cb06f26"></a>

## vol_cv~tsz20

- ID：`c31a2e6d6cb06f26`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_cv（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_cv aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0034 / -0.0004。

登记表达式或插件说明：

```text
ts_zscore(im_vol_cv, 20)
```


<a id="f-a41594fafaeaa783"></a>

## vol_herf~d1

- ID：`a41594fafaeaa783`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0109 / -0.0188。

登记表达式或插件说明：

```text
im_vol_herf
```


<a id="f-0b9dd8b80666fd19"></a>

## vol_herf~d5_20

- ID：`0b9dd8b80666fd19`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0063 / -0.0018。

登记表达式或插件说明：

```text
rolling_mean(im_vol_herf, 5) - rolling_mean(im_vol_herf, 20)
```


<a id="f-504aa99615f10d7d"></a>

## vol_herf~ema10

- ID：`504aa99615f10d7d`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0017 / -0.0371。

登记表达式或插件说明：

```text
ema(im_vol_herf, 10)
```


<a id="f-5a631be3b92b8803"></a>

## vol_herf~m20

- ID：`5a631be3b92b8803`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0102 / -0.0334。

登记表达式或插件说明：

```text
rolling_mean(im_vol_herf, 20)
```


<a id="f-c75588cfaea6084e"></a>

## vol_herf~m20_ncap

- ID：`c75588cfaea6084e`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (m20_ncap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0056 / -0.0320。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vol_herf, 20)), log_cap)
```


<a id="f-2e587975f3fbfb08"></a>

## vol_herf~m20_nturn

- ID：`2e587975f3fbfb08`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0023 / -0.0354。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vol_herf, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-f5235eed92b489f4"></a>

## vol_herf~m5

- ID：`f5235eed92b489f4`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (m5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0095 / -0.0263。

登记表达式或插件说明：

```text
rolling_mean(im_vol_herf, 5)
```


<a id="f-282a1a58fc54f8a6"></a>

## vol_herf~m60

- ID：`282a1a58fc54f8a6`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0119 / -0.0266。

登记表达式或插件说明：

```text
rolling_mean(im_vol_herf, 60)
```


<a id="f-1ae3d2b4da172df3"></a>

## vol_herf~s20

- ID：`1ae3d2b4da172df3`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0131 / -0.0091。

登记表达式或插件说明：

```text
rolling_std(im_vol_herf, 20)
```


<a id="f-2e7b52e7d2a5fd9d"></a>

## vol_herf~tsz20

- ID：`2e7b52e7d2a5fd9d`；归属：历史候选，未列入上述集合。
- 机制：minute:vol_herf（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vol_herf aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0038 / -0.0002。

登记表达式或插件说明：

```text
ts_zscore(im_vol_herf, 20)
```


<a id="f-57c0ea7e74feb56c"></a>

## vshare_am~d1

- ID：`57c0ea7e74feb56c`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0209 / 0.0088。

登记表达式或插件说明：

```text
im_vshare_am
```


<a id="f-20f1978a18b3a6bb"></a>

## vshare_am~d5_20

- ID：`20f1978a18b3a6bb`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0072 / -0.0165。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_am, 5) - rolling_mean(im_vshare_am, 20)
```


<a id="f-f872827f7cf2b4d3"></a>

## vshare_am~ema10

- ID：`f872827f7cf2b4d3`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0430 / 0.0221。

登记表达式或插件说明：

```text
ema(im_vshare_am, 10)
```


<a id="f-174973d8454a3c3b"></a>

## vshare_am~m20

- ID：`174973d8454a3c3b`；归属：research_597, pool_current。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0393 / 0.0136。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_am, 20)
```


<a id="f-ea90aac566d01b13"></a>

## vshare_am~m20_ncap

- ID：`ea90aac566d01b13`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0389 / 0.0139。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_am, 20)), log_cap)
```


<a id="f-1763b301e4e64f18"></a>

## vshare_am~m20_nturn

- ID：`1763b301e4e64f18`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (m20_nturn)
- 原判定：redundant；历史均值 / 最差年 RankIC：-0.0158 / -0.0340。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_am, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-234ba64f14bd721f"></a>

## vshare_am~m5

- ID：`234ba64f14bd721f`；归属：research_597, pool_current。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0344 / 0.0157。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_am, 5)
```


<a id="f-4cd4f5ddf472a17b"></a>

## vshare_am~m60

- ID：`4cd4f5ddf472a17b`；归属：research_597, pool_current。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0354 / 0.0004。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_am, 60)
```


<a id="f-adb0e7f8d25eaacc"></a>

## vshare_am~s20

- ID：`adb0e7f8d25eaacc`；归属：research_597, pool_current。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0320 / 0.0045。

登记表达式或插件说明：

```text
rolling_std(im_vshare_am, 20)
```


<a id="f-2fe5d8a7ac499885"></a>

## vshare_am~tsz20

- ID：`2fe5d8a7ac499885`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_am（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vshare_am aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0022 / -0.0100。

登记表达式或插件说明：

```text
ts_zscore(im_vshare_am, 20)
```


<a id="f-072c7f4027a7697d"></a>

## vshare_close30~d1

- ID：`072c7f4027a7697d`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (d1)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0061 / -0.0240。

登记表达式或插件说明：

```text
im_vshare_close30
```


<a id="f-21cc8a2f0519a167"></a>

## vshare_close30~d5_20

- ID：`21cc8a2f0519a167`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0008 / -0.0085。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_close30, 5) - rolling_mean(im_vshare_close30, 20)
```


<a id="f-f37f0b532d24a88f"></a>

## vshare_close30~ema10

- ID：`f37f0b532d24a88f`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0217 / -0.0586。

登记表达式或插件说明：

```text
ema(im_vshare_close30, 10)
```


<a id="f-83131480340fa22c"></a>

## vshare_close30~m20

- ID：`83131480340fa22c`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (m20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0197 / -0.0604。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_close30, 20)
```


<a id="f-ef607dea0d5e73f4"></a>

## vshare_close30~m20_ncap

- ID：`ef607dea0d5e73f4`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (m20_ncap)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0176 / -0.0533。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_close30, 20)), log_cap)
```


<a id="f-e4ab6fd3b6a88f76"></a>

## vshare_close30~m20_nturn

- ID：`e4ab6fd3b6a88f76`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0113 / -0.0478。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_close30, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-38a6cf5d03ea9eb8"></a>

## vshare_close30~m5

- ID：`38a6cf5d03ea9eb8`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (m5)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0154 / -0.0483。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_close30, 5)
```


<a id="f-1afd764338670da5"></a>

## vshare_close30~m60

- ID：`1afd764338670da5`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (m60)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0179 / -0.0637。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_close30, 60)
```


<a id="f-abae34303e00defb"></a>

## vshare_close30~s20

- ID：`abae34303e00defb`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (s20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0044 / -0.0248。

登记表达式或插件说明：

```text
rolling_std(im_vshare_close30, 20)
```


<a id="f-2c213fc734b04297"></a>

## vshare_close30~tsz20

- ID：`2c213fc734b04297`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_close30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_close30 aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0049 / -0.0061。

登记表达式或插件说明：

```text
ts_zscore(im_vshare_close30, 20)
```


<a id="f-7de19c51a9ff1ba8"></a>

## vshare_last5~d1

- ID：`7de19c51a9ff1ba8`；归属：research_597, pool_current。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0163 / 0.0033。

登记表达式或插件说明：

```text
im_vshare_last5
```


<a id="f-1d6a74bceaf43ce7"></a>

## vshare_last5~d5_20

- ID：`1d6a74bceaf43ce7`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0119 / 0.0033。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_last5, 5) - rolling_mean(im_vshare_last5, 20)
```


<a id="f-8896fba0e4da3889"></a>

## vshare_last5~ema10

- ID：`8896fba0e4da3889`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (ema10)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0087 / -0.0161。

登记表达式或插件说明：

```text
ema(im_vshare_last5, 10)
```


<a id="f-4548169ec46719ff"></a>

## vshare_last5~m20

- ID：`4548169ec46719ff`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (m20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0059 / -0.0226。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_last5, 20)
```


<a id="f-e61a51f8e53e9d80"></a>

## vshare_last5~m20_ncap

- ID：`e61a51f8e53e9d80`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (m20_ncap)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0121 / -0.0089。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_last5, 20)), log_cap)
```


<a id="f-8520ebe1118b9c3f"></a>

## vshare_last5~m20_nturn

- ID：`8520ebe1118b9c3f`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (m20_nturn)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0008 / -0.0282。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_last5, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-67d4d866b2ee43b7"></a>

## vshare_last5~m5

- ID：`67d4d866b2ee43b7`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0114 / -0.0107。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_last5, 5)
```


<a id="f-f4979d1830cf0852"></a>

## vshare_last5~m60

- ID：`f4979d1830cf0852`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (m60)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0045 / -0.0276。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_last5, 60)
```


<a id="f-e58a2da52a836375"></a>

## vshare_last5~s20

- ID：`e58a2da52a836375`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (s20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0115 / -0.0363。

登记表达式或插件说明：

```text
rolling_std(im_vshare_last5, 20)
```


<a id="f-fb079b68a450016e"></a>

## vshare_last5~tsz20

- ID：`fb079b68a450016e`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_last5（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_last5 aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0142 / 0.0054。

登记表达式或插件说明：

```text
ts_zscore(im_vshare_last5, 20)
```


<a id="f-27bca8681ad61c6c"></a>

## vshare_open30~d1

- ID：`27bca8681ad61c6c`；归属：research_597, pool_current。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (d1)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0252 / 0.0205。

登记表达式或插件说明：

```text
im_vshare_open30
```


<a id="f-f3858de475741b2b"></a>

## vshare_open30~d5_20

- ID：`f3858de475741b2b`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (d5_20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：0.0096 / -0.0063。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_open30, 5) - rolling_mean(im_vshare_open30, 20)
```


<a id="f-2010d0d51317ca41"></a>

## vshare_open30~ema10

- ID：`2010d0d51317ca41`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0507 / 0.0480。

登记表达式或插件说明：

```text
ema(im_vshare_open30, 10)
```


<a id="f-9fb33d328a89600e"></a>

## vshare_open30~m20

- ID：`9fb33d328a89600e`；归属：research_597, pool_current。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0463 / 0.0412。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_open30, 20)
```


<a id="f-134a92f738bcaa82"></a>

## vshare_open30~m20_ncap

- ID：`134a92f738bcaa82`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0475 / 0.0392。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_open30, 20)), log_cap)
```


<a id="f-248a92e7c459b3d5"></a>

## vshare_open30~m20_nturn

- ID：`248a92e7c459b3d5`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0191 / 0.0121。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_vshare_open30, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-547f43757710b558"></a>

## vshare_open30~m5

- ID：`547f43757710b558`；归属：research_597, pool_current。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (m5)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0416 / 0.0365。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_open30, 5)
```


<a id="f-7141c7fb1b63b5e5"></a>

## vshare_open30~m60

- ID：`7141c7fb1b63b5e5`；归属：research_597, pool_current。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (m60)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0397 / 0.0282。

登记表达式或插件说明：

```text
rolling_mean(im_vshare_open30, 60)
```


<a id="f-743adf257e0cc593"></a>

## vshare_open30~s20

- ID：`743adf257e0cc593`；归属：research_597, pool_current。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0411 / 0.0226。

登记表达式或插件说明：

```text
rolling_std(im_vshare_open30, 20)
```


<a id="f-2e344b1c88a6bc33"></a>

## vshare_open30~tsz20

- ID：`2e344b1c88a6bc33`；归属：历史候选，未列入上述集合。
- 机制：minute:vshare_open30（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_vshare_open30 aggregated (tsz20)
- 原判定：no_signal；历史均值 / 最差年 RankIC：-0.0039 / -0.0087。

登记表达式或插件说明：

```text
ts_zscore(im_vshare_open30, 20)
```


<a id="f-f11f79b0a5f464c9"></a>

## zero_share~d1

- ID：`f11f79b0a5f464c9`；归属：research_597, pool_current。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (d1)
- 原判定：pass_mean；历史均值 / 最差年 RankIC：0.0540 / 0.0140。

登记表达式或插件说明：

```text
im_zero_share
```


<a id="f-2b1db0316992b70e"></a>

## zero_share~d5_20

- ID：`2b1db0316992b70e`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (d5_20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0173 / -0.0027。

登记表达式或插件说明：

```text
rolling_mean(im_zero_share, 5) - rolling_mean(im_zero_share, 20)
```


<a id="f-d3990163d0418d30"></a>

## zero_share~ema10

- ID：`d3990163d0418d30`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (ema10)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0482 / 0.0064。

登记表达式或插件说明：

```text
ema(im_zero_share, 10)
```


<a id="f-c7f3680f351c1986"></a>

## zero_share~m20

- ID：`c7f3680f351c1986`；归属：research_597, pool_current。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (m20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0463 / 0.0013。

登记表达式或插件说明：

```text
rolling_mean(im_zero_share, 20)
```


<a id="f-74eb20d347458621"></a>

## zero_share~m20_ncap

- ID：`74eb20d347458621`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (m20_ncap)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0438 / 0.0019。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_zero_share, 20)), log_cap)
```


<a id="f-c0e3b42aa7f92f5e"></a>

## zero_share~m20_nturn

- ID：`c0e3b42aa7f92f5e`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (m20_nturn)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0234 / -0.0234。

登记表达式或插件说明：

```text
cs_neutralize(cs_rank(rolling_mean(im_zero_share, 20)), cs_rank(rolling_mean(turnover, 20)))
```


<a id="f-c022bc5f6c1853d0"></a>

## zero_share~m5

- ID：`c022bc5f6c1853d0`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (m5)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0520 / 0.0116。

登记表达式或插件说明：

```text
rolling_mean(im_zero_share, 5)
```


<a id="f-6452712147c70d67"></a>

## zero_share~m60

- ID：`6452712147c70d67`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (m60)
- 原判定：redundant；历史均值 / 最差年 RankIC：0.0382 / -0.0084。

登记表达式或插件说明：

```text
rolling_mean(im_zero_share, 60)
```


<a id="f-c2fa8b9f5c900764"></a>

## zero_share~s20

- ID：`c2fa8b9f5c900764`；归属：research_597, pool_current。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`-1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (s20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0264 / 0.0003。

登记表达式或插件说明：

```text
rolling_std(im_zero_share, 20)
```


<a id="f-715be4ae962c75e2"></a>

## zero_share~tsz20

- ID：`715be4ae962c75e2`；归属：历史候选，未列入上述集合。
- 机制：minute:zero_share（登记标签，不是独立信息量判定）。
- 类型：`dsl`；冻结方向：`1`；评价状态：`ok`。
- 原假设：minute field im_zero_share aggregated (tsz20)
- 原判定：weak_signal；历史均值 / 最差年 RankIC：0.0155 / 0.0018。

登记表达式或插件说明：

```text
ts_zscore(im_zero_share, 20)
```
