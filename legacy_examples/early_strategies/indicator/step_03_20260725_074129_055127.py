import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

# ========================== 全局参数 ==========================
params = {
    "adx_period": 14,
    "bbands_period": 20,
    "bbands_std": 2,
    "rsi_period": 5,
    "rsi_oversold": 25,
    "trend_momentum_period": 20,
    "trend_liquidity_period": 5,
    "trend_lowvol_period": 20,
    "trend_position_period": 20,
    "top_n_oscillate": 3,
    "top_n_trend": 10,
    "hold_days": 5,
    "atr_period": 14,
    "single_stock_max_weight": 0.15,
    "daily_loss_threshold": 0.02,
    "oscillate_target_weight": 0.5,
    "trend_target_weight": 1.0,
    "cash": "cash"
}

# 环境变量声明（必须顶层）
strategy_next_phase = "validate"
strategy_decision_reason = "实现持仓5日再平衡、止损、T+1约束、附加仓位调节，修正震荡模式限定于ADX∈[20,25]"

# ========================== 工具函数 ==========================
def _prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    """将窄表转换为宽表，并生成prev列"""
    data = data.sort_values(['code', 'trade_date']).reset_index(drop=True)
    data['close_prev'] = data.groupby('code')['close'].shift(1)
    data['high_prev'] = data.groupby('code')['high'].shift(1)
    data['low_prev'] = data.groupby('code')['low'].shift(1)
    data['volume_prev'] = data.groupby('code')['volume'].shift(1)
    data['open_prev'] = data.groupby('code')['open'].shift(1)
    pivot = data.set_index(['trade_date', 'code']).unstack(level='code')
    return pivot

def _calc_adx_index(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算沪深300等权平均指数的ADX"""
    idx_close = close.mean(axis=1)
    idx_high = high.mean(axis=1)
    idx_low = low.mean(axis=1)
    up = idx_high - idx_high.shift(1)
    down = idx_low.shift(1) - idx_low
    plus_dm = pd.Series(0.0, index=idx_close.index)
    minus_dm = pd.Series(0.0, index=idx_close.index)
    plus_dm[(up > down) & (up > 0)] = up[(up > down) & (up > 0)]
    minus_dm[(down > up) & (down > 0)] = down[(down > up) & (down > 0)]
    tr = pd.concat([
        idx_high - idx_low,
        (idx_high - idx_close.shift(1)).abs(),
        (idx_low - idx_close.shift(1)).abs()
    ], axis=1).max(axis=1)
    tr_smoothed = tr.ewm(span=period, adjust=False).mean()
    plus_dm_smoothed = plus_dm.ewm(span=period, adjust=False).mean()
    minus_dm_smoothed = minus_dm.ewm(span=period, adjust=False).mean()
    plus_di = 100 * plus_dm_smoothed / tr_smoothed
    minus_di = 100 * minus_dm_smoothed / tr_smoothed
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx

def _calc_bbands(close: pd.DataFrame, period: int = 20, std_mult: float = 2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """计算布林带中轨、下轨"""
    ma = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    lower = ma - std_mult * std
    return ma, lower

def _calc_rsi(close: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    """计算RSI"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi[avg_loss == 0] = 100
    rsi[avg_gain == 0] = 0
    return rsi

def _calc_atr(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """计算每只股票的ATR（基于prev数据）"""
    # 计算三个TR分量，然后取逐元素最大值
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.DataFrame(
        np.maximum(np.maximum(tr1.values, tr2.values), tr3.values),
        index=high.index,
        columns=high.columns
    )
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr

# ========================== 中间变量计算函数 ==========================
def calc_adx(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """计算ADX指数值"""
    train = train_data_bundle['stock_kline_daily_hfq']
    valid = validate_data_bundle['stock_kline_daily_hfq']
    data = pd.concat([train, valid], ignore_index=True)
    pivot = _prepare_data(data)
    close = pivot['close']
    high = pivot['high']
    low = pivot['low']
    adx = _calc_adx_index(close, high, low, params['adx_period'])
    min_date = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].min()
    max_date = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].max()
    adx = adx.loc[min_date:max_date].reset_index()
    adx.columns = ['trade_date', 'adx']
    return adx

def calc_oscillate_signals(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """震荡模式选股信号（每日候选股票代码列表）"""
    train = train_data_bundle['stock_kline_daily_hfq']
    valid = validate_data_bundle['stock_kline_daily_hfq']
    data = pd.concat([train, valid], ignore_index=True)
    pivot = _prepare_data(data)
    close_prev = pivot['close_prev']
    _, lower = _calc_bbands(close_prev, params['bbands_period'], params['bbands_std'])
    rsi = _calc_rsi(close_prev, params['rsi_period'])
    cond = (close_prev < lower) & (rsi < params['rsi_oversold'])
    min_date = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].min()
    max_date = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].max()
    cond = cond.loc[min_date:max_date]
    signal_list = []
    for date in cond.index:
        codes = cond.columns[cond.loc[date]].tolist()
        for code in codes:
            signal_list.append({'trade_date': date, 'code': code})
    result = pd.DataFrame(signal_list)
    if result.empty:
        result = pd.DataFrame(columns=['trade_date', 'code'])
    return result

