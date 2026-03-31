import arxiv
import requests
import os
from datetime import datetime, timedelta

import time
from config import settings
from core.pdf_utils import extract_text_from_pdf

class ArxivService:
    def __init__(self):
        # arXiv API requires 3 seconds between requests
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3,
            num_retries=3
        )

    def fetch_papers(self, query: str = "cat:cs.AI", max_results: int = 10):
        """
        Fetches papers from arXiv based on the query.
        """
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = []
        # Use the client to iterate results to ensure rate limiting is respected
        for result in self.client.results(search):
            results.append({
                "arxiv_id": result.entry_id.split('/')[-1],
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published_date": result.published,
                "updated_date": result.updated,
                "pdf_url": result.pdf_url,
                "category": result.primary_category
            })
        return results

    def get_paper_by_id(self, arxiv_id: str):
        """
        Fetches a single paper by its arXiv ID.
        """
        search = arxiv.Search(id_list=[arxiv_id])
        try:
            results = list(self.client.results(search))
            if not results:
                return None
            
            result = results[0]
            return {
                "arxiv_id": result.entry_id.split('/')[-1],
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published_date": result.published,
                "updated_date": result.updated,
                "pdf_url": result.pdf_url,
                "category": result.primary_category
            }
        except Exception as e:
            print(f"Error fetching paper {arxiv_id}: {e}")
            return None

    def download_pdf(self, pdf_url: str, save_path: str):
        """
        Downloads the PDF from the given URL.
        """
        # Respect arXiv's rate limit for PDF downloads too
        time.sleep(3)
        
        headers = {
            "User-Agent": f"arXiv-AI-Assistant/1.0 (mailto:{settings.EMAIL_SENDER})"
        }
        
        try:
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            print(f"Error downloading PDF {pdf_url}: {e}")
            raise

    def extract_text(self, pdf_path: str) -> str:
        """Extracts text from a PDF file. Delegates to core.pdf_utils."""
        return extract_text_from_pdf(pdf_path)

arxiv_service = ArxivService()
