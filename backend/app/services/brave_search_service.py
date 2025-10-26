"""
Brave Search API Service

Provides real-time web search capabilities for medical information.
Supplements local knowledge base with current web sources.
"""

import os
from typing import Dict, List, Optional
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class BraveSearchService:
    """Service for Brave Search API integration"""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        enabled: bool = True,
        max_results: int = 5,
        timeout: int = 10,
    ):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.enabled = enabled and bool(self.api_key)
        self.max_results = max_results
        self.timeout = timeout
        
        if not self.enabled:
            logger.warning("brave_search_disabled", reason="no_api_key" if not self.api_key else "disabled")
        else:
            logger.info("brave_search_initialized", max_results=max_results)
    
    async def search_medical_web(
        self,
        query: str,
        num_results: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search the web for medical information
        
        Args:
            query: Search query
            num_results: Number of results to return (default: self.max_results)
        
        Returns:
            List of search result dicts with title, url, snippet, published_date
        """
        if not self.enabled:
            logger.warning("brave_search_not_enabled")
            return []
        
        num_results = num_results or self.max_results
        
        # Enhance query for medical context
        enhanced_query = self._enhance_medical_query(query)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "q": enhanced_query,
                        "count": num_results,
                        "search_lang": "en",
                        "safesearch": "strict",
                    },
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": self.api_key,
                    },
                )
                
                if response.status_code != 200:
                    logger.error(
                        "brave_search_error",
                        status_code=response.status_code,
                        response=response.text[:200],
                    )
                    return []
                
                data = response.json()
                results = self._parse_search_results(data)
                
                logger.info(
                    "brave_search_completed",
                    query=enhanced_query,
                    num_results=len(results),
                )
                
                return results
        
        except httpx.TimeoutException:
            logger.error("brave_search_timeout", query=enhanced_query)
            return []
        except Exception as e:
            logger.error("brave_search_exception", query=enhanced_query, error=str(e))
            return []
    
    def _enhance_medical_query(self, query: str) -> str:
        """
        Enhance query for better medical search results
        
        Strategy:
        - Add medical context keywords
        - Prioritize authoritative sources
        """
        # Check if query already has medical context
        medical_keywords = ['diagnosis', 'symptoms', 'treatment', 'condition', 'disease']
        has_medical_context = any(kw in query.lower() for kw in medical_keywords)
        
        if has_medical_context:
            # Already medical, just add source preference
            return f"{query} site:nih.gov OR site:cdc.gov OR site:who.int OR site:pubmed.gov"
        else:
            # Add medical context
            return f"medical {query} clinical guidelines"
    
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """Parse Brave API response into clean result list"""
        results = []
        
        web_results = data.get("web", {}).get("results", [])
        
        for item in web_results[:self.max_results]:
            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
                "published_date": item.get("age", "Unknown date"),
                "source": "brave_search",
            }
            results.append(result)
        
        return results
    
    def extract_snippets(self, results: List[Dict]) -> List[str]:
        """Extract text snippets from search results for RAG-like usage"""
        snippets = []
        
        for result in results:
            snippet = result.get("snippet", "")
            if snippet:
                # Format: [Title] Snippet [URL]
                formatted = f"[{result['title']}] {snippet} [Source: {result['url']}]"
                snippets.append(formatted)
        
        return snippets
    
    def filter_by_relevance(
        self,
        results: List[Dict],
        query: str,
        threshold: float = 0.6,
    ) -> List[Dict]:
        """
        Filter results by relevance to query
        
        Simple keyword matching for now
        Can be enhanced with embedding similarity later
        """
        query_words = set(query.lower().split())
        filtered = []
        
        for result in results:
            # Calculate simple relevance score
            title_words = set(result.get("title", "").lower().split())
            snippet_words = set(result.get("snippet", "").lower().split())
            
            combined_words = title_words.union(snippet_words)
            overlap = len(query_words.intersection(combined_words))
            score = overlap / len(query_words) if query_words else 0
            
            if score >= threshold:
                result["relevance_score"] = score
                filtered.append(result)
        
        # Sort by relevance
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return filtered
    
    def deduplicate_with_rag(
        self,
        web_results: List[Dict],
        rag_sources: List[Dict],
    ) -> List[Dict]:
        """
        Remove web results that duplicate RAG sources
        
        Useful to avoid showing the same information twice
        """
        # For now, simple title matching
        # Can be enhanced with URL/content similarity
        
        rag_titles = set()
        for source in rag_sources:
            source_file = source.get("source_file", "").lower()
            # Extract document name
            if source_file:
                doc_name = source_file.split("/")[-1].replace(".pdf", "")
                rag_titles.add(doc_name)
        
        filtered = []
        for result in web_results:
            title_lower = result.get("title", "").lower()
            # Check if web result title overlaps with RAG sources
            is_duplicate = any(rag_title in title_lower for rag_title in rag_titles)
            
            if not is_duplicate:
                filtered.append(result)
        
        return filtered
