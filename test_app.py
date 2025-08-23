# pip install pytest pytest-asyncio httpx
import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app import app, settings, pattern_detector, presidio_detector, metrics


# Test fixtures
@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://test")


# Metrics system is not implemented in current version
# @pytest.fixture(autouse=True)
# def reset_metrics():
#     """Reset metrics before each test"""
#     pass


class TestComplianceDetection:
    """Test enhanced compliance detection with Presidio"""

    @patch("app.compliance_detector.presidio_analyzer")
    def test_email_detection_presidio(self, mock_analyzer):
        # Mock Presidio analyzer
        mock_result = MagicMock()
        mock_result.entity_type = "EMAIL_ADDRESS"
        mock_result.score = 0.9
        mock_result.start = 11
        mock_result.end = 30
        mock_analyzer.analyze.return_value = [mock_result]

        assessment = compliance_detector.assess_compliance(
            "Contact me at john.doe@example.com", threshold=1.0
        )
        assert assessment.total_score >= 0.5
        assert len(assessment.detected_entities) >= 1
        assert not assessment.blocked  # Below threshold

    def test_email_detection_regex(self):
        assessment = compliance_detector.assess_compliance(
            "Contact me at john.doe@example.com", threshold=1.0
        )
        assert assessment.total_score >= 0.5
        assert len(assessment.triggered_patterns) >= 1
        assert any("email" in pattern for pattern in assessment.triggered_patterns)
        assert not assessment.blocked  # Below default threshold

    @patch("app.compliance_detector.presidio_analyzer")
    def test_ssn_detection_presidio(self, mock_analyzer):
        mock_result = MagicMock()
        mock_result.entity_type = "US_SSN"
        mock_result.score = 0.95
        mock_result.start = 10
        mock_result.end = 21
        mock_analyzer.analyze.return_value = [mock_result]

        assessment = compliance_detector.assess_compliance(
            "My SSN is 123-45-6789", threshold=1.0
        )
        assert assessment.total_score >= 1.0
        assert len(assessment.detected_entities) >= 1
        assert assessment.blocked

    def test_ssn_detection_regex(self):
        assessment = compliance_detector.assess_compliance(
            "My SSN is 123-45-6789", threshold=1.0
        )
        assert assessment.total_score >= 1.0
        assert len(assessment.triggered_patterns) >= 1
        assert any("ssn" in pattern for pattern in assessment.triggered_patterns)
        assert assessment.blocked

    @patch("app.compliance_detector.presidio_analyzer")
    def test_credit_card_detection_presidio(self, mock_analyzer):
        mock_result = MagicMock()
        mock_result.entity_type = "CREDIT_CARD"
        mock_result.score = 0.9
        mock_result.start = 14
        mock_result.end = 33
        mock_analyzer.analyze.return_value = [mock_result]

        assessment = compliance_detector.assess_compliance(
            "Card number: 1234 5678 9012 3456", threshold=1.0
        )
        assert assessment.total_score >= 1.0
        assert len(assessment.detected_entities) >= 1
        assert assessment.blocked

    def test_phone_detection_regex(self):
        assessment = compliance_detector.assess_compliance(
            "Call me at (555) 123-4567", threshold=1.0
        )
        assert assessment.total_score >= 0.3
        assert len(assessment.triggered_patterns) >= 1
        assert any("phone" in pattern for pattern in assessment.triggered_patterns)
        assert not assessment.blocked  # Below threshold

    def test_hipaa_phi_detection(self):
        phi_text = "Patient John Doe, DOB: 01/15/1980, diagnosed with diabetes"
        assessment = compliance_detector.assess_compliance(
            phi_text, threshold=0.8, compliance_type="HIPAA"
        )
        assert assessment.total_score >= 0.8
        assert assessment.blocked
        assert assessment.compliance_type == "HIPAA"

    def test_pci_dss_detection(self):
        pci_text = "Customer card: 4532 1234 5678 9012, CVV: 123, exp: 12/25"
        assessment = compliance_detector.assess_compliance(
            pci_text, threshold=0.8, compliance_type="PCI_DSS"
        )
        assert assessment.total_score >= 1.5  # Multiple PCI violations
        assert assessment.blocked
        assert assessment.compliance_type == "PCI_DSS"

    def test_gdpr_pii_detection(self):
        pii_text = "Name: María González, Email: maria@example.com, IP: 192.168.1.1"
        assessment = compliance_detector.assess_compliance(
            pii_text, threshold=0.8, compliance_type="GDPR"
        )
        assert assessment.total_score >= 1.0
        assert assessment.blocked
        assert assessment.compliance_type == "GDPR"

    def test_multiple_compliance_violations(self):
        text = "Patient: John Doe, SSN: 123-45-6789, Card: 4532123456789012, Email: john@hospital.com"
        assessment = compliance_detector.assess_compliance(text, threshold=1.0)
        assert assessment.total_score >= 2.0  # Multiple high-risk violations
        assert len(assessment.triggered_patterns) >= 3
        assert assessment.blocked

    def test_safe_content(self):
        assessment = compliance_detector.assess_compliance(
            "What is the weather today?", threshold=1.0
        )
        assert assessment.total_score == 0.0
        assert len(assessment.triggered_patterns) == 0
        assert len(assessment.detected_entities) == 0
        assert not assessment.blocked

    def test_snippet_truncation(self):
        long_text = "a" * 150 + "test@example.com"
        assessment = compliance_detector.assess_compliance(long_text, threshold=1.0)
        assert len(assessment.text_snippet) <= 103  # Truncated with ...
        if len(assessment.text_snippet) == 103:
            assert assessment.text_snippet.endswith("...")


