import arxiv
import logging
import requests
import os
from datetime import date
from typing import Iterator

import time
from config import settings
from core.pdf_utils import extract_text_from_pdf
from poll_constants import POLL_SAFETY_CAP

logger = logging.getLogger(__name__)

class ArxivService:
    def __init__(self):
        # arXiv TOS: ≥3s between requests, single connection. page_size is
        # the per-HTTP-call result count; the API caps it at 2000. Larger
        # pages amortize the 3s delay over more papers (~16x speed-up vs
        # the prior 100 for multi-thousand-paper queries).
        self.client = arxiv.Client(
            page_size=2000,
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

    def fetch_papers_since(
        self,
        category: str,
        since_date: date,
        until_date: date | None = None,
        safety_cap: int = POLL_SAFETY_CAP,
        descending: bool = False,
    ) -> Iterator[dict]:
        """Yield papers in ``category`` with ``submittedDate`` in
        ``[since_date, until_date]`` inclusive. If ``until_date`` is omitted,
        the upper bound is open (``*``) — matches the daily-poll usage.

        Uses arXiv's ``submittedDate`` range query. By default iterates oldest
        → newest so daily-poll callers can track a running high-water mark
        as they consume the stream. Set ``descending=True`` for backfill use
        cases where the most recent papers should land first (so an
        interrupted run keeps the most relevant results). Papers are yielded
        as dicts in the same shape as :meth:`fetch_papers`. This is a
        generator — it does not materialise the full result list.

        ``safety_cap`` is a hard ceiling to guard against runaway loops from
        malformed queries or a pathological date range. Under normal operation
        (daily poll, a handful of categories) we expect at most a few hundred
        results per category per call.
        """
        since_str = since_date.strftime("%Y%m%d0000")
        until_str = until_date.strftime("%Y%m%d2359") if until_date else "*"
        query = (
            f"cat:{category} AND "
            f"submittedDate:[{since_str} TO {until_str}]"
        )
        search = arxiv.Search(
            query=query,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=(
                arxiv.SortOrder.Descending
                if descending
                else arxiv.SortOrder.Ascending
            ),
        )
        count = 0
        for result in self.client.results(search):
            if count >= safety_cap:
                logger.warning(
                    "fetch_papers_since hit safety_cap=%d for "
                    "category=%s since=%s — stopping early",
                    safety_cap, category, since_date,
                )
                break
            count += 1
            yield {
                "arxiv_id": result.entry_id.split('/')[-1],
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published_date": result.published,
                "updated_date": result.updated,
                "pdf_url": result.pdf_url,
                "category": result.primary_category,
            }

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
