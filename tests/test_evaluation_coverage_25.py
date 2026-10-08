#!/usr/bin/env python3
"""Check independently sourced 13-model import against reviewed source manifest."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
data=json.loads((root/"data/model-evaluations.json").read_text())
manifest=json.loads((root/"data/evaluation-imports/2026-10-08-priority-13.json").read_text())
catalog=json.loads((root/"data/model-pricing.json").read_text())
models={m["model_id"] for m in catalog["models"]}
benchmarks={b["benchmark_id"] for b in data["benchmarks"]}
prior={o["model_id"] for o in data["observations"] if o["evidence_type"]=="independent"}
assert len(prior)>=25, f"Expected at least the previously verified 25 models; got {len(prior)}"
entries=manifest["entries"]
assert len(entries)==13 and len({e["model_id"] for e in entries})==13
expected={}
for entry in entries:
    assert entry["model_id"] in models
    assert entry["model_id"] in prior
    assert entry["source_url"].startswith("https://artificialanalysis.ai/models/comparisons/")
    assert entry["scores"]
    for benchmark,score in entry["scores"].items():
        assert benchmark in benchmarks
        assert isinstance(score,(int,float)) and not isinstance(score,bool) and score>=0
        expected[(entry["model_id"],benchmark)]=score
    if entry["model_id"]=="grok-4.3":
        assert "aa-intelligence-index-v4.3.2" not in entry["scores"], "Do not import estimated index scores"
seen=set()
for obs in data["observations"]:
    assert obs["observation_id"] not in seen
    seen.add(obs["observation_id"])
    if obs["model_id"] not in {e["model_id"] for e in entries}: continue
    k=(obs["model_id"],obs["benchmark_id"])
    assert k in expected, f"Unreviewed import: {k}"
    assert obs["score"]==expected[k], f"Transcript mismatch: {k}"
    assert obs["evidence_type"]=="independent"
    assert obs["source_url"]==next(e["source_url"] for e in entries if e["model_id"]==obs["model_id"])
    del expected[k]
assert not expected, f"Missing evaluation import observations: {expected}"
print(f"PASS: 25 covered models; 13 new models verified against source manifest")
