# pip install pytest pytest-asyncio httpx
import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app import app, settings, metrics, risk_patterns, llm_judge

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

class TestRiskPatterns:
    """Test risk pattern detection"""
    
    def test_email_detection(self):
        assessment = risk_patterns.assess_risk("Contact me at john.doe@example.com")
        assert assessment.score == 0.5
        assert len(assessment.triggered_rules) == 1
        assert "email" in assessment.triggered_rules[0]
        assert not assessment.blocked  # Below default threshold
    
    def test_ssn_detection(self):
        assessment = risk_patterns.assess_risk("My SSN is 123-45-6789")
        assert assessment.score == 1.0
        assert len(assessment.triggered_rules) == 1
        assert "ssn" in assessment.triggered_rules[0]
        assert assessment.blocked  # At default threshold
    
    def test_credit_card_detection(self):
        assessment = risk_patterns.assess_risk("Card number: 1234 5678 9012 3456")
        assert assessment.score == 1.0
        assert len(assessment.triggered_rules) == 1
        assert "credit_card" in assessment.triggered_rules[0]
        assert assessment.blocked
    
    def test_phone_detection(self):
        assessment = risk_patterns.assess_risk("Call me at (555) 123-4567")
        assert assessment.score == 0.3
        assert len(assessment.triggered_rules) == 1
        assert "phone" in assessment.triggered_rules[0]
        assert not assessment.blocked
    
    def test_secrets_detection(self):
        assessment = risk_patterns.assess_risk("My password is secret123")
        assert assessment.score == 0.8
        assert len(assessment.triggered_rules) == 1
        assert "secrets" in assessment.triggered_rules[0]
        assert not assessment.blocked  # Below default threshold
    
    def test_harmful_content_detection(self):
        assessment = risk_patterns.assess_risk("I want to kill this bug")
        assert assessment.score == 1.5
        assert len(assessment.triggered_rules) == 1
        assert "harmful_content" in assessment.triggered_rules[0]
        assert assessment.blocked
    
    def test_multiple_patterns(self):
        text = "Email me at test@example.com or call (555) 123-4567 with your password"
        assessment = risk_patterns.assess_risk(text)
        assert assessment.score == 1.6  # 0.5 + 0.3 + 0.8
        assert len(assessment.triggered_rules) == 3
        assert assessment.blocked
    
    def test_safe_content(self):
        assessment = risk_patterns.assess_risk("What is the weather today?")
        assert assessment.score == 0.0
        assert len(assessment.triggered_rules) == 0
        assert not assessment.blocked
    
    def test_snippet_truncation(self):
        long_text = "a" * 150 + "test@example.com"
        assessment = risk_patterns.assess_risk(long_text)
        assert len(assessment.snippet) == 103  # 100 + "..."
        assert assessment.snippet.endswith("...")

class TestLLMJudge:
    """Test LLM judge functionality"""
    
    @patch('app.llm_judge.chain.ainvoke')
    async def test_judge_risky_content(self, mock_invoke):
        mock_invoke.return_value = "RISKY"
        
        result = await llm_judge.is_risky("Some risky content")
        assert result is True
        mock_invoke.assert_called_once()
    
    @patch('app.llm_judge.chain.ainvoke')
    async def test_judge_safe_content(self, mock_invoke):
        mock_invoke.return_value = "SAFE"
        
        result = await llm_judge.is_risky("Safe content")
        assert result is False
        mock_invoke.assert_called_once()
    
    @patch('app.llm_judge.chain.ainvoke')
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
        response = await client.post("/assess-risk", params={"text": "My SSN is 123-45-6789"})
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1.0
        assert data["blocked"] is True
        assert len(data["triggered_rules"]) == 1
    
    @pytest.mark.asyncio
    async def test_assess_risk_safe_content(self, client):
        response = await client.post("/assess-risk", params={"text": "What is the weather?"})
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0.0
        assert data["blocked"] is False
        assert len(data["triggered_rules"]) == 0

class TestChatStreaming:
    """Test chat streaming functionality"""
    
    @pytest.mark.asyncio
    @patch('app.settings.openai_api_key', 'test-key')
    @patch('app.ChatOpenAI')
    async def test_safe_chat_stream(self, mock_openai, client):
        # Mock the LangChain chain
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(["Hello ", "there! ", "How ", "can ", "I ", "help?"])
        
        mock_llm = AsyncMock()
        mock_openai.return_value = mock_llm
        
        with patch('app.chain', mock_chain):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_chat_stream_no_api_key(self, client):
        with patch('app.settings.openai_api_key', ''):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)
            assert response.status_code == 500
            assert "OpenAI API key not configured" in response.json()["detail"]
    
    @pytest.mark.asyncio
    @patch('app.settings.openai_api_key', 'test-key')
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
    @patch('app.settings.openai_api_key', 'test-key')
    async def test_legacy_get_endpoint(self, client):
        with patch('app.ChatOpenAI'):
            response = await client.get("/chat/stream?q=Hello")
            assert response.status_code == 200

