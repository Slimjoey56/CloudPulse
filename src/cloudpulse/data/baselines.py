"""Chronological evaluation of a per-series robust z-score baseline."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

KEY_COLUMNS = ["series_id", "timestamp"]
DEFAULT_THRESHOLD = 3.5


def chronological_split(
    frame: pd.DataFrame,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> dict[str, pd.DataFrame]:
    """Split each series independently in timestamp order."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train_fraction plus validation_fraction must be less than 1")
    if frame.duplicated(KEY_COLUMNS).any():
        raise ValueError("Chronological splitting requires unique series timestamps")

    parts: dict[str, list[pd.DataFrame]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    for _, group in frame.groupby("series_id", sort=True):
        ordered = group.sort_values("timestamp", kind="stable")
        row_count = len(ordered)
        train_end = int(row_count * train_fraction)
        validation_end = int(row_count * (train_fraction + validation_fraction))
        if train_end < 1 or validation_end <= train_end or validation_end >= row_count:
            raise ValueError(
                "Each series must contain enough rows for non-empty train, validation, "
                "and test splits"
            )
        parts["train"].append(ordered.iloc[:train_end])
        parts["validation"].append(ordered.iloc[train_end:validation_end])
        parts["test"].append(ordered.iloc[validation_end:])

    return {
        name: pd.concat(groups, ignore_index=True) if groups else frame.iloc[0:0].copy()
        for name, groups in parts.items()
    }


def _fit_robust_location_scale(values: pd.Series) -> tuple[float | None, float | None, str]:
    """Fit median and robust scale using training values only."""
    observed = values.dropna()
    if observed.empty:
        return None, None, "unavailable_no_training_values"

    center = float(observed.median())
    mad = float((observed - center).abs().median())
    if mad > 0:
        return center, 1.4826 * mad, "median_absolute_deviation"

    interquartile_range = float(observed.quantile(0.75) - observed.quantile(0.25))
    if interquartile_range > 0:
        return center, interquartile_range / 1.349, "interquartile_range_fallback"

    return center, None, "zero_variance_unscorable"


def _score_values(values: pd.Series, center: float, scale: float) -> pd.Series:
    """Calculate absolute robust z-scores using a positive training scale."""
    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("scale must be finite and positive")
    return (values - center).abs() / scale


def _average_precision(labels: list[int], scores: list[float]) -> float | None:
    """Compute non-interpolated average precision, grouping tied scores."""
    positive_count = sum(labels)
    if positive_count == 0 or not labels:
        return None

    ordered = sorted(zip(scores, labels, strict=True), key=lambda pair: pair[0], reverse=True)
    true_positives = 0
    false_positives = 0
    previous_recall = 0.0
    average_precision = 0.0
    index = 0

    while index < len(ordered):
        current_score = ordered[index][0]
        while index < len(ordered) and ordered[index][0] == current_score:
            if ordered[index][1] == 1:
                true_positives += 1
            else:
                false_positives += 1
            index += 1
        recall = true_positives / positive_count
        precision = true_positives / (true_positives + false_positives)
        average_precision += (recall - previous_recall) * precision
        previous_recall = recall

    return float(average_precision)


def _evaluate_partition(
    frame: pd.DataFrame,
    center: float | None,
    scale: float | None,
    threshold: float,
) -> dict[str, Any]:
    """Evaluate one chronological partition; missing values are unscored."""
    observed = frame.loc[frame["value"].notna()].copy()
    missing_count = int(frame["value"].isna().sum())
    if center is None or scale is None or observed.empty:
        return {
            "rows": int(len(frame)),
            "scored_rows": 0,
            "unscored_rows": int(len(observed)),
            "unscored_positive_labels": int(observed["label"].sum()),
            "missing_value_rows": missing_count,
            "positive_labels": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "true_negatives": 0,
            "precision": 0.0,
            "recall": None,
            "f1": None,
            "average_precision": None,
        }

    scores = _score_values(observed["value"], center, scale).tolist()
    labels = observed["label"].astype(int).tolist()
    predictions = [int(score >= threshold) for score in scores]
    true_positives = sum(y == 1 and pred == 1 for y, pred in zip(labels, predictions, strict=True))
    false_positives = sum(y == 0 and pred == 1 for y, pred in zip(labels, predictions, strict=True))
    false_negatives = sum(y == 1 and pred == 0 for y, pred in zip(labels, predictions, strict=True))
    true_negatives = sum(y == 0 and pred == 0 for y, pred in zip(labels, predictions, strict=True))
    positive_count = sum(labels)
    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = true_positives / positive_count if positive_count else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if recall is not None and precision + recall
        else (0.0 if recall == 0 else None)
    )

    return {
        "rows": int(len(frame)),
        "scored_rows": int(len(observed)),
        "unscored_rows": 0,
        "unscored_positive_labels": 0,
        "missing_value_rows": missing_count,
        "positive_labels": int(positive_count),
        "true_positives": int(true_positives),
        "false_positives": int(false_positives),
        "false_negatives": int(false_negatives),
        "true_negatives": int(true_negatives),
        "precision": float(precision),
        "recall": float(recall) if recall is not None else None,
        "f1": float(f1) if f1 is not None else None,
        "average_precision": _average_precision(labels, scores),
    }


