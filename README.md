# CloudPulse

**Intelligent Cloud Infrastructure Monitoring, Anomaly Detection and Predictive Capacity Engineering**

CloudPulse is an applied research and software-engineering project for analysing operational telemetry, detecting unusual service behaviour, and forecasting measured workload signals. The work is being developed as a reproducible research prototype, not represented as a production monitoring service.

## Current implementation

- Pinned acquisition utility for the Microsoft Cloud Monitoring Dataset.
- CSV loader that preserves each source file as an independent time series.
- CSVW metadata ingestion where metadata is available.
- Validation of timestamps, numeric values, and binary anomaly labels.
- Descriptive data-quality audit with exact-duplicate and conflicting-timestamp classification.
- Conservative modelling-view preparation that collapses exact copies and excludes unresolved conflicting timestamp groups.
- Per-series exploratory summaries for missingness, labels, sampling intervals, and value distributions.
- Telemetry record schema and duplicate-observation checks.
- Unit tests and a GitHub Actions quality workflow.

The raw dataset is not stored in this repository. The acquisition command writes it to an ignored local data directory.

## Research direction

The first empirical study uses expert-labelled Microsoft service telemetry, including request-rate, database-activity, and latency signals. It is suitable for univariate service-telemetry anomaly detection and forecasting of the measured signal.

A separate containerised testbed dataset is under evaluation for resource-level fault scenarios. Dataset results will remain separate because their data-generation and measurement processes differ.

The Microsoft repository README describes 67 time series; the inspected pinned source snapshot contains 60 CSV files and 60 metadata JSON files. This discrepancy is documented in the dataset card and selection record.

## Research integrity

- No model performance numbers are published before experiments are run.
- No synthetic telemetry is presented as observed production data.
- Time-dependent evaluation uses chronological splits.
- Data sources, licenses, versions, and transformations are documented.
- Every model is compared with a baseline.
- Limitations and negative results are retained in the research record.

## Quick start

Python 3.11 or later is the initial target.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Download the pinned Microsoft dataset snapshot:

```bash
python -m cloudpulse.data.download_microsoft
```

Generate the descriptive data-quality report:

```bash
python -m cloudpulse.data.audit_microsoft
```

Prepare a modelling view in Python after loading the dataset:

```python
from pathlib import Path

from cloudpulse.data.microsoft import load_microsoft_series
from cloudpulse.data.preparation import prepare_microsoft_model_frame

raw = load_microsoft_series(Path("data/raw/microsoft_cloud_monitoring"))
model_frame, preparation_report = prepare_microsoft_model_frame(raw)
print(preparation_report)
```

Generate reproducible per-series exploratory summaries:

```bash
python -m cloudpulse.data.explore_microsoft
```

The exploration command prepares the data first and writes `reports/generated/microsoft_cloud_monitoring_exploration.json`. It reports value statistics per series and does not pool values across metrics with different units.

The preparation function preserves the raw frame, collapses exact duplicate observations, excludes unresolved conflicting timestamp groups, and retains missing values for downstream training-only handling.

The default report path is `reports/generated/microsoft_cloud_monitoring_audit.json`. Raw data and generated reports are excluded from Git.

Run code-quality checks:

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

## Documentation

- [Research plan](docs/research/RESEARCH_PLAN.md)
- [Architecture](docs/architecture/ARCHITECTURE.md)
- [Dataset selection decision](docs/data/DATASET_DECISION.md)
- [Microsoft dataset card](docs/data/DATASET_CARD_MICROSOFT.md)
- [Duplicate timestamp investigation](docs/data/DUPLICATE_RECORD_INVESTIGATION.md)
- [Modelling view policy](docs/data/MODELLING_VIEW_POLICY.md)
- [Exploratory analysis protocol](docs/research/EXPLORATORY_ANALYSIS_PROTOCOL.md)
- [Observed exploratory findings](docs/research/EXPLORATORY_FINDINGS.md)
- [Data governance](docs/data/DATA_GOVERNANCE.md)
- [Development roadmap](docs/ROADMAP.md)
- [Contribution standards](CONTRIBUTING.md)

## Scope boundaries

The Microsoft dataset does not directly provide CPU or memory utilisation and cannot independently validate multivariate root-cause analysis or infrastructure capacity prediction. Those claims require an appropriate separate resource-telemetry dataset and experiments.

CloudPulse does not autonomously remediate infrastructure or guarantee outage prediction. Any future recommendation is advisory and must be reviewed by an operator.

## License

No license has been selected for the CloudPulse code yet. Until one is added, the default copyright rules apply. Public visibility does not by itself grant permission to reuse the code.
