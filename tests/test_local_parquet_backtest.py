from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("duckdb")

MODULE_PATH = PROJECT_ROOT / "src" / "quanta_agents" / "local_parquet_backtest.py"
MODULE_SPEC = importlib.util.spec_from_file_location("local_parquet_backtest", MODULE_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)
normalize_stock_code = MODULE.normalize_stock_code
load_market_dates = MODULE.load_market_dates
run_target_weight_backtest = MODULE.run_target_weight_backtest


def _write_market(path: Path, rows: list[dict[str, object]]) -> None:
    frame = pd.DataFrame(rows)
    if "qfq_ratio" not in frame.columns:
        frame["qfq_ratio"] = 1.0
    if "raw_open" not in frame.columns:
        frame["raw_open"] = frame["open"] / frame["qfq_ratio"]
    if "raw_prev_close" not in frame.columns:
        frame["raw_prev_close"] = frame["prev_close"] / frame["qfq_ratio"]
    if "is_st" not in frame.columns:
        frame["is_st"] = False
    if "is_delisting" not in frame.columns:
        frame["is_delisting"] = False
    frame.to_parquet(path, index=False)


def test_normalize_stock_code_supports_common_exchange_suffixes() -> None:
    assert normalize_stock_code("sh600000") == "sh600000"
    assert normalize_stock_code("600000.SH") == "sh600000"
    assert normalize_stock_code("600000.SSE") == "sh600000"
    assert normalize_stock_code("sz000001") == "sz000001"
    assert normalize_stock_code("000001.SZSE") == "sz000001"


def test_load_market_dates_filters_codes_and_period(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "daily.parquet",
        [
            {
                "date": date,
                "code": code,
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
            for date, code in (
                ("2024-01-01", "sh600000"),
                ("2024-01-02", "600000.SH"),
                ("2024-01-03", "sz000001"),
                ("2024-01-04", "sh600000"),
            )
        ],
    )

    dates = load_market_dates(
        tmp_path,
        ["600000.SSE", "sh600000"],
        "2024-01-02 15:30:00+08:00",
        "2024-01-04",
    )

    assert dates.equals(
        pd.DatetimeIndex(["2024-01-02", "2024-01-04"], name="trade_date")
    )
    assert dates.tz is None


def test_load_market_dates_rejects_empty_codes_and_reversed_period(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="至少要有一个"):
        load_market_dates(tmp_path, [], "2024-01-01", "2024-01-02")

    with pytest.raises(ValueError, match="不能早于"):
        load_market_dates(tmp_path, ["600000.SH"], "2024-01-03", "2024-01-02")


def test_load_market_dates_reports_when_selected_stock_has_no_rows(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "daily.parquet",
        [
            {
                "date": "2024-01-02",
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
        ],
    )

    with pytest.raises(ValueError, match="没有行情"):
        load_market_dates(tmp_path, ["000001.SZ"], "2024-01-01", "2024-01-03")


def test_target_weights_trade_next_open_sell_first_and_use_board_lots(tmp_path: Path) -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    market_rows: list[dict[str, object]] = []
    prices = {
        "sh600000": [(10.0, 10.0, 9.8), (10.0, 10.5, 10.0), (11.0, 11.0, 10.5), (11.0, 11.5, 11.0)],
        "sz000001": [(20.0, 20.0, 19.8), (20.0, 20.0, 20.0), (20.0, 21.0, 20.0), (21.0, 21.0, 21.0)],
    }
    for code, code_prices in prices.items():
        for date, (open_price, close_price, prev_close) in zip(dates, code_prices):
            market_rows.append(
                {
                    "date": date,
                    "code": code,
                    "open": open_price,
                    "high": max(open_price, close_price),
                    "low": min(open_price, close_price),
                    "close": close_price,
                    "volume": 1_000_000.0,
                    "prev_close": prev_close,
                }
            )
    _write_market(tmp_path / "daily.parquet", market_rows)

    weights = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "600000.SSE": [1.0, 0.0],
            "000001.SZSE": [0.0, 1.0],
            "cash": [0.0, 0.0],
        }
    )
    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start="2024-01-02",
        end="2024-01-05",
        capital=100_000.0,
    )

    daily = stats["_daily_df"].set_index("date")
    trades = stats["_trades_df"]
    assert daily.loc[pd.Timestamp("2024-01-02"), "trade_count"] == 0
    assert daily.loc[pd.Timestamp("2024-01-03"), "trade_count"] == 1
    assert daily.loc[pd.Timestamp("2024-01-04"), "trade_count"] == 2
    assert trades["side"].tolist() == ["buy", "sell", "buy"]
    assert trades["code"].tolist() == ["sh600000", "sh600000", "sz000001"]
    assert bool((trades["shares"] % 100 == 0).all())
    assert int(trades.iloc[2]["shares"]) > 0
    assert daily.loc[pd.Timestamp("2024-01-03"), "commission"] == pytest.approx(
        float(trades.iloc[0]["turnover"]) * 0.0003
    )
    assert stats["total_trade_count"] == 3
    for key in ("annual_return", "sharpe_ratio", "max_drawdown", "max_ddpercent"):
        assert isinstance(stats[key], float)


