from __future__ import annotations

import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "openai" not in sys.modules:
    openai_stub = ModuleType("openai")

    class _DummyOpenAI:  # pragma: no cover - test bootstrap stub
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda *a, **k: None))

    setattr(openai_stub, "OpenAI", _DummyOpenAI)
    sys.modules["openai"] = openai_stub

from quanta_agents.semantic import MetadataManager, SemanticLayer
from quanta_agents.semantic.metadata import ParquetConnector, SQLiteConnector


class _FakeSqlConnector:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def execute_query(self, query: str, params: dict[str, object] | None = None) -> pd.DataFrame:
        self.calls.append((query, params))
        if "stock_kline_daily_qfq" in query:
            return pd.DataFrame(
                {
                    "trade_date": ["2024-01-02", "2024-01-02"],
                    "code": ["000001.SZ", "000001.SZ"],
                    "open": [10.0, 10.5],
                    "close": [11.0, 11.5],
                }
            )
        if "bank_rate_data" in query:
            return pd.DataFrame(
                {
                    "trade_date": ["2024-01-02", "2024-01-02"],
                    "3year_rate": [2.8, 2.9],
                    "5year_rate": [3.0, 3.1],
                }
            )
        if "momentum_factor_data" in query:
            return pd.DataFrame(
                {
                    "trade_date": ["2024-01-02"],
                    "000001.SZ": [1.2],
                    "000002.SZ": [0.8],
                }
            )
        if "basic_stock_info" in query:
            return pd.DataFrame(
                {
                    "code": ["000001.SZ"],
                    "name": ["PingAn"],
                }
            )
        return pd.DataFrame()

    def get_table_schema(self, table: str) -> dict[str, object]:
        return {"table": table, "columns": []}


