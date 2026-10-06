#!/usr/bin/env python3
"""Regression tests for the lightweight model index."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_model_index.py"
spec = importlib.util.spec_from_file_location("build_model_index", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

catalog = json.loads((ROOT / "data/model-pricing.json").read_text(encoding="utf-8"))
published = json.loads((ROOT / "data/model-index.json").read_text(encoding="utf-8"))
built = module.build_index(catalog)

assert built == published, "Published model-index.json is stale"
assert built["model_count"] == len(catalog["models"])
assert built["provider_count"] == len({m["provider"] for m in catalog["models"]})
assert [m["model_id"] for m in built["models"]] == [m["model_id"] for m in catalog["models"]]

heavy = {"official_sources", "provenance", "notes", "pricing", "reasoning", "modalities", "knowledge_cutoff", "positioning", "aliases"}
for row in built["models"]:
    assert not (heavy & set(row)), f"{row['model_id']}: heavy fields leaked into lightweight index"
    assert set(row) == module.INDEX_MODEL_KEYS
    assert set(row["pricing_basis"]) == {"meter", "display_unit"}

full_bytes = len(json.dumps(catalog, separators=(",", ":")).encode())
index_bytes = len(json.dumps(built, separators=(",", ":")).encode())
assert index_bytes < full_bytes * 0.45, f"Index is too heavy: {index_bytes}/{full_bytes} bytes"

print(f"Lightweight model index OK: {built['model_count']} models; {index_bytes}/{full_bytes} bytes")
