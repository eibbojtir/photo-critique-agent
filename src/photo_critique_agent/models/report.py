from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from photo_critique_agent.models.critique import CritiqueResult
from photo_critique_agent.models.photo import PhotoAsset


class CritiqueFinding(BaseModel):
    """Single observation produced by the critique pipeline."""

    model_config = ConfigDict(extra="forbid")

    category: str
    severity: str = Field(pattern="^(info|note|warning|strong)$")
    summary: str
    recommendation: str


class CritiqueReport(BaseModel):
    """Structured critique output for one photo."""

    model_config = ConfigDict(extra="forbid")

    filename: str
    persona: str
    score_overall: float = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    findings: list[CritiqueFinding] = Field(default_factory=list)


class ReportBundle(BaseModel):
    """Combined report payload written to JSON and Markdown renderers."""

    model_config = ConfigDict(extra="forbid")

    reports: list[CritiqueReport] = Field(default_factory=list)


class SessionSummary(BaseModel):
    """Session-level rollup shown in generated reports."""

    model_config = ConfigDict(extra="forbid")

    total_images: int = Field(ge=0)
    keep_count: int = Field(ge=0)
    pass_count: int = Field(ge=0)
    average_score: float = Field(ge=0, le=10)


class RankedCritiqueEntry(BaseModel):
    """Photo asset paired with its critique result for reporting."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    asset: PhotoAsset
    critique: CritiqueResult


class CritiqueSessionReport(BaseModel):
    """Serializable bundle used for JSON, Markdown, and HTML outputs."""

    model_config = ConfigDict(extra="forbid")

    persona: str
    style: Optional[str] = None
    summary: SessionSummary
    top_images: list[RankedCritiqueEntry] = Field(default_factory=list)
    runners_up: list[RankedCritiqueEntry] = Field(default_factory=list)
    entries: list[RankedCritiqueEntry] = Field(default_factory=list)