class TestSSEStreaming:
    """Test Server-Sent Events streaming functionality"""

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_sse_format(self, mock_openai, client):
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(["Hello ", "world!"])

        with patch("app.chain", mock_chain):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)

            assert response.status_code == 200
            assert (
                response.headers["content-type"] == "text/event-stream; charset=utf-8"
            )
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_sse_heartbeat(self, mock_openai, client):
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter([])  # Empty stream to test heartbeat

        with patch("app.chain", mock_chain):
            request_data = {"message": "Hello", "delay_ms": 100}
            response = await client.post("/chat/stream", json=request_data)

            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
                if b"event: heartbeat" in content:
                    break  # Found heartbeat

            content_str = content.decode()
            assert "event: heartbeat" in content_str
            assert "data: ping" in content_str

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_sse_compliance_blocking(self, mock_openai, client):
        # Mock stream with SSN that should be blocked
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(["Your SSN is ", "123-45-", "6789"])

        with patch("app.chain", mock_chain):
            request_data = {"message": "What's my SSN?"}
            response = await client.post("/chat/stream", json=request_data)

            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk

            content_str = content.decode()
            assert "event: blocked" in content_str
            assert (
                "PII/PHI detected" in content_str
                or "compliance violation" in content_str
            )


class TestAuditLogging:
    """Test audit logging and compliance tracking"""

    @pytest.mark.asyncio
    async def test_audit_log_creation(self, client):
        response = await client.post(
            "/assess-risk", params={"text": "My SSN is 123-45-6789"}
        )
        assert response.status_code == 200

        # Check that audit log was created
        audit_logs = metrics.get_audit_logs()
        assert len(audit_logs) > 0

        latest_log = audit_logs[-1]
        assert latest_log["event_type"] == "risk_assessment"
        assert latest_log["blocked"] is True
        assert "user_agent" in latest_log
        assert "timestamp" in latest_log

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_streaming_audit_log(self, mock_openai, client):
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(["Safe response"])

        with patch("app.chain", mock_chain):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)

            # Consume the stream
            async for chunk in response.aiter_bytes():
                pass

        # Check audit log
        audit_logs = metrics.get_audit_logs()
        stream_logs = [log for log in audit_logs if log["event_type"] == "stream_chat"]
        assert len(stream_logs) > 0

        latest_log = stream_logs[-1]
        assert "session_id" in latest_log
        assert "tokens_processed" in latest_log
        assert "compliance_checks" in latest_log

    @pytest.mark.asyncio
    async def test_compliance_endpoint_audit(self, client):
        response = await client.get("/compliance/audit-logs")
        assert response.status_code == 200

        data = response.json()
        assert "logs" in data
        assert "total_count" in data
        assert "filtered_count" in data


