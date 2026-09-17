from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd


STRATEGY_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = STRATEGY_DIR.parent
PROJECT_ROOT = WORKSPACE_ROOT / "QuantaAgents"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from quanta_agents.local_parquet_backtest import run_target_weight_backtest


TRAIN_START = pd.Timestamp("2020-01-01")
TRAIN_END = pd.Timestamp("2023-12-31")
TEST_START = pd.Timestamp("2024-01-01")
TEST_END = pd.Timestamp("2025-12-31")
INITIAL_CAPITAL = 1_000_000.0
BUY_COST = 0.0003
SELL_COST = 0.0008
SLIPPAGE = 0.001
RISK_FREE_RATE = 0.02


def _default_parquet_glob() -> str:
    finance_root = WORKSPACE_ROOT.parent
    candidates = sorted(
        finance_root.glob("*/february_march_results/cache/daily_by_stock/*.parquet")
    )
    if not candidates:
        raise FileNotFoundError("没有找到项目配置的本地日线 Parquet")
    return str(candidates[0].parent / "*.parquet")


def _load_membership(path: Path) -> pd.DataFrame:
    membership = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=["code", "start_date", "end_date"],
        dtype={"code": "string"},
    )
    membership["code"] = membership["code"].str.strip().str.lower()
    membership["start_date"] = pd.to_datetime(
        membership["start_date"], errors="coerce"
    ).dt.normalize()
    membership["end_date"] = pd.to_datetime(
        membership["end_date"], errors="coerce"
    ).dt.normalize()
    membership = membership.dropna(subset=["code", "start_date", "end_date"])
    membership = membership[
        membership["code"].str.match(r"^(sh|sz)\d{6}$", na=False)
    ]
    return membership.drop_duplicates().reset_index(drop=True)


