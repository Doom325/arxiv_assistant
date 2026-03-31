
import os
from dotenv import load_dotenv, find_dotenv

print(f"Searching for .env...")
path = find_dotenv()
print(f"Found .env at: {path}")

load_dotenv(path)

print("Check Keys:")
print(f"GEMINI_API_KEY present: {'GEMINI_API_KEY' in os.environ}")
print(f"GOOGLE_API_KEY present: {'GOOGLE_API_KEY' in os.environ}")

# Do NOT print the value for security
