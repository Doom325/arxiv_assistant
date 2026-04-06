# Parallel Pattern Backfill - Project Plan

This document tracks execution progress for the parallel backfill implementation.

## PR Strategy

Each phase maps to one focused PR. This keeps reviews manageable and allows incremental merging without blocking parallel work streams. **Do not combine phases into a single PR.**

| PR | Branch | Scope | Estimated Size |
|----|--------|-------|----------------|
| PR 1 | `feat/mitmproxy-metrics-addon` | Phase 0 — mitmproxy addon, compose changes, Prometheus config, Grafana dashboard | ~4 files, ~300 lines |
| PR 2 | `config/ollama-parallel` | Phase 1 — Ollama service config changes, pre-flight test script/results | ~2 files, ~50 lines (config + docs) |
| PR 3 | `feat/backfill-parallel-script` | Phase 2 — `backfill_parallel.py` core implementation | ~1-2 files, ~250-350 lines |
| PR 4 | `test/backfill-parallel` | Phase 3 — all unit and integration tests for the backfill script | ~2-3 test files, ~300-400 lines |
| PR 5 | `docs/backfill-accuracy-validation` | Phase 4 — accuracy comparison results, documented in markdown | ~1 file, docs only |

Phase 5 (deployment) is operational, not code — no PR needed.

## Phase 0: Observability Infrastructure (mitmproxy + Grafana)
| ID | Task | Description | Dependencies | Status |
|----|------|-------------|--------------|--------|
| T0.1 | Create mitmproxy addon | Write `ollama_metrics_addon.py` — intercepts `/api/chat` responses, extracts Ollama timing/token metadata, exposes Prometheus metrics on `:8765` | None | DONE |
| T0.2 | Update monitoring compose | Mount addon into mitmproxy container, add `--scripts` flag, expose port 8765, add `pip install prometheus-client` to entrypoint | T0.1 | DONE |
| T0.3 | Add Prometheus scrape target | Add `ollama-mitmproxy:8765` job to `prometheus.yml` with 5s scrape interval | T0.2 | DONE |
| T0.4 | Create Grafana dashboard | Auto-provisioned dashboard: request rate, latency p50/p95/p99, tokens/sec, active requests, error rate, model memory | T0.3 | DONE |
| T0.5 | Test observability stack | Restart monitoring stack. Send single `/api/chat` request through `:8434`. Verify: addon loads (check container logs), metrics appear at `:8765/metrics`, Grafana dashboard populates | T0.4 | PENDING |
| T0.6 | **PR 1: Submit** | Branch `feat/mitmproxy-metrics-addon`. Scope: addon script, compose changes, prometheus.yml, grafana dashboard. Label `reviewer:pending`. | T0.5 | PENDING |

## Phase 1: Environment & Host Configuration
| ID | Task | Description | Dependencies | Status |
|----|------|-------------|--------------|--------|
| T1.1 | Update Ollama config | Add `OLLAMA_NUM_PARALLEL=4`, `OLLAMA_KV_CACHE_TYPE=q8_0` to ollama.service override. (`OLLAMA_FLASH_ATTENTION=1` already set.) Restart daemon. | None | PENDING |
| T1.2 | Pre-flight gate: single baseline | Send 1 classification request through `:8434` (mitmproxy). Record baseline latency and memory. | T0.5, T1.1 | PENDING |
| T1.3 | Pre-flight gate: parallel stress | Send 4 concurrent classification requests through `:8434` with `num_ctx=4096`. **Pass criteria:** all 4 return valid JSON, system memory <80 GB, per-request latency <2x baseline, no OOM/Vulkan errors. Also compare memory at model load vs during active requests (validates q8_0 + num_ctx interaction). | T1.2 | PENDING |
| T1.4 | Verify mitmproxy under load | Confirm mitmproxy handled 4 concurrent requests without errors. Check `:8765/metrics` shows `ollama_requests_total` = 4, `ollama_active_requests` peaked at 4. Verify flows visible in mitmweb UI. | T1.3 | PENDING |
| T1.5 | **PR 2: Submit** | Branch `config/ollama-parallel`. Scope: ollama.service override, pre-flight results documented. Label `reviewer:pending`. | T1.4 | PENDING |

## Phase 2: Backend Script Implementation
| ID | Task | Description | Dependencies | Status |
|----|------|-------------|--------------|--------|
| T2.1 | Core skeleton | Parse CLI args (`--category`, `--start`, `--end`, `--workers`, `--dry-run`). Configure `ThreadPoolExecutor(max_workers=N)`. | None | PENDING |
| T2.2 | Deterministic partitioning | Implement `hashlib.md5(arxiv_id.encode()).hexdigest()` based modulo partitioning. **NOT** `hash()` — Python's built-in hash is randomized per-process via `PYTHONHASHSEED`, breaking resume determinism. | T2.1 | PENDING |
| T2.3 | Inline HTTP POST | Direct calls to `http://localhost:8434/api/chat` (through mitmproxy, not `:11434` directly). Hardcode: `timeout=120`, `num_ctx=4096`, `keep_alive=30m`, `temperature=0.1`, `format=json`. Apply `sanitize_text()` to title and abstract before sending — the inline approach bypasses `llm_service` which normally handles this. | T2.1 | PENDING |
| T2.4 | DB micro-commits | Per-paper commit cycle: open `SessionLocal()` → classify → write `PatternExperimentResult` → commit → close. Tag all rows with `model_name="gemma3:12b-parallel-backfill"` for rollback safety. | T2.2, T2.3 | PENDING |
| T2.5 | Observability logging | Thread-safe JSONL append to `backfill_metrics.jsonl`. Schema per line: `{"timestamp", "worker_id", "arxiv_id", "elapsed_seconds", "status", "eval_count", "prompt_eval_count", "tokens_per_sec", "error_message"}`. Use file lock or queue-based writer to prevent interleaved writes. | T2.4 | PENDING |
| T2.6 | Progress display | Terminal progress: `[Worker X] N/M papers | Xs avg | N errors | ETA: Xm`. Plus summary stats on completion: total processed, error count, average latency, total tokens. | T2.5 | PENDING |
| T2.7 | **PR 3: Submit** | Branch `feat/backfill-parallel-script`. Scope: `backend/scripts/backfill_parallel.py` only. No tests in this PR — they go in PR 4. Label `reviewer:pending`. | T2.6 | PENDING |

