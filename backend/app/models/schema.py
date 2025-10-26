"""Structured schemas used for validating LLM output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentAnswer(BaseModel):
    answer: str = Field(..., description="Markdown answer for the end user.")
    citations: list[str] = Field(
        default_factory=list,
        description="List of citation tokens used in the answer.",
    )
    follow_up: list[str] = Field(
        default_factory=list,
        description="Recommended follow-up actions or questions.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Confidence notes emitted by the agent.",
    )
