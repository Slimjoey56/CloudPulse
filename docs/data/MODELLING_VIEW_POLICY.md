# Modelling View Policy

## Purpose

The raw Microsoft telemetry frame is the immutable analytical input. The modelling view is a derived representation that applies only documented, deterministic duplicate handling. It does not overwrite downloaded files or alter the audit report.

## Rules

1. Group observations by `(series_id, timestamp)`.
2. If a timestamp group contains more than one distinct `(value, label)` pair, classify the whole group as conflicting and exclude all rows in that group from the current supervised modelling view.
3. Among non-conflicting groups, collapse repeated rows only when `series_id`, `timestamp`, `value`, and `label` are identical.
4. Retain missing measurement values as missing. Imputation, if required by a model, must be fitted on training data only and applied to validation/test data without leakage.
5. Sort the resulting frame by series and timestamp and verify uniqueness of `(series_id, timestamp)`.

## Rationale

Exact copies do not add a new measurement or label. Keeping multiple copies would give the same timestamp additional weight in fitting and evaluation.

Conflicting observations cannot be resolved from the available source fields. Selecting the first row, averaging values, or taking a majority label would introduce an unsupported assumption. Excluding the complete timestamp group is therefore the conservative supervised-learning policy while preserving the raw observations for later review.

## Implementation

Use `prepare_microsoft_model_frame(frame)` from `cloudpulse.data.preparation`. It returns:

- a new prepared DataFrame;
- a report containing input rows, excluded conflicting groups and rows, collapsed exact duplicate rows, retained missing-value rows, and output rows.

The input DataFrame is not mutated. The function does not impute values, create temporal splits, fit a model, or calculate performance metrics.

## Required downstream safeguards

- Use chronological train/validation/test splits independently within each series.
- Fit any imputer, scaler, or threshold using training data only.
- Keep all observations from a timestamp group in the same partition; the prepared view currently enforces one row per series/timestamp.
- Evaluate point-level and event-level anomaly metrics separately once an event definition is documented.
- Report the number of rows excluded by this policy with each experiment.
