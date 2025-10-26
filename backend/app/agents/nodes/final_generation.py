"""Final response generation node."""

from __future__ import annotations

import logging
from typing import Any
import re

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
        # try to extract a JSON payload from the model output (handles code
        # fences, ```json blocks, or inline JSON). This makes the parser more
        # robust when the LLM includes markdown formatting.
        def _extract_json_from_text(text: str) -> str:
            t = (text or "").strip()
            if not t:
                return t
            # Look for ```json\n{...}``` blocks first
            m = re.search(r"```(?:json)?\s*\n(.*?)\n```", t, re.S | re.I)
            if m:
                return m.group(1).strip()
            # Fallback: any fenced block
            m = re.search(r"```(.*?)```", t, re.S)
            if m:
                return m.group(1).strip()
            # Fallback: first JSON object in the text
            m = re.search(r"(\{.*\})", t, re.S)
            if m:
                return m.group(1).strip()
            return t

        json_payload = _extract_json_from_text(raw)
        parsed = AgentAnswer.model_validate_json(json_payload)
    except Exception as exc:  # pragma: no cover - parsing errors
        # pass large/unstructured data via the `extra` mapping so stdlib logging
        # (and adapters) don't receive unexpected keyword args. Keep a concise
        # message as the main log record for readability.
        logger.warning(
            "final_generation_parse_failed: parsing AgentAnswer failed: %s",
            str(exc),
            extra={"raw": raw, "error": str(exc)},
        )
        parsed = AgentAnswer(answer=raw.strip(), citations=[], follow_up=[], warnings=[])

    # Build a human-friendly textual answer rather than returning raw JSON.
    answer_lines: list[str] = []
    answer_lines.append(parsed.answer.strip())

    # Attach retrieval sources (if any)
    state["citations"] = citations
    if citations:
        answer_lines.append("\nSources:")
        for c in citations:
            lbl = c.get("label")
            src = c.get("source") or "unknown"
            score = c.get("score")
            score_part = f" (score={score:.3f})" if isinstance(score, (int, float)) else ""
            answer_lines.append(f"- {lbl}: {src}{score_part}")

    # Include follow-up suggestions and warnings for readability
    if parsed.follow_up:
        answer_lines.append("\nSuggested follow-up:")
        for item in parsed.follow_up:
            answer_lines.append(f"- {item}")

    if parsed.warnings:
        answer_lines.append("\nWarnings:")
        for w in parsed.warnings:
            answer_lines.append(f"- {w}")

    answer_with_citations = "\n".join(answer_lines)
    state["final_answer"] = answer_with_citations
    state.setdefault("warnings", [])
    if parsed.warnings:
        state["warnings"].extend(parsed.warnings)
    state["follow_up"] = parsed.follow_up
    state["avg_context_score"] = avg_score
    state.setdefault("logprobs", [])
    state["raw_prompt"] = prompt
    return state