class TestStreamBlocking:
    """Test stream blocking functionality"""
    
    @pytest.mark.asyncio
    @patch('app.settings.openai_api_key', 'test-key')
    @patch('app.ChatOpenAI')
    async def test_blocked_stream_ssn(self, mock_openai, client):
        # Mock a stream that includes an SSN
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(["My SSN is ", "123-45-", "6789", " please help"])
        
        with patch('app.chain', mock_chain):
            request_data = {"message": "What's your SSN?"}
            response = await client.post("/chat/stream", json=request_data)
            
            # Collect the stream response
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
            
            content_str = content.decode()
            assert "[BLOCKED]" in content_str
            assert "I notice this response might contain personal information" in content_str
            
            # Check metrics were updated
            stats = metrics.get_stats()
            assert stats["blocked_requests"] == 1
    
    @pytest.mark.asyncio
    @patch('app.settings.openai_api_key', 'test-key')
    @patch('app.ChatOpenAI')
    async def test_stream_with_custom_threshold(self, mock_openai, client):
        # Test with higher threshold that shouldn't block email
        mock_chain = AsyncMock()
        mock_chain.astream.return_value = iter(["Contact me at ", "test@", "example.com"])
        
        with patch('app.chain', mock_chain):
            request_data = {
                "message": "What's your email?",
                "risk_threshold": 2.0  # Higher than email score (0.5)
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
            system_prompt="Custom prompt"
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
        assert template == "I notice this response might contain personal information. Let me provide a general answer instead: "
    
    def test_credentials_template(self):
        from app import get_safe_template
        
        rules = ["secrets: Potential secret/credential detected"]
        template = get_safe_template(rules)
        assert template == "I can't share information that might contain credentials or secrets. Here's a safer approach: "
    
    def test_harmful_template(self):
        from app import get_safe_template
        
        rules = ["harmful_content: Potentially harmful content detected"]
        template = get_safe_template(rules)
        assert template == "I can't provide that type of content. Let me offer helpful information instead: "
    
    def test_general_template(self):
        from app import get_safe_template
        
        rules = ["unknown: Some other rule"]
        template = get_safe_template(rules)
        assert template == "Let me rephrase to keep this safe and compliant: "

class TestMetrics:
    """Test metrics tracking"""
    
    def test_record_request(self):
        metrics.record_request(blocked=False, delay_ms=100, risk_score=0.3)
        stats = metrics.get_stats()
        
        assert stats["total_requests"] == 1
        assert stats["blocked_requests"] == 0
        assert stats["block_rate"] == 0.0
        assert stats["avg_delay_ms"] == 100.0
        assert stats["avg_risk_score"] == 0.3
    
    def test_record_blocked_request(self):
        metrics.record_request(blocked=True, delay_ms=150, risk_score=1.2)
        stats = metrics.get_stats()
        
        assert stats["blocked_requests"] == 1
        assert stats["block_rate"] == 1.0
        assert stats["avg_risk_score"] == 1.2
    
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
    @patch('app.settings.openai_api_key', 'test-key')
    @patch('app.ChatOpenAI')
    async def test_llm_error_handling(self, mock_openai, client):
        # Mock a chain that raises an exception
        mock_chain = AsyncMock()
        mock_chain.astream.side_effect = Exception("API Error")
        
        with patch('app.chain', mock_chain):
            request_data = {"message": "Hello"}
            response = await client.post("/chat/stream", json=request_data)
            
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
            
            content_str = content.decode()
            assert "Error: API Error" in content_str
    
    @pytest.mark.asyncio
    @patch('app.settings.openai_api_key', 'test-key')
    @patch('app.llm_judge.is_risky')
    async def test_judge_error_in_stream(self, mock_judge, client):
        # Mock judge that raises an exception
        mock_judge.side_effect = Exception("Judge Error")
        
        with patch('app.ChatOpenAI'):
            request_data = {"message": "My password is secret123"}  # Should trigger judge
            response = await client.post("/chat/stream", json=request_data)
            
            # Should still work despite judge error
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])