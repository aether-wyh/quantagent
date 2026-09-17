from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


TABLE_KEY = "stock_kline_daily_qfq"
TIME_COLUMN = "trade_date"
REQUIRED_COLUMNS = [
    "trade_date", "code", "open", "high", "low", "close", "volume"
]

DEFAULT_PARAMS: Dict[str, Any] = {
    "adx_period": 14,
    "atr_period": 14,
    "rsi_period": 5,
    "boll_period": 20,
    "boll_std": 2.0,
    "volume_period": 20,
    "volume_multiple": 1.2,
    "minimum_history": 60,
    "minimum_valid_ratio": 0.80,
    "range_adx_lower": 20.0,
    "trend_adx_lower": 25.0,
    "range_rsi_limit": 25.0,
    "range_holding_days": 10,
    "range_slots": 3,
    "trend_slots": 5,
    "single_position_limit": 0.15,
    "stop_atr_multiple": 2.0,
    "profit_trigger_atr_multiple": 2.0,
    "raised_stop_atr_multiple": 1.0,
    "portfolio_loss_limit": -0.02,
    "risk_position_multiplier": 0.50,
    # 用于策略内部净值计算；正式回测还应分别测试单边10和20个基点。
    "commission_bps": 3.0,
    "sell_tax_bps": 5.0,
    "slippage_bps": 10.0,
    "cost_scenarios_bps": [10.0, 20.0],
}

_injected_params = globals().get("params", {})
if _injected_params is None:
    _injected_params = {}
if not isinstance(_injected_params, dict):
    raise TypeError("params必须是字典")

params: Dict[str, Any] = {**DEFAULT_PARAMS, **_injected_params}


def _wilder_average(values: pd.Series, period: int) -> pd.Series:
    """按Wilder方法计算移动平均，只使用当前及更早的数据。"""
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    result = np.full(len(arr), np.nan, dtype=float)

    initial_values: List[float] = []
    current = np.nan
    initialized = False

    for i, value in enumerate(arr):
        if not np.isfinite(value):
            continue

        if not initialized:
            initial_values.append(float(value))
            if len(initial_values) == period:
                current = float(np.mean(initial_values))
                result[i] = current
                initialized = True
        else:
            current = ((period - 1.0) * current + float(value)) / period
            result[i] = current

    return pd.Series(result, index=values.index, dtype=float)


def _market_symbols(validate_df: pd.DataFrame) -> List[str]:
    """根据注入的universe确认中国股票范围。"""
    universe_value = globals().get("universe")
    if not isinstance(universe_value, list):
        raise ValueError(
            "数据导入或元数据维护问题：未注入有效的universe，无法判断市场类型"
        )

    asset_by_symbol: Dict[str, str] = {}
    supported_assets = {"中国股票", "期货"}

    for group in universe_value:
        if not isinstance(group, dict):
            raise ValueError(
                "数据导入或元数据维护问题：universe中的条目必须是字典"
            )

        asset = group.get("asset")
        symbols = group.get("symbols")
        if asset not in supported_assets or not isinstance(symbols, list):
            raise ValueError(
                "数据导入或元数据维护问题：universe的asset或symbols不符合约定"
            )

        for symbol in symbols:
            symbol = str(symbol)
            previous_asset = asset_by_symbol.get(symbol)
            if previous_asset is not None and previous_asset != asset:
                raise ValueError(
                    f"数据导入或元数据维护问题：标的{symbol}对应多个市场类型"
                )
            asset_by_symbol[symbol] = asset

    observed_symbols = set(validate_df["code"].astype(str).unique())
    unknown = sorted(observed_symbols.difference(asset_by_symbol))
    if unknown:
        sample = ", ".join(unknown[:5])
        raise ValueError(
            f"数据导入或元数据维护问题：以下标的未在universe中声明：{sample}"
        )

    non_stock = sorted(
        symbol
        for symbol in observed_symbols
        if asset_by_symbol[symbol] != "中国股票"
    )
    if non_stock:
        sample = ", ".join(non_stock[:5])
        raise ValueError(
            f"数据导入或元数据维护问题：股票日线表中出现非中国股票标的：{sample}"
        )

    return sorted(observed_symbols)


