from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix


_TABLE_KEY = "periodic_minute_events"
_REQUIRED_COLUMNS = [
    "date",
    "code",
    "candidate_id",
    "trigger_ts",
    "pulse5_return",
]


def _prepare_events(
    data_bundle: Dict[str, pd.DataFrame],
    start_date: str,
    end_date: str,
    period_name: str,
) -> pd.DataFrame:
    """检查并取出指定日期范围的候选事件。"""
    if _TABLE_KEY not in data_bundle:
        raise KeyError(
            f"数据导入或元数据维护问题：{period_name}缺少表 {_TABLE_KEY}"
        )

    source = data_bundle[_TABLE_KEY]
    if not isinstance(source, pd.DataFrame):
        raise TypeError(
            f"数据导入或元数据维护问题：{_TABLE_KEY} 必须是 DataFrame"
        )

    missing_columns = [
        column for column in _REQUIRED_COLUMNS if column not in source.columns
    ]
    if missing_columns:
        raise KeyError(
            "数据导入或元数据维护问题："
            f"{_TABLE_KEY} 缺少字段 {missing_columns}"
        )

    events = source.loc[:, _REQUIRED_COLUMNS].copy()

    valid_codes = events["code"].map(
        lambda value: isinstance(value, str) and len(value) > 0
    )
    if not bool(valid_codes.all()):
        raise ValueError(
            "数据导入或元数据维护问题：code 必须全部是非空字符串"
        )

    parsed_dates = pd.to_datetime(events["date"], errors="coerce")
    if bool(parsed_dates.isna().any()):
        raise ValueError(
            "数据导入或元数据维护问题：date 中存在无法识别的日期"
        )

    parsed_trigger_ts = pd.to_datetime(
        events["trigger_ts"],
        errors="coerce",
    )
    if bool(parsed_trigger_ts.isna().any()):
        raise ValueError(
            "数据导入或元数据维护问题：trigger_ts 中存在无法识别的时间"
        )

    parsed_pulse5_return = pd.to_numeric(
        events["pulse5_return"],
        errors="coerce",
    )
    invalid_pulse_values = (
        events["pulse5_return"].notna()
        & parsed_pulse5_return.isna()
    )
    if bool(invalid_pulse_values.any()):
        raise ValueError(
            "数据导入或元数据维护问题："
            "pulse5_return 中存在无法识别的非缺失数值"
        )

    events["date"] = parsed_dates
    events["trigger_ts"] = parsed_trigger_ts
    events["pulse5_return"] = parsed_pulse5_return

    start_value = pd.Timestamp(start_date).date()
    end_value = pd.Timestamp(end_date).date()
    event_dates = events["date"].dt.date
    period_mask = event_dates.between(start_value, end_value)

    period_events = events.loc[period_mask].reset_index(drop=True)
    if period_events.empty:
        raise ValueError(
            f"数据导入或元数据维护问题：{period_name}没有指定日期范围内的事件"
        )

    return period_events


def _has_complete_horizon(
    trigger_ts: pd.Series,
    horizon_minutes: int,
) -> pd.Series:
    """判断评价时间是否完整处于同一上午或下午交易时段。"""
    trigger_day = trigger_ts.dt.normalize()
    horizon_end = trigger_ts + pd.Timedelta(
        minutes=horizon_minutes
    )

    morning_start = trigger_day + pd.Timedelta(
        hours=9,
        minutes=30,
    )
    morning_end = trigger_day + pd.Timedelta(
        hours=11,
        minutes=30,
    )
    afternoon_start = trigger_day + pd.Timedelta(hours=13)
    afternoon_end = trigger_day + pd.Timedelta(hours=15)

    complete_morning = (
        trigger_ts.ge(morning_start)
        & horizon_end.le(morning_end)
    )
    complete_afternoon = (
        trigger_ts.ge(afternoon_start)
        & horizon_end.le(afternoon_end)
    )
    return complete_morning | complete_afternoon


def _keep_earlier_spaced_events(
    events: pd.DataFrame,
    minimum_gap_minutes: int,
) -> pd.DataFrame:
    """同一股票事件间隔不足指定分钟数时，只保留较早事件。"""
    if events.empty:
        return events.copy()

    ordered = events.sort_values(
        ["code", "trigger_ts"],
        kind="mergesort",
    ).reset_index(drop=True)

    trigger_values = (
        ordered["trigger_ts"].astype("int64").to_numpy()
    )
    minimum_gap = pd.Timedelta(
        minutes=minimum_gap_minutes
    ).value
    keep_mask = np.zeros(len(ordered), dtype=bool)

    grouped_positions = ordered.groupby(
        "code",
        sort=False,
    ).indices

    for positions in grouped_positions.values():
        last_kept_trigger = None
        for position in positions:
            current_trigger = trigger_values[position]
            if (
                last_kept_trigger is None
                or current_trigger - last_kept_trigger >= minimum_gap
            ):
                keep_mask[position] = True
                last_kept_trigger = current_trigger

    return (
        ordered.loc[keep_mask]
        .sort_values(["trigger_ts", "code"], kind="mergesort")
        .reset_index(drop=True)
    )