def _escaped_parquet_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _load_period_union_data(
    parquet_glob: str,
    membership: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[pd.DataFrame, int]:
    """按项目现有做法，读取期间出现过的全部成分股及其整段行情。"""

    period_codes = membership.loc[
        (membership["end_date"] >= start) & (membership["start_date"] <= end),
        ["code"],
    ].drop_duplicates()
    if period_codes.empty:
        raise ValueError(f"{start.date()} 至 {end.date()} 没有沪深300成分记录")

    connection = duckdb.connect(":memory:")
    connection.register("period_codes", period_codes)
    escaped_path = _escaped_parquet_path(parquet_glob)
    query = f"""
        SELECT
            lower(CAST(source.code AS VARCHAR)) AS code,
            CAST(source.date AS DATE) AS trade_date,
            CAST(source.open AS DOUBLE) AS open,
            CAST(source.high AS DOUBLE) AS high,
            CAST(source.low AS DOUBLE) AS low,
            CAST(source.close AS DOUBLE) AS close,
            CAST(source.volume AS DOUBLE) AS volume,
            CAST(source.prev_close AS DOUBLE) AS prev_close
        FROM read_parquet('{escaped_path}', union_by_name=true) AS source
        INNER JOIN period_codes AS members
            ON lower(CAST(source.code AS VARCHAR)) = members.code
        WHERE CAST(source.date AS DATE) >= ?
          AND CAST(source.date AS DATE) <= ?
        ORDER BY code, trade_date
    """
    try:
        data = connection.execute(query, [start.date(), end.date()]).fetchdf()
    finally:
        connection.close()

    if data.empty:
        raise ValueError(f"{start.date()} 至 {end.date()} 没有可用行情")
    data["trade_date"] = pd.to_datetime(data["trade_date"]).dt.normalize()
    data = data.drop_duplicates(subset=["code", "trade_date"], keep="last")
    data = data.sort_values(["code", "trade_date"]).reset_index(drop=True)
    return data, int(period_codes["code"].nunique())


def _load_active_member_benchmark(
    parquet_glob: str,
    membership: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """计算每日历史成分股等权参考收益，不扣费用。"""

    active_membership = membership.loc[
        (membership["end_date"] >= start) & (membership["start_date"] <= end),
        ["code", "start_date", "end_date"],
    ].copy()
    connection = duckdb.connect(":memory:")
    connection.register("active_membership", active_membership)
    escaped_path = _escaped_parquet_path(parquet_glob)
    query = f"""
        SELECT
            CAST(source.date AS DATE) AS trade_date,
            lower(CAST(source.code AS VARCHAR)) AS code,
            CAST(source.close AS DOUBLE) AS close,
            CAST(source.prev_close AS DOUBLE) AS prev_close
        FROM read_parquet('{escaped_path}', union_by_name=true) AS source
        INNER JOIN active_membership AS members
            ON lower(CAST(source.code AS VARCHAR)) = members.code
           AND CAST(source.date AS DATE) >= CAST(members.start_date AS DATE)
           AND CAST(source.date AS DATE) <= CAST(members.end_date AS DATE)
        WHERE CAST(source.date AS DATE) >= ?
          AND CAST(source.date AS DATE) <= ?
        ORDER BY trade_date, code
    """
    try:
        bars = connection.execute(query, [start.date(), end.date()]).fetchdf()
    finally:
        connection.close()

    bars["trade_date"] = pd.to_datetime(bars["trade_date"]).dt.normalize()
    bars = bars.drop_duplicates(subset=["trade_date", "code"], keep="last")
    valid = (
        np.isfinite(bars["close"])
        & np.isfinite(bars["prev_close"])
        & (bars["close"] > 0)
        & (bars["prev_close"] > 0)
    )
    bars = bars.loc[valid].copy()
    bars["return"] = bars["close"] / bars["prev_close"] - 1.0
    daily = (
        bars.groupby("trade_date")
        .agg(return_rate=("return", "mean"), member_count=("code", "nunique"))
        .reset_index()
        .sort_values("trade_date")
    )
    daily["balance"] = INITIAL_CAPITAL * (1.0 + daily["return_rate"]).cumprod()
    return daily


def _run_strategy_source(
    source_path: Path,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
) -> pd.DataFrame:
    # 旧代码把输入键写成 hfq；这里按其 JSON 指定的数据来源装入 qfq 数据。
    namespace: dict[str, Any] = {
        "train_data_bundle": {"stock_kline_daily_hfq": train_data},
        "validate_data_bundle": {"stock_kline_daily_hfq": test_data},
    }
    source = source_path.read_text(encoding="utf-8")
    exec(compile(source, str(source_path), "exec"), namespace)
    weights = namespace.get("output_weights_df")
    if not isinstance(weights, pd.DataFrame) or weights.empty:
        raise RuntimeError(f"{source_path.name} 没有生成有效权重")
    return weights.copy()


def _shift_weight_dates_for_same_day_diagnostic(
    weights: pd.DataFrame,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
) -> pd.DataFrame:
    """仅用于比较：把 D 日信号提前到 D 日开盘执行。"""

    if "trade_date" not in weights.columns:
        raise ValueError("目标权重缺少 trade_date")
    all_dates = pd.DatetimeIndex(
        pd.concat([train_data["trade_date"], test_data["trade_date"]])
        .drop_duplicates()
        .sort_values()
    )
    previous_date = pd.Series(all_dates[:-1], index=all_dates[1:])
    shifted = weights.copy()
    target_dates = pd.to_datetime(shifted["trade_date"]).dt.normalize()
    shifted_dates = target_dates.map(previous_date)
    if shifted_dates.isna().any():
        missing = target_dates.loc[shifted_dates.isna()].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"这些目标日期缺少前一交易日: {missing[:5]}")
    shifted["trade_date"] = shifted_dates.to_numpy()
    return shifted


def _metrics_from_balance_and_returns(
    balance: pd.Series,
    returns: pd.Series,
    starting_balance: float,
) -> dict[str, float]:
    balance = pd.to_numeric(balance, errors="coerce").dropna()
    returns = pd.to_numeric(returns, errors="coerce").dropna()
    if balance.empty:
        return {}
    periods = max(1, len(balance))
    total_return = float(balance.iloc[-1] / starting_balance - 1.0)
    annual_return = float((balance.iloc[-1] / starting_balance) ** (252.0 / periods) - 1.0)
    daily_rf = (1.0 + RISK_FREE_RATE) ** (1.0 / 252.0) - 1.0
    std = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
    sharpe = (
        float((returns.mean() - daily_rf) / std * math.sqrt(252.0))
        if std > 0
        else 0.0
    )
    balance_with_start = pd.concat(
        [pd.Series([starting_balance], dtype="float64"), balance.reset_index(drop=True)]
    )
    drawdown = balance_with_start / balance_with_start.cummax() - 1.0
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "sharpe_ratio": sharpe,
        "max_ddpercent": float(drawdown.min()),
    }


