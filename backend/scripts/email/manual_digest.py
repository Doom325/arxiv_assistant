import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from scheduler import send_daily_email_digest
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Manually triggering daily email digest...")
    send_daily_email_digest()
    print("Manual trigger complete.")
