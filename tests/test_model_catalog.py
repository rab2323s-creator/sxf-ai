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

# Previously shared guide links must resolve to unique, indexable model references.
for model_id, expected_route in {
    "claude-sonnet-5": "/models/claude-sonnet-5/",
    "claude-haiku-4-5-20251001": "/models/claude-haiku-4-5/",
}.items():
    model = next(row for row in catalog["models"] if row["model_id"] == model_id)
    assert model["sxf_url"] == expected_route, f"{model_id}: expected dedicated page"
    assert model.get("page_template") == "catalog-reference", f"{model_id}: missing page generator"
    html_path = ROOT / expected_route.lstrip("/") / "index.html"
    assert html_path.exists(), f"{model_id}: generated HTML file missing"
    html = html_path.read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="https://sxf.si{expected_route}"' in html, f"{model_id}: canonical mismatch"
    assert 'data-model-history' in html, f"{model_id}: missing verified history"

# New multimodal specialist records must not silently enter text-only arithmetic.
selected_specialists = {
    "gpt-image-2.5-sunburst": ("OpenAI", "image-generation"),
    "gpt-realtime-2.1": ("OpenAI", "speech-to-speech"),
    "gpt-realtime-2.1-mini": ("OpenAI", "speech-to-speech"),
    "gemini-3.8-live": ("Google", "speech-to-speech"),
    "gemini-embedding-2": ("Google", "embeddings"),
}
assert len(catalog["models"]) >= 75, "Expected the approved specialist batch"
for model_id, (provider, capability) in selected_specialists.items():
    model = next(row for row in catalog["models"] if row["model_id"] == model_id)
    assert model["provider"] == provider, f"{model_id}: provider mismatch"
    assert capability in model["capabilities"], f"{model_id}: missing capability"
    assert model["calculator_eligible"] is False, f"{model_id}: mixed-modality specialist must not enter text calculator"
    assert model["pricing_basis"]["meter"] == "tokens", f"{model_id}: expected published native unit"
    assert model["page_template"] == "catalog-reference", f"{model_id}: missing generated page contract"
    assert model["sxf_url"].startswith("/models/"), f"{model_id}: missing canonical route"
    reference = ROOT / model["sxf_url"].lstrip("/") / "index.html"
    assert reference.is_file(), f"{model_id}: missing HTML reference"
    html = reference.read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="https://sxf.si{model["sxf_url"]}"' in html, f"{model_id}: wrong canonical URL"
    assert "data-model-history" in html and "data-what-changed" in html, f"{model_id}: missing provenance modules"

candidate_queue = json.loads((ROOT / "data" / "model-candidates" / "queue.json").read_text(encoding="utf-8"))
assert not selected_specialists.keys() & {item["proposed_record"]["model_id"] for item in candidate_queue["candidates"]}, "Published models still appear as pending candidates"
assert len(candidate_queue["candidates"]) == 4, "Four unapproved candidates must remain pending"
explorer_js = (ROOT / "models" / "explorer.js").read_text(encoding="utf-8")
assert '<option value="image-generation">Image generation</option>' in explorer_js, "Image generation task filter is missing"

print(f"Catalog regression tests OK: {len(catalog['models'])} models")
