import re

# Test API key format
api_key = "AIzaSyATBxlRuYcd3sme4Kz2O7pu_TIABuF0wtM"

# Gemini API keys should start with "AIza" and be about 39 characters long
gemini_pattern = r'^AIza[A-Za-z0-9_-]{35}$'

print(f"API Key: {api_key}")
print(f"Length: {len(api_key)}")
print(f"Starts with AIza: {api_key.startswith('AIza')}")
print(f"Matches Gemini pattern: {bool(re.match(gemini_pattern, api_key))}")

# Test if this looks like a valid key format
if re.match(gemini_pattern, api_key):
    print("✅ API key format appears valid")
else:
    print("❌ API key format appears invalid")
    print("Expected format: AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (39 chars total)")