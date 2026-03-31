import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.email_service import email_service
from models import Paper
from datetime import date

# Mock paper object
paper = Paper(
    arxiv_id="1234.5678",
    title="Test Paper: AI in 2025",
    summary="This is a test summary of the paper. It discusses the future of AI.",
    published_date=date.today(),
    category="cs.AI",
    pdf_url="http://arxiv.org/pdf/1234.5678"
)

# Send test email
# REPLACE WITH YOUR EMAIL FOR TESTING
test_email = "sumanth.gttpt@gmail.com" 
print(f"Sending test email to {test_email}...")
email_service.send_daily_digest(test_email, [paper])
print("Done.")
