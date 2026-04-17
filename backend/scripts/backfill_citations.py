#!/usr/bin/env python3
"""
Backfill citations by scanning PDFs on disk and processing them with GROBID.

Disk-driven, not DB-driven: iterates every PDF in PDF_SAVE_DIR, derives the
arxiv_id from the filename, looks up the paper in the DB, and writes GROBID
citations + citation links. Skips papers that already have citations unless
--overwrite is set.

This avoids all the complexity of date filters, download checks, and
full_text_sections dependencies. If the PDF exists, it gets processed.

Usage:
    # Process all PDFs on disk (skip papers that already have citations):
    python scripts/backfill_citations.py --workers 6

    # Overwrite existing citations (e.g. replace old LLM output with GROBID):
    python scripts/backfill_citations.py --workers 6 --overwrite

    # Dry run (count what would be processed):
    python scripts/backfill_citations.py --dry-run

    # Limit to N papers (useful for testing):
    python scripts/backfill_citations.py --limit 100 --workers 6
"""

import argparse
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add backend root to path so services can be imported
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from database import SessionLocal
from models import Paper
from config import settings
from services.grobid_service import extract_references_from_pdf, is_alive
from services.citation_service import resolve_citations

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

PDF_DIR = settings.PDF_SAVE_DIR


def scan_pdfs() -> list[dict]:
    """Scan PDF_DIR for all .pdf files. Returns list of {arxiv_id, pdf_path}
    sorted by arxiv_id descending (newest first, since IDs are YYMM.NNNNN)."""
    pdfs = []
    for fname in os.listdir(PDF_DIR):
        if not fname.endswith(".pdf"):
            continue
        arxiv_id = fname[:-4]  # strip .pdf
        pdfs.append({"arxiv_id": arxiv_id, "pdf_path": os.path.join(PDF_DIR, fname)})
    # Sort descending by arxiv_id (YYMM.NNNNN — lexicographic = chronological)
    pdfs.sort(key=lambda x: x["arxiv_id"], reverse=True)
    return pdfs


def filter_needing_citations(pdf_list: list[dict], overwrite: bool) -> list[dict]:
    """Filter to papers that exist in the DB and need citations.

    With overwrite=False: skip papers where citations IS NOT NULL and non-empty.
    With overwrite=True: process all papers that exist in the DB.

    Returns the filtered list with paper DB id added.
    """
    db = SessionLocal()
    try:
        # Batch-fetch all arxiv_ids that exist in DB, with their citation status
        arxiv_ids = [p["arxiv_id"] for p in pdf_list]

        # Process in batches of 1000 to avoid huge IN clauses
        db_info: dict[str, dict] = {}
        batch_size = 1000
        for i in range(0, len(arxiv_ids), batch_size):
            batch = arxiv_ids[i:i + batch_size]
            rows = db.query(Paper.id, Paper.arxiv_id, Paper.citations).filter(
                Paper.arxiv_id.in_(batch)
            ).all()
            for paper_id, arxiv_id, citations in rows:
                has_cits = citations is not None and len(citations) > 0 if isinstance(citations, list) else citations is not None
                db_info[arxiv_id] = {"id": paper_id, "has_citations": has_cits}

        result = []
        n_not_in_db = 0
        n_already_has = 0
        for p in pdf_list:
            info = db_info.get(p["arxiv_id"])
            if info is None:
                n_not_in_db += 1
                continue
            if not overwrite and info["has_citations"]:
                n_already_has += 1
                continue
            result.append({**p, "id": info["id"]})

        logger.info(f"Filter: {len(pdf_list)} PDFs on disk → {len(result)} to process "
                     f"({n_not_in_db} not in DB, {n_already_has} already have citations)")
        return result
    finally:
        db.close()


