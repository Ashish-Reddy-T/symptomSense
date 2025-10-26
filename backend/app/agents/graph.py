"""LangGraph orchestration for the agent."""

from __future__ import annotations

from functools import partial
from typing import TypedDict

from langgraph.graph import END, StateGraph

from ..core.settings import Settings
from ..services.image_service import ViTImageClassifier
from ..services.rag_service import GeminiClient, GeminiRetriever
from ..services.stt_service import WhisperService
from ..services.tts_service import PiperService
from .nodes.classify_input import classify_input
from .nodes.confidence_verification import confidence_verification
from .nodes.document_rag import document_rag
from .nodes.final_generation import final_generation
from .nodes.image_analysis import image_analysis
from .nodes.web_search import web_search_agent  # NEW


class AgentState(TypedDict, total=False):
    text_query: str
    image_data: str
    task_types: list[str]
    rag_documents: list[dict]
    rag_scores: list[float]
    rag_metadata: list[dict]
    final_answer: str
    image_analysis: dict
    citations: list[dict]
    warnings: list[str]
    avg_context_score: float
    logprobs: list[float]
    # NEW: Web search and confidence fields
    web_search_results: list[dict]
    web_search_snippets: list[str]
    confidence_profile: dict
    hitl_flagged: bool


def build_graph(
    *,
    settings: Settings,
    retriever: GeminiRetriever,
    gemini: GeminiClient,
    vit: ViTImageClassifier,
    stt_service: WhisperService | None = None,
    tts_service: PiperService | None = None,
    # NEW: Enhanced services
    confidence_service=None,
    nlg_service=None,
    hitl_service=None,
    brave_service=None,
    orchestrator=None,
):
    graph = StateGraph(AgentState)
    _ = (stt_service, tts_service)  # resources available for future steps

    graph.add_node("classify_input", partial(classify_input, settings=settings))
    graph.add_node("image_analysis", partial(image_analysis, classifier=vit, settings=settings))
    graph.add_node("document_rag", partial(document_rag, retriever=retriever, settings=settings))
    # NEW: Add web search agent node
    graph.add_node("web_search", partial(
        web_search_agent,
        brave_service=brave_service,
    ))
    # NEW: Update final_generation with all services
    graph.add_node("final_generation", partial(
        final_generation,
        gemini=gemini,
        settings=settings,
        confidence_service=confidence_service,
        nlg_service=nlg_service,
        hitl_service=hitl_service,
        orchestrator=orchestrator,
    ))
    graph.add_node("confidence_verification", partial(confidence_verification, settings=settings))

    graph.set_entry_point("classify_input")

    def route_from_classify(state: AgentState) -> str:
        tasks = state.get("task_types", [])
        if "image_query" in tasks:
            return "image_analysis"
        if "document_query" in tasks:
            return "document_rag"
        return "final_generation"

    def route_after_image(state: AgentState) -> str:
        tasks = state.get("task_types", [])
        if "document_query" in tasks:
            return "document_rag"
        return "final_generation"
    
    # NEW: Router after RAG to decide web search
    def route_after_rag(state: AgentState) -> str:
        """Decide if web search is needed after RAG"""
        if not orchestrator or not confidence_service:
            return "final_generation"
        
        # Check if we should trigger web search
        should_search = orchestrator.should_invoke_web_search(
            state,
            confidence_service,
        )
        
        if should_search:
            return "web_search"
        return "final_generation"

    graph.add_conditional_edges(
        "classify_input",
        route_from_classify,
        {
            "image_analysis": "image_analysis",
            "document_rag": "document_rag",
            "final_generation": "final_generation",
        },
    )

    graph.add_conditional_edges(
        "image_analysis",
        route_after_image,
        {
            "document_rag": "document_rag",
            "final_generation": "final_generation",
        },
    )

    # NEW: Add conditional routing after document_rag
    graph.add_conditional_edges(
        "document_rag",
        route_after_rag,
        {
            "web_search": "web_search",
            "final_generation": "final_generation",
        },
    )
    
    # NEW: Web search always goes to final generation
    graph.add_edge("web_search", "final_generation")
    
    graph.add_edge("final_generation", "confidence_verification")
    graph.add_edge("confidence_verification", END)

    return graph.compile()
