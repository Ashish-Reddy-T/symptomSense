"""PDF parsing helpers leveraging Docling or Unstructured."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


def parse_pdf_to_markdown(
    path: str | Path,
    *,
    parser: Literal["docling", "unstructured"] = "docling",
) -> str:
    pdf_path = Path(path)
    if parser == "docling":
        return _parse_with_docling(pdf_path)
    if parser == "unstructured":
        return _parse_with_unstructured(pdf_path)
    msg = f"Unsupported parser '{parser}'"
    raise ValueError(msg)


def _parse_with_docling(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except ImportError as exc:  # pragma: no cover - import guard
        raise RuntimeError("Docling is not installed. Install `docling`.") from exc

    converter = DocumentConverter()
    logger.info("docling_parse_start", path=str(path))
    result = converter.convert(str(path))
    document = getattr(result, "document", None)
    if document is None:
        logger.warning("docling_no_document", path=str(path))
        return ""
    if hasattr(document, "export_to_markdown"):
        return document.export_to_markdown()
    markdown = getattr(document, "markdown", None)
    if markdown:
        return markdown
    html = getattr(document, "export_to_markdown", None)
    if callable(html):
        return html()
    logger.warning("docling_markdown_missing", path=str(path))
    return ""


def _parse_with_unstructured(path: Path) -> str:
    try:
        from unstructured.partition.pdf import partition_pdf  # type: ignore
    except ImportError as exc:  # pragma: no cover - import guard
        raise RuntimeError("Unstructured is not installed. Install `unstructured`.") from exc

    logger.info("unstructured_parse_start", path=str(path))
    elements = partition_pdf(filename=str(path))
    texts = [element.text.strip() for element in elements if getattr(element, "text", "").strip()]
    return "\n\n".join(texts)