class ParquetConnectorTest(TestCase):
    def test_query_daily_data_converts_codes_and_filters_dates(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            parquet_path = Path(tmp_dir) / "daily.parquet"
            pd.DataFrame(
                {
                    "date": pd.to_datetime(
                        ["2024-01-02", "2024-01-04", "2024-01-02", "2024-01-03"]
                    ),
                    "code": ["sh600000", "sz000001", "sz000001", "sh600000"],
                    "open": [10.0, 20.8, 20.0, 10.6],
                    "high": [10.8, 21.4, 20.8, 11.0],
                    "low": [9.8, 20.5, 19.7, 10.4],
                    "close": [10.5, 21.0, 20.5, 10.8],
                    "volume": [1000.0, 2100.0, 2000.0, 1100.0],
                    "amount": [10_200.0, 43_900.0, 40_400.0, 11_800.0],
                    "float_shares": [1_000_000.0, 2_000_000.0, 2_000_000.0, 1_000_000.0],
                    "total_shares": [1_200_000.0, 2_400_000.0, 2_400_000.0, 1_200_000.0],
                    "raw_prev_close": [9.9, 20.5, 19.8, 10.5],
                    "is_st": [False, True, True, False],
                    "is_delisting": [False, False, False, False],
                    "float_market_cap": [10_000_000.0, 42_000_000.0, 41_000_000.0, 10_800_000.0],
                    "total_market_cap": [12_000_000.0, 50_400_000.0, 49_200_000.0, 12_960_000.0],
                    "qfq_ratio": [1.1, 1.2, 1.2, 1.1],
                    "vwap_qfq": [10.2, 20.9, 20.2, 10.7],
                    "prev_close": [9.9, 20.5, 19.8, 10.5],
                    "gu_1m": [0.1, 0.2, 0.3, 0.4],
                    "gd_1m": [0.4, 0.3, 0.2, 0.1],
                    "rbar_up17": [0.01, 0.02, 0.03, 0.04],
                    "rbar_down17": [-0.01, -0.02, -0.03, -0.04],
                    "r_0931_1000": [0.001, 0.002, 0.003, 0.004],
                    "r_1001_1030": [0.004, 0.003, 0.002, 0.001],
                    "overnight_return": [0.005, -0.002, 0.001, 0.003],
                }
            ).to_parquet(parquet_path, index=False)

            connector = ParquetConnector(str(parquet_path))
            try:
                result = connector.execute_query(
                    """
                    SELECT trade_date, code, open, high, low, close, volume, amount,
                           float_shares, total_shares, raw_prev_close, is_st,
                           is_delisting, float_market_cap, total_market_cap,
                           qfq_ratio, vwap_qfq, prev_close,
                           gu_1m, gd_1m, rbar_up17, rbar_down17, r_0931_1000,
                           r_1001_1030, overnight_return
                    FROM stock_kline_daily_qfq
                    WHERE trade_date BETWEEN :start AND :end
                    ORDER BY trade_date, code
                    """,
                    {"start": "2024-01-02", "end": "2024-01-03"},
                )
            finally:
                connector.conn.close()

        self.assertEqual(result["code"].tolist(), ["000001.SZ", "600000.SH", "600000.SH"])
        self.assertEqual(
            result["trade_date"].dt.strftime("%Y-%m-%d").tolist(),
            ["2024-01-02", "2024-01-02", "2024-01-03"],
        )
        sz_row = result.loc[result["code"] == "000001.SZ"].iloc[0]
        self.assertEqual(float(sz_row["close"]), 20.5)
        self.assertEqual(float(sz_row["amount"]), 40_400.0)
        self.assertEqual(float(sz_row["qfq_ratio"]), 1.2)
        self.assertEqual(float(sz_row["prev_close"]), 19.8)
        self.assertEqual(float(sz_row["raw_prev_close"]), 19.8)
        self.assertTrue(bool(sz_row["is_st"]))
        self.assertFalse(bool(sz_row["is_delisting"]))
        self.assertEqual(float(sz_row["float_market_cap"]), 41_000_000.0)
        self.assertEqual(float(sz_row["total_market_cap"]), 49_200_000.0)
        self.assertEqual(
            [
                float(sz_row[column])
                for column in (
                    "gu_1m",
                    "gd_1m",
                    "rbar_up17",
                    "rbar_down17",
                    "r_0931_1000",
                    "r_1001_1030",
                    "overnight_return",
                )
            ],
            [0.3, 0.2, 0.03, -0.03, 0.003, 0.002, 0.001],
        )

    def test_hs300_uses_membership_valid_on_each_trade_date(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            parquet_path = root / "daily.parquet"
            membership_path = root / "csi300.txt"
            rows: list[dict[str, object]] = []
            for date in pd.to_datetime(["2024-01-02", "2024-01-03"]):
                for code, price in (("sz000001", 10.0), ("sh600000", 20.0)):
                    rows.append(
                        {
                            "date": date,
                            "code": code,
                            "open": price,
                            "high": price,
                            "low": price,
                            "close": price,
                            "volume": 1000.0,
                            "amount": 10_000.0,
                            "float_shares": 1_000_000.0,
                            "total_shares": 1_200_000.0,
                            "raw_prev_close": price,
                            "is_st": False,
                            "is_delisting": False,
                            "float_market_cap": price * 1_000_000.0,
                            "total_market_cap": price * 1_200_000.0,
                            "qfq_ratio": 1.0,
                            "vwap_qfq": price,
                            "prev_close": price,
                            "gu_1m": 0.1,
                            "gd_1m": 0.2,
                            "rbar_up17": 0.01,
                            "rbar_down17": -0.01,
                            "r_0931_1000": 0.001,
                            "r_1001_1030": 0.002,
                            "overnight_return": 0.003,
                        }
                    )
            pd.DataFrame(rows).to_parquet(parquet_path, index=False)
            membership_path.write_text(
                "SZ000001\t2024-01-02\t2024-01-02\n"
                "SH600000\t2024-01-03\t2024-01-03\n"
                "SHT00018\t2024-01-02\t2024-01-03\n",
                encoding="utf-8",
            )
            metadata = MetadataManager(
                {
                    "datasets": [
                        {
                            "name": "stock_kline_daily_qfq",
                            "type": "time_series",
                            "datetime_column": "trade_date",
                            "symbol_column": "code",
                        },
                        {
                            "name": "csi300_membership",
                            "type": "static",
                            "symbol_column": "code",
                        },
                    ],
                    "universes": {"hs300": {"symbols": ["000001.SZ"]}},
                }
            )
            connector = ParquetConnector(
                str(parquet_path),
                csi300_membership_path=str(membership_path),
            )
            layer = SemanticLayer(metadata, default_engine="parquet")
            layer._connectors["parquet"] = connector
            try:
                self.assertEqual(
                    layer.get_universe_list("hs300"),
                    ["000001.SZ", "600000.SH"],
                )
                result = layer.load_time_series_data(
                    "stock_kline_daily_qfq",
                    ["open", "close"],
                    {"start": "2024-01-02", "end": "2024-01-03"},
                    {"type": "named_pool", "value": "hs300"},
                )
            finally:
                connector.conn.close()

        self.assertEqual(
            result["code"].tolist(),
            ["000001.SZ", "600000.SH"],
        )
        self.assertEqual(
            result["trade_date"].dt.strftime("%Y-%m-%d").tolist(),
            ["2024-01-02", "2024-01-03"],
        )


class SemanticLayerRequiredDataTest(TestCase):
    def setUp(self) -> None:
        metadata = {
            "datasets": [
                {
                    "name": "stock_kline_daily_qfq",
                    "type": "time_series",
                    "datetime_column": "trade_date",
                    "symbol_column": "code",
                    "fields": [
                        {"name": "open"},
                        {"name": "close"},
                    ],
                },
                {
                    "name": "momentum_factor_data",
                    "type": "panel",
                    "datetime_column": "trade_date",
                },
                {
                    "name": "bank_rate_data",
                    "type": "auxiliary",
                    "datetime_column": "trade_date",
                    "fields": [
                        {"name": "3year_rate"},
                        {"name": "5year_rate"},
                    ],
                },
                {
                    "name": "basic_stock_info",
                    "type": "static",
                    "fields": [
                        {"name": "code"},
                        {"name": "name"},
                    ],
                },
            ],
            "universes": {
                "hs300": {
                    "symbols": ["000001.SZ", "000002.SZ"],
                }
            },
        }
        self.layer = SemanticLayer(MetadataManager(metadata))
        self.fake_connector = _FakeSqlConnector()
        self.layer._connectors["sqlite"] = self.fake_connector

    def test_universe_lookup_requires_exact_pool_key(self) -> None:
        self.assertIsNotNone(self.layer.metadata.get_universe("hs300"))
        self.assertIsNone(self.layer.metadata.get_universe("沪深300"))

    def test_dataset_lookup_supports_table_key(self) -> None:
        dataset = self.layer.metadata.get_dataset("stock_kline_daily_qfq")
        self.assertIsNotNone(dataset)
        assert dataset is not None
        self.assertEqual(dataset.get("table_key"), "stock_kline_daily_qfq")

    def test_semantic_layer_constructor_can_default_to_sqlite_via_env(self) -> None:
        with patch.dict("os.environ", {"QUANTA_DATA_ENGINE": "sqlite"}, clear=False):
            layer = SemanticLayer(MetadataManager({"datasets": [], "universes": {}, "backtest_datasets": []}))

        self.assertEqual(layer.default_engine, "sqlite")

    def test_semantic_layer_default_uses_env_engine(self) -> None:
        with patch.dict("os.environ", {"QUANTA_DATA_ENGINE": "sqlite"}, clear=False):
            layer = SemanticLayer.default()

        self.assertEqual(layer.default_engine, "sqlite")

    def test_sqlite_connector_resolves_relative_path_against_project_root(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            fake_root = Path(tmp_dir)
            with patch("quanta_agents.semantic.metadata.PROJECT_ROOT", fake_root):
                connector = SQLiteConnector("./market_data.db")

        self.assertEqual(connector.db_path, str(fake_root / "market_data.db"))

    def test_load_required_data_dispatches_by_table_type(self) -> None:
        result = self.layer.load_required_data(
            [
                {
                    "table_key": "stock_kline_daily_qfq",
                    "type": "time_series",
                    "fields": ["open", "close"],
                    "universe": {"type": "named_pool", "value": "hs300"},
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "purpose": "测试日线行情",
                },
                {
                    "table_key": "momentum_factor_data",
                    "type": "panel",
                    "universe": {"type": "named_pool", "value": "hs300"},
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "purpose": "测试面板表",
                },
                {
                    "table_key": "bank_rate_data",
                    "type": "auxiliary",
                    "fields": ["3year_rate", "5year_rate"],
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "purpose": "测试辅助表",
                },
                {
                    "table_key": "basic_stock_info",
                    "type": "static",
                    "fields": ["code", "name"],
                    "purpose": "测试静态表",
                },
            ]
        )

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["type"], "time_series")
        self.assertEqual(result[0]["universe"]["type"], "named_pool")
        self.assertEqual(result[0]["data"].columns.tolist(), ["trade_date", "code", "open", "close"])
        self.assertEqual(len(result[0]["data"]), 1)
        self.assertEqual(float(result[0]["data"]["close"].iloc[0]), 11.5)
        self.assertEqual(result[1]["type"], "panel")
        self.assertEqual(result[1]["data"].columns.tolist(), ["trade_date", "000001.SZ", "000002.SZ"])
        self.assertEqual(result[2]["type"], "auxiliary")
        self.assertEqual(result[2]["data"].columns.tolist(), ["trade_date", "3year_rate", "5year_rate"])
        self.assertEqual(len(result[2]["data"]), 1)
        self.assertEqual(float(result[2]["data"]["3year_rate"].iloc[0]), 2.9)
        self.assertEqual(result[3]["type"], "static")
        self.assertEqual(result[3]["data"].columns.tolist(), ["code", "name"])

        self.assertEqual(len(self.fake_connector.calls), 4)
        time_series_query, time_series_params = self.fake_connector.calls[0]
        self.assertIn("stock_kline_daily_qfq", time_series_query)
        self.assertIn("code IN (:sym_0, :sym_1)", time_series_query)
        self.assertEqual(time_series_params, {"start": "2024-01-01", "end": "2024-12-31", "sym_0": "000001.SZ", "sym_1": "000002.SZ"})

        panel_query, panel_params = self.fake_connector.calls[1]
        self.assertIn("SELECT * FROM momentum_factor_data", panel_query)
        self.assertEqual(panel_params, {"start": "2024-01-01", "end": "2024-12-31"})

        auxiliary_query, auxiliary_params = self.fake_connector.calls[2]
        self.assertIn("bank_rate_data", auxiliary_query)
        self.assertNotIn("IN (", auxiliary_query)
        self.assertEqual(auxiliary_params, {"start": "2024-01-01", "end": "2024-12-31"})

        static_query, static_params = self.fake_connector.calls[3]
        self.assertIn("SELECT code, name FROM basic_stock_info", static_query)
        self.assertEqual(static_params, {})
