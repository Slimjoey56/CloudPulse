import json
from pathlib import Path

import pandas as pd
import pytest

from cloudpulse.data.audit_microsoft import build_audit_report
from cloudpulse.data.baselines import build_robust_zscore_report, chronological_split
from cloudpulse.data.exploration import build_exploration_report
from cloudpulse.data.microsoft import load_microsoft_series
from cloudpulse.data.preparation import prepare_microsoft_model_frame


def _write_series(path: Path, rows: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rows, encoding="utf-8")


def test_loader_reads_metadata_and_identifies_multiple_series(tmp_path: Path) -> None:
    first = tmp_path / "domain-a" / "series-1.csv"
    _write_series(
        first,
        "TimeStamp,Value,Label\n2026-01-01T00:00:00Z,1.5,0\n2026-01-01T01:00:00Z,2.5,1\n",
    )
    Path(f"{first}-metadata.json").write_text(
        json.dumps(
            {
                "notes": ["API request rate for test service."],
                "schema:publisher": {"schema:name": "Example publisher"},
            }
        ),
        encoding="utf-8",
    )
    _write_series(
        tmp_path / "domain-b" / "series-2.csv",
        "TimeStamp,Value,Label\n2026-01-02T00:00:00Z,3.5,0\n",
    )

    frame = load_microsoft_series(tmp_path)

    assert len(frame) == 3
    assert frame["series_id"].nunique() == 2
    assert isinstance(frame["timestamp"].dtype, pd.DatetimeTZDtype)
    assert str(frame["timestamp"].dtype.tz) == "UTC"
    assert int(frame["label"].sum()) == 1
    first_row = frame.loc[frame["series_id"] == "domain-a/series-1"].iloc[0]
    assert first_row["metric_description"] == "API request rate for test service."
    assert first_row["publisher"] == "Example publisher"


def test_loader_preserves_blank_measurements_as_missing(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "series.csv",
        "TimeStamp,Value,Label\n2026-01-01T00:00:00Z,1.0,0\n2026-01-01T01:00:00Z,,1\n",
    )

    frame = load_microsoft_series(tmp_path)

    assert len(frame) == 2
    assert pd.isna(frame.iloc[1]["value"])
    report = build_audit_report(frame)
    assert report["row_count"] == 2
    assert report["valid_value_count"] == 1
    assert report["missing_value_count"] == 1
    assert report["missing_value_fraction"] == 0.5


def test_loader_rejects_non_empty_non_numeric_measurements(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "invalid.csv",
        "TimeStamp,Value,Label\n2026-01-01T00:00:00Z,not-a-number,0\n",
    )

    with pytest.raises(ValueError, match="non-empty values are not numeric"):
        load_microsoft_series(tmp_path)


def test_loader_rejects_missing_columns(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "invalid.csv",
        "TimeStamp,Value\n2026-01-01T00:00:00Z,1.0\n",
    )

    with pytest.raises(ValueError, match="missing required columns"):
        load_microsoft_series(tmp_path)


def test_loader_rejects_invalid_timestamps(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "invalid.csv",
        "TimeStamp,Value,Label\nnot-a-date,1.0,0\n",
    )

    with pytest.raises(ValueError, match="timestamps could not be parsed"):
        load_microsoft_series(tmp_path)


def test_loader_rejects_non_binary_labels(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "invalid.csv",
        "TimeStamp,Value,Label\n2026-01-01T00:00:00Z,1.0,2\n",
    )

    with pytest.raises(ValueError, match="only 0 and 1"):
        load_microsoft_series(tmp_path)


def test_loader_rejects_infinite_values(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "invalid.csv",
        "TimeStamp,Value,Label\n2026-01-01T00:00:00Z,inf,0\n",
    )

    with pytest.raises(ValueError, match="values must be finite"):
        load_microsoft_series(tmp_path)


