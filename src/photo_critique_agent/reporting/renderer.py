from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from photo_critique_agent.models.critique import CritiqueResult
from photo_critique_agent.models.persona import PersonaConfig
from photo_critique_agent.models.photo import PhotoAsset
from photo_critique_agent.models.report import (
    CritiqueSessionReport,
    RankedCritiqueEntry,
    SessionSummary,
)


def build_session_report(
    assets: list[PhotoAsset],
    critiques: list[CritiqueResult],
    persona: PersonaConfig,
    style: str | None = None,
) -> CritiqueSessionReport:
    """Pair assets with critiques, rank them, and compute session summary."""
    critiques_by_filename = {critique.filename: critique for critique in critiques}
    entries = [
        RankedCritiqueEntry(
            rank=index,
            asset=asset,
            critique=critiques_by_filename[asset.filename],
        )
        for index, asset in enumerate(
            sorted(
                assets,
                key=lambda item: (
                    -critiques_by_filename[item.filename].score,
                    item.filename.lower(),
                ),
            ),
            start=1,
        )
    ]

    keep_count = sum(1 for entry in entries if entry.critique.recommendation == "keep")
    total_images = len(entries)
    summary = SessionSummary(
        total_images=total_images,
        keep_count=keep_count,
        pass_count=total_images - keep_count,
        average_score=round(
            sum(entry.critique.score for entry in entries) / total_images, 2
        )
        if total_images
        else 0.0,
    )
    return CritiqueSessionReport(
        persona=persona.name,
        style=style,
        summary=summary,
        top_images=entries[:3],
        runners_up=entries[3:],
        entries=entries,
    )


def write_report_outputs(
    assets: list[PhotoAsset],
    critiques: list[CritiqueResult],
    persona: PersonaConfig,
    output_dir: Path,
    style: str | None = None,
) -> CritiqueSessionReport:
    """Write session JSON, Markdown, and HTML outputs into the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session_report = build_session_report(
        assets=assets,
        critiques=critiques,
        persona=persona,
        style=style,
    )

    environment = _build_template_environment()
    markdown = environment.get_template("report.md.j2").render(report=session_report)
    html = environment.get_template("report.html.j2").render(report=session_report)

    (output_dir / "results.json").write_text(
        json.dumps(session_report.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "critique_report.md").write_text(markdown, encoding="utf-8")
    (output_dir / "critique_report.html").write_text(html, encoding="utf-8")
    return session_report


def _build_template_environment() -> Environment:
    return Environment(
        loader=PackageLoader("photo_critique_agent", "templates"),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