def test_zero_weight_columns_are_not_loaded_and_results_stay_the_same(
    tmp_path: Path,
) -> None:
    _write_market(
        tmp_path / "daily.parquet",
        [
            {
                "date": date,
                "code": code,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 1_000_000.0,
                "prev_close": price,
            }
            for date, code, price in (
                ("2024-01-02", "sh600000", 10.0),
                ("2024-01-04", "sh600000", 11.0),
                ("2024-01-02", "sz000001", 20.0),
                ("2024-01-03", "sz000001", 20.0),
                ("2024-01-04", "sz000001", 20.0),
            )
        ],
    )
    weights = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "600000.SH": [1.0, 1.0],
            "000001.SZ": [0.0, 0.0],
            "cash": [0.0, 0.0],
        }
    )
    resolved_path = MODULE._resolve_parquet_path(tmp_path)
    start = pd.Timestamp("2024-01-02")
    end = pd.Timestamp("2024-01-04")
    all_codes = ["sh600000", "sz000001"]
    full_market = MODULE._load_market_data(resolved_path, all_codes, start, end)
    full_bundle = {
        "start": start,
        "end": end,
        "calendar_codes": tuple(all_codes),
        "raw_codes": tuple(all_codes),
        "market_dates": MODULE._load_market_calendar(
            resolved_path,
            all_codes,
            start,
            end,
        ),
        "bars_by_date": {
            pd.Timestamp(trade_date): frame.set_index("raw_code", drop=False)
            for trade_date, frame in full_market.groupby("trade_date", sort=True)
        },
    }
    reference = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start=start,
        end=end,
        prepared_market=full_bundle,
    )

    original_loader = MODULE._load_market_data
    with patch.object(MODULE, "_load_market_data", wraps=original_loader) as loader:
        optimized = run_target_weight_backtest(
            weights,
            parquet_path=tmp_path,
            start=start,
            end=end,
        )

    assert loader.call_args.args[1] == ["sh600000"]
    assert optimized["total_trade_count"] == 1
    assert optimized["_daily_df"]["date"].tolist() == list(
        pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    )
    for key in (
        "end_balance",
        "total_return",
        "annual_return",
        "annual_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "max_ddpercent",
        "total_commission",
        "total_slippage",
        "win_rate",
        "profit_loss_ratio",
    ):
        assert optimized[key] == pytest.approx(reference[key])
    pd.testing.assert_frame_equal(optimized["_daily_df"], reference["_daily_df"])
    pd.testing.assert_frame_equal(optimized["_trades_df"], reference["_trades_df"])


def test_pure_cash_strategy_still_loads_every_stock_column(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "daily.parquet",
        [
            {
                "date": "2024-01-02",
                "code": code,
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
            for code in ("sh600000", "sz000001")
        ],
    )
    weights = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "600000.SH": [0.0],
            "000001.SZ": [0.0],
            "cash": [1.0],
        }
    )

    original_loader = MODULE._load_market_data
    with patch.object(MODULE, "_load_market_data", wraps=original_loader) as loader:
        stats = run_target_weight_backtest(
            weights,
            parquet_path=tmp_path,
            start="2024-01-02",
            end="2024-01-02",
        )

    assert loader.call_args.args[1] == ["sh600000", "sz000001"]
    assert stats["total_trade_count"] == 0
    assert stats["end_balance"] == pytest.approx(1_000_000.0)


