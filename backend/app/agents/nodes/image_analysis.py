"""Image analysis node."""

from __future__ import annotations

import logging
from typing import Any

from ...core.settings import Settings
from ...services.image_service import ViTImageClassifier

logger = logging.getLogger(__name__)


async def image_analysis(state: dict[str, Any], *, classifier: ViTImageClassifier, settings: Settings) -> dict[str, Any]:
    image_data = state.get("image_data")
    if not image_data:
        return state
    try:
        prediction = classifier.predict_from_base64(image_data)
        state["image_analysis"] = {
            "label": prediction.label,
            "confidence": prediction.confidence,
            "scores": prediction.scores,
        }
    except Exception as exc:  # pragma: no cover - model runtime errors
        logger.exception("image_analysis_failed", error=str(exc))
        state["image_analysis_error"] = str(exc)
    return state
