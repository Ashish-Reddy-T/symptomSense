from __future__ import annotations

import json

import pytest
from backend.app.agents.nodes.classify_input import classify_input
from backend.app.agents.nodes.confidence_verification import confidence_verification
from backend.app.agents.nodes.final_generation import final_generation
from backend.app.core.settings import Settings


@pytest.mark.asyncio
async def test_classify_input_detects_modalities() -> None:
    settings = Settings()
    state = {"text_query": "Explain this", "image_data": "data:image/png;base64,abc"}
    result = await classify_input(state, settings=settings)
    assert "image_query" in result["task_types"]
    assert "document_query" in result["task_types"]


class StubGemini:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate_with_fallback(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(
            {
                "answer": "Answer with [doc1] citation",
                "citations": ["doc1"],
                "follow_up": ["Check labs"],
                "warnings": [],
            }
        )


@pytest.mark.asyncio
async def test_final_generation_formats_prompt() -> None:
    settings = Settings()
    gemini = StubGemini()
    state = {
        "text_query": "Is this safe?",
        "rag_documents": [
            {"text": "Doc text", "metadata": {"source_file": "doc.pdf"}, "score": 0.8}
        ],
        "image_analysis": {"label": "Normal", "confidence": 0.9},
    }
    result = await final_generation(state, gemini=gemini, settings=settings)
    assert "Answer" in result["final_answer"]
    assert gemini.prompts
    assert result["citations"][0]["source"] == "doc.pdf"
    assert result["follow_up"] == ["Check labs"]


@pytest.mark.asyncio
async def test_confidence_verification_appends_warnings() -> None:
    settings = Settings()
    state = {
        "final_answer": "Result",
        "image_analysis": {"label": "Test", "confidence": 0.1},
        "rag_documents": [],
        "avg_context_score": 0.1,
    }
    updated = await confidence_verification(state, settings=settings)
    assert "Confidence Notes" in updated["final_answer"]
    assert len(updated["warnings"]) == 3