def build_robust_zscore_report(
    frame: pd.DataFrame,
    threshold: float = DEFAULT_THRESHOLD,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> dict[str, Any]:
    """Fit per-series robust statistics on train and evaluate validation/test."""
    required = {"series_id", "timestamp", "value", "label"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if threshold <= 0 or not math.isfinite(threshold):
        raise ValueError("threshold must be a finite positive number")

    splits = chronological_split(frame, train_fraction, validation_fraction)
    series_reports: list[dict[str, Any]] = []
    aggregate_counts = {
        "test_rows": 0,
        "missing_value_rows": 0,
        "scored_rows": 0,
        "unscored_rows": 0,
        "unscored_positive_labels": 0,
        "positive_labels": 0,
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "true_negatives": 0,
    }

    for series_id, train_group in splits["train"].groupby("series_id", sort=True):
        validation_group = splits["validation"].loc[splits["validation"]["series_id"] == series_id]
        test_group = splits["test"].loc[splits["test"]["series_id"] == series_id]
        center, scale, scale_method = _fit_robust_location_scale(train_group["value"])
        validation_metrics = _evaluate_partition(validation_group, center, scale, threshold)
        test_metrics = _evaluate_partition(test_group, center, scale, threshold)
        for key in aggregate_counts:
            source_key = "rows" if key == "test_rows" else key
            aggregate_counts[key] += int(test_metrics[source_key])
        series_reports.append(
            {
                "series_id": str(series_id),
                "train_rows": int(len(train_group)),
                "training_missing_value_rows": int(train_group["value"].isna().sum()),
                "training_center": center,
                "training_scale": scale,
                "scale_method": scale_method,
                "validation": validation_metrics,
                "test": test_metrics,
            }
        )

    tp = aggregate_counts["true_positives"]
    fp = aggregate_counts["false_positives"]
    fn = aggregate_counts["false_negatives"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if recall is not None and precision + recall
        else (0.0 if recall == 0 else None)
    )
    total_positive_labels_including_unscored = (
        tp + fn + aggregate_counts["unscored_positive_labels"]
    )
    recall_counting_unscored_as_misses = (
        tp / total_positive_labels_including_unscored
        if total_positive_labels_including_unscored
        else None
    )
    f1_counting_unscored_as_misses = (
        2
        * precision
        * recall_counting_unscored_as_misses
        / (precision + recall_counting_unscored_as_misses)
        if recall_counting_unscored_as_misses is not None
        and precision + recall_counting_unscored_as_misses
        else (0.0 if recall_counting_unscored_as_misses == 0 else None)
    )
    test_scoring_coverage = (
        aggregate_counts["scored_rows"] / aggregate_counts["test_rows"]
        if aggregate_counts["test_rows"]
        else 0.0
    )
    return {
        "method": "per-series training median and scaled MAD robust z-score",
        "threshold": float(threshold),
        "train_fraction": float(train_fraction),
        "validation_fraction": float(validation_fraction),
        "test_fraction": float(1 - train_fraction - validation_fraction),
        "threshold_tuning": "None; threshold was fixed before evaluation.",
        "fit_policy": (
            "Each series' median and robust scale are fitted using its training "
            "partition only. Labels are used only for evaluation."
        ),
        "missing_value_policy": "Rows with missing values are retained in splits but unscored.",
        "scale_fallbacks": {
            "primary": "1.4826 multiplied by training median absolute deviation",
            "secondary": "training interquartile range divided by 1.349",
            "zero_variance": "series is unscorable; no arbitrary anomaly flags are generated",
        },
        "test_scoring_coverage": float(test_scoring_coverage),
        "test_micro_metrics": {
            **aggregate_counts,
            "precision": float(precision),
            "recall": float(recall) if recall is not None else None,
            "f1": float(f1) if f1 is not None else None,
            "recall_counting_unscored_as_misses": (
                float(recall_counting_unscored_as_misses)
                if recall_counting_unscored_as_misses is not None
                else None
            ),
            "f1_counting_unscored_as_misses": (
                float(f1_counting_unscored_as_misses)
                if f1_counting_unscored_as_misses is not None
                else None
            ),
        },
        "series": series_reports,
    }
