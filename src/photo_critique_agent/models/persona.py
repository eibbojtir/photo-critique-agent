from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PersonaTone = Literal["analytical", "encouraging", "direct"]


class PersonaRubric(BaseModel):
    """Weighted dimensions for critique emphasis."""

    model_config = ConfigDict(extra="forbid")

    composition: int = Field(ge=1, le=10)
    technical_quality: int = Field(ge=1, le=10)
    storytelling: int = Field(ge=1, le=10)
    subject_impact: int = Field(ge=1, le=10)
    ethics: int = Field(ge=1, le=10)


class PersonaConfig(BaseModel):
    """YAML-backed persona definition."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str
    description: str
    tone: PersonaTone
    audience: str
    goals: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    rubric: PersonaRubric

