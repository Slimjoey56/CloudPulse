from datetime import UTC, datetime

import pandas as pd
import pytest

from cloudpulse.telemetry.schema import TelemetryRecord
from cloudpulse.telemetry.validation import (
    find_duplicate_observations,
    records_to_frame,
)


def _record(timestamp: datetime, value: float = 1.0) -> TelemetryRecord:
    return TelemetryRecord(
        timestamp=timestamp,
        entity_id="node-a",
        metric_name="cpu",
        value=value,
        unit="percent",
    )


def test_records_to_frame_sorts_by_entity_metric_and_time() -> None:
    later = datetime(2026, 1, 2, tzinfo=UTC)
    earlier = datetime(2026, 1, 1, tzinfo=UTC)

    frame = records_to_frame([_record(later), _record(earlier)])

    assert list(frame["timestamp"]) == [earlier, later]


def test_records_to_frame_handles_empty_input() -> None:
    frame = records_to_frame([])

    assert list(frame.columns) == [
        "timestamp",
        "entity_id",
        "metric_name",
        "value",
        "unit",
        "source",
    ]
    assert frame.empty


def test_duplicate_detector_flags_all_repeated_keys() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    frame = records_to_frame([_record(timestamp), _record(timestamp, 2.0)])

    duplicates = find_duplicate_observations(frame)

    assert len(duplicates) == 2


def test_duplicate_detector_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        find_duplicate_observations(pd.DataFrame({"entity_id": ["node-a"]}))
