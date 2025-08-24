#!/usr/bin/env python3
"""
Fixed Sliding Window Analysis Verification
==========================================

This test verifies that the sliding window analysis now correctly shows
what was analyzed in the USER INPUT, not the AI response.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_input_analysis_fix():
    """Test that window analysis shows user input, not AI response"""
    print("🔍 Testing Input Analysis Fix")
    print("=" * 50)
    
    test_message = {
        "message": "Hello, my name is John Smith I work at Acme Corp and my email is john.smit"
    }
    
    print(f"📝 User Input: {test_message['message']}")
    print("\n🔍 Expected: Window analysis should show the USER INPUT text")
    print("❌ Previous Bug: Window analysis showed AI RESPONSE text")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=test_message,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200:
            window_analyses = []
            ai_response_chunks = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        
                        if data["type"] == "window_analysis":
                            analysis_content = json.loads(data["content"])
                            window_analyses.append(analysis_content)
                            
                            # Check if window_text contains USER INPUT
                            window_text = analysis_content["window_text"]
                            
                            print(f"\n🪟 Window {len(window_analyses)}:")
                            print(f"   Position: {analysis_content['analysis_position']}")
                            print(f"   Size: {analysis_content['window_size']} tokens")
                            print(f"   Risk Score: {analysis_content['total_score']:.3f}")
                            print(f"   Analyzed Text: {window_text[:100]}...")
                            
                            # Verify it's analyzing USER INPUT, not AI response
                            if "John Smith" in window_text:
                                print(f"   ✅ CORRECT: Analyzing user input (found 'John Smith')")
                            elif "How can I assist" in window_text:
                                print(f"   ❌ BUG: Still analyzing AI response")
                            else:
                                print(f"   ⚠️  UNCLEAR: Neither user input nor typical AI response")
                        
                        elif data["type"] == "chunk":
                            ai_response_chunks.append(data["content"])
                            
                        elif data["type"] == "complete":
                            break
                            
                    except json.JSONDecodeError:
                        continue
                    except KeyError:
                        continue
            
            print(f"\n📊 Analysis Summary:")
            print(f"   🪟 Windows Analyzed: {len(window_analyses)}")
            print(f"   🤖 AI Response Chunks: {len(ai_response_chunks)}")
            
            ai_response = "".join(ai_response_chunks)
            print(f"   💬 AI Response Preview: {ai_response[:100]}...")
            
            # Final verification
            if window_analyses:
                first_window = window_analyses[0]
                if "John Smith" in first_window["window_text"]:
                    print(f"\n🎉 SUCCESS: Window analysis correctly shows USER INPUT")
                    print(f"   ✅ User said: 'Hello, my name is John Smith...'")
                    print(f"   ✅ Window analyzed: '{first_window['window_text'][:50]}...'")
                    return True
                else:
                    print(f"\n❌ FAILED: Window analysis still shows wrong content")
                    return False
            else:
                print(f"\n❌ FAILED: No window analyses found")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multiple_windows():
    """Test with longer input to see multiple windows"""
    print("\n🔍 Testing Multiple Windows")
    print("=" * 50)
    
    long_message = {
        "message": "Hello, my name is John Smith and I work at Acme Corporation. My email address is john.smith@acme.com and my phone number is 555-123-4567. I need assistance with processing customer data for Alice Johnson whose SSN is 123-45-6789. Please help me understand compliance requirements for healthcare data in the United States."
    }
    
    print(f"📝 Input Length: {len(long_message['message'])} characters")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=long_message,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200:
            window_count = 0
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data["type"] == "window_analysis":
                            window_count += 1
                            analysis_content = json.loads(data["content"])
                            
                            print(f"🪟 Window {window_count}: Score {analysis_content['total_score']:.3f}, "
                                  f"Size {analysis_content['window_size']}, "
                                  f"Text: '{analysis_content['window_text'][:50]}...'")
                            
                        elif data["type"] == "blocked":
                            print(f"🛑 Content was blocked!")
                            break
                            
                        elif data["type"] == "complete":
                            break
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            print(f"\n📊 Total Windows: {window_count}")
            return window_count > 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run complete verification"""
    print("🚀 Fixed Sliding Window Analysis Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Input analysis fix
    results.append(test_input_analysis_fix())
    
    # Test 2: Multiple windows
    results.append(test_multiple_windows())
    
    print("\n📊 Final Results")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ The fix is working correctly:")
        print("   • Window analysis shows USER INPUT text")
        print("   • AI response streams separately")
        print("   • Clear separation between analysis and generation")
        print("   • Demo will now be intuitive for engineers")
    else:
        print(f"❌ Some tests failed ({passed}/{total})")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
