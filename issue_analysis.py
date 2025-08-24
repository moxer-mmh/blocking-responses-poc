#!/usr/bin/env python3
"""
Comprehensive Issue Analysis
============================

This script analyzes all the issues mentioned by the user:
1. Token flow - are we showing AI output or user input tokens?
2. Real-time risk scoring issues
3. Token counting problems  
4. Pattern score always being 0
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_pattern_detection():
    """Test why pattern score is always 0"""
    print("🔍 ISSUE 1: Pattern Score Always 0")
    print("=" * 50)
    
    # Test with text that should trigger patterns
    test_cases = [
        "My SSN is 123-45-6789",
        "My email is john@example.com", 
        "My credit card is 4532 1234 5678 9012",
        "My phone is 555-123-4567",
        "Regular text with no patterns"
    ]
    
    for test_text in test_cases:
        print(f"\n📝 Testing: '{test_text}'")
        
        try:
            response = requests.post(
                f"{API_BASE}/compliance/analyze-text",
                json={"text": test_text},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   📊 Pattern Score: {result.get('pattern_score', 'N/A')}")
                print(f"   🔍 Presidio Score: {result.get('presidio_score', 'N/A')}")
                print(f"   🎯 Total Score: {result.get('total_score', 'N/A')}")
                print(f"   ⚠️  Rules: {result.get('triggered_rules', [])}")
                print(f"   🏷️  Entities: {[e['entity_type'] for e in result.get('presidio_entities', [])]}")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def test_token_flow_analysis():
    """Test what tokens are being analyzed in the stream"""
    print("\n🔄 ISSUE 2: Token Flow Analysis")
    print("=" * 50)
    
    test_message = {
        "message": "Hello John Smith, your SSN 123-45-6789 is important."
    }
    
    print(f"📝 User Input: {test_message['message']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=test_message,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200:
            token_count = 0
            window_count = 0
            ai_tokens = []
            window_texts = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data["type"] == "chunk":
                            token_count += 1
                            ai_tokens.append(data["content"])
                            
                        elif data["type"] == "window_analysis":
                            window_count += 1
                            analysis = json.loads(data["content"])
                            window_texts.append(analysis["window_text"])
                            
                            print(f"\n🪟 Window {window_count}:")
                            print(f"   📍 Position: {analysis['analysis_position']}")
                            print(f"   📏 Size: {analysis['window_size']} tokens")
                            print(f"   📊 Pattern Score: {analysis['pattern_score']}")
                            print(f"   🔍 Presidio Score: {analysis['presidio_score']}")
                            print(f"   📝 Text: '{analysis['window_text'][:80]}{'...' if len(analysis['window_text']) > 80 else ''}'")
                            
                        elif data["type"] == "completed":
                            break
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            print(f"\n📊 ANALYSIS SUMMARY:")
            print(f"   🤖 AI Tokens Generated: {token_count}")
            print(f"   🪟 Windows Analyzed: {window_count}")
            print(f"   📝 AI Response: '{''.join(ai_tokens)[:100]}{'...' if len(''.join(ai_tokens)) > 100 else ''}'")
            
            # Check if windows contain user input vs AI output
            user_input_in_windows = any("John Smith" in text or "123-45-6789" in text for text in window_texts)
            ai_output_in_windows = any("assist" in text or "help" in text for text in window_texts)
            
            print(f"\n🔍 TOKEN FLOW ANALYSIS:")
            print(f"   ✅ User Input in Windows: {user_input_in_windows}")
            print(f"   ❌ AI Output in Windows: {ai_output_in_windows}")
            
            if ai_output_in_windows:
                print(f"   🚨 ISSUE FOUND: Windows are analyzing AI OUTPUT instead of user input!")
            else:
                print(f"   ✅ CORRECT: Windows are analyzing user input only")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def test_risk_scoring_calculation():
    """Test the real-time risk scoring calculations"""
    print("\n📊 ISSUE 3: Real-time Risk Scoring")
    print("=" * 50)
    
    test_message = {
        "message": "Tell me about John Doe with ssn"  # Should trigger high risk
    }
    
    print(f"📝 Test Message: {test_message['message']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=test_message,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200:
            risk_scores = []
            token_texts = []
            analysis_scores = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data["type"] == "chunk":
                            token_texts.append(data["content"])
                            token_risk = data.get("risk_score", 0)
                            risk_scores.append(token_risk)
                            
                        elif data["type"] == "window_analysis":
                            analysis = json.loads(data["content"])
                            analysis_scores.append(analysis["total_score"])
                            
                        elif data["type"] == "completed":
                            break
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            print(f"\n📊 RISK SCORING ANALYSIS:")
            print(f"   🎯 Window Analysis Scores: {analysis_scores}")
            print(f"   🔄 Token Risk Scores: {risk_scores[:10]}{'...' if len(risk_scores) > 10 else ''}")
            print(f"   📈 Max Window Score: {max(analysis_scores) if analysis_scores else 'N/A'}")
            print(f"   📈 Max Token Score: {max(risk_scores) if risk_scores else 'N/A'}")
            
            # Check if risk scores match window analysis
            if analysis_scores and risk_scores:
                if max(analysis_scores) > 0.5 and max(risk_scores) < 0.1:
                    print(f"   🚨 ISSUE: Window shows high risk ({max(analysis_scores):.3f}) but tokens show low risk ({max(risk_scores):.3f})")
                else:
                    print(f"   ✅ Risk scoring appears consistent")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_token_counting():
    """Test token counting accuracy"""
    print("\n🔢 ISSUE 4: Token Counting")
    print("=" * 50)
    
    import tiktoken
    
    test_texts = [
        "Hello world",
        "Tell me about John Doe with ssn",
        "Hello, my name is John Smith and I work at Acme Corporation"
    ]
    
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    for text in test_texts:
        print(f"\n📝 Text: '{text}'")
        
        # Count tokens locally
        tokens = encoder.encode(text)
        local_count = len(tokens)
        print(f"   🔢 Local Token Count: {local_count}")
        print(f"   📜 Tokens: {[encoder.decode([t]) for t in tokens[:10]]}{'...' if len(tokens) > 10 else ''}")
        
        # Test via API
        try:
            response = requests.post(
                f"{API_BASE}/chat/stream",
                json={"message": text},
                stream=True,
                timeout=10
            )
            
            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            
                            if data["type"] == "window_analysis":
                                analysis = json.loads(data["content"])
                                print(f"   🪟 Window Size (API): {analysis['window_size']} tokens")
                                print(f"   📍 Analysis Position: {analysis['analysis_position']} tokens")
                                break
                                
                        except (json.JSONDecodeError, KeyError):
                            continue
                            
        except Exception as e:
            print(f"   ❌ API Error: {e}")

def main():
    """Run comprehensive issue analysis"""
    print("🔍 COMPREHENSIVE ISSUE ANALYSIS")
    print("=" * 70)
    
    # Test 1: Pattern detection 
    test_pattern_detection()
    
    # Test 2: Token flow
    test_token_flow_analysis()
    
    # Test 3: Risk scoring
    test_risk_scoring_calculation()
    
    # Test 4: Token counting
    test_token_counting()
    
    print("\n🎯 ANALYSIS COMPLETE")
    print("=" * 70)
    print("Check the output above for specific issues found!")

if __name__ == "__main__":
    main()
