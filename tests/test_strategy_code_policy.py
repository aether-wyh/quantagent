from __future__ import annotations

import pytest

from quanta_agents.strategy_code_policy import (
    compile_strategy_definitions,
    validate_generated_strategy_code,
)


def test_event_strategy_rejects_result_fields_and_direct_file_reads() -> None:
    blocked = [
        'value = frame["forward_5m"]',
        'frame = pd.read_parquet("events.parquet")',
        'import os\npath = os.environ["QUANTA_EVENT_FEATURES_PATH"]',
        'from pathlib import Path\nraw = Path("events.parquet").read_bytes()',
        'from pandas import read_parquet as rp\nframe = rp("events.parquet")',
        'reader = pd.read_parquet\nframe = reader("events.parquet")',
        'value = frame.forward_5m',
        'value = frame["forward_" + "5m"]',
        'value = getattr(frame, "forward_5m")',
        'value = frame["analysis_only_full_day_low_to_close_ma5_distance"]',
        'value = frame.analysis_only_full_day_low_to_close_ma5_distance',
        'reader = pd.__dict__["read_parquet"]\nframe = reader("events.parquet")',
        'reader = open\nframe = reader("events.parquet")',
    ]

    for code in blocked:
        with pytest.raises(ValueError, match="事件策略代码检查失败"):
            validate_generated_strategy_code(code, event_mode=True)


def test_safe_event_strategy_code_is_allowed() -> None:
    code = """
def output_weights(train_data_bundle, validate_data_bundle, params):
    events = validate_data_bundle["periodic_minute_events"]
    return events["trigger_low_to_live_close_ma5_distance"]
"""

    validate_generated_strategy_code(code, event_mode=True)


def test_safe_exception_type_name_is_allowed() -> None:
    code = """
def describe_error(exc):
    return type(exc).__name__
"""

    validate_generated_strategy_code(code, event_mode=True)


@pytest.mark.parametrize(
    "code",
    [
        "result = frame.shift(-1)",
        "result = frame.shift(periods=-2)",
        "result = frame.shift(0 - 1)",
        "result = frame.shift(-lag_days)",
        "result = frame.bfill()",
        "result = frame.backfill()",
        'result = frame.fillna(method="bfill")',
        'result = frame.fillna(None, "backfill")',
        "result = frame.rolling(5, center=True).mean()",
        "result = frame.rolling(5, None, True).mean()",
        "result = frame.expanding(center=True).mean()",
    ],
)
def test_daily_strategy_rejects_obvious_future_row_operations(code: str) -> None:
    with pytest.raises(ValueError, match="日线策略代码检查失败"):
        validate_generated_strategy_code(code, event_mode=False)


@pytest.mark.parametrize(
    "code",
    [
        "result = frame.shift(1)",
        "result = frame.shift(periods=0)",
        "result = frame.ffill()",
        "result = frame.rolling(5, center=False).mean()",
        "result = frame.expanding().mean()",
    ],
)
def test_daily_strategy_allows_past_only_window_operations(code: str) -> None:
    validate_generated_strategy_code(code, event_mode=False)


@pytest.mark.parametrize(
    "code",
    [
        "import os",
        'frame = pd.read_parquet("prices.parquet")',
        "from pathlib import Path",
    ],
)
def test_daily_strategy_keeps_existing_import_and_file_safety_checks(code: str) -> None:
    with pytest.raises(ValueError, match="日线策略代码检查失败"):
        validate_generated_strategy_code(code, event_mode=False)


@pytest.mark.parametrize(
    "code",
    [
        """
for decision_date in signal_dates:
    current_member_codes = {
        str(code)
        for code in current_rows["code"]
        if _is_member_on_date(membership_lookup, code, decision_date)
    }
""",
        """
for decision_date in signal_dates:
    for code in current_rows["code"]:
        if _is_member_on_date(membership_lookup, code, decision_date):
            selected_codes.add(code)
""",
        """
flags = [
    _is_member_on_date(membership_lookup, code, decision_date)
    for decision_date in signal_dates
    for code in current_rows_by_date[decision_date]["code"]
]
""",
    ],
)
def test_daily_strategy_rejects_per_stock_membership_checks_in_nested_iterations(
    code: str,
) -> None:
    with pytest.raises(ValueError, match="先按日期生成成员集合"):
        validate_generated_strategy_code(code, event_mode=False)


