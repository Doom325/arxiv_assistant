# Reading Queue with Priority Scoring — Detailed Brainstorm

## Problem Statement

Researchers bookmark papers but have no guidance on what to read next. The current library is a flat list sorted by date or name — it doesn't account for relevance to the user's interests, paper importance, or reading urgency. Papers pile up and the most valuable ones get buried.

**Goal:** Automatically rank unread bookmarked papers by relevance to the user's research interests, paper impact, and freshness. Surface a prioritized "Up Next" queue.

---

## Core Concept

Build a **user interest profile** from papers the user has already engaged with (summarized, bookmarked, chatted about), then score every unread bookmarked paper against that profile. Combine with signals like citation impact, freshness, and category alignment to produce a single priority score.

---

## Scoring Algorithm Design

### Input Signals

| Signal | Source | Weight | Rationale |
|--------|--------|--------|-----------|
| **Interest Similarity** | Cosine similarity of paper embedding vs user interest vector | 0.35 | Core relevance signal |
| **Citation Impact** | Count of papers citing this one (from CitationLink table) | 0.20 | Community-validated importance |
| **Freshness** | Days since publication (decay function) | 0.15 | Newer papers more actionable |
| **Category Alignment** | Match with user's most-bookmarked categories | 0.10 | Topical relevance |
| **Entity Overlap** | Shared entities (models, datasets, tasks) with user's read papers | 0.10 | Methodological relevance |
| **Peer Reads** | How many papers in user's library cite this paper | 0.10 | "Missing link" signal |

### User Interest Vector

**Construction:**
- Take all papers the user has "engaged" with (defined below)
- Average their embeddings (768D from `Paper.embedding` column)
- Weight recent engagements higher (exponential decay, half-life = 30 days)
- This produces a single 768D vector representing the user's current research focus

**What counts as "engaged":**
1. Paper has `generated_summary` (user triggered analysis)
2. Paper was explicitly bookmarked (exists in UserLibrary)
3. Paper was discussed in RAG chat (future: track chat context papers)
4. Paper was viewed for >30 seconds (future: interaction tracking)

### Freshness Decay Function

```
freshness_score = exp(-0.03 * days_since_publication)
```
- Paper from today: 1.0
- Paper from 1 week ago: 0.81
- Paper from 1 month ago: 0.41
- Paper from 3 months ago: 0.07

### Category Alignment Score

```
category_score = count(papers_in_same_category_in_library) / total_library_papers
```
Normalized so the user's most-bookmarked category gets score 1.0.

### Entity Overlap Score

```
entity_overlap = |paper_entities ∩ user_entity_set| / |paper_entities|
```
Where `user_entity_set` = all entities extracted from user's read papers.

### Final Score

```
priority = (0.35 * interest_similarity) +
           (0.20 * normalized_citation_count) +
           (0.15 * freshness_score) +
           (0.10 * category_alignment) +
           (0.10 * entity_overlap) +
           (0.10 * peer_reads_score)
```

All individual scores normalized to [0, 1] before combining.

---

## Backend Design

### New Database Models

#### Option A: Extend UserLibrary (Simpler)

Add columns to existing `UserLibrary` model:

```python
# In models/user.py — UserLibrary additions
priority_score = Column(Float, nullable=True, default=None)
read_status = Column(String, default="unread")  # unread, reading, read, skipped
last_scored_at = Column(DateTime, nullable=True)
manual_priority = Column(Integer, nullable=True)  # user override: 1=low, 2=med, 3=high
```

**Pros:** No new tables, simpler queries, works with existing library endpoints.
**Cons:** Mixes queue logic with bookmark logic, migration needed on existing table.

#### Option B: New ReadingQueue Table (Cleaner)

```python
class ReadingQueue(Base):
    __tablename__ = "reading_queue"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)

    # Scoring
    priority_score = Column(Float, default=0.0)
    interest_similarity = Column(Float, nullable=True)
    citation_impact = Column(Float, nullable=True)
    freshness_score = Column(Float, nullable=True)
    category_score = Column(Float, nullable=True)
    entity_overlap = Column(Float, nullable=True)
    peer_reads_score = Column(Float, nullable=True)

    # Status
    read_status = Column(String, default="unread")  # unread, reading, read, skipped
    manual_priority = Column(Integer, nullable=True)  # user override

    # Metadata
    added_at = Column(DateTime, default=func.now())
    scored_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    paper = relationship("Paper")
```

