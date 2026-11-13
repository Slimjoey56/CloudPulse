# Data Governance and Provenance

## Dataset admission checklist

A dataset is not approved for experiments until the following fields are documented:

| Field | Required record |
|---|---|
| Name | Official dataset name |
| Source | Canonical publisher or repository |
| Access | Exact download or query procedure |
| License | License text or authoritative license reference |
| Version | Release, snapshot, or retrieval date |
| Coverage | Time period and entities |
| Schema | Fields, types, units, timestamp semantics |
| Labels | Definition and known limitations |
| Privacy | Sensitive fields and mitigation |
| Size | Storage and compute requirements |
| Processing | Reproducible transformations |

## Data handling

- Do not commit large raw datasets.
- Do not commit credentials, tokens, private logs, or user-identifiable telemetry.
- Keep source files immutable where feasible and record checksums for acquired files.
- Store derived data separately from raw input.
- Document all filtering, aggregation, resampling, and imputation.
- Never label synthetic anomalies as observed incidents.
- Clearly distinguish public benchmark data, simulated data, and operational telemetry.

## Synthetic data

Synthetic telemetry may be used to test schema validation, pipeline behaviour, and controlled edge cases. It must be labelled synthetic and must not be presented as evidence of real-world model performance.

## Dataset decision record

No external dataset has been approved in this initial commit. The next research stage will compare candidate datasets against the admission checklist and select one based on suitability, reproducibility, licensing, and feasible compute requirements.