def _select_events(
    events: pd.DataFrame,
    params: Dict[str, Any],
) -> pd.DataFrame:
    """按已批准的D5条件筛选并处理重复及相邻事件。"""
    deduplicated = events.drop_duplicates(
        subset=["trigger_ts", "code"],
        keep="first",
    )

    selected = deduplicated.loc[
        deduplicated["pulse5_return"].notna()
        & deduplicated["pulse5_return"].le(
            params["pulse5_return_max"]
        )
    ].copy()

    complete_horizon = _has_complete_horizon(
        selected["trigger_ts"],
        params["event_horizon_minutes"],
    )
    selected = selected.loc[complete_horizon].copy()

    return _keep_earlier_spaced_events(
        selected,
        params["event_horizon_minutes"],
    )


def _summarize_training_events(
    train_events: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, int]:
    """
    只统计训练期基础候选及入选事件数量。

    这些数字不用于筛选、排序或改变目标比例。
    """
    selected = _select_events(train_events, params)

    return {
        "candidate_event_count": int(len(train_events)),
        "selected_event_count": int(len(selected)),
        "selected_trigger_count": int(
            selected["trigger_ts"].nunique()
        ),
        "selected_code_count": int(selected["code"].nunique()),
        "missing_pulse5_return_count": int(
            train_events["pulse5_return"].isna().sum()
        ),
    }


def _market_for_codes(
    codes: List[str],
    universe_definition: Any,
) -> Dict[str, str]:
    """依据注入的 universe 判断每只股票所属的市场。"""
    if not isinstance(universe_definition, list) or not universe_definition:
        raise ValueError(
            "数据导入或元数据维护问题：universe 必须是非空列表"
        )

    code_set = set(codes)
    code_market: Dict[str, str] = {}
    all_assets = set()
    dataset_assets = set()

    for item in universe_definition:
        if not isinstance(item, dict):
            raise TypeError(
                "数据导入或元数据维护问题：universe 的每一项必须是字典"
            )

        asset = item.get("asset")
        if asset not in {"中国股票", "期货"}:
            raise ValueError(
                "数据导入或元数据维护问题："
                "universe 的 asset 只能是中国股票或期货"
            )
        all_assets.add(asset)

        symbols = item.get("symbols", [])
        if symbols is None:
            symbols = []
        if not isinstance(symbols, list):
            raise TypeError(
                "数据导入或元数据维护问题："
                "universe 中的 symbols 必须是列表"
            )

        is_dataset_defined = (
            item.get("type") == "dataset_defined"
            or "dataset" in item
        )
        dataset_name = item.get("dataset")
        if is_dataset_defined and (
            dataset_name is None
            or dataset_name == _TABLE_KEY
        ):
            dataset_assets.add(asset)

        for symbol in symbols:
            if symbol not in code_set:
                continue
            previous_asset = code_market.get(symbol)
            if previous_asset is not None and previous_asset != asset:
                raise ValueError(
                    "数据导入或元数据维护问题："
                    f"{symbol} 在 universe 中对应多个市场"
                )
            code_market[symbol] = asset

    if dataset_assets:
        if len(dataset_assets) != 1:
            raise ValueError(
                "数据导入或元数据维护问题："
                f"{_TABLE_KEY} 在 universe 中对应多个市场"
            )
        dataset_asset = next(iter(dataset_assets))
        for code in codes:
            previous_asset = code_market.get(code)
            if (
                previous_asset is not None
                and previous_asset != dataset_asset
            ):
                raise ValueError(
                    "数据导入或元数据维护问题："
                    f"{code} 的市场定义互相冲突"
                )
            code_market[code] = dataset_asset

    missing_codes = [
        code for code in codes if code not in code_market
    ]
    if missing_codes and len(all_assets) == 1:
        only_asset = next(iter(all_assets))
        for code in missing_codes:
            code_market[code] = only_asset
        missing_codes = []

    if missing_codes:
        examples = missing_codes[:5]
        raise ValueError(
            "数据导入或元数据维护问题："
            f"无法依据 universe 判断部分代码的市场，示例：{examples}"
        )

    return code_market


