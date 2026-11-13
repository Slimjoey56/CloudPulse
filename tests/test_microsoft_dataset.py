import json
from pathlib import Path

import pandas as pd
import pytest

from cloudpulse.data.audit_microsoft import build_audit_report
from cloudpulse.data.microsoft import load_microsoft_series


def _write_series(path: Path, rows: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rows, encoding="utf-8")


def test_loader_reads_metadata_and_identifies_multiple_series(tmp_path: Path) -> None:
    first = tmp_path / "domain-a" / "series-1.csv"
    _write_series(
        first,
        "TimeStamp,Value,Label\n"
        "2026-01-01T00:00:00Z,1.5,0\n"
        "2026-01-01T01:00:00Z,2.5,1\n",
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
    assert str(frame["timestamp"].dtype) == "datetime64[ns, UTC]"
    assert int(frame["label"].sum()) == 1
    first_row = frame.loc[frame["series_id"] == "domain-a/series-1"].iloc[0]
    assert first_row["metric_description"] == "API request rate for test service."
    assert first_row["publisher"] == "Example publisher"


def test_loader_preserves_blank_measurements_as_missing(tmp_path: Path) -> None:
    _write_series(
        tmp_path / "series.csv",
        "TimeStamp,Value,Label\n"
        "2026-01-01T00:00:00Z,1.0,0\n"
        "2026-01-01T01:00:00Z,,1\n",
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


def test_audit_report_is_descriptive_and_counts_duplicates() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                ],
                utc=True,
            ),
            "value": [1.0, 2.0, 3.0],
            "label": [0, 1, 0],
            "series_id": ["series-a", "series-a", "series-a"],
            "source_file": ["a.csv", "a.csv", "a.csv"],
            "metric_description": [None, None, None],
            "publisher": [None, None, None],
        }
    )

    report = build_audit_report(frame)

    assert report["row_count"] == 3
    assert report["series_count"] == 1
    assert report["anomaly_points"] == 1
    assert report["duplicate_entity_timestamps"] == 1
    assert "No model has been trained" in report["interpretation"]
