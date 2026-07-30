# Arxiv Assistant Search Functionality Understanding

This document details how the search functionality works in the `arxiv_assistant` project as of the current state of the codebase.

## 1. Overview
The search system employs a **Hybrid Search** strategy, combining Semantic Search (vector-based) and Full-Text Search (keyword-based) using PostgreSQL. The results from both methods are merged and ranked using **Reciprocal Rank Fusion (RRF)** to provide highly relevant results.

The primary entry point for search is the `POST /papers/search` endpoint located in `backend/routers/search.py`.

## 2. Step-by-Step Execution

### Step 1: Query Parsing
The search starts by parsing the user's raw query string (`parse_query` function) to extract specific metadata filters. It looks for the following operators:
- `category:` (e.g., `category:cs.AI`)
- `after:` (e.g., `after:2023` or `after:2023-01-01`)
- `before:` (e.g., `before:2024` or `before:2024-12-31`)
- `author:` (e.g., `author:Smith`)
- `entity:` (e.g., `entity:Transformer`)

These operators are stripped from the query to produce a "clean query", and the extracted filters are stored for later use in SQL queries.

### Step 2: Query Embedding Generation
The clean query is converted into a vector embedding to be used in semantic search.
- It uses `query_cache.get_or_generate` with the task type `"retrieval_query"`.
- This ensures that duplicate search queries do not hit the LLM provider API repeatedly, saving time and cost.

### Step 3: Semantic Search (Vector Search)
A SQL query is constructed against the `PaperEmbedding` table (joined with the `Paper` table).
- **Filtering**: All extracted metadata filters from the query string, as well as explicit parameters passed to the API (like UI dropdowns for category or date pickers), are applied as standard SQL `WHERE` clauses.
- **Ranking**: The query orders the results by the L2 distance between the paper's stored embedding and the generated query embedding (`PaperEmbedding.embedding.l2_distance(query_embedding)`).
- **Pooling**: A large pool of the top 10,000 results (`POOL_SIZE = 10000`) is fetched for RRF scoring.

### Step 4: Full-Text Search (Keyword Search)
A parallel SQL query is constructed against the `Paper` table for keyword matching.
- **Filtering**: Applies the exact same metadata and explicit UI filters as the semantic search.
- **Matching**: Uses PostgreSQL's built-in `tsvector` and `tsquery` capabilities.
  - The `search_vector` on the `Paper` model is a computed column that concatenates the title (Weight A), the extracted entities (Weight A), and the summary (Weight B).
  - The query filters for rows where `search_vector @@ plainto_tsquery('english', clean_query)`.
- **Ranking**: Results are ordered by relevance using `ts_rank_cd`.
- **Pooling**: Again, the top 10,000 results are fetched.

### Step 5: Reciprocal Rank Fusion (RRF)
The results from both Semantic Search and Full-Text Search are merged.
- RRF calculates a combined score for each paper using its rank position in both result lists.
- Formula: `score = sum(1.0 / (k + rank))`
- In this implementation, `k = 60`, and `rank` is the 0-indexed position of the paper in the respective list.

### Step 6: Final Ranking and Pagination
The combined list of papers is sorted based on the API's `sort_by` parameter:
- **`relevance`**: Sorts papers in descending order of their computed RRF scores.
- **`date`**: Sorts the pooled papers by `published_date` descending.
- **`title`**: Sorts the pooled papers alphabetically by `title`.
Finally, the `skip` and `limit` parameters are applied to paginate the results before returning them to the user.

## 3. Database Schema Highlights (`backend/models/paper.py`)

### `Paper` Model
- Contains metadata (title, authors, dates, etc.).
- `search_vector`: A `TSVECTOR` column computed automatically and indexed using a GIN index for fast full-text searches.

### `PaperEmbedding` Model
- Represents a 1-to-many relationship with `Paper` (a paper can have multiple embeddings, perhaps from different models or prompt templates).
- Uses `pgvector` (`Vector(768)`) to store the actual high-dimensional vectors. *(Note: While `GEMINI.md` mentions 3072D embeddings, the current SQLAlchemy model definition specifies `Vector(768)`)*.

## 4. Chat / RAG System Integration
The search router also includes a `/papers/chat` endpoint which acts as a simple Retrieval-Augmented Generation (RAG) system:
1. Generates an embedding for the user's question.
2. Performs a purely semantic search (L2 distance) to find the top 3 most relevant papers.
3. Constructs a context prompt using the titles and summaries of those 3 papers.
4. Passes the context and the user's query to the `llm_service.chat` method to generate a natural language response.
