"""Generated data checks only; no historical market data or model calls."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from quanta_agents.meta_v6.data import (
    MarketPanel, PanelError, historical_universe, inspect_parquet_sources,
    load_market_panel,
)


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.dates = pd.bdate_range("2020-01-01", periods=6)
        self.calendar = self.root / "calendar.txt"
        self.members = self.root / "membership.txt"
        self.cache = self.root / "cache"
        self.set_calendar(self.dates)
        self.members.write_text("SH600001 2020-01-01 2020-01-31\n", encoding="utf-8")

    def set_calendar(self, dates):
        self.calendar.write_text("\n".join(dates.strftime("%Y-%m-%d")) + "\n", encoding="utf-8")

    def write_stock(self, code="sh600001", dates=None, ratio=None, **overrides):
        dates = self.dates if dates is None else dates
        n = len(dates)
        ratio = np.full(n, .5) if ratio is None else np.array(ratio, dtype=float)
        raw = np.arange(n, dtype=float) + 10
        values = {"date": dates, "code": [code] * n, "open": raw * ratio,
                  "high": (raw + 1) * ratio, "low": (raw - 1) * ratio,
                  "close": (raw + .5) * ratio, "volume": np.full(n, 1000.),
                  "amount": np.full(n, 10000.), "qfq_ratio": ratio,
                  "raw_open": raw, "raw_prev_close": raw - .5}
        values.update(overrides)
        pq.write_table(pa.Table.from_pandas(pd.DataFrame(values), preserve_index=False),
                       self.source / (code + ".parquet"))

    def load(self, **kwargs):
        options = dict(start=self.dates[0], end=self.dates[-1],
                       authorized_start=self.dates[0], authorized_end=self.dates[-1],
                       calendar_path=self.calendar, membership_path=self.members,
                       optional_fields=(), cache_dir=self.cache)
        options.update(kwargs)
        return load_market_panel(self.source, **options)

    def test_fixed_starting_anchor_separates_signal_from_raw(self):
        self.write_stock(ratio=[.5, .5, 1, 1, 1, 1])
        result = self.load()
        np.testing.assert_allclose(result.fields["open"].iloc[:, 0], [10, 11, 24, 26, 28, 30])
        np.testing.assert_allclose(result.fields["raw_open"].iloc[:, 0], [10, 11, 12, 13, 14, 15])
        np.testing.assert_allclose(result.fields["raw_close"].iloc[:, 0], np.arange(6) + 10.5)
        np.testing.assert_allclose(result.fields["adjustment_factor"].iloc[:, 0], [.9999999999999999, 1, 2, 2, 2, 2])
        self.assertTrue(result.eligible.to_numpy().all())
        self.assertFalse(result.provenance["execution_certified"])

    def test_uniform_qfq_rescaling_does_not_change_signal_prices(self):
        self.write_stock(ratio=[.5] * 6)
        first = self.load()
        self.write_stock(ratio=[.25] * 6)
        second = self.load()
        pd.testing.assert_frame_equal(first.fields["close"], second.fields["close"])
        self.assertNotEqual(first.provenance["cache_key"], second.provenance["cache_key"])

    def test_missing_rows_files_and_optional_fields_are_not_filled(self):
        self.write_stock(dates=self.dates.delete(2))
        self.members.write_text("SH600001 2020-01-01 2020-01-31\nSH600002 2020-01-01 2020-01-31\n")
        result = self.load(optional_fields=("gu_1m",))
        self.assertTrue(np.isnan(result.fields["close"].loc[self.dates[2], "sh600001"]))
        self.assertFalse(result.eligible.loc[self.dates[2], "sh600001"])
        self.assertFalse(result.eligible["sh600002"].any())
        self.assertTrue(result.fields["gu_1m"].isna().all().all())
        self.assertEqual(result.fields["bar_observed"].loc[self.dates[2], "sh600001"], 0)
        self.assertEqual(result.eligible["sh600001"].sum(), 5)

    def test_membership_uses_signal_date_inclusive_intervals(self):
        self.write_stock()
        self.members.write_text("SH600001 2020-01-02 2020-01-03\nSH600001 2020-01-08 2020-01-08\n")
        result = self.load()
        self.assertEqual(result.eligible["sh600001"].tolist(), [False, True, True, False, False, True])
        self.assertEqual(historical_universe(self.members, start="2020-01-01", end="2020-01-08"), ["sh600001"])

    def test_authorization_rejects_before_source_read(self):
        with patch("quanta_agents.meta_v6.data.inspect_parquet_sources", side_effect=AssertionError("source accessed")):
            with self.assertRaisesRegex(PanelError, "authorization"):
                self.load(end="2025-01-01")

    def test_retired_legacy_metadata_outside_scope_not_silently_selected(self):
        self.write_stock()
        self.members.write_text("SHT00018 2005-04-08 2007-01-03\nSH600001 2020-01-01 2020-01-31\n")
        self.assertEqual(self.load().symbols, ["sh600001"])
        self.members.write_text("SHT00018 2020-01-01 2020-01-31\n")
        with self.assertRaisesRegex(PanelError, "canonical stock code"):
            self.load()

    def test_same_row_group_future_data_never_returned_or_cached(self):
        # Deliberately distinctive out-of-scope numerical sentinel in same row group.
        all_dates = self.dates.append(pd.DatetimeIndex(["2025-01-01"]))
        self.write_stock(dates=all_dates, volume=[1000.] * 6 + [123456789.])
        result = self.load()
        self.assertEqual(len(result.dates), 6)
        self.assertEqual(result.provenance["missing"]["source_quality"]["sh600001"]["returned_rows"], 6)
        self.assertEqual(result.fields["volume"].max().max(), 1000.)
        cached = self.load()
        self.assertEqual(cached.fingerprint(), result.fingerprint())
        self.assertIn("storage pages may overlap", result.provenance["range_isolation"])

    def test_cache_reuses_source_values_and_returned_mutation_isolated(self):
        self.write_stock()
        result = self.load()
        fingerprint = result.fingerprint()
        result.fields["close"].iloc[0, 0] = 999
        with patch("quanta_agents.meta_v6.data.pq.read_table", side_effect=AssertionError("source values reloaded")):
            cached = self.load()
        self.assertEqual(cached.fingerprint(), fingerprint)
        self.assertTrue(cached.load_metrics["cache_hit"])
        self.assertFalse(cached.load_metrics["market_values_reloaded_on_cache_hit"])

    def test_corrupt_cache_is_rejected(self):
        self.write_stock()
        result = self.load()
        payload = self.cache / result.provenance["cache_key"] / "panel.npz"
        with payload.open("ab") as stream:
            stream.write(b"corrupted")
        with self.assertRaisesRegex(PanelError, "payload hash"):
            self.load()

    def test_duplicate_foreign_code_invalid_ratio_and_broken_ohlc(self):
        self.write_stock(dates=self.dates[:5].append(self.dates[:1]))
        with self.assertRaisesRegex(PanelError, "duplicate"):
            self.load()
        self.write_stock(code="sh600001", qfq_ratio=[.5, 0, .5, .5, .5, .5], high=[5., 6., 7., 8., 9., 10.])
        result = self.load()
        self.assertFalse(result.eligible.iloc[0, 0])
        self.assertFalse(result.eligible.iloc[1, 0])
        self.assertTrue(np.isnan(result.fields["close"].iloc[1, 0]))
        frame = pq.read_table(self.source / "sh600001.parquet").to_pandas()
        frame.loc[0, "code"] = "sz000001"
        pq.write_table(pa.Table.from_pandas(frame), self.source / "sh600001.parquet")
        with self.assertRaisesRegex(PanelError, "foreign stock"):
            self.load()

    def test_metadata_inventory_does_not_load_numeric_arrays(self):
        self.write_stock()
        with patch("quanta_agents.meta_v6.data.pq.read_table", side_effect=AssertionError("numeric read")):
            result = inspect_parquet_sources(self.source, ["sh600001", "sh600002"])
        self.assertEqual(result[0]["rows_in_file"], 6)
        self.assertEqual(result[1]["status"], "missing")

    def test_no_sixteen_stock_or_512_day_limit(self):
        self.dates = pd.bdate_range("2017-01-02", periods=600)
        self.set_calendar(self.dates)
        symbols = ["sh" + str(600000 + i) for i in range(20)]
        for code in symbols:
            self.write_stock(code=code)
        result = self.load(membership_path=None, symbols=symbols, cache_dir=None)
        self.assertEqual(result.eligible.shape, (600, 20))
        self.assertEqual(result.eligible.to_numpy().sum(), 12000)

    def test_panel_rejects_misaligned_axes(self):
        dates = self.dates[:2]
        valid = pd.DataFrame(True, index=dates, columns=["sh600001"])
        values = pd.DataFrame(1., index=self.dates[:1], columns=["sh600001"])
        with self.assertRaisesRegex(PanelError, "identical axes"):
            MarketPanel({"close": values}, valid, {})


if __name__ == "__main__":
    unittest.main()
