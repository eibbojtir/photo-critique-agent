from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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