class TestComplianceEndpoints:
    """Test new compliance-specific endpoints"""

    @pytest.mark.asyncio
    async def test_compliance_patterns_endpoint(self, client):
        response = await client.get("/compliance/patterns")
        assert response.status_code == 200

        data = response.json()
        assert "PII" in data
        assert "PHI" in data
        assert "PCI" in data
        assert "email" in data["PII"]
        assert "ssn" in data["PII"]
        assert "credit_card" in data["PCI"]

    @pytest.mark.asyncio
    async def test_compliance_types_endpoint(self, client):
        response = await client.get("/compliance/types")
        assert response.status_code == 200

        data = response.json()
        assert "HIPAA" in data
        assert "PCI_DSS" in data
        assert "GDPR" in data
        assert "CCPA" in data

        # Check HIPAA details
        assert data["HIPAA"]["description"]
        assert data["HIPAA"]["default_threshold"] == 0.7

    @pytest.mark.asyncio
    async def test_safe_rewrite_endpoint(self, client):
        request_data = {
            "text": "Contact John Doe at john.doe@company.com or call (555) 123-4567",
            "compliance_type": "PII",
            "rewrite_style": "professional",
        }

        response = await client.post("/compliance/safe-rewrite", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "original_text" in data
        assert "rewritten_text" in data
        assert "detected_violations" in data
        assert "rewrite_applied" in data

        # Should not contain the original PII
        assert "john.doe@company.com" not in data["rewritten_text"]
        assert "(555) 123-4567" not in data["rewritten_text"]


class TestLLMJudge:
    """Test LLM judge functionality"""

    @patch("app.llm_judge.chain.ainvoke")
    async def test_judge_risky_content(self, mock_invoke):
        mock_invoke.return_value = "RISKY"

        result = await llm_judge.is_risky("Some risky content")
        assert result is True
        mock_invoke.assert_called_once()

    @patch("app.llm_judge.chain.ainvoke")
    async def test_judge_safe_content(self, mock_invoke):
        mock_invoke.return_value = "SAFE"

        result = await llm_judge.is_risky("Safe content")
        assert result is False
        mock_invoke.assert_called_once()

    @patch("app.llm_judge.chain.ainvoke")
    async def test_judge_error_handling(self, mock_invoke):
        mock_invoke.side_effect = Exception("API Error")

        result = await llm_judge.is_risky("Some content")
        assert result is True  # Fail safe

    def test_judge_disabled(self):
        # Test when judge is disabled
        original_enabled = llm_judge.enabled
        llm_judge.enabled = False

        async def test():
            result = await llm_judge.is_risky("Any content")
            assert result is False

        import asyncio

        asyncio.run(test())

        llm_judge.enabled = original_enabled


class TestAPI:
    """Test API endpoints"""

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
        assert data["delay_tokens"] == settings.delay_tokens

    @pytest.mark.asyncio
    async def test_get_patterns(self, client):
        response = await client.get("/patterns")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "ssn" in data
        assert data["email"]["score"] == 0.5
        assert data["ssn"]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "blocked_requests" in data
        assert "block_rate" in data
        assert "settings" in data

    @pytest.mark.asyncio
    async def test_assess_risk_endpoint(self, client):
        response = await client.post(
            "/assess-risk", params={"text": "My SSN is 123-45-6789"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1.0
        assert data["blocked"] is True
        assert len(data["triggered_rules"]) == 1

    @pytest.mark.asyncio
    async def test_assess_risk_safe_content(self, client):
        response = await client.post(
            "/assess-risk", params={"text": "What is the weather?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0.0
        assert data["blocked"] is False
        assert len(data["triggered_rules"]) == 0


class TestChatStreaming:
    """Test chat streaming functionality"""

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_safe_chat_stream(self, mock_openai, client):
        # Mock the LangChain chain
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(
            ["Hello ", "there! ", "How ", "can ", "I ", "help?"]
        )

        mock_llm = AsyncMock()
        mock_openai.return_value = mock_llm

        with patch("app.chain", mock_chain):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)
            assert response.status_code == 200
            assert (
                response.headers["content-type"] == "text/event-stream; charset=utf-8"
            )

    @pytest.mark.asyncio
    async def test_chat_stream_no_api_key(self, client):
        with patch("app.settings.openai_api_key", ""):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)
            assert response.status_code == 500
            assert "OpenAI API key not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    async def test_chat_stream_validation(self, client):
        # Test empty message
        request_data = {"message": ""}
        response = await client.post("/chat/stream", json=request_data)
        assert response.status_code == 422

        # Test message too long
        request_data = {"message": "a" * 10001}
        response = await client.post("/chat/stream", json=request_data)
        assert response.status_code == 422

        # Test invalid parameters
        request_data = {"message": "Hello", "delay_tokens": 200}  # Too high
        response = await client.post("/chat/stream", json=request_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    async def test_legacy_get_endpoint(self, client):
        with patch("app.ChatOpenAI"):
            response = await client.get("/chat/stream?q=Hello")
            assert response.status_code == 200


class TestStreamBlocking:
    """Test stream blocking functionality"""

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_blocked_stream_ssn(self, mock_openai, client):
        # Mock a stream that includes an SSN
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(
            ["My SSN is ", "123-45-", "6789", " please help"]
        )

        with patch("app.chain", mock_chain):
            request_data = {"message": "What's your SSN?"}
            response = await client.post("/chat/stream", json=request_data)

            # Collect the stream response
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk

            content_str = content.decode()
            assert "[BLOCKED]" in content_str
            assert (
                "I notice this response might contain personal information"
                in content_str
            )

            # Check metrics were updated
            stats = metrics.get_stats()
            assert stats["blocked_requests"] == 1

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_stream_with_custom_threshold(self, mock_openai, client):
        # Test with higher threshold that shouldn't block email
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(
            ["Contact me at ", "test@", "example.com"]
        )

        with patch("app.chain", mock_chain):
            request_data = {
                "message": "What's your email?",
                "risk_threshold": 2.0,  # Higher than email score (0.5)
            }
            response = await client.post("/chat/stream", json=request_data)

            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk

            content_str = content.decode()
            assert "[BLOCKED]" not in content_str
            assert "[DONE]" in content_str


class TestConfiguration:
    """Test configuration and customization"""

    def test_get_stream_config_defaults(self):
        from app import get_stream_config, ChatRequest

        req = ChatRequest(message="Hello")
        config = get_stream_config(req)

        assert config["delay_tokens"] == settings.delay_tokens
        assert config["delay_ms"] == settings.delay_ms
        assert config["risk_threshold"] == settings.risk_threshold
        assert config["model"] == settings.default_model

    def test_get_stream_config_custom(self):
        from app import get_stream_config, ChatRequest

        req = ChatRequest(
            message="Hello",
            delay_tokens=30,
            delay_ms=500,
            risk_threshold=1.5,
            model="gpt-4",
            system_prompt="Custom prompt",
        )
        config = get_stream_config(req)

        assert config["delay_tokens"] == 30
        assert config["delay_ms"] == 500
        assert config["risk_threshold"] == 1.5
        assert config["model"] == "gpt-4"
        assert config["system_prompt"] == "Custom prompt"


class TestSafeTemplates:
    """Test safe response templates"""

    def test_pii_template(self):
        from app import get_safe_template

        rules = ["email: Email address detected", "phone: Phone number detected"]
        template = get_safe_template(rules)
        assert (
            template
            == "I notice this response might contain personal information. Let me provide a general answer instead: "
        )

    def test_credentials_template(self):
        from app import get_safe_template

        rules = ["secrets: Potential secret/credential detected"]
        template = get_safe_template(rules)
        assert (
            template
            == "I can't share information that might contain credentials or secrets. Here's a safer approach: "
        )

    def test_harmful_template(self):
        from app import get_safe_template

        rules = ["harmful_content: Potentially harmful content detected"]
        template = get_safe_template(rules)
        assert (
            template
            == "I can't provide that type of content. Let me offer helpful information instead: "
        )

    def test_general_template(self):
        from app import get_safe_template

        rules = ["unknown: Some other rule"]
        template = get_safe_template(rules)
        assert template == "Let me rephrase to keep this safe and compliant: "


class TestMetrics:
    """Test metrics tracking"""

    def test_record_request(self):
        # Reset metrics first
        initial_total = metrics.total_requests
        initial_blocked = metrics.blocked_requests

        metrics.record_request(blocked=False, delay_ms=100, risk_score=0.3)

        assert metrics.total_requests == initial_total + 1
        assert metrics.blocked_requests == initial_blocked
        assert metrics.avg_risk_score > 0.0  # Should have some average now
        assert metrics.avg_processing_time > 0.0  # Should have some processing time

    def test_record_blocked_request(self):
        initial_total = metrics.total_requests
        initial_blocked = metrics.blocked_requests

        metrics.record_request(blocked=True, delay_ms=150, risk_score=1.2)

        assert metrics.total_requests == initial_total + 1
        assert metrics.blocked_requests == initial_blocked + 1
        assert metrics.block_rate > 0.0

    def test_record_judge_call(self):
        initial_calls = metrics.judge_calls
        metrics.record_judge_call()
        assert metrics.judge_calls == initial_calls + 1

    def test_risk_scores_limit(self):
        # Test that risk scores list doesn't grow beyond 1000
        for i in range(1100):
            metrics.record_request(risk_score=i)

        assert len(metrics.risk_scores) == 1000
        assert metrics.risk_scores[0] == 100  # First 100 should be dropped


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.ChatOpenAI")
    async def test_llm_error_handling(self, mock_openai, client):
        # Mock a chain that raises an exception
        mock_chain = AsyncMock()
        mock_chain.astream.side_effect = Exception("API Error")

        with patch("app.chain", mock_chain):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)

            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk

            content_str = content.decode()
            assert "Error: API Error" in content_str

    @pytest.mark.asyncio
    @patch("app.settings.openai_api_key", "test-key")
    @patch("app.llm_judge.is_risky")
    async def test_judge_error_in_stream(self, mock_judge, client):
        # Mock judge that raises an exception
        mock_judge.side_effect = Exception("Judge Error")

        with patch("app.ChatOpenAI"):
            request_data = {
                "message": "My password is secret123"
            }  # Should trigger judge
            response = await client.post("/chat/stream", json=request_data)

            # Should still work despite judge error
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