def process_one(paper_info: dict) -> dict:
    """Process a single PDF: GROBID → DB. Uses its own DB session for
    thread safety."""
    paper_id = paper_info["id"]
    arxiv_id = paper_info["arxiv_id"]
    pdf_path = paper_info["pdf_path"]
    result = {"arxiv_id": arxiv_id, "status": "unknown", "n_citations": 0, "wall_sec": 0}

    db = SessionLocal()
    try:
        wall_start = time.time()
        citations = extract_references_from_pdf(pdf_path)
        wall_sec = time.time() - wall_start

        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            result["status"] = "skip_not_found"
            return result

        paper.citations = citations
        db.commit()

        n_links = resolve_citations(paper, citations, db)

        result["status"] = "ok"
        result["n_citations"] = len(citations)
        result["n_links"] = n_links
        result["wall_sec"] = round(wall_sec, 2)
        return result
    except Exception as e:
        db.rollback()
        result["status"] = f"error: {type(e).__name__}: {e}"
        logger.error(f"{arxiv_id}: {result['status']}")
        return result
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill citations from PDFs on disk using GROBID")
    parser.add_argument("--workers", type=int, default=6, help="Number of papers to process concurrently (default: 6)")
    parser.add_argument("--overwrite", action="store_true", help="Re-extract even for papers that already have citations")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N papers (0 = no limit)")
    parser.add_argument("--dry-run", action="store_true", help="Count candidates without processing")
    args = parser.parse_args()

    logger.info(f"GROBID URL:  {settings.GROBID_URL}")
    logger.info(f"PDF dir:     {PDF_DIR}")
    logger.info(f"Workers:     {args.workers}")
    logger.info(f"Overwrite:   {args.overwrite}")

    # Step 1: Scan disk
    logger.info("Scanning PDF directory...")
    all_pdfs = scan_pdfs()
    logger.info(f"Found {len(all_pdfs)} PDFs on disk")

    # Step 2: Filter to papers needing citations
    logger.info("Checking DB for papers needing citations...")
    candidates = filter_needing_citations(all_pdfs, overwrite=args.overwrite)

    if args.limit > 0:
        candidates = candidates[:args.limit]
        logger.info(f"Limited to {len(candidates)} papers (--limit {args.limit})")

    if not candidates:
        logger.info("Nothing to do.")
        return

    if args.dry_run:
        logger.info(f"Dry run: {len(candidates)} papers would be processed.")
        logger.info(f"  First 5: {[c['arxiv_id'] for c in candidates[:5]]}")
        logger.info(f"  Last 5:  {[c['arxiv_id'] for c in candidates[-5:]]}")
        return

    # Step 3: Health check
    if not is_alive():
        logger.error(f"GROBID is not reachable at {settings.GROBID_URL}. "
                     "Start it with: docker compose up -d grobid")
        sys.exit(1)
    logger.info("GROBID is alive ✓")

    # Step 4: Process
    results: list[dict] = []
    total_start = time.time()
    n_total = len(candidates)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_one, c): c for c in candidates}
        for i, future in enumerate(as_completed(futures), 1):
            r = future.result()
            results.append(r)
            status = r["status"]
            if status == "ok":
                if i % 100 == 0 or i == n_total:
                    elapsed = time.time() - total_start
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (n_total - i) / rate if rate > 0 else 0
                    logger.info(f"[{i}/{n_total}] {r['arxiv_id']}  "
                                f"cits={r['n_citations']}  {r['wall_sec']}s  "
                                f"({rate:.1f} papers/s, ETA {eta/60:.0f}m)")
            else:
                logger.warning(f"[{i}/{n_total}] {r['arxiv_id']}  {status}")

    total_wall = time.time() - total_start
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_skip = sum(1 for r in results if r["status"].startswith("skip"))
    n_err = sum(1 for r in results if r["status"].startswith("error"))
    total_cits = sum(r["n_citations"] for r in results)

    logger.info(f"\n{'=' * 50}")
    logger.info(f"Backfill complete")
    logger.info(f"  OK:       {n_ok}")
    logger.info(f"  Skipped:  {n_skip}")
    logger.info(f"  Errors:   {n_err}")
    logger.info(f"  Total citations extracted: {total_cits:,}")
    logger.info(f"  Mean cits/paper:  {total_cits / n_ok:.1f}" if n_ok else "  (no successful papers)")
    logger.info(f"  Throughput: {n_ok / total_wall:.1f} papers/s")
    logger.info(f"  Wall time: {total_wall:.1f}s ({total_wall / 60:.1f} min)")


if __name__ == "__main__":
    main()
