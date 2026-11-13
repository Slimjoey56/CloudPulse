# Dataset Selection Decision — Stage 1

**Decision status:** Microsoft Cloud Monitoring Dataset selected for the first reproducible ingestion and anomaly-analysis pipeline. This is a scoped engineering decision, not a claim that one dataset covers every CloudPulse objective.

## Candidate comparison

| Candidate | Observed characteristics | Decision |
|---|---|---|
| Microsoft Cloud Monitoring Dataset | Production service/client telemetry; expert-labelled anomalies; minute/hour granularity; CSV plus per-series JSON metadata; compact repository snapshot | Selected for the first pipeline |
| Infrastructure Monitoring Testbed (Mendeley Data, 2025) | 18 containerised workload profiles (15 training, 3 test); controlled CPU, database, I/O and network fault injection; one-second collection; CC BY 4.0 | Secondary candidate; inspect files and schema before admission |
| IBM Cloud Console dataset (Zenodo, 2024) | Approximately 4.5 months; 39,365 five-minute intervals; 117,448 features; published files total about 5.5 GB | Deferred because of data volume and high-dimensional processing cost; verify license metadata before use |

## Why Microsoft is first

The dataset provides expert-labelled service anomalies in a small, inspectable CSV format. It is suitable for building and testing:
- source-specific acquisition and provenance recording;
- schema and data-quality checks;
- univariate anomaly-detection baselines;
- false-positive analysis on series with no anomaly labels;
- time-ordered evaluation.

It is not a direct CPU/memory benchmark. Its documented domains include database query rates, API request rates, API latency, purchase rates, and application crash rates. The first experiments must therefore be described as service-telemetry anomaly detection and demand-signal analysis—not as validated CPU or memory forecasting.

## Inventory discrepancy

The Microsoft README describes 67 time series. The pinned repository tree inspected for this project contains 120 files under `data/`: 60 CSV files and 60 corresponding JSON metadata files. The inventory is pinned to source commit:

`6a07a53c2fac495fb6831811df4c980d6c04bd10`

The pipeline will assert this observed inventory and report any future upstream change rather than silently accepting it.

## Licensing and redistribution

The source repository contains an MIT LICENSE file. The dataset files are distributed inside that repository, but the project will not mirror raw data into this repository. The source URL, pinned commit, retrieval time, and archive SHA-256 are recorded by the acquisition utility. Before any redistribution or repackaging, review the source terms for data-specific rights and retain required attribution.

The Mendeley testbed is listed as CC BY 4.0 on its dataset record. Its records describe controlled containerised experiments and injected faults. It remains a separate dataset: do not concatenate it with Microsoft series or compare raw metric values as if they share a measurement process.

The IBM Cloud dataset page describes its contents and 5.5 GB file set, but the inspected page did not expose a clear license value. It is therefore deferred pending rights verification.

## Experimental constraints

- Treat each Microsoft CSV as an independent univariate series unless metadata establishes a defensible grouping.
- Preserve each series identifier and original timestamp.
- Do not fabricate timestamps or sampling cadence.
- Do not interpolate across long gaps without an explicit experiment.
- Use chronological splits within each series.
- Report results by series/domain as well as aggregate summaries.
- Include no-anomaly series in false-alert analysis where their labels support that interpretation.
- Avoid claiming cross-metric multivariate detection from this dataset alone.

## Sources

- Microsoft repository: https://github.com/microsoft/cloud-monitoring-dataset
- Mendeley Data DOI: https://doi.org/10.17632/drkg8r6tfr.1
- IBM Cloud dataset DOI: https://doi.org/10.5281/zenodo.14062900