def _yearly_metrics(daily: pd.DataFrame) -> dict[str, dict[str, float]]:
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    results: dict[str, dict[str, float]] = {}
    previous_balance = INITIAL_CAPITAL
    for year, group in frame.groupby(frame["date"].dt.year, sort=True):
        group = group.sort_values("date")
        metrics = _metrics_from_balance_and_returns(
            group["balance"], group["return"], previous_balance
        )
        metrics["trade_count"] = int(group["trade_count"].sum())
        metrics["commission"] = float(group["commission"].sum())
        metrics["slippage"] = float(group["slippage"].sum())
        results[str(year)] = metrics
        previous_balance = float(group["balance"].iloc[-1])
    return results


def _benchmark_metrics(daily: pd.DataFrame) -> dict[str, Any]:
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["trade_date"]).dt.normalize()
    frame["return"] = frame["return_rate"]
    metrics = _metrics_from_balance_and_returns(
        frame["balance"], frame["return"], INITIAL_CAPITAL
    )
    yearly: dict[str, dict[str, float]] = {}
    previous_balance = INITIAL_CAPITAL
    for year, group in frame.groupby(frame["date"].dt.year, sort=True):
        group = group.sort_values("date")
        yearly[str(year)] = _metrics_from_balance_and_returns(
            group["balance"], group["return"], previous_balance
        )
        previous_balance = float(group["balance"].iloc[-1])
    metrics["yearly"] = yearly
    metrics["average_member_count"] = float(frame["member_count"].mean())
    return metrics


