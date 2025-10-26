"""Services for chunking, embedding, and retrieving documents."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

import google.generativeai as genai
import httpx
import structlog
from sentence_transformers import CrossEncoder
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.settings import Settings
from ..storage.qdrant_client import query_collection, upsert_points

logger = structlog.get_logger(__name__)

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
def _embed_text(model_name: str, text: str) -> list[float]:
    response = genai.embed_content(model=model_name, content=text)
    embedding = response.get("embedding")
    if embedding is None:
        raise RuntimeError("No embedding returned from Gemini.")
    if hasattr(embedding, "values"):
        return list(embedding.values)
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
        generative_model: genai.GenerativeModel | None = None,
    ) -> None:
        self.settings = settings
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._embed_model_name = settings.GEMINI_EMBED_MODEL
        self._generative_model = generative_model or genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL
        )
        self._embedding_dim: int | None = settings.GEMINI_EMBED_DIMENSION
        # Optional local embedding fallback (lazy-loaded)
        self._local_embedder = None
        self._use_local = bool(getattr(settings, "USE_LOCAL_EMBEDDINGS", False))
        self._local_model_name = getattr(settings, "LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")

    def embed(self, text: str) -> list[float]:
        # If configured to use local embeddings, prefer them first.
        if self._use_local:
            try:
                if self._local_embedder is None:
                    from sentence_transformers import SentenceTransformer

                    try:
                        self._local_embedder = SentenceTransformer(self._local_model_name)
                    except Exception:
                        # fallback to a small, reliable model
                        self._local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
                vec = self._local_embedder.encode(text)
                vec_list = list(map(float, vec.tolist())) if hasattr(vec, "tolist") else list(map(float, vec))
                if self._embedding_dim is None:
                    self._embedding_dim = len(vec_list)
                return vec_list
            except Exception as exc:  # pragma: no cover - fallback to Gemini
                logger = structlog.get_logger(__name__)
                logger.warning("local_embed_failed", error=str(exc), fallback=self._local_model_name)

        # Default: try Gemini embeddings first (if allowed), otherwise use local as fallback
        try:
            vector = _embed_text(self._embed_model_name, text)
            if self._embedding_dim is None:
                self._embedding_dim = len(vector)
            return vector
        except Exception as exc:  # pragma: no cover - fallback path
            logger = structlog.get_logger(__name__)
            logger.warning("gemini_embed_failed", error=str(exc), fallback="local_sentence_transformer")
            try:
                if self._local_embedder is None:
                    from sentence_transformers import SentenceTransformer

                    self._local_embedder = SentenceTransformer(self._local_model_name)
                vec = self._local_embedder.encode(text)
                vec_list = list(map(float, vec.tolist())) if hasattr(vec, "tolist") else list(map(float, vec))
                if self._embedding_dim is None:
                    self._embedding_dim = len(vec_list)
                return vec_list
            except Exception:
                raise

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def generate(self, prompt: str) -> str:
        return _generate_text(self._generative_model, prompt)

    @property
    def embedding_dimension(self) -> int:
        if self._embedding_dim is not None:
            return self._embedding_dim
        try:
            probe_vector = self.embed("dimension probe")
            self._embedding_dim = len(probe_vector)
        except Exception as exc:  # pragma: no cover - offline environments
            logger.warning("gemini_embedding_probe_failed: %s", exc)
            self._embedding_dim = 384 # self.settings.GEMINI_EMBED_DIMENSION or 3072
        return self._embedding_dim

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
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
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
        # Try to locate an appropriate collection. The ingestion process may
        # have created a collection with a different embedding dimension
        # suffix (e.g. "medical-knowledge_d384"). Prefer an exact configured
        # collection name if it exists; otherwise pick the most populated
        # collection that starts with the configured base name.
        base_collection = collection or self.settings.QDRANT_COLLECTION
        try:
            cols = getattr(self.client.get_collections(), "collections", [])
            col_names = [c.name for c in cols]
        except Exception:
            col_names = []

        chosen = None
        if base_collection in col_names:
            chosen = base_collection
        else:
            # find collections that start with the base name
            candidates = [n for n in col_names if n.startswith(base_collection)]
            if candidates:
                # pick the candidate with the largest point count
                best = None
                best_count = -1
                from ..storage.qdrant_client import get_collection_count

                for c in candidates:
                    try:
                        cnt = get_collection_count(self.client, c)
                    except Exception:
                        cnt = 0
                    if cnt > best_count:
                        best_count = cnt
                        best = c
                chosen = best or candidates[0]
        if chosen is None:
            chosen = base_collection

        hits = query_collection(
            self.client,
            collection=chosen,
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
        def _score(item: dict) -> float:
            return float(item.get("rerank_score", item.get("score", 0.0)) or 0.0)

        return sorted(hits, key=_score, reverse=True)

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