def test_daily_strategy_allows_single_signal_row_membership_check() -> None:
    code = """
membership_flags = []
for decision_date, code in signal_rows[["trade_date", "code"]].itertuples(
    index=False,
    name=None,
):
    membership_flags.append(
        _is_member_on_date(membership_lookup, code, decision_date)
    )
"""

    validate_generated_strategy_code(code, event_mode=False)


def test_daily_strategy_allows_member_code_sets_prepared_before_date_loop() -> None:
    code = """
member_codes_by_date = {
    decision_date: set(
        membership.loc[
            membership["start_date"].le(decision_date)
            & membership["end_date"].ge(decision_date),
            "code",
        ].astype(str)
    )
    for decision_date in signal_dates
}
for decision_date in signal_dates:
    current_member_codes = member_codes_by_date[decision_date]
"""

    validate_generated_strategy_code(code, event_mode=False)


@pytest.mark.parametrize(
    "code",
    [
        "import pandas as pd",
        "import numpy as np",
        "import math",
        "import numbers",
        "import statistics",
        "import datetime",
        "from collections import defaultdict, deque",
        "from typing import Any, Dict",
        "from scipy import sparse",
    ],
)
def test_event_strategy_allows_only_needed_computation_imports(code: str) -> None:
    validate_generated_strategy_code(code, event_mode=True)


@pytest.mark.parametrize(
    "code",
    [
        "import sys",
        "import importlib",
        "import subprocess",
        "import socket",
        "import urllib.request",
        "import requests",
        "import pandas.io",
        "from numpy import load as loader",
    ],
)
def test_event_strategy_rejects_system_process_network_and_io_imports(
    code: str,
) -> None:
    with pytest.raises(ValueError, match="事件策略代码检查失败"):
        validate_generated_strategy_code(code, event_mode=True)


def test_definition_compile_skips_top_level_output_call() -> None:
    code = """
calls = []
def output_weights(train_data_bundle, validate_data_bundle, params):
    calls.append("called")
    return 1
output_weights_df = output_weights(train_data_bundle, validate_data_bundle, {})
"""
    namespace = {
        "train_data_bundle": {},
        "validate_data_bundle": {},
    }

    exec(compile_strategy_definitions(code), namespace)

    assert namespace["calls"] == []
    assert "output_weights_df" not in namespace


def test_definition_compile_skips_indirect_top_level_function_calls() -> None:
    code = """
calls = []
def helper():
    calls.append(len(validate_data_bundle))
helper()
result = helper()
"""
    namespace = {"validate_data_bundle": {}}

    exec(compile_strategy_definitions(code), namespace)

    assert namespace["calls"] == []
    assert "result" not in namespace


@pytest.mark.parametrize(
    "code",
    [
        "def bad(value=validate_data_bundle['events']):\n    return value",
        "def bad(value=make_value()):\n    return value",
        "@decorate(validate_data_bundle)\ndef bad():\n    return None",
        "def bad(value: validate_data_bundle['events']):\n    return value",
    ],
)
def test_definition_compile_rejects_definition_time_data_or_calls(code: str) -> None:
    with pytest.raises(ValueError, match="不得|不允许"):
        compile_strategy_definitions(code)


def test_definition_compile_keeps_literal_defaults_and_annotations() -> None:
    code = """
from __future__ import annotations
from typing import Any

params = {"threshold": 4}
def output_weights(data: Any, threshold: int = 4) -> int:
    return threshold
"""
    namespace: dict[str, object] = {}

    exec(compile_strategy_definitions(code), namespace)

    assert namespace["params"] == {"threshold": 4}
    assert namespace["output_weights"]({}, 7) == 7


def test_definition_compile_keeps_safe_optional_scipy_import() -> None:
    code = """
try:
    from scipy import sparse as scipy_sparse
except ImportError:
    scipy_sparse = None

def has_sparse_module():
    return scipy_sparse is not None
"""
    namespace: dict[str, object] = {}

    exec(compile_strategy_definitions(code), namespace)

    assert "scipy_sparse" in namespace
    assert callable(namespace["has_sparse_module"])
