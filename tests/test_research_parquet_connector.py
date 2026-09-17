from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quanta_agents.semantic.layer import SemanticLayer
from quanta_agents.semantic.metadata import MetadataManager, ResearchParquetConnector


def test_analysis_only_prefix_is_hidden_for_every_research_dataset() -> None:
    assert ResearchParquetConnector._is_hidden_outcome(
        "periodic_minute_events",
        "analysis_only_full_day_low_to_close_ma5_distance",
    )
    assert ResearchParquetConnector._is_hidden_outcome(
        "periodic_fourier_features_2026",
        "analysis_only_future_description",
    )


def test_research_parquet_connector_reads_named_dataset(tmp_path: Path) -> None:
    data_path = tmp_path / "events.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
            "code": ["sh600000", "sz000001"],
            "trigger_low_to_prev5_close_ma5_distance": [-0.02, 0.01],
            "analysis_only_full_day_low_to_close_ma5_distance": [-0.05, -0.01],
            "forward_5m": [0.001, -0.002],
        }
    ).to_parquet(data_path, index=False)

    connector = ResearchParquetConnector(
        {"periodic_minute_events": str(data_path)}
    )
    result = connector.execute_query(
        """
        SELECT code
        FROM periodic_minute_events
        WHERE date BETWEEN :start AND :end
        ORDER BY code
        """,
        {"start": "2025-01-01", "end": "2025-01-02 23:59:59"},
    )

    assert result.to_dict(orient="records") == [
        {"code": "sh600000"}
    ]
    schema = connector.get_table_schema("periodic_minute_events")
    assert schema["base_path"] == str(data_path)
    assert {item["name"] for item in schema["columns"]} == {
        "date",
        "code",
        "trigger_low_to_prev5_close_ma5_distance",
    }
    with pytest.raises(Exception):
        connector.execute_query(
            "SELECT forward_5m FROM periodic_minute_events"
        )
    with pytest.raises(Exception):
        connector.execute_query(
            "SELECT analysis_only_full_day_low_to_close_ma5_distance "
            "FROM periodic_minute_events"
        )


def test_event_dataset_keeps_multiple_events_on_same_stock_date(tmp_path: Path) -> None:
    data_path = tmp_path / "events.parquet"
    pd.DataFrame(
        {
            "candidate_id": ["a", "b"],
            "date": pd.to_datetime(["2025-01-02", "2025-01-02"]),
            "code": ["sh600000", "sh600000"],
            "trigger_ts": pd.to_datetime(
                ["2025-01-02 10:00:00", "2025-01-02 10:30:00"]
            ),
            "period": [2, 3],
            "forward_5m": [0.001, -0.002],
        }
    ).to_parquet(data_path, index=False)
    metadata = MetadataManager(
        {
            "datasets": [
                {
                    "table_key": "periodic_minute_events",
                    "type": "auxiliary",
                    "datetime_column": "date",
                    "symbol_column": "code",
                    "primary_keys": ["candidate_id"],
                }
            ]
        }
    )
    connector = ResearchParquetConnector(
        {"periodic_minute_events": str(data_path)}
    )
    layer = SemanticLayer(metadata, default_engine="research_parquet")
    layer._connectors["research_parquet"] = connector

    result = layer.load_auxiliary_data(
        "periodic_minute_events",
        ["trigger_ts", "period"],
        {"start": "2025-01-01", "end": "2025-01-03"},
    )

    assert result["candidate_id"].tolist() == ["a", "b"]
    assert result["period"].tolist() == [2, 3]

    escaped_path = data_path.resolve().as_posix().replace("'", "''")
    injected_field = (
        "(SELECT max(forward_5m) "
        f"FROM read_parquet('{escaped_path}')) AS leaked_future"
    )
    with pytest.raises(ValueError, match="不可用字段"):
        layer.load_auxiliary_data(
            "periodic_minute_events",
            ["trigger_ts", injected_field],
            {"start": "2025-01-01", "end": "2025-01-03"},
        )
