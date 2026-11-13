"""Prepare a conservative modelling view from raw Microsoft telemetry."""

from __future__ import annotations

import pandas as pd

KEY_COLUMNS = ["series_id", "timestamp"]
OBSERVATION_COLUMNS = [*KEY_COLUMNS, "value", "label"]


def prepare_microsoft_model_frame(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Remove exact copies and exclude unresolved conflicting timestamp groups.

    The input frame is never mutated. Missing measurements are retained for
    downstream, training-only missing-data handling.
    """
    required = set(OBSERVATION_COLUMNS)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    input_rows = len(frame)
    if frame.empty:
        return frame.copy(), {
            "input_rows": 0,
            "conflicting_timestamp_groups_excluded": 0,
            "conflicting_rows_excluded": 0,
            "exact_duplicate_rows_removed": 0,
            "missing_value_rows_retained": 0,
            "output_rows": 0,
        }

    unique_observations = frame.drop_duplicates(subset=OBSERVATION_COLUMNS)
    observation_counts = unique_observations.groupby(
        KEY_COLUMNS, dropna=False
    ).size()
    conflicting_keys = observation_counts[observation_counts > 1].index

    row_keys = pd.MultiIndex.from_frame(frame[KEY_COLUMNS])
    conflict_mask = row_keys.isin(conflicting_keys)
    conflicting_rows_excluded = int(conflict_mask.sum())

    candidates = frame.loc[~conflict_mask].copy()
    prepared = candidates.drop_duplicates(subset=OBSERVATION_COLUMNS, keep="first")
    exact_duplicate_rows_removed = len(candidates) - len(prepared)
    prepared = prepared.sort_values(
        KEY_COLUMNS,
        kind="stable",
        ignore_index=True,
    )

    if prepared.duplicated(KEY_COLUMNS).any():
        raise RuntimeError("Prepared modelling view still contains duplicate timestamps")

    report = {
        "input_rows": int(input_rows),
        "conflicting_timestamp_groups_excluded": int(len(conflicting_keys)),
        "conflicting_rows_excluded": conflicting_rows_excluded,
        "exact_duplicate_rows_removed": int(exact_duplicate_rows_removed),
        "missing_value_rows_retained": int(prepared["value"].isna().sum()),
        "output_rows": int(len(prepared)),
    }
    return prepared, report
