"""Descriptive exploratory analysis for prepared Microsoft telemetry."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

KEY_COLUMNS = ["series_id", "timestamp"]
QUANTILES = (0.01, 0.25, 0.50, 0.75, 0.99)


def _finite_or_none(value: Any) -> float | None:
    """Convert a numeric summary to JSON-safe float or None."""
    if pd.isna(value):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def build_exploration_report(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarise each prepared univariate series without pooling metric values."""
    required = {"series_id", "timestamp", "value", "label"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame.duplicated(KEY_COLUMNS).any():
        raise ValueError("Exploration requires a prepared frame with unique series timestamps")

    reports: list[dict[str, Any]] = []
    for series_id, group in frame.groupby("series_id", sort=True):
        ordered = group.sort_values("timestamp")
        values = ordered["value"].dropna()
        missing_count = int(ordered["value"].isna().sum())
        intervals = ordered["timestamp"].diff().dropna().dt.total_seconds()
        median_interval = _finite_or_none(intervals.median()) if not intervals.empty else None
        gap_count = (
            int((intervals > 1.5 * median_interval).sum()) if median_interval is not None else 0
        )
        quantiles = (
            {f"q{int(q * 100):02d}": _finite_or_none(values.quantile(q)) for q in QUANTILES}
            if not values.empty
            else {f"q{int(q * 100):02d}": None for q in QUANTILES}
        )
        median_value = _finite_or_none(values.median()) if not values.empty else None
        mad = (
            _finite_or_none((values - values.median()).abs().median()) if not values.empty else None
        )
        reports.append(
            {
                "series_id": str(series_id),
                "row_count": int(len(ordered)),
                "valid_value_count": int(len(values)),
                "missing_value_count": missing_count,
                "missing_value_fraction": float(missing_count / len(ordered)),
                "anomaly_label_count": int(ordered["label"].sum()),
                "anomaly_label_fraction": float(ordered["label"].mean()),
                "start_utc": ordered["timestamp"].min().isoformat(),
                "end_utc": ordered["timestamp"].max().isoformat(),
                "median_sampling_interval_seconds": median_interval,
                "interval_gap_count": gap_count,
                "value_mean": _finite_or_none(values.mean()) if not values.empty else None,
                "value_std": _finite_or_none(values.std()) if len(values) > 1 else None,
                "value_min": _finite_or_none(values.min()) if not values.empty else None,
                "value_max": _finite_or_none(values.max()) if not values.empty else None,
                "value_median": median_value,
                "value_median_absolute_deviation": mad,
                "value_zero_fraction": (float(values.eq(0).mean()) if not values.empty else None),
                "value_quantiles": quantiles,
                "metric_description": (
                    str(ordered["metric_description"].dropna().iloc[0])
                    if "metric_description" in ordered
                    and ordered["metric_description"].notna().any()
                    else None
                ),
            }
        )

    return {
        "series_count": int(frame["series_id"].nunique()),
        "row_count": int(len(frame)),
        "valid_value_count": int(frame["value"].notna().sum()),
        "missing_value_count": int(frame["value"].isna().sum()),
        "anomaly_label_count": int(frame["label"].sum()),
        "anomaly_label_fraction": float(frame["label"].mean()) if len(frame) else 0.0,
        "value_statistics_scope": (
            "Computed independently within each univariate series. Values from "
            "different metrics are not pooled because units and meanings differ."
        ),
        "interval_gap_definition": (
            "A timestamp interval greater than 1.5 times that series' median "
            "observed interval. This is a descriptive flag, not proof of data loss."
        ),
        "model_training_performed": False,
        "series": reports,
    }