**Pros:** Clean separation, can store individual scoring components for transparency, easy to drop/rebuild.
**Cons:** Additional table, needs sync with UserLibrary (when user bookmarks, auto-add to queue).

**Recommendation:** Option B — cleaner, allows storing scoring breakdown for the "why is this ranked here?" UI feature.

#### User Interest Profile (Cached)

```python
class UserInterestProfile(Base):
    __tablename__ = "user_interest_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    interest_vector = Column(Vector(768), nullable=True)
    top_categories = Column(JSON, nullable=True)       # {"cs.AI": 0.4, "cs.CL": 0.3, ...}
    top_entities = Column(JSON, nullable=True)          # ["LoRA", "RAG", "GPT-4", ...]
    papers_used = Column(Integer, default=0)            # how many papers contributed to profile
    computed_at = Column(DateTime, default=func.now())
```

Caches the user interest vector so we don't recompute it every time. Recomputed by the scheduler.

### New Service: `reading_queue_service.py`

```python
class ReadingQueueService:
    def compute_user_interest_vector(self, user_id, db) -> list[float]:
        """Average embeddings of engaged papers with time-decay weighting."""

    def score_paper(self, paper, interest_vector, user_profile, db) -> dict:
        """Compute all scoring components for a single paper."""

    def rescore_queue(self, user_id, db) -> int:
        """Rescore all unread papers in user's queue. Returns count scored."""

    def sync_queue_from_library(self, user_id, db):
        """Add any bookmarked papers not yet in queue. Remove un-bookmarked ones."""

    def get_queue(self, user_id, db, limit, offset, status_filter) -> list:
        """Return prioritized queue ordered by priority_score desc."""

    def mark_read(self, user_id, paper_id, db):
        """Mark paper as read, update read_at timestamp."""

    def update_manual_priority(self, user_id, paper_id, priority, db):
        """Override automatic scoring with user's manual priority."""
```

### New Router: `routers/queue.py`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/queue` | Get prioritized reading queue (paginated, filterable by status) |
| `GET` | `/queue/stats` | Queue stats: total unread, avg priority, estimated reading time |
| `GET` | `/queue/{paper_id}/explain` | Why is this paper ranked here? (show scoring breakdown) |
| `POST` | `/queue/{paper_id}/read` | Mark as read |
| `POST` | `/queue/{paper_id}/reading` | Mark as currently reading |
| `POST` | `/queue/{paper_id}/skip` | Mark as skipped (deprioritize) |
| `PATCH` | `/queue/{paper_id}/priority` | Set manual priority override (1/2/3) |
| `POST` | `/queue/rescore` | Manually trigger re-scoring |
| `DELETE` | `/queue/{paper_id}` | Remove from queue (keeps in library) |

### Scheduler Job

```python
# In scheduler.py — new job
def rescore_reading_queues():
    """Rescore all users' reading queues. Run daily at 2 AM IST."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            queue_service.rescore_queue(user.id, db)
        logger.info(f"Rescored queues for {len(users)} users")
    finally:
        db.close()

# Register: scheduler.add_job(rescore_reading_queues, CronTrigger(hour=20, minute=30))  # 2 AM IST = 20:30 UTC
```

### Auto-Sync Trigger

When a paper is bookmarked via `POST /library/{paper_id}`:
- Automatically add to ReadingQueue with status "unread"
- Compute initial priority score inline (fast path — just interest similarity + freshness)
- Full scoring happens in next scheduler run

When a paper is removed from library:
- Remove from ReadingQueue

---

## Frontend Design

### New Route: `/queue`

Dedicated reading queue page accessible from sidebar.

### Queue Page Layout

