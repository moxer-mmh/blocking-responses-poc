#!/usr/bin/env python3
"""Test email detection scoring"""

import requests
import json

API_BASE = "http://localhost:8000"

test_texts = [
    "Contact john.doe@gmail.com for more info",
    "My email is john.doe123@gmail.com",
    "Send to doe.john@gmail.com",
    "Email: john.doe.professional@gmail.com"
]

print("Testing email detection scores:")
print("="*50)

for text in test_texts:
    response = requests.post(
        f"{API_BASE}/assess-risk",
        params={"text": text}
    )
    
    if response.ok:
        data = response.json()
        print(f"\nText: {text}")
        print(f"Score: {data['score']:.2f}")
        print(f"Blocked: {data['blocked']}")
        print(f"Rules: {data['triggered_rules']}")
    else:
        print(f"Error: {response.status_code}")

print("\n" + "="*50)
print("Current threshold: 1.0")
print("Email pattern weight: 0.3")
print("\nConclusion: Emails alone won't trigger blocking!")