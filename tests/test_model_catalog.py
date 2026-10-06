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
assert catalog["schema_version"] == "1.6", "Generalized pricing units require schema v1.6"
assert all(set(m["access"]) == {"official_api", "open_weight", "self_hostable"} for m in catalog["models"]), "Every model must have explicit access taxonomy"
assert all(m["lifecycle"]["status"] in {"current", "preview", "legacy", "deprecated"} for m in catalog["models"]), "Every model must have lifecycle status"
assert all(m["capabilities"] for m in catalog["models"]), "Every model must have structured capabilities"
meters = {m["pricing_basis"]["meter"] for m in catalog["models"]}
assert {"tokens", "pages", "minutes", "search_units"}.issubset(meters), "Specialist batch must exercise multiple pricing meters"
assert all(
    m["pricing_basis"]["quantity"] == 1_000_000
    for m in catalog["models"]
    if m["pricing_basis"]["meter"] == "tokens"
), "Token rates must preserve per-million arithmetic"
assert any("ocr" in m["capabilities"] for m in catalog["models"]), "OCR specialist coverage missing"
assert any("transcription" in m["capabilities"] for m in catalog["models"]), "Transcription specialist coverage missing"
assert any("rerank" in m["capabilities"] for m in catalog["models"]), "Rerank specialist coverage missing"
assert any("embeddings" in m["capabilities"] for m in catalog["models"]), "Embeddings specialist coverage missing"
assert all((m["access"]["self_hostable"] is False) or m["access"]["open_weight"] is True for m in catalog["models"]), "Self-hostable models must be open-weight"
assert all(
    (not m["calculator_eligible"]) or (m["pricing_status"] == "official-paid" and m["pricing"].get("standard"))
    for m in catalog["models"]
), "Calculator-eligible models require official Standard pricing"

print(f"Catalog regression tests OK: {len(catalog['models'])} models")
