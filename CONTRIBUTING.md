# Development and Research Standards

CloudPulse is intended to be an inspectable engineering and research project. Contributions should make the system more correct, reproducible, or useful.

## Before adding data

1. Record the originating dataset or service and its canonical URL.
2. Review the dataset license and any usage restrictions.
3. Record retrieval date, dataset version, schema, units, and timezone.
4. Identify sensitive fields and confirm they are not required.
5. Keep raw source data out of Git unless redistribution is explicitly permitted and the file is small enough for repository storage.
6. Document filtering, missing-value handling, resampling, and transformations.

## Before training a model

- State the prediction or detection target precisely.
- Define the observational unit and time horizon.
- Establish a simple baseline.
- Use chronological splits for temporal prediction.
- Fit preprocessing only on training data.
- Keep a final holdout untouched until model selection is complete.
- Report suitable metrics and error analysis, not only a single headline score.
- Record random seeds, package versions, configuration, and data version.

## Code quality

Run:

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

Add tests for new behaviours, including invalid inputs and edge cases. Avoid silently coercing malformed telemetry into valid records.

## Results and authorship

Do not publish a metric, chart, benchmark, or deployment claim unless it can be reproduced from tracked code and documented inputs. Record the actual work performed and the tools used. Every contributor should be able to explain the code they submit.
