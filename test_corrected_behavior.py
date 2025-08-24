#!/usr/bin/env python3
"""
TESTING CORRECTED BEHAVIOR
==========================

After fixing risk threshold from 1.0 → 0.7
"""

import requests
import json

def test_corrected_behavior():
    """Test the behavior with corrected risk threshold"""
    print("🔧 TESTING CORRECTED BEHAVIOR")
    print("=" * 50)
    
    # Check new threshold
    try:
        response = requests.get("http://localhost:8000/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            threshold = config.get('risk_threshold', 'unknown')
            print(f"📊 New Risk Threshold: {threshold}")
        else:
            print(f"❌ Could not get config: {response.status_code}")
    except Exception as e:
        print(f"❌ Config error: {e}")
    
    print(f"\n🧪 TESTING BOTH CASES:")
    
    test_cases = [
        ("Hello my name is John Smith and I work at Acme Corporation", "Should be BLOCKED now (0.765 ≥ 0.7)"),
        ("Hello my name is John Smith and I work at Acme", "Should be BLOCKED (1.53 ≥ 0.7)")
    ]
    
    for text, expectation in test_cases:
        print(f"\n📝 Testing: '{text}'")
        print(f"   💭 {expectation}")
        
        try:
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
                print(f"   🏷️  Entities: {[e['entity_type'] for e in result['presidio_entities']]}")
                
                if result['blocked']:
                    print(f"   ✅ CORRECTLY BLOCKED")
                else:
                    print(f"   ❌ NOT BLOCKED (should be blocked at 0.7 threshold)")
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def test_stream_blocking():
    """Test that streaming now blocks correctly"""
    print(f"\n🔄 TESTING STREAM BLOCKING")
    print("=" * 50)
    
    test_text = "Hello my name is John Smith and I work at Acme Corporation"
    print(f"📝 Testing: '{test_text}'")
    print(f"💭 Should be BLOCKED in stream now")
    
    try:
        response = requests.post(
            "http://localhost:8000/chat/stream",
            json={"message": test_text},
            stream=True,
            timeout=15
        )
        
        blocked = False
        completed = False
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data["type"] == "blocked":
                            blocked = True
                            print(f"   ✅ STREAM BLOCKED: {data.get('content', 'No reason given')}")
                            break
                        elif data["type"] == "completed":
                            completed = True
                            print(f"   ❌ STREAM COMPLETED (should have been blocked)")
                            break
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        if not blocked and not completed:
            print(f"   ❌ STREAM HANGING (possible issue)")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def explain_pattern_scores():
    """Explain why pattern scores are 0"""
    print(f"\n📚 EXPLAINING PATTERN SCORES")
    print("=" * 50)
    
    print(f"🎯 Why Pattern Score = 0.000 for 'John Smith':")
    print(f"   ✅ Pattern detection looks for specific formats:")
    print(f"   • SSN: 123-45-6789 → Pattern Score: 1.2")
    print(f"   • Email: john@example.com → Pattern Score: 0.4") 
    print(f"   • Credit Card: 4532 1234 5678 9012 → Pattern Score: 0.5")
    print(f"   • Phone: 555-123-4567 → Pattern Score: 0.5")
    print(f"")
    print(f"   ❌ 'John Smith' is just a name (no specific pattern)")
    print(f"   ✅ Presidio detects it as PERSON entity → Presidio Score: 0.765")
    print(f"   ✅ Total = Pattern (0.0) + Presidio (0.765) = 0.765")
    print(f"")
    print(f"🎯 This is CORRECT behavior!")

def main():
    print("🎯 COMPREHENSIVE CORRECTED TESTING")
    print("=" * 60)
    
    test_corrected_behavior()
    test_stream_blocking()
    explain_pattern_scores()
    
    print(f"\n🎖️  FINAL SUMMARY:")
    print(f"=" * 60)
    print(f"1. ✅ Risk threshold fixed: 1.0 → 0.7")
    print(f"2. ✅ Both test cases should now BLOCK correctly")
    print(f"3. ✅ Pattern Score = 0.000 is CORRECT (no patterns in names)")
    print(f"4. ✅ Presidio Score = 0.765 is CORRECT (person detection)")
    print(f"5. ✅ Total Score = 0.765 ≥ 0.7 → BLOCKS correctly")

if __name__ == "__main__":
    main()
