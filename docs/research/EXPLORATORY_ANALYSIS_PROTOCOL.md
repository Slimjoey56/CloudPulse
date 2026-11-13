# Exploratory Analysis Protocol

## Objective

Describe the prepared Microsoft telemetry series before selecting anomaly-detection or forecasting baselines. The analysis is descriptive and does not claim predictive performance.

## Input

The exploration command loads the pinned Microsoft source data, applies the documented duplicate-safe modelling-view policy, and computes summaries independently for each univariate series.

- Exact duplicate observations are collapsed.
- Complete timestamp groups with conflicting values or labels are excluded.
- Missing measurements are retained and counted.
- The raw source frame is not modified.

## Per-series measurements

For every series, the report records:

- row, valid-value, missing-value, and anomaly-label counts;
- missing-value and anomaly-label fractions;
- UTC start and end timestamps;
- median observed sampling interval;
- count of intervals greater than 1.5 times the series' median interval;
- mean, sample standard deviation, minimum, maximum, median, and median absolute deviation;
- 1st, 25th, 50th, 75th, and 99th percentiles;
- fraction of valid values equal to zero;
- metric description where supplied by source metadata.

Value statistics are never pooled across different series. The source contains different metric types and units, so a cross-series mean or scale comparison would be uninterpretable without additional metadata and a justified normalization strategy.

## Interpretation constraints

- The interval-gap flag is a descriptive threshold, not proof that a measurement was lost.
- Point labels are not yet converted into anomaly events.
- Distribution summaries do not establish stationarity, seasonality, or forecastability.
- No imputation, scaling, feature selection, or model fitting occurs in this stage.
- Missing-value handling for a future model must be fitted using training data only.

## Reproduction

Run `python -m cloudpulse.data.explore_microsoft`.

The default output is `reports/generated/microsoft_cloud_monitoring_exploration.json`. The generated report includes the modelling-view preparation counts used to produce the summaries.
