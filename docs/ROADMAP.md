# Development Roadmap

This roadmap is dependency-driven. A stage is complete only when its acceptance criteria are met and recorded.

## Stage 0 — Project foundation
- [x] Define the project purpose and scope.
- [x] Establish research questions and evaluation principles.
- [x] Establish data governance rules.
- [x] Create Python packaging and quality configuration.
- [ ] Run the initial environment setup and test suite on a development machine.

## Stage 1 — Dataset selection and audit
- [x] Compare candidate public infrastructure telemetry datasets.
- [x] Inspect source provenance, schema, and repository inventory.
- [x] Create dataset decision record and dataset card.
- [x] Implement pinned dataset acquisition utility.
- [x] Implement canonical loader and descriptive audit command.
- [ ] Verify data-specific reuse terms before any redistribution.
- [ ] Download the dataset and run the audit on a development machine.
- [x] Inspect the automated CI audit artifact and review per-series quality findings.
- [x] Classify exact duplicate observations and conflicting timestamp groups.
- [x] Document the source-level duplicate investigation and handling policy.
- [x] Implement and test a conservative modelling-view preparation function.
- [x] Review the generated data-quality report and document findings.

**Exit criteria:** a downloaded, version-pinned dataset; reproducible acquisition manifest; completed data-quality report; documented limitations. No model claims are required at this stage.

## Stage 2 — Exploratory analysis and baseline
- [x] Generate per-series distribution, temporal-interval, missingness, and label summaries.
- [x] Add reproducible exploratory-analysis output to dataset CI artifacts.
- [ ] Define anomaly-event handling and point-label evaluation policy.
- [x] Implement a fixed-threshold robust z-score anomaly-detection baseline.
- [x] Compare a per-series validation-selected threshold without using test labels.
- [x] Implement a causal rolling robust detector with past-only windows and temporal-gap resets.
- [x] Add validation-only threshold selection and CI evaluation for the rolling detector.
- [ ] Analyse rolling detector error profiles and compare against static baselines.
- [ ] Implement a separate static threshold baseline and compare its error profile.
- [ ] Implement a simple forecasting baseline for suitable signals.
- [ ] Define chronological validation and test boundaries.

**Exit criteria:** baseline metrics and error analysis generated from reproducible experiments.

## Stage 3 — Candidate machine-learning models
- [ ] Implement candidate anomaly detectors.
- [ ] Implement candidate forecasting models.
- [ ] Tune using validation data only.
- [ ] Evaluate once on the held-out test period.
- [ ] Perform robustness and ablation analysis.

**Exit criteria:** complete experiment records, comparison tables, and limitations.

## Stage 4 — Inference service
- [ ] Define versioned request and response schemas.
- [ ] Implement model loading and prediction interfaces.
- [ ] Add API validation and error handling.
- [ ] Add unit and integration tests.
- [ ] Measure latency and resource use.

## Stage 5 — Monitoring interface
- [ ] Build views for telemetry history, alerts, and forecasts.
- [ ] Show model/data version and prediction timestamps.
- [ ] Communicate uncertainty and known limitations.
- [ ] Add operator feedback workflow.

## Stage 6 — Cloud and deployment engineering
- [ ] Containerise validated services.
- [ ] Define environment-specific configuration.
- [ ] Add CI checks and reproducible deployment instructions.
- [ ] Provision minimal cloud resources through reviewed infrastructure code.
- [ ] Document security controls and cost assumptions.

## Stage 7 — Research communication
- [ ] Write a reproducibility guide.
- [ ] Publish dataset and model cards.
- [ ] Document negative results and limitations.
- [ ] Prepare a technical report with methods, experiments, and evidence.
- [ ] Record a demonstration using the working application.
