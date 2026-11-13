"""Evaluate a fixed-threshold robust z-score baseline on Microsoft telemetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cloudpulse.data.baselines import build_robust_zscore_report
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
        help="Path for the JSON baseline report",
    )
    args = parser.parse_args()

    raw_frame = load_microsoft_series(args.data)
    prepared_frame, preparation_report = prepare_microsoft_model_frame(raw_frame)
    report = build_robust_zscore_report(prepared_frame)
    report["preparation"] = preparation_report

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    metrics = report["test_micro_metrics"]
    print(f"Series evaluated: {len(report['series'])}")
    print(f"Test scored rows: {metrics['scored_rows']}")
    print(f"Test micro precision: {metrics['precision']}")
    print(f"Test micro recall: {metrics['recall']}")
    print(f"Test micro F1: {metrics['f1']}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
