from __future__ import annotations

from pathlib import Path

import pytest

from quanta_agents.calculation_contract import (
    CalculationContractError,
    check_calculation_contract_call_performance,
    check_generated_calculation_contracts,
    check_generated_consecutive_market_days,
    required_consecutive_market_days,
    required_date_offsets,
)


CONTRACT = {
    "contract_id": "market_returns",
    "table_key": "daily",
    "date_basis": "shared_market_trading_calendar",
    "required_dates": ["t", "t-1", "t-30"],
    "required_value_columns": ["close", "amount"],
    "allow_missing_intermediate_rows": True,
    "use_common_sample": True,
    "empty_sample_action": "condition_false",
}


GOOD_CODE = r'''
import pandas as pd

def calculation_contract_sample(
    daily_frame,
    market_dates,
    decision_date,
    contract,
    symbol_column,
    datetime_column,
):
    dates = pd.DatetimeIndex(pd.to_datetime(market_dates)).sort_values().unique()
    decision_position = dates.get_loc(pd.Timestamp(decision_date))
    required_dates = {
        pd.Timestamp(dates[decision_position - int(offset)])
        for offset in contract["required_offsets"]
    }
    work = daily_frame.copy()
    work[datetime_column] = pd.to_datetime(work[datetime_column])
    work = work.loc[work[datetime_column].isin(required_dates)]
    valid = work[contract["required_value_columns"]].notna().all(axis=1)
    work = work.loc[valid]
    counts = work.groupby(symbol_column)[datetime_column].nunique()
    selected = counts.loc[counts.eq(len(required_dates))].index
    if not contract["allow_missing_intermediate_rows"]:
        complete_dates = set(dates[decision_position - max(contract["required_offsets"]):decision_position + 1])
        complete = daily_frame.groupby(symbol_column)[datetime_column].agg(
            lambda values: complete_dates.issubset(set(pd.to_datetime(values)))
        )
        selected = selected.intersection(complete.loc[complete].index)
    return selected.tolist()

def market_filter(frame, dates, decision_date, contract):
    symbols = calculation_contract_sample(
        frame, dates, decision_date, contract, "symbol", "trade_date"
    )
    return bool(symbols)

def output_weights(train_data_bundle, validate_data_bundle, params):
    market_filter(
        validate_data_bundle["daily"],
        params["market_dates"],
        params["decision_date"],
        params["contract"],
    )
    return pd.DataFrame()
'''


BAD_PER_SYMBOL_CODE = r'''
import pandas as pd

def calculation_contract_sample(
    daily_frame,
    market_dates,
    decision_date,
    contract,
    symbol_column,
    datetime_column,
):
    work = daily_frame.sort_values([symbol_column, datetime_column])
    needed = len(contract["required_offsets"])
    counts = work.groupby(symbol_column).tail(needed).groupby(symbol_column).size()
    return counts.loc[counts.eq(needed)].index.tolist()

def output_weights(train_data_bundle, validate_data_bundle, params):
    calculation_contract_sample(
        validate_data_bundle["daily"], [], None, params, "symbol", "trade_date"
    )
    return pd.DataFrame()
'''


GOOD_CONSECUTIVE_CODE = r'''
import pandas as pd

def consecutive_market_day_sample(
    daily_frame, market_dates, consecutive_days, symbol_column, datetime_column
):
    dates = pd.DatetimeIndex(pd.to_datetime(market_dates)).sort_values().unique()
    date_positions = {pd.Timestamp(date): position for position, date in enumerate(dates)}
    work = daily_frame.copy()
    work[datetime_column] = pd.to_datetime(work[datetime_column])
    work["_position"] = work[datetime_column].map(date_positions)
    work = work.loc[work["_position"].notna()]
    available = {
        (str(symbol), int(position))
        for symbol, position in zip(work[symbol_column], work["_position"])
    }
    pairs = []
    for symbol in work[symbol_column].astype(str).unique():
        for end_position in range(consecutive_days - 1, len(dates)):
            if all(
                (symbol, position) in available
                for position in range(end_position - consecutive_days + 1, end_position + 1)
            ):
                pairs.append((symbol, pd.Timestamp(dates[end_position])))
    return pairs

def output_weights(train_data_bundle, validate_data_bundle, params):
    consecutive_market_day_sample(
        validate_data_bundle["daily"], params["market_dates"], 2, "symbol", "trade_date"
    )
    return pd.DataFrame()
'''


