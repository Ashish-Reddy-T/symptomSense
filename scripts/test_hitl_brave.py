#!/usr/bin/env python3
"""
Test HITL and Brave Search services
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.services.hitl_service import HITLService
from app.services.brave_search_service import BraveSearchService
from app.services.confidence_service import ConfidenceService, ConfidenceProfile

def test_hitl_service():
    """Test HITL service queue management"""
    print("=" * 60)
    print("Testing HITL Service")
    print("=" * 60)
    
    # Use a test queue path
    service = HITLService(
        queue_path="./data/hitl_queue_test",
        enabled=True,
        confidence_threshold=0.70
    )
    
    # Test 1: Check if should flag low confidence
    print("\n[Test 1] Should flag low confidence query")
    low_conf_profile = ConfidenceProfile(
        overall_confidence=0.58,
        image_confidence=0.55,
        rag_confidence=0.45,
        llm_confidence=0.65,
        confidence_level="low"
    )
    should_flag = service.should_flag_for_review(low_conf_profile)
    print(f"Low confidence ({low_conf_profile.overall_confidence}) should be flagged: {should_flag}")
    assert should_flag == True, "Low confidence should trigger HITL"
    
    # Test 2: Don't flag high confidence
    print("\n[Test 2] Should NOT flag high confidence query")
    high_conf_profile = ConfidenceProfile(
        overall_confidence=0.89,
        image_confidence=0.91,
        rag_confidence=0.75,
        llm_confidence=0.90,
        confidence_level="high"
    )
    should_flag = service.should_flag_for_review(high_conf_profile)
    print(f"High confidence ({high_conf_profile.overall_confidence}) should be flagged: {should_flag}")
    assert should_flag == False, "High confidence should NOT trigger HITL"
    
    # Test 3: Flag contradictory signals
    print("\n[Test 3] Should flag contradictory confidence signals")
    contradictory_profile = ConfidenceProfile(
        overall_confidence=0.75,
        image_confidence=0.95,
        rag_confidence=0.30,  # Big difference!
        llm_confidence=0.80,
        confidence_level="medium"
    )
    should_flag = service.should_flag_for_review(contradictory_profile)
    print(f"Contradictory signals (image=0.95, rag=0.30) should be flagged: {should_flag}")
    assert should_flag == True, "Contradictory signals should trigger HITL"
    
    # Test 4: Add item to queue
    print("\n[Test 4] Add item to HITL queue")
    item = service.add_to_queue(
        query="Is this pneumonia?",
        confidence_profile=low_conf_profile,
        initial_response="Uncertain analysis...",
        image_data="base64_image_data_here"
    )
    print(f"Created HITL item: {item.id}")
    print(f"Status: {item.status}")
    assert item.status == "pending"
    
    # Test 5: Get queue stats
    print("\n[Test 5] Get queue statistics")
    stats = service.get_queue_stats()
    print(f"Queue stats: {stats}")
    assert stats["pending"] >= 1, "Should have at least 1 pending item"
    
    # Test 6: Get pending items
    print("\n[Test 6] Retrieve pending items")
    pending = service.get_pending_items()
    print(f"Found {len(pending)} pending items")
    assert len(pending) >= 1
    
    # Test 7: Update item status
    print("\n[Test 7] Update item with expert feedback")
    success = service.update_item_status(
        item_id=item.id,
        status="resolved",
        expert_feedback="Confirmed diagnosis of pneumonia by radiologist"
    )
    print(f"Update successful: {success}")
    assert success == True
    
    # Test 8: Generate HITL flag message
    print("\n[Test 8] Generate user-facing HITL message")
    message = service.generate_hitl_flag_message(low_conf_profile)
    print(f"HITL Message:\n{message}")
    assert "flagged for expert review" in message.lower()
    
    print("\n✅ HITL Service tests completed!\n")
    return True


async def test_brave_search_service():
    """Test Brave Search service (mocked if no API key)"""
    print("=" * 60)
    print("Testing Brave Search Service")
    print("=" * 60)
    
    # Check if API key exists
    api_key = os.getenv("BRAVE_API_KEY")
    
    if not api_key or api_key == "your_brave_key_here":
        print("\n⚠️  No Brave API key found - running with mock mode")
        service = BraveSearchService(api_key=None, enabled=False)
        
        # Test disabled service
        print("\n[Test 1] Service disabled without API key")
        print(f"Service enabled: {service.enabled}")
        assert service.enabled == False
        
        results = await service.search_medical_web("pneumonia treatment")
        print(f"Results with disabled service: {results}")
        assert results == []
        
        print("\n✅ Brave Search Service tests completed (mock mode)!\n")
        return True
    
    # Real API tests
    service = BraveSearchService(
        api_key=api_key,
        enabled=True,
        max_results=3,
        timeout=10
    )
    
    print(f"\n✅ Brave API key found - running real API tests")
    
    # Test 1: Basic search
    print("\n[Test 1] Search for medical information")
    results = await service.search_medical_web("pneumonia symptoms treatment")
    print(f"Found {len(results)} results")
    if results:
        print(f"First result: {results[0]['title'][:60]}...")
    
    # Test 2: Temporal query
    print("\n[Test 2] Search with temporal keywords")
    results = await service.search_medical_web("latest 2025 covid treatment guidelines")
    print(f"Found {len(results)} results for temporal query")
    
    # Test 3: Extract snippets
    if results:
        print("\n[Test 3] Extract snippets from results")
        snippets = service.extract_snippets(results)
        print(f"Extracted {len(snippets)} snippets")
        if snippets:
            print(f"First snippet (truncated): {snippets[0][:100]}...")
    
    # Test 4: Relevance filtering
    print("\n[Test 4] Filter results by relevance")
    filtered = service.filter_by_relevance(results, "treatment", threshold=0.3)
    print(f"Filtered to {len(filtered)} relevant results")
    
    # Test 5: Deduplicate with RAG
    print("\n[Test 5] Deduplicate with RAG sources")
    rag_sources = [
        {"source_file": "data/knowledge_base/pneumonia_guide.pdf"},
    ]
    deduplicated = service.deduplicate_with_rag(results, rag_sources)
    print(f"After deduplication: {len(deduplicated)} results")
    
    print("\n✅ Brave Search Service tests completed!\n")
    return True


if __name__ == "__main__":
    try:
        print("\n🧪 Starting HITL and Brave Search Tests\n")
        
        success = True
        
        # Test HITL (synchronous)
        success = test_hitl_service() and success
        
        # Test Brave Search (async)
        success = asyncio.run(test_brave_search_service()) and success
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\n💡 Note: If you have a Brave API key, add it to .env to test real searches")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
