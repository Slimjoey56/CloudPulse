"""Loader and validation for the Microsoft Cloud Monitoring Dataset."""

import json
import math
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"TimeStamp", "Value", "Label"}


def _read_metadata(csv_path: Path) -> tuple[str | None, str | None]:
    """Read optional CSVW metadata without assuming every field is populated."""
    metadata_path = Path(f"{csv_path}-metadata.json")
    if not metadata_path.exists():
        return None, None

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    notes = metadata.get("notes", [])
    if isinstance(notes, str):
        description = notes
    elif isinstance(notes, list):
        description = " ".join(str(note) for note in notes if note)
    else:
        description = None

    description = description or metadata.get("schema:description") or None
    publisher = metadata.get("schema:publisher", {})
    publisher_name = publisher.get("schema:name") if isinstance(publisher, dict) else None
    return description, publisher_name


def load_microsoft_series(data_dir: Path) -> pd.DataFrame:
    """Load CSV time series below data_dir into a canonical long-form frame.

    Each source CSV remains a distinct univariate series. Timestamps are
    normalised to UTC for consistent ordering. Naive source timestamps are
    interpreted as UTC by pandas; the original source timestamp is retained
    only in the raw downloaded files.
    """
    csv_files = sorted(data_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found under {data_dir}")

    frames: list[pd.DataFrame] = []
    for csv_path in csv_files:
        source = pd.read_csv(csv_path)
        missing = REQUIRED_COLUMNS.difference(source.columns)
        if missing:
            raise ValueError(f"{csv_path}: missing required columns {sorted(missing)}")

        frame = source.loc[:, ["TimeStamp", "Value", "Label"]].copy()
        timestamps = pd.to_datetime(frame["TimeStamp"], utc=True, errors="coerce")
        if timestamps.isna().any():
            bad_count = int(timestamps.isna().sum())
            raise ValueError(f"{csv_path}: {bad_count} timestamps could not be parsed")

        values = pd.to_numeric(frame["Value"], errors="coerce")
        if values.isna().any():
            bad_count = int(values.isna().sum())
            raise ValueError(f"{csv_path}: {bad_count} values are not numeric")
        if not values.map(math.isfinite).all():
            raise ValueError(f"{csv_path}: values must be finite")

        labels = pd.to_numeric(frame["Label"], errors="coerce")
        if labels.isna().any() or not labels.isin([0, 1]).all():
            raise ValueError(f"{csv_path}: Label must contain only 0 and 1")

        description, publisher = _read_metadata(csv_path)
        frame = pd.DataFrame(
            {
                "timestamp": timestamps,
                "value": values.astype("float64"),
                "label": labels.astype("int8"),
                "series_id": csv_path.relative_to(data_dir).with_suffix("").as_posix(),
                "source_file": csv_path.relative_to(data_dir).as_posix(),
                "metric_description": description,
                "publisher": publisher,
            }
        )
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values(
        ["series_id", "timestamp"],
        kind="stable",
        ignore_index=True,
    )
