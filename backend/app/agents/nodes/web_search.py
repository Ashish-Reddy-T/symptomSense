"""
Web Search Agent Node

Performs real-time web search using Brave API to supplement knowledge base.
Triggered when RAG confidence is low or query requires recent information.
"""

from typing import TypedDict, Dict, List
import structlog

logger = structlog.get_logger(__name__)


class State(TypedDict, total=False):
    """Agent state (inherits from main graph)"""
    text_query: str
    task_types: list[str]
    rag_context: list[str]
    rag_scores: list[float]
    web_search_results: list[Dict]
    web_search_snippets: list[str]
    confidence_profile: Dict


async def web_search_agent(state: State, *, brave_service) -> State:
    """
    Web search agent node
    
    Searches the web using Brave API when:
    - RAG confidence < 0.5
    - Temporal keywords detected
    - Explicit web search request
    
    Args:
        state: Current graph state
        brave_service: BraveSearchService instance
    
    Returns:
        Updated state with web search results
    """
    query = state.get("text_query", "")
    
    logger.info(
        "web_search_agent_invoked",
        query=query[:100],
        has_rag_context=bool(state.get("rag_context")),
    )
    
    if not query:
        logger.warning("web_search_agent_no_query")
        return state
    
    try:
        # Perform web search
        results = await brave_service.search_medical_web(query)
        
        if not results:
            logger.warning("web_search_no_results", query=query[:50])
            return {
                **state,
                "web_search_results": [],
                "web_search_snippets": [],
            }
        
        # Extract snippets for context
        snippets = brave_service.extract_snippets(results)
        
        # Optional: Deduplicate with RAG sources
        rag_sources = state.get("rag_metadata", [])
        if rag_sources:
            results = brave_service.deduplicate_with_rag(results, rag_sources)
        
        logger.info(
            "web_search_completed",
            num_results=len(results),
            num_snippets=len(snippets),
        )
        
        return {
            **state,
            "web_search_results": results,
            "web_search_snippets": snippets,
        }
    
    except Exception as e:
        logger.error(
            "web_search_agent_error",
            error=str(e),
            query=query[:50],
        )
        return {
            **state,
            "web_search_results": [],
            "web_search_snippets": [],
        }
