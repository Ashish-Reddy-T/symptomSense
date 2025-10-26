"""Services for chunking, embedding, and retrieving documents."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Sequence

import google.generativeai as genai
import httpx
from sentence_transformers import CrossEncoder
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.settings import Settings
from ..storage.qdrant_client import query_collection, upsert_points

logger = logging.getLogger(__name__)

# Gemini text-embedding-004 dimensionality.
EMBEDDING_DIM = 768



def chunk_markdown(markdown: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    """Split markdown into overlapping windows with preference for headings."""
    if not markdown:
        return []

    paragraphs = re.split(r"\n{2,}", markdown)
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if buffer_len + len(para) <= max_chars:
            buffer.append(para)
            buffer_len += len(para)
            continue
        if buffer:
            chunks.append("\n\n".join(buffer))
        overlap_text = "\n\n".join(buffer[-1:]) if buffer else ""
        buffer = [overlap_text, para] if overlap_text else [para]
        buffer = [seg for seg in buffer if seg]
        buffer_len = sum(len(seg) for seg in buffer)
    if buffer:
        chunks.append("\n\n".join(buffer))
    return [chunk.strip() for chunk in chunks if chunk.strip()]


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(3))
def _embed_text(model: genai.EmbeddingModel, text: str) -> list[float]:
    response = model.embed_content(text)
    embedding = getattr(response, "embedding", None) or response.get("embedding")
    values = getattr(embedding, "values", None)
    if values is not None:
        return list(values)
    return list(embedding)


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(3))
def _generate_text(model: genai.GenerativeModel, prompt: str) -> str:
    response = model.generate_content(prompt)
    if hasattr(response, "text") and response.text:
        return response.text
    if getattr(response, "candidates", None):
        for candidate in response.candidates:
            for part in getattr(candidate.content, "parts", []):
                text = getattr(part, "text", None)
                if text:
                    return text
    return ""


@dataclass
class RetrievedChunk:
    text: str
    score: float | None
    metadata: dict


class GeminiClient:
    """Shared Gemini client for embeddings + text generation."""

    def __init__(
        self,
        settings: Settings,
        *,
        embedding_model: genai.EmbeddingModel | None = None,
        generative_model: genai.GenerativeModel | None = None,
    ) -> None:
        self.settings = settings
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._embedding_model = embedding_model or genai.EmbeddingModel(model_name=settings.GEMINI_EMBED_MODEL)
        self._generative_model = generative_model or genai.GenerativeModel(model_name=settings.GEMINI_MODEL)

    def embed(self, text: str) -> list[float]:
        return _embed_text(self._embedding_model, text)

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def generate(self, prompt: str) -> str:
        return _generate_text(self._generative_model, prompt)

    def generate_with_fallback(self, prompt: str) -> str:
        try:
            return self.generate(prompt)
        except Exception as exc:  # pragma: no cover - network failure path
            logger.exception("gemini_generate_failed", error=str(exc))
            if not self.settings.OPENROUTER_API_KEY:
                raise
            return self._generate_openrouter(prompt)

    def _generate_openrouter(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=30) as client:
            response = client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return (message.get("content") or "").strip()

    def close(self) -> None:
        """Allow uniform cleanup calls (Gemini SDK manages its own resources)."""


class GeminiRetriever:
    """Wrapper around Qdrant that uses Gemini embeddings and optional reranking."""

    def __init__(
        self,
        settings: Settings,
        client,
        gemini: GeminiClient,
        *,
        reranker: CrossEncoder | None = None,
    ) -> None:
        self.settings = settings
        self.client = client
        self.gemini = gemini
        self._reranker = reranker
        self._reranker_loaded = reranker is not None

    def add_documents(
        self,
        texts: Sequence[str],
        metadatas: Sequence[dict],
        *,
        collection: str | None = None,
    ) -> None:
        vectors = self.gemini.embed_batch(texts)
        payloads = [
            {**metadata, "text": text, "chunk_length": len(text)}
            for text, metadata in zip(texts, metadatas, strict=False)
        ]
        upsert_points(
            self.client,
            collection=collection or self.settings.QDRANT_COLLECTION,
            vectors=vectors,
            payloads=payloads,
        )

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        collection: str | None = None,
    ) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        vector = self.gemini.embed(query)
        hits = query_collection(
            self.client,
            collection=collection or self.settings.QDRANT_COLLECTION,
            query_vector=vector,
            top_k=top_k * 2,
        )
        if not hits:
            return []
        reranked = self._rerank(query, hits)
        selected = reranked[:top_k]
        return [
            RetrievedChunk(
                text=hit["payload"].get("text", ""),
                score=hit.get("score"),
                metadata=hit["payload"],
            )
            for hit in selected
        ]

    def _rerank(self, query: str, hits: list[dict]) -> list[dict]:
        reranker = self._get_reranker()
        if reranker is None:
            return hits
        pairs = [[query, hit["payload"].get("text", "")] for hit in hits]
        scores = reranker.predict(pairs)
        for hit, score in zip(hits, scores, strict=False):
            hit["rerank_score"] = float(score)
        return sorted(hits, key=lambda item: item.get("rerank_score", item.get("score", 0)), reverse=True)

    def _get_reranker(self) -> CrossEncoder | None:
        if self.settings.ENV == "test":
            return None
        if self._reranker is None and not self._reranker_loaded:
            logger.info("loading reranker", model=self.settings.RERANKER_MODEL)
            device = "cuda" if self.settings.TORCH_DEVICE == "cuda" else "cpu"
            self._reranker = CrossEncoder(self.settings.RERANKER_MODEL, device=device)
            self._reranker_loaded = True
        return self._reranker

    def close(self) -> None:
        if self._reranker is not None and hasattr(self._reranker, "model"):
            self._reranker.model.to("cpu")
