# Duplicate Timestamp Investigation

## Scope and reproducibility

This investigation evaluates repeated `(series_id, timestamp)` keys in the 60 CSV files from the Microsoft Cloud Monitoring Dataset, pinned to source commit `6a07a53c2fac495fb6831811df4c980d6c04bd10`.

The source files were read directly from that immutable Git commit. The analysis compares each observation's `Value` and `Label`; it does not infer that repeated timestamps are erroneous solely because they occur more than once.

## Findings

| Measure | Observed |
|---|---:|
| Source CSV files | 60 |
| Source rows | 225,445 |
| Repeated entity/timestamp groups | 223 |
| Excess rows beyond one per timestamp | 241 |
| Exact duplicate excess rows (same value and label) | 238 |
| Conflicting timestamp groups | 3 |
| Rows in conflicting groups | 6 |
| Groups with differing values | 1 |
| Groups with differing labels | 2 |

The 241 excess rows reconcile as 238 exact duplicate excess rows plus 3 additional observations in the three conflicting two-row groups.

### Where duplicates occur

| Series | Repeated timestamp groups | Excess rows | Exact duplicate excess rows |
|---|---:|---:|---:|
| application-crash-rate-1/app1-01 | 9 | 11 | 11 |
| application-crash-rate-1/app1-02 | 11 | 13 | 13 |
| application-crash-rate-1/app1-03 | 11 | 13 | 13 |
| application-crash-rate-1/app1-04 | 11 | 13 | 12 |
| application-crash-rate-1/app1-05 | 11 | 13 | 13 |
| application-crash-rate-1/app1-06 | 11 | 13 | 13 |
| application-crash-rate-1/app1-07 | 11 | 13 | 13 |
| application-crash-rate-1/app1-08 | 11 | 13 | 12 |
| application-crash-rate-1/app1-09 | 6 | 8 | 8 |
| application-crash-rate-2/app2-01 through app2-10 | 13 each | 13 each | 13 each |
| ecommerce-api-incoming-rps/api-01 | 1 | 1 | 0 |

No repeated timestamp keys were observed in the other source series.

### Conflicting observations

Three timestamps have more than one distinct `(Value, Label)` observation:

1. `application-crash-rate-1/app1-04`, `2018-06-25 14:00:00`: both values are `60.0`, but labels differ (`1` and `0`).
2. `application-crash-rate-1/app1-08`, `2018-07-14 20:00:00`: both values are `41.0`, but labels differ (`1` and `0`).
3. `ecommerce-api-incoming-rps/api-01`, `2017-11-05T01:00:00Z`: values differ (`74.5658333333333` and `70.6033333333333`), while both labels are `0`.

These are material data-quality cases. In the first two, the measurement is identical but the expert anomaly label is inconsistent at the same timestamp. In the third, two different measurements are assigned to the same series and timestamp. The source data alone does not establish which observation is authoritative.

## Handling decision

- Preserve all source rows in the canonical raw-data layer.
- Do not average, sum, select-first, or silently drop conflicting observations.
- Exact duplicate observations may be collapsed only in a separately derived modelling view, with the raw data and a count of collapsed copies retained.
- Exclude the three conflicting timestamp groups from supervised model fitting and evaluation until a documented resolution policy is approved. Report their exclusion explicitly.
- Keep the duplicate audit in the reproducible data-quality report so changes in source data or handling are detectable.

This is a conservative data-integrity decision, not a claim that the source publisher has confirmed the records are erroneous.

## Implementation

The audit command now reports, at dataset and series level:

- repeated timestamp groups;
- excess rows beyond one per timestamp;
- exact duplicate excess rows;
- conflicting timestamp groups and the number of rows involved;
- groups with value conflicts;
- groups with label conflicts.

The audit is descriptive. It does not modify source observations, train a model, or measure predictive performance.
