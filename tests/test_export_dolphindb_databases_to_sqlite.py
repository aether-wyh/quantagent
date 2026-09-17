from __future__ import annotations

import sqlite3
import sys
from tempfile import TemporaryDirectory
from pathlib import Path
from types import ModuleType
from unittest import TestCase
from importlib.util import module_from_spec, spec_from_file_location

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "export_dolphindb_databases_to_sqlite.py"

spec = spec_from_file_location("export_dolphindb_databases_to_sqlite", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

if "openai" not in sys.modules:
    openai_stub = ModuleType("openai")

    class _DummyOpenAI:  # pragma: no cover - test bootstrap stub
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = ModuleType("chat")

    setattr(openai_stub, "OpenAI", _DummyOpenAI)
    sys.modules["openai"] = openai_stub


class _FakeSession:
    def __init__(self, frames: dict[str, object]) -> None:
        self.frames = frames
        self.queries: list[str] = []

    def run(self, script: str):
        self.queries.append(script)
        for key, frame in self.frames.items():
            if key in script:
                return frame
        raise AssertionError(f"unexpected DolphinDB script: {script}")

    def close(self) -> None:
        return None


class ExportDolphinDBDatabasesToSQLiteTest(TestCase):
    def test_export_all_replaces_existing_sqlite_files(self) -> None:
        pd = __import__("pandas")

        market_stock_df = pd.DataFrame(
            [
                {
                    "code": "000001.SZSE",
                    "trade_date": "2024-01-02",
                    "open": 1.0,
                    "high": 2.0,
                    "low": 0.5,
                    "close": 1.5,
                    "volume": 100.0,
                }
            ]
        )
        market_futures_df = pd.DataFrame(
            [
                {
                    "code": "IF2401",
                    "trade_date": "2024-01-02",
                    "open": 3.0,
                    "high": 4.0,
                    "low": 2.5,
                    "close": 3.5,
                    "volume": 12.0,
                    "open_interest": 88.0,
                }
            ]
        )
        vnpy_stock_df = pd.DataFrame(
            [
                {
                    "symbol": "000001",
                    "exchange": "SZSE",
                    "datetime": pd.Timestamp("2024-01-02 09:30:00"),
                    "interval": "1d",
                    "volume": 100.0,
                    "turnover": 150.0,
                    "open_interest": 0.0,
                    "open_price": 1.0,
                    "high_price": 2.0,
                    "low_price": 0.5,
                    "close_price": 1.5,
                }
            ]
        )
        vnpy_futures_df = pd.DataFrame(
            [
                {
                    "symbol": "IF2401",
                    "exchange": "CFFEX",
                    "datetime": pd.Timestamp("2024-01-02 15:00:00"),
                    "interval": "1d",
                    "volume": 12.0,
                    "turnover": 42.0,
                    "open_interest": 88.0,
                    "open_price": 3.0,
                    "high_price": 4.0,
                    "low_price": 2.5,
                    "close_price": 3.5,
                }
            ]
        )

        fake_session = _FakeSession(
            {
                "stock_kline_daily_qfq": market_stock_df,
                "futures_kline_daily_hfq": market_futures_df,
                "vnpy_stock_daily_qfq": vnpy_stock_df,
                "vnpy_futures_daily_hfq": vnpy_futures_df,
            }
        )

        with TemporaryDirectory() as tmp_dir:
            market_sqlite = Path(tmp_dir) / "market_data.db"
            vnpy_sqlite = Path(tmp_dir) / "vnpy_bar.sqlite3"

            with sqlite3.connect(market_sqlite) as conn:
                conn.execute("CREATE TABLE stale_table (value INTEGER)")
                conn.execute("INSERT INTO stale_table(value) VALUES (1)")
            with sqlite3.connect(vnpy_sqlite) as conn:
                conn.execute("CREATE TABLE stale_table (value INTEGER)")
                conn.execute("INSERT INTO stale_table(value) VALUES (1)")

            summaries = module.export_all(
                fake_session,
                market_src_db="dfs://market_data",
                vnpy_src_db="dfs://vnpy_bar_db",
                market_sqlite=str(market_sqlite),
                vnpy_sqlite=str(vnpy_sqlite),
                replace_existing=True,
                start_date=None,
                end_date=None,
            )

            self.assertEqual(len(summaries), 4)

            with sqlite3.connect(market_sqlite) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "select name from sqlite_master where type='table' order by name"
                    ).fetchall()
                }
                tables.discard("sqlite_sequence")
                self.assertEqual(tables, {"futures_kline_daily_hfq", "stock_kline_daily_qfq"})
                stock_row = conn.execute(
                    "select code, trade_date, open, high, low, close, volume from stock_kline_daily_qfq"
                ).fetchone()
                futures_row = conn.execute(
                    "select code, trade_date, open, high, low, close, volume, open_interest from futures_kline_daily_hfq"
                ).fetchone()
                self.assertEqual(stock_row, ("000001.SZSE", "2024-01-02", 1.0, 2.0, 0.5, 1.5, 100.0))
                self.assertEqual(futures_row, ("IF2401", "2024-01-02", 3.0, 4.0, 2.5, 3.5, 12.0, 88.0))

            with sqlite3.connect(vnpy_sqlite) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "select name from sqlite_master where type='table' order by name"
                    ).fetchall()
                }
                tables.discard("sqlite_sequence")
                self.assertEqual(tables, {"vnpy_futures_daily_hfq", "vnpy_stock_daily_qfq"})
                stock_row = conn.execute(
                    "select symbol, exchange, datetime, interval, volume, turnover, open_interest, open_price, high_price, low_price, close_price, gateway_name from vnpy_stock_daily_qfq"
                ).fetchone()
                futures_row = conn.execute(
                    "select symbol, exchange, datetime, interval, volume, turnover, open_interest, open_price, high_price, low_price, close_price, gateway_name from vnpy_futures_daily_hfq"
                ).fetchone()
                self.assertEqual(
                    stock_row,
                    ("000001", "SZSE", "2024-01-02 09:30:00", "1d", 100.0, 150.0, 0.0, 1.0, 2.0, 0.5, 1.5, "DB"),
                )
                self.assertEqual(
                    futures_row,
                    ("IF2401", "CFFEX", "2024-01-02 15:00:00", "1d", 12.0, 42.0, 88.0, 3.0, 4.0, 2.5, 3.5, "DB"),
                )

            self.assertTrue(all(summary.rows == 1 for summary in summaries))
            self.assertFalse(any("stale_table" in summary.source_table for summary in summaries))
