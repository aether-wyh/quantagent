from __future__ import annotations

from datetime import datetime
import json
import sqlite3
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


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

from quanta_agents.agents.strategy_tester import StrategyTester
from quanta_agents.semantic.layer import SemanticLayer
from quanta_agents.semantic.metadata import MetadataManager
from quanta_agents.state import init_state


class StrategyTesterTest(TestCase):
    def test_stats_to_result_rejects_negative_result_without_custom_rules(self) -> None:
        result = StrategyTester._stats_to_result(
            {
                "annual_return": -0.08,
                "sharpe_ratio": -0.4,
                "max_drawdown": -20_000.0,
                "max_ddpercent": -0.10,
                "total_trade_count": 12,
            },
            {"capital": 1_000_000.0},
        )

        self.assertFalse(result.passed)
        self.assertIn("default_gate", result.summary)

    def test_stats_to_result_infers_percent_units_from_balance_consistency(self) -> None:
        stats = {
            "capital": 1_000_000.0,
            "end_balance": 1_013_384.6164999583,
            "total_return": 1.3384616499958257,
            "annual_return": 0.6623315381422643,
            "sharpe_ratio": 0.03,
            "max_drawdown": -332154.87719586224,
            "max_ddpercent": -30.573594345257355,
        }

        result = StrategyTester._stats_to_result(stats, {"capital": 1_000_000.0})

        self.assertAlmostEqual(result.annual_return, 0.006623315381422643, places=12)
        assert result.max_ddpercent is not None
        self.assertAlmostEqual(result.max_ddpercent, 0.30573594345257354, places=12)

    def test_stats_to_result_keeps_ratio_units_when_consistent(self) -> None:
        stats = {
            "capital": 1_000_000.0,
            "end_balance": 1_013_384.6164999583,
            "total_return": 0.013384616499958257,
            "annual_return": 0.06623315381422643,
            "sharpe_ratio": 0.03,
            "max_drawdown": -332154.87719586224,
            "max_ddpercent": -0.30573594345257354,
        }

        result = StrategyTester._stats_to_result(stats, {"capital": 1_000_000.0})

        self.assertAlmostEqual(result.annual_return, 0.06623315381422643, places=12)
        assert result.max_ddpercent is not None
        self.assertAlmostEqual(result.max_ddpercent, 0.30573594345257354, places=12)

    def test_stats_to_result_uses_equity_curve_for_max_ddpercent(self) -> None:
        daily_df = __import__("pandas").DataFrame(
            [
                {"date": "2024-01-02", "balance": 1_000_000.0},
                {"date": "2024-01-03", "balance": 1_200_000.0},
                {"date": "2024-01-04", "balance": 1_100_000.0},
            ]
        )
        stats = {
            "annual_return": 0.1,
            "sharpe_ratio": 1.0,
            "max_drawdown": -100_000.0,
            "max_ddpercent": -10.0,
            "_daily_df": daily_df,
        }

        result = StrategyTester._stats_to_result(stats, {"capital": 1_000_000.0})

        self.assertEqual(result.max_drawdown, -100_000.0)
        assert result.max_ddpercent is not None
        self.assertAlmostEqual(result.max_ddpercent, 100_000.0 / 1_200_000.0, places=10)

    def test_stats_to_result_checks_event_count_and_reports_event_metrics(self) -> None:
        stats = {
            "annual_return": 0.1,
            "sharpe_ratio": 1.0,
            "max_drawdown": -1_000.0,
            "max_ddpercent": -0.01,
            "total_trade_count": 12,
            "event_gross_mean_return": 0.002,
            "event_net_mean_return": 0.0004,
            "event_success_column": "joint_minute_hit",
            "event_success_rate": 0.42,
            "event_success_ci_low": 0.25,
            "event_success_ci_high": 0.61,
        }

        result = StrategyTester._stats_to_result(
            stats,
            {
                "evaluation": {
                    "min_trade_count": 20,
                    "min_event_net_mean": 0.0003,
                    "min_event_success_rate": 0.40,
                }
            },
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.trade_count, 12)
        self.assertEqual(result.event_net_mean_return, 0.0004)
        self.assertEqual(result.event_success_rate, 0.42)
        self.assertEqual(result.event_success_column, "joint_minute_hit")
        self.assertIn("min_trade_count=20", result.summary)
        self.assertIn("min_event_success_rate=40.00%", result.summary)
        self.assertIn("event_net_mean=0.0400%", result.summary)
        self.assertIn("joint_minute_hit=42.00%", result.summary)
        self.assertIn("success_95pct_range=[25.00%, 61.00%]", result.summary)

    def test_event_success_gate_uses_explicit_metric_and_keeps_legacy_default(self) -> None:
        stats = {
            "annual_return": 0.10,
            "sharpe_ratio": 1.0,
            "max_drawdown": -1_000.0,
            "max_ddpercent": -0.01,
            "total_trade_count": 8_919,
            "event_net_mean_return": 0.0005193,
            "event_gross_up_rate": 0.4857,
            "event_joint_minute_hit_rate": 0.2674,
            "event_success_column": "joint_minute_hit",
            "event_success_rate": 0.2674,
            "event_success_ci_low": 0.25,
            "event_success_ci_high": 0.28,
        }
        common_evaluation = {
            "min_trade_count": 100,
            "min_event_net_mean": 0.0,
            "min_event_success_rate": 0.35,
        }

        gross_result = StrategyTester._stats_to_result(
            stats,
            {
                "evaluation": {
                    **common_evaluation,
                    "event_success_metric": "gross_up_rate",
                }
            },
        )
        joint_result = StrategyTester._stats_to_result(
            stats,
            {
                "evaluation": {
                    **common_evaluation,
                    "event_success_metric": "joint_minute_hit",
                }
            },
        )
        legacy_result = StrategyTester._stats_to_result(
            stats,
            {"evaluation": common_evaluation},
        )

        self.assertTrue(gross_result.passed)
        self.assertEqual(gross_result.event_success_metric, "gross_up_rate")
        self.assertEqual(gross_result.event_success_metric_value, 0.4857)
        self.assertEqual(gross_result.event_joint_minute_hit_rate, 0.2674)
        self.assertIn("gross_up_rate=48.57%", gross_result.summary)
        self.assertIn("joint_minute_hit=26.74%", gross_result.summary)
        self.assertNotIn("success_95pct_range", gross_result.summary)

        self.assertFalse(joint_result.passed)
        self.assertEqual(joint_result.event_success_metric_value, 0.2674)
        self.assertFalse(legacy_result.passed)
        self.assertEqual(
            legacy_result.event_success_metric,
            "legacy_event_success_rate",
        )
        self.assertEqual(legacy_result.event_success_metric_value, 0.2674)

    def test_resolve_vt_symbols_preserves_raw_suffixes(self) -> None:
        symbols = StrategyTester._resolve_vt_symbols(
            {"universe": {"type": "symbol_list", "value": ["000001.SZ", "600000.SH", "000001.SZSE", "000001.SZ"]}},
        )
        self.assertEqual(symbols, ["000001.SZ", "600000.SH", "000001.SZSE"])

    def test_intersect_vt_symbols_requires_exact_symbol_match(self) -> None:
        intersected = StrategyTester._intersect_vt_symbols(
            ["000001.SZ", "600000.SSE", "000488.SZSE"],
            ["000001.SZSE", "000488.SZSE", "600000.SSE"],
        )
        self.assertEqual(intersected, ["600000.SSE", "000488.SZSE"])

    def test_ensure_vnpy_dolphindb_settings_writes_expected_database_config(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            setting_path = Path(tmp_dir) / ".vntrader" / "vt_setting.json"

            with patch.dict("os.environ", {}, clear=True), patch.object(StrategyTester, "_resolve_vnpy_setting_path", return_value=setting_path):
                written_path = StrategyTester._ensure_vnpy_dolphindb_settings()

            self.assertEqual(written_path, setting_path)
            settings = json.loads(setting_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["database.name"], "dolphindb")
            self.assertEqual(settings["database.database"], "vnpy_bar_db")
            self.assertEqual(settings["database.host"], "localhost")
            self.assertEqual(settings["database.port"], 8848)
            self.assertEqual(settings["database.user"], "admin")
            self.assertEqual(settings["database.password"], "")

    def test_ensure_vnpy_database_settings_supports_sqlite(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            setting_path = Path(tmp_dir) / ".vntrader" / "vt_setting.json"
            sqlite_path = Path(tmp_dir) / "vnpy_bar.sqlite3"

            with patch.object(StrategyTester, "_resolve_vnpy_setting_path", return_value=setting_path):
                with patch.object(StrategyTester, "_resolve_vnpy_sqlite_db_path", return_value=str(sqlite_path)):
                    written_path = StrategyTester._ensure_vnpy_database_settings(backtest_db_backend="sqlite")

            self.assertEqual(written_path, setting_path)
            settings = json.loads(setting_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["database.name"], "sqlite")
            self.assertEqual(settings["database.database"], str(sqlite_path))

    def test_resolve_backtest_db_backend_reads_quanta_data_engine_env(self) -> None:
        with patch.dict("os.environ", {"QUANTA_DATA_ENGINE": "sqlite"}, clear=False):
            backend = StrategyTester._resolve_backtest_db_backend()
        self.assertEqual(backend, "sqlite")

    def test_resolve_backtest_db_backend_prefers_explicit_parquet_backend(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "QUANTA_DATA_ENGINE": "dolphindb",
                "QUANTA_BACKTEST_DB_BACKEND": "parquet",
            },
            clear=False,
        ):
            backend = StrategyTester._resolve_backtest_db_backend()
        self.assertEqual(backend, "parquet")

    def test_ensure_vnpy_database_settings_uses_sqlite_backtest_db_path_env(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            setting_path = Path(tmp_dir) / ".vntrader" / "vt_setting.json"
            sqlite_path = Path(tmp_dir) / "custom_vnpy.sqlite3"

            with patch.dict("os.environ", {"SQLITE_BACKTEST_DB_PATH": str(sqlite_path)}, clear=False):
                with patch.object(StrategyTester, "_resolve_vnpy_setting_path", return_value=setting_path):
                    written_path = StrategyTester._ensure_vnpy_database_settings(backtest_db_backend="sqlite")

            self.assertEqual(written_path, setting_path)
            settings = json.loads(setting_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["database.name"], "sqlite")
            self.assertEqual(settings["database.database"], str(sqlite_path))

    def test_resolve_backtest_dataset_specs_requires_non_empty_keys(self) -> None:
        state = init_state(
            user_idea="backtest dataset required",
            max_epochs=1,
            experiment_spec={"experiment_id": "exp_backtest_required"},
        )
        with self.assertRaisesRegex(RuntimeError, "backtest_datasets is required"):
            StrategyTester._resolve_backtest_dataset_specs(state, strategy_result={})

    def test_load_available_bar_vt_symbols_reads_from_sqlite(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            sqlite_path = Path(tmp_dir) / "vnpy_bar.sqlite3"
            with sqlite3.connect(sqlite_path) as conn:
                conn.execute("CREATE TABLE dbbardata (symbol TEXT, exchange TEXT)")
                conn.execute("INSERT INTO dbbardata(symbol, exchange) VALUES ('000488', 'SZSE')")
                conn.execute("INSERT INTO dbbardata(symbol, exchange) VALUES ('600025', 'SSE')")
                conn.execute("INSERT INTO dbbardata(symbol, exchange) VALUES ('000488', 'SZSE')")

            with patch.object(StrategyTester, "_resolve_vnpy_sqlite_db_path", return_value=str(sqlite_path)):
                vt_symbols = StrategyTester._load_available_bar_vt_symbols(
                    backtest_db_backend="sqlite",
                    backtest_dataset_specs=[{"table_key": "dbbardata"}],
                )

        self.assertEqual(vt_symbols, ["000488.SZSE", "600025.SSE"])

    def test_load_available_bar_vt_symbols_reads_symbol_exchange_pairs(self) -> None:
        fake_df = __import__("pandas").DataFrame(
            [
                {"symbol": "000488", "exchange": "SZSE"},
                {"symbol": "600025", "exchange": "SSE"},
                {"symbol": "000488", "exchange": "SZSE"},
            ]
        )

        class _FakeConnector:
            def execute_query(self, query):
                self.last_query = query
                return fake_df

        with patch("quanta_agents.agents.strategy_tester.DolphinDBConnector", return_value=_FakeConnector()):
            vt_symbols = StrategyTester._load_available_bar_vt_symbols(
                backtest_db_backend="dolphindb",
                backtest_dataset_specs=[{"table_key": "bar"}],
            )

        self.assertEqual(vt_symbols, ["000488.SZSE", "600025.SSE"])

    def test_ensure_vnpy_dolphindb_compatibility_redirects_db_path(self) -> None:
        class _FakeDolphinDBDatabase:
            def __init__(self) -> None:
                self.db_path = "dfs://vnpy"
                self.session = SimpleNamespace(run=self._run)

            def _run(self, query):
                import pandas as pd

                self.last_query = query
                return pd.DataFrame(
                    [
                        {
                            "symbol": "000488",
                            "exchange": "SZSE",
                            "datetime": pd.Timestamp("2024-01-02"),
                            "interval": "d",
                            "volume": 1.0,
                            "turnover": 2.0,
                            "open_interest": 0.0,
                            "open_price": 3.0,
                            "high_price": 4.0,
                            "low_price": 2.5,
                            "close_price": 3.5,
                        }
                    ]
                )

        fake_package = ModuleType("vnpy_dolphindb")
        fake_database_module = ModuleType("vnpy_dolphindb.dolphindb_database")
        setattr(fake_database_module, "DolphindbDatabase", _FakeDolphinDBDatabase)

        with patch.dict(
            sys.modules,
            {
                "vnpy_dolphindb": fake_package,
                "vnpy_dolphindb.dolphindb_database": fake_database_module,
            },
        ):
            StrategyTester._ensure_vnpy_dolphindb_compatibility(
                backtest_dataset_specs=[{"table_key": "bar"}],
            )

        patched_class = fake_package.Database
        instance = patched_class()
        self.assertEqual(instance.db_path, "dfs://vnpy_bar_db")
        from datetime import datetime as _dt
        from vnpy.trader.constant import Exchange, Interval

        bars = instance.load_bar_data("000488", Exchange.SZSE, Interval.DAILY, _dt(2024, 1, 1), _dt(2025, 12, 31))
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].symbol, "000488")
        self.assertEqual(bars[0].exchange.value, "SZSE")

    def test_ensure_vnpy_sqlite_compatibility_loads_from_selected_tables(self) -> None:
        class _FakeSqliteDatabase:
            def __init__(self) -> None:
                self.ready = True

        with TemporaryDirectory() as tmp_dir:
            sqlite_path = Path(tmp_dir) / "bars.sqlite3"
            with sqlite3.connect(sqlite_path) as conn:
                conn.execute(
                    "CREATE TABLE table_a (symbol TEXT, exchange TEXT, datetime TEXT, interval TEXT, volume REAL, turnover REAL, open_interest REAL, open_price REAL, high_price REAL, low_price REAL, close_price REAL)"
                )
                conn.execute(
                    "CREATE TABLE table_b (symbol TEXT, exchange TEXT, datetime TEXT, interval TEXT, volume REAL, turnover REAL, open_interest REAL, open_price REAL, high_price REAL, low_price REAL, close_price REAL)"
                )
                conn.execute(
                    "INSERT INTO table_a VALUES ('000488', 'SZSE', '2024-01-02 00:00:00', 'd', 1, 2, 0, 3, 4, 2.5, 3.5)"
                )
                conn.execute(
                    "INSERT INTO table_b VALUES ('000488', 'SZSE', '2024-01-03 00:00:00', 'd', 2, 3, 0, 4, 5, 3.5, 4.5)"
                )

            fake_package = ModuleType("vnpy_sqlite")
            fake_database_module = ModuleType("vnpy_sqlite.sqlite_database")
            setattr(fake_database_module, "SqliteDatabase", _FakeSqliteDatabase)

            with patch.object(StrategyTester, "_resolve_vnpy_sqlite_db_path", return_value=str(sqlite_path)):
                with patch.dict(
                    sys.modules,
                    {
                        "vnpy_sqlite": fake_package,
                        "vnpy_sqlite.sqlite_database": fake_database_module,
                    },
                ):
                    StrategyTester._ensure_vnpy_sqlite_compatibility(
                        backtest_dataset_specs=[
                            {"table_key": "table_a"},
                            {"table_key": "table_b"},
                        ]
                    )

            patched_class = fake_package.Database
            instance = patched_class()
            from datetime import datetime as _dt
            from vnpy.trader.constant import Exchange, Interval

            bars = instance.load_bar_data("000488", Exchange.SZSE, Interval.DAILY, _dt(2024, 1, 1), _dt(2024, 1, 31))
            self.assertEqual(len(bars), 2)
            self.assertEqual([bar.datetime.strftime("%Y-%m-%d") for bar in bars], ["2024-01-02", "2024-01-03"])

    def test_ensure_vnpy_dolphindb_compatibility_queries_selected_tables(self) -> None:
        class _FakeDolphinDBDatabase:
            def __init__(self) -> None:
                self.db_path = "dfs://vnpy"
                self.queries: list[str] = []
                self.session = SimpleNamespace(run=self._run)

            def _run(self, query):
                import pandas as pd

                self.queries.append(query)
                if '"table_a"' in query:
                    return pd.DataFrame(
                        [{
                            "symbol": "000488",
                            "exchange": "SZSE",
                            "datetime": pd.Timestamp("2024-01-02"),
                            "interval": "d",
                            "volume": 1.0,
                            "turnover": 2.0,
                            "open_interest": 0.0,
                            "open_price": 3.0,
                            "high_price": 4.0,
                            "low_price": 2.5,
                            "close_price": 3.5,
                        }]
                    )
                if '"table_b"' in query:
                    return pd.DataFrame(
                        [{
                            "symbol": "000488",
                            "exchange": "SZSE",
                            "datetime": pd.Timestamp("2024-01-03"),
                            "interval": "d",
                            "volume": 2.0,
                            "turnover": 3.0,
                            "open_interest": 0.0,
                            "open_price": 4.0,
                            "high_price": 5.0,
                            "low_price": 3.5,
                            "close_price": 4.5,
                        }]
                    )
                return pd.DataFrame()

        fake_package = ModuleType("vnpy_dolphindb")
        fake_database_module = ModuleType("vnpy_dolphindb.dolphindb_database")
        setattr(fake_database_module, "DolphindbDatabase", _FakeDolphinDBDatabase)

        with patch.dict(
            sys.modules,
            {
                "vnpy_dolphindb": fake_package,
                "vnpy_dolphindb.dolphindb_database": fake_database_module,
            },
        ):
            StrategyTester._ensure_vnpy_dolphindb_compatibility(
                backtest_dataset_specs=[
                    {"table_key": "table_a"},
                    {"table_key": "table_b"},
                ]
            )

        patched_class = fake_package.Database
        instance = patched_class()
        from datetime import datetime as _dt
        from vnpy.trader.constant import Exchange, Interval

        bars = instance.load_bar_data("000488", Exchange.SZSE, Interval.DAILY, _dt(2024, 1, 1), _dt(2024, 1, 31))
        self.assertEqual(len(bars), 2)
        self.assertTrue(any('"table_a"' in query for query in instance.queries))
        self.assertTrue(any('"table_b"' in query for query in instance.queries))

    def test_run_intersects_universe_with_available_bar_symbols(self) -> None:
        code = """
class StrategyTemplate:
    pass

class DemoPortfolioStrategy(StrategyTemplate):
    def on_init(self):
        pass

    def on_bar(self, bar):
        pass
"""

        state = init_state(
            user_idea="portfolio strategy test",
            max_epochs=1,
            experiment_spec={
                "experiment_id": "exp_portfolio_intersection",
                "universe": {"type": "symbol_list", "value": ["000488.SZSE", "600025.SSE"]},
                "backtest_start": "2024-01-01",
                "backtest_end": "2024-12-31",
            },
        )
        state["selected_base_class"] = "StrategyTemplate"
        state["selected_template"] = "PortfolioStrategyTemplate"
        state["code_text"] = code
        state["strategy_generation_meta"] = {}
        state["strategy_result"] = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000488.SZSE": 0.5, "600025.SSE": 0.4, "cash": 0.1}]
            ),
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        tester = StrategyTester()

        with patch.object(StrategyTester, "_ensure_vnpy_database_settings", return_value=Path("/tmp/vt_setting.json")):
            with patch.object(StrategyTester, "_ensure_vnpy_dolphindb_compatibility", return_value=None):
                with patch.object(StrategyTester, "_load_available_bar_vt_symbols", return_value=["600025.SSE", "000488.SZSE"]):
                    with patch.object(
                        StrategyTester,
                        "_recompute_output_weights_for_backtest",
                        return_value=(state["strategy_result"]["output_weights"], {}),
                    ):
                        with patch("quanta_agents.agents.strategy_tester.importlib.import_module", return_value=object()):
                            with patch.object(StrategyTester, "_run_engine_backtest", return_value={"annual_return": 0.1, "sharpe_ratio": 1.0, "max_ddpercent": -0.05}) as engine_mock:
                                result = tester.run(state)

        self.assertTrue(engine_mock.called)
        self.assertEqual(engine_mock.call_args.kwargs["vt_symbols"], ["000488.SZSE", "600025.SSE"])
        self.assertEqual(result["phase"], "test")

    def test_ensure_vnpy_dolphindb_compatibility_adds_tick_overview(self) -> None:
        class _FakeDolphinDBDatabase:
            def __init__(self) -> None:
                self.ready = True

        fake_package = ModuleType("vnpy_dolphindb")
        fake_database_module = ModuleType("vnpy_dolphindb.dolphindb_database")
        setattr(fake_database_module, "DolphindbDatabase", _FakeDolphinDBDatabase)

        with patch.dict(
            sys.modules,
            {
                "vnpy_dolphindb": fake_package,
                "vnpy_dolphindb.dolphindb_database": fake_database_module,
            },
        ):
            StrategyTester._ensure_vnpy_dolphindb_compatibility(
                backtest_dataset_specs=[{"table_key": "bar"}],
            )

        patched_class = fake_package.Database
        instance = patched_class()
        self.assertTrue(hasattr(instance, "get_tick_overview"))
        self.assertEqual(instance.get_tick_overview(), [])

    def test_load_strategy_class_ignores_template_base_class_itself(self) -> None:
        code = """
class StrategyTemplate:
    def on_bars(self, bars):
        pass

class RsiMeanReversionStrategy(StrategyTemplate):
    def on_init(self):
        pass

    def on_bars(self, bars):
        pass

    def on_trade(self, trade):
        pass
"""
        strategy_class = StrategyTester._load_strategy_class_by_template(
            code,
            expected_base_class="StrategyTemplate",
        )
        self.assertEqual(strategy_class.__name__, "RsiMeanReversionStrategy")

    def test_build_fixed_portfolio_strategy_uses_update_trade_hook(self) -> None:
        code = StrategyTester._build_fixed_portfolio_strategy_code()
        namespace: dict[str, object] = {"__name__": "__generated_strategy__"}
        exec(compile(code, "generated_strategy.py", "exec"), namespace)

        strategy_class = namespace["Strategy"]
        strategy = strategy_class(
            strategy_engine=object(),
            strategy_name="demo",
            vt_symbols=["000001.SZSE"],
            setting={"capital": 1_000_000.0},
        )
        trade = SimpleNamespace(
            pnl=123.45,
            commission=6.7,
            datetime=datetime(2024, 1, 2),
            symbol="000001",
            direction="LONG",
            volume=100,
            price=12.34,
        )

        self.assertTrue(callable(getattr(strategy, "update_trade", None)))
        self.assertFalse(hasattr(type(strategy), "on_trade"))

        strategy.update_trade(trade)

        self.assertEqual(strategy.capital_tracker.trade_count, 1)
        self.assertAlmostEqual(strategy.capital_tracker.total_commission, 6.7)
        self.assertAlmostEqual(strategy.capital_tracker.equity, 1_000_123.45)

    def test_semantic_layer_converts_raw_sh_sz_symbols_to_vnpy_format(self) -> None:
        layer = SemanticLayer(MetadataManager.from_yaml_files())
        series = layer._to_vt_symbol(
            __import__("pandas").Series(["000001.SZ", "600000.SH", "000001.SZSE", "600000.SSE"])
        )
        self.assertEqual(series.tolist(), ["000001.SZSE", "600000.SSE", "000001.SZSE", "600000.SSE"])

    def test_run_routes_single_symbol_weights_to_portfolio_backtest(self) -> None:
        code = """
class StrategyTemplate:
    pass

class DemoPortfolioStrategy(StrategyTemplate):
    def on_init(self):
        pass

    def on_bars(self, bars):
        pass

    def update_trade(self, trade):
        pass
"""

        state = init_state(
            user_idea="cta strategy test",
            max_epochs=1,
            experiment_spec={
                "universe": {"type": "symbol_list", "value": ["000001.SZSE"]},
                "backtest_start": "2024-01-01",
                "backtest_end": "2024-12-31",
            },
        )
        state["selected_base_class"] = "StrategyTemplate"
        state["selected_template"] = "PortfolioStrategyTemplate"
        state["code_text"] = code
        state["strategy_generation_meta"] = {}
        state["strategy_result"] = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZSE": 0.9, "cash": 0.1}]
            ),
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        tester = StrategyTester()

        with patch.object(StrategyTester, "_ensure_vnpy_database_settings", return_value=Path("/tmp/vt_setting.json")):
            with patch.object(StrategyTester, "_load_available_bar_vt_symbols", return_value=["000001.SZSE"]):
                with patch.object(
                    StrategyTester,
                    "_recompute_output_weights_for_backtest",
                    return_value=(state["strategy_result"]["output_weights"], {}),
                ):
                    with patch("quanta_agents.agents.strategy_tester.importlib.import_module", return_value=object()):
                        with patch.object(
                            StrategyTester,
                            "_run_engine_backtest",
                            return_value={
                                "annual_return": 20.0,
                                "sharpe_ratio": 1.6,
                                "max_ddpercent": -10.0,
                            },
                        ) as engine_mock:
                            result = tester.run(state)

        self.assertTrue(engine_mock.called)
        self.assertEqual(engine_mock.call_args.kwargs["engine_module"], "vnpy_portfoliostrategy.backtesting")
        self.assertIsNotNone(result["test_result"])
        assert result["test_result"] is not None
        self.assertTrue(result["test_result"].passed)
        self.assertEqual(result["phase"], "test")
        self.assertTrue(any("portfolio backtest engine" in item for item in result["history"]))
        self.assertEqual(result["selected_template"], "PortfolioStrategyTemplate")

    def test_run_uses_local_parquet_target_weight_backtest_without_vnpy(self) -> None:
        weights = __import__("pandas").DataFrame(
            [{"datetime": "2024-01-02", "000001.SZ": 0.9, "cash": 0.1}]
        )
        state = init_state(
            user_idea="local parquet test",
            max_epochs=1,
            experiment_spec={
                "experiment_id": "exp_local_parquet",
                "backtest_start": "2024-01-01",
                "backtest_end": "2024-12-31",
            },
        )
        state["strategy_code"] = "def output_weights(*args):\n    return None\n"
        state["strategy_result"] = {
            "output_weights": weights,
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        stats = {
            "capital": 1_000_000.0,
            "end_balance": 1_100_000.0,
            "total_return": 0.1,
            "annual_return": 0.1,
            "sharpe_ratio": 1.0,
            "max_drawdown": -10_000.0,
            "max_ddpercent": -0.02,
        }
        tester = StrategyTester()

        with patch.dict(
            "os.environ",
            {"QUANTA_BACKTEST_DB_BACKEND": "parquet"},
            clear=False,
        ):
            with patch.object(
                StrategyTester,
                "_recompute_output_weights_for_backtest",
                return_value=(weights, {}),
            ):
                with patch.object(StrategyTester, "_ensure_vnpy_database_settings") as vnpy_settings:
                    with patch(
                        "quanta_agents.local_parquet_backtest.run_target_weight_backtest",
                        return_value=stats,
                    ) as local_backtest:
                        with patch.object(StrategyTester, "_export_backtest_artifacts", return_value={}):
                            result = tester.run(state)

        vnpy_settings.assert_not_called()
        local_backtest.assert_called_once()
        self.assertEqual(result["selected_template"], "LocalParquetTargetWeight")
        self.assertEqual(result["phase"], "test")
        self.assertIsNotNone(result["test_result"])

    def test_portfolio_backtest_uses_vt_symbols_signature(self) -> None:
        class _FakeEngine:
            def __init__(self) -> None:
                self.parameters = None

            def set_parameters(self, **kwargs):
                self.parameters = kwargs

            def add_strategy(self, *args, **kwargs):
                return None

            def load_data(self):
                return None

            def run_backtesting(self):
                return None

            def calculate_result(self):
                return [{"date": "2024-01-02", "balance": 1000000.0}]

            def calculate_statistics(self, output=False):
                return {"annual_return": 0.1, "sharpe_ratio": 1.0, "max_ddpercent": -0.05}

        fake_module = ModuleType("vnpy_portfoliostrategy.backtesting")
        setattr(fake_module, "BacktestingEngine", _FakeEngine)
        fake_package = ModuleType("vnpy_portfoliostrategy")
        setattr(fake_package, "backtesting", fake_module)

        with patch.dict(sys.modules, {"vnpy_portfoliostrategy": fake_package, "vnpy_portfoliostrategy.backtesting": fake_module}):
            stats = StrategyTester._run_engine_backtest(
                engine_module="vnpy_portfoliostrategy.backtesting",
                strategy_class=type("DemoPortfolioStrategy", (), {}),
                vt_symbol="000001.SZSE",
                vt_symbols=["000001.SZSE", "000002.SZSE"],
                interval_name="1d",
                start=datetime(2024, 1, 1),
                end=datetime(2024, 12, 31),
                experiment_spec={"capital": 1000000.0},
                contract_settings={
                    "000001.SZSE": {"long_rate": 0.001, "short_rate": 0.002, "size": 10, "pricetick": 0.01},
                    "000002.SZSE": {"long_rate": 0.003, "short_rate": 0.004, "size": 20, "pricetick": 0.02},
                },
            )

        self.assertIn("annual_return", stats)
        self.assertEqual(stats["_daily_df"][0]["balance"], 1000000.0)

    def test_run_exports_backtest_artifacts_on_success(self) -> None:
        code = """
class StrategyTemplate:
    pass

class DemoPortfolioStrategy(StrategyTemplate):
    def on_init(self):
        pass

    def on_bars(self, bars):
        pass

    def on_trade(self, trade):
        pass

    def on_order(self, order):
        pass
"""

        state = init_state(
            user_idea="portfolio strategy export test",
            max_epochs=1,
            experiment_spec={
                "experiment_id": "exp_portfolio_export",
                "universe": {"type": "symbol_list", "value": ["000001.SZSE"]},
                "backtest_start": "2024-01-01",
                "backtest_end": "2024-12-31",
            },
        )
        state["selected_base_class"] = "StrategyTemplate"
        state["selected_template"] = "PortfolioStrategyTemplate"
        state["code_text"] = code
        state["strategy_generation_meta"] = {}
        state["strategy_result"] = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZSE": 0.8, "cash": 0.2}]
            ),
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        tester = StrategyTester()

        with patch.object(StrategyTester, "_ensure_vnpy_database_settings", return_value=Path("/tmp/vt_setting.json")):
            with patch.object(StrategyTester, "_load_available_bar_vt_symbols", return_value=["000001.SZSE"]):
                with patch.object(
                    StrategyTester,
                    "_recompute_output_weights_for_backtest",
                    return_value=(state["strategy_result"]["output_weights"], {}),
                ):
                    with patch("quanta_agents.agents.strategy_tester.importlib.import_module", return_value=object()):
                        with patch.object(
                            StrategyTester,
                            "_run_engine_backtest",
                            return_value={
                                "annual_return": 12.0,
                                "sharpe_ratio": 1.1,
                                "max_ddpercent": -9.0,
                            },
                        ):
                            with patch.object(StrategyTester, "_export_backtest_artifacts", return_value={"performance_summary": "/tmp/summary.json"}) as export_mock:
                                result = tester.run(state)

        self.assertTrue(export_mock.called)
        self.assertEqual(result["phase"], "test")

    def test_export_backtest_artifacts_writes_trades_and_target_weights(self) -> None:
        pd = __import__("pandas")
        state = init_state(
            user_idea="export local details",
            max_epochs=1,
            experiment_spec={"experiment_id": "exp_export_local_details"},
        )
        stats = {
            "capital": 1_000_000.0,
            "end_balance": 1_010_000.0,
            "total_return": 0.01,
            "annual_return": 0.1,
            "sharpe_ratio": 1.0,
            "max_drawdown": -1_000.0,
            "max_ddpercent": -0.01,
            "_daily_df": pd.DataFrame(
                [{"date": "2024-01-02", "balance": 1_010_000.0}]
            ),
            "_trades_df": pd.DataFrame(
                [{"date": "2024-01-02", "code": "sz000001", "side": "buy", "shares": 100}]
            ),
            "_target_weights_df": pd.DataFrame(
                {"000001.SZ": [0.9], "cash": [0.1]},
                index=pd.DatetimeIndex(["2024-01-02"], name="trade_date"),
            ),
        }
        result = StrategyTester._stats_to_result(stats, {"capital": 1_000_000.0})

        with TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            with patch.object(StrategyTester, "_resolve_backtest_output_dir", return_value=output_dir):
                paths = StrategyTester._export_backtest_artifacts(
                    state=state,
                    stats=stats,
                    backtest_result=result,
                    template_family="local_parquet",
                    experiment_spec={"capital": 1_000_000.0},
                )

            self.assertTrue(Path(paths["trades"]).is_file())
            self.assertTrue(Path(paths["target_weights"]).is_file())
            exported_weights = pd.read_csv(paths["target_weights"])
            self.assertIn("trade_date", exported_weights.columns)

    def test_event_artifact_exports_only_nonzero_target_weights(self) -> None:
        pd = __import__("pandas")
        state = init_state(
            user_idea="export event details",
            max_epochs=1,
            experiment_spec={"experiment_id": "exp_export_event_details"},
        )
        stats = {
            "capital": 1_000_000.0,
            "end_balance": 1_001_000.0,
            "total_return": 0.001,
            "annual_return": 0.01,
            "sharpe_ratio": 0.2,
            "max_drawdown": -100.0,
            "max_ddpercent": -0.0001,
            "event_gross_up_rate": 0.4857,
            "event_joint_minute_hit_rate": 0.2674,
            "event_success_column": "joint_minute_hit",
            "event_success_rate": 0.2674,
            "_daily_df": pd.DataFrame(
                [{"date": "2024-01-02", "balance": 1_001_000.0}]
            ),
            "_target_weights_df": pd.DataFrame(
                {
                    "sh600000": pd.arrays.SparseArray(
                        [0.5, 0.0], fill_value=0.0
                    ),
                    "sz000001": pd.arrays.SparseArray(
                        [0.0, 1.0], fill_value=0.0
                    ),
                    "cash": [0.5, 0.0],
                },
                index=pd.DatetimeIndex(
                    ["2024-01-02 10:00:00", "2024-01-02 10:01:00"],
                    name="trigger_ts",
                ),
            ),
        }
        experiment_spec = {
            "capital": 1_000_000.0,
            "evaluation": {
                "min_event_success_rate": 0.35,
                "event_success_metric": "gross_up_rate",
            },
        }
        result = StrategyTester._stats_to_result(stats, experiment_spec)

        with TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            with patch.object(
                StrategyTester,
                "_resolve_backtest_output_dir",
                return_value=output_dir,
            ):
                paths = StrategyTester._export_backtest_artifacts(
                    state=state,
                    stats=stats,
                    backtest_result=result,
                    template_family="event_parquet",
                    experiment_spec=experiment_spec,
                )

            exported_weights = pd.read_csv(paths["target_weights"])
            performance_summary = json.loads(
                Path(paths["performance_summary"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                exported_weights.columns.tolist(),
                ["trigger_ts", "code", "weight"],
            )
            self.assertEqual(len(exported_weights), 2)
            self.assertTrue(paths["target_weights"].endswith("target_weights_nonzero.csv"))
            self.assertEqual(
                performance_summary["event_success_metric"], "gross_up_rate"
            )
            self.assertEqual(
                performance_summary["event_success_metric_value"], 0.4857
            )
            self.assertEqual(
                performance_summary["event_joint_minute_hit_rate"], 0.2674
            )
            self.assertEqual(
                performance_summary["evaluation_requirements"][
                    "event_success_metric"
                ],
                "gross_up_rate",
            )

    def test_artifact_error_does_not_discard_scored_result(self) -> None:
        state = init_state(
            user_idea="keep scored result",
            max_epochs=1,
            experiment_spec={"experiment_id": "exp_keep_scored_result"},
        )
        result = StrategyTester._stats_to_result(
            {
                "annual_return": 0.10,
                "sharpe_ratio": 1.0,
                "max_drawdown": -10_000.0,
                "max_ddpercent": -0.05,
                "total_trade_count": 10,
            },
            {"capital": 1_000_000.0},
        )

        with patch.object(
            StrategyTester,
            "_export_backtest_artifacts",
            side_effect=PermissionError("read only"),
        ):
            with patch("quanta_agents.agents.strategy_tester.write_trace_json"):
                paths = StrategyTester._safe_export_backtest_artifacts(
                    state=state,
                    stats={},
                    backtest_result=result,
                    template_family="local_parquet",
                    experiment_spec={"capital": 1_000_000.0},
                )

        self.assertTrue(result.passed)
        self.assertIn("artifact_error", paths)
        self.assertTrue(any("could not be saved" in item for item in state["history"]))

    def test_run_stops_when_portfolio_dependency_missing(self) -> None:
        code = """
class StrategyTemplate:
    pass

class DemoPortfolioStrategy(StrategyTemplate):
    def on_init(self):
        pass

    def on_bars(self, bars):
        pass
"""

        state = init_state(
            user_idea="portfolio dependency missing",
            max_epochs=1,
                experiment_spec={
                    "experiment_id": "exp_portfolio_missing_dep",
                    "universe": {"type": "symbol_list", "value": ["000001.SZSE", "000002.SZSE"]},
                    "backtest_start": "2024-01-01",
                    "backtest_end": "2024-12-31",
                },
        )
        state["selected_base_class"] = "StrategyTemplate"
        state["selected_template"] = "PortfolioStrategyTemplate"
        state["code_text"] = code
        state["strategy_generation_meta"] = {}
        state["strategy_result"] = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZSE": 0.6, "000002.SZSE": 0.3, "cash": 0.1}]
            ),
            "backtest_datasets": ["vnpy_stock_daily_qfq"],
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        tester = StrategyTester()

        with patch.object(StrategyTester, "_ensure_vnpy_database_settings", return_value=Path("/tmp/vt_setting.json")):
            with patch.object(StrategyTester, "_load_available_bar_vt_symbols", return_value=[]):
                with patch.object(
                    StrategyTester,
                    "_recompute_output_weights_for_backtest",
                    return_value=(state["strategy_result"]["output_weights"], {}),
                ):
                    with patch("quanta_agents.agents.strategy_tester.importlib.import_module") as import_mock:
                        import_mock.side_effect = ModuleNotFoundError("No module named 'vnpy_portfoliostrategy'")
                        result = tester.run(state)

        self.assertEqual(result["phase"], "strategy")
        self.assertIsNone(result["test_result"])
        self.assertIn("vnpy_portfoliostrategy", result["backtest_feedback"])

    def test_resolve_template_from_output_weights_df_returns_portfolio_for_single_symbol(self) -> None:
        strategy_result = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZSE": 0.7, "cash": 0.3}]
            ),
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        family, base_class, normalized_df, columns = StrategyTester._resolve_template_from_output_weights_df(strategy_result)

        self.assertEqual(family, "portfolio")
        self.assertEqual(base_class, "StrategyTemplate")
        self.assertEqual(columns, ["000001.SZSE"])
        self.assertTrue(hasattr(normalized_df, "index"))

    def test_resolve_template_from_output_weights_df_preserves_raw_symbol_columns(self) -> None:
        strategy_result = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZ": 0.7, "cash": 0.3}]
            ),
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        family, base_class, normalized_df, columns = StrategyTester._resolve_template_from_output_weights_df(strategy_result)

        self.assertEqual(family, "portfolio")
        self.assertEqual(base_class, "StrategyTemplate")
        self.assertEqual(columns, ["000001.SZ"])
        self.assertIn("000001.SZ", list(normalized_df.columns))
        self.assertNotIn("000001.SZSE", list(normalized_df.columns))

    def test_resolve_template_from_output_weights_df_returns_portfolio_for_multi_symbol(self) -> None:
        strategy_result = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZSE": 0.5, "000002.SZSE": 0.4, "cash": 0.1}]
            ),
            "strategy_output": {"output_weights_df": {"datetime_column": "datetime"}},
        }

        family, base_class, normalized_df, columns = StrategyTester._resolve_template_from_output_weights_df(strategy_result)

        self.assertEqual(family, "portfolio")
        self.assertEqual(base_class, "StrategyTemplate")
        self.assertEqual(columns, ["000001.SZSE", "000002.SZSE"])
        self.assertTrue(hasattr(normalized_df, "index"))

    def test_resolve_template_from_output_weights_df_accepts_explicit_trade_date_column(self) -> None:
        strategy_result = {
            "output_weights": __import__("pandas").DataFrame(
                [{"trade_date": "2024-01-02", "000001.SZSE": 0.7, "cash": 0.3}]
            ),
            "strategy_output": {"output_weights_df": {"datetime_column": "trade_date"}},
        }

        family, base_class, normalized_df, columns = StrategyTester._resolve_template_from_output_weights_df(strategy_result)

        self.assertEqual(family, "portfolio")
        self.assertEqual(base_class, "StrategyTemplate")
        self.assertEqual(columns, ["000001.SZSE"])
        self.assertEqual(normalized_df.index.name, "trade_date")

    def test_resolve_template_from_output_weights_df_uses_explicit_time_column_meta(self) -> None:
        strategy_result = {
            "output_weights": __import__("pandas").DataFrame(
                [{"event_time": "2024-01-02", "000001.SZSE": 0.6, "cash": 0.4}]
            ),
            "strategy_output": {
                "output_weights_df": {
                    "datetime_column": "event_time",
                }
            },
        }

        family, base_class, normalized_df, columns = StrategyTester._resolve_template_from_output_weights_df(strategy_result)

        self.assertEqual(family, "portfolio")
        self.assertEqual(base_class, "StrategyTemplate")
        self.assertEqual(columns, ["000001.SZSE"])
        self.assertEqual(normalized_df.index.name, "event_time")

    def test_resolve_template_from_output_weights_df_rejects_missing_datetime_column_meta(self) -> None:
        strategy_result = {
            "output_weights": __import__("pandas").DataFrame(
                [{"datetime": "2024-01-02", "000001.SZSE": 0.7, "cash": 0.3}]
            )
        }

        with self.assertRaisesRegex(RuntimeError, "datetime_column"):
            StrategyTester._resolve_template_from_output_weights_df(strategy_result)
