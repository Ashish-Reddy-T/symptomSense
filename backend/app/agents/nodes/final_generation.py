"""Final response generation node."""

from __future__ import annotations

import logging
from typing import Any

from ...core.settings import Settings
from ...services.rag_service import GeminiClient

logger = logging.getLogger(__name__)


def _format_context(documents: list[dict]) -> tuple[str, list[dict], float | None]:
    if not documents:
        return "No supporting documents retrieved.", [], None
    lines: list[str] = []
    citations: list[dict] = []
    total_score = 0.0
    scored = 0
    for idx, doc in enumerate(documents, start=1):
        text = (doc.get("text") or "").strip()
        truncated = text[:750] + ("…" if len(text) > 750 else "")
        lines.append(f"[doc{idx}] {truncated}")
        citations.append(
            {
                "label": f"doc{idx}",
                "source": doc.get("metadata", {}).get("source_file") or doc.get("metadata", {}).get("source"),
                "score": doc.get("score"),
            }
        )
        score = doc.get("score")
        if isinstance(score, (int, float)):
            total_score += float(score)
            scored += 1
    avg_score = (total_score / scored) if scored else None
    return "\n".join(lines), citations, avg_score


def _format_image_analysis(image_analysis: dict | None) -> str:
    if not image_analysis:
        return "No image supplied."
    if "label" in image_analysis:
        conf = image_analysis.get("confidence", 0)
        return f"Prediction: {image_analysis['label']} (confidence {conf:.2f})."
    return "Image analysis unavailable."


async def final_generation(
    state: dict[str, Any],
    *,
    gemini: GeminiClient,
    settings: Settings,
) -> dict[str, Any]:
    question = (state.get("text_query") or "Describe the attached image.").strip()
    context_text, citations, avg_score = _format_context(state.get("rag_documents", []))
    image_summary = _format_image_analysis(state.get("image_analysis"))

    prompt = f"""
You are an evidence-focused medical assistant helping clinicians during a hackathon demo.
Use the supplied sources to craft an accurate, concise answer. Follow these rules:
- Prefer clinical, verifiable language; do not invent facts.
- Cite evidence inline using [docN] notation when referencing a context snippet.
- If context is insufficient or uncertain, clearly state limitations.
- Finish with a short bullet list of recommended follow-up actions.

Context snippets:
{context_text}

Image insights:
{image_summary}

User query:
{question}

Respond in Markdown.
"""
    try:
        answer = gemini.generate_with_fallback(prompt)
    except Exception as exc:  # pragma: no cover - LLM failure path
        logger.exception("final_generation_failed", error=str(exc))
        state["final_answer"] = "I encountered an error while generating the response."
        state.setdefault("warnings", []).append("LLM generation failed; using fallback messaging.")
        return state

    state["final_answer"] = answer.strip()
    state["citations"] = citations
    state["avg_context_score"] = avg_score
    state.setdefault("logprobs", [])
    state["raw_prompt"] = prompt
    return state
