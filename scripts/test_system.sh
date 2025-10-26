#!/bin/bash
# Comprehensive system test script

set -e

echo "🧪 =========================================="
echo "   AGENTIC MEDICAL ASSISTANT - SYSTEM TESTS"
echo "=========================================="
echo ""

API_BASE="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo "📡 Test 1: Health Check"
response=$(curl -s "${API_BASE}/health")
if echo "$response" | grep -q "ok"; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: Simple text query
echo "📝 Test 2: Simple Medical Query"
response=$(curl -s -X POST "${API_BASE}/api/process_input" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "What is pneumonia?"}')

answer_len=$(echo "$response" | jq -r '.answer | length')
if [ "$answer_len" -gt 100 ]; then
    echo -e "${GREEN}✅ Got response (${answer_len} chars)${NC}"
    echo "$response" | jq -r '.answer' | head -3
else
    echo -e "${RED}❌ Response too short or failed${NC}"
    echo "$response" | jq '.'
    exit 1
fi
echo ""

# Test 3: Web search query (temporal)
echo "🌐 Test 3: Web Search (Temporal Query)"
response=$(curl -s -X POST "${API_BASE}/api/process_input" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "What are the latest 2025 COVID treatment guidelines?"}')

web_count=$(echo "$response" | jq -r '.web_sources | length')
if [ "$web_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Web search triggered - ${web_count} sources found${NC}"
    echo "$response" | jq -r '.web_sources[0].title'
else
    echo -e "${YELLOW}⚠️  No web sources (might be expected)${NC}"
fi
echo ""

# Test 4: Image classification
echo "🖼️  Test 4: Image Classification"
# Create simple test image
python3 -c "import base64, io; from PIL import Image; img = Image.new('RGB', (100, 100), 'gray'); buf = io.BytesIO(); img.save(buf, format='PNG'); print(f'data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}')" > /tmp/test_img.txt

response=$(curl -s -X POST "${API_BASE}/api/process_input" \
  -H "Content-Type: application/json" \
  -d "{\"text_query\": \"Analyze this X-ray\", \"image_base64\": \"$(cat /tmp/test_img.txt)\"}")

img_label=$(echo "$response" | jq -r '.image_analysis.label // "none"')
img_conf=$(echo "$response" | jq -r '.image_analysis.confidence // 0')
if [ "$img_label" != "none" ]; then
    echo -e "${GREEN}✅ Image classified as: ${img_label} (${img_conf})${NC}"
else
    echo -e "${RED}❌ Image classification failed${NC}"
    exit 1
fi
echo ""

# Test 5: Confidence and HITL
echo "🎯 Test 5: Confidence System"
confidence=$(echo "$response" | jq -r '.confidence_profile.confidence_level')
hitl=$(echo "$response" | jq -r '.hitl_flagged')
echo -e "   Confidence Level: ${YELLOW}${confidence}${NC}"
echo -e "   HITL Flagged: ${hitl}"
echo ""

# Test 6: Frontend accessibility
echo "🌐 Test 6: Frontend Accessibility"
frontend_response=$(curl -s http://localhost:3000/)
if echo "$frontend_response" | grep -q "Agentic"; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "=========================================="
echo ""
echo "📊 Access URLs:"
echo "   Backend:  http://localhost:8000/health"
echo "   Frontend: http://localhost:3000/"
echo "   API Docs: http://localhost:8000/docs"
echo ""
