"""Warm start models to reduce first-request latency."""

from __future__ import annotations

import logging

from backend.app.core.settings import Settings
from backend.app.services.image_service import ViTImageClassifier
from backend.app.services.rag_service import EMBEDDING_DIM, GeminiClient, GeminiRetriever
from backend.app.services.stt_service import WhisperService
from backend.app.services.tts_service import PiperService
from backend.app.storage.qdrant_client import ensure_collection, init_qdrant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = Settings()
    qdrant = init_qdrant(settings)
    ensure_collection(qdrant, settings.QDRANT_COLLECTION, vector_size=EMBEDDING_DIM)
    gemini = GeminiClient(settings=settings)
    retriever = GeminiRetriever(settings=settings, client=qdrant, gemini=gemini)
    vit = ViTImageClassifier(settings=settings)
    stt = WhisperService(settings=settings)
    tts = PiperService(settings=settings)

    logger.info("warm_start_complete")

    for resource in (tts, stt, vit, retriever, gemini, qdrant):
        close = getattr(resource, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
