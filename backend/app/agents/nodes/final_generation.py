"""Enhanced final response generation node with NLG and confidence services."""

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
    confidence_service=None,
    nlg_service=None,
    hitl_service=None,
    orchestrator=None,
) -> dict[str, Any]:
    """
    Enhanced final generation with:
    - Confidence aggregation
    - Context combination (RAG + Web)
    - Natural language generation
    - HITL flagging
    """
    
    question = (state.get("text_query") or "Describe the attached image.").strip()
    
    # Calculate unified confidence profile
    image_conf = None
    if state.get("image_analysis"):
        image_conf = state["image_analysis"].get("confidence")
    
    rag_scores = state.get("rag_scores", [])
    llm_logprobs = state.get("logprobs", [])
    
    confidence_profile = None
    if confidence_service:
        confidence_profile = confidence_service.aggregate_confidence(
            image_conf=image_conf,
            rag_scores=rag_scores,
            llm_logprobs=llm_logprobs,
        )
    
    # Combine contexts from RAG and Web
    combined_context = None
    if orchestrator:
        combined_context = orchestrator.combine_rag_and_web_context(
            rag_context=[doc.get("text", "") for doc in state.get("rag_documents", [])],
            rag_scores=rag_scores,
            web_snippets=state.get("web_search_snippets", []),
            web_results=state.get("web_search_results", []),
        )
    
    # Determine agent weights
    agent_weights = {}
    if orchestrator and confidence_profile:
        agent_weights = orchestrator.determine_agent_priority(
            state,
            confidence_profile.to_dict() if confidence_profile else None,
        )
    
    # Build synthesis prompt
    if orchestrator and combined_context and confidence_profile:
        prompt = orchestrator.create_synthesis_prompt(
            state,
            combined_context,
            confidence_profile.to_dict(),
            agent_weights,
        )
    else:
        # Fallback to original prompt format
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
- DO NOT add unnecessary disclaimers about being an AI.
- Focus on providing accurate, actionable medical information.

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

    # Prepare citations from RAG + Web
    rag_sources = []
    if state.get("rag_documents"):
        for i, doc in enumerate(state["rag_documents"], start=1):
            rag_sources.append({
                "label": f"doc{i}",
                "source": doc.get("source", "unknown"),
                "source_file": doc.get("source", "unknown"),
                "score": state.get("rag_scores", [])[i - 1] if state.get("rag_scores") and len(state.get("rag_scores", [])) > i - 1 else 0.0,
            })
    
    web_sources = []
    if state.get("web_search_results"):
        for i, result in enumerate(state["web_search_results"], start=1):
            web_sources.append({
                "label": f"web{i}",
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
            })
    
    # Prepare RAG context texts
    rag_context = [doc.get("text", "") for doc in state.get("rag_documents", [])]
    
    # Naturalize response with NLG service
    if nlg_service and confidence_profile:
        natural_answer = nlg_service.naturalize_response(
            raw_answer=parsed.answer,
            confidence_profile=confidence_profile,
            rag_context=rag_context,
            web_sources=web_sources,
            image_analysis=state.get("image_analysis"),
        )
        
        # Format citations properly
        citations_formatted = nlg_service.format_citations(
            rag_sources=rag_sources,
            web_sources=web_sources,
            image_source=state.get("image_analysis"),
        )
        
        state["final_answer"] = natural_answer
        state["citations"] = rag_sources + web_sources
    else:
        # Fallback to original formatting
        answer_lines: list[str] = []
        answer_lines.append(parsed.answer.strip())

        # Attach retrieval sources (if any)
        all_citations = rag_sources + web_sources
        state["citations"] = all_citations
        if all_citations:
            answer_lines.append("\nSources:")
            for c in all_citations:
                if "url" in c:  # web citation
                    answer_lines.append(f"- {c['label']}: {c['title']} ({c['url']})")
                else:  # rag citation
                    score_part = f" (score={c['score']:.3f})" if isinstance(c.get("score"), (int, float)) else ""
                    answer_lines.append(f"- {c['label']}: {c['source']}{score_part}")

        # Include follow-up suggestions and warnings for readability
        if parsed.follow_up:
            answer_lines.append("\nSuggested follow-up:")
            for item in parsed.follow_up:
                answer_lines.append(f"- {item}")

        if parsed.warnings:
            answer_lines.append("\nWarnings:")
            for w in parsed.warnings:
                answer_lines.append(f"- {w}")

        state["final_answer"] = "\n".join(answer_lines)
    
    # Check if we should flag for HITL
    hitl_flagged = False
    if hitl_service and confidence_profile:
        hitl_flagged = hitl_service.should_flag_for_review(
            confidence_profile=confidence_profile,
        )
        
        if hitl_flagged:
            hitl_service.add_to_queue(
                query=question,
                confidence_profile=confidence_profile,
                initial_response=state["final_answer"],
                image_data=state.get("image_data"),
            )
    
    # Store metadata in state
    state["confidence_profile"] = confidence_profile.to_dict() if confidence_profile else None
    state["hitl_flagged"] = hitl_flagged
    state.setdefault("warnings", [])
    if parsed.warnings:
        state["warnings"].extend(parsed.warnings)
    state["follow_up"] = parsed.follow_up
    state["avg_context_score"] = sum(rag_scores) / len(rag_scores) if rag_scores else 0.0
    state.setdefault("logprobs", [])
    state["raw_prompt"] = prompt
    
    return state
