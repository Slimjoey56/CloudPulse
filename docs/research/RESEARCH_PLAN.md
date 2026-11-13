# Research Plan

## Working title

Intelligent Cloud Infrastructure Monitoring, Anomaly Detection and Predictive Capacity Engineering

## Problem statement

Infrastructure operators observe time-indexed measurements such as CPU utilisation, memory consumption, network throughput, request volume, and latency. These signals are noisy, correlated, and dependent on workload patterns. Fixed thresholds can be useful, but may generate excessive alerts when normal operating conditions change. Forecasting resource demand also requires careful treatment of trends, seasonality, workload shifts, and temporal leakage.

CloudPulse will investigate a reproducible workflow for analysing infrastructure telemetry and evaluating anomaly-detection and forecasting methods.

## Research questions

**RQ1 — Detection:** How do simple statistical detectors compare with unsupervised machine-learning methods for identifying injected or source-labelled anomalous intervals in infrastructure telemetry?

**RQ2 — Forecasting:** How accurately can resource-use models forecast future demand over defined horizons when evaluated on later time periods?

**RQ3 — Robustness:** How does performance change across services, workload regimes, missing observations, and distribution shifts?

**RQ4 — Operational trade-offs:** What is the relationship between detection recall, false alerts per unit time, detection delay, inference cost, and model complexity?

## Hypotheses to test

These are hypotheses, not findings:

- H1: A detector using multiple telemetry signals may identify some anomalous patterns that independent univariate thresholds miss.
- H2: Forecasting performance will vary by resource, horizon, and workload regime.
- H3: Evaluation on temporally separated holdouts will produce more conservative estimates than randomly shuffled evaluation.
- H4: More complex models will not necessarily improve operational utility enough to justify their added cost.

## Experimental design

### Dataset qualification

A dataset will only be selected after reviewing:
- provenance and authoritative download location;
- license and redistribution conditions;
- time coverage and sampling cadence;
- entity identifiers and available telemetry fields;
- documented labels, if any;
- data gaps, sampling bias, and known collection limitations;
- storage and compute requirements.

No dataset is assumed to be selected in this initial specification.

### Data splits

For time-dependent experiments, preserve chronological order. The initial design is:
- training period: earliest segment;
- validation period: subsequent segment;
- test period: latest segment.

Exact boundaries will be determined after inspecting the selected dataset. Where multiple machines or services exist, additional group-aware experiments will assess generalisation to unseen entities. Any overlap in windows or entities will be documented.

### Baselines

Candidate baselines, subject to data suitability:
- static operational thresholds;
- rolling median and median absolute deviation;
- seasonal or persistence forecasting;
- linear regression or another simple interpretable forecasting model.

### Candidate models

Candidates may include Isolation Forest for anomaly detection and gradient-boosted or tree-based regression for forecasting. Model inclusion depends on data characteristics and baseline results; no algorithm is preselected as the winner.

### Metrics

Detection:
- precision, recall, and F1;
- area under precision-recall curve where scores are available;
- false positives per machine-hour or service-hour;
- event-level detection rate and detection delay when event intervals are defined.

Forecasting:
- MAE and RMSE;
- MASE or another scale-aware metric where its assumptions hold;
- results reported separately by resource, entity, and forecast horizon.

Operational:
- inference latency and memory use measured on a documented environment;
- alert volume under stated threshold policies;
- calibration and threshold sensitivity where applicable.

### Leakage controls

- Split by time before fitting learned preprocessing.
- Do not use future values in rolling features.
- Do not compute global normalisation statistics using validation or test rows.
- Ensure overlapping forecast windows do not cross split boundaries.
- Keep model selection separate from the final test evaluation.
- Document any labels or features derived from incident outcomes.

## Error analysis

For each final experiment, inspect false positives and false negatives by entity, time period, metric, and workload regime. Examine missingness, drift, alert persistence, and failure cases. Report limitations and uncertainty rather than presenting a single metric as universal.

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

This document defines the research protocol. It does not report experimental results. Dataset selection and exploratory data analysis are pending.
