# mitmproxy Observability for Pattern Backfill

This document specifies how to upgrade the existing `ollama-mitmproxy` container to serve as the full observability layer for the parallel pattern backfill — capturing every request/response, exporting per-request Prometheus metrics, and feeding them into the existing Grafana stack.

## Current State

```
ollama-mitmproxy (mitmproxy:latest, Python 3.14)
├── Port 8434 → reverse proxy to Ollama :11434
├── Port 8081 → mitmweb UI (password: ollama)
├── stream_large_bodies=0 (full payload capture)
└── On ollama-monitoring_default bridge network

ollama-metrics (norskhelsenett/ollama-metrics)
├── Port 8082 → /metrics endpoint
├── Only 3 metrics: loaded_models, model_loaded, model_ram_mb
└── Model-level only, no per-request data

ollama-prometheus → scrapes ollama-metrics:8080 every 15s
ollama-grafana → dashboards from Prometheus datasource
```

**Gap:** No per-request metrics (latency, tokens/sec, queue depth, error rate). The metrics sidecar only reports model state.

## Target Architecture

```
backfill_parallel.py (4 threads)
    │
    ▼
:8434 ─── ollama-mitmproxy ───┬─── :11434 (Ollama)
           │                   │
           │ addon script      │
           ▼                   │
    Prometheus metrics ◄───────┘
    exposed on :8765
           │
           ▼
    ollama-prometheus (scrapes :8765)
           │
           ▼
    ollama-grafana (dashboard)
```

The mitmproxy addon script intercepts every `/api/chat` response, extracts Ollama's native timing/token metadata, and exposes it as Prometheus metrics on a dedicated port inside the container.

## Implementation

### 1. mitmproxy Addon Script

A Python addon that hooks into mitmproxy's `response` event. For every Ollama `/api/chat` response, it parses the JSON body and updates Prometheus counters/histograms.

#### [NEW] `ollama-monitoring/mitmproxy/ollama_metrics_addon.py`

```python
"""
mitmproxy addon: extracts per-request metrics from Ollama API responses
and exposes them as Prometheus metrics.

Metrics exposed:
  - ollama_request_duration_seconds (histogram) — total request wall time
  - ollama_inference_duration_seconds (histogram) — model eval time only
  - ollama_prompt_eval_duration_seconds (histogram) — prompt processing time
  - ollama_tokens_generated_total (counter) — output tokens
  - ollama_tokens_input_total (counter) — input/prompt tokens
  - ollama_requests_total (counter) — request count by model and status
  - ollama_tokens_per_second (gauge) — last observed generation speed
  - ollama_active_requests (gauge) — concurrent in-flight requests
"""

import json
import logging
import threading
from mitmproxy import http

from prometheus_client import (
    Counter, Histogram, Gauge, start_http_server
)

logger = logging.getLogger("ollama_metrics")

# ── Prometheus metrics ──────────────────────────────────────────────

REQUEST_DURATION = Histogram(
    "ollama_request_duration_seconds",
    "Total wall-clock request duration",
    ["model"],
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120, 300),
)

INFERENCE_DURATION = Histogram(
    "ollama_inference_duration_seconds",
    "Model eval (token generation) duration",
    ["model"],
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120),
)

PROMPT_EVAL_DURATION = Histogram(
    "ollama_prompt_eval_duration_seconds",
    "Prompt evaluation (prefill) duration",
    ["model"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 20),
)

TOKENS_GENERATED = Counter(
    "ollama_tokens_generated_total",
    "Total output tokens generated",
    ["model"],
)

TOKENS_INPUT = Counter(
    "ollama_tokens_input_total",
    "Total input/prompt tokens processed",
    ["model"],
)

REQUESTS_TOTAL = Counter(
    "ollama_requests_total",
    "Total requests by model and status",
    ["model", "status"],
)

TOKENS_PER_SECOND = Gauge(
    "ollama_tokens_per_second",
    "Last observed token generation rate",
    ["model"],
)

ACTIVE_REQUESTS = Gauge(
    "ollama_active_requests",
    "Number of in-flight requests",
    ["model"],
)

# ── Prometheus HTTP server (started once) ───────────────────────────

_server_started = False
_lock = threading.Lock()

METRICS_PORT = 8765


def _ensure_server():
    global _server_started
    with _lock:
        if not _server_started:
            start_http_server(METRICS_PORT)
            logger.info(f"Prometheus metrics server started on :{METRICS_PORT}")
            _server_started = True


# ── mitmproxy addon class ──────────────────────────────────────────

class OllamaMetricsAddon:
    def load(self, loader):
        _ensure_server()
        logger.info("OllamaMetricsAddon loaded")

    def request(self, flow: http.HTTPFlow):
        """Track active requests on /api/chat."""
        if "/api/chat" in flow.request.path:
            try:
                body = json.loads(flow.request.content)
                model = body.get("model", "unknown")
                ACTIVE_REQUESTS.labels(model=model).inc()
                # Stash model name for use in response handler
                flow.metadata["ollama_model"] = model
            except Exception:
                pass

    def response(self, flow: http.HTTPFlow):
        """Extract metrics from completed /api/chat responses."""
        if "/api/chat" not in flow.request.path:
            return

        model = flow.metadata.get("ollama_model", "unknown")
        ACTIVE_REQUESTS.labels(model=model).dec()

        status = "ok" if flow.response.status_code == 200 else "error"
        REQUESTS_TOTAL.labels(model=model, status=status).inc()

        # Wall-clock duration from mitmproxy's own timing
        if flow.response.timestamp_end and flow.request.timestamp_start:
            wall_time = flow.response.timestamp_end - flow.request.timestamp_start
            REQUEST_DURATION.labels(model=model).observe(wall_time)

        if flow.response.status_code != 200:
            return

        try:
            data = json.loads(flow.response.content)
        except (json.JSONDecodeError, TypeError):
            return

        # ── Ollama native API response fields ──
        # eval_count:            output tokens generated
        # eval_duration:         time generating tokens (nanoseconds)
        # prompt_eval_count:     input tokens processed
        # prompt_eval_duration:  time processing prompt (nanoseconds)

        eval_count = data.get("eval_count", 0)
        eval_duration_ns = data.get("eval_duration", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)

        if eval_count:
            TOKENS_GENERATED.labels(model=model).inc(eval_count)
        if prompt_eval_count:
            TOKENS_INPUT.labels(model=model).inc(prompt_eval_count)

        if eval_duration_ns > 0:
            eval_secs = eval_duration_ns / 1e9
            INFERENCE_DURATION.labels(model=model).observe(eval_secs)
            if eval_count > 0:
                TOKENS_PER_SECOND.labels(model=model).set(eval_count / eval_secs)

        if prompt_eval_duration_ns > 0:
            PROMPT_EVAL_DURATION.labels(model=model).observe(
                prompt_eval_duration_ns / 1e9
            )


addons = [OllamaMetricsAddon()]
```

