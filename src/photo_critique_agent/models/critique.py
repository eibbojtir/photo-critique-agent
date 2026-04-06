from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


KeepRecommendation = Literal["keep", "pass"]


class CritiqueResult(BaseModel):
    """Structured critique output for one photo asset."""

    model_config = ConfigDict(extra="forbid")

    filename: str
    persona: str
    score: float = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: KeepRecommendation
    critique: str
    context: dict[str, Any] = Field(default_factory=dict)


class CritiqueResultBundle(BaseModel):
    """Collection of critique results written by the analyze pipeline."""

    model_config = ConfigDict(extra="forbid")

    results: list[CritiqueResult] = Field(default_factory=list)
