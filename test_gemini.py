#!/usr/bin/env python3
"""
Test script to verify Gemini API key works
"""
import requests
import json

def test_gemini_api():
    """Test the Gemini API with a simple prompt"""
    
    print("🧪 Testing Gemini API Configuration")
    print("=" * 50)
    
    # Import config here to debug
    try:
        from config import GEMINI_API_KEY, GEMINI_MODEL
        print(f"✅ Successfully imported config")
        print(f"   GEMINI_API_KEY length: {len(GEMINI_API_KEY) if GEMINI_API_KEY else 0}")
        print(f"   GEMINI_API_KEY value: {GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10 else f"   GEMINI_API_KEY value: {GEMINI_API_KEY}")
        print(f"   GEMINI_MODEL: {GEMINI_MODEL}")
    except Exception as e:
        print(f"❌ ERROR importing config: {e}")
        return False
    
    # Check API key
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        print("❌ ERROR: API key not configured properly")
        print(f"Current value: '{GEMINI_API_KEY}'")
        print("Please set a valid GEMINI_API_KEY in config.py")
        return False
    
    print(f"✅ API Key: {'*' * 20}{GEMINI_API_KEY[-8:]}")
    print(f"✅ Model: {GEMINI_MODEL}")
    
    # Test API call
    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [{
                'parts': [{'text': 'Hello! Please respond with "API test successful" if you can read this.'}]
            }],
            'generationConfig': {
                'maxOutputTokens': 50,
                'temperature': 0.1
            }
        }
        
        print(f"\n📡 Making API request to: {url[:80]}...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ SUCCESS! Gemini Response: {text_response}")
                return True
            else:
                print(f"❌ ERROR: No response in result: {result}")
                return False
        else:
            error_response = response.text
            print(f"❌ ERROR: {response.status_code}")
            print(f"Error details: {error_response}")
            
            # Parse error details
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_msg = error_json['error'].get('message', 'Unknown error')
                    print(f"Error message: {error_msg}")
                    
                    if 'API key not valid' in error_msg:
                        print("\n🔧 TROUBLESHOOTING:")
                        print("1. Check your API key at: https://aistudio.google.com/app/apikey")
                        print("2. Make sure the key has Generative AI API access")
                        print("3. Verify the key isn't expired or restricted")
                        print("4. Try creating a new API key")
                        print("5. Make sure there are no extra spaces or quotes in the key")
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    if success:
        print("\n🎉 Gemini API is working correctly!")
        print("You can now use AI features in the teacher portal.")
    else:
        print("\n💔 Gemini API test failed.")
        print("Please check your API key configuration.")