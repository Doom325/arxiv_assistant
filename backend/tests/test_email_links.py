from datetime import date
from unittest.mock import patch
from models import Paper
from services.email_service import email_service
from config import settings


def test_paper_app_url_resolution():
    paper_with_arxiv_id = Paper(
        id=42,
        arxiv_id="2403.12345",
        title="Test Paper",
        summary="Abstract test",
        published_date=date(2025, 1, 1),
        category="cs.AI",
        pdf_url="https://arxiv.org/pdf/2403.12345.pdf",
    )
    url = email_service._get_paper_app_url(paper_with_arxiv_id)
    assert url == f"{settings.FRONTEND_URL.rstrip('/')}/paper/2403.12345"

    paper_with_id_only = Paper(
        id=99,
        arxiv_id=None,
        title="Test Paper 2",
        summary="Abstract test 2",
        published_date=date(2025, 1, 1),
        category="cs.AI",
        pdf_url="https://arxiv.org/pdf/99.pdf",
    )
    url_id = email_service._get_paper_app_url(paper_with_id_only)
    assert url_id == f"{settings.FRONTEND_URL.rstrip('/')}/paper/99"


def test_generate_text_includes_both_links():
    paper = Paper(
        id=1,
        arxiv_id="2501.00001",
        title="Deep Reasoning with LLMs",
        summary="An in-depth study of reasoning in LLMs.",
        published_date=date(2025, 1, 15),
        category="cs.AI",
        pdf_url="https://arxiv.org/pdf/2501.00001.pdf",
    )

    text = email_service._generate_text([paper])
    assert f"Arxiv Assistant: {settings.FRONTEND_URL.rstrip('/')}/paper/2501.00001" in text
    assert "arXiv Link: https://arxiv.org/pdf/2501.00001.pdf" in text
    assert "Title: Deep Reasoning with LLMs" in text


def test_generate_html_includes_both_links():
    paper = Paper(
        id=2,
        arxiv_id="2501.00002",
        title="Agentic Workflow Optimization",
        summary="Workflow optimization techniques.",
        generated_summary="1. **Core Problem**: Slow workflows.\n2. **Key Innovation**: New scheduler.",
        published_date=date(2025, 1, 16),
        category="cs.AI",
        pdf_url="https://arxiv.org/pdf/2501.00002.pdf",
    )

    html = email_service._generate_html([paper])
    expected_app_url = f"{settings.FRONTEND_URL.rstrip('/')}/paper/2501.00002"

    # Title links to app
    assert f'href="{expected_app_url}" class="title"' in html
    # Primary button links to app
    assert f'href="{expected_app_url}" class="btn btn-primary"' in html
    assert "Read in Arxiv Assistant" in html
    # Secondary button links to arXiv
    assert 'href="https://arxiv.org/pdf/2501.00002.pdf" class="btn btn-secondary"' in html
    assert "View on arXiv" in html


def test_send_paper_summary_includes_both_links():
    paper = Paper(
        id=3,
        arxiv_id="2501.00003",
        title="Single Paper Summary",
        summary="Summary test.",
        published_date=date(2025, 1, 17),
        category="cs.AI",
        pdf_url="https://arxiv.org/pdf/2501.00003.pdf",
    )

    with patch.object(email_service, "_send", return_value=(True, "ok")) as mock_send:
        email_service.send_paper_summary("user@example.com", paper)

        assert mock_send.called
        args, _ = mock_send.call_args
        to_email, subject, html_content, text_content = args

        assert to_email == "user@example.com"
        expected_app_url = f"{settings.FRONTEND_URL.rstrip('/')}/paper/2501.00003"
        assert expected_app_url in html_content
        assert "https://arxiv.org/pdf/2501.00003.pdf" in html_content
        assert expected_app_url in text_content
        assert "https://arxiv.org/pdf/2501.00003.pdf" in text_content