def calc_trend_signals(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """趋势模式因子得分及选股结果"""
    train = train_data_bundle['stock_kline_daily_hfq']
    valid = validate_data_bundle['stock_kline_daily_hfq']
    data = pd.concat([train, valid], ignore_index=True)
    pivot = _prepare_data(data)
    close_prev = pivot['close_prev']
    high_prev = pivot['high_prev']
    low_prev = pivot['low_prev']
    volume_prev = pivot['volume_prev']
    amt = np.log(close_prev * volume_prev)
    amt_5ma = amt.rolling(window=params['trend_liquidity_period'], min_periods=params['trend_liquidity_period']).mean()
    momentum = close_prev / close_prev.shift(params['trend_momentum_period']) - 1
    returns = close_prev.pct_change()
    low_vol = -returns.rolling(window=params['trend_lowvol_period'], min_periods=params['trend_lowvol_period']).std(ddof=0)
    low_20 = low_prev.rolling(window=params['trend_position_period'], min_periods=params['trend_position_period']).min()
    high_20 = high_prev.rolling(window=params['trend_position_period'], min_periods=params['trend_position_period']).max()
    price_position = (close_prev - low_20) / (high_20 - low_20).replace(0, np.nan)
    def zscore_cross(df):
        mean = df.mean(axis=1)
        std = df.std(axis=1, ddof=0)
        return (df.sub(mean, axis=0)).div(std.replace(0, np.nan), axis=0)
    liq_z = zscore_cross(amt_5ma)
    mom_z = zscore_cross(momentum)
    lowvol_z = zscore_cross(low_vol)
    pos_z = zscore_cross(price_position)
    score = (liq_z + mom_z + lowvol_z + pos_z) / 4.0
    min_date = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].min()
    max_date = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].max()
    score = score.loc[min_date:max_date]
    score_long = score.stack().reset_index()
    score_long.columns = ['trade_date', 'code', 'score']
    score_long = score_long.sort_values(['trade_date', 'score'], ascending=[True, False])
    return score_long