@pytest.mark.parametrize(
    ("open_price", "volume"),
    [(11.0, 1_000_000.0), (10.0, 0.0)],
)
def test_limit_up_or_suspension_blocks_buy(
    tmp_path: Path,
    open_price: float,
    volume: float,
) -> None:
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": "2024-01-02",
                "code": "600000.SH",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
            {
                "date": "2024-01-03",
                "code": "600000.SH",
                "open": open_price,
                "high": open_price,
                "low": open_price,
                "close": open_price,
                "volume": volume,
                "prev_close": 10.0,
            },
        ],
    )
    weights = pd.DataFrame(
        {
            "trade_date": ["2024-01-02"],
            "sh600000": [1.0],
            "cash": [0.0],
        }
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path / "*.parquet",
        start="2024-01-02",
        end="2024-01-03",
        capital=100_000.0,
    )

    assert stats["total_trade_count"] == 0
    assert stats["end_balance"] == pytest.approx(100_000.0)


def test_chinext_uses_twenty_percent_price_limit(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "sz300001.parquet",
        [
            {
                "date": "2024-01-02",
                "code": "sz300001",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
            {
                "date": "2024-01-03",
                "code": "sz300001",
                "open": 11.0,
                "high": 11.0,
                "low": 11.0,
                "close": 11.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
        ],
    )
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "300001.SZ": [1.0], "cash": [0.0]}
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start="2024-01-02",
        end="2024-01-03",
        capital=100_000.0,
    )

    assert stats["total_trade_count"] == 1


@pytest.mark.parametrize(
    ("code", "trade_date", "expected_ratio"),
    [
        ("sz300001", "2020-08-21", 0.10),
        ("sz300001", "2020-08-24", 0.20),
        ("sz302132", "2020-08-21", 0.10),
        ("sz302132", "2020-08-24", 0.20),
    ],
)
def test_sz300_and_sz302_price_limit_changes_on_reform_date(
    code: str,
    trade_date: str,
    expected_ratio: float,
) -> None:
    assert MODULE._daily_limit_ratio(code, trade_date) == pytest.approx(
        expected_ratio
    )


@pytest.mark.parametrize(
    "code", ["sz301001", "sz302132", "sh688001", "sh689009"]
)
def test_post_reform_boards_use_twenty_percent_price_limit(code: str) -> None:
    assert MODULE._daily_limit_ratio(code, "2021-01-04") == pytest.approx(0.20)


def test_sz302_eleven_percent_open_is_not_blocked_as_limit_up(
    tmp_path: Path,
) -> None:
    _write_market(
        tmp_path / "sz302132.parquet",
        [
            {
                "date": "2024-01-02",
                "code": "sz302132",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
            {
                "date": "2024-01-03",
                "code": "sz302132",
                "open": 11.1,
                "high": 11.1,
                "low": 11.1,
                "close": 11.1,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
        ],
    )
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "302132.SZ": [1.0], "cash": [0.0]}
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start="2024-01-02",
        end="2024-01-03",
        capital=100_000.0,
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.0,
        lot_size=0,
    )

    assert stats["_trades_df"]["side"].tolist() == ["buy"]


@pytest.mark.parametrize(
    ("code", "trade_date", "expected_ratio"),
    [
        ("sh600000", "2024-01-03", 0.05),
        ("sz000001", "2024-01-03", 0.05),
        ("sz300001", "2020-08-21", 0.05),
        ("sz300001", "2020-08-24", 0.20),
        ("sz302132", "2020-08-21", 0.05),
        ("sz302132", "2020-08-24", 0.20),
        ("sz301001", "2024-01-03", 0.20),
        ("sh688001", "2024-01-03", 0.20),
    ],
)
def test_st_price_limit_depends_on_board_and_chinext_reform_date(
    code: str,
    trade_date: str,
    expected_ratio: float,
) -> None:
    assert MODULE._daily_limit_ratio(
        code,
        trade_date,
        is_st=True,
    ) == pytest.approx(expected_ratio)


