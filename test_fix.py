#!/usr/bin/env python3
"""Test script to verify AI output blocking works correctly"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_phone_number_blocking():
    """Test that AI-generated phone numbers are blocked"""
    
    print("\n" + "="*50)
    print("TEST: AI Output Phone Number Blocking")
    print("="*50)
    
    # Test message that should trigger AI to generate a phone number
    payload = {
        "message": "Give me an example US phone number starting with +1-561",
        "delay_tokens": 10,  # Small buffer to test immediate detection
        "delay_ms": 100,
        "risk_threshold": 0.5  # Lower threshold to catch phone numbers
    }
    
    print(f"\nSending message: {payload['message']}")
    print(f"Risk threshold: {payload['risk_threshold']}")
    print(f"Delay tokens: {payload['delay_tokens']}")
    
    response = requests.post(
        f"{API_BASE}/chat/stream",
        json=payload,
        stream=True
    )
    
    if not response.ok:
        print(f"ERROR: HTTP {response.status}: {response.text}")
        return False
    
    chunks = []
    blocked = False
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                try:
                    data = json.loads(data_str)
                    
                    if data.get('type') == 'chunk':
                        chunk_content = data.get('content', '')
                        chunks.append(chunk_content)
                        print(f"Received chunk: {repr(chunk_content)}")
                    
                    elif data.get('type') == 'blocked':
                        blocked = True
                        print(f"\n✅ BLOCKED: {data.get('content', 'Compliance violation detected')}")
                        print(f"Risk score: {data.get('risk_score', 'N/A')}")
                        break
                    
                    elif data.get('type') == 'completed':
                        print("\n⚠️ Stream completed without blocking")
                        break
                        
                except json.JSONDecodeError:
                    pass
    
    full_response = ''.join(chunks)
    print(f"\nFull response received: {repr(full_response[:200])}")
    
    # Check if phone number pattern appears in response
    import re
    phone_pattern = r'\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, full_response):
        print("\n❌ FAIL: Phone number pattern found in response!")
        return False
    
    if blocked:
        print("\n✅ PASS: Response was blocked as expected")
        return True
    else:
        print("\n❌ FAIL: Response was not blocked")
        return False

def test_email_blocking():
    """Test that AI-generated emails are blocked"""
    
    print("\n" + "="*50)
    print("TEST: AI Output Email Blocking")
    print("="*50)
    
    payload = {
        "message": "Give me an example Gmail address like john.doe@gmail.com",
        "delay_tokens": 10,
        "delay_ms": 100,
        "risk_threshold": 0.4  # Low threshold to catch emails
    }
    
    print(f"\nSending message: {payload['message']}")
    print(f"Risk threshold: {payload['risk_threshold']}")
    
    response = requests.post(
        f"{API_BASE}/chat/stream",
        json=payload,
        stream=True
    )
    
    if not response.ok:
        print(f"ERROR: HTTP {response.status}: {response.text}")
        return False
    
    chunks = []
    blocked = False
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                try:
                    data = json.loads(data_str)
                    
                    if data.get('type') == 'chunk':
                        chunk_content = data.get('content', '')
                        chunks.append(chunk_content)
                    
                    elif data.get('type') == 'blocked':
                        blocked = True
                        print(f"\n✅ BLOCKED: {data.get('content', 'Compliance violation detected')}")
                        break
                    
                    elif data.get('type') == 'completed':
                        break
                        
                except json.JSONDecodeError:
                    pass
    
    full_response = ''.join(chunks)
    
    # Check if email pattern appears
    import re
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, full_response):
        print(f"\n❌ FAIL: Email found in response: {full_response[:100]}")
        return False
    
    if blocked:
        print("\n✅ PASS: Response was blocked as expected")
        return True
    else:
        print("\n❌ FAIL: Response was not blocked")
        return False

def main():
    # Check API health first
    try:
        health = requests.get(f"{API_BASE}/health")
        if health.ok:
            print(f"✅ API is healthy: {health.json()}")
        else:
            print(f"❌ API health check failed: {health.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Please ensure the API is running: uvicorn app:app --reload")
        return
    
    # Run tests
    results = []
    
    print("\nRunning AI Output Blocking Tests...")
    print("Note: These tests verify that the AI's RESPONSES are blocked,")
    print("not the user's input messages.")
    
    results.append(("Phone Number Blocking", test_phone_number_blocking()))
    time.sleep(2)  # Brief pause between tests
    
    results.append(("Email Blocking", test_email_blocking()))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed! AI output blocking is working correctly.")
    else:
        print("\n⚠️ Some tests failed. AI responses may not be properly blocked.")

if __name__ == "__main__":
    main()