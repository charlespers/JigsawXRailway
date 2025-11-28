#!/bin/bash
# Comprehensive smoke test for PCB Design API
# Run this before deployments to catch route registration issues

BACKEND_URL="${BACKEND_URL:-https://web-backend-24f1.up.railway.app}"

echo "=== PCB Design API Smoke Test ==="
echo "Backend URL: $BACKEND_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=${4:-200}
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BACKEND_URL$endpoint" 2>&1)
    else
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BACKEND_URL$endpoint" 2>&1)
    fi
    
    http_code=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} $method $endpoint -> $http_code"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $method $endpoint -> $http_code (expected $expected_status)"
        echo "  Response: $(echo "$body" | head -c 200)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test 1: Health check
echo "1. Health Check"
test_endpoint "GET" "/health" "" 200
echo ""

# Test 2: Routes diagnostics
echo "2. Routes Diagnostics"
test_endpoint "GET" "/api/v1/routes" "" 200
test_endpoint "POST" "/api/v1/analysis/test" "{}" 200
echo ""

# Test 3: Analysis endpoints (with minimal test data)
TEST_PART='{"id":"test-001","mpn":"TEST-001","manufacturer":"Test","category":"test","cost_estimate":1.0}'
TEST_BOM='{"bom_items":[{"part_data":'$TEST_PART',"quantity":1}],"connections":[],"provider":"xai"}'

echo "3. Analysis Endpoints"
test_endpoint "POST" "/api/v1/analysis/cost" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/supply-chain" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/power" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/thermal" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/signal-integrity" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/manufacturing-readiness" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/validation" "$TEST_BOM" 200
test_endpoint "POST" "/api/v1/analysis/bom-insights" "$TEST_BOM" 200
echo ""

# Test 4: Streaming endpoint (just verify it exists)
echo "4. Streaming Endpoint"
test_endpoint "POST" "/mcp/component-analysis" '{"query":"test"}' 200
echo ""

# Summary
echo "=== Test Summary ==="
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""
    echo "⚠️  Some endpoints failed. Check route registration in routes/__init__.py"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi

