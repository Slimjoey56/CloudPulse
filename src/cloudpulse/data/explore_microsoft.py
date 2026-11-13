"""Generate per-series exploratory summaries for the prepared Microsoft dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cloudpulse.data.exploration import build_exploration_report
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
        default=Path("reports/generated/microsoft_cloud_monitoring_exploration.json"),
        help="Path for the JSON exploration report",
    )
    args = parser.parse_args()

    raw_frame = load_microsoft_series(args.data)
    prepared_frame, preparation_report = prepare_microsoft_model_frame(raw_frame)
    report = build_exploration_report(prepared_frame)
    report["preparation"] = preparation_report

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Series: {report['series_count']}")
    print(f"Prepared rows: {report['row_count']}")
    print(f"Missing measurements retained: {report['missing_value_count']}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
