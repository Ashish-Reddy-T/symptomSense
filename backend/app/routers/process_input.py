"""Router for multimodal agent processing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..models.dto import Citation, ProcessInputRequest, ProcessInputResponse
from ..telemetry.metrics import RequestTracker

router = APIRouter()


@router.post("/process_input", response_model=ProcessInputResponse)
async def process_input(req: ProcessInputRequest, request: Request) -> ProcessInputResponse:
    if not (req.text_query or req.image_base64):
        raise HTTPException(status_code=400, detail="Provide text_query or image_base64.")

    tracker = RequestTracker("process_input")
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="Agent graph not initialised.")

    state = {"text_query": req.text_query, "image_data": req.image_base64}
    try:
        result = await graph.ainvoke(state)
        tracker.observe_success()
    except Exception:
        tracker.observe_error()
        raise

    citations_data = result.get("citations") or []
    citations = [citation if isinstance(citation, Citation) else Citation(**citation) for citation in citations_data]

    return ProcessInputResponse(
        answer=result.get("final_answer", ""),
        citations=citations,
        warnings=result.get("warnings") or [],
        image_analysis=result.get("image_analysis"),
    )
