#!/usr/bin/env python3
"""
Quick test script for new services
Tests confidence_service and nlg_service with sample data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.services.confidence_service import ConfidenceService, ConfidenceProfile
from app.services.nlg_service import NLGService

def test_confidence_service():
    """Test confidence service with various scenarios"""
    print("=" * 60)
    print("Testing Confidence Service")
    print("=" * 60)
    
    service = ConfidenceService(high_threshold=0.85, medium_threshold=0.70)
    
    # Test 1: High confidence image + good RAG
    print("\n[Test 1] High confidence image + good RAG scores")
    profile = service.aggregate_confidence(
        image_conf=0.91,
        rag_scores=[0.65, 0.58, 0.52],
        llm_logprobs=[-0.3, -0.5, -0.4]
    )
    print(f"Result: {profile.to_dict()}")
    print(f"Should trigger HITL: {service.should_trigger_hitl(profile)}")
    print(f"Should trigger web search: {service.should_trigger_web_search(profile, 'what is pneumonia')}")
    
    # Test 2: Low RAG confidence (should trigger web search)
    print("\n[Test 2] Good image but low RAG confidence")
    profile = service.aggregate_confidence(
        image_conf=0.88,
        rag_scores=[0.25, 0.18, 0.15],
        llm_logprobs=[-0.5, -0.6]
    )
    print(f"Result: {profile.to_dict()}")
    print(f"Should trigger web search: {service.should_trigger_web_search(profile, 'pneumonia treatment')}")
    
    # Test 3: Temporal query (should trigger web search)
    print("\n[Test 3] Temporal query with decent RAG")
    profile = service.aggregate_confidence(
        image_conf=None,
        rag_scores=[0.60, 0.55],
        llm_logprobs=[-0.8, -0.9]
    )
    print(f"Result: {profile.to_dict()}")
    print(f"Should trigger web search: {service.should_trigger_web_search(profile, 'latest 2025 covid treatment')}")
    
    # Test 4: Low overall confidence (should trigger HITL)
    print("\n[Test 4] Low confidence across the board")
    profile = service.aggregate_confidence(
        image_conf=0.55,
        rag_scores=[0.30, 0.25],
        llm_logprobs=[-2.5, -3.0]
    )
    print(f"Result: {profile.to_dict()}")
    print(f"Should trigger HITL: {service.should_trigger_hitl(profile)}")
    
    print("\n✅ Confidence Service tests completed!\n")
    return True


def test_nlg_service():
    """Test NLG service with sample responses"""
    print("=" * 60)
    print("Testing NLG Service")
    print("=" * 60)
    
    service = NLGService(tone="professional_conversational")
    
    # Test 1: High confidence response
    print("\n[Test 1] High confidence pneumonia detection")
    profile = ConfidenceProfile(
        overall_confidence=0.89,
        image_confidence=0.91,
        rag_confidence=0.75,
        llm_confidence=0.90,
        confidence_level="high"
    )
    
    raw_answer = "The imaging shows consolidation consistent with pneumonia. Treatment typically involves antibiotics."
    
    image_analysis = {
        "prediction": "PNEUMONIA",
        "confidence": 0.91,
        "model": "ViT-XRay"
    }
    
    natural_response = service.naturalize_response(
        raw_answer=raw_answer,
        confidence_profile=profile,
        image_analysis=image_analysis,
        rag_context=["Pneumonia is inflammation of the lungs...", "Common symptoms include fever..."],
        web_sources=None
    )
    
    print(f"Natural Response:\n{natural_response}\n")
    
    # Test 2: Medium confidence response
    print("\n[Test 2] Medium confidence with RAG context")
    profile = ConfidenceProfile(
        overall_confidence=0.75,
        image_confidence=0.78,
        rag_confidence=0.68,
        llm_confidence=0.80,
        confidence_level="medium"
    )
    
    natural_response = service.naturalize_response(
        raw_answer="The patterns suggest pneumonia but additional tests would help confirm.",
        confidence_profile=profile,
        image_analysis={"prediction": "PNEUMONIA", "confidence": 0.78},
        rag_context=["Some context about pneumonia"],
    )
    
    print(f"Natural Response:\n{natural_response}\n")
    
    # Test 3: Low confidence response (should have strong disclaimer)
    print("\n[Test 3] Low confidence - should have strong disclaimer")
    profile = ConfidenceProfile(
        overall_confidence=0.58,
        image_confidence=0.55,
        rag_confidence=0.45,
        llm_confidence=0.65,
        confidence_level="low"
    )
    
    natural_response = service.naturalize_response(
        raw_answer="The analysis is unclear.",
        confidence_profile=profile,
        image_analysis={"prediction": "UNCERTAIN", "confidence": 0.55},
    )
    
    print(f"Natural Response:\n{natural_response}\n")
    
    # Test 4: Citation formatting
    print("\n[Test 4] Citation formatting")
    rag_sources = [
        {"source_file": "data/knowledge_base/pneumonia_guide.pdf", "score": 0.75},
        {"source_file": "data/knowledge_base/chest_xray_manual.pdf", "score": 0.68},
    ]
    
    web_sources = [
        {"title": "CDC Pneumonia Guidelines 2025", "url": "https://cdc.gov/pneumonia", "relevance_score": 0.82},
        {"title": "NIH Clinical Trials", "url": "https://nih.gov/trials", "relevance_score": 0.78},
    ]
    
    citations = service.format_citations(
        rag_sources=rag_sources,
        web_sources=web_sources,
        image_source={"model": "ViT-XRay", "prediction": "PNEUMONIA", "confidence": 0.91}
    )
    
    print(f"Citations:\n{citations}")
    
    print("\n✅ NLG Service tests completed!\n")
    return True


if __name__ == "__main__":
    try:
        print("\n🧪 Starting Service Tests\n")
        
        success = True
        success = test_confidence_service() and success
        success = test_nlg_service() and success
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
