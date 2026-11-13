"""Validation helpers for collections of telemetry records."""

from collections.abc import Iterable

import pandas as pd

from cloudpulse.telemetry.schema import TelemetryRecord


def records_to_frame(records: Iterable[TelemetryRecord]) -> pd.DataFrame:
    """Convert validated records into a stable tabular representation."""
    materialized = list(records)
    columns = [
        "timestamp",
        "entity_id",
        "metric_name",
        "value",
        "unit",
        "source",
    ]
    if not materialized:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame([record.model_dump() for record in materialized])
    return frame.loc[:, columns].sort_values(
        ["entity_id", "metric_name", "timestamp"],
        kind="stable",
        ignore_index=True,
    )


def find_duplicate_observations(frame: pd.DataFrame) -> pd.DataFrame:
    """Return repeated entity/metric/timestamp keys without silently dropping them."""
    required = {"entity_id", "metric_name", "timestamp"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    duplicate_mask = frame.duplicated(
        subset=["entity_id", "metric_name", "timestamp"],
        keep=False,
    )
    return frame.loc[duplicate_mask].sort_values(
        ["entity_id", "metric_name", "timestamp"],
        kind="stable",
    )
