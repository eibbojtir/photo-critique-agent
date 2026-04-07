from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from photo_critique_agent.critique import analyze_assets
from photo_critique_agent.ingestion import inspect_photo_assets
from photo_critique_agent.models.critique import AnalysisOptions
from photo_critique_agent.personas import load_persona
from photo_critique_agent.reporting import build_session_report, write_report_outputs


def test_build_session_report_ranks_top_images_and_runners_up(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(images_dir / "eagle.jpg", color=(90, 90, 120), exif_fields={33434: (1, 2000), 37386: (500, 1), 34855: 640})
    _write_jpeg(images_dir / "owl.jpg", color=(70, 80, 90), exif_fields={33434: (1, 1000), 37386: (400, 1), 34855: 1000})
    _write_jpeg(images_dir / "otter.jpg", color=(100, 80, 60), exif_fields={33434: (1, 640), 37386: (300, 1), 34855: 1250})
    _write_jpeg(images_dir / "duck.jpg", color=(80, 100, 100), exif_fields={33434: (1, 250), 37386: (135, 1), 34855: 3200})

    persona = load_persona("wildlife")
    assets = inspect_photo_assets(images_dir)
    critiques = analyze_assets(assets, persona)
    report = build_session_report(assets, critiques, persona)

    assert report.summary.total_images == 4
    assert len(report.top_images) == 3
    assert len(report.runners_up) == 1
    assert report.top_images[0].critique.score >= report.top_images[1].critique.score
    assert report.entries[0].rank == 1
    assert report.runners_up[0].asset.filename == "duck.jpg"


def test_write_report_outputs_creates_json_markdown_and_html(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(images_dir / "warbler.jpg", color=(120, 120, 60), exif_fields={33434: (1, 1250), 37386: (500, 1), 34855: 800})
    metadata_csv = tmp_path / "metadata.csv"
    _write_metadata_csv(
        metadata_csv,
        [{"filename": "warbler.jpg", "rating": "5", "keywords": "warbler,migration,reeds"}],
    )

    persona = load_persona("wildlife")
    assets = inspect_photo_assets(images_dir, metadata_csv)
    critiques = analyze_assets(assets, persona, options=AnalysisOptions(style="Saul Leiter"))
    output_dir = tmp_path / "output"

    write_report_outputs(
        assets,
        critiques,
        persona,
        output_dir,
        options=AnalysisOptions(style="Saul Leiter"),
    )

    results_payload = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    markdown = (output_dir / "critique_report.md").read_text(encoding="utf-8")
    html = (output_dir / "critique_report.html").read_text(encoding="utf-8")

    assert results_payload["summary"]["total_images"] == 1
    assert results_payload["style"] == "Saul Leiter"
    assert results_payload["entries"][0]["asset"]["filename"] == "warbler.jpg"
    assert results_payload["entries"][0]["critique"]["context"]["rating"] == "5"
    assert results_payload["entries"][0]["critique"]["context"]["style"] == "Saul Leiter"
    assert "## Session Summary" in markdown
    assert "## Top 3 Images" in markdown
    assert "Style lens: Saul Leiter" in markdown
    assert "warbler.jpg" in markdown
    assert "<h2>Ranked Gallery</h2>" in html
    assert "score-badge" in html
    assert "Style lens: Saul Leiter" in html
    assert "warbler.jpg" in html


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
