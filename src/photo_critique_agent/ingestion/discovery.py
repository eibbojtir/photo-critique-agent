from __future__ import annotations

from pathlib import Path

JPEG_SUFFIXES = {".jpg", ".jpeg"}


def discover_images(images_dir: Path) -> list[Path]:
    """Recursively find JPEG images beneath a directory."""
    return sorted(
        path
        for path in images_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in JPEG_SUFFIXES
    )
