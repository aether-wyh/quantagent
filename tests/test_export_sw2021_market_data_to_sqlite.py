from __future__ import annotations

import sqlite3
import sys
from tempfile import TemporaryDirectory
from pathlib import Path
from types import ModuleType
from unittest import TestCase
from importlib.util import module_from_spec, spec_from_file_location


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "export_sw2021_market_data_to_sqlite.py"

spec = spec_from_file_location("export_sw2021_market_data_to_sqlite", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


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


class ExportSw2021MarketDataToSQLiteTest(TestCase):
    def test_export_sw2021_market_data_replaces_existing_sqlite_file(self) -> None:
        pd = __import__("pandas")

        fake_session = _FakeSession(
            {
                "sw2021_index_classify_l1": pd.DataFrame(
                    [
                        {
                            "index_code": "801010.SW",
                            "industry_name": "农林牧渔",
                            "level": 1,
                            "industry_code": "801010",
                            "is_pub": "Y",
                            "parent_code": "801000",
                            "src": "SW",
                        }
                    ]
                ),
                "sw2021_index_classify_l2": pd.DataFrame(
                    [
                        {
                            "index_code": "801020.SW",
                            "industry_name": "采掘",
                            "level": 2,
                            "industry_code": "801020",
                            "is_pub": "Y",
                            "parent_code": "801000",
                            "src": "SW",
                        }
                    ]
                ),
                "sw2021_index_classify_l3": pd.DataFrame(
                    [
                        {
                            "index_code": "801030.SW",
                            "industry_name": "化工",
                            "level": 3,
                            "industry_code": "801030",
                            "is_pub": "Y",
                            "parent_code": "801000",
                            "src": "SW",
                        }
                    ]
                ),
                "sw2021_l1_members": pd.DataFrame(
                    [
                        {
                            "l1_code": "801010",
                            "l1_name": "农林牧渔",
                            "l2_code": "801011",
                            "l2_name": "种植业",
                            "l3_code": "8010111",
                            "l3_name": "粮食种植",
                            "stock_code": "000001",
                            "ts_code": "000001.SZ",
                            "name": "平安银行",
                            "in_date": pd.Timestamp("2024-01-02 00:00:00"),
                            "out_date": None,
                            "is_new": "Y",
                        }
                    ]
                ),
            }
        )

        with TemporaryDirectory() as tmp_dir:
            sqlite_path = Path(tmp_dir) / "market_data.db"
            with sqlite3.connect(sqlite_path) as conn:
                conn.execute("CREATE TABLE stale_table (value INTEGER)")
                conn.execute("INSERT INTO stale_table(value) VALUES (1)")

            summaries = module.export_sw2021_market_data(
                fake_session,
                source_db="dfs://market_data",
                target_sqlite=str(sqlite_path),
                replace_existing=True,
            )

            self.assertEqual(len(summaries), 4)

            with sqlite3.connect(sqlite_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "select name from sqlite_master where type='table' order by name"
                    ).fetchall()
                }
                tables.discard("sqlite_sequence")
                self.assertEqual(
                    tables,
                    {
                        "sw2021_index_classify_l1",
                        "sw2021_index_classify_l2",
                        "sw2021_index_classify_l3",
                        "sw2021_l1_members",
                    },
                )

                row = conn.execute(
                    "select index_code, industry_name, level, industry_code, is_pub, parent_code, src from sw2021_index_classify_l1"
                ).fetchone()
                self.assertEqual(row, ("801010.SW", "农林牧渔", "1", "801010", "Y", "801000", "SW"))

                member_row = conn.execute(
                    "select l1_code, l1_name, l2_code, l2_name, l3_code, l3_name, stock_code, ts_code, name, in_date, out_date, is_new from sw2021_l1_members"
                ).fetchone()
                self.assertEqual(
                    member_row,
                    (
                        "801010",
                        "农林牧渔",
                        "801011",
                        "种植业",
                        "8010111",
                        "粮食种植",
                        "000001",
                        "000001.SZ",
                        "平安银行",
                        "2024-01-02",
                        None,
                        "Y",
                    ),
                )

            self.assertTrue(all(summary.rows == 1 for summary in summaries))
            self.assertFalse(any("stale_table" in summary.source_table for summary in summaries))