```
┌─────────────────────────────────────────────────────────┐
│  Reading Queue                          [Rescore] [Filter]│
│                                                           │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Queue Stats Bar                                       ││
│  │ 📚 23 unread  ·  ⏱ ~4.5 hrs  ·  🔥 3 high priority  ││
│  └──────────────────────────────────────────────────────┘│
│                                                           │
│  ┌─ Up Next ─────────────────────────────────────────── ┐│
│  │ █████ [HIGH] Paper Title Here                   ✓ ⊘  ││
│  │ Score: 0.87  ·  cs.AI  ·  2026-03-18  ·  ~8 min    ││
│  │ "Highly relevant to your work on RAG systems..."     ││
│  └──────────────────────────────────────────────────────┘│
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ████ [MED] Another Paper Title                ✓ ⊘  │ │
│  │ Score: 0.72  ·  cs.CL  ·  2026-03-15  ·  ~12 min  │ │
│  │ "Shares entities: LoRA, BERT with your library..."  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ... more papers ...                                      │
│                                                           │
│  ┌─ Completed ──────────────────────────────────────── ┐ │
│  │ ✓ Read Paper Title (read 2 days ago)                │ │
│  │ ✓ Another Read Paper (read 1 week ago)              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Queue Card Component

Each queue item shows:
- **Priority badge:** HIGH (red/orange), MEDIUM (yellow), LOW (blue) based on score thresholds
- **Priority bar:** Visual fill bar showing relative score (0-100%)
- **Paper title** (clickable → opens peek sheet)
- **Score breakdown tooltip:** Hover to see "Interest: 0.9, Citations: 0.7, Fresh: 0.5..."
- **Relevance reason:** One-line explanation: "Similar to papers in your RAG list" or "Highly cited in your field"
- **Quick actions:**
  - ✓ Mark as read
  - ⊘ Skip
  - ↑↓ Manual priority override
  - Click title → peek sheet with abstract + analyze

### Dashboard Integration

Add an "Up Next" tile to the existing bento grid on the dashboard:

```
┌── Up Next ──────────────────┐
│ 📖 Paper Title (score 0.87) │
│    cs.AI · 2 days ago       │
│                              │
│ 📖 Paper Title (score 0.72) │
│    cs.CL · 5 days ago       │
│                              │
│ View Queue →                 │
└──────────────────────────────┘
```

Shows top 3 papers from the queue. Links to `/queue`.

### Sidebar Addition

Add "Reading Queue" link with unread badge count:

```
📚 Reading Queue (23)
```

### Filter/Sort Options

- **Status filter:** All, Unread, Reading, Read, Skipped
- **Sort:** Priority (default), Date added, Publication date, Reading time
- **Category filter:** Same category filter as dashboard
- **Priority filter:** High only, Medium+, All

---

## Relevance Explanation Feature

For each queued paper, generate a one-line human-readable explanation of why it's ranked where it is. This builds trust in the algorithm.

### Explanation Templates

Based on which scoring component dominated:

| Dominant Signal | Template |
|----------------|----------|
| Interest similarity | "Closely matches your recent reading on {top_entity}" |
| Citation impact | "Highly cited ({count} citations), influential in {category}" |
| Freshness | "Just published — relevant to your interests" |
| Category alignment | "Aligns with your focus on {category}" |
| Entity overlap | "Uses {entity1}, {entity2} — tools you follow" |
| Peer reads | "{count} papers in your library cite this work" |

### Backend Implementation

```python
def generate_explanation(scoring_breakdown: dict, paper: Paper, user_profile: dict) -> str:
    """Pick the top scoring signal and generate a human-readable explanation."""
    signals = [
        ("interest", scoring_breakdown["interest_similarity"], ...),
        ("citations", scoring_breakdown["citation_impact"], ...),
        ...
    ]
    top_signal = max(signals, key=lambda s: s[1])
    return TEMPLATES[top_signal[0]].format(**context)
```

---

## Read Status Tracking

### States

```
unread → reading → read
  ↓                  ↑
  └─→ skipped ───────┘ (can un-skip)
