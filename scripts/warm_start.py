"""Warm start models to reduce first-request latency."""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.settings import Settings
from backend.app.core.logging import configure_logging
from backend.app.services.image_service import ViTImageClassifier
from backend.app.services.rag_service import GeminiClient, GeminiRetriever
from backend.app.services.stt_service import WhisperService
from backend.app.services.tts_service import PiperService
from backend.app.storage.qdrant_client import ensure_collection, init_qdrant

configure_logging()
logger = structlog.get_logger(__name__)


def main() -> None:
    settings = Settings()
    resources: list[object] = []

    try:
        gemini = GeminiClient(settings=settings)
        embed_dim = gemini.embedding_dimension
        resources.append(gemini)
    except Exception as exc:  # pragma: no cover - offline fallback
        logger.warning("warm_start_gemini_failed", error=str(exc))
        gemini = None
        embed_dim = settings.GEMINI_EMBED_DIMENSION or 3072

    try:
        qdrant = init_qdrant(settings)
        ensure_collection(qdrant, settings.QDRANT_COLLECTION, vector_size=embed_dim)
        resources.append(qdrant)
    except Exception as exc:  # pragma: no cover
        logger.warning("warm_start_qdrant_failed", error=str(exc))
        qdrant = None

    if gemini and qdrant:
        try:
            retriever = GeminiRetriever(settings=settings, client=qdrant, gemini=gemini)
            resources.append(retriever)
        except Exception as exc:  # pragma: no cover
            logger.warning("warm_start_retriever_failed", error=str(exc))

    for name, factory in (
        ("vit", lambda: ViTImageClassifier(settings=settings)),
        ("whisper", lambda: WhisperService(settings=settings)),
        ("piper", lambda: PiperService(settings=settings)),
    ):
        try:
            instance = factory()
            resources.append(instance)
        except Exception as exc:  # pragma: no cover - optional components
            logger.warning("warm_start_model_failed", component=name, error=str(exc))

    logger.info("warm_start_complete")

    for resource in resources:
        close = getattr(resource, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # pragma: no cover - best effort
                pass


if __name__ == "__main__":
    main()
