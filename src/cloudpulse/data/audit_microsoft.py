"""Create a reproducible data-quality report for the Microsoft dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cloudpulse.data.microsoft import load_microsoft_series



def _duplicate_metrics(frame: pd.DataFrame) -> dict[str, int]:
    """Classify repeated entity/timestamp keys without dropping source rows."""
    key_columns = ["series_id", "timestamp"]
    observation_columns = [*key_columns, "value", "label"]
    key_counts = frame.groupby(key_columns, dropna=False).size()
    duplicate_keys = key_counts[key_counts > 1].index
    duplicate_rows = (
        frame.set_index(key_columns).loc[duplicate_keys].reset_index()
        if len(duplicate_keys)
        else frame.iloc[0:0]
    )

    observation_counts = duplicate_rows.groupby(key_columns, dropna=False)[
        ["value", "label"]
    ].apply(lambda group: len(group.drop_duplicates()))
    conflicting_keys = observation_counts[observation_counts > 1].index
    conflicting_rows = (
        duplicate_rows.set_index(key_columns).loc[conflicting_keys].reset_index()
        if len(conflicting_keys)
        else duplicate_rows.iloc[0:0]
    )
    value_counts = duplicate_rows.groupby(key_columns, dropna=False)["value"].nunique(
        dropna=False
    )
    label_counts = duplicate_rows.groupby(key_columns, dropna=False)["label"].nunique(
        dropna=False
    )

    return {
        "duplicate_timestamp_groups": int(len(duplicate_keys)),
        "duplicate_excess_rows": int(frame.duplicated(key_columns).sum()),
        "exact_duplicate_excess_rows": int(frame.duplicated(observation_columns).sum()),
        "conflicting_timestamp_groups": int(len(conflicting_keys)),
        "conflicting_timestamp_rows": int(len(conflicting_rows)),
        "value_conflict_groups": int((value_counts > 1).sum()),
        "label_conflict_groups": int((label_counts > 1).sum()),
    }


def build_audit_report(frame: pd.DataFrame) -> dict[str, object]:
    """Summarise file-level and dataset-level quality without fitting models."""
    series_reports: list[dict[str, object]] = []
    for series_id, group in frame.groupby("series_id", sort=True):
        ordered = group.sort_values("timestamp")
        intervals = ordered["timestamp"].diff().dropna().dt.total_seconds()
        median_interval = float(intervals.median()) if not intervals.empty else None
        duplicate_metrics = _duplicate_metrics(ordered)
        series_reports.append(
            {
                "series_id": str(series_id),
                "rows": int(len(ordered)),
                "missing_value_count": int(ordered["value"].isna().sum()),
                "valid_value_count": int(ordered["value"].notna().sum()),
                "start_utc": ordered["timestamp"].min().isoformat(),
                "end_utc": ordered["timestamp"].max().isoformat(),
                "anomaly_points": int(ordered["label"].sum()),
                "anomaly_fraction": float(ordered["label"].mean()),
                **duplicate_metrics,
                "median_interval_seconds": median_interval,
                "metric_description": (
                    str(ordered["metric_description"].dropna().iloc[0])
                    if ordered["metric_description"].notna().any()
                    else None
                ),
            }
        )

    missing_value_count = int(frame["value"].isna().sum())
    valid_value_count = int(frame["value"].notna().sum())
    duplicate_metrics = _duplicate_metrics(frame)
    return {
        "row_count": int(len(frame)),
        "series_count": int(frame["series_id"].nunique()),
        "valid_value_count": valid_value_count,
        "missing_value_count": missing_value_count,
        "missing_value_fraction": (float(missing_value_count / len(frame)) if len(frame) else 0.0),
        "anomaly_points": int(frame["label"].sum()),
        "anomaly_fraction": float(frame["label"].mean()),
        **duplicate_metrics,
        "series": series_reports,
        "interpretation": (
            "Descriptive data-quality audit only. Missing measurements are "
            "retained and reported, not imputed. No model has been trained "
            "and no predictive performance is measured."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/raw/microsoft_cloud_monitoring"),
        help="Directory containing the extracted CSV and metadata files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/microsoft_cloud_monitoring_audit.json"),
        help="Path for the JSON audit report",
    )
    args = parser.parse_args()

    frame = load_microsoft_series(args.data)
    report = build_audit_report(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Rows: {report['row_count']}")
    print(f"Series: {report['series_count']}")
    print(f"Missing measurements: {report['missing_value_count']}")
    print(f"Anomaly points: {report['anomaly_points']}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
