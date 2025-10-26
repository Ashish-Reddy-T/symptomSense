"""Offline ingestion pipeline: PDF -> markdown -> chunks -> embeddings -> Qdrant."""

from __future__ import annotations

import logging
from pathlib import Path

from backend.app.core.settings import Settings
from backend.app.services.docling_service import parse_pdf_to_markdown
from backend.app.services.rag_service import EMBEDDING_DIM, GeminiClient, GeminiRetriever, chunk_markdown
from backend.app.storage.qdrant_client import ensure_collection, init_qdrant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def iter_pdfs(base_dir: Path) -> list[Path]:
    return sorted(p for p in base_dir.glob("*.pdf"))


def ingest() -> None:
    settings = Settings()
    knowledge_dir = Path("data/knowledge_base")
    if not knowledge_dir.exists():
        logger.warning("knowledge_dir_missing", path=str(knowledge_dir))
        return

    qdrant = init_qdrant(settings)
    ensure_collection(qdrant, settings.QDRANT_COLLECTION, vector_size=EMBEDDING_DIM)
    gemini = GeminiClient(settings=settings)
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
