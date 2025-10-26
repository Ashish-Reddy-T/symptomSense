"""Offline ingestion pipeline: PDF -> markdown -> chunks -> embeddings -> Qdrant."""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.settings import Settings
from backend.app.core.logging import configure_logging
from backend.app.services.docling_service import parse_pdf_to_markdown
from backend.app.services.rag_service import GeminiClient, GeminiRetriever, chunk_markdown
from backend.app.storage.qdrant_client import ensure_collection, init_qdrant

configure_logging()
logger = structlog.get_logger(__name__)


def iter_pdfs(base_dir: Path) -> list[Path]:
    return sorted(p for p in base_dir.glob("*.pdf"))


def ingest() -> None:
    settings = Settings()
    knowledge_dir = Path("data/knowledge_base")
    if not knowledge_dir.exists():
        logger.warning("knowledge_dir_missing", path=str(knowledge_dir))
        return

    gemini = GeminiClient(settings=settings)
    embed_dim = gemini.embedding_dimension
    # If the developer left QDRANT_MODE=memory, warn and switch to a disk
    # backed instance for ingestion so the vectors persist and are visible to
    # the API process. In-memory Qdrant instances live only in-process and
    # therefore a separate ingest run would not populate the running API.
    if settings.QDRANT_MODE == "memory":
        logger.warning(
            "qdrant_memory_mode_ingest",
            msg=(
                "QDRANT_MODE=memory; ingestion will create an ephemeral in-memory DB "
                "that won't be visible to the running API. Switching to disk at './data/qdrant_db' for persistence."
            ),
        )
        settings.QDRANT_MODE = "disk"
        settings.QDRANT_PATH = Path("./data/qdrant_db")

    qdrant = init_qdrant(settings)
    ensure_collection(qdrant, settings.QDRANT_COLLECTION, vector_size=embed_dim)
    retriever = GeminiRetriever(settings=settings, client=qdrant, gemini=gemini)

    try:
        for pdf_path in iter_pdfs(knowledge_dir):
            logger.info("ingest_pdf_start", path=str(pdf_path))
            markdown = parse_pdf_to_markdown(pdf_path, parser=settings.PARSER)
            chunks = chunk_markdown(markdown)
            if not chunks:
                logger.info("no_chunks_extracted", path=str(pdf_path))
                continue
            metadatas = [
                {
                    "source_file": str(pdf_path),
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                }
                for idx, _ in enumerate(chunks)
            ]
            retriever.add_documents(chunks, metadatas)
            logger.info("ingest_pdf_done", path=str(pdf_path), chunks=len(chunks))
    finally:
        gemini.close()
        retriever.close()
        qdrant.close()


if __name__ == "__main__":
    ingest()
