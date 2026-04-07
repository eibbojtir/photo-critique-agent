from __future__ import annotations

from typing import Literal, Optional
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator


KeepRecommendation = Literal["keep", "pass"]


class AnalysisOptions(BaseModel):
    """Runtime analysis settings that are independent from persona YAML."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    style: Optional[str] = Field(default=None, max_length=80)

    @field_validator("style")
    @classmethod
    def validate_style(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = unicodedata.normalize("NFKC", value).strip()
        if not normalized:
            return None
        if any(ord(char) < 32 or ord(char) == 127 for char in normalized):
            raise ValueError("Style must not contain control characters.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,'&()-")
        invalid = sorted({char for char in normalized if char not in allowed})
        if invalid:
            raise ValueError(
                "Style may only contain letters, numbers, spaces, and basic punctuation (.,'&()-)."
            )

        return normalized


class CritiqueContext(BaseModel):
    """Typed metadata attached to each critique result."""

    model_config = ConfigDict(extra="forbid")

    rating: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    style: Optional[str] = None


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
    context: CritiqueContext = Field(default_factory=CritiqueContext)


class CritiqueResultBundle(BaseModel):
    """Collection of critique results written by the analyze pipeline."""

    model_config = ConfigDict(extra="forbid")

    results: list[CritiqueResult] = Field(default_factory=list)
