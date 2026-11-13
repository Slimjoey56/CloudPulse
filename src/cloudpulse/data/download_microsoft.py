"""Download a pinned snapshot of the Microsoft Cloud Monitoring Dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

SOURCE_COMMIT = "6a07a53c2fac495fb6831811df4c980d6c04bd10"
ARCHIVE_URL = f"https://codeload.github.com/microsoft/cloud-monitoring-dataset/zip/{SOURCE_COMMIT}"
EXPECTED_CSV_FILES = 60
EXPECTED_METADATA_FILES = 60


def sha256_file(path: Path) -> str:
    """Calculate a file's SHA-256 digest using bounded memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_dataset(output_dir: Path) -> dict[str, object]:
    """Download and safely extract only the pinned dataset directory."""
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(
            f"{output_dir} already exists; move it or remove it before downloading again"
        )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"User-Agent": "CloudPulse-research/0.1"},
    )

    with tempfile.TemporaryDirectory(dir=output_dir.parent) as temp_name:
        temp_dir = Path(temp_name)
        archive_path = temp_dir / "source.zip"
        with urllib.request.urlopen(request, timeout=60) as response:
            with archive_path.open("wb") as archive:
                shutil.copyfileobj(response, archive)

        archive_digest = sha256_file(archive_path)
        staging = temp_dir / "dataset"
        staging.mkdir()

        with zipfile.ZipFile(archive_path) as archive:
            selected = []
            for member in archive.infolist():
                parts = PurePosixPath(member.filename).parts
                if "data" not in parts:
                    continue
                data_index = parts.index("data")
                relative = PurePosixPath(*parts[data_index + 1 :])
                if not relative.parts or member.is_dir():
                    continue
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError(f"Unsafe archive path: {member.filename}")
                if relative.suffix.lower() not in {".csv", ".json"}:
                    continue
                selected.append((member, relative))

            for member, relative in selected:
                destination = staging.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)

        csv_count = sum(1 for path in staging.rglob("*.csv"))
        metadata_count = sum(1 for path in staging.rglob("*.json"))
        if csv_count != EXPECTED_CSV_FILES or metadata_count != EXPECTED_METADATA_FILES:
            raise ValueError(
                "Unexpected source inventory: "
                f"{csv_count} CSV and {metadata_count} JSON files; "
                f"expected {EXPECTED_CSV_FILES} and {EXPECTED_METADATA_FILES}"
            )

        manifest = {
            "dataset": "Microsoft Cloud Monitoring Dataset",
            "source_url": "https://github.com/microsoft/cloud-monitoring-dataset",
            "source_commit": SOURCE_COMMIT,
            "archive_url": ARCHIVE_URL,
            "archive_sha256": archive_digest,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "csv_files": csv_count,
            "metadata_files": metadata_count,
            "raw_data_bytes": sum(
                path.stat().st_size for path in staging.rglob("*") if path.is_file()
            ),
            "note": "Raw source data is retained locally and must not be committed to Git.",
        }
        (staging / "provenance.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        staging.rename(output_dir)

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/microsoft_cloud_monitoring"),
        help="Local destination for the raw dataset",
    )
    args = parser.parse_args()
    manifest = download_dataset(args.output)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
