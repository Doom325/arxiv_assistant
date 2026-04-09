# Parallel Pattern Backfill Implementation Plan

This plan transforms the current single-threaded backfill process into a highly parallelized pipeline capable of fully utilizing the Framework Desktop's unified memory and `gemma3:12b` capabilities. We are moving forward with **Option B (OLLAMA_NUM_PARALLEL) + a threaded Python script**, but with a hardened architecture to ensure database integrity, efficient memory use, and fault tolerance based on updated Ollama insights.

## User Review Required

> [!CAUTION]
> **Host Access Required:** We need to update `ollama.service` on the physical Framework machine (at `192.168.1.32`). Do you want me to execute `sudo systemctl edit ollama` over SSH, or will you do this manually?

> [!WARNING]
> **Production Worker Conflict:** Running 4 backfill threads will saturate the 4 Ollama slots. If the `production_worker.py` attempts to classify a new paper concurrently, it will queue and block. You **must** temporarily stop the production worker during this backfill. Do you approve?

## Proposed Changes

### 1. Host Machine (Ollama Server)

#### [MODIFY] Ollama Service (`ollama.service` on 192.168.1.32)
Based on Ollama documentation, `OLLAMA_NUM_PARALLEL=4` multiplicatively increases effective context size (e.g., 4 parallel slots of 64K context = 256K total allocated memory). We must tightly control this. We will add the following environment variables to `ollama.service`:
- `Environment="OLLAMA_NUM_PARALLEL=4"`
- `Environment="OLLAMA_FLASH_ATTENTION=1"` (Enables high-efficiency memory management)
- `Environment="OLLAMA_KV_CACHE_TYPE=q8_0"` (Quantizes the KV cache to 8-bit, drastically reducing the multithreading memory overhead with negligible quality loss)
- Restart the Ollama daemon.

**Pre-flight Gate:** We will manually run 4 simultaneous `curl` requests to `/api/chat`. 
*Success requires:*
- System memory stays comfortably under 80 GB. We will explicitly test load-memory vs active-request-memory to verify if Ollama forcefully allocates the total `NUM_PARALLEL` footprint regardless of `num_ctx`.
- Per-request latency stays within 2x of a single-request baseline (ensure Vulkan isn't thrashing).
- No OOM errors.

### 2. Backend Pipeline

#### [NEW] [backfill_parallel.py](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/scripts/backfill_parallel.py)
A specialized, fault-tolerant multithreaded script substituting `backfill_patterns.py` for bulk processing.

- **Execution Context:** The process **must** be executed inside an active `tmux` session directly mimicking `ssh gsumanth@192.168.1.32 && tmux new -s backfill` to guarantee it survives network drops.
- **Thread Pool:** Uses `concurrent.futures.ThreadPoolExecutor(max_workers=4)`.
- **No Singleton:** The script will **not** import `llm_service` to avoid module-level config singletons. Instead, workers will format the V6 CoT prompt, strictly applying our `sanitize_text` utility on titles/abstracts, and make raw HTTP POST requests to `OLLAMA_BASE_URL/api/chat`.
- **Request Hardening:** 
  - Forces `"num_ctx": 4096` in the payload for classification. 
  - Forces `"keep_alive": "30m"` to prevent Ollama from randomly unloading the model cold-start penalty if a thread finishes early.
  - Hardcodes a `timeout=120` constraint on the POST request to instantly abort any hung threads (since it should only take ~5-15s per query).
- **Deterministic Partitioning:** Uses modulo arithmetic on a hash of the `arxiv_id` (`hash(arxiv_id) % 4`) to partition tasks so that re-runs or resume operations seamlessly overlap without missing or duplicating uncommitted papers.
- **Micro-commits:** Threads will open a database session, process and **commit a single paper at a time**, then cleanly close the session. This represents 100% crash safety against ~0.2% latency overhead, stopping any fear of DB pool starvation.
- **Rollback Safety / Tagging:** Results written by this script will tag `model_name` as `"gemma3:12b-parallel-backfill"`. This allows us a 1-click `DELETE FROM` query to completely wipe the backfill if anything unexpectedly impacts data quality.
- **JSONL Observability:** Appends to a `backfill_metrics.jsonl` log file (timestamp, worker_id, elapsed_time, success_state) so progress isn't lost if the SSH terminal disconnects.

## Open Questions

1. **Host Execution:** Can I push the config changes to the `192.168.1.32` host directly?

## Verification Plan

### Automated Tests
1. **Adversarial Smoke Test:** Create a small test script evaluating a mock set of 20 papers divided across 2 workers using a dummy local database to guarantee sessions don't deadlock and rows correctly commit. **This test will include edge-case papers natively found on arxiv**:
  - One with a blank/null abstract.
  - One with a massive 1500+ character title.
  - One densely packed with `$\mathcal{O}(n)$` LaTeX symbols and raw Unicode.

### Manual Verification
1. **Sequential vs Parallel Accuracy Test:** Run 20 predefined papers through the classic `backfill_patterns.py` and the new `backfill_parallel.py`. Verify that `is_agentic`, `primary_category`, and `patterns` identically match, proving that `NUM_PARALLEL`'s KV cache sharing does not degrade the model's reasoning performance.
2. Watch `backfill_metrics.jsonl` via `tail -f` to observe real-time health and parsing success rates across all 4 thread IDs.
