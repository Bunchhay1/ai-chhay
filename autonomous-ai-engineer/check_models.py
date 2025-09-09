# check_models.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

print("Attempting to list available models...")

try:
    # Load the API key from the .env file
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("\nERROR: GOOGLE_API_KEY not found in .env file.")
    else:
        genai.configure(api_key=api_key)
        
        print("\n--- Available Models ---")
        model_found = False
        for m in genai.list_models():
            # Check if the model supports the 'generateContent' method
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
                model_found = True
        
        if not model_found:
            print("No models supporting 'generateContent' were found.")
        print("------------------------")

except Exception as e:
    print(f"\nAn error occurred: {e}")