from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


PRICE_TABLE_KEY = "stock_kline_daily_qfq"
MEMBERSHIP_TABLE_KEY = "csi300_membership"
TIME_COLUMN = "trade_date"
SYMBOL_COLUMN = "code"

params: Dict[str, Any] = {
    "consolidation_days": 30,
    "return_count": 29,
    "volatility_limit": 0.015,
    "volume_average_days": 30,
    "volume_multiplier": 2.0,
    "candle_body_multiplier": 2.0,
    "holding_days": 5,
    "single_stock_weight": 0.10,
}


def _check_required_columns(
    data: pd.DataFrame,
    required_columns: List[str],
    table_key: str,
) -> None:
    missing_columns = [
        column for column in required_columns if column not in data.columns
    ]
    if missing_columns:
        raise ValueError(
            f"{table_key} 缺少字段 {missing_columns}，属于数据导入或元数据维护问题"
        )


def _confirm_china_stock_market(universe_data: Any) -> None:
    if not isinstance(universe_data, list):
        raise ValueError("universe 格式错误，属于数据导入或元数据维护问题")

    has_china_stock_market = False
    for item in universe_data:
        if not isinstance(item, dict) or "asset" not in item:
            raise ValueError("universe 条目格式错误，属于数据导入或元数据维护问题")
        if item["asset"] == "中国股票":
            has_china_stock_market = True

    if not has_china_stock_market:
        raise ValueError("universe 未确认中国股票市场，属于数据导入或元数据维护问题")


