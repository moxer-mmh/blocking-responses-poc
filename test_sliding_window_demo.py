#!/usr/bin/env python3
"""
Sliding Window Analysis Demo Script
==================================

This script demonstrates the new sliding window analysis feature that replaces
the inefficient token-by-token analysis approach.

Key improvements:
- 25x fewer API calls (analyzes every 25 tokens instead of every token)
- Better context (150-token windows vs single tokens)
- Real-time visibility into what's being analyzed
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def test_analysis_config():
    """Test the analysis configuration endpoint"""
    print("🔧 Testing Analysis Configuration")
    print("=" * 50)
    
    response = requests.get(f"{API_BASE}/compliance/analysis-config")
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Window Size: {config['current_config']['analysis_window_size']} tokens")
        print(f"✅ Analysis Frequency: Every {config['current_config']['analysis_frequency']} tokens")
        print(f"✅ Efficiency Gain: {config['performance_estimates']['efficiency_gain']}")
        print(f"✅ Context Improvement: {config['performance_estimates']['context_improvement']}")
        return config
    else:
        print(f"❌ Failed to get config: {response.status_code}")
        return None

def test_safe_content():
    """Test with safe content to see sliding window analysis"""
    print("\n🟢 Testing Safe Content (Should Pass)")
    print("=" * 50)
    
    safe_message = {
        "message": "I am working on a technical project about machine learning algorithms. "
                  "The team is developing new approaches for natural language processing. "
                  "We are focusing on transformer architectures and attention mechanisms. "
                  "This research could help improve AI systems for various applications. "
                  "Our goal is to create more efficient and accurate models that can "
                  "understand context better and provide more helpful responses."
    }
    
    print(f"📝 Input: {safe_message['message'][:100]}...")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=safe_message,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=10
        )
        
        if response.status_code == 200:
            window_analyses = []
            chunks_received = 0
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        
                        if data["type"] == "window_analysis":
                            analysis_content = json.loads(data["content"])
                            window_analyses.append(analysis_content)
                            print(f"🔍 Window {len(window_analyses)}: Position {analysis_content['analysis_position']}, "
                                  f"Score: {analysis_content['total_score']:.3f}, "
                                  f"Size: {analysis_content['window_size']} tokens")
                        
                        elif data["type"] == "chunk":
                            chunks_received += 1
                        
                        elif data["type"] == "complete":
                            break
                            
                    except json.JSONDecodeError:
                        continue
                    except KeyError:
                        continue
            
            print(f"✅ Message passed! Received {chunks_received} chunks")
            print(f"🔍 Analyzed {len(window_analyses)} windows")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_risky_content():
    """Test with risky content to see blocking"""
    print("\n🔴 Testing Risky Content (Should Block)")
    print("=" * 50)
    
    risky_message = {
        "message": "Hello, my name is John Smith and my social security number is 123-45-6789. "
                  "I work at Acme Corp and my email is john.smith@acme.com. "
                  "I need to process credit card 4532-1234-5678-9012 for customer Alice Johnson "
                  "whose phone is (555) 123-4567. Please help me with this transaction."
    }
    
    print(f"📝 Input: {risky_message['message'][:100]}...")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=risky_message,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=10
        )
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data["type"] == "blocked":
                            print(f"🛑 Content blocked! Risk score: {data['risk_score']:.2f}")
                            print(f"📋 Reason: {data['content']}")
                            return True
                            
                    except json.JSONDecodeError:
                        continue
                    except KeyError:
                        continue
            
        print("❌ Content was not blocked (unexpected)")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health_check():
    """Test API health"""
    print("🏥 Testing API Health")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API Status: {health['status']}")
            print(f"✅ Version: {health['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def main():
    """Run the complete sliding window demo"""
    print("🚀 Sliding Window Analysis Demo")
    print("=" * 60)
    print("This demo shows the new efficient analysis approach:")
    print("• Old: 1 analysis call per token (expensive)")
    print("• New: 1 analysis call per 25 tokens (25x improvement)")
    print("• Better context: 150-token windows vs single tokens")
    print("=" * 60)
    
    # Test sequence
    results = []
    
    # 1. Health check
    results.append(test_health_check())
    
    # 2. Configuration
    config = test_analysis_config()
    results.append(config is not None)
    
    # 3. Safe content test
    results.append(test_safe_content())
    
    # 4. Risky content test
    results.append(test_risky_content())
    
    # Summary
    print("\n📊 Demo Results Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Sliding window analysis is working correctly.")
        print("\n🔗 Next Steps:")
        print("• Open http://localhost:80 to see the web interface")
        print("• Test different content types in the Stream Monitor")
        print("• View real-time window analysis visualization")
        print("• Check audit logs and compliance metrics")
    else:
        print("❌ Some tests failed. Check the API and frontend deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
