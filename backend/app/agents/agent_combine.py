"""
Agent Orchestrator (Agent Combine)

Intelligent routing and combination of specialized agents based on:
- Query type (image, text, multi-modal)
- Confidence scores
- Previous agent results
- Temporal requirements
"""

from typing import Dict, List, Optional, Literal
import structlog

logger = structlog.get_logger(__name__)


class AgentOrchestrator:
    """
    Intelligent multi-agent coordinator
    
    Decides which agents to invoke and how to combine their results
    based on confidence scores and query characteristics.
    """
    
    def __init__(
        self,
        web_search_threshold: float = 0.5,
        hitl_threshold: float = 0.70,
    ):
        self.web_search_threshold = web_search_threshold
        self.hitl_threshold = hitl_threshold
    
    def should_invoke_web_search(
        self,
        state: Dict,
        confidence_service,
    ) -> bool:
        """
        Determine if web search agent should be invoked
        
        Triggers:
        - RAG confidence < threshold
        - Temporal keywords in query
        - Zero or very few RAG results
        """
        query = state.get("text_query", "").lower()
        rag_scores = state.get("rag_scores", [])
        
        # Check if RAG returned results
        if not rag_scores:
            logger.info("web_search_trigger_no_rag_results")
            return True
        
        # Check RAG confidence
        max_rag_score = max(rag_scores) if rag_scores else 0
        if max_rag_score < self.web_search_threshold:
            logger.info(
                "web_search_trigger_low_rag_confidence",
                max_score=max_rag_score,
                threshold=self.web_search_threshold,
            )
            return True
        
        # Check for temporal keywords
        temporal_keywords = [
            'latest', 'current', 'recent', 'new', 'update',
            '2024', '2025', 'today', 'now', 'modern'
        ]
        
        if any(kw in query for kw in temporal_keywords):
            logger.info("web_search_trigger_temporal_query", query=query[:50])
            return True
        
        return False
    
    def combine_rag_and_web_context(
        self,
        rag_context: List[str],
        rag_scores: List[float],
        web_snippets: List[str],
        web_results: List[Dict],
    ) -> Dict:
        """
        Merge RAG and web search results into unified context
        
        Strategy:
        - Weight by confidence/relevance
        - Prefer recent web sources if available
        - Maintain attribution
        """
        combined = {
            "context_chunks": [],
            "sources": [],
        }
        
        # Add RAG results with attribution
        for i, (chunk, score) in enumerate(zip(rag_context, rag_scores), 1):
            combined["context_chunks"].append({
                "text": chunk,
                "source_type": "knowledge_base",
                "source_id": f"doc{i}",
                "relevance": score,
            })
        
        # Add web results with attribution
        for i, (snippet, result) in enumerate(zip(web_snippets, web_results), 1):
            combined["context_chunks"].append({
                "text": snippet,
                "source_type": "web",
                "source_id": f"web{i}",
                "url": result.get("url"),
                "title": result.get("title"),
                "relevance": result.get("relevance_score", 0.7),  # Default moderate
            })
        
        # Sort by relevance
        combined["context_chunks"].sort(
            key=lambda x: x.get("relevance", 0),
            reverse=True,
        )
        
        logger.info(
            "context_combined",
            num_rag=len(rag_context),
            num_web=len(web_snippets),
            total=len(combined["context_chunks"]),
        )
        
        return combined
    
    def resolve_contradictions(
        self,
        image_result: Optional[Dict],
        rag_context: List[str],
        web_snippets: List[str],
    ) -> Dict:
        """
        Detect and resolve contradictory information from different sources
        
        Strategy:
        - Flag contradictions for user awareness
        - Prioritize high-confidence image results
        - Note discrepancies in final answer
        """
        contradictions = []
        
        # Simple keyword contradiction detection
        # (Can be enhanced with embeddings/LLM later)
        
        if image_result:
            image_finding = image_result.get("prediction", "").lower()
            
            # Check if RAG context contradicts image
            negative_keywords = ['not', 'no', 'negative', 'absent', 'clear']
            for chunk in rag_context[:3]:  # Check top 3 chunks
                chunk_lower = chunk.lower()
                if image_finding in chunk_lower:
                    if any(nk in chunk_lower for nk in negative_keywords):
                        contradictions.append({
                            "type": "image_vs_rag",
                            "description": f"Image suggests {image_finding} but text context may indicate otherwise",
                        })
                        break
        
        return {
            "has_contradictions": len(contradictions) > 0,
            "contradictions": contradictions,
        }
    
    def determine_agent_priority(
        self,
        state: Dict,
        confidence_profile: Optional[Dict] = None,
    ) -> Dict[str, float]:
        """
        Assign weights to different agent outputs for final combination
        
        Returns dict of agent weights (sum to 1.0)
        """
        weights = {}
        
        has_image = bool(state.get("image_data"))
        has_rag = bool(state.get("rag_context"))
        has_web = bool(state.get("web_search_results"))
        
        if has_image and confidence_profile:
            image_conf = confidence_profile.get("image_confidence", 0)
            if image_conf > 0.85:
                # High confidence image: prioritize
                weights["image"] = 0.6
                weights["rag"] = 0.2
                weights["web"] = 0.2
            elif image_conf > 0.70:
                # Medium confidence: balanced
                weights["image"] = 0.4
                weights["rag"] = 0.3
                weights["web"] = 0.3
            else:
                # Low confidence: de-prioritize image
                weights["image"] = 0.2
                weights["rag"] = 0.4
                weights["web"] = 0.4
        else:
            # Text-only
            if has_rag and has_web:
                # Both sources available
                rag_conf = confidence_profile.get("rag_confidence", 0) if confidence_profile else 0.5
                if rag_conf > 0.6:
                    weights["rag"] = 0.6
                    weights["web"] = 0.4
                else:
                    weights["rag"] = 0.4
                    weights["web"] = 0.6
            elif has_rag:
                weights["rag"] = 1.0
            elif has_web:
                weights["web"] = 1.0
        
        logger.info("agent_weights_calculated", weights=weights)
        return weights
    
    def create_synthesis_prompt(
        self,
        state: Dict,
        combined_context: Dict,
        confidence_profile: Dict,
        agent_weights: Dict[str, float],
    ) -> str:
        """
        Create prompt for LLM to synthesize final answer from multiple sources
        
        Provides clear instructions on how to weight and combine sources
        """
        query = state.get("text_query", "")
        image_analysis = state.get("image_analysis", {})
        
        prompt_parts = [
            f"**Query:** {query}\n",
        ]
        
        # Add image context if available
        if image_analysis:
            pred = image_analysis.get("prediction", "Unknown")
            conf = image_analysis.get("confidence", 0)
            weight = agent_weights.get("image", 0)
            prompt_parts.append(
                f"**Image Analysis (weight={weight:.0%}):** "
                f"{pred} (confidence: {conf:.0%})\n"
            )
        
        # Add knowledge base context
        rag_chunks = [c for c in combined_context["context_chunks"] if c["source_type"] == "knowledge_base"]
        if rag_chunks:
            weight = agent_weights.get("rag", 0)
            prompt_parts.append(f"\n**Knowledge Base Sources (weight={weight:.0%}):**\n")
            for chunk in rag_chunks[:3]:  # Top 3
                prompt_parts.append(f"- [{chunk['source_id']}] {chunk['text'][:200]}...\n")
        
        # Add web search context
        web_chunks = [c for c in combined_context["context_chunks"] if c["source_type"] == "web"]
        if web_chunks:
            weight = agent_weights.get("web", 0)
            prompt_parts.append(f"\n**Recent Web Sources (weight={weight:.0%}):**\n")
            for chunk in web_chunks[:3]:  # Top 3
                prompt_parts.append(f"- [{chunk['source_id']}] {chunk['text'][:200]}...\n")
        
        # Add instructions
        conf_level = confidence_profile.get("confidence_level", "medium")
        instructions = f"""
\n**Instructions:**
Based on the above sources, provide a comprehensive answer to the query.
- Weight sources according to the specified weights
- Cite sources using [doc1], [web1], etc.
- Confidence level: {conf_level}
- Tone: Professional yet conversational
- DO NOT add unnecessary disclaimers about being an AI
- Focus on providing accurate, actionable medical information

Generate a clear, natural language response:
"""
        prompt_parts.append(instructions)
        
        return "".join(prompt_parts)