## Phase 3: Unit & Integration Testing
| ID | Task | Description | Dependencies | Status |
|----|------|-------------|--------------|--------|
| T3.1 | Partition determinism | Test that `md5(arxiv_id) % N` produces identical assignments across separate Python invocations (simulating crash + restart). Verify even distribution across 4 workers for 100+ real arxiv_ids. | T2.2 | PENDING |
| T3.2 | Session thread safety | Spin up 4 threads writing to a test PostgreSQL database simultaneously. Verify: zero deadlocks, correct row count, no duplicate `arxiv_id` entries per `prompt_version`. | T2.4 | PENDING |
| T3.3 | Adversarial edge cases | Test the inline HTTP + parsing pipeline against adversarial inputs sourced from real arxiv papers: (a) empty string abstract, (b) 1500+ character title, (c) dense LaTeX/Unicode (`$\mathcal{O}(n \log n)$`), (d) abstract with null bytes / UTF-16 surrogates. Verify `sanitize_text` is applied and each case either classifies or fails gracefully without crashing the worker. | T2.3 | PENDING |
| T3.4 | Logger thread safety | Spawn 4 threads each writing 50 JSONL lines concurrently. Verify output file has exactly 200 valid JSON lines with no corruption or interleaving. | T2.5 | PENDING |
| T3.5 | Resume correctness | Simulate a crash: run backfill on 20 papers, kill after 10 are committed. Re-run. Verify: the 10 completed papers are skipped (not re-processed), the remaining 10 are processed, final DB has exactly 20 rows. | T2.4 | PENDING |
| T3.6 | Rollback tagging | Verify all rows written by `backfill_parallel.py` have `model_name="gemma3:12b-parallel-backfill"`. Run `DELETE FROM pattern_experiment_results WHERE model_name = 'gemma3:12b-parallel-backfill'` and confirm clean removal without affecting rows from other sources. | T2.4 | PENDING |
| T3.7 | Timeout handling | Mock an Ollama endpoint that hangs for 200 seconds. Verify the worker times out at 120s, logs an error to JSONL, and moves on to the next paper without crashing. | T2.3 | PENDING |
| T3.8 | **PR 4: Submit** | Branch `test/backfill-parallel`. Scope: all test files for T3.1–T3.7. Label `reviewer:pending`. | T3.7 | PENDING |

## Phase 4: Accuracy Validation
| ID | Task | Description | Dependencies | Status |
|----|------|-------------|--------------|--------|
| T4.1 | Sequential baseline | Run the existing `backfill_patterns.py` on 20 specific papers (spanning diverse categories and edge cases). Record `is_agentic`, `primary_category`, `patterns` for each. | T1.3 | PENDING |
| T4.2 | Parallel comparison | Run `backfill_parallel.py` on the same 20 papers. Diff results against T4.1 baseline. **Pass criteria:** identical `is_agentic` and `primary_category` for all 20. `patterns` array may have minor confidence variations (temperature=0.1 is near-deterministic, not fully deterministic), but category/name pairs must match. | T3 (all), T4.1 | PENDING |
| T4.3 | Document results | Record any discrepancies. If `NUM_PARALLEL` KV cache sharing causes systematic divergence, flag for investigation before proceeding to full backfill. | T4.2 | PENDING |
| T4.4 | **PR 5: Submit** | Branch `docs/backfill-accuracy-validation`. Scope: accuracy comparison results markdown. Label `reviewer:pending`. | T4.3 | PENDING |

## Phase 5: Deployment & Execution
| ID | Task | Description | Dependencies | Status |
|----|------|-------------|--------------|--------|
| T5.1 | Stop production worker | Halt `production_worker.py` to free all 4 Ollama parallel slots for backfill. Verify no classification requests are in flight. | T4.3 | PENDING |
| T5.2 | Open monitoring | Open Grafana dashboard (`http://192.168.1.32:3000`) and mitmweb UI (`http://192.168.1.32:8081`) for live monitoring. | T0.5 | PENDING |
| T5.3 | Execute backfill | SSH into Framework, start `tmux new -s backfill`, launch script. Detach with `Ctrl+B, D`. | T5.1, T5.2 | PENDING |
| T5.4 | Monitor first 50 papers | Watch Grafana for: request rate ~4 req/parallel, latency stable, error rate ~0%, active requests hovering at 4. Tail `backfill_metrics.jsonl` for any anomalies. | T5.3 | PENDING |
| T5.5 | Spot-check results | After first 50 papers, query DB for a sample of 5 results. Manually verify `is_agentic` and `primary_category` look reasonable. Check `num_violations = 0` for majority. | T5.4 | PENDING |
| T5.6 | Full run completion | Let backfill run to completion. Final checks: total rows match expected count, error rate in JSONL, no gaps in partitions. | T5.5 | PENDING |
| T5.7 | Restart production worker | Resume `production_worker.py` after backfill completes. | T5.6 | PENDING |