def _load_and_check_data(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """读取并检查训练期和验证期日线。"""
    for bundle_name, bundle in (
        ("train_data_bundle", train_data_bundle),
        ("validate_data_bundle", validate_data_bundle),
    ):
        if not isinstance(bundle, dict) or TABLE_KEY not in bundle:
            raise ValueError(
                f"数据导入或元数据维护问题：{bundle_name}缺少{TABLE_KEY}"
            )

    train_df = train_data_bundle[TABLE_KEY]
    validate_df = validate_data_bundle[TABLE_KEY]

    if not isinstance(train_df, pd.DataFrame) or not isinstance(
        validate_df, pd.DataFrame
    ):
        raise TypeError("数据导入或元数据维护问题：日线数据必须是DataFrame")

    for data_name, data in (("训练集", train_df), ("验证集", validate_df)):
        missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
        if missing:
            raise ValueError(
                f"数据导入或元数据维护问题：{data_name}缺少字段{missing}"
            )
        if data.empty:
            raise ValueError(f"数据导入或元数据维护问题：{data_name}为空")
        if data["code"].isna().any():
            raise ValueError(
                f"数据导入或元数据维护问题：{data_name}存在空股票代码"
            )

    train = train_df[REQUIRED_COLUMNS].copy()
    validate = validate_df[REQUIRED_COLUMNS].copy()

    train["_dt"] = pd.to_datetime(train[TIME_COLUMN], errors="coerce")
    validate["_dt"] = pd.to_datetime(validate[TIME_COLUMN], errors="coerce")
    if train["_dt"].isna().any() or validate["_dt"].isna().any():
        raise ValueError(
            "数据导入或元数据维护问题：trade_date存在无法识别的日期"
        )

    train["code"] = train["code"].astype(str)
    validate["code"] = validate["code"].astype(str)

    if train.duplicated(["_dt", "code"]).any():
        raise ValueError(
            "数据导入或元数据维护问题：训练集存在重复的日期和股票代码"
        )
    if validate.duplicated(["_dt", "code"]).any():
        raise ValueError(
            "数据导入或元数据维护问题：验证集存在重复的日期和股票代码"
        )

    if train["_dt"].max() >= validate["_dt"].min():
        raise ValueError(
            "数据导入或元数据维护问题：训练集和验证集时间重叠或顺序错误"
        )

    symbols = _market_symbols(validate)
    train = train[train["code"].isin(symbols)].copy()
    validate = validate[validate["code"].isin(symbols)].copy()

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        train[column] = pd.to_numeric(train[column], errors="coerce")
        validate[column] = pd.to_numeric(validate[column], errors="coerce")

    train["_source"] = "train"
    validate["_source"] = "validate"
    return train, validate, symbols


def _calculate_features(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    strategy_params: Dict[str, Any],
) -> Tuple[pd.DataFrame, List[pd.Timestamp], List[str]]:
    """使用训练期预热指标，并顺序计算验证期指标。"""
    train, validate, symbols = _load_and_check_data(
        train_data_bundle, validate_data_bundle
    )

    all_data = pd.concat([train, validate], ignore_index=True)
    all_data = all_data.sort_values(
        ["code", "_dt"], kind="mergesort"
    ).reset_index(drop=True)

    pieces: List[pd.DataFrame] = []

    for _, stock_data in all_data.groupby("code", sort=False):
        stock_data = stock_data.sort_values(
            "_dt", kind="mergesort"
        ).reset_index(drop=True).copy()

        high = stock_data["high"]
        low = stock_data["low"]
        close = stock_data["close"]
        volume = stock_data["volume"]
        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        true_range[~(high.notna() & low.notna())] = np.nan

        upward_move = high.diff()
        downward_move = -low.diff()
        plus_dm = pd.Series(
            np.where(
                (upward_move > downward_move) & (upward_move > 0),
                upward_move,
                0.0,
            ),
            index=stock_data.index,
            dtype=float,
        )
        minus_dm = pd.Series(
            np.where(
                (downward_move > upward_move) & (downward_move > 0),
                downward_move,
                0.0,
            ),
            index=stock_data.index,
            dtype=float,
        )
        if len(stock_data):
            plus_dm.iloc[0] = 0.0
            minus_dm.iloc[0] = 0.0

        atr = _wilder_average(
            true_range, int(strategy_params["atr_period"])
        )
        smoothed_plus_dm = _wilder_average(
            plus_dm, int(strategy_params["adx_period"])
        )
        smoothed_minus_dm = _wilder_average(
            minus_dm, int(strategy_params["adx_period"])
        )

        plus_di = 100.0 * smoothed_plus_dm / atr.replace(0.0, np.nan)
        minus_di = 100.0 * smoothed_minus_dm / atr.replace(0.0, np.nan)
        di_sum = (plus_di + minus_di).replace(0.0, np.nan)
        dx = 100.0 * (plus_di - minus_di).abs() / di_sum
        adx = _wilder_average(dx, int(strategy_params["adx_period"]))

        price_change = close.diff()
        gain = price_change.clip(lower=0.0)
        loss = (-price_change).clip(lower=0.0)
        average_gain = _wilder_average(
            gain, int(strategy_params["rsi_period"])
        )
        average_loss = _wilder_average(
            loss, int(strategy_params["rsi_period"])
        )

        rsi = pd.Series(np.nan, index=stock_data.index, dtype=float)
        normal_rsi = average_loss > 0
        rsi.loc[normal_rsi] = (
            100.0
            - 100.0
            / (
                1.0
                + average_gain.loc[normal_rsi]
                / average_loss.loc[normal_rsi]
            )
        )
        rsi.loc[(average_loss == 0) & (average_gain > 0)] = 100.0
        rsi.loc[(average_loss == 0) & (average_gain == 0)] = 50.0

        boll_period = int(strategy_params["boll_period"])
        boll_middle = close.rolling(
            boll_period, min_periods=boll_period
        ).mean()
        boll_std = close.rolling(
            boll_period, min_periods=boll_period
        ).std(ddof=0)
        boll_lower = (
            boll_middle
            - float(strategy_params["boll_std"]) * boll_std
        )

        ema5 = close.ewm(span=5, adjust=False, min_periods=5).mean()
        ema20 = close.ewm(span=20, adjust=False, min_periods=20).mean()
        ema60 = close.ewm(span=60, adjust=False, min_periods=60).mean()
        ema12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
        ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
        dif = ema12 - ema26

        volume_mean20 = volume.rolling(
            int(strategy_params["volume_period"]),
            min_periods=int(strategy_params["volume_period"]),
        ).mean()

        valid_bar = stock_data[
            ["open", "high", "low", "close", "volume"]
        ].notna().all(axis=1)
        valid_count = valid_bar.astype(int).cumsum()

        raw_values = {
            "atr": atr,
            "adx": adx,
            "rsi": rsi,
            "boll_lower": boll_lower,
            "ema5": ema5,
            "ema20": ema20,
            "ema60": ema60,
            "dif": dif,
            "volume_mean20": volume_mean20,
            "valid_count": valid_count,
        }
        for name, values in raw_values.items():
            stock_data[name] = values

        shift_columns = [
            "close",
            "high",
            "low",
            "volume",
            "atr",
            "adx",
            "rsi",
            "boll_lower",
            "ema5",
            "ema20",
            "ema60",
            "dif",
            "volume_mean20",
            "valid_count",
        ]
        for column in shift_columns:
            stock_data[f"{column}_1"] = stock_data[column].shift(1)

        for column in ["close", "boll_lower", "ema5", "ema20"]:
            stock_data[f"{column}_2"] = stock_data[column].shift(2)

        pieces.append(stock_data)

    features = pd.concat(pieces, ignore_index=True)
    validation_dates = sorted(validate["_dt"].unique())
    return features, list(validation_dates), symbols


def _build_context(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    strategy_params: Dict[str, Any],
) -> Tuple[
    pd.DataFrame,
    List[pd.Timestamp],
    List[str],
    pd.DataFrame,
    Dict[pd.Timestamp, List[str]],
    Dict[pd.Timestamp, List[str]],
]:
    """计算环境以及两类候选股排名。"""
    features, dates, symbols = _calculate_features(
        train_data_bundle, validate_data_bundle, strategy_params
    )
    validation_features = features[
        features["_source"] == "validate"
    ].copy()

    minimum_history = int(strategy_params["minimum_history"])
    denominator = float(len(symbols))
    environment_rows: List[Dict[str, Any]] = []
    range_candidates: Dict[pd.Timestamp, List[str]] = {}
    trend_candidates: Dict[pd.Timestamp, List[str]] = {}

    grouped = {
        date: day.copy()
        for date, day in validation_features.groupby("_dt", sort=False)
    }

    for date in dates:
        day = grouped.get(date, validation_features.iloc[0:0].copy())

        valid_adx = (
            day["adx_1"].notna()
            & (day["valid_count_1"] >= minimum_history)
        )
        valid_count = int(valid_adx.sum())
        valid_ratio = valid_count / denominator
        environment_adx = (
            float(day.loc[valid_adx, "adx_1"].median())
            if valid_count
            else np.nan
        )
        eligible = (
            valid_ratio >= float(strategy_params["minimum_valid_ratio"])
            and np.isfinite(environment_adx)
        )

        if not eligible or environment_adx < float(
            strategy_params["range_adx_lower"]
        ):
            regime = "cash"
            regime_code = 0
        elif environment_adx <= float(
            strategy_params["trend_adx_lower"]
        ):
            regime = "range"
            regime_code = 1
        else:
            regime = "trend"
            regime_code = 2

        environment_rows.append(
            {
                TIME_COLUMN: date,
                "environment_adx": environment_adx,
                "valid_ratio": valid_ratio,
                "eligible": int(eligible),
                "regime_code": regime_code,
                "regime": regime,
            }
        )

        common_history = day["valid_count_1"] >= minimum_history
        positive_atr = day["atr_1"].notna() & (day["atr_1"] > 0)

        range_mask = (
            common_history
            & positive_atr
            & day["close_2"].notna()
            & day["boll_lower_2"].notna()
            & day["close_1"].notna()
            & day["boll_lower_1"].notna()
            & day["rsi_1"].notna()
            & (day["close_2"] <= day["boll_lower_2"])
            & (day["close_1"] > day["boll_lower_1"])
            & (day["close_1"] > day["close_2"])
            & (
                day["rsi_1"]
                < float(strategy_params["range_rsi_limit"])
            )
        )
        range_ranked = day.loc[range_mask].copy()
        range_ranked["range_distance"] = (
            range_ranked["close_1"] - range_ranked["boll_lower_1"]
        ) / range_ranked["atr_1"]
        range_ranked = range_ranked.sort_values(
            ["rsi_1", "range_distance", "code"],
            ascending=[True, False, True],
            kind="mergesort",
        )
        range_candidates[date] = range_ranked["code"].head(
            int(strategy_params["range_slots"])
        ).tolist()

        trend_mask = (
            common_history
            & positive_atr
            & day["ema5_1"].notna()
            & day["ema20_1"].notna()
            & day["ema60_1"].notna()
            & day["dif_1"].notna()
            & day["close_1"].notna()
            & day["volume_1"].notna()
            & day["volume_mean20_1"].notna()
            & (day["close_1"] > 0)
            & (day["ema5_1"] > day["ema20_1"])
            & (day["ema20_1"] > day["ema60_1"])
            & (day["dif_1"] > 0)
            & (
                day["volume_1"]
                > float(strategy_params["volume_multiple"])
                * day["volume_mean20_1"]
            )
        )
        trend_ranked = day.loc[trend_mask].copy()
        trend_ranked["trend_score"] = (
            trend_ranked["dif_1"] / trend_ranked["close_1"]
        )
        trend_ranked = trend_ranked.sort_values(
            ["trend_score", "code"],
            ascending=[False, True],
            kind="mergesort",
        )
        trend_candidates[date] = trend_ranked["code"].head(
            int(strategy_params["trend_slots"])
        ).tolist()

    environment = pd.DataFrame(environment_rows)
    return (
        validation_features,
        dates,
        symbols,
        environment,
        range_candidates,
        trend_candidates,
    )


def environment_adx_factor(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """返回验证期的环境ADX、有效比例和环境分类。"""
    _, _, _, environment, _, _ = _build_context(
        train_data_bundle, validate_data_bundle, params
    )
    return environment.reset_index(drop=True)


def prior_atr_factor(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """返回每个决策日开盘前已知的ATR14。"""
    features, dates, symbols = _calculate_features(
        train_data_bundle, validate_data_bundle, params
    )
    validation_features = features[
        features["_source"] == "validate"
    ]
    result = validation_features.pivot(
        index="_dt", columns="code", values="atr_1"
    ).reindex(index=dates, columns=symbols)
    result.columns.name = None
    result.insert(0, TIME_COLUMN, result.index)
    return result.reset_index(drop=True)


def range_entry_signal(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """返回震荡候选排名，1表示当天排名第一。"""
    _, dates, symbols, _, candidates, _ = _build_context(
        train_data_bundle, validate_data_bundle, params
    )
    result = pd.DataFrame(0, index=dates, columns=symbols, dtype=int)
    for date, ranked_symbols in candidates.items():
        for rank, symbol in enumerate(ranked_symbols, start=1):
            result.loc[date, symbol] = rank
    result.insert(0, TIME_COLUMN, result.index)
    return result.reset_index(drop=True)


def trend_entry_signal(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """返回趋势候选排名，1表示当天排名第一。"""
    _, dates, symbols, _, _, candidates = _build_context(
        train_data_bundle, validate_data_bundle, params
    )
    result = pd.DataFrame(0, index=dates, columns=symbols, dtype=int)
    for date, ranked_symbols in candidates.items():
        for rank, symbol in enumerate(ranked_symbols, start=1):
            result.loc[date, symbol] = rank
    result.insert(0, TIME_COLUMN, result.index)
    return result.reset_index(drop=True)


def _run_strategy(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    strategy_params: Dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """逐日模拟开盘交易，并返回开盘后权重和组合减仓记录。"""
    (
        features,
        dates,
        symbols,
        environment,
        range_candidates,
        trend_candidates,
    ) = _build_context(
        train_data_bundle, validate_data_bundle, strategy_params
    )

    environment_by_date = environment.set_index(TIME_COLUMN)
    day_by_date = {
        date: day.set_index("code", drop=False)
        for date, day in features.groupby("_dt", sort=False)
    }

    commission_rate = float(strategy_params["commission_bps"]) / 10000.0
    sell_tax_rate = float(strategy_params["sell_tax_bps"]) / 10000.0
    slippage_rate = float(strategy_params["slippage_bps"]) / 10000.0
    single_limit = float(strategy_params["single_position_limit"])

    if not 0 < single_limit <= 1:
        raise ValueError("single_position_limit必须在0和1之间")
    if min(commission_rate, sell_tax_rate, slippage_rate) < 0:
        raise ValueError("交易费用参数不能为负数")

    cash_value = 1.0
    positions: Dict[str, Dict[str, Any]] = {}
    active_environment = None
    range_batch_start = None
    range_renew_pending = False
    trend_ready_slots = 0
    trend_deferred_slots: Dict[int, int] = {}
    close_nav_history: List[float] = []

    weight_rows: List[Dict[str, Any]] = []
    risk_rows: List[Dict[str, Any]] = []

    for day_number, date in enumerate(dates):
        day = day_by_date.get(date)
        if day is None:
            day = pd.DataFrame(columns=features.columns).set_index(
                pd.Index([], name="code")
            )

        regime = str(environment_by_date.loc[date, "regime"])

        def field(symbol: str, column: str) -> float:
            if symbol not in day.index or column not in day.columns:
                return np.nan
            value = day.loc[symbol, column]
            if isinstance(value, pd.Series):
                value = value.iloc[0]
            try:
                return float(value)
            except (TypeError, ValueError):
                return np.nan

        def valid_price(value: float) -> bool:
            return bool(np.isfinite(value) and value > 0)

        def opening_value(symbol: str) -> float:
            current_open = field(symbol, "open")
            if valid_price(current_open):
                return current_open

            previous_close = field(symbol, "close_1")
            if valid_price(previous_close):
                return previous_close

            return float(positions[symbol]["last_price"])

        previous_close_return = np.nan
        if len(close_nav_history) >= 2 and close_nav_history[-2] > 0:
            previous_close_return = (
                close_nav_history[-1] / close_nav_history[-2] - 1.0
            )

        risk_reduction = bool(
            np.isfinite(previous_close_return)
            and previous_close_return
            < float(strategy_params["portfolio_loss_limit"])
        )
        position_multiplier = (
            float(strategy_params["risk_position_multiplier"])
            if risk_reduction
            else 1.0
        )
        risk_rows.append(
            {
                TIME_COLUMN: date,
                "previous_close_return": previous_close_return,
                "risk_reduction": int(risk_reduction),
                "position_multiplier": position_multiplier,
            }
        )

        if active_environment == "trend" and regime == "trend":
            trend_ready_slots += trend_deferred_slots.pop(day_number, 0)

        # 先检查上一交易日是否触及当时已经有效的止损价。
        for symbol, position in list(positions.items()):
            if position["pending_exit"]:
                continue
            if day_number <= position["entry_day"]:
                continue

            previous_low = field(symbol, "low_1")
            previous_close = field(symbol, "close_1")

            if (
                valid_price(previous_low)
                and previous_low <= position["stop_price"]
            ):
                position["pending_exit"] = True
                position["exit_reason"] = "stop"
                continue

            trigger_price = (
                position["entry_price"]
                + float(strategy_params["profit_trigger_atr_multiple"])
                * position["entry_atr"]
            )
            raised_stop = (
                position["entry_price"]
                + float(strategy_params["raised_stop_atr_multiple"])
                * position["entry_atr"]
            )
            if valid_price(previous_close) and previous_close >= trigger_price:
                position["stop_price"] = max(
                    position["stop_price"], raised_stop
                )

        # 环境变化时，旧环境持仓先退出。
        if active_environment != regime:
            active_environment = None
            range_batch_start = None
            range_renew_pending = False
            trend_ready_slots = 0
            trend_deferred_slots = {}
            for position in positions.values():
                position["pending_exit"] = True
                position["exit_reason"] = "environment"

        # 趋势持仓只按死叉、止损或环境变化退出。
        if active_environment == "trend" and regime == "trend":
            for symbol, position in positions.items():
                if position["pending_exit"]:
                    continue
                ema5_previous = field(symbol, "ema5_1")
                ema20_previous = field(symbol, "ema20_1")
                ema5_two_days_ago = field(symbol, "ema5_2")
                ema20_two_days_ago = field(symbol, "ema20_2")
                crossed_down = (
                    np.isfinite(ema5_previous)
                    and np.isfinite(ema20_previous)
                    and np.isfinite(ema5_two_days_ago)
                    and np.isfinite(ema20_two_days_ago)
                    and ema5_two_days_ago >= ema20_two_days_ago
                    and ema5_previous < ema20_previous
                )
                if crossed_down:
                    position["pending_exit"] = True
                    position["exit_reason"] = "ema_cross"

        # 买入日算第1日，第11个交易日开盘退出上一批。
        if (
            active_environment == "range"
            and regime == "range"
            and range_batch_start is not None
            and day_number - range_batch_start
            >= int(strategy_params["range_holding_days"])
        ):
            range_renew_pending = True
            for position in positions.values():
                if position["mode"] == "range":
                    position["pending_exit"] = True
                    position["exit_reason"] = "holding_period"

        def sell_quantity(symbol: str, quantity: float) -> None:
            nonlocal cash_value
            if quantity <= 0:
                return
            current_open = field(symbol, "open")
            if not valid_price(current_open):
                return

            quantity = min(quantity, positions[symbol]["shares"])
            execution_price = current_open * (1.0 - slippage_rate)
            proceeds = quantity * execution_price
            cash_value += proceeds * (
                1.0 - commission_rate - sell_tax_rate
            )
            positions[symbol]["shares"] -= quantity

        # 卖出订单优先执行；没有开盘价时继续保留到后续交易日。
        sold_modes: List[str] = []
        for symbol in list(positions):
            position = positions[symbol]
            if not position["pending_exit"]:
                continue
            if day_number <= position["entry_day"]:
                continue

            current_open = field(symbol, "open")
            if not valid_price(current_open):
                continue

            sold_mode = position["mode"]
            sell_quantity(symbol, position["shares"])
            if positions[symbol]["shares"] <= 1e-12:
                del positions[symbol]
                sold_modes.append(sold_mode)

        if active_environment == "trend" and regime == "trend":
            newly_empty_slots = sum(
                mode == "trend" for mode in sold_modes
            )
            if newly_empty_slots:
                activation_day = day_number + 1
                trend_deferred_slots[activation_day] = (
                    trend_deferred_slots.get(activation_day, 0)
                    + newly_empty_slots
                )

        entering_environment = False
        if active_environment is None and not positions:
            active_environment = regime
            entering_environment = True
            if regime == "trend":
                trend_ready_slots = int(strategy_params["trend_slots"])
            elif regime == "range":
                range_batch_start = day_number

        new_symbols: List[str] = []

        def add_member(symbol: str, mode: str) -> bool:
            if symbol in positions:
                return False

            current_open = field(symbol, "open")
            entry_atr = field(symbol, "atr_1")
            if not valid_price(current_open):
                return False
            if not np.isfinite(entry_atr) or entry_atr <= 0:
                return False

            positions[symbol] = {
                "shares": 0.0,
                "entry_price": np.nan,
                "entry_atr": entry_atr,
                "stop_price": np.nan,
                "entry_day": day_number,
                "mode": mode,
                "pending_exit": False,
                "exit_reason": "",
                "last_price": current_open,
            }
            new_symbols.append(symbol)
            return True

        if (
            active_environment == "range"
            and regime == "range"
            and entering_environment
        ):
            for symbol in range_candidates.get(date, []):
                add_member(symbol, "range")

        if (
            active_environment == "range"
            and regime == "range"
            and range_renew_pending
            and not positions
        ):
            range_batch_start = day_number
            range_renew_pending = False
            for symbol in range_candidates.get(date, []):
                add_member(symbol, "range")

        if active_environment == "trend" and regime == "trend":
            maximum_slots = int(strategy_params["trend_slots"])
            trend_ready_slots = min(
                trend_ready_slots,
                max(0, maximum_slots - len(positions)),
            )
            if trend_ready_slots > 0:
                for symbol in trend_candidates.get(date, []):
                    if trend_ready_slots <= 0:
                        break
                    if add_member(symbol, "trend"):
                        trend_ready_slots -= 1

        def open_nav() -> float:
            asset_value = sum(
                position["shares"] * opening_value(symbol)
                for symbol, position in positions.items()
            )
            return cash_value + asset_value

        # 正常持仓按同一金额调到目标比例，组合减仓日统一减半。
        desired_symbols = [
            symbol
            for symbol, position in positions.items()
            if (
                active_environment in {"range", "trend"}
                and position["mode"] == active_environment
                and not position["pending_exit"]
            )
        ]

        reference_nav = open_nav()
        target_slot = single_limit * position_multiplier
        cost_buffer = max(
            0.95,
            1.0
            - 2.0
            * (commission_rate + sell_tax_rate + slippage_rate),
        )
        target_value = target_slot * reference_nav * cost_buffer

        # 先减仓，再使用剩余现金买入。
        for symbol in sorted(desired_symbols):
            current_open = field(symbol, "open")
            if not valid_price(current_open):
                continue
            current_value = positions[symbol]["shares"] * current_open
            if current_value > target_value:
                sell_quantity(
                    symbol,
                    (current_value - target_value) / current_open,
                )

        for symbol in sorted(desired_symbols):
            current_open = field(symbol, "open")
            if not valid_price(current_open):
                continue

            current_value = positions[symbol]["shares"] * current_open
            missing_value = target_value - current_value
            if missing_value <= 0:
                continue

            execution_price = current_open * (1.0 + slippage_rate)
            full_quantity = missing_value / current_open
            full_cost = (
                full_quantity
                * execution_price
                * (1.0 + commission_rate)
            )
            if full_cost > cash_value:
                full_quantity *= max(cash_value, 0.0) / full_cost
                full_cost = cash_value

            if full_quantity <= 0:
                continue

            cash_value -= full_cost
            position = positions[symbol]
            position["shares"] += full_quantity

            if not np.isfinite(position["entry_price"]):
                position["entry_price"] = execution_price
                position["stop_price"] = (
                    execution_price
                    - float(strategy_params["stop_atr_multiple"])
                    * position["entry_atr"]
                )

        # 买入未成功时不建立空头寸记录。
        for symbol in list(new_symbols):
            if symbol not in positions:
                continue
            if positions[symbol]["shares"] > 1e-12:
                continue

            failed_mode = positions[symbol]["mode"]
            del positions[symbol]
            if (
                failed_mode == "trend"
                and active_environment == "trend"
            ):
                trend_ready_slots += 1

        nav_at_open = open_nav()
        if not np.isfinite(nav_at_open) or nav_at_open <= 0:
            raise RuntimeError("组合开盘净值无效，无法生成目标权重")

        row: Dict[str, Any] = {TIME_COLUMN: date}
        asset_weight_sum = 0.0
        for symbol in symbols:
            if symbol in positions:
                weight = (
                    positions[symbol]["shares"]
                    * opening_value(symbol)
                    / nav_at_open
                )
            else:
                weight = 0.0

            if weight < -1e-12:
                raise RuntimeError("中国股票权重不能为负数")
            weight = max(0.0, float(weight))
            row[symbol] = weight
            asset_weight_sum += weight

        cash_weight = 1.0 - asset_weight_sum
        if cash_weight < -1e-10:
            raise RuntimeError("现金权重小于0，策略产生了未允许的借款")
        row["cash"] = min(1.0, max(0.0, cash_weight))
        row["cash"] += 1.0 - (
            sum(row[symbol] for symbol in symbols) + row["cash"]
        )
        weight_rows.append(row)

        # 当前收盘数据只在当天权重已经生成后使用，供下一交易日判断。
        close_asset_value = 0.0
        for symbol, position in positions.items():
            current_close = field(symbol, "close")
            if valid_price(current_close):
                position["last_price"] = current_close
            close_asset_value += (
                position["shares"] * position["last_price"]
            )

        close_nav = cash_value + close_asset_value
        if not np.isfinite(close_nav) or close_nav <= 0:
            raise RuntimeError("组合收盘净值无效")
        close_nav_history.append(float(close_nav))

    weights = pd.DataFrame(weight_rows)
    weights = weights[[TIME_COLUMN] + symbols + ["cash"]]

    asset_sum = weights[symbols].sum(axis=1)
    total_sum = asset_sum + weights["cash"]
    if not np.allclose(total_sum.to_numpy(), 1.0, atol=1e-6):
        raise RuntimeError("目标权重与现金权重之和不等于1")
    if (weights[symbols] < -1e-12).any().any():
        raise RuntimeError("中国股票目标权重出现负数")
    if (
        (weights["cash"] < -1e-12)
        | (weights["cash"] > 1.0 + 1e-12)
    ).any():
        raise RuntimeError("现金权重不在0到1之间")

    return weights, pd.DataFrame(risk_rows)


def portfolio_risk_factor(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """返回前一收盘净值变化和当天组合减仓标记。"""
    _, risk_data = _run_strategy(
        train_data_bundle, validate_data_bundle, params
    )
    return risk_data


def output_weights(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """
    生成验证期间的开盘后目标权重。

    训练期只用于指标预热；验证期信号只读取当前开盘前已经可见的
    T-1及更早数据。当前开盘价只用于执行交易。
    """
    weights, _ = _run_strategy(
        train_data_bundle, validate_data_bundle, params
    )
    return weights


strategy_output = {
    "environment_adx_factor": {
        "description": "T开盘前成分股ADX14中位数、有效比例和环境分类",
        "function_name": "environment_adx_factor",
        "expected_characteristics": [
            "valid_ratio数值应位于0和1之间",
            "valid_ratio低于0.80时eligible必须等于0且regime_code必须等于0",
            "eligible等于1时，ADX低于20、20至25、超过25应分别对应环境编号0、1、2",
            "environment_adx应等于当日满足60条历史要求股票的ADX14中位数",
        ],
        "datetime_column": "trade_date",
    },
    "prior_atr_factor": {
        "description": "每只股票在T开盘前已知的T-1日Wilder ATR14",
        "function_name": "prior_atr_factor",
        "expected_characteristics": [
            "所有有限ATR值都应大于或等于0",
            "每个震荡或趋势新持仓对应的入场ATR必须严格大于0",
            "ATR只能随T-1及更早的最高价、最低价和收盘价变化",
        ],
        "datetime_column": "trade_date",
    },
    "range_entry_signal": {
        "description": "震荡模式候选股排序，非候选为0，1至3代表入选顺序",
        "function_name": "range_entry_signal",
        "expected_characteristics": [
            "每个日期最多有3个大于0的排名",
            "排名只能取0、1、2、3且正排名不得重复",
            "所有正排名股票必须同时满足下轨回归、价格回升和RSI5低于25",
            "排序应先按RSI5升序，再按下轨距离除以ATR降序，最后按股票代码升序",
        ],
        "datetime_column": "trade_date",
    },
    "trend_entry_signal": {
        "description": "趋势模式候选股排序，非候选为0，1至5代表入选顺序",
        "function_name": "trend_entry_signal",
        "expected_characteristics": [
            "每个日期最多有5个大于0的排名",
            "排名只能取0至5的整数且正排名不得重复",
            "所有正排名股票必须满足EMA5大于EMA20大于EMA60、DIF大于0和放量条件",
            "正排名应按DIF除以收盘价降序排列，同分时按股票代码升序",
        ],
        "datetime_column": "trade_date",
    },
    "portfolio_risk_factor": {
        "description": "前一交易日收盘净值变化及当天是否统一减半持仓",
        "function_name": "portfolio_risk_factor",
        "expected_characteristics": [
            "position_multiplier只能取1.0或0.5",
            "previous_close_return低于-0.02时risk_reduction必须等于1",
            "risk_reduction等于1时震荡和趋势正常仓位上限分别不超过22.5%和37.5%",
            "风险限制只由前两个已完成交易日的收盘净值决定",
        ],
        "datetime_column": "trade_date",
    },
    "output_weights_df": {
        "description": "验证期每个交易日开盘交易后的中国股票与现金权重；静态成分名单需在结果中说明幸存者偏差，缺少可交易状态需说明成交偏差",
        "function_name": "output_weights",
        "datetime_column": "trade_date",
    },
}

strategy_next_phase = "validate"
strategy_decision_reason = (
    "本轮没有上一轮统计结果，代码已实现全部交易规则，需要先检查"
    "2020至2023年的收益方向、年度稳定性、换手、费用敏感度、各环境表现"
    "以及缺失开盘价造成的延后交易；静态沪深300名单和缺少可交易状态也须单独说明。"
)

output_weights_df = output_weights(
    train_data_bundle,
    validate_data_bundle,
    params,
)