import requests
import json

# List available models in Gemini API
API_KEY = "AIzaSyATBxlRuYcd3sme4Kz2O7pu_TIABuF0wtM"

def list_gemini_models():
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        # List models endpoint
        url = f'https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}'
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Available models:")
            
            if 'models' in result:
                for model in result['models']:
                    name = model.get('name', 'Unknown')
                    display_name = model.get('displayName', 'Unknown')
                    supported_methods = model.get('supportedGenerationMethods', [])
                    
                    print(f"  - {name}")
                    print(f"    Display Name: {display_name}")
                    print(f"    Supported Methods: {supported_methods}")
                    print()
            return True
        else:
            print(f"❌ Failed to list models!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    list_gemini_models()