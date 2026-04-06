from __future__ import annotations

import csv
from pathlib import Path

from photo_critique_agent.models.photo import SupplementalMetadata


def load_supplemental_metadata(metadata_csv: Path | None) -> dict[str, SupplementalMetadata]:
    """Load CSV metadata keyed by image filename."""
    if metadata_csv is None:
        return {}

    with metadata_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "filename" not in reader.fieldnames:
            raise ValueError("metadata CSV must include a 'filename' column")

        metadata_by_filename: dict[str, SupplementalMetadata] = {}
        for row in reader:
            filename = (row.get("filename") or "").strip()
            if not filename:
                continue

            values = {
                key: value
                for key, value in row.items()
                if key != "filename" and value is not None and value != ""
            }
            metadata_by_filename[filename] = SupplementalMetadata(
                filename=filename,
                values=values,
            )

    return metadata_by_filename
