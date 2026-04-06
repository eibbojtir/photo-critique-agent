from __future__ import annotations

from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any, Optional

from PIL import ExifTags, Image

from photo_critique_agent.models.photo import ExifMetadata

EXIF_TAG_NAMES = ExifTags.TAGS


def extract_exif_metadata(image_path: Path) -> Optional[ExifMetadata]:
    """Extract a small normalized EXIF subset from a JPEG."""
    with Image.open(image_path) as image:
        width, height = image.size
        raw_exif = image.getexif()

    if not raw_exif:
        return ExifMetadata(width_px=width, height_px=height)

    exif_by_name = {
        EXIF_TAG_NAMES.get(tag_id, str(tag_id)): value for tag_id, value in raw_exif.items()
    }

    return ExifMetadata(
        camera_make=_string_or_none(exif_by_name.get("Make")),
        camera_model=_string_or_none(exif_by_name.get("Model")),
        lens_model=_string_or_none(exif_by_name.get("LensModel")),
        captured_at=_parse_captured_at(exif_by_name),
        focal_length_mm=_float_or_none(exif_by_name.get("FocalLength")),
        aperture=_float_or_none(exif_by_name.get("FNumber")),
        shutter_speed_s=_parse_exposure_time(exif_by_name),
        iso=_int_or_none(exif_by_name.get("ISOSpeedRatings")),
        width_px=width,
        height_px=height,
    )


def _string_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, tuple) and len(value) == 2 and value[1]:
        return float(Fraction(value[0], value[1]))
    try:
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _int_or_none(value: Any) -> Optional[int]:
    numeric_value = _float_or_none(value)
    if numeric_value is None:
        return None
    return int(numeric_value)


def _parse_exposure_time(exif_by_name: dict[str, Any]) -> Optional[float]:
    return _float_or_none(exif_by_name.get("ExposureTime"))


def _parse_captured_at(exif_by_name: dict[str, Any]) -> Optional[datetime]:
    for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
        value = exif_by_name.get(key)
        if not value:
            continue
        try:
            return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            continue
    return None
