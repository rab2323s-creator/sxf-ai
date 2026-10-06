#!/usr/bin/env python3
"""Regression tests for deterministic model reverification scheduling."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_reverification_queue.py"
spec = importlib.util.spec_from_file_location("build_reverification_queue", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

catalog = json.loads((ROOT / "data/model-pricing.json").read_text(encoding="utf-8"))
published = json.loads((ROOT / "data/model-reverification.json").read_text(encoding="utf-8"))
built = module.build_queue(catalog)

assert built == published, "Published model-reverification.json is stale"
assert built["as_of"] == catalog["source_verified"]
assert built["summary"]["total"] == len(catalog["models"])
assert len(built["items"]) == len({item["model_id"] for item in built["items"]})
assert {item["model_id"] for item in built["items"]} == {m["model_id"] for m in catalog["models"]}
assert all(item["source_urls"] for item in built["items"]), "Every reverification item needs primary evidence"
assert all(item["review_scope"] == ["identity", "pricing", "specs", "lifecycle"] for item in built["items"])

for item in built["items"]:
    if item["lifecycle_status"] == "preview":
        assert item["review_interval_days"] == 7
    elif item["lifecycle_status"] == "current" and item["pricing_status"] == "official-paid":
        assert item["review_interval_days"] == 30
    elif item["lifecycle_status"] == "current":
        assert item["review_interval_days"] == 45

statuses = [module.STATUS_RANK[item["status"]] for item in built["items"]]
assert statuses == sorted(statuses), "Queue must put overdue/due work before fresh work"

print(
    f"Reverification queue regression tests OK: "
    f"{built['summary']['overdue']} overdue / {built['summary']['due']} due / {built['summary']['fresh']} fresh"
)
