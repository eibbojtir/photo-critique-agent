from __future__ import annotations

from typing import Optional

from photo_critique_agent.critique.evaluator import (
    CritiqueEvaluator,
    MetadataPlaceholderEvaluator,
)
from photo_critique_agent.models.critique import AnalysisOptions, CritiqueResult
from photo_critique_agent.models.persona import PersonaConfig
from photo_critique_agent.models.photo import PhotoAsset


def analyze_assets(
    assets: list[PhotoAsset],
    persona: PersonaConfig,
    options: Optional[AnalysisOptions] = None,
    evaluator: Optional[CritiqueEvaluator] = None,
) -> list[CritiqueResult]:
    """Analyze normalized assets with the configured evaluator."""
    active_evaluator = evaluator or MetadataPlaceholderEvaluator()
    active_options = options or AnalysisOptions()
    return [active_evaluator.evaluate(asset, persona, options=active_options) for asset in assets]
