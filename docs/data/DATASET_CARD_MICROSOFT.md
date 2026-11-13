# Dataset Card: Microsoft Cloud Monitoring Dataset

## Identity

- **Publisher:** Microsoft
- **Repository:** https://github.com/microsoft/cloud-monitoring-dataset
- **Pinned source commit:** `6a07a53c2fac495fb6831811df4c980d6c04bd10`
- **Source branch at inspection:** `master`
- **Repository status:** archived/read-only
- **Repository license file:** MIT
- **Project handling:** raw data is downloaded locally; it is not committed to CloudPulse.

## What the publisher documents

The repository describes 67 real-world time series derived from Microsoft production service and client telemetry, with expert-labelled anomaly time points. Documented domains include purchase counts, database query rates, service API request rates, API latency, and Windows application crash rates. Sampling is per minute or per hour depending on the series.

Each CSV is documented as having:
- `TimeStamp`: ISO 8601 timestamp; timezone designation may be absent;
- `Value`: numeric observation;
- `Label`: 1 for anomaly and 0 for non-anomaly.

Each CSV has an accompanying JSON metadata file following CSVW conventions.

## Inventory observed for the pinned commit

A recursive Git tree inspection found:
- 120 files below `data/`;
- 60 CSV files;
- 60 JSON metadata files;
- 8,217,316 bytes total across those data files.

This differs from the README's stated 67 time series. The project records the observed inventory and does not assume the reason for the discrepancy.

## Appropriate uses

- univariate service telemetry anomaly detection;
- baseline comparison on expert-labelled series;
- false-positive analysis using series with no anomaly labels;
- temporal pattern exploration;
- forecasting of the measured signal, with careful description of the target.

## Inappropriate or unsupported claims

This dataset does not directly establish:
- CPU or memory utilisation forecasting;
- root-cause identification across correlated infrastructure metrics;
- generalisation to all cloud providers or production systems;
- production outage prediction;
- infrastructure cost savings.

## Known limitations

- Different series have different sampling frequencies.
- The timestamp timezone may be absent.
- The data are univariate at the CSV-file level.
- Metric definitions and units must be read from each metadata file; values must not be assumed to share a common unit.
- The repository is archived.
- The README inventory count and inspected file inventory differ.
- Expert labels are point labels; event-level evaluation requires a documented conversion rule.

## Acquisition and integrity

Run:

```bash
python -m cloudpulse.data.download_microsoft
```

The downloader pins the source commit and writes a local provenance manifest containing the retrieval timestamp and SHA-256 of the downloaded archive. It expects 60 CSV and 60 JSON metadata files. Raw data is excluded from Git by `.gitignore`.

## Citation and attribution

Cite the Microsoft Cloud Monitoring Dataset repository and retain its attribution and license notice when using the data. Verify data-specific reuse terms before redistributing the raw files or derived bundles.
