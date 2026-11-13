# Architecture

## Current design

CloudPulse is organised as a staged pipeline. Components are introduced only when they have a validated responsibility and test coverage.

```text
Telemetry source
      |
      v
Ingestion and schema validation
      |
      v
Quality checks and canonical time series
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

## Component responsibilities

### Data ingestion
- Read source-specific input through adapters.
- Preserve original timestamps and entity identifiers.
- Convert values to documented units only through explicit transformations.
- Reject invalid schemas and report malformed rows.

### Canonical telemetry model

The initial canonical record is expected to represent:
- event timestamp;
- entity or workload identifier;
- metric name;
- numeric value;
- unit;
- optional source metadata.

The final schema will be adjusted only after the selected dataset is inspected.

### Quality and feature engineering
- Validate monotonicity and duplicate timestamps within an entity/metric series.
- Measure missingness and irregular sampling.
- Derive rolling and lag features without looking forward.
- Preserve transformation metadata.

### Model layer
Separate detection and forecasting tasks. Every model has a baseline, explicit input contract, training configuration, and evaluation report.

### API and application
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
