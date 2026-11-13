from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from cloudpulse.telemetry.schema import TelemetryRecord


def test_record_normalises_timestamp_to_utc() -> None:
    record = TelemetryRecord(
        timestamp=datetime.fromisoformat("2026-01-01T01:00:00+01:00"),
        entity_id="worker-01",
        metric_name="cpu_utilization",
        value=42.5,
        unit="percent",
    )

    assert record.timestamp == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        TelemetryRecord(
            timestamp=datetime(2026, 1, 1),
            entity_id="worker-01",
            metric_name="cpu_utilization",
            value=42.5,
            unit="percent",
        )


def test_record_rejects_non_finite_value() -> None:
    with pytest.raises(ValidationError, match="finite"):
        TelemetryRecord(
            timestamp=datetime.now(timezone.utc),
            entity_id="worker-01",
            metric_name="cpu_utilization",
            value=float("nan"),
            unit="percent",
        )


def test_record_rejects_empty_entity_identifier() -> None:
    with pytest.raises(ValidationError):
        TelemetryRecord(
            timestamp=datetime.now(timezone.utc),
            entity_id=" ",
            metric_name="cpu_utilization",
            value=42.5,
            unit="percent",
        )


def test_record_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        TelemetryRecord(
            timestamp=datetime.now(timezone.utc),
            entity_id="worker-01",
            metric_name="cpu_utilization",
            value=42.5,
            unit="percent",
            unexpected="not allowed",
        )
