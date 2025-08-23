#!/usr/bin/env python3
"""Simple test script to verify the API is working"""

import json
import asyncio
from app import pattern_detector, app


def test_risk_patterns():
    """Test the risk assessment patterns"""
    print("=== Testing Risk Patterns ===")

    test_cases = [
        ("What's the weather like?", "Safe content"),
        ("My email is john@example.com", "Email detection"),
        ("My SSN is 123-45-6789", "SSN detection"),
        ("Call me at (555) 123-4567", "Phone detection"),
        ("My password is secret123", "Secret detection"),
        ("Multiple: john@test.com, 123-45-6789, password", "Multiple patterns"),
    ]

    for text, description in test_cases:
        assessment = pattern_detector.assess_compliance_risk(text)
        print(f"\n{description}:")
        print(f"  Text: {text}")
        print(f"  Risk Score: {assessment.score:.2f}")
        print(f"  Blocked: {assessment.blocked}")
        print(
            f"  Rules: {', '.join(assessment.triggered_rules) if assessment.triggered_rules else 'None'}"
        )


def test_configuration():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    from app import settings

    print(f"Model: {settings.default_model}")
    print(f"Judge Model: {settings.judge_model}")
    print(f"Delay Tokens: {settings.delay_tokens}")
    print(f"Delay MS: {settings.delay_ms}")
    print(f"Risk Threshold: {settings.risk_threshold}")
    print(f"Judge Threshold: {settings.judge_threshold}")
    print(f"CORS Origins: {settings.get_cors_origins()}")


def test_health_endpoints():
    """Test health and info endpoints"""
    print("\n=== Testing Health Endpoints ===")

    # Import test client
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test health endpoint
    response = client.get("/health")
    print(f"Health Check: {response.status_code} - {response.json()}")

    # Test config endpoint
    response = client.get("/config")
    print(f"Config: {response.status_code} - {json.dumps(response.json(), indent=2)}")

    # Test patterns endpoint
    response = client.get("/patterns")
    print(f"Patterns: {response.status_code}")
    for name, info in response.json().items():
        print(f"  {name}: score={info['score']}, desc='{info['description']}'")


def test_risk_endpoint():
    """Test the risk assessment endpoint"""
    print("\n=== Testing Risk Assessment Endpoint ===")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    test_texts = [
        "Safe content here",
        "Email me at test@example.com",
        "My SSN is 123-45-6789",
    ]

    for text in test_texts:
        response = client.post(f"/assess-risk?text={text}")
        result = response.json()
        print(f"\nText: {text}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Blocked: {result['blocked']}")
        print(
            f"  Rules: {', '.join(result['triggered_rules']) if result['triggered_rules'] else 'None'}"
        )


def main():
    """Run all tests"""
    print("🧪 Blocking Responses API - System Verification\n")

    try:
        test_risk_patterns()
        test_configuration()
        test_health_endpoints()
        test_risk_endpoint()

        print("\n✅ All tests completed successfully!")
        print("\n🌐 Access your services at:")
        print("  Web Interface: http://localhost")
        print("  API Direct: http://localhost:8000")
        print("  API Docs: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

