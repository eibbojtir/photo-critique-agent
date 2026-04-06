from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from typer.testing import CliRunner

from photo_critique_agent.cli import app
from photo_critique_agent.ingestion import (
    discover_images,
    extract_exif_metadata,
    inspect_photo_assets,
    load_supplemental_metadata,
)


def test_image_discovery_recursively_finds_only_jpegs(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    nested_dir = images_dir / "nested"
    nested_dir.mkdir(parents=True)

    _write_jpeg(images_dir / "owl.JPG", color=(120, 90, 40))
    _write_jpeg(nested_dir / "fox.jpeg", color=(40, 90, 120))
    (nested_dir / "notes.txt").write_text("ignore me", encoding="utf-8")

    discovered = discover_images(images_dir)

    assert [path.name for path in discovered] == ["fox.jpeg", "owl.JPG"]


def test_exif_extraction_reads_realistic_camera_fields(tmp_path: Path) -> None:
    image_path = tmp_path / "heron.jpg"
    _write_jpeg(
        image_path,
        color=(75, 110, 150),
        exif_fields={
            271: "Canon",
            272: "EOS R5",
            42036: "RF100-500mm F4.5-7.1 L IS USM",
            36867: "2025:06:14 07:32:11",
            33437: (56, 10),
            33434: (1, 1000),
            37386: (500, 1),
            34855: 1600,
        },
    )

    exif = extract_exif_metadata(image_path)

    assert exif is not None
    assert exif.camera_make == "Canon"
    assert exif.camera_model == "EOS R5"
    assert exif.lens_model == "RF100-500mm F4.5-7.1 L IS USM"
    assert exif.captured_at is not None
    assert exif.captured_at.isoformat() == "2025-06-14T07:32:11"
    assert exif.aperture == 5.6
    assert exif.shutter_speed_s == 0.001
    assert exif.focal_length_mm == 500.0
    assert exif.iso == 1600
    assert exif.width_px == 1600
    assert exif.height_px == 1067


def test_csv_merge_attaches_rows_by_filename(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(images_dir / "hawk.jpg", color=(20, 30, 40))
    _write_jpeg(images_dir / "eagle.jpg", color=(30, 40, 50))

    metadata_csv = tmp_path / "metadata.csv"
    _write_metadata_csv(
        metadata_csv,
        [
            {"filename": "hawk.jpg", "title": "Perched hawk", "rating": "4"},
            {"filename": "missing.jpg", "title": "Not used", "rating": "2"},
        ],
    )

    assets = inspect_photo_assets(images_dir, metadata_csv)
    assets_by_name = {asset.filename: asset for asset in assets}

    assert assets_by_name["hawk.jpg"].supplemental is not None
    assert assets_by_name["hawk.jpg"].supplemental.values == {
        "title": "Perched hawk",
        "rating": "4",
    }
    assert assets_by_name["eagle.jpg"].supplemental is None


def test_missing_metadata_is_handled_cleanly(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(images_dir / "sparrow.jpg", color=(90, 80, 70))

    assets = inspect_photo_assets(images_dir)

    assert len(assets) == 1
    assert assets[0].filename == "sparrow.jpg"
    assert assets[0].supplemental is None
    assert assets[0].exif is not None
    assert assets[0].exif.camera_make is None
    assert assets[0].exif.width_px == 1600
    assert assets[0].exif.height_px == 1067


def test_load_supplemental_metadata_requires_filename_column(tmp_path: Path) -> None:
    metadata_csv = tmp_path / "metadata.csv"
    metadata_csv.write_text("title,rating\nBird,5\n", encoding="utf-8")

    try:
        load_supplemental_metadata(metadata_csv)
    except ValueError as exc:
        assert "filename" in str(exc)
    else:
        raise AssertionError("Expected metadata loader to reject CSV without filename")


def test_inspect_cli_writes_normalized_assets_json(tmp_path: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        images_dir = Path("images")
        images_dir.mkdir()
        _write_jpeg(images_dir / "warbler.jpg", color=(140, 130, 50))

        metadata_csv = Path("metadata.csv")
        _write_metadata_csv(
            metadata_csv,
            [{"filename": "warbler.jpg", "title": "Yellow warbler", "location": "Wetlands"}],
        )

        result = runner.invoke(
            app,
            ["inspect", str(images_dir), "--metadata", str(metadata_csv)],
        )

        assert result.exit_code == 0
        assert "Found 1 JPEG images" in result.stdout
        assert "Wrote normalized assets to output/assets.json" in result.stdout

        payload = json.loads(Path("output/assets.json").read_text(encoding="utf-8"))
        assert payload[0]["filename"] == "warbler.jpg"
        assert payload[0]["supplemental"]["values"]["title"] == "Yellow warbler"


def _write_jpeg(
    path: Path,
    *,
    color: tuple[int, int, int],
    exif_fields: Optional[dict[int, object]] = None,
) -> None:
    from PIL import Image

    image = Image.new("RGB", (1600, 1067), color=color)
    if exif_fields:
        exif = Image.Exif()
        for tag, value in exif_fields.items():
            exif[tag] = value
        image.save(path, format="JPEG", quality=92, exif=exif)
        return

    image.save(path, format="JPEG", quality=92)


def _write_metadata_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
