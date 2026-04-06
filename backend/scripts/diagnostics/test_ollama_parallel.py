#!/usr/bin/env python3
import time
import requests
import concurrent.futures
import sys

OLLAMA_URL = "http://192.168.1.32:8434/api/chat"
MODEL = "gemma3:12b"

def test_request(worker_id):
    prompt = "Classify this paper: 'Attention is all you need'. Just respond with JSON."
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.1
        }
    }
    start = time.time()
    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=30)
        res.raise_for_status()
        elapsed = time.time() - start
        return worker_id, elapsed, res.json()
    except Exception as e:
        elapsed = time.time() - start
        return worker_id, elapsed, str(e)

if __name__ == "__main__":
    print(f"--- baseline single request ---")
    _, single_latency, data = test_request(0)
    print(f"Single req latency: {single_latency:.2f}s")
    if isinstance(data, dict):
        print(f"Eval count: {data.get('eval_count', 'N/A')}")
    else:
        print(f"Error: {data}")
        sys.exit(1)

    print(f"\n--- Parallel 4 requests ---")
    start_all = time.time()
    latencies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(test_request, i) for i in range(4)]
        for f in concurrent.futures.as_completed(futures):
            w_id, lat, res_data = f.result()
            latencies.append(lat)
            success = isinstance(res_data, dict)
            print(f"Worker {w_id} finished in {lat:.2f}s - Success: {success}")

    avg_parallel = sum(latencies)/len(latencies)
    print(f"\nTotal parallel wall time: {time.time() - start_all:.2f}s")
    print(f"Average latency per request: {avg_parallel:.2f}s")
    if avg_parallel < 2 * single_latency:
        print("PASS: Parallel latency is within 2x of baseline.")
    else:
        print(f"WARNING: Parallel latency ({avg_parallel:.2f}s) is > 2x baseline ({single_latency:.2f}s)")