### 2. Container Changes

#### [MODIFY] `ollama-monitoring/docker-compose.yml` — mitmproxy service

Mount the addon script into the container and pass it via `--scripts`. Expose the Prometheus metrics port. Install `prometheus-client` at startup.

```yaml
  mitmproxy:
    image: mitmproxy/mitmproxy:latest
    container_name: ollama-mitmproxy
    command: >
      sh -c "pip install --quiet prometheus-client &&
      mitmweb
      --web-host 0.0.0.0
      --web-port 8080
      --mode reverse:http://host.docker.internal:11434@11434
      --set stream_large_bodies=0
      --set web_password=ollama
      --scripts /addons/ollama_metrics_addon.py"
    ports:
      - "8434:11434"   # proxied Ollama API
      - "8081:8080"    # mitmproxy web inspector
      - "8765:8765"    # Prometheus metrics endpoint
    volumes:
      - ./mitmproxy/ollama_metrics_addon.py:/addons/ollama_metrics_addon.py:ro,z
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

**Note on `pip install` in entrypoint:** This runs on every container restart (~3s overhead). For a production-permanent setup, build a custom image with a Dockerfile. For the backfill campaign, the entrypoint approach is acceptable.

#### [MODIFY] `ollama-monitoring/prometheus/prometheus.yml` — add scrape target

```yaml
scrape_configs:
  - job_name: "ollama-metrics"
    static_configs:
      - targets: ["ollama-metrics:8080"]

  - job_name: "ollama-request-metrics"
    static_configs:
      - targets: ["ollama-mitmproxy:8765"]
    scrape_interval: 5s    # faster for real-time backfill monitoring

  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9091"]
```

### 3. Grafana Dashboard

#### [NEW] `ollama-monitoring/grafana/provisioning/dashboards/dashboard.yml`

```yaml
apiVersion: 1

providers:
  - name: "default"
    orgId: 1
    folder: ""
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
```

#### [NEW] `ollama-monitoring/grafana/provisioning/dashboards/ollama-backfill.json`

A pre-built dashboard with 6 panels:

| Panel | Type | Query | Purpose |
|---|---|---|---|
| Request Rate | Time series | `rate(ollama_requests_total[1m])` | Throughput — are all 4 workers active? |
| Request Latency (p50/p95/p99) | Time series | `histogram_quantile(0.95, rate(ollama_request_duration_seconds_bucket[5m]))` | Detect latency spikes or Vulkan thrashing |
| Tokens/sec | Gauge | `ollama_tokens_per_second` | Real-time generation speed |
| Active Requests | Time series | `ollama_active_requests` | Queue depth — should hover at 4 during backfill |
| Cumulative Tokens | Stat | `ollama_tokens_generated_total` + `ollama_tokens_input_total` | Total work done |
| Error Rate | Time series | `rate(ollama_requests_total{status="error"}[5m])` | Catch systematic failures early |
| Model Memory | Gauge | `ollama_model_ram_mb` | From existing sidecar — watch for OOM |

The actual JSON for this dashboard is ~200 lines. I'll generate it during implementation. The key is that it's auto-provisioned — no manual Grafana setup needed.

#### [MODIFY] `ollama-monitoring/docker-compose.yml` — Grafana volumes

Add the dashboards directory mount:

```yaml
  grafana:
    # ... existing config ...
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro,z
```

This already mounts the full `provisioning/` tree, so adding `provisioning/dashboards/` is picked up automatically.

### 4. Backfill Script Integration

The backfill script targets `:8434` (mitmproxy) instead of `:11434` (Ollama directly):

```python
# In backfill_parallel.py — each worker's HTTP POST
OLLAMA_URL = "http://localhost:8434/api/chat"  # through mitmproxy

