from __future__ import annotations

from abc import ABC, abstractmethod

from photo_critique_agent.models.critique import CritiqueResult
from photo_critique_agent.models.persona import PersonaConfig
from photo_critique_agent.models.photo import PhotoAsset


class CritiqueEvaluator(ABC):
    """Interface for metadata-only or future model-backed evaluators."""

    @abstractmethod
    def evaluate(
        self,
        asset: PhotoAsset,
        persona: PersonaConfig,
        style: str | None = None,
    ) -> CritiqueResult:
        """Return a structured critique for one photo asset."""


class MetadataPlaceholderEvaluator(CritiqueEvaluator):
    """Deterministic scoring based on EXIF and supplemental metadata only."""

    def evaluate(
        self,
        asset: PhotoAsset,
        persona: PersonaConfig,
        style: str | None = None,
    ) -> CritiqueResult:
        exif = asset.exif
        supplemental_values = asset.supplemental.values if asset.supplemental else {}

        score = 6.0
        strengths: list[str] = []
        weaknesses: list[str] = []

        focal_length = exif.focal_length_mm if exif else None
        if focal_length is not None:
            if focal_length >= 400:
                score += 0.8
                strengths.append("Long focal length supports strong subject isolation.")
            elif focal_length >= 200:
                score += 0.4
                strengths.append("Telephoto reach helps keep the subject prominent.")
            else:
                weaknesses.append("Shorter focal length may make subject separation harder.")
        else:
            weaknesses.append("Missing focal length leaves subject reach unclear.")

        shutter_speed = exif.shutter_speed_s if exif else None
        if shutter_speed is not None:
            if shutter_speed <= 1 / 1000:
                score += 0.6
                strengths.append("Fast shutter speed should help preserve feather and fur detail.")
            elif shutter_speed <= 1 / 500:
                score += 0.3
                strengths.append("Shutter speed is reasonable for moderate subject motion.")
            else:
                score -= 0.5
                weaknesses.append("Slower shutter speed increases the chance of motion blur.")
        else:
            weaknesses.append("Missing shutter speed makes motion control harder to judge.")

        iso = exif.iso if exif else None
        if iso is not None:
            if iso >= 3200:
                score -= 1.0
                weaknesses.append("Very high ISO may noticeably soften fine detail.")
            elif iso >= 1600:
                score -= 0.5
                weaknesses.append("Elevated ISO may trade away some image cleanliness.")
            else:
                strengths.append("ISO stays in a range that should preserve cleaner files.")
        else:
            weaknesses.append("ISO metadata is missing, so noise tradeoffs are less clear.")

        rating = supplemental_values.get("rating")
        keywords = _parse_keywords(supplemental_values.get("keywords"))

        if rating:
            strengths.append(f"Existing rating context: {rating}.")
        if keywords:
            strengths.append(f"Keywords emphasize {', '.join(keywords[:3])}.")
        if style:
            strengths.append(
                f"Style study lens applied: {style}, with feedback nudged toward that artist's visual priorities."
            )

        score = max(0.0, min(10.0, round(score, 1)))
        recommendation = "keep" if score >= 6.5 else "pass"

        if recommendation == "keep":
            strengths.append(
                f"{persona.name.capitalize()} persona fit is solid for {persona.focus_areas[0]}."
            )
        else:
            weaknesses.append(
                f"Metadata signals are not yet strong enough for a confident {persona.name} keep."
            )

        critique = _build_critique_paragraph(
            asset=asset,
            persona=persona,
            score=score,
            recommendation=recommendation,
            rating=rating,
            keywords=keywords,
            style=style,
        )

        return CritiqueResult(
            filename=asset.filename,
            persona=persona.name,
            score=score,
            strengths=_dedupe(strengths),
            weaknesses=_dedupe(weaknesses),
            recommendation=recommendation,
            critique=critique,
            context={
                "rating": rating,
                "keywords": keywords,
                "style": style,
            },
        )


def _parse_keywords(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _build_critique_paragraph(
    *,
    asset: PhotoAsset,
    persona: PersonaConfig,
    score: float,
    recommendation: str,
    rating: object,
    keywords: list[str],
    style: str | None,
) -> str:
    focal_length = asset.exif.focal_length_mm if asset.exif else None
    shutter_speed = asset.exif.shutter_speed_s if asset.exif else None
    iso = asset.exif.iso if asset.exif else None

    details: list[str] = [
        f"This placeholder {persona.name} critique scores the frame at {score:.1f}/10 and lands on a {recommendation} recommendation.",
    ]
    if focal_length is not None:
        details.append(f"The {focal_length:.0f}mm field of view suggests useful subject reach.")
    if shutter_speed is not None:
        details.append(f"A shutter speed of {shutter_speed:.4f}s informs the technical motion assessment.")
    if iso is not None:
        details.append(f"ISO {iso} contributes to the noise tradeoff estimate.")
    if rating:
        details.append(f"CSV context includes a prior rating of {rating}.")
    if keywords:
        details.append(f"Keywords noted for this frame: {', '.join(keywords)}.")
    if style:
        details.append(
            f"Using a {style}-inspired reading, the critique leans toward the visual traits associated with that body of work."
        )
    return " ".join(details)
