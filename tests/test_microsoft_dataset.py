import json
from pathlib import Path

import pandas as pd
import pytest

from cloudpulse.data.audit_microsoft import build_audit_report
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
