"""Document retrieval node."""

from __future__ import annotations

import logging
from typing import Any

from ...core.settings import Settings
from ...services.rag_service import GeminiRetriever

logger = logging.getLogger(__name__)


async def document_rag(
    state: dict[str, Any],
    *,
    retriever: GeminiRetriever,
    settings: Settings,
) -> dict[str, Any]:
    query = (state.get("text_query") or "").strip()
    if not query:
        state["rag_documents"] = []
        return state
    try:
        results = retriever.retrieve(query, top_k=5)
    except Exception as exc:  # pragma: no cover - network/runtime errors
        logger.exception("rag_retrieve_failed", error=str(exc))
        state["rag_documents"] = []
        state["rag_error"] = str(exc)
        return state
    state["rag_documents"] = [
        {
            "text": item.text,
            "score": item.score,
            "metadata": item.metadata,
            "citation": item.metadata.get("source_file") or item.metadata.get("source", "unknown"),
        }
        for item in results
    ]
    return state
