"""Auxiliary source attachment tests use generated values exclusively."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from quanta_agents.meta_v6.auxiliary import (
    HF0280_FIELDS, load_auxiliary_panel, register_auxiliary_source,
)
from quanta_agents.meta_v6.data import MarketPanel, PanelError


class AuxiliaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.cache = self.root / "cache"
        self.dates = pd.bdate_range("2015-01-05", periods=3)
        self.codes = ["sh600001", "sh600002"]
        self.start, self.end = "2015-01-01", "2015-01-07"
        self.panel = self.make_panel()

    def make_panel(self):
        cols = pd.Index(self.codes, name="symbol")
        dates = self.dates.rename("date")
        fields = {"open": pd.DataFrame(10., index=dates, columns=cols),
                  "close": pd.DataFrame(10.5, index=dates, columns=cols),
                  "raw_open": pd.DataFrame(20., index=dates, columns=cols),
                  "amount": pd.DataFrame(1000., index=dates, columns=cols)}
        fields.update({name: pd.DataFrame(np.nan, index=dates, columns=cols) for name in HF0280_FIELDS})
        eligible = pd.DataFrame(True, index=dates, columns=cols)
        eligible.iloc[1, 0] = False
        return MarketPanel(fields, eligible, {"request": {"start": self.start, "end": self.end},
            "source_class": "previously_exposed_development", "causal_fields": ["open", "close", "amount"],
            "execution_only_fields": ["raw_open"], "price_basis": {"signal": "fixed starting anchor"}})

    def write_source(self, code="sh600001", dates=None, overrides=None, only=None):
        dates = self.dates if dates is None else dates
        fields = HF0280_FIELDS if only is None else only
        values = {"date": dates, "code": [code] * len(dates)}
        values.update({name: np.arange(len(dates), dtype=float) + i for i, name in enumerate(fields)})
        values.update(overrides or {})
        pq.write_table(pa.Table.from_pandas(pd.DataFrame(values), preserve_index=False), self.source / (code + ".parquet"))

    def register(self, **kwargs):
        options = dict(symbols=self.codes, start=self.start, end=self.end,
                       authorized_start=self.start, authorized_end=self.end)
        options.update(kwargs)
        return register_auxiliary_source(self.source, **options)

    def admission(self, registry):
        return {"registration_id": registry["registration_id"],
                "base_panel_fingerprint": self.panel.fingerprint(),
                "authorized_start": self.start, "authorized_end": self.end,
                "fields": registry["fields"], "purpose": "generated fixture verification",
                "authorization_reference": "unit-test-generated-values-only"}

    def load(self, registry, **kwargs):
        options = dict(admission=self.admission(registry), cache_dir=self.cache)
        options.update(kwargs)
        return load_auxiliary_panel(self.panel, registry, **options)

    def test_registration_never_decodes_market_value_arrays(self):
        self.write_source()
        with patch("quanta_agents.meta_v6.auxiliary.pq.read_table", side_effect=AssertionError("numeric decode")):
            registry = self.register()
        self.assertFalse(registry["market_value_arrays_read"])
        self.assertEqual(registry["metadata_summary"]["missing_symbols"], ["sh600002"])
        self.assertFalse(registry["timing"]["historical_available_at_verified"])

    def test_numeric_load_requires_explicit_source_and_panel_admission(self):
        self.write_source()
        registry = self.register()
        with patch("quanta_agents.meta_v6.auxiliary.pq.read_table", side_effect=AssertionError("numeric decode")):
            with self.assertRaisesRegex(PanelError, "admission"):
                self.load(registry, admission={})
            wrong = self.admission(registry)
            wrong["base_panel_fingerprint"] = "wrong"
            with self.assertRaisesRegex(PanelError, "another base panel"):
                self.load(registry, admission=wrong)

    def test_exact_join_preserves_base_prices_eligibility_and_missing_universe(self):
        self.write_source(dates=self.dates.delete(1))
        registry = self.register()
        base_identity = self.panel.fingerprint()
        result = self.load(registry)
        self.assertEqual(result.symbols, self.codes)
        self.assertTrue(np.isnan(result.fields["gu_1m"].iloc[1, 0]))
        self.assertEqual(result.fields["gu_1m"].iloc[0, 0], 0.)
        self.assertTrue(result.fields["gu_1m"]["sh600002"].isna().all())
        pd.testing.assert_frame_equal(result.eligible, self.panel.eligible)
        for name in ["open", "close", "raw_open", "amount"]:
            pd.testing.assert_frame_equal(result.fields[name], self.panel.fields[name])
        self.assertEqual(self.panel.fingerprint(), base_identity)
        self.assertNotEqual(result.fingerprint(), base_identity)

    def test_only_seven_fields_allowed_and_existing_observations_not_overwritten(self):
        with self.assertRaisesRegex(PanelError, "seven HF0280"):
            self.register(fields=["open"])
        self.write_source()
        registry = self.register()
        self.panel.fields["gu_1m"].iloc[0, 0] = 42.
        with self.assertRaisesRegex(PanelError, "overwrite existing"):
            self.load(registry)

    def test_same_row_group_2025_values_absent_from_output_cache_and_stats(self):
        dates = self.dates.append(pd.DatetimeIndex(["2025-01-01"]))
        self.write_source(dates=dates, overrides={name: [1., 2., 3., 123456789.] for name in HF0280_FIELDS})
        registry = self.register()
        result = self.load(registry)
        self.assertEqual(result.fields["gu_1m"].max().max(), 3.)
        self.assertEqual(result.provenance["auxiliary"]["nonmissing_stock_days"]["gu_1m"], 3)
        self.assertEqual(result.provenance["auxiliary"]["source_quality"]["sh600001"]["returned_rows"], 3)
        cached = self.load(registry)
        self.assertTrue(cached.load_metrics["cache_hit"])
        self.assertEqual(cached.fingerprint(), result.fingerprint())

    def test_cache_reuse_never_reloads_source_values_and_isolates_mutation(self):
        self.write_source()
        registry = self.register()
        result = self.load(registry)
        fingerprint = result.fingerprint()
        result.fields["gu_1m"].iloc[0, 0] = 9999.
        with patch("quanta_agents.meta_v6.auxiliary.pq.read_table", side_effect=AssertionError("numeric decode")):
            cached = self.load(registry)
        self.assertEqual(cached.fingerprint(), fingerprint)

    def test_changed_source_and_forged_registry_are_rejected(self):
        self.write_source()
        registry = self.register()
        changed = deepcopy(registry)
        changed["source_notes"] = "forged"
        with self.assertRaisesRegex(PanelError, "registry identity"):
            self.load(changed)
        self.write_source(overrides={"gu_1m": [11., 12., 13.]})
        with self.assertRaisesRegex(PanelError, "source changed"):
            self.load(registry)

    def test_missing_columns_remain_nan_and_infinite_values_are_disclosed(self):
        self.write_source(only=["gu_1m"], overrides={"gu_1m": [np.inf, 0., -1.]})
        registry = self.register()
        result = self.load(registry)
        self.assertTrue(result.fields["gd_1m"].isna().all().all())
        self.assertTrue(np.isnan(result.fields["gu_1m"].iloc[0, 0]))
        self.assertEqual(result.fields["gu_1m"].iloc[2, 0], -1.)
        self.assertEqual(result.provenance["auxiliary"]["source_quality"]["sh600001"]["infinite_values_replaced_with_missing"]["gu_1m"], 1)

    def test_duplicate_foreign_code_and_off_calendar_rows_are_rejected(self):
        self.write_source(dates=self.dates[:2].append(self.dates[:1]))
        with self.assertRaisesRegex(PanelError, "duplicate"):
            self.load(self.register())
        self.write_source(overrides={"code": ["sh600002"] * 3})
        with self.assertRaisesRegex(PanelError, "foreign code"):
            self.load(self.register())
        self.write_source(dates=pd.DatetimeIndex(["2015-01-03"]))
        with self.assertRaisesRegex(PanelError, "calendar"):
            self.load(self.register())

    def test_dates_and_universe_cannot_expand(self):
        self.write_source()
        with self.assertRaisesRegex(PanelError, "authorization"):
            self.register(end="2025-12-31")
        registry = self.register(symbols=self.codes[:1])
        with self.assertRaisesRegex(PanelError, "universe"):
            self.load(registry)
        registry = self.register()
        admission = self.admission(registry)
        admission["authorized_end"] = "2025-12-31"
        with self.assertRaisesRegex(PanelError, "dates exceed"):
            self.load(registry, admission=admission)

    def test_no_sixteen_stock_or_512_session_limit(self):
        self.codes = ["sh" + str(600001 + i) for i in range(17)]
        self.dates = pd.bdate_range("2015-01-05", periods=520)
        self.end = str(self.dates[-1].date())
        self.panel = self.make_panel()
        self.write_source()
        registry = self.register()
        result = self.load(registry, cache_dir=None)
        self.assertEqual(result.fields["gu_1m"].shape, (520, 17))
        self.assertEqual(registry["metadata_summary"]["present_files"], 1)


if __name__ == "__main__":
    unittest.main()
