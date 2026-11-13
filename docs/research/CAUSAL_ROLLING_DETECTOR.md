# Causal Rolling Robust Detector Protocol

## Research question

Does a causal, locally adaptive robust detector improve point-level anomaly detection over the existing static per-series robust z-score baseline on the pinned Microsoft Cloud Monitoring Dataset?

This experiment remains univariate. It does not claim multivariate root-cause identification or capacity prediction.

## Detector

For each series, observations are sorted chronologically. At timestamp (t), the detector estimates its reference location and scale from up to the preceding 60 observations, excluding the current observation:

- Location: median of the historical window.
- Scale: (1.4826 \times MAD), with (IQR / 1.349) as a fallback when MAD is zero and IQR is positive.
- Score: absolute deviation of the current value from the historical median, divided by the historical robust scale.
- Default alert threshold: 3.5.

The default minimum history is 20 non-missing observations. A score is unavailable before this minimum is met or when the historical window has zero robust scale.

## Temporal gaps and missing values

The window is observation-count based rather than duration based because the source contains series with different sampling frequencies. For each series, the median positive timestamp interval is calculated. A gap greater than three times that interval starts a new segment and resets the rolling history.

Missing measurement rows remain in the sequence and do not contribute to rolling statistics. They are not imputed. The minimum-history requirement counts non-missing historical observations, not elapsed timestamps.

The gap factor and window size are explicit CLI parameters so later sensitivity experiments can vary them without changing the implementation.

## Evaluation design

- Reuse the prepared modelling view and per-series chronological 60/20/20 split.
- Compute scores in timestamp order using only preceding measurements. The rolling history is allowed to carry forward from training into validation and from validation into test, as it would in a causal online scoring process.
- Use validation labels only to select a per-series threshold from the same predeclared grid used by the static baseline: 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0, and 10.0.
- Retain the fixed 3.5 threshold as a comparator.
- Never use test labels for threshold selection.
- Report warm-up/gap/zero-scale unscored rows separately from original missing measurements. Count unscored positive labels as misses in conservative recall and F1.

The validation and test partitions are scored with the same historical-only rule. Validation measurements may contribute to the history used to score later test observations, but validation labels do not.

## Limitations

- The detector is univariate and uses a fixed observation-count window.
- A window of 60 observations represents different elapsed durations across source series.
- The three-times-median gap rule is a predeclared engineering choice, not a learned optimum.
- Rolling median and MAD may be insensitive to some gradual shifts or recurring seasonal patterns.
- Point-level labels do not measure event-level alert quality.
- This experiment does not validate production alerting, root-cause analysis, CPU/memory forecasting, or capacity prediction.

## Reproduction

Run:

```bash
python -m cloudpulse.data.evaluate_microsoft_baseline
```

The command writes the static baseline report and the causal rolling report under `reports/generated/`. Rolling parameters can be changed with `--rolling-window`, `--rolling-min-periods`, and `--max-gap-factor`.
