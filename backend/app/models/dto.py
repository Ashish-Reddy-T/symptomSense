"""Pydantic data-transfer objects for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProcessInputRequest(BaseModel):
    text_query: str | None = Field(default=None, description="The user's textual question or notes.")
    image_base64: str | None = Field(default=None, description="Optional base64-encoded image data URL.")


class Citation(BaseModel):
    label: str
    source: str | None = None
    score: float | None = None


class ProcessInputResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    image_analysis: dict[str, Any] | None = None


class STTResponse(BaseModel):
    text: str
    language: str | None = None
    duration: float | None = None
    words: list[str] = Field(default_factory=list)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesise with Piper.")


class TTSResponse(BaseModel):
    audio_base64: str
    sample_rate: int
    format: str = "wav"