```

### Auto-Detection (Future)

- If user opens peek sheet for >30 seconds → auto-mark as "reading"
- If user triggers "Analyze with Gemini" → auto-mark as "reading"
- If user views paper detail page → auto-mark as "reading"
- If summary is generated → suggest marking as "read"

### Manual Controls

- Click ✓ → mark read
- Click ⊘ → mark skipped (moves to bottom, grayed out)
- Click 📖 → mark reading (highlights in sidebar)

---

## Reading Time Estimation

Already have `estimateReadingTime` in `lib/categoryColors.ts`:
```typescript
export function estimateReadingTime(text?: string): string | null {
    if (!text) return null;
    const words = text.split(/\s+/).length;
    const minutes = Math.ceil(words / 200);
    return `${minutes} min read`;
}
```

For the queue, compute based on full paper (abstract + summary length), not just the displayed text. Could also use PDF page count if available.

**Queue-level stat:** Sum of all unread papers' reading times → "~4.5 hours of reading in your queue"

---

## Edge Cases & Considerations

### Cold Start

New user with 0 bookmarks:
- No interest vector → skip interest similarity, weight other signals more
- Show "Bookmark some papers to get personalized recommendations"
- Fall back to citation impact + freshness as primary signals

### Stale Queue

Papers that have been in the queue for >30 days unread:
- Gradually decay priority (freshness score already handles this)
- After 90 days, suggest archiving: "These papers have been in your queue for a while. Archive?"

### Manual Override

User sets manual priority (High/Medium/Low):
- Manual priority overrides automatic score for sorting
- Within same manual priority tier, use automatic score
- Sort order: Manual High > Auto-scored > Manual Low > Skipped

### Queue Size

- Soft limit: warn at 50+ unread papers ("Your queue is getting long...")
- No hard limit, but paginate at 20 per page
- "Reading velocity" stat: papers read per week (trailing 4 weeks)

### Re-scoring Frequency

- **Full rescore:** Daily at 2 AM IST (scheduler job)
- **Quick rescore on events:**
  - User bookmarks new paper → score that paper immediately
  - User marks paper as read → triggers profile update + rescore top 10
  - User triggers summarization → profile update

---

## Migration Plan

### Phase 1: Core (MVP)

1. Add `ReadingQueue` and `UserInterestProfile` models
2. Create migration script
3. Implement `reading_queue_service.py` with basic scoring (interest similarity + freshness only)
4. Add `/queue` router with GET, mark-read, mark-skip endpoints
5. Add scheduler job for daily rescoring
6. Frontend: `/queue` page with basic list, status toggle, priority badge
7. Auto-sync: hook into library add/remove

### Phase 2: Enhanced Scoring

8. Add citation impact signal
9. Add entity overlap signal
10. Add peer reads signal
11. Add category alignment signal
12. Store scoring breakdown in ReadingQueue table
13. Frontend: score breakdown tooltip, relevance explanation

### Phase 3: Dashboard Integration

14. "Up Next" tile on dashboard bento grid
15. Sidebar unread badge
16. Reading velocity stats
17. Queue insights in analytics page

### Phase 4: Smart Features

18. Auto-detect reading status from user behavior
19. Stale paper archiving suggestions
20. "Similar to what you just read" recommendations after marking read
21. Weekly reading report in email digest

---

## API Client Additions (frontend/lib/api.ts)

```typescript
// Reading Queue
getQueue: async (status?: string, limit?: number, offset?: number) => { ... },
getQueueStats: async () => { ... },
getQueueExplanation: async (paperId: number) => { ... },
markRead: async (paperId: number) => { ... },
markReading: async (paperId: number) => { ... },
markSkipped: async (paperId: number) => { ... },
setManualPriority: async (paperId: number, priority: number) => { ... },
rescoreQueue: async () => { ... },
removeFromQueue: async (paperId: number) => { ... },
```

---

## Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `backend/models/queue.py` | ReadingQueue, UserInterestProfile models |
| `backend/routers/queue.py` | Queue API endpoints |
| `backend/services/reading_queue_service.py` | Scoring logic, profile computation |
| `backend/migrate_reading_queue.py` | Database migration |
| `frontend/app/queue/page.tsx` | Queue page |
| `frontend/components/QueueCard.tsx` | Queue item card with priority badge |
| `frontend/components/dashboard/QueueTile.tsx` | "Up Next" dashboard tile |

### Modified Files
| File | Change |
|------|--------|
| `backend/models/__init__.py` | Export new models |
| `backend/main.py` | Register queue router |
| `backend/scheduler.py` | Add rescore job |
| `backend/routers/library.py` | Hook add/remove to sync queue |
| `frontend/lib/api.ts` | Add queue API methods |
| `frontend/components/Sidebar.tsx` | Add queue link with badge |
| `frontend/components/DashboardContent.tsx` | Add "Up Next" tile |
