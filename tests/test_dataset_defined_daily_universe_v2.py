from __future__ import annotations

from types import MethodType

import pandas as pd

from quanta_agents.semantic.layer import SemanticLayer


def test_required_daily_data_accepts_dataset_defined_universe() -> None:
    normalized = SemanticLayer._normalize_required_universe(
        {"type": "dataset_defined", "value": "stock_kline_daily_qfq"},
        prefix="required_data[0]",
    )

    assert normalized == {
        "type": "dataset_defined",
        "value": "stock_kline_daily_qfq",
    }


def test_dataset_defined_daily_data_loads_all_rows_without_symbol_filter() -> None:
    layer = object.__new__(SemanticLayer)
    captured: dict[str, object] = {}

    def fake_get_connector(self: SemanticLayer, dataset_name: str) -> object:
        captured["connector_dataset"] = dataset_name
        return object()

    def fake_fetch_data(
        self: SemanticLayer,
        *,
        dataset: str,
        fields: list[str],
        start_date: str,
        end_date: str,
        symbols: list[str] | None,
        vt_symbol_format: bool,
    ) -> pd.DataFrame:
        captured.update(
            {
                "dataset": dataset,
                "fields": fields,
                "start_date": start_date,
                "end_date": end_date,
                "symbols": symbols,
                "vt_symbol_format": vt_symbol_format,
            }
        )
        return pd.DataFrame({"code": ["000001.SZ"]})

    layer._get_connector = MethodType(fake_get_connector, layer)
    layer.fetch_data = MethodType(fake_fetch_data, layer)

    result = layer.load_time_series_data(
        "stock_kline_daily_qfq",
        ["open", "close"],
        {"start": "2020-01-01", "end": "2020-12-31"},
        {"type": "dataset_defined", "value": "stock_kline_daily_qfq"},
    )

    assert result["code"].tolist() == ["000001.SZ"]
    assert captured["symbols"] is None
    assert captured["dataset"] == "stock_kline_daily_qfq"
