# Robust Z-Score Baseline Protocol

## Purpose

Establish a transparent statistical anomaly-detection baseline before introducing more complex machine-learning models. This is a per-series detector, not a multivariate infrastructure model.

## Evaluation design

- Input is the prepared modelling view, after exact-copy collapse and exclusion of unresolved conflicting timestamp groups.
- Each series is sorted by timestamp and split independently into 60% training, 20% validation, and 20% test rows.
- Training statistics are fitted independently for each series using its training values only.
- Anomaly labels are not used to fit the center or scale; they are used only to calculate evaluation metrics.
- The fixed baseline uses an absolute robust z-score threshold of 3.5, set before evaluation.
- A separate comparison selects a per-series threshold by maximising F1 on the validation partition over the predeclared grid 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0, and 10.0. The test partition is never used for threshold selection.
- If a series has no scored validation rows or no positive validation labels, the tuned comparison falls back to the fixed threshold of 3.5 and records the reason.

## Detector

For each series, the training median is the location estimate. Scale is estimated using:

1. `1.4826 × median absolute deviation` when the training MAD is non-zero;
2. `IQR / 1.349` when MAD is zero but IQR is non-zero;
3. if both robust scale estimates are zero, the series is marked unscorable for that partition. No arbitrary anomaly flags are generated from a zero denominator.

A scored observation is flagged when its absolute robust z-score is greater than or equal to 3.5.

## Missing values

Missing-value rows remain in their chronological partition but cannot be scored by this baseline. They are reported separately and excluded from confusion-matrix metrics. This baseline does not impute measurements.

## Metrics

Validation and test reports include scored rows, missing rows, positive labels, TP, FP, FN, TN, precision, recall, F1, and average precision. Recall, F1, and average precision are undefined when the evaluated partition has no positive labels; the report uses `null` rather than inventing a score. Precision is set to zero when there are no predicted positives.

Test micro metrics aggregate confusion counts across series. Per-series metrics remain available because anomaly prevalence and metric semantics vary across series. Average precision is reported per series and is not pooled across different series.

## Limitations

- This is a univariate, distribution-based baseline and does not model temporal dependence beyond chronological evaluation.
- A single fixed threshold may not be optimal for every series.
- A static training distribution may be weak under drift or seasonality.
- Point-label metrics do not measure event detection quality.
- No production deployment, root-cause analysis, CPU/memory forecasting, or capacity prediction is validated by this experiment.

## Reproduction

Run `python -m cloudpulse.data.evaluate_microsoft_baseline`.

The default output is `reports/generated/microsoft_robust_zscore_baseline.json`. The report includes both fixed-threshold and validation-selected test metrics, the selected threshold and fallback reason for each series, and preprocessing counts so every exclusion is visible alongside the evaluation results.
