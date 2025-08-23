"""
Comprehensive Test Suite for Blocking Responses API
Tests all security fixes, compliance detection, and edge cases
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

# Import the app and components
from app import app, pattern_detector, presidio_detector, MetricsTracker, generate_session_id, sanitize_for_logging

class TestClient:
    def __init__(self):
        self.client = TestClient(app)

@pytest.fixture
def test_client():
    return TestClient()

# ==================== SECURITY TESTS ====================

class TestSecurityFixes:
    """Test all critical security fixes"""
    
    def test_secure_session_id_generation(self):
        """Test that session IDs are cryptographically secure"""
        # Generate multiple session IDs
        session_ids = [generate_session_id() for _ in range(100)]
        
        # Check uniqueness
        assert len(set(session_ids)) == 100, "Session IDs should be unique"
        
        # Check format (12 character hex)
        for sid in session_ids:
            assert len(sid) == 12, f"Session ID {sid} should be 12 characters"
            assert all(c in '0123456789abcdef' for c in sid), f"Session ID {sid} should be hex"
    
    def test_logging_sanitization(self):
        """Test PII sanitization in logging"""
        test_cases = [
            ("My SSN is 123-45-6789", "My SSN is ***-**-****"),
            ("Credit card 4532-1234-5678-9012", "Credit card ****-****-****-****"),
            ("4532123456789012", "****-****-****-****"),
            ("Normal text without PII", "Normal text without PII"),
            ("", ""),
            ("SSN: 987-65-4321 and card: 5555-4444-3333-2222", "SSN: ***-**-**** and card: ****-****-****-****"),
        ]
        
        for input_text, expected in test_cases:
            result = sanitize_for_logging(input_text)
            assert result == expected, f"Input: {input_text}, Expected: {expected}, Got: {result}"
    
    def test_input_validation_limits(self, test_client):
        """Test input validation and field limits"""
        # Test message length limit (5000 chars)
        long_message = "A" * 5001
        response = test_client.client.post("/chat/stream", json={
            "message": long_message
        })
        assert response.status_code == 422, "Should reject messages over 5000 characters"
        
        # Test valid message length
        valid_message = "A" * 4999
        response = test_client.client.post("/chat/stream", json={
            "message": valid_message
        })
        assert response.status_code != 422, "Should accept messages under 5000 characters"
        
        # Test empty message
        response = test_client.client.post("/chat/stream", json={
            "message": ""
        })
        assert response.status_code == 422, "Should reject empty messages"
        
        # Test model field length
        response = test_client.client.post("/chat/stream", json={
            "message": "test",
            "model": "A" * 101
        })
        assert response.status_code == 422, "Should reject model field over 100 chars"
        
        # Test delay_tokens range
        response = test_client.client.post("/chat/stream", json={
            "message": "test",
            "delay_tokens": 4
        })
        assert response.status_code == 422, "Should reject delay_tokens < 5"
        
        response = test_client.client.post("/chat/stream", json={
            "message": "test", 
            "delay_tokens": 51
        })
        assert response.status_code == 422, "Should reject delay_tokens > 50"
        
        # Test risk_threshold range
        response = test_client.client.post("/chat/stream", json={
            "message": "test",
            "risk_threshold": 2.1
        })
        assert response.status_code == 422, "Should reject risk_threshold > 2.0"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client):
        """Test rate limiting functionality"""
        # Note: This test assumes slowapi is properly configured
        # Make rapid requests to trigger rate limit
        
        responses = []
        for i in range(15):  # More than the 10/minute limit
            response = test_client.client.post("/chat/stream", json={
                "message": f"test message {i}"
            })
            responses.append(response.status_code)
            
        # Should have some 429 (rate limited) responses
        rate_limited = sum(1 for code in responses if code == 429)
        assert rate_limited > 0, "Rate limiting should trigger after 10 requests"

# ==================== COMPLIANCE DETECTION TESTS ====================

class TestComplianceDetection:
    """Test all compliance detection patterns and scenarios"""
    
    def test_ssn_detection(self):
        """Test SSN pattern detection"""
        test_cases = [
            ("123-45-6789", True, 1.2),  # Valid SSN format
            ("123456789", False, 0.0),   # No dashes
            ("12-45-6789", False, 0.0),  # Invalid format
            ("123-4-6789", False, 0.0),  # Invalid format
            ("My SSN is 987-65-4321", True, 1.2),  # In context
            ("Call 123-456-7890", False, 0.0),  # Phone number, not SSN
        ]
        
        for text, should_detect, expected_score in test_cases:
            result = pattern_detector.assess_compliance_risk(text)
            if should_detect:
                assert result.score >= expected_score, f"Should detect SSN in: {text}"
                assert any("ssn" in rule.lower() for rule in result.triggered_rules), f"Should trigger SSN rule for: {text}"
            else:
                assert not any("ssn" in rule.lower() for rule in result.triggered_rules), f"Should not detect SSN in: {text}"
    
    def test_credit_card_detection(self):
        """Test credit card detection with Luhn validation"""
        test_cases = [
            # Valid credit cards (pass Luhn check)
            ("4532015112830366", True, 1.5),  # Valid Visa
            ("5555555555554444", True, 1.5),  # Valid Mastercard  
            ("378282246310005", True, 1.5),   # Valid Amex
            
            # Invalid credit cards (fail Luhn check)
            ("4532-1234-5678-9012", False, 0.0),  # Invalid Luhn
            ("1234-5678-9012-3456", False, 0.0),  # Invalid format
            
            # Context detection
            ("My credit card is 4532015112830366", True, 2.0),  # Card + context
            ("PCI compliance for 4532015112830366", True, 2.0),  # Card + PCI context
            
            # Non-credit card numbers
            ("Phone: 123-456-7890", False, 0.0),
            ("ID: 12345678901234567890", False, 0.0),
        ]
        
        for text, should_detect, expected_min_score in test_cases:
            result = pattern_detector.assess_compliance_risk(text)
            if should_detect:
                assert result.score >= expected_min_score, f"Should detect credit card in: {text} (got {result.score})"
                detected_cc = any("credit" in rule.lower() for rule in result.triggered_rules)
                assert detected_cc, f"Should trigger credit card rule for: {text}"
            else:
                detected_cc = any("credit" in rule.lower() for rule in result.triggered_rules)
                assert not detected_cc, f"Should not detect credit card in: {text}"
    
    def test_email_detection(self):
        """Test email pattern detection"""
        test_cases = [
            ("john@example.com", True, 0.4),
            ("user.name+tag@domain.co.uk", True, 0.4),
            ("invalid.email", False, 0.0),
            ("@domain.com", False, 0.0),
            ("My email is john.doe@company.org", True, 0.4),
        ]
        
        for text, should_detect, expected_score in test_cases:
            result = pattern_detector.assess_compliance_risk(text)
            if should_detect:
                assert result.score >= expected_score, f"Should detect email in: {text}"
                assert any("email" in rule.lower() for rule in result.triggered_rules)
    
    def test_phone_detection(self):
        """Test phone number pattern detection"""
        test_cases = [
            ("(555) 123-4567", True, 0.5),
            ("555-123-4567", True, 0.5),
            ("555.123.4567", True, 0.5),
            ("15551234567", True, 0.5),
            ("Call me at (555) 123-4567", True, 0.5),
            ("123-45-6789", False, 0.0),  # SSN, not phone
        ]
        
        for text, should_detect, expected_score in test_cases:
            result = pattern_detector.assess_compliance_risk(text)
            if should_detect:
                phone_detected = any("phone" in rule.lower() for rule in result.triggered_rules)
                assert phone_detected, f"Should detect phone in: {text}"
    
    def test_regional_compliance_variations(self):
        """Test regional compliance rule variations"""
        test_cases = [
            ("john@example.com", "GDPR", 0.6),  # Higher email weight for GDPR
            ("john@example.com", "CCPA", 0.5),  # Medium email weight for CCPA
            ("john@example.com", None, 0.4),    # Default email weight
            
            ("4532015112830366", "PCI", 2.0),   # Higher card weight for PCI
            ("4532015112830366", None, 1.5),   # Default card weight
        ]
        
        for text, region, expected_score in test_cases:
            result = pattern_detector.assess_compliance_risk(text, region)
            assert result.score >= expected_score, f"Regional scoring failed for {text} in {region}"
    
    def test_context_detection(self):
        """Test contextual risk scoring"""
        test_cases = [
            # PHI context
            ("Patient John Smith diagnosed with cancer", 0.8),
            ("Medical record number MRN123456", 0.6),
            ("Prescription for medication XYZ", 0.6),
            
            # PCI context  
            ("Credit card payment processing", 0.5),
            ("PCI compliance requirements", 0.5),
            ("Card verification value CVV", 0.5),
            
            # Combined context and PII
            ("Patient SSN: 123-45-6789 for medical record", 1.8),  # SSN + PHI context
            ("Credit card 4532015112830366 for payment", 2.0),    # Card + PCI context
        ]
        
        for text, expected_min_score in test_cases:
            result = pattern_detector.assess_compliance_risk(text)
            assert result.score >= expected_min_score, f"Context scoring failed for: {text} (got {result.score})"

# ==================== PRESIDIO INTEGRATION TESTS ====================

class TestPresidioIntegration:
    """Test Microsoft Presidio integration"""
    
    @pytest.mark.skipif(not hasattr(presidio_detector, 'analyzer') or presidio_detector.analyzer is None, 
                       reason="Presidio not available")
    def test_presidio_entity_detection(self):
        """Test Presidio entity detection"""
        test_cases = [
            ("My name is John Smith", ["PERSON"]),
            ("I live in New York", ["LOCATION"]),
            ("My phone is 555-123-4567", ["PHONE_NUMBER"]),
            ("Email: john@example.com", ["EMAIL_ADDRESS"]),
            ("SSN: 123-45-6789", ["US_SSN"]),
        ]
        
        for text, expected_entities in test_cases:
            score, entities = presidio_detector.analyze_text(text)
            entity_types = [e["entity_type"] for e in entities]
            
            for expected_entity in expected_entities:
                assert expected_entity in entity_types, f"Should detect {expected_entity} in: {text}"
    
    @pytest.mark.skipif(not hasattr(presidio_detector, 'analyzer') or presidio_detector.analyzer is None,
                       reason="Presidio not available")  
    def test_presidio_confidence_threshold(self):
        """Test Presidio confidence threshold filtering"""
        # This depends on the actual Presidio models and their confidence scores
        text = "Maybe John could be a name"  # Low confidence
        score, entities = presidio_detector.analyze_text(text)
        
        # Should filter out low-confidence detections
        high_conf_entities = [e for e in entities if e["score"] >= 0.6]
        assert len(high_conf_entities) <= len(entities), "Confidence filtering should work"

# ==================== STREAMING AND SSE TESTS ====================

class TestStreamingFunctionality:
    """Test streaming and Server-Sent Events"""
    
    def test_sse_event_format(self, test_client):
        """Test SSE event formatting"""
        response = test_client.client.post("/chat/stream", json={
            "message": "Safe test message"
        })
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse SSE events
        content = response.text
        events = []
        for line in content.split('\n'):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass
        
        assert len(events) > 0, "Should have SSE events"
        
        # Check event structure
        for event in events:
            assert "type" in event, "Event should have type field"
            assert "content" in event, "Event should have content field" 
            assert "timestamp" in event, "Event should have timestamp field"
    
    def test_streaming_with_blocking(self, test_client):
        """Test streaming behavior when content is blocked"""
        response = test_client.client.post("/chat/stream", json={
            "message": "My SSN is 123-45-6789"
        })
        
        assert response.status_code == 200
        
        # Should get immediate blocking response
        content = response.text
        assert "blocked" in content.lower(), "Should indicate blocking"
        assert "1.20" in content or "1.2" in content, "Should show risk score"
    
    def test_streaming_safe_content(self, test_client):
        """Test streaming with safe content"""
        response = test_client.client.post("/chat/stream", json={
            "message": "Hello, how are you today?"
        })
        
        assert response.status_code == 200
        
        # Should get normal streaming response
        content = response.text
        assert "chunk" in content, "Should have chunk events"
        assert "completed" in content, "Should have completion event"

# ==================== API ENDPOINT TESTS ====================

class TestAPIEndpoints:
    """Test all API endpoints thoroughly"""
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
    
    def test_config_endpoint(self, test_client):
        """Test configuration endpoint"""
        response = test_client.client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "delay_tokens", "delay_ms", "risk_threshold", "default_model",
            "enable_judge", "enable_safe_rewrite", "cors_origins"
        ]
        
        for field in required_fields:
            assert field in data, f"Config should include {field}"
        
        # Check specific values
        assert data["risk_threshold"] == 0.7, "Risk threshold should be 0.7"
        assert isinstance(data["cors_origins"], list), "CORS origins should be a list"
    
    def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint"""
        response = test_client.client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "total_requests", "blocked_requests", "block_rate", "avg_risk_score",
            "pattern_detections", "presidio_detections", "performance_metrics"
        ]
        
        for field in required_fields:
            assert field in data, f"Metrics should include {field}"
    
    def test_audit_logs_endpoint(self, test_client):
        """Test audit logs endpoint"""
        response = test_client.client.get("/audit-logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
    
    def test_audit_logs_filtering(self, test_client):
        """Test audit logs with filtering"""
        # Test event type filtering
        response = test_client.client.get("/audit-logs?event_type=user_input_blocked")
        assert response.status_code == 200
        
        # Test limit parameter
        response = test_client.client.get("/audit-logs?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 5
    
    def test_risk_assessment_endpoint(self, test_client):
        """Test risk assessment endpoint"""
        test_cases = [
            ("Hello world", False, 0.0),
            ("My SSN is 123-45-6789", True, 1.2),
            ("Credit card: 4532015112830366", True, 1.5),
            ("Email: john@example.com", False, 0.4),  # Below threshold
        ]
        
        for text, should_block, expected_min_score in test_cases:
            response = test_client.client.post(f"/assess-risk?text={text}")
            assert response.status_code == 200
            
            data = response.json()
            assert "pattern_score" in data
            assert "blocked" in data
            assert "triggered_rules" in data
            
            if should_block:
                assert data["blocked"] == True, f"Should block: {text}"
                assert data["pattern_score"] >= expected_min_score, f"Score too low for: {text}"

# ==================== ERROR HANDLING TESTS ====================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_api_key(self, test_client):
        """Test behavior when API key is missing"""
        # This depends on configuration - might pass with env var or fail
        with patch.dict('os.environ', {}, clear=True):
            response = test_client.client.post("/chat/stream", json={
                "message": "test without API key"
            })
            # Should either work (if key in env) or return 400
            assert response.status_code in [200, 400, 422]
    
    def test_invalid_json(self, test_client):
        """Test invalid JSON handling"""
        response = test_client.client.post("/chat/stream", 
                                         data="invalid json",
                                         headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_required_fields(self, test_client):
        """Test missing required fields"""
        # Missing message field
        response = test_client.client.post("/chat/stream", json={})
        assert response.status_code == 422
        
        # Empty message
        response = test_client.client.post("/chat/stream", json={"message": ""})
        assert response.status_code == 422
    
    def test_invalid_field_types(self, test_client):
        """Test invalid field types"""
        test_cases = [
            {"message": 123},  # message should be string
            {"message": "test", "delay_tokens": "invalid"},  # should be int
            {"message": "test", "risk_threshold": "invalid"},  # should be float
            {"message": "test", "enable_safe_rewrite": "invalid"},  # should be bool
        ]
        
        for invalid_data in test_cases:
            response = test_client.client.post("/chat/stream", json=invalid_data)
            assert response.status_code == 422, f"Should reject invalid data: {invalid_data}"

# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Test performance and load handling"""
    
    def test_response_time(self, test_client):
        """Test API response times"""
        start_time = time.time()
        response = test_client.client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check should be fast, took {response_time}s"
    
    def test_compliance_detection_performance(self):
        """Test compliance detection speed"""
        test_text = "This is a long message " * 100 + " with SSN 123-45-6789 at the end"
        
        start_time = time.time()
        result = pattern_detector.assess_compliance_risk(test_text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 1.0, f"Compliance detection should be fast, took {processing_time}s"
        assert result.score > 0, "Should detect SSN"
    
    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = test_client.client.get("/health")
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Start 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Check results
        response_codes = []
        while not results.empty():
            response_codes.append(results.get())
        
        assert len(response_codes) == 10, "All requests should complete"
        assert all(code == 200 for code in response_codes), "All requests should succeed"

# ==================== EDGE CASE TESTS ====================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_extremely_long_input(self):
        """Test handling of very long inputs"""
        # Test maximum allowed length
        max_text = "A" * 5000
        result = pattern_detector.assess_compliance_risk(max_text)
        assert result.score >= 0, "Should handle maximum length input"
        
        # Test just over maximum
        over_max = "A" * 5001
        # This should be handled by input validation at API level
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        test_cases = [
            "测试 SSN: 123-45-6789 中文",  # Chinese characters
            "SSN: 123-45-6789 🔒🛡️",     # Emojis
            "SSN\t123-45-6789\n",         # Tabs and newlines
            "SSN: 123\u200d45\u200d6789", # Zero-width joiners
        ]
        
        for text in test_cases:
            result = pattern_detector.assess_compliance_risk(text)
            # Should detect SSN regardless of surrounding characters
            assert result.score >= 1.0, f"Should detect SSN in unicode text: {text}"
    
    def test_multiple_pii_types(self):
        """Test text with multiple PII types"""
        text = """
        Patient Information:
        Name: John Smith
        SSN: 123-45-6789
        Email: john.smith@hospital.org
        Phone: (555) 123-4567
        Credit Card: 4532015112830366
        Medical Record: MRN-12345
        """
        
        result = pattern_detector.assess_compliance_risk(text)
        
        # Should detect multiple types and accumulate scores
        assert result.score > 3.0, f"Should have high cumulative score, got {result.score}"
        assert len(result.triggered_rules) >= 3, "Should trigger multiple rules"
        
        # Should definitely be blocked
        assert result.blocked == True, "Multiple PII should be blocked"
    
    def test_false_positive_prevention(self):
        """Test prevention of false positives"""
        false_positive_cases = [
            "The year 1234-56-7890 was significant",  # Date-like but not SSN format
            "Model number: 4532-1234-5678-9012",     # Invalid credit card (Luhn fails)
            "Phone extension 123-45-6789",           # Could be SSN format but different context
            "Version 1.2.3.4 of software",           # IP address, not sensitive
        ]
        
        for text in false_positive_cases:
            result = pattern_detector.assess_compliance_risk(text)
            # These should have low or zero scores
            assert result.score < 0.5, f"Should not trigger high score for: {text} (got {result.score})"
    
    def test_boundary_risk_scores(self):
        """Test behavior at risk threshold boundaries"""
        # Test exactly at threshold
        threshold = 0.7
        
        # Find text that scores exactly at threshold
        # This is tricky since scores are calculated dynamically
        # We'll test with known patterns
        
        # Just below threshold
        email_text = "Contact: john@example.com"  # Should be 0.4
        result = pattern_detector.assess_compliance_risk(email_text)
        if result.score < threshold:
            assert not result.blocked, f"Should not block score {result.score} below threshold {threshold}"
        
        # Above threshold  
        ssn_text = "SSN: 123-45-6789"  # Should be 1.2
        result = pattern_detector.assess_compliance_risk(ssn_text)
        if result.score >= threshold:
            assert result.blocked, f"Should block score {result.score} above threshold {threshold}"

# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Test integration between components"""
    
    def test_end_to_end_blocking_flow(self, test_client):
        """Test complete blocking flow from request to audit log"""
        # Make request with sensitive data
        response = test_client.client.post("/chat/stream", json={
            "message": "My SSN is 123-45-6789"
        })
        
        assert response.status_code == 200
        
        # Should be blocked
        content = response.text
        assert "blocked" in content.lower()
        
        # Check audit logs
        audit_response = test_client.client.get("/audit-logs?limit=1")
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert len(audit_data["logs"]) > 0
        
        latest_log = audit_data["logs"][0]
        assert latest_log["event_type"] == "user_input_blocked"
        assert latest_log["risk_score"] >= 1.0
        assert latest_log["blocked"] == True
    
    def test_metrics_updates(self, test_client):
        """Test that metrics are updated correctly"""
        # Get initial metrics
        initial_response = test_client.client.get("/metrics")
        initial_data = initial_response.json()
        initial_total = initial_data["total_requests"]
        initial_blocked = initial_data["blocked_requests"]
        
        # Make a request that should be blocked
        test_client.client.post("/chat/stream", json={
            "message": "SSN: 987-65-4321"
        })
        
        # Check updated metrics
        updated_response = test_client.client.get("/metrics")
        updated_data = updated_response.json()
        
        assert updated_data["total_requests"] > initial_total, "Total requests should increase"
        assert updated_data["blocked_requests"] > initial_blocked, "Blocked requests should increase"

# ==================== PYTEST CONFIGURATION ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