def test_price_limits_round_raw_price_to_cent_before_readjusting() -> None:
    bar = pd.Series(
        {
            "raw_code": "sh600000",
            "trade_date": pd.Timestamp("2024-01-03"),
            # 故意与官方原始前收盘不一致，确保计算不再用前复权昨收还原。
            "prev_close": 999.0,
            "raw_prev_close": 10.05,
            "qfq_ratio": 1.2,
            "is_st": False,
        }
    )

    assert MODULE._limit_up_price(bar, "sh600000") == pytest.approx(13.272)
    assert MODULE._limit_down_price(bar, "sh600000") == pytest.approx(10.86)


def test_limit_up_compares_raw_cents_despite_adjusted_open_error() -> None:
    qfq_ratio = 0.8765
    bar = pd.Series(
        {
            "raw_code": "sh600000",
            "trade_date": pd.Timestamp("2024-01-03"),
            "prev_close": 319.64 * qfq_ratio,
            "open": 351.60 * qfq_ratio - 0.00002,
            "raw_prev_close": 319.64,
            "raw_open": 351.60,
            "qfq_ratio": qfq_ratio,
            "is_st": False,
            "is_delisting": False,
        }
    )

    assert MODULE._raw_limit_price(bar, "sh600000", direction=1) == MODULE.Decimal(
        "351.60"
    )
    assert MODULE._is_limit_up(bar, "sh600000") is True


def test_limit_down_compares_raw_cents_despite_adjusted_open_error() -> None:
    qfq_ratio = 0.8765
    bar = pd.Series(
        {
            "raw_code": "sh600000",
            "trade_date": pd.Timestamp("2024-01-03"),
            "prev_close": 390.67 * qfq_ratio,
            "open": 351.60 * qfq_ratio + 0.00002,
            "raw_prev_close": 390.67,
            "raw_open": 351.60,
            "qfq_ratio": qfq_ratio,
            "is_st": False,
            "is_delisting": False,
        }
    )

    assert MODULE._raw_limit_price(bar, "sh600000", direction=-1) == MODULE.Decimal(
        "351.60"
    )
    assert MODULE._is_limit_down(bar, "sh600000") is True


@pytest.mark.parametrize("raw_open", [8.0, 12.0])
def test_delisting_open_strictly_outside_ordinary_limits_is_not_blocked(
    raw_open: float,
) -> None:
    bar = pd.Series(
        {
            "raw_code": "sh600000",
            "trade_date": pd.Timestamp("2024-01-03"),
            "raw_prev_close": 10.0,
            "raw_open": raw_open,
            "is_st": False,
            "is_delisting": True,
        }
    )

    assert MODULE._is_limit_up(bar, "sh600000") is False
    assert MODULE._is_limit_down(bar, "sh600000") is False


@pytest.mark.parametrize("qfq_ratio", [None, 0.0, float("nan")])
def test_invalid_qfq_ratio_is_rejected_directly(
    tmp_path: Path,
    qfq_ratio: float | None,
) -> None:
    rows = [
        {
            "date": date,
            "code": "sh600000",
            "open": 10.0,
            "high": 10.0,
            "low": 10.0,
            "close": 10.0,
            "volume": 1_000_000.0,
            "prev_close": 10.0,
            "qfq_ratio": qfq_ratio,
        }
        for date in ("2024-01-02", "2024-01-03")
    ]
    _write_market(tmp_path / "daily.parquet", rows)
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "600000.SH": [1.0], "cash": [0.0]}
    )

    with pytest.raises(ValueError, match="无效 qfq_ratio"):
        run_target_weight_backtest(
            weights,
            parquet_path=tmp_path,
            start="2024-01-02",
            end="2024-01-03",
        )