def test_audit_report_classifies_exact_and_conflicting_duplicates() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T01:00:00Z",
                ],
                utc=True,
            ),
            "value": [1.0, 1.0, 2.0, 2.0, 3.0, 3.0],
            "label": [0, 0, 0, 1, 0, 0],
            "series_id": ["series-a"] * 6,
            "source_file": ["a.csv"] * 6,
            "metric_description": [None] * 6,
            "publisher": [None] * 6,
        }
    )

    report = build_audit_report(frame)
    series_report = report["series"][0]

    assert report["row_count"] == 6
    assert report["series_count"] == 1
    assert report["duplicate_timestamp_groups"] == 2
    assert report["duplicate_excess_rows"] == 4
    assert report["exact_duplicate_excess_rows"] == 2
    assert report["conflicting_timestamp_groups"] == 1
    assert report["conflicting_timestamp_rows"] == 4
    assert report["value_conflict_groups"] == 1
    assert report["label_conflict_groups"] == 1
    assert report["modelling_view_preparation"] == {
        "input_rows": 6,
        "conflicting_timestamp_groups_excluded": 1,
        "conflicting_rows_excluded": 4,
        "exact_duplicate_rows_removed": 1,
        "missing_value_rows_retained": 0,
        "output_rows": 1,
    }
    assert series_report["duplicate_timestamp_groups"] == 2
    assert series_report["duplicate_excess_rows"] == 4
    assert series_report["conflicting_timestamp_groups"] == 1
    assert "No model has been trained" in report["interpretation"]


def test_model_frame_collapses_exact_copies_and_excludes_conflicts() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T02:00:00Z",
                ],
                utc=True,
            ),
            "value": [1.0, 1.0, 2.0, 3.0, float("nan")],
            "label": [0, 0, 0, 0, 1],
            "series_id": ["series-a"] * 5,
            "source_file": ["a.csv"] * 5,
        }
    )
    original = frame.copy(deep=True)

    prepared, report = prepare_microsoft_model_frame(frame)

    assert len(frame) == len(original)
    pd.testing.assert_frame_equal(frame, original)
    assert len(prepared) == 2
    assert not prepared.duplicated(["series_id", "timestamp"]).any()
    assert report == {
        "input_rows": 5,
        "conflicting_timestamp_groups_excluded": 1,
        "conflicting_rows_excluded": 2,
        "exact_duplicate_rows_removed": 1,
        "missing_value_rows_retained": 1,
        "output_rows": 2,
    }
    assert prepared["value"].isna().sum() == 1


def test_model_frame_handles_empty_input() -> None:
    frame = pd.DataFrame(columns=["series_id", "timestamp", "value", "label"])

    prepared, report = prepare_microsoft_model_frame(frame)

    assert prepared.empty
    assert report["input_rows"] == 0
    assert report["output_rows"] == 0


def test_model_frame_rejects_missing_required_columns() -> None:
    frame = pd.DataFrame({"series_id": ["series-a"], "timestamp": [pd.Timestamp.now()]})

    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_microsoft_model_frame(frame)


def test_exploration_report_summarises_each_series_independently() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T02:00:00Z",
                    "2026-01-01T06:00:00Z",
                    "2026-01-01T00:00:00Z",
                ],
                utc=True,
            ),
            "value": [1.0, 2.0, float("nan"), 4.0, float("nan")],
            "label": [0, 1, 0, 0, 1],
            "series_id": ["series-a"] * 4 + ["series-b"],
            "metric_description": ["Request rate"] * 4 + ["Latency"],
        }
    )

    report = build_exploration_report(frame)
    first, second = report["series"]

    assert report["series_count"] == 2
    assert report["row_count"] == 5
    assert report["valid_value_count"] == 3
    assert report["missing_value_count"] == 2
    assert report["anomaly_label_count"] == 2
    assert first["valid_value_count"] == 3
    assert first["missing_value_count"] == 1
    assert first["anomaly_label_count"] == 1
    assert first["median_sampling_interval_seconds"] == 3600.0
    assert first["interval_gap_count"] == 1
    assert first["value_median"] == 2.0
    assert first["value_median_absolute_deviation"] == 1.0
    assert second["value_mean"] is None
    assert second["value_quantiles"]["q50"] is None
    assert report["model_training_performed"] is False


def test_exploration_rejects_unprepared_duplicate_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "series_id": ["series-a", "series-a"],
            "timestamp": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"],
                utc=True,
            ),
            "value": [1.0, 1.0],
            "label": [0, 0],
        }
    )

    with pytest.raises(ValueError, match="unique series timestamps"):
        build_exploration_report(frame)


