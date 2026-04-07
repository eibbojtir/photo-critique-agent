"""Bundled persona configurations."""

from __future__ import annotations

from importlib.resources import files

import yaml

from photo_critique_agent.models.persona import PersonaConfig


def list_personas() -> list[str]:
    """Return bundled persona names in sorted order."""
    return sorted(
        resource.name.removesuffix(".yaml")
        for resource in files(__name__).iterdir()
        if resource.name.endswith(".yaml")
    )


def load_persona(name: str) -> PersonaConfig:
    """Load a bundled persona YAML by name."""
    persona_path = files(__name__).joinpath(f"{name}.yaml")
    if not persona_path.is_file():
        available = ", ".join(list_personas())
        raise FileNotFoundError(
            f"Unknown persona '{name}'. Available personas: {available}."
        )
    raw_data = yaml.safe_load(persona_path.read_text(encoding="utf-8"))
    return PersonaConfig.model_validate(raw_data)


__all__ = ["list_personas", "load_persona"]
