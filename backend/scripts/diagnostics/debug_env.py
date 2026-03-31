
import sys
import os
sys.path.append(os.getcwd())
try:
    from backend.config import settings
    print(f"SENDER: {settings.EMAIL_SENDER}")
    print(f"RECIPIENTS: {settings.EMAIL_RECIPIENTS}")
    print(f"PASSWORD LENGTH: {len(settings.EMAIL_PASSWORD)}")
    print(f"PASSWORD START: {settings.EMAIL_PASSWORD[:2]}***")
    print(f"SMTP: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
    
    # Check if .env exists in CWD
    print(f"CWD: {os.getcwd()}")
    print(f"Root .env exists: {os.path.exists('.env')}")
    print(f"Backend .env exists: {os.path.exists('backend/.env')}")
except Exception as e:
    print(f"Error: {e}")