def test_chronological_split_is_per_series_and_order_preserving() -> None:
    timestamps = pd.date_range("2026-01-01", periods=10, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "series_id": ["series-a"] * 10 + ["series-b"] * 10,
            "timestamp": list(timestamps) + list(timestamps),
            "value": list(range(10)) + list(range(10)),
            "label": [0] * 20,
        }
    )

    splits = chronological_split(frame)

    assert len(splits["train"]) == 12
    assert len(splits["validation"]) == 4
    assert len(splits["test"]) == 4
    for series_id in ("series-a", "series-b"):
        train = splits["train"].loc[splits["train"]["series_id"] == series_id]
        validation = splits["validation"].loc[splits["validation"]["series_id"] == series_id]
        test = splits["test"].loc[splits["test"]["series_id"] == series_id]
        assert train["timestamp"].max() < validation["timestamp"].min()
        assert validation["timestamp"].max() < test["timestamp"].min()


def test_robust_zscore_uses_training_only_and_reports_test_metrics() -> None:
    timestamps = pd.date_range("2026-01-01", periods=20, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "series_id": ["series-a"] * 20 + ["series-b"] * 20,
            "timestamp": list(timestamps) + list(timestamps),
            "value": list(range(1, 13)) + [13, 14, 15, 16, 100, 1, 2, 3] + [5] * 16 + [5, 5, 8, 5],
            "label": [0] * 12 + [0, 1, 1, 0] + [1, 0, 0, 0] + [0] * 16 + [1, 0, 0, 0],
        }
    )

    report = build_robust_zscore_report(frame)
    first, second = report["series"]

    assert report["threshold"] == 3.5
    assert report["threshold_tuning"].startswith("Fixed-threshold")
    assert first["training_center"] == 6.5
    assert first["scale_method"] == "median_absolute_deviation"
    assert first["test"]["true_positives"] == 1
    assert first["test"]["false_positives"] == 0
    assert first["test"]["recall"] == 1.0
    assert first["test"]["average_precision"] == 1.0
    assert first["validation_selected_threshold"] == 1.5
    assert first["threshold_selection"] == "selected_max_validation_f1"
    assert first["test_at_validation_selected_threshold"]["true_positives"] == 1
    assert second["scale_method"] == "zero_variance_unscorable"
    assert second["validation_selected_threshold"] == 3.5
    assert second["threshold_selection"] == "fallback_unscorable_training_series"
    assert second["test"]["scored_rows"] == 0
    assert second["test"]["unscored_rows"] == 4
    assert second["test"]["false_positives"] == 0
    assert second["test"]["recall"] is None

    changed_test_labels = frame.copy()
    test_mask = (changed_test_labels["series_id"] == "series-a") & (
        changed_test_labels["timestamp"] >= timestamps[16]
    )
    changed_test_labels.loc[test_mask, "label"] = [0, 1, 1, 1]
    changed_report = build_robust_zscore_report(changed_test_labels)
    assert (
        changed_report["series"][0]["validation_selected_threshold"]
        == first["validation_selected_threshold"]
    )

    assert report["test_micro_metrics"]["test_rows"] == 8
    assert report["test_micro_metrics"]["scored_rows"] == 4
    assert report["test_micro_metrics"]["unscored_rows"] == 4
    assert report["test_micro_metrics"]["unscored_positive_labels"] == 1
    assert report["test_scoring_coverage"] == 0.5
    assert report["test_micro_metrics"]["recall_counting_unscored_as_misses"] == 0.5
    assert report["test_micro_metrics"]["true_positives"] == 1
    assert report["test_micro_metrics"]["false_positives"] == 0
    assert report["test_micro_metrics"]["unscored_rows"] == 4
    assert report["test_micro_metrics"]["precision"] == 1.0


def test_chronological_split_rejects_duplicate_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "series_id": ["series-a", "series-a"],
            "timestamp": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"],
                utc=True,
            ),
            "value": [1.0, 1.0],
            "label": [0, 0],
        }
    )

    with pytest.raises(ValueError, match="unique series timestamps"):
        chronological_split(frame)
