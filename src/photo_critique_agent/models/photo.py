from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExifMetadata(BaseModel):
    """Normalized EXIF fields extracted from a photo when present."""

    model_config = ConfigDict(extra="allow")

    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    captured_at: Optional[datetime] = None
    focal_length_mm: Optional[float] = Field(default=None, ge=0)
    aperture: Optional[float] = Field(default=None, gt=0)
    shutter_speed_s: Optional[float] = Field(default=None, gt=0)
    iso: Optional[int] = Field(default=None, gt=0)
    width_px: Optional[int] = Field(default=None, gt=0)
    height_px: Optional[int] = Field(default=None, gt=0)


class SupplementalMetadata(BaseModel):
    """Row-level metadata that may come from an external CSV."""

    model_config = ConfigDict(extra="allow")

    filename: str
    values: dict[str, Any] = Field(default_factory=dict)


class PhotoAsset(BaseModel):
    """Single photo plus metadata sources used during critique."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    filename: str
    path: Path
    relative_path: Optional[Path] = None
    exif: Optional[ExifMetadata] = None
    supplemental: Optional[SupplementalMetadata] = None
