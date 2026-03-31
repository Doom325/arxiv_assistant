"""Tests for routers/integrations.py — summarize, email, GDrive endpoints."""


class TestEmailDebug:
    def test_email_debug_returns_config(self, client):
        response = client.get("/papers/email/debug")
        assert response.status_code == 200
        data = response.json()
        assert "resend_installed" in data
        assert "resend_api_key_set" in data
        assert "email_sender" in data


class TestSummarizePaper:
    def test_summarize_paper_not_found(self, client):
        response = client.post("/papers/999999/summarize")
        assert response.status_code == 404
        assert response.json()["detail"] == "Paper not found"


class TestEmailPaper:
    def test_email_paper_not_found(self, client):
        response = client.post("/papers/999999/email")
        assert response.status_code == 404
        assert response.json()["detail"] == "Paper not found"
