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
    from .services.rag_service import EMBEDDING_DIM, GeminiClient, GeminiRetriever
    from .services.stt_service import WhisperService
    from .services.tts_service import PiperService
    from .storage.qdrant_client import ensure_collection, init_qdrant

    qdrant = init_qdrant(settings)
    ensure_collection(qdrant, settings.QDRANT_COLLECTION, vector_size=EMBEDDING_DIM)

    gemini = GeminiClient(settings=settings)
    retriever = GeminiRetriever(settings=settings, client=qdrant, gemini=gemini)
    vit_classifier = ViTImageClassifier(settings=settings)
    stt_service = WhisperService(settings=settings)
    tts_service = PiperService(settings=settings)

    graph = build_graph(
        settings=settings,
        retriever=retriever,
        gemini=gemini,
        vit=vit_classifier,
        stt_service=stt_service,
        tts_service=tts_service,
    )

    app.state.settings = settings
    app.state.qdrant = qdrant
    app.state.gemini = gemini
    app.state.retriever = retriever
    app.state.vit = vit_classifier
    app.state.stt_service = stt_service
    app.state.tts_service = tts_service
    app.state.graph = graph

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
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

register_exception_handlers(app)

app.include_router(process_input.router, prefix="/api")
app.include_router(stt.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(health.router)
