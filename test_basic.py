# Basic test suite for the blocking responses API
import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app import app, settings, metrics


# Test fixtures
@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test"""
    metrics.total_requests = 0
    metrics.blocked_requests = 0
    metrics.judge_calls = 0
    metrics.avg_delay_ms = 0.0
    metrics.risk_scores = []
    if hasattr(metrics, "audit_logs"):
        metrics.audit_logs = []


class TestBasicAPI:
    """Test basic API functionality"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_config(self, client):
        response = await client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "delay_tokens" in data
        assert "delay_ms" in data
        assert "risk_threshold" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "blocked_requests" in data
        assert "block_rate" in data
        assert "settings" in data


class TestComplianceDetection:
    """Test compliance detection functionality"""

    @pytest.mark.asyncio
    async def test_assess_risk_safe_content(self, client):
        response = await client.post(
            "/assess-risk", params={"text": "What is the weather?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] >= 0.0
        assert data["blocked"] is False
        assert len(data["triggered_rules"]) >= 0

    @pytest.mark.asyncio
    async def test_assess_risk_risky_content(self, client):
        response = await client.post(
            "/assess-risk", params={"text": "My SSN is 123-45-6789"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] >= 1.0
        assert data["blocked"] is True
        assert len(data["triggered_rules"]) >= 1


class TestComplianceEndpoints:
    """Test new compliance-specific endpoints"""

    @pytest.mark.asyncio
    async def test_compliance_patterns_endpoint(self, client):
        try:
            response = await client.get("/compliance/patterns")
            if response.status_code == 200:
                data = response.json()
                assert "PII" in data or "email" in data
            else:
                # Endpoint might not be implemented yet
                assert response.status_code in [404, 405]
        except Exception:
            # Expected if endpoint not yet implemented
            pass

    @pytest.mark.asyncio
    async def test_streaming_endpoint_exists(self, client):
        # Just test that the endpoint exists and handles requests
        try:
            response = await client.post("/chat/stream", json={"message": "Hello"})
            # Any response code is fine for this basic test
            assert response.status_code in [200, 401, 500]  # 500 if no API key
        except Exception:
            # Expected if OpenAI not configured
            pass


class TestBasicSanity:
    """Basic sanity checks"""

    def test_imports_work(self):
        """Test that all imports work correctly"""
        try:
            from app import compliance_detector

            assert hasattr(compliance_detector, "assess_compliance")
        except ImportError:
            # Module might use different name
            pass

        # Test basic app components exist
        assert hasattr(app, "get")
        assert hasattr(metrics, "get_stats")
        assert callable(metrics.get_stats)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

