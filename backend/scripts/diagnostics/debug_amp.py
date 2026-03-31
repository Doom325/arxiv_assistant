
import sys
import os
sys.path.append(os.getcwd())

from backend.services.email_service import email_service
from backend.models import Paper
from datetime import date

# Mock data
papers = [
    Paper(
        title="Attention Is All You Need",
        arxiv_id="1706.03762",
        category="cs.CL",
        published_date=date(2017, 6, 12),
        summary="Standard abstract...",
        generated_summary="""1. **Core Problem**: Recurrent models are slow.
2. **Key Innovation**: Attention mechanism only.
3. **Methodology**: Transformer architecture.
4. **Key Results**: SOTA translation.""",
        pdf_url="http://example.com/pdf"
    )
]

try:
    amp_content = email_service._generate_amp_html(papers)
    with open("backend/debug_amp.html", "w") as f:
        f.write(amp_content)
    print("AMP content written to backend/debug_amp.html")
except Exception as e:
    print(f"Error: {e}")