def test_missing_qfq_ratio_column_is_rejected_directly(tmp_path: Path) -> None:
    pd.DataFrame(
        [
            {
                "date": date,
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
            for date in ("2024-01-02", "2024-01-03")
        ]
    ).to_parquet(tmp_path / "daily.parquet", index=False)
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "600000.SH": [1.0], "cash": [0.0]}
    )

    with pytest.raises(ValueError, match="必须包含 qfq_ratio"):
        run_target_weight_backtest(
            weights,
            parquet_path=tmp_path,
            start="2024-01-02",
            end="2024-01-03",
        )


def test_missing_official_raw_price_fields_are_rejected_directly(
    tmp_path: Path,
) -> None:
    pd.DataFrame(
        [
            {
                "date": date,
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
                "qfq_ratio": 1.0,
                "is_st": False,
                "is_delisting": False,
            }
            for date in ("2024-01-02", "2024-01-03")
        ]
    ).to_parquet(tmp_path / "daily.parquet", index=False)
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "600000.SH": [1.0], "cash": [0.0]}
    )

    with pytest.raises(ValueError, match="raw_open.*raw_prev_close"):
        run_target_weight_backtest(
            weights,
            parquet_path=tmp_path,
            start="2024-01-02",
            end="2024-01-03",
        )


@pytest.mark.parametrize(
    ("decision_date", "buy_date", "sell_date", "expected_sell_count"),
    [
        ("2020-08-19", "2020-08-20", "2020-08-21", 0),
        ("2020-08-20", "2020-08-21", "2020-08-24", 1),
    ],
)
def test_chinext_limit_down_sell_respects_reform_date(
    tmp_path: Path,
    decision_date: str,
    buy_date: str,
    sell_date: str,
    expected_sell_count: int,
) -> None:
    _write_market(
        tmp_path / "sz300001.parquet",
        [
            {
                "date": decision_date,
                "code": "sz300001",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
            {
                "date": buy_date,
                "code": "sz300001",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
            {
                "date": sell_date,
                "code": "sz300001",
                "open": 9.0,
                "high": 9.0,
                "low": 9.0,
                "close": 9.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
        ],
    )
    weights = pd.DataFrame(
        {
            "date": [decision_date, buy_date],
            "300001.SZ": [1.0, 0.0],
            "cash": [0.0, 1.0],
        }
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start=decision_date,
        end=sell_date,
        capital=100_000.0,
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.0,
        lot_size=0,
    )

    trades = stats["_trades_df"]
    assert int((trades["side"] == "sell").sum()) == expected_sell_count
    assert "main-board ST 5%" in stats["_backtest_debug"][
        "price_limit_rule"
    ]


def test_fractional_mode_applies_slippage_to_execution_price(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": "2024-01-02",
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
            {
                "date": "2024-01-03",
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            },
        ],
    )
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "600000.SH": [0.5], "cash": [0.5]}
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start="2024-01-02",
        end="2024-01-03",
        capital=100_000.0,
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.001,
        lot_size=0,
    )

    trade = stats["_trades_df"].iloc[0]
    assert float(trade["reference_price"]) == pytest.approx(10.0)
    assert float(trade["price"]) == pytest.approx(10.01)
    assert float(trade["shares"]) == pytest.approx(5_000.0)
    assert float(stats["total_slippage"]) == pytest.approx(50.0)
    assert stats["_backtest_debug"]["position_mode"] == "fractional adjusted-price units"


