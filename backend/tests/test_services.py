from __future__ import annotations

from typing import Any

import pytest

from backend.app.core.settings import Settings
from backend.app.services import rag_service
from backend.app.services.rag_service import GeminiRetriever, chunk_markdown
from backend.app.telemetry.metrics import REQUEST_TOTAL, RequestTracker


def test_chunk_markdown_breaks_text() -> None:
    text = "# Title\n\nParagraph one.\n\nParagraph two." * 3
    chunks = chunk_markdown(text, max_chars=50, overlap=10)
    assert chunks
    assert all(len(chunk) <= 60 for chunk in chunks)


def test_request_tracker_records_success() -> None:
    metric = REQUEST_TOTAL.labels(endpoint="unittest", status="success")
    start = metric._value.get()
    tracker = RequestTracker("unittest")
    tracker.observe_success()
    assert metric._value.get() == start + 1


class StubGemini:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[float(i)] * 3 for i, _ in enumerate(texts, start=1)]

    def embed(self, _: str) -> list[float]:
        return [0.1, 0.2, 0.3]


def test_gemini_retriever_add_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_upsert(client, collection, vectors, payloads, ids=None):  # noqa: ANN001
        captured["vectors"] = vectors
        captured["payloads"] = payloads

    monkeypatch.setattr(rag_service, "upsert_points", fake_upsert)
    retriever = GeminiRetriever(settings=Settings(), client=object(), gemini=StubGemini())
    retriever.add_documents(["chunk"], [{"source_file": "doc.pdf"}])
    assert captured["payloads"][0]["text"] == "chunk"


def test_gemini_retriever_retrieve(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        rag_service,
        "query_collection",
        lambda *args, **kwargs: [  # noqa: ANN001
            {"payload": {"text": "Doc", "source_file": "doc.pdf"}, "score": 0.7}
        ],
    )
    retriever = GeminiRetriever(settings=Settings(), client=object(), gemini=StubGemini())
    results = retriever.retrieve("query", top_k=1)
    assert results[0].text == "Doc"
