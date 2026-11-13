"""Tests for causal rolling robust anomaly scores."""

import pandas as pd
import pytest

from cloudpulse.data.baselines import causal_rolling_scores


def _frame(values: list[float], gap_at: int | None = None) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=len(values), freq="min", tz="UTC")
    if gap_at is not None:
        timestamps = timestamps.where(
            timestamps < timestamps[gap_at],
            timestamps + pd.Timedelta(hours=2),
        )
    return pd.DataFrame(
        {
            "series_id": "series-a",
            "timestamp": timestamps,
            "value": values,
        }
    )


def test_rolling_reference_excludes_current_observation() -> None:
    frame = _frame([float(value) for value in range(1, 12)])
    original = causal_rolling_scores(frame, window=5, min_periods=5)

    changed = frame.copy()
    changed.loc[5, "value"] = 10_000.0
    modified = causal_rolling_scores(changed, window=5, min_periods=5)

    assert original.loc[5, "rolling_center"] == modified.loc[5, "rolling_center"]
    assert original.loc[5, "rolling_scale"] == modified.loc[5, "rolling_scale"]
    assert original.loc[5, "rolling_score"] != modified.loc[5, "rolling_score"]


def test_future_observations_do_not_change_past_scores() -> None:
    frame = _frame([float(value) for value in range(1, 12)])
    original = causal_rolling_scores(frame, window=5, min_periods=5)

    changed = frame.copy()
    changed.loc[10, "value"] = -50_000.0
    modified = causal_rolling_scores(changed, window=5, min_periods=5)

    assert original.loc[8, "rolling_score"] == modified.loc[8, "rolling_score"]


def test_first_score_requires_minimum_historical_observations() -> None:
    frame = _frame([float(value) for value in range(1, 10)])
    scored = causal_rolling_scores(frame, window=5, min_periods=5)

    assert scored.loc[:4, "rolling_score"].isna().all()
    assert pd.notna(scored.loc[5, "rolling_score"])


def test_large_timestamp_gap_resets_rolling_history() -> None:
    frame = _frame([float(value) for value in range(1, 16)], gap_at=8)
    scored = causal_rolling_scores(frame, window=5, min_periods=5)

    assert scored.loc[8:12, "rolling_score"].isna().all()
    assert pd.notna(scored.loc[13, "rolling_score"])


def test_missing_values_do_not_count_toward_minimum_history() -> None:
    frame = _frame([1.0, 2.0, float("nan"), 4.0, 5.0, 6.0, 7.0])
    scored = causal_rolling_scores(frame, window=5, min_periods=5)

    assert pd.isna(scored.loc[5, "rolling_score"])
    assert pd.isna(scored.loc[6, "rolling_score"])


@pytest.mark.parametrize(
    ("window", "min_periods", "gap_factor"),
    [(1, 1, 3.0), (5, 6, 3.0), (5, 2, 1.0)],
)
def test_invalid_rolling_configuration_is_rejected(
    window: int, min_periods: int, gap_factor: float
) -> None:
    with pytest.raises(ValueError):
        causal_rolling_scores(
            _frame([float(value) for value in range(1, 10)]),
            window=window,
            min_periods=min_periods,
            max_gap_factor=gap_factor,
        )
