"""
Comprehensive endpoint tests for PCB Design API
Tests all analysis endpoints to ensure they're accessible and functional
"""

import pytest
import requests
import json
from typing import Dict, Any

# Backend URL - update this for your deployment
BACKEND_URL = "https://web-backend-24f1.up.railway.app"

# Test data
TEST_PART = {
    "id": "test-part-001",
    "mpn": "TEST-001",
    "manufacturer": "Test Manufacturer",
    "category": "test",
    "cost_estimate": 1.0,
    "supply_voltage_range": {"min": 3.0, "max": 5.0, "nominal": 3.3},
    "interface_type": ["I2C"],
    "operating_temp_range": {"min": -40, "max": 85}
}

TEST_BOM_ITEM = {
    "part_data": TEST_PART,
    "quantity": 1
}

TEST_CONNECTION = {
    "net_name": "VCC",
    "components": ["part1", "part2"],
    "pins": ["VCC", "VDD"]
}


class TestHealthEndpoints:
    """Test health and diagnostic endpoints."""
    
    def test_health_endpoint(self):
        """Test /health endpoint returns 200."""
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✓ Health check: {data}")
    
    def test_routes_endpoint(self):
        """Test /api/v1/routes endpoint returns 200."""
        response = requests.get(f"{BACKEND_URL}/api/v1/routes", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert isinstance(data.get("routes"), list)
        assert data.get("analysis_routes_count", 0) >= 0
        print(f"✓ Routes endpoint: {data['analysis_routes_count']} analysis routes, {data['total_routes']} total routes")


class TestAnalysisEndpoints:
    """Test all analysis endpoints."""
    
    def test_analysis_test_endpoint(self):
        """Test /api/v1/analysis/test endpoint."""
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/test",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("analysis_routes_count", 0) >= 0
        assert isinstance(data.get("routes"), list)
        print(f"✓ Test endpoint: {data['analysis_routes_count']} analysis routes exposed")
    
    def test_cost_analysis_endpoint(self):
        """Test /api/v1/analysis/cost endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/cost",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_cost" in data or "cost_breakdown" in data
        print(f"✓ Cost analysis: {data}")
    
    def test_supply_chain_analysis_endpoint(self):
        """Test /api/v1/analysis/supply-chain endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/supply-chain",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "risks" in data or "suppliers" in data or "lead_times" in data
        print(f"✓ Supply chain analysis: {data}")
    
    def test_power_analysis_endpoint(self):
        """Test /api/v1/analysis/power endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "connections": [TEST_CONNECTION],
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/power",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_power_watts" in data or "power_rails" in data
        print(f"✓ Power analysis: {data}")
    
    def test_thermal_analysis_endpoint(self):
        """Test /api/v1/analysis/thermal endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "connections": [TEST_CONNECTION],
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/thermal",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "thermal_issues" in data or "temperature_estimates" in data
        print(f"✓ Thermal analysis: {data}")
    
    def test_signal_integrity_analysis_endpoint(self):
        """Test /api/v1/analysis/signal-integrity endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "connections": [TEST_CONNECTION],
            "pcb_thickness_mm": 1.6,
            "trace_width_mils": 5,
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/signal-integrity",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "signal_issues" in data or "impedance" in data or "crosstalk" in data
        print(f"✓ Signal integrity analysis: {data}")
    
    def test_manufacturing_readiness_endpoint(self):
        """Test /api/v1/analysis/manufacturing-readiness endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "connections": [TEST_CONNECTION],
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/manufacturing-readiness",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "readiness_score" in data or "issues" in data or "recommendations" in data
        print(f"✓ Manufacturing readiness: {data}")
    
    def test_validation_endpoint(self):
        """Test /api/v1/analysis/validation endpoint."""
        payload = {
            "bom_items": [TEST_BOM_ITEM],
            "connections": [TEST_CONNECTION],
            "constraints": {},
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analysis/validation",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "summary" in data or "errors" in data or "warnings" in data
        print(f"✓ Design validation: {data}")


class TestComponentAnalysis:
    """Test component analysis SSE endpoint."""
    
    def test_component_analysis_endpoint(self):
        """Test /mcp/component-analysis endpoint."""
        payload = {
            "query": "Create a simple IoT sensor board",
            "provider": "xai"
        }
        response = requests.post(
            f"{BACKEND_URL}/mcp/component-analysis",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60,
            stream=True
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        # Check that it's SSE format
        assert "text/event-stream" in response.headers.get("content-type", "").lower()
        print("✓ Component analysis SSE endpoint working")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Endpoint Tests")
    print("=" * 60)
    
    # Run health tests
    print("\n[1] Testing Health Endpoints...")
    health_tests = TestHealthEndpoints()
    try:
        health_tests.test_health_endpoint()
        health_tests.test_routes_endpoint()
    except Exception as e:
        print(f"✗ Health tests failed: {e}")
    
    # Run analysis tests
    print("\n[2] Testing Analysis Endpoints...")
    analysis_tests = TestAnalysisEndpoints()
    test_methods = [
        analysis_tests.test_analysis_test_endpoint,
        analysis_tests.test_cost_analysis_endpoint,
        analysis_tests.test_supply_chain_analysis_endpoint,
        analysis_tests.test_power_analysis_endpoint,
        analysis_tests.test_thermal_analysis_endpoint,
        analysis_tests.test_signal_integrity_analysis_endpoint,
        analysis_tests.test_manufacturing_readiness_endpoint,
        analysis_tests.test_validation_endpoint,
    ]
    
    passed = 0
    failed = 0
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
        except Exception as e:
            print(f"✗ {test_method.__name__} failed: {e}")
            failed += 1
    
    print(f"\n[3] Testing Component Analysis...")
    try:
        analysis_tests.test_component_analysis_endpoint()
        passed += 1
    except Exception as e:
        print(f"✗ Component analysis test failed: {e}")
        failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

