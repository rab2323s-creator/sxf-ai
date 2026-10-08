#!/usr/bin/env python3
"""Regression guard for 35 independent models and exact raw-source transcript."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
data=json.loads((root/"data/model-evaluations.json").read_text())
catalog=json.loads((root/"data/model-pricing.json").read_text())
manifest=json.loads((root/"data/evaluation-imports/2026-10-08-priority-10.json").read_text())
models={m["model_id"] for m in catalog["models"]}
benchmarks={b["benchmark_id"] for b in data["benchmarks"]}
covered={o["model_id"] for o in data["observations"] if o["evidence_type"]=="independent"}
assert len(covered)==35, f"Expected 35 independently tested models; found {len(covered)}"
assert len(manifest["entries"])==10
tables={t["id"]:t for t in manifest["source_tables"]}
expected={}
for entry in manifest["entries"]:
    assert entry["model_id"] in models and entry["model_id"] in covered
    table=tables[entry["table"]]
    assert table["source_url"].startswith("https://artificialanalysis.ai/models/comparisons/")
    for benchmark,cells in table["scores"].items():
        assert benchmark in benchmarks
        raw=cells[entry["column"]]
        if not raw or "*" in raw:
            continue
        value=float(raw.rstrip("%"))
        assert value>=0
        expected[(entry["model_id"],benchmark)]=(value,table["source_url"],table["model_variants"][entry["column"]])
new_models={e["model_id"] for e in manifest["entries"]}
seen=set()
for observation in data["observations"]:
    key=observation["observation_id"]
    assert key not in seen, key
    seen.add(key)
    if observation["model_id"] not in new_models: continue
    identity=(observation["model_id"],observation["benchmark_id"])
    assert identity in expected, f"Unreviewed observation: {identity}"
    score,url,variant=expected.pop(identity)
    assert observation["score"]==score,(identity,observation["score"],score)
    assert observation["source_url"]==url
    assert variant in observation["source_name"]
    assert observation["evidence_type"]=="independent"
assert not expected, f"Missing observations: {expected}"
print("PASS: 35 covered models; 90 new measured scores match raw-source transcript")