def output_weights(
    train_data_bundle: Dict[str, pd.DataFrame],
    validate_data_bundle: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> pd.DataFrame:
    """
    生成验证期间的目标权重矩阵（无未来数据）。

    每一行的 trigger_ts 是目标比例形成时间，实际执行从下一分钟
    开盘开始，并在 trigger 后第20分钟收盘评价。仅保留
    pulse5_return 不高于批准阈值的事件，缺失值不入选。
    同一时间下的全部合格股票等权。
    """
    train_events = _prepare_events(
        train_data_bundle,
        params["train_start"],
        params["train_end"],
        "训练期",
    )
    validate_events = _prepare_events(
        validate_data_bundle,
        params["validate_start"],
        params["validate_end"],
        "验证期",
    )

    # 训练期只做说明性数量统计，不读取评价字段或确定新阈值。
    _summarize_training_events(train_events, params)

    all_codes = sorted(
        validate_events["code"].unique().tolist()
    )
    market_by_code = _market_for_codes(all_codes, universe)

    all_trigger_ts = pd.Index(
        validate_events["trigger_ts"].drop_duplicates()
    ).sort_values()

    selected_events = _select_events(validate_events, params)
    selected = selected_events.loc[
        :,
        ["trigger_ts", "code"],
    ]

    selected_count = selected.groupby(
        "trigger_ts",
        sort=False,
    )["code"].size()

    trigger_position = pd.Series(
        np.arange(len(all_trigger_ts), dtype=np.int64),
        index=all_trigger_ts,
    )
    code_position = {
        code: position
        for position, code in enumerate(all_codes)
    }

    if selected.empty:
        row_positions = np.array([], dtype=np.int64)
        column_positions = np.array([], dtype=np.int64)
        weight_values = np.array([], dtype=float)
    else:
        row_positions = (
            selected["trigger_ts"]
            .map(trigger_position)
            .to_numpy(dtype=np.int64)
        )
        column_positions = (
            selected["code"]
            .map(code_position)
            .to_numpy(dtype=np.int64)
        )
        weight_values = (
            1.0
            / selected["trigger_ts"]
            .map(selected_count)
            .to_numpy(dtype=float)
        )

    weight_matrix = coo_matrix(
        (
            weight_values,
            (row_positions, column_positions),
        ),
        shape=(len(all_trigger_ts), len(all_codes)),
        dtype=float,
    ).tocsr()

    # 中国股票不得出现负权重。
    chinese_column_positions = {
        position
        for position, code in enumerate(all_codes)
        if market_by_code[code] == "中国股票"
    }
    if chinese_column_positions and weight_matrix.nnz:
        negative_columns = set(
            weight_matrix.indices[
                weight_matrix.data < -1e-12
            ].tolist()
        )
        if negative_columns.intersection(
            chinese_column_positions
        ):
            raise ValueError("中国股票目标权重不能小于零")

    selected_by_time = (
        selected_count.reindex(
            all_trigger_ts,
            fill_value=0,
        ).to_numpy(dtype=np.int64)
    )
    cash_weights = np.where(
        selected_by_time == 0,
        1.0,
        0.0,
    )

    total_weights = (
        np.asarray(weight_matrix.sum(axis=1)).reshape(-1)
        + cash_weights
    )
    if not np.allclose(
        total_weights,
        1.0,
        atol=1e-6,
    ):
        raise ValueError("目标权重与现金权重之和必须等于1")
    if (
        np.any(cash_weights < 0.0)
        or np.any(cash_weights > 1.0)
    ):
        raise ValueError("现金权重必须在0到1之间")

    asset_weights = pd.DataFrame.sparse.from_spmatrix(
        weight_matrix,
        columns=all_codes,
    )
    asset_weights.insert(
        0,
        "trigger_ts",
        all_trigger_ts,
    )
    asset_weights["cash"] = cash_weights

    return asset_weights.reset_index(drop=True)


params: Dict[str, Any] = {
    "train_start": "2022-01-01",
    "train_end": "2023-12-31",
    "validate_start": "2024-01-01",
    "validate_end": "2024-12-31",
    "pulse5_return_max": -0.006113537117903958,
    "event_horizon_minutes": 20,
    "generic_selection_conditions": [
        {
            "feature": "pulse5_return",
            "operator": "<=",
            "value": -0.006113537117903958,
        },
    ],
}


strategy_output = {
    "output_weights_df": {
        "description": (
            "验证期基础分钟候选事件先按trigger_ts和code去重，"
            "仅保留pulse5_return不高于批准阈值且数值不缺失的事件，"
            "排除无法在同一上午或下午取得完整20分钟价格的事件，"
            "同一股票不足20分钟的相邻事件只保留较早一次，"
            "同一trigger_ts下全部合格股票等权，从下一分钟开盘进入，"
            "并在trigger后第20分钟收盘评价的目标比例矩阵"
        ),
        "function_name": "output_weights",
        "datetime_column": "trigger_ts",
    }
}


strategy_next_phase = "validate"
strategy_decision_reason = (
    "已将pulse5_return上限从-0.004851349670356973"
    "改为-0.006113537117903958，"
    "20分钟评价时间及其他规则保持不变，需要重新进行统计验证"
)


output_weights_df = output_weights(
    train_data_bundle,
    validate_data_bundle,
    params,
)