def test_sell_cost_changes_on_2023_08_28_and_old_call_stays_constant(
    tmp_path: Path,
) -> None:
    dates = ("2023-08-23", "2023-08-24", "2023-08-25", "2023-08-28", "2023-08-29")
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": date,
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
            for date in dates
        ],
    )
    weights = pd.DataFrame(
        {
            "date": dates[:4],
            "600000.SH": [1.0, 0.0, 1.0, 0.0],
            "cash": [0.0, 1.0, 0.0, 1.0],
        }
    )

    dated = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[-1],
        buy_cost=0.0003,
        sell_cost=0.0008,
        sell_cost_before_change=0.0013,
        sell_cost_change_date="2023-08-28",
        slippage=0.0,
        lot_size=0,
    )
    dated_sells = dated["_trades_df"].loc[
        dated["_trades_df"]["side"].eq("sell")
    ]
    assert dated_sells["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2023-08-25",
        "2023-08-29",
    ]
    assert dated_sells["commission_rate"].tolist() == pytest.approx(
        [0.0013, 0.0008]
    )
    assert dated["_backtest_debug"]["transaction_cost_rule"] == {
        "type": "dated",
        "sell_rate_before_change": 0.0013,
        "sell_rate_before_end": "2023-08-27",
        "sell_rate_from_change": 0.0008,
        "sell_rate_change_date": "2023-08-28",
        "description": "2023-08-27及以前卖出费 0.001300；2023-08-28起卖出费 0.000800",
        "buy_rate": 0.0003,
        "slippage_rate_each_side": 0.0,
    }

    constant = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[-1],
        buy_cost=0.0,
        sell_cost=0.004,
        slippage=0.0,
        lot_size=0,
    )
    constant_sells = constant["_trades_df"].loc[
        constant["_trades_df"]["side"].eq("sell")
    ]
    assert constant_sells["commission_rate"].tolist() == pytest.approx(
        [0.004, 0.004]
    )
    assert constant["_backtest_debug"]["transaction_cost_rule"]["type"] == "constant"


def test_sell_executed_on_2023_08_28_uses_reduced_cost_rate(
    tmp_path: Path,
) -> None:
    dates = ("2023-08-24", "2023-08-25", "2023-08-28")
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": date,
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
            for date in dates
        ],
    )
    weights = pd.DataFrame(
        {
            "date": dates[:2],
            "600000.SH": [1.0, 0.0],
            "cash": [0.0, 1.0],
        }
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[-1],
        buy_cost=0.0003,
        sell_cost=0.0008,
        sell_cost_before_change=0.0013,
        sell_cost_change_date="2023-08-28",
        slippage=0.0,
        lot_size=0,
    )

    sell = stats["_trades_df"].loc[stats["_trades_df"]["side"].eq("sell")].iloc[0]
    assert sell["date"] == pd.Timestamp("2023-08-28")
    assert sell["commission_rate"] == pytest.approx(0.0008)


def test_delisting_flag_blocks_new_buy_but_allows_existing_position_to_sell(
    tmp_path: Path,
) -> None:
    dates = ("2024-01-02", "2024-01-03", "2024-01-04")
    rows = [
        {
            "date": date,
            "code": "sh600000",
            "open": 10.0,
            "high": 10.0,
            "low": 10.0,
            "close": 10.0,
            "volume": 1_000_000.0,
            "prev_close": 10.0,
            "is_delisting": is_delisting,
        }
        for date, is_delisting in zip(dates, (False, False, True), strict=True)
    ]
    _write_market(tmp_path / "sh600000.parquet", rows)
    weights = pd.DataFrame(
        {
            "date": dates[:2],
            "600000.SH": [1.0, 0.0],
            "cash": [0.0, 1.0],
        }
    )

    held_then_sold = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[-1],
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.0,
        lot_size=0,
    )
    assert held_then_sold["_trades_df"]["side"].tolist() == ["buy", "sell"]

    blocked_rows = [dict(row) for row in rows]
    blocked_rows[1]["is_delisting"] = True
    _write_market(tmp_path / "sh600000.parquet", blocked_rows)
    blocked = run_target_weight_backtest(
        weights.iloc[:1],
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[1],
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.0,
        lot_size=0,
    )
    assert blocked["total_trade_count"] == 0
    assert "blocks new buys" in blocked["_backtest_debug"]["delisting_entry_rule"]