BAD_CONSECUTIVE_SHIFT_CODE = r'''
import pandas as pd

def consecutive_market_day_sample(
    daily_frame, market_dates, consecutive_days, symbol_column, datetime_column
):
    work = daily_frame.sort_values([symbol_column, datetime_column]).copy()
    work["_previous"] = work.groupby(symbol_column)[datetime_column].shift(1)
    selected = work.loc[work["_previous"].notna(), [symbol_column, datetime_column]]
    return list(selected.itertuples(index=False, name=None))

def output_weights(train_data_bundle, validate_data_bundle, params):
    consecutive_market_day_sample(
        validate_data_bundle["daily"], params["market_dates"], 2, "symbol", "trade_date"
    )
    return pd.DataFrame()
'''


BAD_REPEATED_FULL_HISTORY_CODE = r'''
def output_weights():
    history = load_daily_history()
    signal_dates = find_signal_dates(history)
    for decision_date in signal_dates:
        common_codes = calculation_contract_sample(
            history,
            market_dates,
            decision_date,
            MARKET_RETURN_CONTRACT,
            "code",
            "trade_date",
        )
    return common_codes
'''


BAD_REPEATED_HISTORY_SCAN_CODE = r'''
def output_weights():
    history = load_daily_history()
    for decision_date in signal_dates:
        required_dates = dates_for(decision_date)
        required_rows = history.loc[
            history["trade_date"].isin(required_dates)
        ].copy()
        calculation_contract_sample(
            required_rows,
            market_dates,
            decision_date,
            MARKET_RETURN_CONTRACT,
            "code",
            "trade_date",
        )
'''


BAD_DATE_MAP_BUILT_INSIDE_LOOP_CODE = r'''
def output_weights():
    history = load_daily_history()
    for decision_date in signal_dates:
        history_by_date = {
            date: date_rows
            for date, date_rows in history.groupby("trade_date", sort=False)
        }
        required_rows = pd.concat(
            [history_by_date[date] for date in dates_for(decision_date)]
        )
        calculation_contract_sample(
            required_rows,
            market_dates,
            decision_date,
            MARKET_RETURN_CONTRACT,
            "code",
            "trade_date",
        )
'''


GOOD_SINGLE_DATE_ROWS_CODE = r'''
def output_weights():
    cap_source = load_daily_history()
    for decision_date, date_rows in cap_source.groupby("trade_date", sort=True):
        calculation_contract_sample(
            date_rows,
            market_dates,
            decision_date,
            FLOAT_MARKET_CAP_CONTRACT,
            "code",
            "trade_date",
        )
'''


GOOD_REUSABLE_DATE_MAP_CODE = r'''
def output_weights():
    history = load_daily_history()
    history_by_date = {
        date: date_rows
        for date, date_rows in history.groupby("trade_date", sort=False)
    }
    for decision_date in signal_dates:
        required_dates = dates_for(decision_date)
        required_rows = pd.concat(
            [history_by_date[date] for date in required_dates],
            ignore_index=True,
        )
        calculation_contract_sample(
            required_rows,
            market_dates,
            decision_date,
            MARKET_RETURN_CONTRACT,
            "code",
            "trade_date",
        )
'''


def test_required_date_offsets_are_market_positions() -> None:
    assert required_date_offsets(["t", "T-1", "t-30"]) == [0, 1, 30]


def test_missing_intermediate_row_remains_in_common_sample() -> None:
    report = check_generated_calculation_contracts(GOOD_CODE, [CONTRACT])

    assert report["passed"] is True
    checked = report["checked_contracts"][0]
    assert checked["selected_symbols"] == ["FULL", "MIDDLE_MISSING"]


def test_per_symbol_row_shift_cannot_replace_shared_market_date() -> None:
    with pytest.raises(CalculationContractError, match="统一市场交易日共同样本不符合计划"):
        check_generated_calculation_contracts(BAD_PER_SYMBOL_CODE, [CONTRACT])


def test_defined_but_unused_sample_function_is_rejected() -> None:
    code = r'''
import pandas as pd
def calculation_contract_sample(
    daily_frame, market_dates, decision_date, contract, symbol_column, datetime_column
):
    return []
def output_weights(train_data_bundle, validate_data_bundle, params):
    return pd.DataFrame()
'''
    with pytest.raises(CalculationContractError, match="不能只定义不用"):
        check_generated_calculation_contracts(code, [CONTRACT])


def test_candidate_without_contract_keeps_previous_behavior() -> None:
    assert check_generated_calculation_contracts("", [])["skipped"] is True


def test_repeated_full_history_contract_call_is_rejected_before_execution() -> None:
    with pytest.raises(
        CalculationContractError,
        match="循环外的整段数据 `history`",
    ):
        check_calculation_contract_call_performance(BAD_REPEATED_FULL_HISTORY_CODE)


