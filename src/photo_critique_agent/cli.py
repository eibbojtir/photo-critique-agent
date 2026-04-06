from __future__ import annotations

from pathlib import Path
from typing import Optional

import json
import typer

from photo_critique_agent.critique import analyze_assets
from photo_critique_agent.ingestion import inspect_photo_assets
from photo_critique_agent.models.job import CritiqueJobConfig
from photo_critique_agent.personas import load_persona

app = typer.Typer(
    help="Local-first photo critique agent for structured image review workflows."
)


@app.command()
def critique(
    image_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    metadata_csv: Optional[Path] = typer.Option(
        None,
        "--metadata-csv",
        help="Optional CSV file with supplemental photo metadata.",
    ),
    persona: str = typer.Option("wildlife", "--persona", help="Persona name to use."),
) -> None:
    """Validate inputs and print the scaffolded job configuration."""
    job = CritiqueJobConfig(
        image_dir=image_dir,
        metadata_csv=metadata_csv,
        persona_name=persona,
    )
    typer.echo(job.model_dump_json(indent=2))


@app.command("inspect")
def inspect_command(
    images_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    metadata: Optional[Path] = typer.Option(
        None,
        "--metadata",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Optional CSV file with supplemental photo metadata.",
    ),
) -> None:
    """Inspect JPEG assets and write normalized metadata to disk."""
    assets = inspect_photo_assets(images_dir=images_dir, metadata_csv=metadata)

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "assets.json"
    output_path.write_text(
        json.dumps(
            [asset.model_dump(mode="json") for asset in assets],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    exif_count = sum(
        1
        for asset in assets
        if asset.exif
        and any(
            value is not None
            for key, value in asset.exif.model_dump().items()
            if key not in {"width_px", "height_px"}
        )
    )
    supplemental_count = sum(1 for asset in assets if asset.supplemental is not None)

    typer.echo(f"Found {len(assets)} JPEG images in {images_dir}")
    typer.echo(f"EXIF extracted for {exif_count} images")
    typer.echo(f"Supplemental metadata merged for {supplemental_count} images")
    typer.echo(f"Wrote normalized assets to {output_path}")


@app.command("analyze")
def analyze_command(
    images_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    metadata: Optional[Path] = typer.Option(
        None,
        "--metadata",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Optional CSV file with supplemental photo metadata.",
    ),
    persona: str = typer.Option(..., "--persona", help="Persona name to use."),
) -> None:
    """Analyze normalized photo assets with a placeholder evaluator."""
    assets = inspect_photo_assets(images_dir=images_dir, metadata_csv=metadata)
    persona_config = load_persona(persona)
    results = analyze_assets(assets=assets, persona=persona_config)

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "critique_results.json"
    output_path.write_text(
        json.dumps([result.model_dump(mode="json") for result in results], indent=2) + "\n",
        encoding="utf-8",
    )

    keep_count = sum(1 for result in results if result.recommendation == "keep")
    average_score = round(
        sum(result.score for result in results) / len(results), 2
    ) if results else 0.0

    typer.echo(f"Analyzed {len(results)} JPEG images with persona '{persona_config.name}'")
    typer.echo(f"Keep recommendations: {keep_count}")
    typer.echo(f"Average score: {average_score:.2f}")
    typer.echo(f"Wrote critique results to {output_path}")


if __name__ == "__main__":
    app()
