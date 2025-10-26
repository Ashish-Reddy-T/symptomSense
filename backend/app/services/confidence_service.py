"""
Unified Confidence Scoring Service

Aggregates confidence from multiple sources:
- Image analysis confidence
- RAG retrieval scores
- LLM generation logprobs

Provides confidence profile for decision-making.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ConfidenceProfile:
    """Unified confidence metrics"""
    overall_confidence: float  # 0-1 scale
    image_confidence: Optional[float] = None
    rag_confidence: Optional[float] = None
    llm_confidence: Optional[float] = None
    confidence_level: str = "unknown"  # "high", "medium", "low", "unknown"
    
    def to_dict(self) -> Dict:
        return {
            "overall_confidence": round(self.overall_confidence, 3),
            "image_confidence": round(self.image_confidence, 3) if self.image_confidence else None,
            "rag_confidence": round(self.rag_confidence, 3) if self.rag_confidence else None,
            "llm_confidence": round(self.llm_confidence, 3) if self.llm_confidence else None,
            "confidence_level": self.confidence_level,
        }


class ConfidenceService:
    """Service for calculating and categorizing confidence scores"""
    
    def __init__(
        self,
        high_threshold: float = 0.85,
        medium_threshold: float = 0.70,
    ):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        
    def calculate_rag_confidence(self, rag_scores: List[float]) -> float:
        """
        Calculate RAG confidence from retrieval scores
        
        Logic:
        - Use max score as primary indicator
        - Boost if multiple high scores (consensus)
        - Penalize if all scores are low
        """
        if not rag_scores:
            return 0.0
            
        max_score = max(rag_scores)
        avg_score = sum(rag_scores) / len(rag_scores)
        
        # Weighted combination: 70% max, 30% average
        confidence = 0.7 * max_score + 0.3 * avg_score
        
        # Boost if we have consensus (multiple high scores)
        high_scores = [s for s in rag_scores if s > 0.6]
        if len(high_scores) >= 3:
            confidence = min(confidence * 1.1, 1.0)
            
        return confidence
    
    def calculate_llm_confidence(self, logprobs: List[float]) -> float:
        """
        Calculate LLM confidence from logprobs
        
        Logic:
        - Convert average logprob to 0-1 scale
        - Higher (less negative) logprobs = higher confidence
        """
        if not logprobs:
            return 0.75  # Default moderate confidence
            
        avg_logprob = sum(logprobs) / len(logprobs)
        
        # Convert logprob to confidence (0-1 scale)
        # Logprobs typically range from -5 to 0
        # -0.5 or better = high confidence
        # -2.0 = medium confidence
        # -5.0 or worse = low confidence
        
        if avg_logprob >= -0.5:
            return 0.95
        elif avg_logprob >= -1.0:
            return 0.85
        elif avg_logprob >= -2.0:
            return 0.70
        elif avg_logprob >= -3.0:
            return 0.55
        else:
            return 0.40
    
    def aggregate_confidence(
        self,
        image_conf: Optional[float] = None,
        rag_scores: Optional[List[float]] = None,
        llm_logprobs: Optional[List[float]] = None,
    ) -> ConfidenceProfile:
        """
        Aggregate confidence from all sources
        
        Weighting strategy:
        - If image present: Image 50%, RAG 25%, LLM 25%
        - If text only: RAG 60%, LLM 40%
        """
        rag_conf = self.calculate_rag_confidence(rag_scores or [])
        llm_conf = self.calculate_llm_confidence(llm_logprobs or [])
        
        # Determine weights based on what's available
        if image_conf is not None and image_conf > 0:
            # Multi-modal: prioritize image
            weights = {"image": 0.5, "rag": 0.25, "llm": 0.25}
            overall = (
                weights["image"] * image_conf +
                weights["rag"] * rag_conf +
                weights["llm"] * llm_conf
            )
        elif rag_scores:
            # Text-only: prioritize RAG
            weights = {"rag": 0.6, "llm": 0.4}
            overall = (
                weights["rag"] * rag_conf +
                weights["llm"] * llm_conf
            )
        else:
            # Fallback to LLM only
            overall = llm_conf
        
        # Categorize confidence level
        if overall >= self.high_threshold:
            level = "high"
        elif overall >= self.medium_threshold:
            level = "medium"
        else:
            level = "low"
        
        profile = ConfidenceProfile(
            overall_confidence=overall,
            image_confidence=image_conf,
            rag_confidence=rag_conf if rag_scores else None,
            llm_confidence=llm_conf,
            confidence_level=level,
        )
        
        logger.info(
            "confidence_calculated",
            profile=profile.to_dict(),
            has_image=image_conf is not None,
            num_rag_scores=len(rag_scores) if rag_scores else 0,
            num_logprobs=len(llm_logprobs) if llm_logprobs else 0,
        )
        
        return profile
    
    def should_trigger_hitl(self, profile: ConfidenceProfile) -> bool:
        """Determine if query should be flagged for human review"""
        return profile.confidence_level == "low"
    
    def should_trigger_web_search(
        self,
        profile: ConfidenceProfile,
        query: str = "",
    ) -> bool:
        """
        Determine if web search should be triggered
        
        Triggers:
        - RAG confidence < 0.5
        - No RAG results
        - Temporal keywords in query
        """
        temporal_keywords = ['latest', 'current', 'recent', 'new', '2024', '2025', 'update']
        
        # Check RAG confidence
        if profile.rag_confidence is None or profile.rag_confidence < 0.5:
            return True
        
        # Check for temporal queries
        query_lower = query.lower()
        if any(kw in query_lower for kw in temporal_keywords):
            return True
            
        return False
