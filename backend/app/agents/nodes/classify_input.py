"""Input classification node."""

from __future__ import annotations

from typing import Any

from ...core.settings import Settings


async def classify_input(state: dict[str, Any], *, settings: Settings) -> dict[str, Any]:
    text_query = (state.get("text_query") or "").strip()
    image_data = state.get("image_data")
    tasks: list[str] = []

    if image_data:
        tasks.append("image_query")
    if text_query:
        tasks.append("document_query")
    if not tasks:
        tasks = ["general_chat"]

    state["task_types"] = tasks
    return state
