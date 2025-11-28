#!/bin/bash
# Test script for all API endpoints

BACKEND_URL="https://web-backend-24f1.up.railway.app"

echo "=== Testing Backend Endpoints ==="
echo "Backend URL: $BACKEND_URL"
echo ""

echo "1. Health Check:"
curl -s "$BACKEND_URL/health"
echo -e "\n"

echo "2. Routes List:"
curl -s "$BACKEND_URL/api/v1/routes"
echo -e "\n"

echo "3. Test Analysis Endpoint:"
curl -s -X POST "$BACKEND_URL/api/v1/analysis/test" \
  -H "Content-Type: application/json" \
  -d '{}'
echo -e "\n"

echo "4. Validation Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/validation" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test"}, "quantity": 1}], "connections": [], "constraints": {}}'
echo -e "\n"

echo "5. Cost Analysis Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/cost" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test", "cost_estimate": 1.0}, "quantity": 1}]}'
echo -e "\n"

echo "6. Power Analysis Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/power" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test"}, "quantity": 1}], "connections": []}'
echo -e "\n"

echo "7. Thermal Analysis Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/thermal" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test"}, "quantity": 1}], "connections": []}'
echo -e "\n"

echo "8. Supply Chain Analysis Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/supply-chain" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test"}, "quantity": 1}]}'
echo -e "\n"

echo "9. Signal Integrity Analysis Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/signal-integrity" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test"}, "quantity": 1}], "connections": [], "pcb_thickness_mm": 1.6, "trace_width_mils": 5}'
echo -e "\n"

echo "10. Manufacturing Readiness Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BACKEND_URL/api/v1/analysis/manufacturing-readiness" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test", "mpn": "TEST-001", "manufacturer": "Test", "category": "test"}, "quantity": 1}], "connections": []}'
echo -e "\n"

echo "=== Test Complete ==="

