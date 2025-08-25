#!/usr/bin/env python3
"""Test the buffer blocking logic with mock data"""

import asyncio
from collections import deque
from app import RegulatedPatternDetector, PresidioDetector

async def test_buffer_blocking():
    """Simulate the buffer logic with sensitive content"""
    
    # Initialize detectors
    pattern_detector = RegulatedPatternDetector()
    presidio_detector = PresidioDetector()
    
    # Simulate AI generating email addresses
    ai_stream = [
        "Sure! Here ",
        "are some example ",
        "Gmail addresses for ",
        "John Doe:\n\n1. ",
        "john.doe@",
        "gmail.com\n",
        "2. doe.john@",
        "gmail.com\n",
        "3. john.doe123@",
        "gmail.com"
    ]
    
    token_buffer = deque()
    risk_threshold = 1.0
    delay_tokens = 20  # Default buffer size
    blocked = False
    emitted_chunks = []
    
    print("Simulating AI stream with email addresses...")
    print("="*60)
    
    for piece in ai_stream:
        # Add to buffer
        token_buffer.append(piece)
        print(f"Added to buffer: {repr(piece)}")
        
        # Analyze FULL buffer (the fix)
        full_buffer_text = "".join(list(token_buffer))
        print(f"Full buffer: {repr(full_buffer_text[:100])}")
        
        # Check for compliance violations
        compliance_result = pattern_detector.assess_compliance_risk(full_buffer_text)
        presidio_score, _ = presidio_detector.analyze_text(full_buffer_text)
        total_score = compliance_result.score + presidio_score
        
        print(f"Buffer risk score: {total_score:.2f}")
        
        if total_score >= risk_threshold:
            blocked = True
            print(f"\n🚫 BLOCKED! Risk score {total_score:.2f} >= {risk_threshold}")
            print(f"Triggered rules: {compliance_result.triggered_rules}")
            break
        
        # Simulate emission (simplified)
        if len(token_buffer) > 3:  # Emit some chunks
            chunk = token_buffer.popleft()
            emitted_chunks.append(chunk)
            print(f"Emitted: {repr(chunk)}")
    
    print("\n" + "="*60)
    print("RESULTS:")
    print(f"Blocked: {blocked}")
    print(f"Emitted content: {repr(''.join(emitted_chunks))}")
    
    # Check if emails leaked
    import re
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    leaked_emails = re.findall(email_pattern, ''.join(emitted_chunks))
    
    if blocked and not leaked_emails:
        print("✅ SUCCESS: Content blocked before emails were shown")
        return True
    elif leaked_emails:
        print(f"❌ FAILURE: Emails leaked: {leaked_emails}")
        return False
    else:
        print("⚠️ No emails generated in test")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_buffer_blocking())