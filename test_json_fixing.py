#!/usr/bin/env python3
"""Test the improved JSON extraction and fixing functions"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_json_from_response, fix_incomplete_json
import json

# Test case that matches your error
truncated_json = '''[ { "q": "What two main aspects must cybersecurity balance to protect sensitive data?", "answer": "Technical defenses and legal/ethical responsibilities.", "keywords": ["technical and ethical", "technical and legal", "technology and compliance"], "feedback": "Cybersecurity isn't just about technology; it also involves following laws and ethical guidelines to properly protect information." }, { "q": "Why is 'compliance' important in cybersecurit'''

print("Testing JSON fixing function...")
print("="*50)

print("Original truncated JSON:")
print(truncated_json[:200] + "...")
print()

# Test the fix
try:
    fixed = fix_incomplete_json(truncated_json)
    print("Fixed JSON:")
    print(fixed[:200] + "...")
    print()
    
    # Try to parse it
    parsed = json.loads(fixed)
    print("✅ Successfully parsed fixed JSON!")
    print(f"Found {len(parsed)} questions")
    for i, q in enumerate(parsed):
        print(f"  {i+1}. {q.get('q', 'No question')[:50]}...")
        
except Exception as e:
    print(f"❌ Still failed: {e}")

print("\n" + "="*50)

# Test some other incomplete JSON cases
test_cases = [
    '{"correct": true, "confidence": 95',  # Missing closing brace
    '[{"q": "test", "answer": "test"}',    # Missing closing bracket
    '[{"q": "test", "answer": "test"},',   # Trailing comma
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest case {i}: {test_case}")
    try:
        fixed = fix_incomplete_json(test_case)
        parsed = json.loads(fixed)
        print(f"✅ Fixed and parsed: {parsed}")
    except Exception as e:
        print(f"❌ Failed: {e}")

print("\nTest completed!")