def _prepare_prices(data: pd.DataFrame, source: str) -> pd.DataFrame:
    required_columns = [
        TIME_COLUMN,
        SYMBOL_COLUMN,
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    _check_required_columns(data, required_columns, PRICE_TABLE_KEY)

    result = data[required_columns].copy()
    result[TIME_COLUMN] = pd.to_datetime(
        result[TIME_COLUMN], errors="coerce"
    ).dt.normalize()

    if result[TIME_COLUMN].isna().any():
        raise ValueError(
            f"{PRICE_TABLE_KEY} 的 {TIME_COLUMN} 存在无效日期，"
            "属于数据导入或元数据维护问题"
        )

    result[SYMBOL_COLUMN] = result[SYMBOL_COLUMN].astype(str)
    for column in ["open", "high", "low", "close", "volume"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    if result.duplicated([TIME_COLUMN, SYMBOL_COLUMN]).any():
        raise ValueError(
            f"{PRICE_TABLE_KEY} 存在重复的日期和股票代码，"
            "属于数据导入或元数据维护问题"
        )

    result["_data_source"] = source
    return result


def _prepare_membership(data: pd.DataFrame) -> pd.DataFrame:
    required_columns = [SYMBOL_COLUMN, "start_date", "end_date"]
    _check_required_columns(data, required_columns, MEMBERSHIP_TABLE_KEY)

    result = data[required_columns].copy()
    result[SYMBOL_COLUMN] = result[SYMBOL_COLUMN].astype(str)
    result["start_date"] = pd.to_datetime(
        result["start_date"], errors="coerce"
    ).dt.normalize()
    result["end_date"] = pd.to_datetime(
        result["end_date"], errors="coerce"
    ).dt.normalize()

    valid_dates = result["start_date"].notna() & result["end_date"].notna()
    if (
        result.loc[valid_dates, "start_date"]
        > result.loc[valid_dates, "end_date"]
    ).any():
        raise ValueError(
            f"{MEMBERSHIP_TABLE_KEY} 存在开始日期晚于结束日期的记录，"
            "属于数据导入或元数据维护问题"
        )

    return result.loc[valid_dates].drop_duplicates().reset_index(drop=True)


def _build_membership_intervals(
    membership: pd.DataFrame,
) -> Dict[str, List[Tuple[pd.Timestamp, pd.Timestamp]]]:
    intervals: Dict[str, List[Tuple[pd.Timestamp, pd.Timestamp]]] = {}

    for code, start_date, end_date in membership[
        [SYMBOL_COLUMN, "start_date", "end_date"]
    ].itertuples(index=False, name=None):
        intervals.setdefault(code, []).append((start_date, end_date))

    for code in intervals:
        intervals[code].sort(key=lambda item: item[0])

    return intervals


def _is_member(
    code: str,
    date: pd.Timestamp,
    membership_intervals: Dict[str, List[Tuple[pd.Timestamp, pd.Timestamp]]],
) -> bool:
    for start_date, end_date in membership_intervals.get(code, []):
        if start_date <= date <= end_date:
            return True
    return False


def output_weights(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """
    生成验证期间的目标权重矩阵。

    训练期日线只用于补足验证期开始前的历史计算窗口，不产生训练期权重。
    每一行日期为目标权重形成日，权重在下一实际交易日开盘执行。
    """
    _confirm_china_stock_market(universe)

    if PRICE_TABLE_KEY not in train_data_bundle:
        raise KeyError(
            f"训练集缺少 {PRICE_TABLE_KEY}，属于数据导入或元数据维护问题"
        )
    if PRICE_TABLE_KEY not in validate_data_bundle:
        raise KeyError(
            f"验证集缺少 {PRICE_TABLE_KEY}，属于数据导入或元数据维护问题"
        )
    if MEMBERSHIP_TABLE_KEY not in train_data_bundle:
        raise KeyError(
            f"训练集缺少 {MEMBERSHIP_TABLE_KEY}，属于数据导入或元数据维护问题"
        )
    if MEMBERSHIP_TABLE_KEY not in validate_data_bundle:
        raise KeyError(
            f"验证集缺少 {MEMBERSHIP_TABLE_KEY}，属于数据导入或元数据维护问题"
        )

    train_prices = _prepare_prices(
        train_data_bundle[PRICE_TABLE_KEY],
        "train",
    )
    validate_prices = _prepare_prices(
        validate_data_bundle[PRICE_TABLE_KEY],
        "validate",
    )

    if validate_prices.empty:
        raise ValueError(f"验证集 {PRICE_TABLE_KEY} 为空，无法生成目标权重")

    train_membership = _prepare_membership(
        train_data_bundle[MEMBERSHIP_TABLE_KEY]
    )
    validate_membership = _prepare_membership(
        validate_data_bundle[MEMBERSHIP_TABLE_KEY]
    )
    membership = pd.concat(
        [train_membership, validate_membership],
        ignore_index=True,
    ).drop_duplicates()
    membership_intervals = _build_membership_intervals(membership)

    # 训练期日线位于验证期之前，仅为验证期初始计算提供历史数据。
    prices = pd.concat(
        [train_prices, validate_prices],
        ignore_index=True,
    ).sort_values(
        [SYMBOL_COLUMN, TIME_COLUMN],
        kind="mergesort",
    ).reset_index(drop=True)

    grouped = prices.groupby(SYMBOL_COLUMN, sort=False, group_keys=False)

    prices["_close_return"] = grouped["close"].pct_change(fill_method=None)
    prices["_consolidation_volatility"] = grouped["_close_return"].transform(
        lambda values: values.rolling(
            window=int(params["return_count"]),
            min_periods=int(params["return_count"]),
        ).std(ddof=1).shift(2)
    )
    prices["_historical_average_volume"] = grouped["volume"].transform(
        lambda values: values.rolling(
            window=int(params["volume_average_days"]),
            min_periods=int(params["volume_average_days"]),
        ).mean().shift(2)
    )
    prices["_previous_volume"] = grouped["volume"].shift(1)

    price_range = prices["high"] - prices["low"]
    candle_body = (prices["close"] - prices["open"]).abs()

    finite_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "_previous_volume",
        "_historical_average_volume",
        "_consolidation_volatility",
    ]
    necessary_values_are_finite = pd.Series(True, index=prices.index)
    for column in finite_columns:
        necessary_values_are_finite &= np.isfinite(prices[column])

    signal_mask = (
        (prices["_data_source"] == "validate")
        & necessary_values_are_finite
        & (
            prices["_consolidation_volatility"]
            <= float(params["volatility_limit"])
        )
        & (
            prices["_previous_volume"]
            >= float(params["volume_multiplier"])
            * prices["_historical_average_volume"]
        )
        & (
            prices["volume"]
            >= float(params["volume_multiplier"])
            * prices["_historical_average_volume"]
        )
        & (prices["high"] > prices["low"])
        & (
            price_range
            > float(params["candle_body_multiplier"]) * candle_body
        )
    )

    raw_signals = prices.loc[
        signal_mask,
        [TIME_COLUMN, SYMBOL_COLUMN],
    ]

    # 信号日必须处于该股票当日有效的沪深300成分区间。
    signals_by_date: Dict[pd.Timestamp, List[str]] = {}
    for signal_date, code in raw_signals.itertuples(index=False, name=None):
        if _is_member(code, signal_date, membership_intervals):
            signals_by_date.setdefault(signal_date, []).append(code)

    trading_dates = sorted(validate_prices[TIME_COLUMN].unique())
    trading_dates = [pd.Timestamp(date) for date in trading_dates]
    symbols = sorted(validate_prices[SYMBOL_COLUMN].unique().tolist())

    weights = pd.DataFrame(
        0.0,
        index=range(len(trading_dates)),
        columns=symbols,
    )
    cash_weights = np.ones(len(trading_dates), dtype=float)

    # 值为该股票计划卖出的交易日序号；卖出发生在该日开盘。
    active_positions: Dict[str, int] = {}
    holding_days = int(params["holding_days"])
    fixed_weight = float(params["single_stock_weight"])

    for date_index, decision_date in enumerate(trading_dates):
        # 当日开盘已经卖出的股票，不再属于当日持仓。
        expired_codes = [
            code
            for code, sell_index in active_positions.items()
            if sell_index <= date_index
        ]
        for code in expired_codes:
            del active_positions[code]

        next_date = (
            trading_dates[date_index + 1]
            if date_index + 1 < len(trading_dates)
            else None
        )

        # 同一股票持有期间再次触发时忽略。
        if next_date is not None:
            for code in signals_by_date.get(decision_date, []):
                if code in active_positions:
                    continue
                if not _is_member(code, next_date, membership_intervals):
                    continue

                buy_index = date_index + 1
                active_positions[code] = buy_index + holding_days

        next_open_index = date_index + 1
        target_codes = sorted(
            code
            for code, sell_index in active_positions.items()
            if sell_index > next_open_index
        )

        position_count = len(target_codes)
        if position_count == 0:
            continue

        if position_count < 10:
            stock_weight = fixed_weight
        else:
            stock_weight = 1.0 / position_count

        for code in target_codes:
            weights.at[date_index, code] = stock_weight

        cash_weights[date_index] = 1.0 - stock_weight * position_count

    output = weights.copy()
    output.insert(0, TIME_COLUMN, trading_dates)
    output["cash"] = cash_weights

    asset_weights = output[symbols]
    if (asset_weights < -1e-12).any().any():
        raise ValueError("中国股票权重不得为负数")
    if ((output["cash"] < -1e-12) | (output["cash"] > 1.0 + 1e-12)).any():
        raise ValueError("现金权重必须在0到1之间")

    total_weights = asset_weights.sum(axis=1) + output["cash"]
    if not np.allclose(total_weights.to_numpy(), 1.0, atol=1e-6, rtol=0.0):
        raise ValueError("每行股票权重与现金权重之和必须等于1")

    return output


output_weights_df = output_weights(
    train_data_bundle,
    validate_data_bundle,
    params,
)

strategy_output = {
    "output_weights_df": {
        "description": "按固定低波动、连续放量及长K线规则生成的验证期目标资产组合权重矩阵",
        "function_name": "output_weights",
        "datetime_column": "trade_date",
    },
}

strategy_next_phase = "validate"
strategy_decision_reason = "固定规则已写入代码，需重新进行统计验证。"