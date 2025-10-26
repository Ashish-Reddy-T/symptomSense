"""Final response generation node."""

from __future__ import annotations

import logging
from typing import Any

from ...core.settings import Settings
from ...models.schema import AgentAnswer
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
        metadata = doc.get("metadata", {})
        source = metadata.get("source_file") or metadata.get("source")
        citations.append({"label": f"doc{idx}", "source": source, "score": doc.get("score")})
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
Use the supplied sources to craft an accurate, concise answer. Respond as strict JSON
matching this schema:
{{
  "answer": "markdown string for the user",
  "citations": ["doc1", "doc2"],
  "follow_up": ["bullet item"],
  "warnings": ["confidence warnings"]
}}

Guidelines:
- Prefer clinical, verifiable language; do not invent facts.
- Cite evidence inline using [docN] notation when referencing a context snippet.
- Explicitly mention uncertainty when context is insufficient.
- Provide 2-3 follow_up actions tailored to the query.
- Include warnings if you are unsure about the recommendation.

Context snippets:
{context_text}

Image insights:
{image_summary}

User query:
{question}
"""
    try:
        raw = gemini.generate_with_fallback(prompt)
    except Exception as exc:  # pragma: no cover - LLM failure path
        logger.exception("final_generation_failed", error=str(exc))
        state["final_answer"] = "I encountered an error while generating the response."
        state.setdefault("warnings", []).append("LLM generation failed; using fallback messaging.")
        return state

    try:
        parsed = AgentAnswer.model_validate_json(raw)
    except Exception as exc:  # pragma: no cover - parsing errors
        logger.warning("final_generation_parse_failed", raw=raw, error=str(exc))
        parsed = AgentAnswer(answer=raw.strip(), citations=[], follow_up=[], warnings=[])

    answer_with_citations = parsed.answer.strip()
    state["final_answer"] = answer_with_citations
    state["citations"] = citations
    state.setdefault("warnings", [])
    if parsed.warnings:
        state["warnings"].extend(parsed.warnings)
    state["follow_up"] = parsed.follow_up
    state["avg_context_score"] = avg_score
    state.setdefault("logprobs", [])
    state["raw_prompt"] = prompt
    return state
