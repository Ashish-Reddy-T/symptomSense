"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .core.errors import register_exception_handlers
from .core.logging import configure_logging
from .core.settings import Settings
from .routers import health, process_input, stt, tts
from .telemetry.tracing import setup_tracing

settings = Settings()
configure_logging(level=settings.LOG_LEVEL, json_logs=settings.LOG_STRUCTURED)
setup_tracing(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .agents.graph import build_graph
    from .services.image_service import ViTImageClassifier
    from .services.rag_service import GeminiClient, GeminiRetriever
    from .services.stt_service import WhisperService
    from .services.tts_service import PiperService
    from .storage.qdrant_client import ensure_collection, init_qdrant
    # NEW: Import enhanced services
    from .services.confidence_service import ConfidenceService
    from .services.nlg_service import NLGService
    from .services.hitl_service import HITLService
    from .services.brave_search_service import BraveSearchService
    from .agents.agent_combine import AgentOrchestrator

    gemini = GeminiClient(settings=settings)
    embed_dim = gemini.embedding_dimension

    qdrant = init_qdrant(settings)
    ensure_collection(qdrant, settings.QDRANT_COLLECTION, vector_size=embed_dim)

    retriever = GeminiRetriever(settings=settings, client=qdrant, gemini=gemini)
    vit_classifier = ViTImageClassifier(settings=settings)
    
    # Initialize STT/TTS services if enabled
    stt_service = WhisperService(settings=settings) if settings.STT_ENABLED else None
    tts_service = PiperService(settings=settings) if settings.TTS_ENABLED else None

    # NEW: Initialize enhanced services
    confidence_service = ConfidenceService(
        high_threshold=settings.MIN_IMAGE_CONFIDENCE,
        medium_threshold=settings.HITL_CONFIDENCE_THRESHOLD,
    )
    
    nlg_service = NLGService(tone=settings.NLG_TONE)
    
    hitl_service = HITLService(
        queue_path=str(settings.HITL_QUEUE_PATH),
        enabled=settings.HITL_ENABLED,
        confidence_threshold=settings.HITL_CONFIDENCE_THRESHOLD,
    )
    
    brave_service = BraveSearchService(
        api_key=settings.BRAVE_API_KEY,
        enabled=settings.BRAVE_SEARCH_ENABLED,
        max_results=settings.BRAVE_MAX_RESULTS,
    )
    
    orchestrator = AgentOrchestrator(
        web_search_threshold=settings.AGENT_WEB_FALLBACK_THRESHOLD,
        hitl_threshold=settings.HITL_CONFIDENCE_THRESHOLD,
    )

    graph = build_graph(
        settings=settings,
        retriever=retriever,
        gemini=gemini,
        vit=vit_classifier,
        stt_service=stt_service,
        tts_service=tts_service,
        # NEW: Pass enhanced services
        confidence_service=confidence_service,
        nlg_service=nlg_service,
        hitl_service=hitl_service,
        brave_service=brave_service,
        orchestrator=orchestrator,
    )

    app.state.settings = settings
    app.state.qdrant = qdrant
    app.state.gemini = gemini
    app.state.retriever = retriever
    app.state.vit = vit_classifier
    app.state.stt_service = stt_service
    app.state.tts_service = tts_service
    app.state.graph = graph
    # NEW: Store enhanced services in app state
    app.state.confidence_service = confidence_service
    app.state.nlg_service = nlg_service
    app.state.hitl_service = hitl_service
    app.state.brave_service = brave_service
    app.state.orchestrator = orchestrator

    try:
        yield
    finally:
        _close_if(app.state, "gemini")
        _close_if(app.state, "retriever")
        _close_if(app.state, "vit")
        _close_if(app.state, "stt_service")
        _close_if(app.state, "tts_service")
        _close_if(app.state, "qdrant")


def _close_if(state: Any, name: str) -> None:
    resource = getattr(state, name, None)
    close = getattr(resource, "close", None)
    if callable(close):
        close()


app = FastAPI(
    title="Agentic Medical Assistant",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Use the property instead of direct field
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

register_exception_handlers(app)

app.include_router(process_input.router, prefix="/api")
app.include_router(stt.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(health.router)
