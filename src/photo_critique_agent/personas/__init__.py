"""Bundled persona configurations."""

from __future__ import annotations

from importlib.resources import files

import yaml

from photo_critique_agent.models.persona import PersonaConfig


def load_persona(name: str) -> PersonaConfig:
    """Load a bundled persona YAML by name."""
    persona_path = files(__name__).joinpath(f"{name}.yaml")
    raw_data = yaml.safe_load(persona_path.read_text(encoding="utf-8"))
    return PersonaConfig.model_validate(raw_data)


__all__ = ["load_persona"]
