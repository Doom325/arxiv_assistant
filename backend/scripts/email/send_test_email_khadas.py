import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from models import Paper
from services.email_service import email_service
from datetime import datetime
from database import SessionLocal
from config import settings

print("Fetching latest papers from DB...")
db = SessionLocal()
try:
    papers = db.query(Paper).order_by(Paper.published_date.desc()).limit(5).all()

    if not papers:
        print("No papers found in DB!")
        sys.exit(1)

    # Use a dummy summary if generated_summary is missing
    for p in papers:
        if not p.generated_summary:
            p.generated_summary = "1. **Core Problem**: Test summary.\n2. **Key Innovation**: Manual test."
    
    print(f"Prepared {len(papers)} papers for testing.")
    print(f"Found recipients: {settings.RECIPIENT_LIST}")

    for recipient in settings.RECIPIENT_LIST:
        print(f"Sending email to {recipient}...")
        email_service.send_daily_digest(recipient, papers)
        
    print("Test email script completed successfully.")
finally:
    db.close()
