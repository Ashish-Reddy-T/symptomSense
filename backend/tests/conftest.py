from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from backend.app.routers import health, process_input, stt, tts
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def test_env() -> Iterator[None]:
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    os.environ.setdefault("ENV", "test")
    yield


class FakeGraph:
    async def ainvoke(self, state: dict) -> dict:
        text = state.get("text_query") or ""
        return {
            "final_answer": f"Echo: {text}".strip(),
            "citations": [{"label": "doc1", "source": "test.pdf", "score": 0.9}],
            "warnings": [],
            "follow_up": ["Confirm vitals", "Consult specialist"],
            "image_analysis": {"label": "Healthy", "confidence": 0.95},
        }


class FakeSTT:
    def transcribe_bytes(self, _: bytes, *, language: str | None = None) -> dict:
        return {
            "text": "transcript",
            "language": language or "en",
            "duration": 1.0,
            "words": ["transcript"],
        }


class FakeTTS:
    def synthesize(self, text: str) -> dict:
        return {
            "audio": text.encode("utf-8"),
            "sample_rate": 16000,
            "format": "wav",
        }


@pytest.fixture()
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(process_input.router, prefix="/api")
    app.include_router(stt.router, prefix="/api")
    app.include_router(tts.router, prefix="/api")
    app.include_router(health.router)

    app.state.graph = FakeGraph()
    app.state.stt_service = FakeSTT()
    app.state.tts_service = FakeTTS()

    with TestClient(app) as client:
        yield client
