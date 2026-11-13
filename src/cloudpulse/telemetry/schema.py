"""Canonical telemetry data contracts."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TelemetryRecord(BaseModel):
    """A single timestamped numeric measurement for one monitored entity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    entity_id: NonEmptyString
    metric_name: NonEmptyString
    value: float
    unit: NonEmptyString
    source: NonEmptyString | None = None

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Require timezone-aware timestamps to avoid ambiguous event ordering."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return value.astimezone(timezone.utc)

    @field_validator("value")
    @classmethod
    def require_finite_value(cls, value: float) -> float:
        """Reject NaN and infinite values at the data boundary."""
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("value must be finite")
        return value
