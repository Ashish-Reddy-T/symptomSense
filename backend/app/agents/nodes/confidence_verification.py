"""Confidence verification node."""

from __future__ import annotations

from typing import Any

from ...core.settings import Settings


async def confidence_verification(state: dict[str, Any], *, settings: Settings) -> dict[str, Any]:
    warnings = list(state.get("warnings", []))

    image_analysis = state.get("image_analysis") or {}
    confidence = image_analysis.get("confidence")
    if isinstance(confidence, (int, float)) and confidence < settings.MIN_IMAGE_CONFIDENCE:
        warning_msg = (
            "Image classifier confidence is "
            f"{confidence:.2f}, please corroborate with a specialist."
        )
        warnings.append(warning_msg)

    if not state.get("rag_documents"):
        warnings.append("No retrieval context was available; answer is based on general knowledge.")

    avg_score = state.get("avg_context_score")
    if isinstance(avg_score, (int, float)) and avg_score < 0.3:
        warnings.append("Retrieved passages had low similarity scores; verify details manually.")

    if warnings:
        formatted = "\n".join(f"- {note}" for note in warnings)
        quoted = formatted.replace("\n", "\n> ")
        note_block = "\n\n> **Confidence Notes**\n> " + quoted
        state["final_answer"] = f"{state.get('final_answer', '').strip()}" + note_block
    state["warnings"] = warnings
    return state
