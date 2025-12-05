import requests
import json

# Test the Gemini API directly
API_KEY = "AIzaSyATBxlRuYcd3sme4Kz2O7pu_TIABuF0wtM"
MODEL = "gemini-2.5-flash"

def test_gemini_api():
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Gemini API endpoint
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}'
        
        data = {
            'contents': [{
                'parts': [{'text': 'Hello, can you respond with "API is working"?'}]
            }],
            'generationConfig': {
                'maxOutputTokens': 100,
                'temperature': 0.7
            }
        }
        
        print(f"Testing API with URL: {url[:80]}...")
        print(f"Model: {MODEL}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ API call failed!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_api()