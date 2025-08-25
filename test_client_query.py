#!/usr/bin/env python3

import requests
import json
import time

# Test the exact query the client mentioned
test_message = "please write me an essay in 500 words about diabetes. What should I do if I am at risk for diabetes."

print(f"Testing with query: {test_message}")
print(f"Expected: With default 150 token window and analysis every 25 tokens")
print(f"Input tokens: ~{len(test_message.split()) * 1.3:.0f} (estimated)")
print(f"Expected windows: ~{len(test_message.split()) * 1.3 / 25:.0f}")
print()

# First test the analysis config endpoint
print("1. Testing analysis config endpoint...")
try:
    response = requests.get("http://localhost:8000/compliance/analysis-config")
    if response.status_code == 200:
        config = response.json()
        print(f"   ✓ Window size: {config['current_config']['analysis_window_size']}")
        print(f"   ✓ Frequency: {config['current_config']['analysis_frequency']}")
        print(f"   ✓ Threshold: {config['current_config']['risk_threshold']}")
        print(f"   ✓ Efficiency: {config['efficiency_info']['efficiency_gain']}")
    else:
        print(f"   ✗ Failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Test the streaming endpoint
print("2. Testing streaming endpoint...")
try:
    payload = {
        "message": test_message,
        "delay_tokens": 20,
        "delay_ms": 100,  # Faster for testing
        "risk_threshold": 1.0,  # High threshold so we don't block
        "analysis_window_size": 150,
        "analysis_frequency": 25
    }
    
    response = requests.post(
        "http://localhost:8000/chat/stream",
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    if response.status_code == 200:
        print("   ✓ Stream started successfully")
        
        # Count events
        window_analyses = 0
        response_windows = 0
        chunks = 0
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data_content = line[6:]
                if data_content == '[DONE]':
                    break
                    
                try:
                    data = json.loads(data_content)
                    
                    if data['type'] == 'window_analysis':
                        window_analyses += 1
                        analysis_data = json.loads(data['content'])
                        if analysis_data.get('analysis_type') == 'input':
                            print(f"     Input Window {window_analyses}: {analysis_data['window_size']} tokens, risk: {analysis_data['total_score']:.3f}")
                    
                    elif data['type'] == 'response_window':
                        response_windows += 1
                        window_data = json.loads(data['content'])
                        print(f"     Response Window {response_windows}: {window_data['window_size']} tokens (safe)")
                    
                    elif data['type'] == 'chunk':
                        chunks += 1
                        if chunks <= 5:  # Show first few chunks
                            print(f"     Chunk {chunks}: '{data['content']}'")
                        elif chunks == 6:
                            print("     ... (more chunks)")
                    
                    elif data['type'] == 'completed':
                        completion_data = json.loads(data['content'])
                        stats = completion_data.get('input_analysis_stats', {})
                        print(f"   ✓ Completed: {stats.get('input_tokens', 0)} input tokens, {stats.get('windows_analyzed', 0)} windows analyzed")
                        print(f"     Response: {stats.get('response_tokens', 0)} tokens, {stats.get('response_windows_displayed', 0)} display windows")
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        print(f"   ✓ Total input windows analyzed: {window_analyses}")
        print(f"   ✓ Total response display windows: {response_windows}")
        print(f"   ✓ Total response chunks: {chunks}")
        
    else:
        print(f"   ✗ Failed: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

print()
print("Test completed!")
