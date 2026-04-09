# Adversarial Critique: Parallel Pattern Backfill Implementation Plan (v3)

> Updated after the plan's third revision which incorporated all v2 feedback: per-paper commits, tmux as a requirement, HTTP timeout=120, keep_alive=30m, rollback tagging, adversarial test cases, sanitize_text, and explicit pre-flight gate thresholds.

## Resolution Tracker

### Original 10 Issues (v1)

All resolved.

| # | Issue | Resolved In | How |
|---|-------|-------------|-----|
| 1 | NUM_PARALLEL memory behavior | v2 | q8_0 KV cache + pre-flight stress test |
| 2 | `llm_service` singleton | v2 | Inline HTTP POST, no singleton import |
| 3 | Error recovery / resume | v3 | Hash partitioning + per-paper commits |
| 4 | Testing | v2 | Smoke test + sequential-vs-parallel accuracy diff |
| 5 | Observability | v2 | JSONL log file |
| 6 | DB connection pool starvation | v3 | Per-paper commit + session close cycle |
| 7 | `num_ctx` override | v2 | Forces 4096 in payload |
| 8 | Production worker conflict | v2 | `[!WARNING]` to stop worker, upgraded to **must** in v3 |
| 9 | Partition strategy | v2 | `hash(arxiv_id) % 4` |
| 10 | Verification gaps | v2 | Sequential vs parallel diff on 20 papers |

### v2 Issues (N1–N8)

All resolved in v3.

| # | Issue | How Resolved |
|---|-------|-------------|
| N1 | Commit granularity 5-10, should be 1 | **Fixed** — "commit a single paper at a time" explicitly stated |
| N2 | tmux should be required | **Fixed** — now a mandatory execution context, not an open question |
| N3 | No HTTP timeout | **Fixed** — `timeout=120` hardcoded |
| N4 | No keep_alive | **Fixed** — `"keep_alive": "30m"` in every payload |
| N5 | Pre-flight has no pass/fail thresholds | **Fixed** — explicit gates: <80 GB memory, <2x latency, no OOM, plus load-vs-active memory comparison |
| N6 | q8_0 + num_ctx=4096 interaction | **Fixed** — pre-flight now explicitly tests load-memory vs active-request-memory |
| N7 | Smoke test edge cases | **Fixed** — adversarial papers included: blank abstract, 1500+ char title, dense LaTeX/Unicode |
| N8 | No rollback strategy | **Fixed** — `model_name="gemma3:12b-parallel-backfill"` tagging for clean `DELETE FROM` |

---

## Remaining Observations

The plan is now architecturally complete. What follows are minor observations, not blockers.

### 1. mitmproxy Integration Not Referenced

The plan targets `OLLAMA_BASE_URL/api/chat` but doesn't specify which port. The companion mitmproxy observability doc (`mitmproxy-backfill-observability.md`) expects the backfill to hit `:8434` (mitmproxy proxy port) so that all requests are captured and metrics are extracted. The plan should explicitly state the target URL is `http://localhost:8434/api/chat`, not `:11434`.

If the backfill bypasses mitmproxy and hits Ollama directly, you lose:
- Full request/response capture in mitmweb
- Per-request Prometheus metrics (latency histograms, tokens/sec, active request gauge)
- The Grafana dashboard that depends on those metrics

This is a one-token change (`8434` vs `11434`) but should be explicit in the plan so the implementor doesn't default to the native port.

### 2. `hash()` Is Not Deterministic Across Python Processes

The plan uses `hash(arxiv_id) % 4` for partitioning. Python's built-in `hash()` is randomized across processes by default (since Python 3.3, via `PYTHONHASHSEED`). This means:
- Run 1 assigns paper `2401.12345` to Worker 2
- Run 2 (after crash/restart) assigns the same paper to Worker 0

This breaks the "deterministic resume" property. The fix is trivial — use `hashlib.md5(arxiv_id.encode()).hexdigest()` and take the integer modulo, or set `PYTHONHASHSEED=0` as an environment variable. Since this is a correctness issue for the resume guarantee, it should be specified.

### 3. Single Open Question Remains Unnecessary

The plan still has one open question: "Can I push the config changes to the `192.168.1.32` host directly?" Given that the `[!CAUTION]` block already frames this as requiring user approval, the open question is redundant — it's already answered by the caution block's existence. Minor formatting nit.

### 4. JSONL Schema Not Specified

The plan says the JSONL log includes "timestamp, worker_id, elapsed_time, success_state." For the log to be useful for post-hoc analysis (and for correlation with the mitmproxy Prometheus metrics), it should also include:
- `arxiv_id` — to identify which paper had issues
- `eval_count` / `prompt_eval_count` — token counts from Ollama's response (already available in the response JSON)
- `error_message` — if status is error, what went wrong (timeout? JSON parse failure? HTTP 500?)

Without `arxiv_id`, a JSONL line like `{"worker": 2, "elapsed": 4.3, "status": "error"}` is useless for debugging.

### 5. Pre-flight Should Test Through mitmproxy

The pre-flight gate says "run 4 simultaneous `curl` requests to `/api/chat`." If the backfill will route through mitmproxy (`:8434`), the pre-flight should also route through mitmproxy to verify:
- mitmproxy handles 4 concurrent reverse-proxy connections without choking
- The addon script doesn't introduce latency or errors under parallel load
- Prometheus metrics actually populate

Testing against `:11434` directly proves Ollama works but doesn't validate the full request path.

---

## Verdict

**The plan is ready for implementation.** The architecture is sound, failure modes are addressed, and the verification strategy is thorough. The remaining items above are refinements, not blockers — they can be caught during code review of the actual script.

The only item I'd call "fix before implementing" is **#2 (hash determinism)** — it's a one-line fix but silently breaks resume if missed.
