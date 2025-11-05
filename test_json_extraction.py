#!/usr/bin/env python3
"""Test the new JSON extraction function"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_json_from_response
import json

# Test cases for the JSON extraction function
test_cases = [
    # Case 1: JSON wrapped in markdown code blocks
    '```json\n[{"q": "What is 2+2?", "answer": "4"}]\n```',
    
    # Case 2: JSON without code blocks
    '[{"q": "What is 2+2?", "answer": "4"}]',
    
    # Case 3: JSON with extra text
    'Here is the JSON: [{"q": "What is 2+2?", "answer": "4"}] Hope this helps!',
    
    # Case 4: JSON object instead of array
    '```json\n{"correct": true, "confidence": 95}\n```',
    
    # Case 5: Mixed content with markdown
    'Here are the questions:\n```json\n[{"q": "What is ls?", "answer": "list files"}]\n```\nThese should work!'
]

print("Testing JSON extraction function...")
print("="*50)

for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest Case {i}:")
    print(f"Input: {test_case[:100]}...")
    
    try:
        extracted = extract_json_from_response(test_case)
        print(f"Extracted: {extracted}")
        
        # Try to parse the extracted JSON
        parsed = json.loads(extracted)
        print(f"✅ Successfully parsed: {type(parsed)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*50)
print("Test completed!")