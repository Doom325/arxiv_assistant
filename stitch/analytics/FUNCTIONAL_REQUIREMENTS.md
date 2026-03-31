# Functional Requirements: Analytics Page

The analytics page is the researcher's observatory -- a data-driven overview of their library's composition, growth trajectory, and most-cited influences. It answers: how is my collection growing, what categories dominate, and which papers are the most referenced?

---

## Domain: Summary Statistics

- REQ-A01: User can see at a glance the total number of papers in the index.
- REQ-A02: User can see today's ingestion count and yesterday's count for comparison.
- REQ-A03: User can see how many library (bookmarked) papers exist.
- REQ-A04: User can see how many distinct arXiv categories are tracked.

## Domain: Charts and Trends

- REQ-A05: User can see a time-series chart of papers ingested per day over a configurable window (default 14 days), with day/week/month granularity toggle.
- REQ-A06: User can see a horizontal bar chart showing paper distribution across arXiv categories over the past 30 days.
- REQ-A07: Charts use warm-palette colors exclusively; no dark backgrounds.

## Domain: Top Citations

- REQ-A08: User can see a ranked list of the most-cited papers in the local library (top 20).
- REQ-A09: Each citation entry shows rank, citation count, title, arXiv ID, category badge, and author line.
- REQ-A10: Papers that exist in the local database are visually distinguished and link to the internal detail page.
- REQ-A11: External papers link to arXiv.
- REQ-A12: User can filter citations by arXiv category and date range.

## Domain: Empty and Loading States

- REQ-A13: While data is loading, the user sees warm-toned skeleton placeholders.
- REQ-A14: When no data is available, the user sees a welcoming empty state with guidance.
