import pandas as pd
import numpy as np
from typing import Dict, Any

# ============================================================
# 全局参数
params = {
    "ma_short": 10,
    "ma_long": 30,
    "long_up_shift": 1,               # 改为1，使信号更敏感
    "mom_window": 20,
    "vol_ratio_window": 10,
    "vol_window": 20,
    "top_n": 10,
    "max_turnover": 0.4,              # 单边换手上限
    "concentration_limit": 0.1,       # 单票集中度上限
    "drawdown_threshold_1": 0.10,     # 回撤10%触发半仓
    "drawdown_threshold_2": 0.15,     # 回撤15%触发空仓
    "lock_days_1": 3,                 # 半仓锁定天数
    "lock_days_2": 5,                 # 空仓锁定天数
    "trial_days": 3                   # 试仓连续无回撤天数
}

# ============================================================
# 策略阶段声明
strategy_next_phase = "validate"      # 仍需验证，未改成test
strategy_decision_reason = "已修复未来函数（全量使用shift(1)数据），调整LONG_UP信号定义，并实现动态回撤止损与换手控制，现提交验证"

# ============================================================
# 中间变量函数1：大盘信号
def calculate_market_signal(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    计算验证期间的大盘等权指数及仓位信号。
    所有计算基于T-1日收盘数据（close.shift(1)），无未来函数。
    返回DataFrame包含：trade_date, EW, MA10, MA30, LONG_UP, PRICE_ABOVE, 仓位档位
    """
    # 合并训练集与验证集，用于预热滚动指标
    train_df = train_data_bundle["stock_kline_daily_hfq"].copy()
    validate_df = validate_data_bundle["stock_kline_daily_hfq"].copy()
    # 合并后的数据按code、trade_date排序
    combined = pd.concat([train_df, validate_df], ignore_index=True)
    combined = combined.sort_values(["code", "trade_date"]).reset_index(drop=True)

    # 计算每只股票的前一日收盘价
    combined["close_prev"] = combined.groupby("code")["close"].shift(1)

    # 每日等权指数：所有股票关闭prev的均值
    ew_daily = combined.groupby("trade_date")["close_prev"].mean().reset_index()
    ew_daily.rename(columns={"close_prev": "EW"}, inplace=True)
    ew_daily = ew_daily.sort_values("trade_date").reset_index(drop=True)

    # 计算MA10, MA30
    ew_daily["MA10"] = ew_daily["EW"].rolling(window=params["ma_short"], min_periods=params["ma_short"]).mean()
    ew_daily["MA30"] = ew_daily["EW"].rolling(window=params["ma_long"], min_periods=params["ma_long"]).mean()

    # 趋势信号
    # LONG_UP: 过去N日MA30上升（N=long_up_shift）
    ew_daily["LONG_UP"] = ew_daily["MA30"] > ew_daily["MA30"].shift(params["long_up_shift"])
    # PRICE_ABOVE: 价格在MA30之上
    ew_daily["PRICE_ABOVE"] = ew_daily["EW"] > ew_daily["MA30"]

    # 仓位档位决策
    def assign_position(row):
        if row["PRICE_ABOVE"] and row["LONG_UP"]:
            return 1.0   # 满仓
        elif row["PRICE_ABOVE"] and not row["LONG_UP"]:
            return 0.5   # 半仓
        elif not row["PRICE_ABOVE"] and row["EW"] > row["MA30"] * 0.97:
            return 0.25  # 轻仓
        else:
            return 0.0   # 空仓

    ew_daily["仓位档位"] = ew_daily.apply(assign_position, axis=1)

    # 只保留验证期数据
    validate_start = validate_df["trade_date"].min()
    validate_end = validate_df["trade_date"].max()
    market_signal = ew_daily[(ew_daily["trade_date"] >= validate_start) & (ew_daily["trade_date"] <= validate_end)].copy()
    market_signal = market_signal.reset_index(drop=True)

    # 显式保留时间列
    market_signal.rename(columns={"trade_date": "trade_date"}, inplace=True)
    return market_signal

# ============================================================
# 中间变量函数2：个股综合得分
def calculate_stock_scores(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    计算验证期间每日各股票的综合因子得分。
    返回宽表：trade_date + 各股票代码列（得分为0-1之间）。
    所有因子基于T-1日数据计算。
    """
    train_df = train_data_bundle["stock_kline_daily_hfq"].copy()
    validate_df = validate_data_bundle["stock_kline_daily_hfq"].copy()
    combined = pd.concat([train_df, validate_df], ignore_index=True)
    combined = combined.sort_values(["code", "trade_date"]).reset_index(drop=True)

    # 计算前一日数据
    combined["close_prev"] = combined.groupby("code")["close"].shift(1)
    combined["high_prev"] = combined.groupby("code")["high"].shift(1)
    combined["low_prev"] = combined.groupby("code")["low"].shift(1)
    combined["volume_prev"] = combined.groupby("code")["volume"].shift(1)

    # 因子1：中期动量
    combined["mom20"] = combined["close_prev"] / combined.groupby("code")["close_prev"].shift(params["mom_window"]) - 1

    # 因子2：日内强度
    combined["range"] = combined["high_prev"] - combined["low_prev"]
    combined["strength"] = np.where(
        combined["range"] > 1e-8,
        (combined["close_prev"] - combined["low_prev"]) / combined["range"],
        0.5
    )

    # 因子3：成交量确认
    combined["vol_ratio"] = combined["volume_prev"] / combined.groupby("code")["volume_prev"].rolling(
        window=params["vol_ratio_window"], min_periods=params["vol_ratio_window"]
    ).mean().reset_index(level=0, drop=True)

    # 因子4：波动率调整动量
    combined["vol_20"] = combined["close_prev"].groupby(combined["code"]).rolling(
        window=params["vol_window"], min_periods=params["vol_window"]
    ).std().reset_index(level=0, drop=True) / combined["close_prev"].groupby(combined["code"]).rolling(
        window=params["vol_window"], min_periods=params["vol_window"]
    ).mean().reset_index(level=0, drop=True)
    combined["mom_vol_adj"] = combined["mom20"] / (combined["vol_20"] + 0.01)

    # 仅保留验证期数据，且去除滚动计算引入的NaN
    validate_start = validate_df["trade_date"].min()
    validate_end = validate_df["trade_date"].max()
    valid = combined[(combined["trade_date"] >= validate_start) & (combined["trade_date"] <= validate_end)].copy()
    valid = valid.dropna(subset=["mom20", "strength", "vol_ratio", "mom_vol_adj"]).reset_index(drop=True)

    # 截面排名法标准化（每个交易日每个因子独立排名）
    def rank_pct(series):
        rank = series.rank(method="average")
        n = rank.count()
        if n > 1:
            return (rank - 1) / (n - 1)
        else:
            return 0.5

    grouped = valid.groupby("trade_date")
    valid["rank_mom20"] = grouped["mom20"].transform(rank_pct)
    valid["rank_strength"] = grouped["strength"].transform(rank_pct)
    valid["rank_vol_ratio"] = grouped["vol_ratio"].transform(rank_pct)
    valid["rank_mom_vol_adj"] = grouped["mom_vol_adj"].transform(rank_pct)

    # 综合得分 = 四个因子排名等权平均
    valid["score"] = (valid["rank_mom20"] + valid["rank_strength"] + valid["rank_vol_ratio"] + valid["rank_mom_vol_adj"]) / 4

    # 转换为宽表：每个交易日一行，列是股票代码
    pivot_scores = valid.pivot_table(index="trade_date", columns="code", values="score", aggfunc="first")
    pivot_scores = pivot_scores.reset_index()
    pivot_scores.columns.name = None
    # 确保所有列名是字符串
    pivot_scores.columns = [str(c) for c in pivot_scores.columns]
    # 时间列显式保留
    pivot_scores.rename(columns={"trade_date": "trade_date"}, inplace=True)
    return pivot_scores

# ============================================================
# 主函数：输出权重矩阵
def output_weights(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    生成验证期间每日开盘时目标权重矩阵（无未来函数）。
    内部模拟真实交易流程：包含动态回撤止损、换手率控制、集中度限制。
    """
    # 获取大盘信号和个股得分（均在函数内使用shift(1)）
    market_signal = calculate_market_signal(train_data_bundle, validate_data_bundle, params)
    stock_scores = calculate_stock_scores(train_data_bundle, validate_data_bundle, params)

    # 获取验证期所有交易日列表
    trade_dates = sorted(market_signal["trade_date"].unique())
    
    # 提取所有可能的股票代码（从得分宽表中获取，不含trade_date）
    score_cols = [c for c in stock_scores.columns if c != "trade_date"]
    all_symbols = sorted(score_cols)
    
    # 初始状态
    cash = 1.0                     # 初始现金比例
    position = {}                  # 当前持仓市值（以初始资金1为单位）
    nav = 1.0                      # 当前净值（初始1）
    max_nav = 1.0                  # 历史最高净值
    lock_remaining = 0             # 锁定剩余天数
    lock_type = None               # "half" 或 "empty"
    trial_count = 0                # 试仓连续无回撤天数
    last_portfolio = {}            # 上一日的持仓市值字典（用于换手率计算）
    prev_trade_date = None         # 上一个交易日
    
    results = []                   # 存储每日权重

    # 用于计算收益的日行情数据（开盘价和收盘价）
    validate_df = validate_data_bundle["stock_kline_daily_hfq"].copy()
    validate_df["trade_date"] = pd.to_datetime(validate_df["trade_date"])
    # 按code+日期排序
    validate_df = validate_df.sort_values(["code", "trade_date"]).reset_index(drop=True)
    # 创建 pivot：开盘价、收盘价
    open_pivot = validate_df.pivot_table(index="trade_date", columns="code", values="open", aggfunc="first")
    close_pivot = validate_df.pivot_table(index="trade_date", columns="code", values="close", aggfunc="first")
    # 确保索引是日期
    open_pivot.index = pd.to_datetime(open_pivot.index)
    close_pivot.index = pd.to_datetime(close_pivot.index)

    # 循环每个交易日
    for i, date in enumerate(trade_dates):
        # 获取当日大盘信号（仓位档位）
        signal_row = market_signal[market_signal["trade_date"] == date]
        if signal_row.empty:
            continue
        position_level = signal_row["仓位档位"].values[0]  # 0.0, 0.25, 0.5, 1.0

        # 根据回撤锁定状态调整仓位
        adjusted_level = position_level
        if lock_remaining > 0:
            if lock_type == "half":
                adjusted_level = min(position_level, 0.5)
            elif lock_type == "empty":
                adjusted_level = 0.0
            lock_remaining -= 1

        # 如果大盘空仓，则直接全部现金
        if adjusted_level == 0.0:
            # 清仓所有股票
            target_weights = pd.Series(0.0, index=all_symbols)
            cash_target = 1.0
        else:
            # 获取当日个股得分
            scores_today = stock_scores[stock_scores["trade_date"] == date]
            if scores_today.empty:
                # 没有足够数据，空仓
                target_weights = pd.Series(0.0, index=all_symbols)
                cash_target = 1.0
            else:
                # 提取得分并降序排序，取Top10
                scores_s = scores_today.iloc[0][all_symbols].dropna()
                if len(scores_s) == 0:
                    target_weights = pd.Series(0.0, index=all_symbols)
                    cash_target = 1.0
                else:
                    top_symbols = scores_s.sort_values(ascending=False).head(params["top_n"]).index.tolist()
                    # 线性递减权重
                    if len(top_symbols) > 0:
                        ranks = list(range(1, len(top_symbols)+1))
                        weights = [params["top_n"] + 1 - r for r in ranks]  # 11 - rank
                        total = sum(weights)
                        weights = [w / total for w in weights]
                        # 构建target weights系列
                        target_weights = pd.Series(0.0, index=all_symbols)
                        for sym, w in zip(top_symbols, weights):
                            target_weights[sym] = w
                        # 缩放至大盘仓位
                        target_weights *= adjusted_level
                        cash_target = 1.0 - adjusted_level
                    else:
                        target_weights = pd.Series(0.0, index=all_symbols)
                        cash_target = 1.0

            # 集中度控制：单票不超过10%
            limit = params["concentration_limit"]
            over_limit = target_weights > limit
            if over_limit.any():
                excess = target_weights[over_limit] - limit
                target_weights[over_limit] = limit
                # 将超额部分重新分配给现金
                cash_target += excess.sum()
                # 确保现金不超1
                cash_target = min(cash_target, 1.0)

        # 换手率控制（与上一日的持仓比较，假设使用开盘价买卖，换手定义为单边绝对变化率）
        # 由于我们不知道实际价格，我们使用市值比例变化代表换手。
        # 单边换手 = sum(|w_target - w_prev|) / 2 ，因为买入和卖出各算一次，但策略说单边换手不超过40%，这里我们用卖出+买入的一半？常见定义为换手率 = sum(|Δw|)/2
        if prev_trade_date is not None and len(last_portfolio) > 0:
            # 将last_portfolio转为与target_weights相同索引的series
            prev_weights = pd.Series(0.0, index=all_symbols)
            for sym, w in last_portfolio.items():
                prev_weights[sym] = w
            turnover = (target_weights - prev_weights).abs().sum() / 2.0
            if turnover > params["max_turnover"]:
                # 限制换手：按比例缩减调整幅度
                scale = params["max_turnover"] / turnover
                # 调整目标权重：new_target = prev_weights + scale * (target_weights - prev_weights)
                target_weights = prev_weights + scale * (target_weights - prev_weights)
                cash_target = 1.0 - target_weights.sum()

        # 更新持仓记录（用于下一天的换手率计算）
        last_portfolio = target_weights.to_dict()
        prev_trade_date = date

        # 模拟当日收益，更新净值
        # 假设当日开盘按目标权重买入，收盘根据涨跌幅计算收益
        # 获取该交易日所有股票的开盘价和收盘价
        date_str = pd.Timestamp(date)
        if date_str in open_pivot.index and date_str in close_pivot.index:
            opens = open_pivot.loc[date_str]
            closes = close_pivot.loc[date_str]
            # 计算每只股票的日收益率
            returns = (closes / opens - 1).fillna(0)
            # 计算组合当日收益（不考虑交易成本）
            portfolio_return = 0.0
            for sym in all_symbols:
                if sym in returns.index:
                    port_weight = target_weights.get(sym, 0.0)
                    ret = returns.get(sym, 0.0)
                    portfolio_return += port_weight * ret
            # 现金部分无收益
            nav = nav * (1 + portfolio_return)
            # 更新最大净值
            if nav > max_nav:
                max_nav = nav

        # 回撤判断（基于收盘后净值，用于下一个交易日）
        drawdown = (max_nav - nav) / max_nav
        if drawdown > params["drawdown_threshold_2"]:
            # 触发空仓锁定
            lock_remaining = params["lock_days_2"]
            lock_type = "empty"
            trial_count = 0
        elif drawdown > params["drawdown_threshold_1"]:
            # 触发半仓锁定（如果未处于更高级锁定）
            if lock_type != "empty":
                lock_remaining = params["lock_days_1"]
                lock_type = "half"
                trial_count = 0
        else:
            # 未触发回撤，且处于试仓期？如果锁定已解除，则进入试仓期
            if lock_remaining == 0 and lock_type == "half":
                trial_count += 1
                if trial_count >= params["trial_days"]:
                    # 恢复满仓，清除锁定类型
                    lock_type = None
                    trial_count = 0

        # 如果锁定到期，自动恢复半仓试仓
        if lock_remaining == 0 and lock_type is not None:
            # 锁定期结束，进入试仓期
            lock_type = None
            trial_count = 0
            # 下一交易日将使用大盘信号（但试仓期已由上面trial_count处理）

        # 构建单日权重行：股票代码列 + cash
        row = {"trade_date": date}
        for sym in all_symbols:
            row[sym] = target_weights.get(sym, 0.0)
        row["cash"] = cash_target
        results.append(row)

    # 构建输出DataFrame
    output_df = pd.DataFrame(results)
    # 确保列顺序：trade_date + 股票代码 + cash
    cols = ["trade_date"] + all_symbols + ["cash"]
    cols = [c for c in cols if c in output_df.columns]
    output_df = output_df[cols]
    return output_df

# ============================================================
# 模块顶层调用，生成最终权重
output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)

# ============================================================
# 策略元信息
strategy_output = {
    "market_signal": {
        "description": "大盘等权指数与双重趋势确认仓位信号",
        "function_name": "calculate_market_signal",
        "expected_characteristics": [
            "验证期间仓位档位分布广泛（0/0.25/0.5/1），不全为极端值",
            "当LONG_UP为True时，未来5日EW平均收益应显著为正（>0）",
            "当仓位档位为0（空仓）时，未来5日EW平均收益应低于非空仓时期",
            "MA10与MA30交叉具备一定持续性（至少连续3天同侧）",
            "验证期空仓信号覆盖至少5个交易日"
        ],
        "datetime_column": "trade_date"
    },
    "stock_scores": {
        "description": "个股综合因子得分（每日截面排名等权合成）",
        "function_name": "calculate_stock_scores",
        "expected_characteristics": [
            "Top10组合次日平均收盘收益显著高于Bottom10（至少0.1%）",
            "Top10组合次日收益胜率高于0.5",
            "各因子截面排名分布均匀（均值接近0.5，标准差接近0.29）",
            "综合得分与次日收益存在正相关（Spearman相关系数>0.05）",
            "动量因子(mom20)在正负区间分布对称，正值比例接近0.5"
        ],
        "datetime_column": "trade_date"
    },
    "output_weights_df": {
        "description": "验证期间每日开盘目标权重矩阵",
        "function_name": "output_weights",
        "datetime_column": "trade_date"
    }
}