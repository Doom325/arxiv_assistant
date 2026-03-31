import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import google.generativeai as genai
import os
from config import settings

print(f"Key: {settings.FINAL_GOOGLE_API_KEY[:5]}...")
genai.configure(api_key=settings.FINAL_GOOGLE_API_KEY)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(e)
