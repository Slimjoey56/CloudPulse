# Development Roadmap

This roadmap is dependency-driven. A stage is complete only when its acceptance criteria are met and recorded.

## Stage 0 — Project foundation
- [x] Define the project purpose and scope.
- [x] Establish research questions and evaluation principles.
- [x] Establish data governance rules.
- [x] Create Python packaging and quality configuration.
- [ ] Run the initial environment setup and test suite on a development machine.

## Stage 1 — Dataset selection and audit
- [ ] Compare candidate public infrastructure telemetry datasets.
- [ ] Verify license, provenance, schema, access method, and resource needs.
- [ ] Create a dataset card and immutable acquisition manifest.
- [ ] Implement a reproducible loader for the selected dataset.
- [ ] Produce a data-quality report.

**Exit criteria:** a documented dataset with reproducible access and a quality report; no model claims.

## Stage 2 — Exploratory analysis and baseline
- [ ] Explore distributions, temporal patterns, missingness, and entity variation.
- [ ] Define anomaly events or a defensible proxy-label strategy.
- [ ] Implement static and robust-statistical detection baselines.
- [ ] Implement a simple forecasting baseline.
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
