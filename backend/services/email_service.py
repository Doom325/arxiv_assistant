import resend
import logging
import markdown
import re
from jinja2 import Template
from config import settings

logger = logging.getLogger(__name__)

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    def __init__(self):
        self.sender_email = settings.EMAIL_SENDER
        if not settings.RESEND_API_KEY:
            logger.warning("⚠️ RESEND_API_KEY not set! Email sending will fail.")
        else:
            logger.info(f"✅ Email service initialized with Resend (sender: {self.sender_email})")

    def _send(self, to_email: str, subject: str, html: str, text: str) -> tuple[bool, str]:
        """Send email via Resend API."""
        try:
            result = resend.Emails.send({
                "from": f"Arxiv Assistant <{self.sender_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": text,
            })
            logger.info(f"✅ Email sent to {to_email}: {result}")
            return True, "ok"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Email to {to_email} failed: {error_msg}")
            return False, error_msg

    def _get_paper_app_url(self, paper) -> str:
        """Returns the web URL to open the paper in Arxiv Assistant."""
        base_url = settings.FRONTEND_URL.rstrip("/")
        paper_id = getattr(paper, "arxiv_id", None) or getattr(paper, "id", None)
        if paper_id:
            return f"{base_url}/paper/{paper_id}"
        return base_url

    def send_daily_digest(self, user_email: str, papers: list):
        """Sends a daily digest email with the given papers."""
        if not papers:
            logger.info(f"No papers to send to {user_email}")
            return

        subject = f"arXiv Daily Digest - {len(papers)} New Papers"
        text_content = self._generate_text(papers)
        html_content = self._generate_html(papers)

        success, detail = self._send(user_email, subject, html_content, text_content)
        if success:
            logger.info(f"Sent daily digest to {user_email}")
        else:
            logger.error(f"Failed to send daily digest to {user_email}: {detail}")

    def send_paper_summary(self, recipient_email: str, paper) -> tuple[bool, str]:
        """Sends a single paper summary email. Returns (success, detail)."""
        subject = f"📄 {paper.title}"
        app_url = self._get_paper_app_url(paper)

        # Plain text
        summary_text = paper.generated_summary or paper.summary or "No summary available."
        clean_summary = summary_text.replace("**", "").replace("#", "")
        text_content = (
            f"Paper: {paper.title}\n"
            f"Category: {paper.category} | Published: {paper.published_date}\n\n"
            f"Summary:\n{clean_summary}\n\n"
            f"Read in Arxiv Assistant: {app_url}\n"
            f"View on arXiv: {paper.pdf_url}\n\n"
            f"---\nSent by Arxiv Assistant"
        )

        # HTML
        if paper.generated_summary:
            summary_html = markdown.markdown(paper.generated_summary)
        elif paper.summary:
            summary_html = f"<p>{paper.summary}</p>"
        else:
            summary_html = "<p><em>No summary available yet.</em></p>"

        html_content = f"""<!DOCTYPE html>
<html>
<head><style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f3f4f6; margin: 0; padding: 0; }}
    .container {{ max-width: 700px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .header {{ background-color: #4f46e5; color: white; padding: 24px; text-align: center; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 600; }}
    .meta {{ color: #6b7280; font-size: 13px; margin-bottom: 16px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
    .summary {{ font-size: 14px; color: #4b5563; background-color: #f9fafb; padding: 16px; border-radius: 6px; border-left: 4px solid #4f46e5; }}
    .summary strong {{ color: #1f2937; font-weight: 600; }}
    .summary p {{ margin-bottom: 10px; }}
    .actions {{ margin-top: 20px; }}
    .btn {{ display: inline-block; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 500; margin-right: 10px; }}
    .btn-primary {{ background-color: #4f46e5; color: #ffffff !important; }}
    .btn-secondary {{ background-color: #f3f4f6; color: #374151 !important; border: 1px solid #d1d5db; }}
    .footer {{ text-align: center; font-size: 12px; color: #9ca3af; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
</style></head>
<body>
    <div class="container">
        <div class="header"><h1>{paper.title}</h1></div>
        <div class="meta">{paper.category} &bull; {paper.published_date}</div>
        <div class="summary">{summary_html}</div>
        <div class="actions">
            <a href="{app_url}" class="btn btn-primary">Read in Arxiv Assistant &rarr;</a>
            <a href="{paper.pdf_url}" class="btn btn-secondary">View on arXiv</a>
        </div>
        <div class="footer"><p>Sent by Arxiv Assistant</p></div>
    </div>
</body>
</html>"""
        return self._send(recipient_email, subject, html_content, text_content)

    def _parse_summary(self, markdown_text: str) -> dict:
        if not markdown_text:
            return {"teaser": "", "content": ""}
        match = re.search(r"1\.\s*\*\*Core Problem\*\*:(.*?)(?=\n\s*\d+\.\s*\*\*Key Innovation|\Z)", markdown_text, re.DOTALL)
        if match:
            return {'teaser': match.group(1).strip(), 'content': markdown_text}
        return {'teaser': markdown_text[:150] + "...", 'content': markdown_text}

    def _generate_text(self, papers: list) -> str:
        lines = ["arXiv Daily Digest", "Your curated research update", "=" * 30, ""]
        for p in papers:
            app_url = self._get_paper_app_url(p)
            lines.append(f"Title: {p.title}")
            lines.append(f"Category: {p.category} | Date: {p.published_date}")
            lines.append(f"Arxiv Assistant: {app_url}")
            lines.append(f"arXiv Link: {p.pdf_url}")
            if p.generated_summary:
                lines.append(f"\nSummary:\n{p.generated_summary.replace('**', '').replace('#', '')}")
            else:
                lines.append(f"\nAbstract:\n{p.summary[:300]}...")
            lines.append("-" * 30 + "\n")
        lines.append("\nSent by Arxiv Assistant")
        return "\n".join(lines)

    def _generate_html(self, papers: list) -> str:
        template_str = """<!DOCTYPE html>
<html><head><style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f3f4f6; margin: 0; padding: 0; }
    .container { max-width: 1000px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; }
    .header { background-color: #4f46e5; color: white; padding: 24px; text-align: center; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }
    .header h1 { margin: 0; font-size: 24px; } .header p { margin: 5px 0 0 0; opacity: 0.9; font-size: 15px; }
    .paper { border: 1px solid #e5e7eb; padding: 20px; margin-bottom: 24px; border-radius: 8px; }
    .title { color: #111827; font-size: 18px; font-weight: 700; text-decoration: none; display: block; margin-bottom: 8px; }
    .title:hover { color: #4f46e5; text-decoration: underline; }
    .meta { color: #6b7280; font-size: 13px; margin-bottom: 16px; font-weight: 500; text-transform: uppercase; }
    .ai-summary { background-color: #f9fafb; padding: 16px; border-radius: 6px; border-left: 4px solid #4f46e5; margin-top: 10px; }
    .badge { background-color: #4f46e5; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; text-transform: uppercase; font-weight: bold; }
    .actions { margin-top: 16px; }
    .btn { display: inline-block; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 500; margin-right: 10px; margin-top: 4px; }
    .btn-primary { background-color: #4f46e5; color: #ffffff !important; }
    .btn-secondary { background-color: #f3f4f6; color: #374151 !important; border: 1px solid #d1d5db; }
    .footer { text-align: center; font-size: 12px; color: #9ca3af; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 20px; }
</style></head>
<body><div class="container">
    <div class="header"><h1>arXiv Daily Digest</h1><p>Your curated research update</p></div>
    {% for paper in papers %}
    <div class="paper">
        <a href="{{ app_url(paper) }}" class="title">{{ paper.title }}</a>
        <div class="meta">{{ paper.category }} • {{ paper.published_date }}</div>
        <div class="summary">
            {% if paper.generated_summary %}
                {% set parts = parse_func(paper.generated_summary) %}
                <div class="ai-summary">
                    <span class="badge">AI Insight</span>
                    <div>{{ md(parts.content) | safe }}</div>
                </div>
            {% else %}
                <p>{{ paper.summary[:400] }}...</p>
            {% endif %}
        </div>
        <div class="actions">
            <a href="{{ app_url(paper) }}" class="btn btn-primary">Read in Arxiv Assistant &rarr;</a>
            <a href="{{ paper.pdf_url }}" class="btn btn-secondary">View on arXiv</a>
        </div>
    </div>
    {% endfor %}
    <div class="footer"><p>Sent by Arxiv Assistant</p></div>
</div></body></html>"""
        template = Template(template_str)
        return template.render(
            papers=papers,
            md=markdown.markdown,
            parse_func=self._parse_summary,
            app_url=self._get_paper_app_url,
        )


email_service = EmailService()
