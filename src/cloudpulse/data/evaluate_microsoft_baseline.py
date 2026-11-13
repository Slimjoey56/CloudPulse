"""Evaluate static and causal rolling robust anomaly detectors on Microsoft telemetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cloudpulse.data.baselines import (
    build_causal_rolling_report,
    build_robust_zscore_report,
)
from cloudpulse.data.microsoft import load_microsoft_series
from cloudpulse.data.preparation import prepare_microsoft_model_frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/raw/microsoft_cloud_monitoring"),
        help="Directory containing the extracted CSV and metadata files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/microsoft_robust_zscore_baseline.json"),
        help="Path for the static baseline JSON report",
    )
    parser.add_argument(
        "--rolling-output",
        type=Path,
        default=Path("reports/generated/microsoft_causal_rolling_detector.json"),
        help="Path for the causal rolling detector JSON report",
    )
    parser.add_argument("--rolling-window", type=int, default=60)
    parser.add_argument("--rolling-min-periods", type=int, default=20)
    parser.add_argument("--max-gap-factor", type=float, default=3.0)
    args = parser.parse_args()

    raw_frame = load_microsoft_series(args.data)
    prepared_frame, preparation_report = prepare_microsoft_model_frame(raw_frame)

    static_report = build_robust_zscore_report(prepared_frame)
    static_report["preparation"] = preparation_report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(static_report, indent=2) + "\\n", encoding="utf-8")

    rolling_report = build_causal_rolling_report(
        prepared_frame,
        window=args.rolling_window,
        min_periods=args.rolling_min_periods,
        max_gap_factor=args.max_gap_factor,
    )
    rolling_report["preparation"] = preparation_report
    args.rolling_output.parent.mkdir(parents=True, exist_ok=True)
    args.rolling_output.write_text(
        json.dumps(rolling_report, indent=2) + "\\n", encoding="utf-8"
    )

    for name, report in (
        ("Static robust z-score", static_report),
        ("Causal rolling detector", rolling_report),
    ):
        metrics = report["test_micro_metrics"]
        tuned = report["validation_tuned_test_micro_metrics"]
        print(f"{name} — test scoring coverage: {report['test_scoring_coverage']:.4f}")
        print(f"{name} — fixed-threshold precision: {metrics['precision']:.4f}")
        print(f"{name} — fixed-threshold recall: {metrics['recall']}")
        print(f"{name} — fixed-threshold F1: {metrics['f1']}")
        print(f"{name} — validation-tuned precision: {tuned['precision']:.4f}")
        print(f"{name} — validation-tuned recall: {tuned['recall']}")
        print(f"{name} — validation-tuned F1: {tuned['f1']}")
    print(f"Static report: {args.output}")
    print(f"Rolling report: {args.rolling_output}")


if __name__ == "__main__":
    main()
