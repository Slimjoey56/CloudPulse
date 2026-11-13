# Architecture

## Current design

CloudPulse is organised as a staged pipeline. Components are introduced only when they have a validated responsibility and test coverage.

```text
Pinned telemetry source
      |
      v
Acquisition + provenance manifest
      |
      v
Source-specific parsing and validation
      |
      v
Canonical time-series records
      |
      +--------------------+
      |                    |
      v                    v
Anomaly detection     Demand forecasting
      |                    |
      +----------+---------+
                 |
                 v
        Evaluation and registry
                 |
                 v
           Inference API
                 |
                 v
       Monitoring and review UI
```

The diagram describes the intended architecture, not a claim that all components have been implemented.

## Data ingestion

The first source adapter targets the pinned Microsoft Cloud Monitoring Dataset snapshot. It:
- downloads a versioned source archive;
- extracts only the `data/` directory;
- records retrieval time and archive SHA-256;
- preserves each CSV as a distinct series;
- reads timestamps, numeric values, point labels, and series metadata;
- rejects malformed timestamps, non-numeric values, and non-binary labels.

The adapter does not infer missing metric units or combine different sampling frequencies.

## Canonical telemetry model

The current canonical data frame contains:
- UTC-normalised event timestamp;
- numeric measurement;
- point anomaly label;
- series identifier;
- source file;
- metadata description and publisher when available.

This is a dataset adapter representation, not a universal infrastructure schema. A later container-testbed adapter will be separate.

## Quality and feature engineering

- Validate required columns and value types.
- Measure timestamp duplicates and sampling intervals.
- Preserve irregular sampling rather than silently resampling.
- Derive rolling and lag features without looking forward.
- Preserve source and transformation metadata.

## Model layer

Separate detection and forecasting tasks. Every model has a baseline, explicit input contract, training configuration, and evaluation report.

## API and application

An API and user interface are later milestones. They must consume versioned model artifacts and expose uncertainty, timestamps, and model/data version information where meaningful.

## Technology choices

The initial Python package uses NumPy, Pandas, and Pydantic. Pytest, Ruff, and mypy are development tools. FastAPI is an optional API dependency.

PostgreSQL, Kafka, Docker, AWS, Terraform, and a UI framework remain planned options—not current runtime requirements. Their introduction must be justified by an implemented use case rather than included as decoration.

## Security and reliability

- No credentials or personal data in source control.
- External input is validated at system boundaries.
- Inference endpoints should have bounded request sizes and explicit error responses.
- Model artifacts and datasets should be versioned independently from application code.
- Any future infrastructure automation should default to least privilege and safe, reviewable plans.
