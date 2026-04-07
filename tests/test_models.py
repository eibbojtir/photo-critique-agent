from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from photo_critique_agent.models.critique import AnalysisOptions, CritiqueContext
from photo_critique_agent.models.job import CritiqueJobConfig
from photo_critique_agent.models.persona import PersonaConfig, PersonaRubric
from photo_critique_agent.models.report import CritiqueFinding, CritiqueReport
from photo_critique_agent.personas import list_personas, load_persona


def test_job_config_accepts_existing_paths(tmp_path: Path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    metadata_csv = tmp_path / "metadata.csv"
    metadata_csv.write_text("filename,title\nbird.jpg,Heron\n", encoding="utf-8")

    job = CritiqueJobConfig(
        image_dir=image_dir,
        metadata_csv=metadata_csv,
        persona_name="wildlife",
    )

    assert job.output_dir == Path("reports")


def test_job_config_rejects_missing_metadata_csv(tmp_path: Path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    with pytest.raises(ValidationError):
        CritiqueJobConfig(
            image_dir=image_dir,
            metadata_csv=tmp_path / "missing.csv",
            persona_name="wildlife",
        )


def test_persona_rubric_enforces_weight_bounds() -> None:
    with pytest.raises(ValidationError):
        PersonaRubric(
            composition=0,
            technical_quality=7,
            storytelling=8,
            subject_impact=9,
            ethics=10,
        )


def test_bundled_wildlife_persona_loads() -> None:
    persona = load_persona("wildlife")

    assert isinstance(persona, PersonaConfig)
    assert persona.name == "wildlife"
    assert "field ethics" in persona.focus_areas


def test_report_requires_valid_severity() -> None:
    with pytest.raises(ValidationError):
        CritiqueFinding(
            category="composition",
            severity="critical",
            summary="Subject is clipped.",
            recommendation="Leave more breathing room in frame.",
        )


def test_report_schema_accepts_valid_payload() -> None:
    report = CritiqueReport(
        filename="owl.jpg",
        persona="wildlife",
        score_overall=8.5,
        strengths=["Good catchlight"],
        opportunities=["Reduce branch overlap near the eye"],
        findings=[
            CritiqueFinding(
                category="subject_impact",
                severity="strong",
                summary="The pose carries strong attention.",
                recommendation="Preserve this framing style for similar encounters.",
            )
        ],
    )

    assert report.findings[0].severity == "strong"


def test_analysis_options_normalizes_valid_style() -> None:
    options = AnalysisOptions(style="  Saul Leiter  ")

    assert options.style == "Saul Leiter"


def test_analysis_options_rejects_invalid_style_characters() -> None:
    with pytest.raises(ValidationError):
        AnalysisOptions(style="<script>")


def test_critique_context_defaults_are_typed() -> None:
    context = CritiqueContext()

    assert context.rating is None
    assert context.keywords == []
    assert context.style is None


def test_list_personas_includes_new_personas() -> None:
    personas = list_personas()

    assert "street" in personas
    assert "travel" in personas