# ========================== 主函数: 生成目标权重 ==========================
def output_weights(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """生成验证期间的目标权重矩阵"""
    train = train_data_bundle['stock_kline_daily_hfq']
    valid = validate_data_bundle['stock_kline_daily_hfq']
    data = pd.concat([train, valid], ignore_index=True)
    pivot = _prepare_data(data)
    close = pivot['close']
    close_prev = pivot['close_prev']
    high_prev = pivot['high_prev']
    low_prev = pivot['low_prev']
    volume_prev = pivot['volume_prev']
    codes = close.columns.tolist()
    high = pivot['high']
    low = pivot['low']
    adx = _calc_adx_index(close, high, low, params['adx_period'])
    bbands_ma, bbands_lower = _calc_bbands(close_prev, params['bbands_period'], params['bbands_std'])
    rsi = _calc_rsi(close_prev, params['rsi_period'])
    atr = _calc_atr(high_prev, low_prev, close_prev, params['atr_period'])
    amt = np.log(close_prev * volume_prev)
    amt_5ma = amt.rolling(window=5, min_periods=5).mean()
    momentum = close_prev / close_prev.shift(20) - 1
    returns = close_prev.pct_change()
    low_vol = -returns.rolling(window=20, min_periods=20).std(ddof=0)
    low_20 = low_prev.rolling(window=20, min_periods=20).min()
    high_20 = high_prev.rolling(window=20, min_periods=20).max()
    price_position = (close_prev - low_20) / (high_20 - low_20).replace(0, np.nan)
    idx_close = close.mean(axis=1)
    idx_ma20 = idx_close.rolling(window=20, min_periods=20).mean()
    trade_dates = validate_data_bundle['stock_kline_daily_hfq']['trade_date'].unique()
    trade_dates = sorted(trade_dates)
    all_dates = pivot.index.unique().sort_values()
    available_dates = adx.dropna().index.unique().sort_values()
    date_series = pd.Series(available_dates, index=available_dates)
    prev_dates = date_series.shift(1).dropna()
    portfolio = {}
    cash_weight = 1.0
    mode = None
    rows = []
    for t in trade_dates:
        try:
            t_prev = prev_dates[t]
        except KeyError:
            row = {'trade_date': t, 'cash': 1.0}
            for code in codes:
                row[code] = 0.0
            rows.append(row)
            cash_weight = 1.0
            continue
        adx_t = adx.loc[t_prev] if t_prev in adx.index else np.nan
        if pd.isna(adx_t):
            new_mode = 'cash'
        elif adx_t < 20:
            new_mode = 'cash'
        elif adx_t <= 25:
            new_mode = 'oscillate'
        else:
            new_mode = 'trend'
        if new_mode != mode:
            portfolio.clear()
            cash_weight = 1.0
            mode = new_mode
        target_weights = {}
        target_cash = 1.0
        if mode == 'cash':
            target_cash = 1.0
        elif mode == 'oscillate':
            cond = (close_prev.loc[t_prev] < bbands_lower.loc[t_prev]) & (rsi.loc[t_prev] < params['rsi_oversold'])
            selected = cond[cond].index.tolist()
            rsi_t = rsi.loc[t_prev]
            selected_sorted = sorted(selected, key=lambda x: rsi_t[x] if pd.notna(rsi_t[x]) else 999)
            top_n = params['top_n_oscillate']
            selected_final = selected_sorted[:top_n]
            if len(selected_final) > 0:
                weight_per = params['oscillate_target_weight'] / len(selected_final)
                weight_per = min(weight_per, params['single_stock_max_weight'])
                for code in selected_final:
                    target_weights[code] = weight_per
                target_cash = 1.0 - sum(target_weights.values())
            else:
                target_cash = 1.0
        elif mode == 'trend':
            def cross_zscore(series):
                s = series.copy()
                mean = s.mean()
                std = s.std(ddof=0)
                if std == 0:
                    return s * 0.0
                return (s - mean) / std
            liq_t = amt_5ma.loc[t_prev]
            mom_t = momentum.loc[t_prev]
            lowvol_t = low_vol.loc[t_prev]
            pos_t = price_position.loc[t_prev]
            liq_z = cross_zscore(liq_t)
            mom_z = cross_zscore(mom_t)
            lowvol_z = cross_zscore(lowvol_t)
            pos_z = cross_zscore(pos_t)
            score = (liq_z + mom_z + lowvol_z + pos_z) / 4.0
            score = score.dropna()
            top_n = params['top_n_trend']
            top_codes = score.nlargest(top_n).index.tolist()
            idx_close_t = idx_close.loc[t_prev]
            idx_ma20_t = idx_ma20.loc[t_prev]
            if pd.notna(idx_close_t) and pd.notna(idx_ma20_t) and idx_close_t < idx_ma20_t:
                target_multiplier = 0.5
            else:
                target_multiplier = 1.0
            target_total = params['trend_target_weight'] * target_multiplier
            n_selected = len(top_codes)
            if n_selected > 0:
                weight_per = target_total / n_selected
                weight_per = min(weight_per, params['single_stock_max_weight'])
                for code in top_codes:
                    target_weights[code] = weight_per
                target_cash = 1.0 - sum(target_weights.values())
            else:
                target_cash = 1.0
        new_portfolio = {}
        new_cash = cash_weight
        for code, info in portfolio.items():
            if t >= info['entry_date'] + pd.Timedelta(days=params['hold_days']):
                continue
            latest_close = close_prev.loc[t_prev, code] if code in close_prev.columns else np.nan
            if pd.notna(latest_close) and latest_close < info['stop_loss']:
                continue
            entry_price = info['entry_price']
            atr_val = atr.loc[t_prev, code] if code in atr.columns else np.nan
            if pd.notna(atr_val) and latest_close >= entry_price + atr_val:
                new_stop = entry_price + atr_val
            else:
                new_stop = info['stop_loss']
            new_portfolio[code] = {
                'entry_date': info['entry_date'],
                'entry_price': entry_price,
                'stop_loss': new_stop,
                'weight': info['weight']
            }
        for code, weight in target_weights.items():
            if code in new_portfolio:
                continue
            entry_price = close_prev.loc[t_prev, code] if code in close_prev.columns else np.nan
            atr_val = atr.loc[t_prev, code] if code in atr.columns else np.nan
            if pd.notna(entry_price) and pd.notna(atr_val):
                stop_loss = entry_price - 2 * atr_val
            else:
                stop_loss = 0.0
            new_portfolio[code] = {
                'entry_date': t,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'weight': weight
            }
        total_weight = sum([v['weight'] for v in new_portfolio.values()])
        new_cash = 1.0 - total_weight
        if new_cash < 0:
            scale = 1.0 / total_weight
            for code in new_portfolio:
                new_portfolio[code]['weight'] *= scale
            new_cash = 0.0
        for code in new_portfolio:
            if new_portfolio[code]['weight'] > params['single_stock_max_weight']:
                excess = new_portfolio[code]['weight'] - params['single_stock_max_weight']
                new_portfolio[code]['weight'] = params['single_stock_max_weight']
                new_cash += excess
        portfolio = new_portfolio
        cash_weight = new_cash
        row = {'trade_date': t, 'cash': cash_weight}
        for code in codes:
            row[code] = portfolio.get(code, {}).get('weight', 0.0)
        rows.append(row)
    weights_df = pd.DataFrame(rows)
    weights_df['cash'] = weights_df['cash'].clip(0, 1)
    sum_cols = [c for c in weights_df.columns if c != 'trade_date']
    row_sum = weights_df[sum_cols].sum(axis=1)
    weights_df[sum_cols] = weights_df[sum_cols].div(row_sum, axis=0).fillna(1.0)
    for col in codes:
        if col in weights_df.columns:
            weights_df[col] = weights_df[col].clip(lower=0)
    weights_df['cash'] = 1.0 - weights_df[codes].sum(axis=1)
    weights_df['cash'] = weights_df['cash'].clip(0, 1)
    return weights_df

# ========================== 模块顶层调用 ==========================
output_weights_df = output_weights(train_data_bundle, validate_data_bundle, params)

# ========================== 中间变量元信息 ==========================
strategy_output = {
    "calc_adx": {
        "description": "基于等权沪深300指数计算的ADX(14)值，用于环境判定（震荡/趋势/空仓）",
        "function_name": "calc_adx",
        "expected_characteristics": [
            "ADX均值应在20-40之间，右偏分布",
            "ADX大于25的交易日占比应较高（>50%），反映市场经常处于趋势状态",
            "ADX小于20的交易日占比应较低（<20%）",
            "ADX在20-25之间的交易日占比约为15%-25%",
            "序列应为平稳但具有明显的趋势性，自相关较高"
        ],
        "datetime_column": "trade_date"
    },
    "calc_oscillate_signals": {
        "description": "震荡模式候选股票信号，满足收盘价<下轨且RSI<25的条件",
        "function_name": "calc_oscillate_signals",
        "expected_characteristics": [
            "有信号的交易日占比应在20%-40%之间（修正后参数更严格）",
            "每个有信号日入选股票数通常在1-3只，极少超过5只",
            "信号集中在ADX处于20-25的区间内，与ADX负相关（市场震荡时更容易出现）",
            "选股池中RSI均值应显著低于整体市场均值",
            "信号的出现应具有一定的持续性（连续数日符合条件的概率高）"
        ],
        "datetime_column": "trade_date"
    },
    "calc_trend_signals": {
        "description": "趋势模式下四个因子等权合成的综合得分，用于选股排序",
        "function_name": "calc_trend_signals",
        "expected_characteristics": [
            "得分在以交易日为横截面内应大致呈标准正态分布（均值为0，标准差为1）",
            "得分与下期收益率应存在显著正相关（动量因子正贡献）",
            "得分中流动性因子与低波动因子应具有负相关（规模效应）",
            "得分序列在时间上应具有一定稳定性，但个股间差异显著",
            "得分最高的10只股票组合应能跑赢等权指数"
        ],
        "datetime_column": "trade_date"
    },
    "output_weights_df": {
        "description": "回测阶段目标资产组合权重矩阵（日频），包含持仓5日再平衡、止损、T+1约束和仓位调节",
        "function_name": "output_weights",
        "datetime_column": "trade_date"
    }
}