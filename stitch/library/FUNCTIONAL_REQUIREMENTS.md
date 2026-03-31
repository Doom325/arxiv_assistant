# Functional Requirements: Library / Bookmarks Page

## Core Browsing
- **REQ-L01** View all bookmarked papers in a responsive grid (1/2/3 columns)
- **REQ-L02** Filter papers by list membership (All, or specific list)
- **REQ-L03** Sort papers by: date added (asc/desc), published date (asc/desc), title (A-Z/Z-A)
- **REQ-L04** Each paper card shows: category, title, abstract snippet, reading time, list badges

## List Management
- **REQ-L05** Create a new list (inline input, Enter to confirm, Escape to cancel)
- **REQ-L06** Delete a list (with confirmation dialog)
- **REQ-L07** List selector as horizontal pill tabs (All + custom lists)
- **REQ-L08** Show list membership badges on each paper card

## Paper Actions
- **REQ-L09** Navigate to paper detail page from card
- **REQ-L10** Toggle bookmark / manage list membership via BookmarkButton
- **REQ-L11** Add paper to reading queue

## Export
- **REQ-L12** Export selected list to Google Drive
- **REQ-L13** Google Drive OAuth flow: show auth URL, accept code, verify
- **REQ-L14** Export status feedback (success/error messages)

## States
- **REQ-L15** Loading state with warm skeleton/spinner
- **REQ-L16** Empty state (no bookmarks) with editorial serif pattern + CTA
- **REQ-L17** Empty list state (selected list has no papers)
