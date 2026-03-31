# Functional Requirements: Paper Detail Page

## Data Display
- **REQ-P01** Display paper title, abstract, publication date, arXiv ID, and categories
- **REQ-P02** Render abstract with full markdown + LaTeX math support (remark-gfm, remark-math, rehype-katex)
- **REQ-P03** Display reading time estimate derived from abstract word count

## AI Analysis
- **REQ-P04** Trigger AI summary generation (calls `/papers/{id}/summarize`)
- **REQ-P05** Show generation progress indicator while polling (3s interval, 180s timeout)
- **REQ-P06** Render AI summary as markdown when available
- **REQ-P07** Support regenerating an existing analysis (force=true)
- **REQ-P08** Browser notification on summary completion

## Bookmarking & Actions
- **REQ-P09** Toggle bookmark state (add/remove from library)
- **REQ-P10** Email paper summary to configured recipients
- **REQ-P11** Email status feedback (idle → sending → sent/error → idle after 3s)
- **REQ-P12** Link to paper PDF in new tab
- **REQ-P13** Link to timeline view for this paper

## References & Citations
- **REQ-P14** Display all extracted citations with title, authors, raw text
- **REQ-P15** Link resolved citations to their paper detail page
- **REQ-P16** Show "Available locally" indicator for resolved citations
- **REQ-P17** External link button for citations with URLs

## Pattern Classification
- **REQ-P18** Display detected agentic patterns with confidence scores
- **REQ-P19** Show confidence bar visualization per pattern
- **REQ-P20** Agentic/Non-Agentic badge
- **REQ-P21** Collapsible Chain-of-Thought reasoning section
- **REQ-P22** Link to Pattern Library page

## Recommended Research
- **REQ-P23** Display similar papers in a 2-column grid
- **REQ-P24** Each recommendation card shows category, title, date, reading time

## Navigation
- **REQ-P25** Back link to previous page (queue or dashboard)
- **REQ-P26** Sticky table of contents sidebar on wide screens (xl+)

## States
- **REQ-P27** Loading state with skeleton/spinner
- **REQ-P28** Paper not found state with back link
- **REQ-P29** Empty AI analysis state with generation CTA
