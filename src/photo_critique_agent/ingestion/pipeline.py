from __future__ import annotations

from pathlib import Path

from photo_critique_agent.ingestion.csv_metadata import load_supplemental_metadata
from photo_critique_agent.ingestion.discovery import discover_images
from photo_critique_agent.ingestion.exif import extract_exif_metadata
from photo_critique_agent.models.photo import PhotoAsset


def inspect_photo_assets(
    images_dir: Path,
    metadata_csv: Path | None = None,
) -> list[PhotoAsset]:
    """Build normalized photo assets from files plus optional CSV metadata."""
    supplemental_by_filename = load_supplemental_metadata(metadata_csv)

    assets: list[PhotoAsset] = []
    for image_path in discover_images(images_dir):
        assets.append(
            PhotoAsset(
                filename=image_path.name,
                path=image_path.resolve(),
                relative_path=image_path.relative_to(images_dir),
                exif=extract_exif_metadata(image_path),
                supplemental=supplemental_by_filename.get(image_path.name),
            )
        )

    return assets
