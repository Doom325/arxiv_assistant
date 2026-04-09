# Parallel Pattern Backfill with Gemma3:12b

## Context

The arxiv_assistant pattern classification pipeline currently runs single-threaded — one paper at a time through `backfill_patterns.py` or the `production_worker.py` loop. With Gemma3:12b at ~8 GB VRAM and 128 GB unified memory on the Framework (AMD AI Max+ Pro 395), there's significant headroom to parallelize.

## Current Architecture

```
backfill_patterns.py (single-threaded)
  └── llm_service.classify_paper(title, abstract)
        └── HTTP POST → Ollama :11434 → gemma3:12b (single model instance)
              └── Sequential inference, one request at a time
```

**Bottleneck:** Ollama processes requests to a single model sequentially by default. Even if we send concurrent HTTP requests, they queue up server-side.

## Strategy: Multiple Ollama Instances

Gemma3:12b loads at ~14 GB with 64K context. The Framework has 128 GB unified memory with ~104 GB available. We can comfortably run **4–6 independent Ollama server instances**, each serving its own gemma3:12b copy.

### Option A: Multiple Ollama Processes on Different Ports (Recommended)

Spin up N separate `ollama serve` processes, each on a different port. Each holds its own model copy in memory.

```
┌─────────────────────────────────────────────────┐
│  Framework Mini PC (128 GB unified, 32 cores)   │
│                                                  │
│  Ollama :11434  ─── gemma3:12b  (~14 GB)        │
│  Ollama :11435  ─── gemma3:12b  (~14 GB)        │
│  Ollama :11436  ─── gemma3:12b  (~14 GB)        │
│  Ollama :11437  ─── gemma3:12b  (~14 GB)        │
│                                                  │
│  Total: ~56 GB  (leaves ~48 GB free)             │
└─────────────────────────────────────────────────┘
          ▲  ▲  ▲  ▲
          │  │  │  │
    ┌─────┴──┴──┴──┴─────┐
    │  backfill_parallel  │
    │  (4 worker threads) │
    │  round-robin across │
    │  Ollama endpoints   │
    └─────────────────────┘
```

**How to launch additional Ollama instances:**

```bash
# Instance 2 on port 11435
OLLAMA_HOST=0.0.0.0:11435 \
OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
OLLAMA_LLM_LIBRARY=vulkan \
OLLAMA_VULKAN=1 \
OLLAMA_FLASH_ATTENTION=1 \
ollama serve &

# Instance 3 on port 11436
OLLAMA_HOST=0.0.0.0:11436 \
OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
OLLAMA_LLM_LIBRARY=vulkan \
OLLAMA_VULKAN=1 \
OLLAMA_FLASH_ATTENTION=1 \
ollama serve &

# Repeat for as many as needed...
```

Each instance shares the same model files on disk (`OLLAMA_MODELS` points to the same dir) but loads its own copy into memory. Pre-warm each by running:

```bash
curl http://localhost:11435/api/generate -d '{"model":"gemma3:12b","prompt":"hi","stream":false}'
curl http://localhost:11436/api/generate -d '{"model":"gemma3:12b","prompt":"hi","stream":false}'
```

### Option B: Ollama's Built-in `OLLAMA_NUM_PARALLEL`

Ollama supports concurrent request handling on a single instance via `OLLAMA_NUM_PARALLEL`. This shares the same model weights in memory (no duplication) but splits the KV cache.

```bash
# In ollama.service override:
Environment="OLLAMA_NUM_PARALLEL=4"
```

**Trade-off:**
| | Option A (Multi-instance) | Option B (NUM_PARALLEL) |
|---|---|---|
| Memory per slot | ~14 GB (full model copy) | ~shared weights + split KV cache |
| Total for 4 slots | ~56 GB | ~14 GB + 4 × KV overhead |
| Throughput | Higher (fully independent) | Good, but contends on compute |
| Complexity | More processes to manage | Single process, one env var |
| GPU scheduling | Each gets own Vulkan context | Single Vulkan context, time-shared |
| Reliability | One crash doesn't kill others | One crash kills all |

**Recommendation:** Start with **Option B** (`OLLAMA_NUM_PARALLEL=4`) for simplicity. If throughput plateaus due to GPU contention, switch to Option A.

### Option C: Hybrid — Reduce Context Window for Backfill

Pattern classification only needs title + first 800 chars of abstract. The 64K context window is wildly oversized for this task. Reducing it frees memory for more parallelism:

```bash
# For backfill-only Ollama instances:
OLLAMA_NUM_CTX=4096  # Plenty for classification
```

At 4K context, gemma3:12b uses ~9 GB instead of ~14 GB, allowing **up to 8–10 parallel instances** in 128 GB.

## Backfill Script Design

The parallel backfill script should:

1. **Query DB** for all papers missing `PatternExperimentResult` entries
2. **Partition** papers into N chunks
3. **Spawn N workers** (threads or processes), each assigned an Ollama endpoint
4. **Each worker** iterates its chunk, calling `classify_paper()` against its assigned endpoint
5. **Batch-commit** results to PostgreSQL (thread-safe via separate sessions)

