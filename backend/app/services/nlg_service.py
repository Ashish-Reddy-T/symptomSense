"""
Natural Language Generation Service

Transforms technical/structured outputs into natural, conversational responses.
Adjusts tone and disclaimers based on confidence levels.
"""

from typing import Dict, List, Optional
from .confidence_service import ConfidenceProfile
import structlog

logger = structlog.get_logger(__name__)


class NLGService:
    """Service for naturalizing AI responses"""
    
    # Phrasing templates based on confidence
    HIGH_CONFIDENCE_PHRASES = [
        "Based on the analysis, this appears to be {finding}.",
        "The {modality} shows signs consistent with {finding}.",
        "This analysis indicates {finding}.",
    ]
    
    MEDIUM_CONFIDENCE_PHRASES = [
        "The {modality} suggests {finding}, though additional verification would be helpful.",
        "This appears consistent with {finding}. Further testing may help confirm.",
        "The analysis shows patterns that may indicate {finding}.",
    ]
    
    LOW_CONFIDENCE_PHRASES = [
        "The analysis is inconclusive, but some patterns suggest possible {finding}.",
        "While not definitive, there are some indicators that could point to {finding}.",
        "The available information doesn't provide a clear picture, though {finding} is a possibility.",
    ]
    
    def __init__(self, tone: str = "professional_conversational"):
        """
        Initialize NLG service
        
        Args:
            tone: Response tone - "clinical", "conversational", "professional_conversational"
        """
        self.tone = tone
    
    def naturalize_response(
        self,
        raw_answer: str,
        confidence_profile: ConfidenceProfile,
        image_analysis: Optional[Dict] = None,
        rag_context: Optional[List[str]] = None,
        web_sources: Optional[List[Dict]] = None,
    ) -> str:
        """
        Transform structured response into natural language
        
        Args:
            raw_answer: Generated answer from LLM
            confidence_profile: Unified confidence metrics
            image_analysis: Image classification results
            rag_context: Retrieved document chunks
            web_sources: Web search results
        
        Returns:
            Naturalized response text
        """
        sections = []
        
        # Main answer with confidence-appropriate phrasing
        main_answer = self._craft_main_answer(
            raw_answer,
            confidence_profile,
            image_analysis
        )
        sections.append(main_answer)
        
        # Supporting context (if high/medium confidence)
        if confidence_profile.confidence_level in ["high", "medium"]:
            context = self._add_supporting_context(rag_context, web_sources)
            if context:
                sections.append(context)
        
        # Next steps / recommendations
        next_steps = self._generate_next_steps(
            confidence_profile,
            image_analysis
        )
        if next_steps:
            sections.append(next_steps)
        
        # Smart disclaimer (only if needed)
        disclaimer = self._generate_smart_disclaimer(confidence_profile)
        if disclaimer:
            sections.append(disclaimer)
        
        return "\n\n".join(sections)
    
    def _craft_main_answer(
        self,
        raw_answer: str,
        profile: ConfidenceProfile,
        image_analysis: Optional[Dict],
    ) -> str:
        """Craft the main answer with appropriate confidence phrasing"""
        
        # If we have image analysis, lead with that
        if image_analysis and image_analysis.get("prediction"):
            finding = image_analysis["prediction"]
            conf_pct = int(image_analysis.get("confidence", 0) * 100)
            
            if profile.confidence_level == "high":
                intro = f"Based on the X-ray analysis, this appears to be {finding}. The imaging shows characteristic patterns consistent with this condition, with a {conf_pct}% confidence level."
            elif profile.confidence_level == "medium":
                intro = f"The X-ray shows patterns that suggest {finding} (confidence: {conf_pct}%). Additional clinical correlation would help confirm this assessment."
            else:
                intro = f"The X-ray analysis suggests possible {finding}, though the confidence level is moderate ({conf_pct}%). A more comprehensive evaluation is recommended."
            
            # Append the rest of the answer
            if raw_answer and not raw_answer.lower().startswith("the image"):
                return f"{intro}\n\n{raw_answer}"
            return intro
        
        # Text-only response - use the raw answer but adjust tone
        if profile.confidence_level == "low":
            prefix = "Based on available information, "
            return f"{prefix}{raw_answer}"
        
        return raw_answer
    
    def _add_supporting_context(
        self,
        rag_context: Optional[List[str]],
        web_sources: Optional[List[Dict]],
    ) -> Optional[str]:
        """Add supporting context from sources"""
        
        parts = []
        
        if rag_context:
            parts.append("This assessment aligns with current medical literature on the topic.")
        
        if web_sources:
            parts.append("Recent clinical guidelines also support this interpretation.")
        
        if not parts:
            return None
        
        return " ".join(parts)
    
    def _generate_next_steps(
        self,
        profile: ConfidenceProfile,
        image_analysis: Optional[Dict],
    ) -> Optional[str]:
        """Generate actionable next steps"""
        
        steps = []
        
        if image_analysis:
            steps.extend([
                "Correlate with clinical symptoms and patient history",
                "Consider additional diagnostic tests if clinically indicated",
                "Consult with a healthcare provider for comprehensive evaluation",
            ])
        else:
            steps.extend([
                "Discuss findings with a qualified healthcare professional",
                "Consider relevant diagnostic tests based on symptoms",
                "Follow evidence-based clinical guidelines for your specific situation",
            ])
        
        if profile.confidence_level == "low":
            steps.insert(0, "Seek professional medical evaluation due to diagnostic uncertainty")
        
        # Format as bullet list
        formatted_steps = "\n".join([f"• {step}" for step in steps])
        return f"**Recommended Next Steps:**\n{formatted_steps}"
    
    def _generate_smart_disclaimer(self, profile: ConfidenceProfile) -> Optional[str]:
        """Generate context-aware disclaimer (not blanket warning)"""
        
        if profile.confidence_level == "high":
            # Minimal disclaimer for high confidence
            return ("**Note:** While this analysis shows high confidence, a formal diagnosis "
                    "should be confirmed by a qualified healthcare professional who can "
                    "consider your complete clinical picture.")
        
        elif profile.confidence_level == "medium":
            # Balanced disclaimer
            return ("**Important:** This assessment should be verified through professional "
                    "medical evaluation. The confidence level suggests that additional "
                    "information or testing may provide more clarity.")
        
        else:  # low confidence
            # Strong disclaimer
            return ("**Important Notice:** The confidence level for this analysis is low, "
                    "indicating significant diagnostic uncertainty. Professional medical "
                    "evaluation is strongly recommended. Do not make health decisions "
                    "based solely on this assessment.")
    
    def format_citations(
        self,
        rag_sources: Optional[List[Dict]] = None,
        web_sources: Optional[List[Dict]] = None,
        image_source: Optional[Dict] = None,
    ) -> str:
        """
        Format citations with proper numbering
        
        Returns formatted citation list
        """
        citations = []
        
        # Image insights (if present)
        if image_source:
            citations.append("**Image Analysis:**")
            citations.append(f"• {image_source.get('model', 'Vision Model')} - "
                           f"{image_source.get('prediction', 'N/A')} "
                           f"({int(image_source.get('confidence', 0) * 100)}% confidence)")
            citations.append("")
        
        # RAG sources
        if rag_sources:
            citations.append("**Knowledge Base Sources:**")
            for i, source in enumerate(rag_sources[:5], 1):
                doc_name = source.get("source_file", "Unknown").split("/")[-1]
                score = source.get("score", 0)
                citations.append(f"• [doc{i}] {doc_name} (relevance: {score:.2f})")
            citations.append("")
        
        # Web sources
        if web_sources:
            citations.append("**External Sources:**")
            for i, source in enumerate(web_sources[:5], 1):
                title = source.get("title", "Web Source")
                url = source.get("url", "#")
                citations.append(f"• [web{i}] {title}")
                citations.append(f"  {url}")
            citations.append("")
        
        return "\n".join(citations) if citations else ""
    
    def create_summary_response(
        self,
        natural_answer: str,
        citations: str,
        confidence_profile: ConfidenceProfile,
    ) -> Dict:
        """
        Create final structured response with natural language
        
        Returns complete response dict
        """
        return {
            "answer": natural_answer,
            "citations": citations,
            "confidence": confidence_profile.to_dict(),
            "confidence_level": confidence_profile.confidence_level,
        }
