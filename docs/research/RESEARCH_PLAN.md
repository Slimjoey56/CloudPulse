# Research Plan

## Working title

Intelligent Cloud Infrastructure Monitoring, Anomaly Detection and Predictive Capacity Engineering

## Problem statement

Cloud and distributed-service operators observe time-indexed signals such as request rates, response latency, database activity, CPU utilisation, memory consumption, and network throughput. These signals are noisy, workload-dependent, and often sampled at different intervals. Fixed thresholds can generate excessive alerts when normal operating conditions change. Forecasting demand requires careful treatment of trend, seasonality, missing observations, and temporal leakage.

CloudPulse will study a reproducible workflow for service and infrastructure telemetry. The first empirical stage uses the Microsoft Cloud Monitoring Dataset for expert-labelled service telemetry. A separate controlled container testbed is being evaluated for resource-level fault scenarios. Results from different datasets will be reported separately because their collection processes and measurement semantics differ.

## Research questions

**RQ1 — Detection:** How do robust statistical detectors compare with unsupervised machine-learning methods for identifying source-labelled anomalous intervals in operational telemetry?

**RQ2 — Forecasting:** How accurately can demand signals such as request rate be forecast at defined horizons when evaluated on later time periods?

**RQ3 — Robustness:** How does performance vary across telemetry series, sampling frequencies, workload regimes, missing observations, and distribution shifts?

**RQ4 — Operational trade-offs:** What is the relationship between detection recall, false alerts per unit time, detection delay, inference cost, and model complexity?

## Hypotheses to test

These are hypotheses, not findings:

- H1: Robust rolling-statistic detectors may provide competitive anomaly detection on some univariate service metrics.
- H2: Forecasting performance will vary by metric, series, and forecast horizon.
- H3: Evaluation on temporally separated holdouts will provide a more realistic estimate than randomly shuffled evaluation.
- H4: More complex models will not necessarily improve operational utility enough to justify their added cost.

## Dataset scope

### First dataset: Microsoft Cloud Monitoring Dataset

The first pipeline targets the pinned Microsoft Cloud Monitoring Dataset snapshot documented in [the dataset card](../data/DATASET_CARD_MICROSOFT.md) and [the selection decision](../data/DATASET_DECISION.md).

The source describes production service/client telemetry with expert anomaly labels. The inspected snapshot contains 60 CSV files and 60 JSON metadata files, although the repository README describes 67 time series. The discrepancy is recorded rather than assumed away.

This dataset supports univariate service-telemetry anomaly detection and forecasting of the measured signal. It does not directly provide CPU or memory utilisation, and it cannot by itself support claims about multivariate root-cause analysis or validated infrastructure capacity prediction.

### Secondary candidate: controlled container testbed

The Mendeley Data testbed (DOI 10.17632/drkg8r6tfr.1) describes 18 containerised workload profiles, 15 for training and 3 for testing, with controlled CPU, database, I/O, and network fault injection. Its dataset record declares CC BY 4.0. It remains a separate candidate until its downloadable files, schemas, labels, and acquisition procedure are audited.

### Admission criteria

A dataset must have documented:
- provenance and authoritative access location;
- license and redistribution conditions;
- time coverage and sampling cadence;
- entity identifiers and available telemetry fields;
- label definitions and limitations;
- data gaps, sampling bias, and collection constraints;
- storage and compute requirements.

## Experimental design

### Data splits

For time-dependent experiments, preserve chronological order:
- training period: earliest segment;
- validation period: subsequent segment;
- test period: latest segment.

Exact boundaries will be selected after auditing each series. Series with different sampling frequencies will not be concatenated as if they share a common clock. Where multiple entities or series are available, group-aware evaluation will be considered separately.

### Baselines

Candidate baselines, subject to data suitability:
- static operational thresholds;
- rolling median and median absolute deviation;
- persistence forecasting;
- seasonal naive forecasting;
- linear regression or another simple interpretable forecasting model.

### Candidate models

Candidates may include Isolation Forest for anomaly detection and tree-based regression for forecasting. Inclusion depends on data suitability and baseline results; no algorithm is preselected as the winner.

### Metrics

Detection:
- precision, recall, and F1;
- area under precision-recall curve where scores are available;
- false positives per unit of monitored time;
- event-level detection rate and detection delay only where event intervals can be defensibly defined.

Forecasting:
- MAE and RMSE;
- MASE or another scale-aware metric where its assumptions hold;
- results reported separately by series and forecast horizon.

Operational:
- inference latency and memory use measured on a documented environment;
- alert volume under stated threshold policies;
- calibration and threshold sensitivity where applicable.

### Leakage controls

- Split by time before fitting learned preprocessing.
- Do not use future values in rolling features.
- Do not compute global normalisation statistics using validation or test rows.
- Ensure overlapping forecast windows do not cross split boundaries.
- Keep model selection separate from final test evaluation.
- Document any labels or features derived from incident outcomes.

## Error analysis

Inspect false positives and false negatives by series, time period, metric, and workload regime. Examine missingness, drift, alert persistence, and failure cases. Report limitations and uncertainty rather than presenting a single metric as universal.

## Reproducibility record

Each experiment should record:
- dataset identifier, version, and retrieval information;
- code commit;
- configuration and random seed;
- Python and dependency versions;
- split boundaries;
- feature definitions;
- model parameters;
- metrics and generated artifact paths.

## Current status

The Microsoft source snapshot has been inspected and a pinned acquisition and audit pipeline has been added. Raw data has not yet been downloaded into a user development environment, and no model has been trained. No predictive results are reported.
