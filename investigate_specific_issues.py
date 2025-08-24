#!/usr/bin/env python3
"""
INVESTIGATING SPECIFIC ISSUES
============================

1. Why "Hello my name is John Smith and I work at Acme Corporation" = WARNING
   But "Hello my name is John Smith and I work at Acme" = BLOCKED

2. Why Pattern Score is always 0.000 in frontend but works in backend API
"""

import requests
import json

def test_text_variations():
    """Test the specific text variations that behave differently"""
    print("🔍 TESTING TEXT VARIATIONS")
    print("=" * 50)
    
    test_cases = [
        "Hello my name is John Smith and I work at Acme Corporation",
        "Hello my name is John Smith and I work at Acme", 
        "John Smith",
        "Hello John Smith",
        "My name is John Smith"
    ]
    
    for text in test_cases:
        print(f"\n📝 Testing: '{text}'")
        
        try:
            # Test with direct analysis API
            response = requests.post(
                "http://localhost:8000/compliance/analyze-text",
                json={"text": text},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   📊 Pattern Score: {result['pattern_score']}")
                print(f"   🔍 Presidio Score: {result['presidio_score']}")
                print(f"   🎯 Total Score: {result['total_score']}")
                print(f"   🚫 Blocked: {result['blocked']}")
                print(f"   ⚠️  Rules: {result['triggered_rules']}")
                print(f"   🏷️  Entities: {[e['entity_type'] for e in result['presidio_entities']]}")
                
                # Test blocking behavior
                if result['total_score'] >= 1.0:
                    print(f"   🔴 SHOULD BLOCK (score >= 1.0)")
                elif result['total_score'] >= 0.7:
                    print(f"   🟡 SHOULD WARN (score >= 0.7)")
                else:
                    print(f"   🟢 SHOULD PASS (score < 0.7)")
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def test_stream_vs_analysis():
    """Test why streaming shows different pattern scores than analysis"""
    print("\n🔄 TESTING STREAM VS ANALYSIS")
    print("=" * 50)
    
    test_text = "Hello my name is John Smith and I work at Acme Corporation"
    
    print(f"📝 Testing: '{test_text}'")
    
    # Test 1: Direct analysis
    print("\n1️⃣ DIRECT ANALYSIS:")
    try:
        response = requests.post(
            "http://localhost:8000/compliance/analyze-text",
            json={"text": test_text},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 Pattern Score: {result['pattern_score']}")
            print(f"   🔍 Presidio Score: {result['presidio_score']}")
            print(f"   🎯 Total Score: {result['total_score']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Stream analysis
    print("\n2️⃣ STREAM ANALYSIS:")
    try:
        response = requests.post(
            "http://localhost:8000/chat/stream",
            json={"message": test_text},
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data["type"] == "window_analysis":
                            analysis = json.loads(data["content"])
                            print(f"   📊 Pattern Score: {analysis['pattern_score']}")
                            print(f"   🔍 Presidio Score: {analysis['presidio_score']}")
                            print(f"   🎯 Total Score: {analysis['total_score']}")
                            print(f"   📝 Window Text: '{analysis['window_text']}'")
                            break
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def analyze_blocking_logic():
    """Analyze the blocking logic differences"""
    print("\n🧠 ANALYZING BLOCKING LOGIC")
    print("=" * 50)
    
    # Check current risk threshold
    try:
        response = requests.get("http://localhost:8000/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            threshold = config.get('risk_threshold', 'unknown')
            print(f"📊 Current Risk Threshold: {threshold}")
            
            if threshold == 1:
                print(f"   ⚠️  ISSUE: Threshold is 1.0 - very high!")
                print(f"   💡 This means only scores >= 1.0 will block")
                print(f"   💡 Scores 0.7-0.99 will show warnings but not block")
        else:
            print(f"❌ Could not get config: {response.status_code}")
    except Exception as e:
        print(f"❌ Config error: {e}")

def main():
    print("🔍 COMPREHENSIVE ISSUE INVESTIGATION")
    print("=" * 60)
    
    test_text_variations()
    test_stream_vs_analysis()
    analyze_blocking_logic()
    
    print(f"\n🎯 SUMMARY:")
    print(f"=" * 60)
    print(f"1. Risk threshold appears to be 1.0 (very high)")
    print(f"2. Pattern scores may differ between APIs")
    print(f"3. Blocking behavior depends on exact total score")
    print(f"4. Frontend may be showing cached or different data")

if __name__ == "__main__":
    main()
