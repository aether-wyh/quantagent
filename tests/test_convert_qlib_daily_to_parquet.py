from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "convert_qlib_daily_to_parquet.py"

spec = spec_from_file_location("convert_qlib_daily_to_parquet", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _write_feature(
    directory: Path,
    name: str,
    start: int,
    values: list[float],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    np.asarray([float(start), *values], dtype="<f4").tofile(
        directory / f"{name}.day.bin"
    )


def _write_stock(
    feature_root: Path,
    code: str,
    *,
    start: int,
    rows: list[dict[str, float]],
    vwap_start: int | None = None,
    vwap_values: list[float] | None = None,
) -> None:
    directory = feature_root / code
    for name in module.REQUIRED_FEATURES:
        _write_feature(directory, name, start, [row[name] for row in rows])
    if vwap_values is not None:
        _write_feature(
            directory,
            "vwap",
            start if vwap_start is None else vwap_start,
            vwap_values,
        )


def _write_raw_daily(
    root: Path,
    code: str,
    rows: list[dict[str, object]],
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    columns = [
        "股票代码",
        "股票名称",
        "交易日期",
        "开盘价",
        "最高价",
        "最低价",
        "收盘价",
        "前收盘价",
        "成交量",
        "成交额",
        "流通市值",
        "总市值",
    ]
    payload = pd.DataFrame(rows, columns=columns).to_csv(index=False)
    (root / f"{code}.csv").write_text(
        "测试资料说明\n" + payload,
        encoding="gb18030",
    )


class ConvertQlibDailyToParquetTest(TestCase):
    def test_code_filter_accepts_only_requested_a_share_prefixes(self) -> None:
        allowed = [
            "sh600000",
            "SH601001",
            "sh603999",
            "sh605001",
            "sh688001",
            "sh689001",
            "sz000001",
            "sz001001",
            "sz002001",
            "sz003001",
            "sz300001",
            "sz301001",
            "sz302001",
        ]
        rejected = [
            "sh000300",
            "sh510050",
            "sh602001",
            "sh900901",
            "sz159001",
            "sz200001",
            "sz399001",
            "bj430001",
        ]
        self.assertTrue(all(module.is_a_share_code(code) for code in allowed))
        self.assertFalse(any(module.is_a_share_code(code) for code in rejected))

    def test_conversion_handles_offsets_missing_days_and_retired_stock(self) -> None:
        dates = [
            "2020-01-02",
            "2020-01-03",
            "2020-01-06",
            "2020-01-07",
            "2020-01-08",
            "2020-01-09",
        ]
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "qlib"
            calendar_dir = root / "calendars"
            calendar_dir.mkdir(parents=True)
            (calendar_dir / "day.txt").write_text(
                "\n".join(dates) + "\n",
                encoding="utf-8",
            )
            feature_root = root / "features"

            _write_stock(
                feature_root,
                "sh600001",
                start=1,
                rows=[
                    {"open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "volume": 100.0, "amount": 1.0, "factor": 0.5},
                    {"open": 11.0, "high": 11.5, "low": 10.5, "close": 11.2, "volume": 110.0, "amount": 2.0, "factor": 0.5},
                    {"open": 12.0, "high": np.nan, "low": 11.5, "close": 12.2, "volume": 120.0, "amount": 3.0, "factor": 0.5},
                    {"open": 13.0, "high": 13.5, "low": 12.5, "close": 13.2, "volume": 130.0, "amount": 4.0, "factor": 0.5},
                    {"open": 14.0, "high": 14.5, "low": 13.5, "close": 14.2, "volume": 140.0, "amount": 5.0, "factor": 0.5},
                ],
                vwap_start=2,
                vwap_values=[11.1, 12.1, 13.1, 14.1],
            )
            # 这只股票在日历结束前已经没有数据，仍应保留已有历史。
            _write_stock(
                feature_root,
                "sz000001",
                start=0,
                rows=[
                    {"open": 20.0, "high": 20.5, "low": 19.5, "close": 20.2, "volume": 200.0, "amount": 6.0, "factor": 0.25},
                    {"open": 21.0, "high": 21.5, "low": 20.5, "close": 21.2, "volume": 210.0, "amount": 7.0, "factor": 0.25},
                    {"open": 22.0, "high": 22.5, "low": 21.5, "close": 22.2, "volume": 220.0, "amount": 8.0, "factor": 0.25},
                ],
            )
            # 指数或基金目录即便具备同名文件，也不能进入结果。
            _write_stock(
                feature_root,
                "sh510050",
                start=0,
                rows=[
                    {"open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 10.0, "amount": 1.0, "factor": 1.0},
                ],
            )

            output_dir = Path(tmp_dir) / "parquet"
            summaries = module.convert_qlib_daily_to_parquet(
                root,
                output_dir,
                start_date="2020-01-06",
                end_date="2020-01-09",
            )

            self.assertEqual([summary.code for summary in summaries], ["sh600001", "sz000001"])
            self.assertEqual([summary.rows for summary in summaries], [3, 1])
            self.assertEqual(
                sorted(path.name for path in output_dir.glob("*.parquet")),
                ["sh600001.parquet", "sz000001.parquet"],
            )

            sh = pd.read_parquet(output_dir / "sh600001.parquet")
            self.assertEqual(tuple(sh.columns), module.OUTPUT_COLUMNS)
            self.assertEqual(
                sh["date"].dt.strftime("%Y-%m-%d").tolist(),
                ["2020-01-06", "2020-01-08", "2020-01-09"],
            )
            self.assertEqual(sh["code"].tolist(), ["sh600001"] * 3)
            np.testing.assert_allclose(sh["prev_close"], [20.4, 22.4, 26.4])
            self.assertEqual(sh["volume"].tolist(), [5500.0, 6500.0, 7000.0])
            self.assertEqual(sh["amount"].tolist(), [2000.0, 4000.0, 5000.0])
            self.assertAlmostEqual(float(sh["close"].iloc[0]), 22.4, places=5)
            self.assertAlmostEqual(float(sh["vwap_qfq"].iloc[0]), 22.2, places=5)
            self.assertTrue((sh["qfq_ratio"] == 1.0).all())
            for column in module.NULLABLE_CONNECTOR_COLUMNS:
                self.assertTrue(sh[column].isna().all(), column)

            retired = pd.read_parquet(output_dir / "sz000001.parquet")
            self.assertEqual(retired["date"].dt.strftime("%Y-%m-%d").tolist(), ["2020-01-06"])
            self.assertAlmostEqual(float(retired["prev_close"].iloc[0]), 84.8, places=5)
            self.assertEqual(float(retired["volume"].iloc[0]), 5500.0)
            self.assertEqual(float(retired["amount"].iloc[0]), 8000.0)
            self.assertTrue(retired["vwap_qfq"].isna().all())

            manifest = json.loads(
                (output_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["source_root"], str(root.resolve()))
            self.assertEqual(
                manifest["date_range"],
                {"start": "2020-01-06", "end": "2020-01-09"},
            )
            self.assertEqual(
                manifest["actual_date_range"],
                {"start": "2020-01-06", "end": "2020-01-09"},
            )
            self.assertEqual(manifest["stock_count"], 2)
            self.assertEqual(manifest["stock_file_count"], 2)
            self.assertEqual(manifest["row_count"], 4)
            self.assertEqual(
                manifest["available_fields"],
                ["open", "high", "low", "close", "volume", "amount", "prev_close"],
            )
            self.assertEqual(manifest["stock_filter"]["exchanges"], ["SH", "SZ"])

    def test_feature_header_uses_calendar_position(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "close.day.bin"
            _write_feature(Path(tmp_dir), "close", 2, [3.0, np.nan, 5.0])
            calendar = pd.date_range("2020-01-01", periods=5, freq="D")

            result = module.read_day_feature(path, calendar)

        self.assertEqual(result.index.tolist(), calendar[2:].tolist())
        self.assertEqual(float(result.iloc[0]), 3.0)
        self.assertTrue(np.isnan(result.iloc[1]))
        self.assertEqual(float(result.iloc[2]), 5.0)

    def test_conversion_strictly_merges_raw_daily_fields(self) -> None:
        dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "qlib"
            calendar_dir = root / "calendars"
            calendar_dir.mkdir(parents=True)
            (calendar_dir / "day.txt").write_text(
                "\n".join(dates) + "\n",
                encoding="utf-8",
            )
            _write_stock(
                root / "features",
                "sh600001",
                start=0,
                rows=[
                    {"open": 5.0, "high": 5.2, "low": 4.9, "close": 5.1, "volume": 10.0, "amount": 1.0, "factor": 0.5},
                    {"open": 5.1, "high": 5.3, "low": 5.0, "close": 5.2, "volume": 11.0, "amount": 1.1, "factor": 0.5},
                    {"open": 4.8, "high": 5.0, "low": 4.7, "close": 4.9, "volume": 12.0, "amount": 1.2, "factor": 0.55},
                ],
            )
            raw_root = Path(tmp_dir) / "raw"
            _write_raw_daily(
                raw_root,
                "sh600001",
                [
                    {"股票代码": "sh600001", "股票名称": "普通公司", "交易日期": dates[0], "开盘价": 10.0, "最高价": 10.4, "最低价": 9.8, "收盘价": 10.2, "前收盘价": 10.0, "成交量": 1000, "成交额": 10000, "流通市值": 100000, "总市值": 200000},
                    {"股票代码": "sh600001", "股票名称": " * S T 测试", "交易日期": dates[1], "开盘价": 10.2, "最高价": 10.6, "最低价": 10.0, "收盘价": 10.4, "前收盘价": 10.2, "成交量": 1100, "成交额": 11000, "流通市值": 101000, "总市值": 201000},
                    {"股票代码": "sh600001", "股票名称": "测试退", "交易日期": dates[2], "开盘价": 8.8, "最高价": 9.1, "最低价": 8.7, "收盘价": 8.9, "前收盘价": 9.3, "成交量": 1200, "成交额": 12000, "流通市值": 90000, "总市值": 180000},
                ],
            )
            output_dir = Path(tmp_dir) / "parquet"

            module.convert_qlib_daily_to_parquet(
                root,
                output_dir,
                raw_daily_root=raw_root,
            )

            result = pd.read_parquet(output_dir / "sh600001.parquet")
            self.assertEqual(
                tuple(result.columns),
                (*module.OUTPUT_COLUMNS, *module.RAW_DAILY_OUTPUT_COLUMNS),
            )
            np.testing.assert_allclose(result["raw_open"], [10.0, 10.2, 8.8])
            np.testing.assert_allclose(result["raw_prev_close"], [10.0, 10.2, 9.3])
            self.assertEqual(result["stock_name"].tolist(), ["普通公司", " * S T 测试", "测试退"])
            self.assertEqual(result["is_st"].tolist(), [False, True, False])
            self.assertEqual(result["is_delisting"].tolist(), [False, False, True])
            np.testing.assert_allclose(result["float_market_cap"], [100000, 101000, 90000])
            np.testing.assert_allclose(result["total_market_cap"], [200000, 201000, 180000])
            np.testing.assert_allclose(
                result["float_shares"],
                np.asarray([100000, 101000, 90000]) / np.asarray([10.2, 10.4, 8.9]),
            )
            np.testing.assert_allclose(
                result["total_shares"],
                np.asarray([200000, 201000, 180000]) / np.asarray([10.2, 10.4, 8.9]),
            )

            manifest = json.loads(
                (output_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["raw_daily"],
                {
                    "source_root": str(raw_root.resolve()),
                    "qlib_candidate_row_count": 3,
                    "required_row_count": 3,
                    "matched_row_count": 3,
                    "match_rate": 1.0,
                    "outside_range_dropped_row_count": 0,
                    "outside_range_dropped_codes": [],
                },
            )
            self.assertEqual(
                manifest["available_fields"],
                [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                    "prev_close",
                    "raw_prev_close",
                    "is_st",
                    "is_delisting",
                    "float_shares",
                    "total_shares",
                    "float_market_cap",
                    "total_market_cap",
                ],
            )

    def test_raw_daily_merge_rejects_missing_invalid_or_empty_required_values(self) -> None:
        qlib_frame = pd.DataFrame(
            {
                **{column: [np.nan] for column in module.OUTPUT_COLUMNS},
                "date": [pd.Timestamp("2020-01-02")],
                "code": ["sh600001"],
            }
        ).loc[:, module.OUTPUT_COLUMNS]
        base_row = {
            "股票代码": "sh600001",
            "股票名称": "普通公司",
            "交易日期": "2020-01-02",
            "开盘价": 10.0,
            "最高价": 10.2,
            "最低价": 9.8,
            "收盘价": 10.1,
            "前收盘价": 9.9,
            "成交量": 1000,
            "成交额": 10000,
            "流通市值": 100000,
            "总市值": 200000,
        }
        cases = [
            ("invalid_open", {**base_row, "开盘价": 0.0}, "raw_open"),
            ("invalid_close", {**base_row, "收盘价": 0.0}, "raw_close"),
            ("invalid_prev_close", {**base_row, "前收盘价": np.nan}, "raw_prev_close"),
            ("invalid_float_market_cap", {**base_row, "流通市值": 0.0}, "float_market_cap"),
            ("invalid_total_market_cap", {**base_row, "总市值": -1.0}, "total_market_cap"),
            ("empty_name", {**base_row, "股票名称": "   "}, "股票名称为空"),
        ]
        for case_name, raw_row, error_pattern in cases:
            with self.subTest(case=case_name), TemporaryDirectory() as tmp_dir:
                raw_root = Path(tmp_dir)
                _write_raw_daily(raw_root, "sh600001", [raw_row])
                with self.assertRaisesRegex(ValueError, error_pattern):
                    module.merge_raw_daily_frame(
                        qlib_frame,
                        raw_root,
                        "sh600001",
                    )

    def test_parse_args_accepts_optional_raw_daily_root(self) -> None:
        args = module.parse_args(["--raw-daily-root", "raw-daily"])
        self.assertEqual(args.raw_daily_root, "raw-daily")

    def test_st_name_rules_cover_historical_and_quote_prefixes(self) -> None:
        names = pd.Series(
            [
                "普通公司",
                "测试ST公司",
                "XD普通公司",
                "N普通公司",
                "ST甲",
                "*ST乙",
                "SST佳通",
                "S*ST佳通",
                "XDST海越",
                "XD * S T 华",
                "XRST甲",
                "XR*ST乙",
                "DRST丙",
                "DR*ST丁",
                "NST毅达",
            ],
            dtype="string",
        )

        result = module.classify_is_st_names(names)

        self.assertEqual(
            result.tolist(),
            [False, False, False, False] + [True] * 11,
        )

    def test_raw_daily_range_removes_copied_history_but_keeps_strict_inner_dates(self) -> None:
        dates = [
            "2015-01-05",
            "2015-01-06",
            "2018-02-27",
            "2018-02-28",
            "2018-03-01",
        ]
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "qlib"
            calendar_dir = root / "calendars"
            calendar_dir.mkdir(parents=True)
            (calendar_dir / "day.txt").write_text(
                "\n".join(dates) + "\n",
                encoding="utf-8",
            )
            _write_stock(
                root / "features",
                "sh601360",
                start=0,
                rows=[
                    {"open": 5.0, "high": 5.2, "low": 4.9, "close": 5.1, "volume": 10.0, "amount": 1.0, "factor": 0.5},
                    {"open": 5.1, "high": 5.3, "low": 5.0, "close": 5.2, "volume": 11.0, "amount": 1.1, "factor": 0.5},
                    {"open": 6.0, "high": 6.2, "low": 5.9, "close": 6.1, "volume": 12.0, "amount": 1.2, "factor": 0.6},
                    {"open": 6.1, "high": 6.3, "low": 6.0, "close": 6.2, "volume": 13.0, "amount": 1.3, "factor": 0.6},
                    {"open": 6.2, "high": 6.4, "low": 6.1, "close": 6.3, "volume": 14.0, "amount": 1.4, "factor": 0.6},
                ],
            )
            raw_rows = [
                {"股票代码": "sh601360", "股票名称": "三六零", "交易日期": dates[2], "开盘价": 10.0, "最高价": 10.3, "最低价": 9.9, "收盘价": 10.2, "前收盘价": 10.0, "成交量": 1000, "成交额": 10000, "流通市值": 102000, "总市值": 204000},
                {"股票代码": "sh601360", "股票名称": "三六零", "交易日期": dates[3], "开盘价": 10.2, "最高价": 10.5, "最低价": 10.1, "收盘价": 10.4, "前收盘价": 10.2, "成交量": 1100, "成交额": 11000, "流通市值": 104000, "总市值": 208000},
                {"股票代码": "sh601360", "股票名称": "三六零", "交易日期": dates[4], "开盘价": 10.4, "最高价": 10.7, "最低价": 10.3, "收盘价": 10.6, "前收盘价": 10.4, "成交量": 1200, "成交额": 12000, "流通市值": 106000, "总市值": 212000},
            ]
            raw_root = Path(tmp_dir) / "raw"
            _write_raw_daily(raw_root, "sh601360", raw_rows)
            output_dir = Path(tmp_dir) / "output"

            summaries = module.convert_qlib_daily_to_parquet(
                root,
                output_dir,
                raw_daily_root=raw_root,
            )

            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].rows, 3)
            self.assertEqual(summaries[0].raw_outside_range_dropped_rows, 2)
            result = pd.read_parquet(output_dir / "sh601360.parquet")
            self.assertEqual(
                result["date"].dt.strftime("%Y-%m-%d").tolist(),
                dates[2:],
            )
            self.assertEqual(result["stock_name"].tolist(), ["三六零"] * 3)
            manifest = json.loads(
                (output_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["raw_daily"]["qlib_candidate_row_count"], 5)
            self.assertEqual(manifest["raw_daily"]["required_row_count"], 3)
            self.assertEqual(
                manifest["raw_daily"]["outside_range_dropped_row_count"],
                2,
            )
            self.assertEqual(
                manifest["raw_daily"]["outside_range_dropped_codes"],
                ["sh601360"],
            )

            missing_root = Path(tmp_dir) / "raw_missing_inner_date"
            _write_raw_daily(
                missing_root,
                "sh601360",
                [raw_rows[0], raw_rows[2]],
            )
            with self.assertRaisesRegex(ValueError, "没有匹配"):
                module.convert_qlib_daily_to_parquet(
                    root,
                    Path(tmp_dir) / "missing_output",
                    raw_daily_root=missing_root,
                )

    def test_end_date_uses_the_last_factor_inside_output_period(self) -> None:
        dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "qlib"
            calendar_dir = root / "calendars"
            calendar_dir.mkdir(parents=True)
            (calendar_dir / "day.txt").write_text(
                "\n".join(dates) + "\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "open": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "close": 1.0,
                    "volume": 10.0,
                    "amount": 1.0,
                    "factor": 0.5,
                },
                {
                    "open": 1.1,
                    "high": 1.1,
                    "low": 1.1,
                    "close": 1.1,
                    "volume": 10.0,
                    "amount": 1.0,
                    "factor": 0.5,
                },
                {
                    "open": 2.4,
                    "high": 2.4,
                    "low": 2.4,
                    "close": 2.4,
                    "volume": 10.0,
                    "amount": 1.0,
                    "factor": 1.0,
                },
            ]
            _write_stock(root / "features", "sh600001", start=0, rows=rows)

            result = module.load_stock_frame(
                root / "features" / "sh600001",
                module.read_day_calendar(root),
                end_date="2020-01-03",
            )

        np.testing.assert_allclose(result["close"], [2.0, 2.2])
        np.testing.assert_allclose(result["qfq_ratio"], [1.0, 1.0])

    def test_stock_listed_after_end_date_returns_empty_frame(self) -> None:
        dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "qlib"
            calendar_dir = root / "calendars"
            calendar_dir.mkdir(parents=True)
            (calendar_dir / "day.txt").write_text(
                "\n".join(dates) + "\n",
                encoding="utf-8",
            )
            _write_stock(
                root / "features",
                "sh600001",
                start=2,
                rows=[
                    {
                        "open": 1.0,
                        "high": 1.0,
                        "low": 1.0,
                        "close": 1.0,
                        "volume": 10.0,
                        "amount": 1.0,
                        "factor": 0.5,
                    }
                ],
            )

            result = module.load_stock_frame(
                root / "features" / "sh600001",
                module.read_day_calendar(root),
                end_date="2020-01-03",
            )

        self.assertTrue(result.empty)
        self.assertEqual(tuple(result.columns), module.OUTPUT_COLUMNS)


if __name__ == "__main__":
    import unittest

    unittest.main()
