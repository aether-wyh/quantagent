from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "deduplicate_market_data_in_dolphindb.py"

spec = spec_from_file_location("deduplicate_market_data_in_dolphindb", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DeduplicateMarketDataInDolphinDBTest(TestCase):
    def test_build_dedup_script_groups_by_code_and_trade_date(self) -> None:
        script = module.build_dedup_script(
            src_db="dfs://market_data",
            src_table="stock_kline_daily_qfq",
            dst_db="dfs://market_data",
            dst_table="stock_kline_daily_qfq",
            replace_original=True,
        )

        self.assertIn("group by code, trade_date", script)
        self.assertIn("last(open) as open", script)
        self.assertIn("last(close) as close", script)
        self.assertIn("dst.append!(deduped)", script)
        self.assertIn("delete from dst;", script)

    def test_build_init_script_creates_partitioned_table(self) -> None:
        script = module.build_init_script(
            dst_db="dfs://market_data",
            dst_table="stock_kline_daily_qfq_dedup",
            replace_existing=True,
            truncate_existing=False,
        )

        self.assertIn("createPartitionedTable", script)
        self.assertIn("dropTable(db, \"stock_kline_daily_qfq_dedup\")", script)

    def test_build_init_script_keeps_table_when_truncating_existing(self) -> None:
        script = module.build_init_script(
            dst_db="dfs://market_data",
            dst_table="stock_kline_daily_qfq",
            replace_existing=True,
            truncate_existing=True,
        )

        self.assertNotIn("dropTable(db, \"stock_kline_daily_qfq\")", script)
