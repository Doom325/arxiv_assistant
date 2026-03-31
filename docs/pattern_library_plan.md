# Architecture Pattern Library — Implementation Plan

## Context
The arXiv Assistant already has a batch experiment script (`run_pattern_experiment.py`) that classifies papers into a 10-category / 43-pattern taxonomy using a V6 CoT prompt via Ollama. However, this data is trapped in the `pattern_experiment_results` table with **no API routes, no frontend, and no auto-classification** for new papers. This plan surfaces that data through a pattern-centric browsable UI, adds auto-classification to the production worker, and integrates pattern badges into existing paper views.

---

## Phase 1: Backend — Shared Taxonomy & Model

### 1.1 Create `backend/taxonomy.py`
Extract the hardcoded taxonomy from `run_pattern_experiment.py` into a shared module so both the worker and routers can import it.

```python
VALID_CATEGORIES = { "agent_memory", "agent_planning", ... }
VALID_PATTERNS = { "agent_memory": ["retrieval_augmented", ...], ... }
CATEGORY_LABELS = { "agent_memory": "Agent Memory", ... }  # Human-readable names
PATTERN_LABELS = { "retrieval_augmented": "Retrieval-Augmented", ... }
V6_COT_PROMPT = """..."""  # Move the prompt template here
```

**Files:** New file `backend/taxonomy.py`

### 1.2 Move `PatternExperimentResult` to `models.py`
The model is currently defined only inside `run_pattern_experiment.py`. Move it to `models.py` so routers can import it. Update `run_pattern_experiment.py` to import from `models`.

**Files:** `backend/models.py`, `backend/run_pattern_experiment.py`

### 1.3 Add Pydantic schemas to `schemas.py`

```python
class PatternDetail(BaseModel):
    category: str
    name: str
    confidence: float
    evidence: Optional[str] = None

class PaperPatternResponse(BaseModel):
    arxiv_id: str
    title: str
    published_date: datetime
    category: str  # arXiv category
    is_agentic: bool
    primary_pattern_category: Optional[str]
    patterns: List[PatternDetail]
    reasoning: Optional[str] = None

class PatternCount(BaseModel):
    name: str
    label: str
    paper_count: int

class CategoryOverview(BaseModel):
    category: str
    label: str
    paper_count: int
    is_agentic_category: bool  # True for agent_* categories
    patterns: List[PatternCount]

class PatternOverviewResponse(BaseModel):
    total_classified: int
    total_agentic: int
    categories: List[CategoryOverview]
```

**Files:** `backend/schemas.py`

---

## Phase 2: Backend — API Router

### 2.1 Create `backend/routers/patterns.py`

Three endpoints:

#### `GET /patterns/overview`
Returns the full taxonomy with paper counts per category and per pattern.
- Queries `pattern_experiment_results` grouped by `primary_category`
- For per-pattern counts: unnest the `patterns` JSON column using PostgreSQL JSON operators (`jsonb_array_elements`) or application-level aggregation
- Filters: `is_agentic` (bool), `start_date`/`end_date` (via join to `papers.published_date`)
- Returns `PatternOverviewResponse`

#### `GET /patterns/papers?category=&pattern=&is_agentic=&skip=&limit=`
Returns paginated papers matching a specific category/pattern.
- Queries `pattern_experiment_results` joined with `papers`
- Filter by `primary_category` or by pattern name within the JSON `patterns` column (using `patterns::jsonb @> '[{"name": "tree_search"}]'`)
- Filter by `is_agentic`, date range
- Exclude rows with `num_violations > 0` or `error IS NOT NULL` (quality gate)
- Returns `List[PaperPatternResponse]`

#### `GET /patterns/paper/{arxiv_id}`
Returns patterns for a single paper.
- Simple lookup by `arxiv_id` in `pattern_experiment_results`
- Returns `PaperPatternResponse` or 404

### 2.2 Register router in `main.py`
```python
from routers import papers, users, library, batch, citations, patterns
app.include_router(patterns.router)
```

**Files:** New file `backend/routers/patterns.py`, `backend/main.py`

---

## Phase 3: Backend — Auto-Classification in Worker

### 3.1 Add `classify_paper()` to `llm_service.py`
Add a new method to the `LLMProvider` interface and both implementations:

```python
# In LLMProvider (abstract)
def classify_paper(self, title: str, abstract: str) -> dict: ...

# GeminiProvider: use generate_content with response_mime_type="application/json"
# OllamaProvider: use /api/chat with format="json"
```

Both use the V6 CoT prompt from `taxonomy.py`, temperature=0.1, and return parsed JSON.

**Files:** `backend/services/llm_service.py`, `backend/taxonomy.py`

### 3.2 Add Step 3 to `production_worker.py`
After Step 2.5 (sync search embedding), add:

```
--- STEP 3: PATTERN CLASSIFICATION ---
```

Logic:
1. Check if `PatternExperimentResult` row exists for this `arxiv_id` (with current `prompt_version`)
2. If not, call `llm_service.classify_paper(paper.title, abstract_text)`
3. Validate output against taxonomy (reuse validation logic from experiment script)
4. Store as a new `PatternExperimentResult` row
5. Log job as `worker_classify`

The abstract text: use `paper.extracted_abstract` (from Step 2), falling back to `paper.summary`. Truncate to 800 chars (matching experiment script behavior).

**Files:** `backend/production_worker.py`

### 3.3 Update `run_pattern_experiment.py`
- Import `PatternExperimentResult` from `models` instead of defining locally
- Import taxonomy constants from `taxonomy.py`
- Import prompt from `taxonomy.py`
- Keep the script functional for batch runs, but now it shares code with the worker

