#!/usr/bin/env python3
"""Regression tests for the generated model catalog."""

from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_model_catalog.py"

spec = importlib.util.spec_from_file_location("build_model_catalog", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

catalog = module.build_catalog()
published = json.loads((ROOT / "data" / "model-pricing.json").read_text(encoding="utf-8"))

assert catalog == published, "Generated catalog differs from published data/model-pricing.json"
assert len(catalog["models"]) == len({m["model_id"] for m in catalog["models"]}), "Duplicate model IDs"
assert all(m["official_sources"] for m in catalog["models"]), "Every model must retain official sources"
assert all(m["provenance"]["evidence"] for m in catalog["models"]), "Every model must retain field evidence"
assert all(
    (not m["calculator_eligible"]) or (m["pricing_status"] == "official-paid" and m["pricing"].get("standard"))
    for m in catalog["models"]
), "Calculator-eligible models require official Standard pricing"

print(f"Catalog regression tests OK: {len(catalog['models'])} models")
