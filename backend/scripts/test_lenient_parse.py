"""Deterministic unit check for OllamaProvider._loads_lenient.

Reproduces the dominant straggler failure mode — raw LaTeX backslashes in the
"reasoning" string that strict json.loads rejects as "Invalid \\escape" — and
confirms the lenient parser recovers the classification fields.
"""
import json
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.llm_service import OllamaProvider

# raw backslashes exactly as nemotron emits them in math-heavy reasoning
bad = r'{"reasoning": "Uses \alpha-divergence over \mathbb{R}^n and \nabla f", "is_agentic": false, "primary_category": "architecture", "patterns": []}'

print("strict json.loads:")
try:
    json.loads(bad)
    print("  parsed (UNEXPECTED — test invalid)")
except json.JSONDecodeError as e:
    print(f"  FAILS as expected: {e}")

print("_loads_lenient:")
r = OllamaProvider._loads_lenient(bad)
assert r["is_agentic"] is False and r["primary_category"] == "architecture"
print(f"  RECOVERED -> is_agentic={r['is_agentic']} primary_category={r['primary_category']}")

# also confirm a normal valid object still round-trips untouched
good = '{"reasoning": "plain text", "is_agentic": true, "primary_category": "multi_agent", "patterns": []}'
assert OllamaProvider._loads_lenient(good)["is_agentic"] is True
print("  valid JSON still parses unchanged: OK")
print("\nPASS")
