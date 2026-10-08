#!/usr/bin/env python3
"""Guard model evaluation imports against coverage inflation and data drift."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"data/model-evaluations.json").read_text())
catalog=json.loads((root/"data/model-pricing.json").read_text())
ids={m["model_id"] for m in catalog["models"]}
bench={b["benchmark_id"] for b in d["benchmarks"]}
seen=set()
for o in d["observations"]:
    assert o["model_id"] in ids,o["model_id"]
    assert o["benchmark_id"] in bench,o["benchmark_id"]
    assert o["observation_id"] not in seen,o["observation_id"]
    seen.add(o["observation_id"])
    assert o["evidence_type"] in ("independent","vendor-reported")
    assert isinstance(o.get("score"),(int,float))
    assert o["source_url"].startswith("https://"),o["source_url"]
    assert o.get("observed_at") and o.get("comparable_group")
    assert all(k in o["model_configuration"] for k in ("reasoning_effort","fallback","tools"))
priority={"gpt-6-luna","gpt-5.6-sol","claude-sonnet-5-5","claude-sonnet-5","llama-4-scout","llama-4-maverick"}
covered={o["model_id"] for o in d["observations"] if o["evidence_type"]=="independent"}
assert priority <= covered,priority-covered
print("PASS: evaluation evidence schema, source URLs, IDs and priority coverage")