def _public_backtest_summary(stats: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "capital",
        "end_balance",
        "total_return",
        "annual_return",
        "annual_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "max_ddpercent",
        "total_trade_count",
        "total_commission",
        "total_slippage",
        "win_rate",
        "profit_loss_ratio",
    ]
    result = {key: stats.get(key) for key in keys}
    result["yearly"] = _yearly_metrics(stats["_daily_df"])
    daily = stats["_daily_df"]
    result["average_invested_ratio"] = float(
        (daily["position_value"] / daily["balance"]).replace([np.inf, -np.inf], np.nan).mean()
    )
    return result


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    raise TypeError(f"无法写入 JSON: {type(value)!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="重跑文件夹中的两套日线策略")
    parser.add_argument("--parquet", default=None, help="日线 Parquet 路径或通配符")
    parser.add_argument(
        "--membership",
        default="D:/qlib_data/qlib_bin/instruments/csi300.txt",
        help="沪深300历史成分文件",
    )
    parser.add_argument(
        "--output-dir",
        default=str(STRATEGY_DIR / "backtest_outputs"),
        help="结果目录",
    )
    args = parser.parse_args()

    parquet_glob = str(args.parquet or _default_parquet_glob())
    membership_path = Path(args.membership).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("读取沪深300历史名单……", flush=True)
    membership = _load_membership(membership_path)
    print("读取2020—2023年前期资料……", flush=True)
    train_data, train_member_union = _load_period_union_data(
        parquet_glob, membership, TRAIN_START, TRAIN_END
    )
    print("读取2024—2025检验资料……", flush=True)
    test_data, test_member_union = _load_period_union_data(
        parquet_glob, membership, TEST_START, TEST_END
    )
    print("计算历史成分股等权参考收益……", flush=True)
    benchmark_daily = _load_active_member_benchmark(
        parquet_glob, membership, TEST_START, TEST_END
    )
    benchmark_daily.to_csv(output_dir / "benchmark_daily.csv", index=False, encoding="utf-8-sig")

    strategy_files = {
        "rolling": STRATEGY_DIR / "rolling" / "step_01_20260726_084204_358339.py",
        "indicator": STRATEGY_DIR / "indicator" / "step_03_20260725_074129_055127.py",
    }
    strategy_results: dict[str, Any] = {}
    for name, source_path in strategy_files.items():
        print(f"生成 {name} 每日目标持仓……", flush=True)
        raw_weights = _run_strategy_source(source_path, train_data, test_data)
        raw_weights.to_parquet(output_dir / f"{name}_target_weights.parquet", index=False)
        same_day_weights = _shift_weight_dates_for_same_day_diagnostic(
            raw_weights, train_data, test_data
        )

        print(f"回测 {name}（次日开盘执行，扣费用和成交价偏差）……", flush=True)
        net_stats = run_target_weight_backtest(
            raw_weights,
            parquet_path=parquet_glob,
            start=TEST_START,
            end=TEST_END,
            capital=INITIAL_CAPITAL,
            buy_cost=BUY_COST,
            sell_cost=SELL_COST,
            slippage=SLIPPAGE,
            lot_size=0,
            membership_df=membership,
            risk_free_rate=RISK_FREE_RATE,
            datetime_column="trade_date",
        )
        net_stats["_daily_df"].to_csv(
            output_dir / f"{name}_daily_net.csv", index=False, encoding="utf-8-sig"
        )
        net_stats["_trades_df"].to_csv(
            output_dir / f"{name}_trades_net.csv", index=False, encoding="utf-8-sig"
        )

        print(f"回测 {name}（次日开盘执行，不扣费用）……", flush=True)
        gross_stats = run_target_weight_backtest(
            raw_weights,
            parquet_path=parquet_glob,
            start=TEST_START,
            end=TEST_END,
            capital=INITIAL_CAPITAL,
            buy_cost=0.0,
            sell_cost=0.0,
            slippage=0.0,
            lot_size=0,
            membership_df=membership,
            risk_free_rate=RISK_FREE_RATE,
            datetime_column="trade_date",
        )

        print(f"回测 {name}（错误的当日开盘执行，仅作比较）……", flush=True)
        same_day_stats = run_target_weight_backtest(
            same_day_weights,
            parquet_path=parquet_glob,
            start=TEST_START,
            end=TEST_END,
            capital=INITIAL_CAPITAL,
            buy_cost=BUY_COST,
            sell_cost=SELL_COST,
            slippage=SLIPPAGE,
            lot_size=0,
            membership_df=membership,
            risk_free_rate=RISK_FREE_RATE,
            datetime_column="trade_date",
        )

        raw_dates = pd.to_datetime(raw_weights["trade_date"])
        stock_columns = [
            column for column in raw_weights.columns if column not in {"trade_date", "cash"}
        ]
        stock_weight_sum = raw_weights[stock_columns].sum(axis=1)
        strategy_results[name] = {
            "source_file": str(source_path),
            "target_weight_rows": int(len(raw_weights)),
            "target_start": raw_dates.min(),
            "target_end": raw_dates.max(),
            "stock_column_count": int(len(stock_columns)),
            "average_target_stock_weight": float(stock_weight_sum.mean()),
            "max_target_stock_weight": float(stock_weight_sum.max()),
            "net": _public_backtest_summary(net_stats),
            "gross": _public_backtest_summary(gross_stats),
            "same_day_execution_diagnostic": _public_backtest_summary(same_day_stats),
        }

    summary = {
        "run_type": "folder_strategy_actual_code_on_local_qfq",
        "data": {
            "parquet_glob": parquet_glob,
            "membership_file": str(membership_path),
            "price_adjustment": "qfq",
            "train_start": TRAIN_START,
            "train_end": TRAIN_END,
            "test_start": TEST_START,
            "test_end": TEST_END,
            "train_rows": int(len(train_data)),
            "test_rows": int(len(test_data)),
            "train_member_union_count": train_member_union,
            "test_member_union_count": test_member_union,
        },
        "settings": {
            "capital": INITIAL_CAPITAL,
            "buy_cost": BUY_COST,
            "sell_cost": SELL_COST,
            "slippage_each_side": SLIPPAGE,
            "lot_size": 0,
            "risk_free_rate": RISK_FREE_RATE,
            "target_date_handling": "DataFrame 的 D 日信号在下一个交易日开盘执行，不提前日期",
            "signal_universe_handling": "按项目现有读取方式使用测试期间成员并集；成交时按历史成分资格检查",
        },
        "known_limits": [
            "原代码要求 stock_kline_daily_hfq，但文件 JSON 指定 vnpy_stock_daily_qfq；本次按 JSON 使用前复权数据并以内存别名交给旧代码",
            "原策略算信号时没有逐日排除尚未加入或已经调出的股票，成交时才按历史成分资格排除",
            "本地日线截至2025-12-31，无法覆盖文件声称的2026-07-23",
            "rolling 内部回撤判断仍沿用其不完整的开盘到收盘净值算法",
            "indicator 的买入价、持有天数和部分风险规则仍按原代码执行",
        ],
        "benchmark": _benchmark_metrics(benchmark_daily),
        "strategies": strategy_results,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    print(f"完成：{summary_path}", flush=True)


if __name__ == "__main__":
    main()