response = requests.post(OLLAMA_URL, json=payload, timeout=120)
```

**No other changes needed.** The mitmproxy addon handles everything transparently.

## Deployment Steps

```bash
ssh gsumanth@192.168.1.32

# 1. Create the addon script
mkdir -p ~/ollama-monitoring/mitmproxy
# (write ollama_metrics_addon.py)

# 2. Update prometheus.yml with new scrape target
# (edit ~/ollama-monitoring/prometheus/prometheus.yml)

# 3. Create Grafana dashboard provisioning
mkdir -p ~/ollama-monitoring/grafana/provisioning/dashboards
# (write dashboard.yml and ollama-backfill.json)

# 4. Recreate affected containers
cd ~/ollama-monitoring
podman compose down
podman compose up -d

# 5. Verify
curl -s http://localhost:8765/metrics | grep ollama_requests
# Should show metric definitions (0 values until backfill starts)

# Open Grafana at http://192.168.1.32:3000 (admin/ollama)
# The "Ollama Backfill" dashboard should appear automatically
```

## Capacity Concerns

### mitmproxy Memory Growth

mitmproxy stores all flows in memory by default. With 4 workers × ~2000 papers, that's ~8000 request/response pairs. Each classification response is ~500 bytes of JSON, but the request (V6 CoT prompt + abstract) is ~2-3 KB. At 8000 flows × ~4 KB average = ~32 MB. Manageable.

**However**, the mitmweb UI retains all flows for browsing. For very long backfills (10,000+ papers), consider:

- Periodically saving and clearing flows via the mitmweb UI
- Or adding `--set flow_detail=0` to reduce per-flow storage
- Or running with `--set termlog_verbosity=error` to reduce logging overhead

### Prometheus Storage

At 5s scrape interval with ~10 metrics × 1 label, Prometheus ingests ~120 samples/minute. For an 8-hour backfill, that's ~57,600 samples — trivial for Prometheus (< 10 MB).

### Proxy Latency Overhead

mitmproxy adds ~2-5ms per request for reverse proxying. Against a 3-5 second classification call, this is 0.1% overhead. The addon's JSON parsing adds another ~0.1ms. Negligible.

## Verification

1. **Addon loads correctly:**
   ```bash
   podman logs ollama-mitmproxy 2>&1 | grep "OllamaMetricsAddon"
   # Should show "OllamaMetricsAddon loaded"
   ```

2. **Metrics endpoint responds:**
   ```bash
   curl -s http://localhost:8765/metrics | grep ollama_request
   ```

3. **Single request test:**
   ```bash
   curl -s http://localhost:8434/api/chat -d '{
     "model": "gemma3:12b",
     "messages": [{"role":"user","content":"hi"}],
     "stream": false
   }'
   # Then check:
   curl -s http://localhost:8765/metrics | grep ollama_requests_total
   # Should show: ollama_requests_total{model="gemma3:12b",status="ok"} 1.0
   ```

4. **Grafana dashboard:**
   - Open `http://192.168.1.32:3000`
   - Navigate to Dashboards → "Ollama Backfill"
   - All panels should show data from the test request above

5. **Concurrent load test (pre-flight):**
   ```bash
   # Fire 4 requests simultaneously to verify metrics under parallel load
   for i in 1 2 3 4; do
     curl -s http://localhost:8434/api/chat -d '{
       "model": "gemma3:12b",
       "messages": [{"role":"user","content":"classify this paper"}],
       "stream": false,
       "options": {"num_ctx": 4096}
     }' &
   done
   wait
   # Check active_requests peaked at 4, all returned status="ok"
   curl -s http://localhost:8765/metrics | grep -E "requests_total|active"
   ```

## Files Changed

| File | Action | Purpose |
|---|---|---|
| `ollama-monitoring/mitmproxy/ollama_metrics_addon.py` | **NEW** | Prometheus metrics addon for mitmproxy |
| `ollama-monitoring/docker-compose.yml` | **MODIFY** | Mount addon, expose :8765, pip install |
| `ollama-monitoring/prometheus/prometheus.yml` | **MODIFY** | Add mitmproxy metrics scrape target |
| `ollama-monitoring/grafana/provisioning/dashboards/dashboard.yml` | **NEW** | Dashboard auto-provisioning config |
| `ollama-monitoring/grafana/provisioning/dashboards/ollama-backfill.json` | **NEW** | Pre-built Grafana dashboard |
