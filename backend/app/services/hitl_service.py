"""
Human-in-the-Loop (HITL) Service

Manages low-confidence queries that need human expert review.
Provides queue management and confidence-based routing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from .confidence_service import ConfidenceProfile
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HITLQueueItem:
    """Item in the HITL review queue"""
    id: str
    timestamp: str
    query: str
    image_data: Optional[str] = None
    initial_response: Optional[str] = None
    confidence_profile: Optional[Dict] = None
    status: str = "pending"  # pending, in_review, resolved
    expert_feedback: Optional[str] = None
    resolution_timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class HITLService:
    """Service for managing human-in-the-loop review queue"""
    
    def __init__(
        self,
        queue_path: str = "./data/hitl_queue",
        enabled: bool = True,
        confidence_threshold: float = 0.70,
    ):
        self.queue_path = Path(queue_path)
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        
        # Ensure queue directory exists
        if self.enabled:
            self.queue_path.mkdir(parents=True, exist_ok=True)
            logger.info("hitl_service_initialized", queue_path=str(self.queue_path))
    
    def should_flag_for_review(self, confidence_profile: ConfidenceProfile) -> bool:
        """
        Determine if query should be flagged for human review
        
        Criteria:
        - Overall confidence < threshold
        - Contradictory confidence signals (high image, low RAG)
        """
        if not self.enabled:
            return False
        
        # Primary check: low overall confidence
        if confidence_profile.overall_confidence < self.confidence_threshold:
            return True
        
        # Secondary check: contradictory signals
        if (confidence_profile.image_confidence and 
            confidence_profile.rag_confidence):
            diff = abs(confidence_profile.image_confidence - confidence_profile.rag_confidence)
            if diff > 0.4:  # 40% difference is significant
                logger.warning(
                    "contradictory_confidence_signals",
                    image_conf=confidence_profile.image_confidence,
                    rag_conf=confidence_profile.rag_confidence,
                )
                return True
        
        return False
    
    def add_to_queue(
        self,
        query: str,
        confidence_profile: ConfidenceProfile,
        initial_response: Optional[str] = None,
        image_data: Optional[str] = None,
    ) -> HITLQueueItem:
        """Add query to HITL review queue"""
        
        item_id = f"hitl_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        item = HITLQueueItem(
            id=item_id,
            timestamp=datetime.utcnow().isoformat(),
            query=query,
            image_data=image_data,
            initial_response=initial_response,
            confidence_profile=confidence_profile.to_dict(),
            status="pending",
        )
        
        # Save to disk
        if self.enabled:
            item_file = self.queue_path / f"{item_id}.json"
            with open(item_file, "w") as f:
                json.dump(item.to_dict(), f, indent=2)
            
            logger.info(
                "hitl_item_queued",
                item_id=item_id,
                confidence=confidence_profile.overall_confidence,
            )
        
        return item
    
    def get_pending_items(self) -> List[HITLQueueItem]:
        """Get all pending HITL items"""
        if not self.enabled:
            return []
        
        items = []
        for item_file in self.queue_path.glob("hitl_*.json"):
            try:
                with open(item_file, "r") as f:
                    data = json.load(f)
                    if data.get("status") == "pending":
                        items.append(HITLQueueItem(**data))
            except Exception as e:
                logger.error("error_loading_hitl_item", file=str(item_file), error=str(e))
        
        # Sort by timestamp (oldest first)
        items.sort(key=lambda x: x.timestamp)
        return items
    
    def update_item_status(
        self,
        item_id: str,
        status: str,
        expert_feedback: Optional[str] = None,
    ) -> bool:
        """Update HITL item with expert feedback"""
        if not self.enabled:
            return False
        
        item_file = self.queue_path / f"{item_id}.json"
        if not item_file.exists():
            logger.error("hitl_item_not_found", item_id=item_id)
            return False
        
        try:
            with open(item_file, "r") as f:
                data = json.load(f)
            
            data["status"] = status
            if expert_feedback:
                data["expert_feedback"] = expert_feedback
            if status == "resolved":
                data["resolution_timestamp"] = datetime.utcnow().isoformat()
            
            with open(item_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info("hitl_item_updated", item_id=item_id, status=status)
            return True
        
        except Exception as e:
            logger.error("error_updating_hitl_item", item_id=item_id, error=str(e))
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get statistics about HITL queue"""
        if not self.enabled:
            return {"enabled": False}
        
        all_items = []
        for item_file in self.queue_path.glob("hitl_*.json"):
            try:
                with open(item_file, "r") as f:
                    data = json.load(f)
                    all_items.append(data)
            except Exception:
                pass
        
        stats = {
            "enabled": True,
            "total_items": len(all_items),
            "pending": sum(1 for item in all_items if item.get("status") == "pending"),
            "in_review": sum(1 for item in all_items if item.get("status") == "in_review"),
            "resolved": sum(1 for item in all_items if item.get("status") == "resolved"),
        }
        
        return stats
    
    def generate_hitl_flag_message(self, confidence_profile: ConfidenceProfile) -> str:
        """
        Generate user-facing message when query is flagged for review
        
        Returns message to append to response
        """
        if confidence_profile.confidence_level == "low":
            return (
                "\n\n**⚠️ This query has been flagged for expert review** due to low "
                "confidence in the analysis. A medical professional will review this "
                "case to provide more accurate guidance. Please check back later or "
                "consult with your healthcare provider in the meantime."
            )
        else:
            return (
                "\n\n**ℹ️ This query has been flagged for additional review** to ensure "
                "accuracy. The initial analysis is provided above, but it will be "
                "verified by a medical expert."
            )
