#!/usr/bin/env python3
"""Quick Gemini API test"""

import requests
import json

# Direct API key (copy from config.py)
API_KEY = "AIzaSyCIJ3pYj-FCwPmo3oz1qARUnd9T8Me5Y6A"

print(f"Testing with API key: {API_KEY}")
print(f"API key length: {len(API_KEY)}")
print(f"API key starts with AIza: {API_KEY.startswith('AIza')}")

# First, let's list available models
print("\n=== LISTING AVAILABLE MODELS ===")
list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    list_response = requests.get(list_url, timeout=30)
    print(f"List models status: {list_response.status_code}")
    
    if list_response.status_code == 200:
        models_data = list_response.json()
        print("Available models:")
        for model in models_data.get('models', []):
            name = model.get('name', '')
            supported_methods = model.get('supportedGenerationMethods', [])
            if 'generateContent' in supported_methods:
                print(f"  ✅ {name} (supports generateContent)")
            else:
                print(f"  ❌ {name} (does not support generateContent)")
    else:
        print(f"Error listing models: {list_response.text}")
        
except Exception as e:
    print(f"Error listing models: {e}")

print("\n=== TESTING API CALL ===")
# Test with correct model format
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [{
        "parts": [{
            "text": "Test question: What is 2+2? Just respond with the number."
        }]
    }]
}

headers = {
    "Content-Type": "application/json"
}

try:
    print("Making API request...")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ EXCEPTION: {e}")