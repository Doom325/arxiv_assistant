# Feature Ideas — arxiv_assistant

Brainstormed 2026-03-19. Ranked by estimated impact.

---

## 1. Paper Comparison View

Select 2-3 papers and get a side-by-side comparison: methodology differences, shared citations, complementary findings. Researchers constantly evaluate which approach to follow.

**Implementation notes:**
- Add multi-select UI on dashboard/bookmarks (checkbox mode)
- New `/compare` page with columnar layout
- Backend endpoint that takes paper IDs, fetches full text, and generates structured comparison via Gemini
- Leverage existing entity extraction to highlight shared/unique datasets, models, metrics

---

## 2. Reading Queue with Priority Scoring

Auto-rank unread bookmarked papers by relevance to your past reading history (using embedding similarity to papers you've already summarized). Surface "you should read this next."

**Implementation notes:**
- Compute average embedding of summarized/read papers as a "user interest vector"
- Score unread bookmarks by cosine similarity to this vector
- New "Up Next" section on dashboard or sidebar
- Re-score on each new bookmark or completed summary

---

## 3. Citation Alert Monitoring

Track specific papers and notify when new papers cite them. "Paper X you bookmarked was cited by 3 new papers this week." Requires periodic re-crawling of citation data.

**Implementation notes:**
- New `WatchedPaper` model with user + paper + last_checked
- Scheduler job: for each watched paper, search recent ingested papers' citation links for matches
- Notification via email digest or in-app notification badge
- UI: "Watch" toggle button on paper detail and peek sheet

---

## 4. Research Gap Finder

Given a topic query, analyze the cluster of related papers and identify what's NOT being addressed. Use the citation graph + entity extraction to find under-explored intersections.

**Example:** "LoRA + legal domain has only 2 papers"

**Implementation notes:**
- Semantic search to find paper cluster for a topic
- Extract entity co-occurrence matrix (e.g., method x domain)
- Identify sparse cells in the matrix as potential gaps
- LLM prompt to synthesize findings into a research gap summary
- New `/research-gaps` page or section in research page

---

## 5. Paper Timeline / Evolution View

For a topic, show how ideas evolved over time: which paper introduced a concept, who extended it, where it forked. Leverage the citation graph + published dates to build a visual lineage.

**Implementation notes:**
- Query: semantic search for topic -> get paper cluster
- Build subgraph from citation links within the cluster
- Sort by published_date, identify root/seminal papers (most cited, earliest)
- Visualize as horizontal timeline with branching (D3.js or react-flow)
- New `/timeline` page with topic search input

---

## 6. Smart Collections with Auto-Tagging

Auto-suggest which list a bookmarked paper belongs to based on its embedding similarity to existing list contents. "This paper looks like it belongs in your RAG list."

**Implementation notes:**
- Compute centroid embedding per bookmark list
- On new bookmark (default "Bookmarks" list), compare paper embedding to each list centroid
- Suggest top 2-3 matching lists in the bookmark dropdown
- Could also run as batch job to suggest re-organization of existing bookmarks
- Low effort: just add similarity scoring to existing BookmarkButton menu

---

## 7. Weekly Research Digest with Trends

Upgrade the daily email from "here are yesterday's papers" to a weekly summary: trending topics, breakthrough papers (high early citations), papers similar to your bookmarks, and category shifts.

**Implementation notes:**
- New scheduler job (weekly, e.g., Monday 8 AM IST)
- Aggregate stats: papers per category this week vs last week (trend detection)
- Find papers most similar to user's bookmarks (embedding search)
- Identify "breakout" papers: high citation count relative to age
- Rich HTML email template with sections for each insight
- Extend existing email_service and email templates

---

## 8. Collaborative Annotations

Add notes/highlights to papers that persist across sessions. Tag sections as "key finding", "methodology", "limitation". Export annotated bibliography for writing.

**Implementation notes:**
- New `PaperAnnotation` model: user, paper, section, text, tag, created_at
- UI: annotation sidebar on paper detail page
- Predefined tags: Key Finding, Methodology, Limitation, Future Work, Dataset, Result
- Free-text notes per annotation
- Export as BibTeX with annotation comments, or markdown bibliography
- Could integrate with the existing Google Drive export

---

## 9. "Explain This Paper" Chat Mode

Instead of RAG over the whole library, focus chat on a single paper: "Explain the loss function in section 3", "What are the limitations?", "How does this compare to [other paper]?" using the full extracted PDF text.

**Implementation notes:**
- New chat mode toggle: "Library Chat" vs "Paper Chat"
- Paper Chat: pass full extracted text (abstract + introduction + sections) as context
- Pre-populate with suggested questions: "Summarize key contributions", "What datasets were used?", "Explain the methodology"
- Could add to the peek sheet or paper detail page as an inline chat
- Backend: new endpoint or parameter on existing chat endpoint to scope context to single paper

---

## 10. Reproducibility Checker

For papers with extracted entities (datasets, models, hardware), cross-reference with other papers using the same setup. Flag if a paper's claimed results are an outlier compared to similar configurations.

**Implementation notes:**
- Query papers sharing same dataset + task entities
- Extract reported metrics (accuracy, F1, etc.) from summaries or full text via LLM
- Build comparison table: paper, model, dataset, reported metric
- Flag outliers (>2 std dev from mean) or missing baselines
- New section on paper detail page: "How does this compare?"
- Requires good entity extraction coverage (GLiNER already extracts Dataset, Model, Metric, Task)

---

## Priority Matrix

| Idea | Impact | Effort | Feasibility with current infra |
|------|--------|--------|-------------------------------|
| 1. Paper Comparison | High | Medium | High — embeddings + Gemini exist |
| 2. Reading Queue | High | Low | High — embeddings + bookmarks exist |
| 3. Citation Alerts | High | Medium | High — citation graph exists |
| 4. Research Gap Finder | High | High | Medium — needs entity co-occurrence |
| 5. Paper Timeline | Medium | High | Medium — needs graph visualization |
| 6. Smart Auto-Tagging | Medium | Low | High — embeddings + lists exist |
| 7. Weekly Digest | Medium | Medium | High — email + analytics exist |
| 8. Annotations | Medium | Medium | Medium — new model + UI needed |
| 9. Single-Paper Chat | High | Low | High — chat + PDF text exist |
| 10. Reproducibility | Medium | High | Medium — needs metric extraction |

**Recommended first picks:** #9 (single-paper chat), #6 (auto-tagging), #2 (reading queue) — highest impact-to-effort ratio given existing infrastructure.
