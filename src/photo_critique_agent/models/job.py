from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CritiqueJobConfig(BaseModel):
    """Validated runtime input for a critique run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    image_dir: Path = Field(description="Directory containing JPEG source images.")
    metadata_csv: Optional[Path] = Field(
        default=None,
        description="Optional CSV with supplemental metadata keyed by filename.",
    )
    persona_name: str = Field(description="Persona identifier to load from YAML.")
    output_dir: Path = Field(default=Path("reports"))

    @model_validator(mode="after")
    def validate_paths(self) -> "CritiqueJobConfig":
        if not self.image_dir.exists() or not self.image_dir.is_dir():
            raise ValueError("image_dir must be an existing directory")
        if self.metadata_csv is not None and (
            not self.metadata_csv.exists() or not self.metadata_csv.is_file()
        ):
            raise ValueError("metadata_csv must be an existing file when provided")
        return self
