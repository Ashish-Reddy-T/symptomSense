"""Helpers for initialising and working with Qdrant."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, Filter, PointStruct, VectorParams

from ..core.settings import Settings
from .files import ensure_dir

logger = structlog.get_logger(__name__)


def init_qdrant(settings: Settings) -> QdrantClient:
    """Initialise a Qdrant client based on configuration."""
    if settings.QDRANT_MODE == "memory":
        logger.info("initialising in-memory qdrant instance")
        return QdrantClient(path=":memory:")

    if settings.QDRANT_MODE == "disk":
        ensure_dir(settings.QDRANT_PATH)
        logger.info("initialising disk qdrant", path=str(settings.QDRANT_PATH))
        return QdrantClient(path=str(settings.QDRANT_PATH))

    logger.info("connecting to remote qdrant", url=settings.QDRANT_URL)
    return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    """Create the collection if it does not already exist."""
    if client.collection_exists(name):
        return

    logger.info("creating_qdrant_collection", name=name, vector_size=vector_size)
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def upsert_points(
    client: QdrantClient,
    collection: str,
    vectors: Sequence[Sequence[float]],
    payloads: Sequence[Mapping[str, object]],
    ids: Sequence[str] | None = None,
) -> None:
    """Upsert points into Qdrant."""
    if ids is None:
        ids = [str(i) for i in range(len(vectors))]

    points = [
        PointStruct(id=pid, vector=vector, payload=payload)
        for pid, vector, payload in zip(ids, vectors, payloads, strict=False)
    ]
    client.upsert(collection_name=collection, wait=True, points=points)


def query_collection(
    client: QdrantClient,
    collection: str,
    query_vector: Sequence[float],
    top_k: int = 5,
    query_filter: Filter | None = None,
) -> list[dict]:
    """Return payloads for the top-K matches."""
    result = client.search(
        collection_name=collection,
        query_vector=list(query_vector),
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )
    return [
        {
            "id": hit.id,
            "score": float(hit.score) if hit.score is not None else None,
            "payload": hit.payload or {},
        }
        for hit in result
    ]