```
┌────────────────────────────────────────┐
│         backfill_parallel.py           │
│                                        │
│  1. Query: SELECT papers without       │
│     pattern results                    │
│  2. Split into N chunks                │
│  3. ThreadPoolExecutor(max_workers=N)  │
│     ├── Worker 0 → :11434/v1           │
│     ├── Worker 1 → :11435/v1           │
│     ├── Worker 2 → :11436/v1           │
│     └── Worker 3 → :11437/v1           │
│  4. Each worker: own DB session,       │
│     own HTTP session, batch commit     │
│  5. Progress bar + live stats          │
└────────────────────────────────────────┘
```

### Key Implementation Notes

**DB thread safety:** Each worker thread must create its own `SessionLocal()` — SQLAlchemy sessions are not thread-safe. Use `sessionmaker` with `scoped_session` or just instantiate per-worker.

**HTTP connection reuse:** Each worker should maintain a `requests.Session()` for connection pooling to its assigned Ollama port.

**Avoid the singleton `llm_service`:** The current `llm_service = get_llm_service()` creates one instance with one `OLLAMA_BASE_URL`. For parallel backfill, instantiate separate `OllamaProvider` objects per worker, each pointed at a different port. Or simpler — just make raw HTTP calls directly (the classify logic is just a POST with the V6 CoT prompt).

**Error handling:** Individual paper failures should be logged and skipped, not crash the worker. Track error counts per endpoint to detect unhealthy Ollama instances.

**Rate limiting:** Not needed for local Ollama, but add a small delay (0.1s) between requests to avoid overwhelming the Vulkan scheduler if using Option A.

## Memory Budget

```
Component                     Memory
─────────────────────────────────────
OS + system overhead           ~5 GB
Ollama instance 1 (gemma3:12b) ~14 GB  (existing, 64K ctx)
Ollama instance 2              ~14 GB
Ollama instance 3              ~14 GB
Ollama instance 4              ~14 GB
PostgreSQL (if local)           ~1 GB
Monitoring (Prometheus+Grafana) ~1 GB
mitmproxy container             ~1 GB
─────────────────────────────────────
Total                          ~64 GB
Available                     ~128 GB
Headroom                       ~64 GB  (room for 4 more instances)
```

With reduced context (4K for backfill): each instance drops to ~9 GB, fitting **8–10 instances** comfortably.

## Quick Start — Fastest Path to 4x Throughput

The simplest approach that requires zero code changes to the existing codebase:

### 1. Set `OLLAMA_NUM_PARALLEL` on the existing Ollama service

```bash
# On Framework:
sudo systemctl edit ollama

# Add under [Service]:
Environment="OLLAMA_NUM_PARALLEL=4"

# Restart:
sudo systemctl restart ollama
```

### 2. Run 4 backfill processes simultaneously

```bash
# Terminal 1 — cs.AI papers, Jan 2025
cd ~/git/arxiv_assistant/backend
PYTHONPATH=. python3 backfill_patterns.py --category cs.AI --start 2025-01-01 --end 2025-03-31

# Terminal 2 — cs.AI papers, Apr 2025
PYTHONPATH=. python3 backfill_patterns.py --category cs.AI --start 2025-04-01 --end 2025-06-30

# Terminal 3 — cs.CL papers
PYTHONPATH=. python3 backfill_patterns.py --category cs.CL --start 2025-01-01 --end 2025-06-30

# Terminal 4 — cs.LG papers
PYTHONPATH=. python3 backfill_patterns.py --category cs.LG --start 2025-01-01 --end 2025-06-30
```

This works **today** with no code changes — `OLLAMA_NUM_PARALLEL` lets the single Ollama server handle 4 concurrent inference requests, and each `backfill_patterns.py` process gets its own DB session.

### 3. For even higher throughput, write `backfill_parallel.py`

A purpose-built script using `ThreadPoolExecutor` + multiple Ollama endpoints. This gives full control over worker count, progress tracking, and error recovery — and avoids manually splitting date ranges.

## Monitoring

The existing Prometheus + Grafana stack (running as Podman containers) can track:
- `ollama_requests_total` — throughput per endpoint
- `ollama_request_duration_seconds` — latency distribution
- GPU utilization via `rocm-smi` (AMD) or custom exporter

Add a simple progress tracker to the backfill script:
```
[Worker 0] 142/500 papers | 3.2s avg | 0 errors | ETA: 19m
[Worker 1] 138/500 papers | 3.4s avg | 1 error  | ETA: 20m
[Worker 2] 145/500 papers | 3.1s avg | 0 errors | ETA: 18m
[Worker 3] 140/500 papers | 3.3s avg | 2 errors | ETA: 19m
```

## Recommendation

1. **Start with Option B** — set `OLLAMA_NUM_PARALLEL=4` on the existing service, run 4 `backfill_patterns.py` processes split by date range. Zero code changes, 4x throughput immediately.
2. **If throughput isn't enough** — write `backfill_parallel.py` with ThreadPoolExecutor and multiple Ollama instances (Option A), reduced to 4K context.
3. **Monitor GPU utilization** — if Vulkan is saturated at 4 parallel, you won't gain from more instances. The AI Max+ Pro 395 has 32 CUs; Gemma3:12b may only saturate ~50% per inference, so 4–6 parallel is likely the sweet spot.
