
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Paper
from backend.services.email_service import email_service
from datetime import datetime

# Load real summary
try:
    with open("backend/new_prompt.md", "r") as f:
        real_summary = f.read()
except FileNotFoundError:
    print("Error: backend/new_prompt.md not found. Using fallback.")
    real_summary = "1. **Core Problem**: Fallback summary text.\n2. **Key Innovation**: None."

# Connect to DB
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("Fetching latest papers...")
papers = db.query(Paper).order_by(Paper.published_date.desc()).limit(5).all()

if not papers:
    print("No papers found!")
    sys.exit(1)

# Inject real summary into the first few papers to test interactivity
count = 0
for p in papers:
    # Creating a temporary attribute effectively (Jinja will see it)
    # Since SQLAlchemy objects track state, we rely on the attribute access in template
    # But usually we shouldn't mute DB objects.
    # To be safe, we'll patch the object instance just for this runtime
    p.generated_summary = real_summary
    count += 1

print(f"Prepared {count} papers with AI summaries.")

from backend.config import settings

print(f"Found recipients: {settings.RECIPIENT_LIST}")

for recipient in settings.RECIPIENT_LIST:
    print(f"Sending email to {recipient}...")
    email_service.send_daily_digest(recipient, papers)

print("Done.")