**Files:** `backend/run_pattern_experiment.py`

---

## Phase 4: Frontend — Pattern Library Page

### 4.1 Add API functions to `frontend/lib/api.ts`

```typescript
// New interfaces
interface PatternDetail { category: string; name: string; confidence: number; evidence?: string; }
interface PaperPattern { arxiv_id: string; title: string; published_date: string; category: string; is_agentic: boolean; primary_pattern_category?: string; patterns: PatternDetail[]; reasoning?: string; }
interface PatternCount { name: string; label: string; paper_count: number; }
interface CategoryOverview { category: string; label: string; paper_count: number; is_agentic_category: boolean; patterns: PatternCount[]; }
interface PatternOverview { total_classified: number; total_agentic: number; categories: CategoryOverview[]; }

// New functions
getPatternOverview(filters?: { is_agentic?: boolean })
getPatternPapers(filters: { category?: string; pattern?: string; is_agentic?: boolean; skip?: number; limit?: number })
getPaperPatterns(arxivId: string)
```

**Files:** `frontend/lib/api.ts`

### 4.2 Create `frontend/app/patterns/page.tsx`

**Layout (pattern-centric, drill-down):**

**State machine:** `overview` → `category` → `papers`

**View 1 — Overview (default):**
- Header: "Architecture Pattern Library" + total stats bar (X papers classified, Y agentic)
- Filter: `[Agentic Only toggle]` `[Date range]`
- Grid of 10 category cards (responsive: 2-col mobile, 3-col tablet, 4-col desktop)
- Each card shows:
  - Category icon + human-readable label (e.g., "Agent Planning")
  - Paper count badge
  - List of sub-patterns as clickable chips
  - Visual indicator if it's an agentic category (indigo accent) vs non-agentic (zinc accent)
- Click a card → transitions to View 2

**View 2 — Category detail:**
- Breadcrumb: `Pattern Library > Agent Planning`
- Back button
- List of patterns within the category, each as an expandable row showing:
  - Pattern name + paper count
  - Click → transitions to View 3

**View 3 — Paper list:**
- Breadcrumb: `Pattern Library > Agent Planning > Tree Search`
- Back button
- List of papers tagged with this pattern
- Each paper card shows: title, date, all detected patterns as badges, confidence score, evidence quote
- Click paper title → links to `/paper/[id]`

**Styling:** Follow existing dark theme — `bg-zinc-900/50`, `border-zinc-800`, indigo accents for agentic, emerald for non-agentic.

**Files:** New file `frontend/app/patterns/page.tsx`

### 4.3 Add "Patterns" to Sidebar

In `frontend/components/Sidebar.tsx`, add to the `navigation` array:
```typescript
{ name: "Patterns", href: "/patterns", icon: Layers }
```
Import `Layers` from `lucide-react`. Insert between "Analysis" and "Deep Dive".

**Files:** `frontend/components/Sidebar.tsx`

### 4.4 Add pattern section to paper detail page

In `frontend/app/paper/[id]/page.tsx`, after the Citations section:
- Call `getPaperPatterns(id)` on mount
- If patterns exist, render a "Detected Patterns" section:
  - `is_agentic` badge (green "Agentic" or gray "Non-Agentic")
  - Primary category badge
  - Grid of pattern badges: `category/name` with confidence bar
  - Expandable CoT reasoning (collapsed by default)
  - Evidence quotes under each pattern

**Files:** `frontend/app/paper/[id]/page.tsx`

---

## File Change Summary

| File | Action | Description |
|---|---|---|
| `backend/taxonomy.py` | **NEW** | Shared taxonomy constants + V6 CoT prompt |
| `backend/models.py` | EDIT | Add `PatternExperimentResult` model |
| `backend/schemas.py` | EDIT | Add pattern-related Pydantic schemas |
| `backend/routers/patterns.py` | **NEW** | Pattern Library API (3 endpoints) |
| `backend/main.py` | EDIT | Register patterns router |
| `backend/services/llm_service.py` | EDIT | Add `classify_paper()` method |
| `backend/production_worker.py` | EDIT | Add Step 3: auto-classification |
| `backend/run_pattern_experiment.py` | EDIT | Import from shared modules |
| `frontend/lib/api.ts` | EDIT | Add pattern API functions + types |
| `frontend/app/patterns/page.tsx` | **NEW** | Pattern Library page (3-view drill-down) |
| `frontend/components/Sidebar.tsx` | EDIT | Add "Patterns" nav item |
| `frontend/app/paper/[id]/page.tsx` | EDIT | Add "Detected Patterns" section |

---

## Verification

1. **Backend API:** Start FastAPI, hit `GET /patterns/overview` — should return category counts from existing experiment data
2. **Pattern drill-down:** Hit `GET /patterns/papers?category=agent_planning&pattern=tree_search` — should return papers
3. **Paper patterns:** Hit `GET /patterns/paper/{arxiv_id}` for a known classified paper — should return its patterns
4. **Frontend:** Navigate to `/patterns` — should see the category grid with counts. Click through to category → pattern → papers. Click a paper → verify pattern badges on detail page.
5. **Auto-classification:** Add a new paper via the sidebar form. Wait for the worker to process it (check worker logs for "Step 3: Pattern Classification"). Verify it appears in the Pattern Library.
6. **Quality gate:** Papers with `num_violations > 0` should be excluded from the `/patterns/papers` results.
