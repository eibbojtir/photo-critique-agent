from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from photo_critique_agent.models.job import CritiqueJobConfig

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


if __name__ == "__main__":
    app()