def test_delisting_outside_limit_sells_at_open_slippage_but_equal_limit_blocks(
    tmp_path: Path,
) -> None:
    dates = ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")
    raw_opens = (10.0, 10.0, 8.0, 9.0)
    delisting = (False, False, True, True)
    qfq_ratio = 0.5
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": date,
                "code": "sh600000",
                "open": raw_open * qfq_ratio,
                "high": raw_open * qfq_ratio,
                "low": raw_open * qfq_ratio,
                "close": raw_open * qfq_ratio,
                "volume": 1_000_000.0,
                "prev_close": 10.0 * qfq_ratio,
                "qfq_ratio": qfq_ratio,
                "is_delisting": flag,
            }
            for date, raw_open, flag in zip(
                dates, raw_opens, delisting, strict=True
            )
        ],
    )

    sold_outside = run_target_weight_backtest(
        pd.DataFrame(
            {
                "date": dates[:2],
                "600000.SH": [1.0, 0.0],
                "cash": [0.0, 1.0],
            }
        ),
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[2],
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.01,
        lot_size=0,
    )
    outside_sell = sold_outside["_trades_df"].loc[
        sold_outside["_trades_df"]["side"].eq("sell")
    ].iloc[0]
    assert outside_sell["date"] == pd.Timestamp("2024-01-04")
    assert outside_sell["reference_price"] == pytest.approx(4.0)
    assert outside_sell["price"] == pytest.approx(3.96)

    blocked_at_equal_limit = run_target_weight_backtest(
        pd.DataFrame(
            {
                "date": [dates[0], dates[2]],
                "600000.SH": [1.0, 0.0],
                "cash": [0.0, 1.0],
            }
        ),
        parquet_path=tmp_path,
        start=dates[0],
        end=dates[3],
        buy_cost=0.0,
        sell_cost=0.0,
        slippage=0.01,
        lot_size=0,
    )
    assert blocked_at_equal_limit["_trades_df"]["side"].tolist() == ["buy"]


def test_historical_membership_is_checked_on_execution_date(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": date,
                "code": "sh600000",
                "open": 10.0,
                "high": 10.0,
                "low": 10.0,
                "close": 10.0,
                "volume": 1_000_000.0,
                "prev_close": 10.0,
            }
            for date in ("2024-01-02", "2024-01-03")
        ],
    )
    weights = pd.DataFrame(
        {"date": ["2024-01-02"], "600000.SH": [1.0], "cash": [0.0]}
    )
    membership = pd.DataFrame(
        {
            "code": ["600000.SH"],
            "start_date": ["2023-01-01"],
            "end_date": ["2024-01-02"],
        }
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start="2024-01-02",
        end="2024-01-03",
        membership_df=membership,
    )

    assert stats["total_trade_count"] == 0
    assert stats["_backtest_debug"]["historical_membership_filter"] is True


def test_fixed_position_is_kept_after_membership_ends_until_planned_exit(tmp_path: Path) -> None:
    _write_market(
        tmp_path / "sh600000.parquet",
        [
            {
                "date": date,
                "code": "sh600000",
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 1_000_000.0,
                "prev_close": previous_close,
            }
            for date, price, previous_close in (
                ("2024-01-02", 10.0, 10.0),
                ("2024-01-03", 9.0, 10.0),
                ("2024-01-04", 9.0, 9.0),
                ("2024-01-05", 9.0, 9.0),
            )
        ],
    )
    weights = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "600000.SH": [0.5, 0.5, 0.5, 0.0],
            "cash": [0.5, 0.5, 0.5, 1.0],
        }
    )
    membership = pd.DataFrame(
        {
            "code": ["600000.SH"],
            "start_date": ["2023-01-01"],
            "end_date": ["2024-01-02"],
        }
    )

    stats = run_target_weight_backtest(
        weights,
        parquet_path=tmp_path,
        start="2024-01-02",
        end="2024-01-05",
        buy_cost=0.0,
        sell_cost=0.0,
        lot_size=0,
        membership_df=membership,
    )

    trades = stats["_trades_df"]
    assert trades["side"].tolist() == ["buy", "sell"]
    assert trades["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-02",
        "2024-01-05",
    ]
    assert trades["reason"].tolist() == ["rebalance", "rebalance"]
    assert stats["_backtest_debug"]["forced_membership_exit_count"] == 0
    assert stats["_backtest_debug"]["blocked_membership_buy_count"] >= 1


def test_weight_rows_must_add_up_to_one(tmp_path: Path) -> None:
    weights = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "600000.SH": [0.7],
            "cash": [0.2],
        }
    )

    with pytest.raises(ValueError, match="必须等于 1"):
        run_target_weight_backtest(weights, parquet_path=tmp_path)
