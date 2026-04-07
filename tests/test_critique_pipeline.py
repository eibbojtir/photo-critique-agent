from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

import pytest
from typer.testing import CliRunner

from photo_critique_agent.cli import app
from photo_critique_agent.critique import analyze_assets
from photo_critique_agent.ingestion import inspect_photo_assets
from photo_critique_agent.models.critique import AnalysisOptions
from photo_critique_agent.personas import load_persona


def test_wildlife_persona_loads_expected_focus() -> None:
    persona = load_persona("wildlife")

    assert persona.name == "wildlife"
    assert persona.tone == "analytical"
    assert "field ethics" in persona.focus_areas
    assert persona.rubric.subject_impact == 10


def test_travel_and_street_personas_load() -> None:
    travel = load_persona("travel")
    street = load_persona("street")

    assert travel.name == "travel"
    assert "sense of place" in travel.focus_areas
    assert street.name == "street"
    assert "visual layering" in street.focus_areas


def test_analyze_assets_generates_keep_for_strong_metadata(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(
        images_dir / "eagle.jpg",
        color=(80, 90, 110),
        exif_fields={
            271: "Canon",
            272: "EOS R5",
            33434: (1, 2000),
            37386: (500, 1),
            34855: 800,
        },
    )
    metadata_csv = tmp_path / "metadata.csv"
    _write_metadata_csv(
        metadata_csv,
        [{"filename": "eagle.jpg", "rating": "5", "keywords": "eagle,flight,banking"}],
    )

    assets = inspect_photo_assets(images_dir, metadata_csv)
    results = analyze_assets(assets, load_persona("wildlife"))

    assert len(results) == 1
    result = results[0]
    assert result.score >= 7.0
    assert result.recommendation == "keep"
    assert result.context.rating == "5"
    assert result.context.keywords == ["eagle", "flight", "banking"]
    assert any("subject isolation" in item.lower() for item in result.strengths)


def test_analyze_assets_includes_style_context_when_requested(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(
        images_dir / "crosswalk.jpg",
        color=(90, 90, 110),
        exif_fields={
            33434: (1, 1000),
            37386: (300, 1),
            34855: 1250,
        },
    )

    assets = inspect_photo_assets(images_dir)
    results = analyze_assets(
        assets,
        load_persona("street"),
        options=AnalysisOptions(style="Saul Leiter"),
    )

    assert len(results) == 1
    result = results[0]
    assert result.context.style == "Saul Leiter"
    assert "Saul Leiter-inspired reading" in result.critique
    assert any("style study lens applied" in item.lower() for item in result.strengths)


def test_analyze_assets_generates_pass_for_noisy_slow_metadata(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_jpeg(
        images_dir / "owl.jpg",
        color=(45, 55, 65),
        exif_fields={
            33434: (1, 125),
            37386: (135, 1),
            34855: 6400,
        },
    )

    assets = inspect_photo_assets(images_dir)
    results = analyze_assets(assets, load_persona("wildlife"))

    assert len(results) == 1
    result = results[0]
    assert result.score <= 5.5
    assert result.recommendation == "pass"
    assert any("motion blur" in item.lower() for item in result.weaknesses)
    assert "pass recommendation" in result.critique


def test_analyze_cli_writes_critique_results(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        images_dir = Path("images")
        images_dir.mkdir()
        _write_jpeg(
            images_dir / "otter.jpg",
            color=(120, 100, 80),
            exif_fields={
                33434: (1, 1000),
                37386: (400, 1),
                34855: 1250,
            },
        )
        metadata_csv = Path("metadata.csv")
        _write_metadata_csv(
            metadata_csv,
            [{"filename": "otter.jpg", "rating": "4", "keywords": "otter,water,behavior"}],
        )

        result = runner.invoke(
            app,
            ["analyze", str(images_dir), "--metadata", str(metadata_csv), "--persona", "wildlife"],
        )

        assert result.exit_code == 0
        assert "Analyzed 1 JPEG images with persona 'wildlife'" in result.stdout
        assert "Wrote output/results.json" in result.stdout
        assert "Wrote output/critique_report.md" in result.stdout
        assert "Wrote output/critique_report.html" in result.stdout

        payload = json.loads(Path("output/results.json").read_text(encoding="utf-8"))
        assert payload["entries"][0]["asset"]["filename"] == "otter.jpg"
        assert payload["entries"][0]["critique"]["persona"] == "wildlife"
        assert payload["entries"][0]["critique"]["context"]["rating"] == "4"


def test_analyze_cli_writes_style_to_results(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        images_dir = Path("images")
        images_dir.mkdir()
        _write_jpeg(
            images_dir / "street-scene.jpg",
            color=(110, 100, 90),
            exif_fields={
                33434: (1, 500),
                37386: (135, 1),
                34855: 1600,
            },
        )

        result = runner.invoke(
            app,
            [
                "analyze",
                str(images_dir),
                "--persona",
                "street",
                "--style",
                "Saul Leiter",
            ],
        )

        assert result.exit_code == 0
        assert "Style lens: Saul Leiter" in result.stdout

        payload = json.loads(Path("output/results.json").read_text(encoding="utf-8"))
        assert payload["persona"] == "street"
        assert payload["style"] == "Saul Leiter"
        assert payload["entries"][0]["critique"]["context"]["style"] == "Saul Leiter"


def test_analyze_cli_rejects_unknown_persona(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        images_dir = Path("images")
        images_dir.mkdir()
        _write_jpeg(images_dir / "frame.jpg", color=(100, 100, 100))

        result = runner.invoke(
            app,
            ["analyze", str(images_dir), "--persona", "unknown-persona"],
        )

        assert result.exit_code != 0
        assert "Unknown persona 'unknown-persona'" in result.stdout
        assert "commercial" in result.stdout
        assert "wildlife" in result.stdout


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("Saul\x07Leiter", "Style must not contain control characters."),
        ("<script>", "Style may only contain letters, numbers, spaces"),
        (" " * 3, "Style lens:"),
    ],
)
def test_style_validation_and_normalization(tmp_path: Path, style: str, expected: str) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        images_dir = Path("images")
        images_dir.mkdir()
        _write_jpeg(images_dir / "frame.jpg", color=(100, 100, 100))

        result = runner.invoke(
            app,
            ["analyze", str(images_dir), "--persona", "street", "--style", style],
        )

        if style.strip():
            assert result.exit_code != 0
            assert expected in result.stdout
        else:
            assert result.exit_code == 0
            assert expected not in result.stdout


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