def test_repeated_history_loc_scan_is_rejected_before_execution() -> None:
    with pytest.raises(CalculationContractError, match="性能检查不通过"):
        check_calculation_contract_call_performance(BAD_REPEATED_HISTORY_SCAN_CODE)


def test_date_map_must_be_built_outside_repeated_decision_loop() -> None:
    with pytest.raises(CalculationContractError, match="性能检查不通过"):
        check_calculation_contract_call_performance(BAD_DATE_MAP_BUILT_INSIDE_LOOP_CODE)


def test_single_date_group_rows_are_allowed_for_offset_zero_contract() -> None:
    report = check_calculation_contract_call_performance(GOOD_SINGLE_DATE_ROWS_CODE)

    assert report["passed"] is True
    assert report["checked_repeated_calls"] == [
        {"line": 5, "daily_frame": "date_rows"}
    ]


def test_reusable_date_map_is_allowed_for_multi_date_contract() -> None:
    report = check_calculation_contract_call_performance(GOOD_REUSABLE_DATE_MAP_CODE)

    assert report["passed"] is True
    assert report["checked_repeated_calls"][0]["daily_frame"] == "required_rows"


def test_actual_epoch005_slow_code_is_rejected_and_candidate004_is_allowed() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    trace_root = repository_root / "experiment_traces"
    slow_code_path = (
        trace_root
        / "exp_consolidation_volume_box_v2_qlib_continue_20260814_231800"
        / "epochs_64"
        / "epoch_005"
        / "strategyagent"
        / "round_001"
        / "step_01_20260814_163924_809621.py"
    )
    candidate004_path = (
        trace_root
        / "exp_consolidation_volume_box_v2_qlib_continue_20260814_231800"
        / "epochs_64"
        / "epoch_004"
        / "strategyagent"
        / "round_001"
        / "step_01_20260814_161340_287294.py"
    )
    if not slow_code_path.is_file() or not candidate004_path.is_file():
        pytest.skip("本机没有这次研究的实际代码记录")

    with pytest.raises(CalculationContractError, match="第1114行"):
        check_calculation_contract_call_performance(
            slow_code_path.read_text(encoding="utf-8")
        )

    report = check_calculation_contract_call_performance(
        candidate004_path.read_text(encoding="utf-8")
    )
    assert report["checked_repeated_calls"] == [
        {"line": 1067, "daily_frame": "date_rows"}
    ]


def test_consecutive_days_are_found_from_baseline_decision() -> None:
    candidate = {
        "hypothesis": "接下来连续两个放量日，第二日为信号日",
        "decision_map": [
            {
                "source_kind": "explicit_condition",
                "field": "volume_expansion_consecutive_days",
                "value": 2,
            }
        ],
    }

    assert required_consecutive_market_days(candidate) == [2]


def test_consecutive_market_day_sample_accepts_exact_adjacent_dates() -> None:
    report = check_generated_consecutive_market_days(
        GOOD_CONSECUTIVE_CODE,
        {"hypothesis": "连续两天放量"},
    )

    assert report["passed"] is True
    assert report["checked_requirements"][0]["consecutive_days"] == 2


def test_per_symbol_shift_cannot_replace_previous_market_day() -> None:
    with pytest.raises(CalculationContractError, match="缺少紧邻市场日K线"):
        check_generated_consecutive_market_days(
            BAD_CONSECUTIVE_SHIFT_CODE,
            {"hypothesis": "连续两天放量"},
        )


def test_candidate_without_consecutive_days_skips_consecutive_check() -> None:
    report = check_generated_consecutive_market_days("", {"hypothesis": "单日放量"})

    assert report["skipped"] is True


def test_runtime_contract_keeps_check_when_later_candidate_omits_words() -> None:
    report = check_generated_consecutive_market_days(
        GOOD_CONSECUTIVE_CODE,
        {"hypothesis": "只修改箱体比例，其余规则不变"},
        continuity_contract={
            "mode": "consecutive_market_trading_days",
            "consecutive_days": 2,
            "condition_field": "consecutive_high_volume_days",
            "missing_bar_action": "condition_false",
        },
    )

    assert report["requirement_source"] == "market_day_continuity_contract"


def test_removed_condition_is_not_reenabled_by_modification_text_alone() -> None:
    report = check_generated_consecutive_market_days(
        "",
        {
            "hypothesis": "只检查单日放量",
            "strategy_modification": "删除连续两日条件",
        },
    )

    assert report["skipped"] is True
