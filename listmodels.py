import google.generativeai as genai
import os
from typing import List

def list_available_models() -> List[str]:
    """List all available Gemini models."""
    try:
        # Configure the API key
        genai.configure(api_key=os.getenv('GEMINI_API_KEYs'))
        
        # Get list of available models
        models = genai.list_models()
        
        print("\nAvailable Gemini Models:")
        print("-" * 50)
        for model in models:
            if "gemini" in model.name.lower():
                print(f"Name: {model.name}")
                print(f"Display Name: {model.display_name}")
                print(f"Description: {model.description}")
                print(f"Input Types: {', '.join(str(t) for t in model.supported_generation_methods)}")
                print("-" * 50)
                
    except Exception as e:
        print(f"Error listing models: {str(e)}")

if __name__ == "__main__":
    list_available_models()
