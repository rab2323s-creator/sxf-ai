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
assert len(candidate_queue["candidates"]) == 2, "Two unapproved candidates must remain pending"
explorer_js = (ROOT / "models" / "explorer.js").read_text(encoding="utf-8")
assert '<option value="image-generation">Image generation</option>' in explorer_js, "Image generation task filter is missing"

# Visual generation expansion: preserve source-backed native billing and generated routes.
visual_models = {
    "gemini-nano-banana-2.1": ("Google", "image-generation"),
    "gemini-3-pro-image": ("Google", "image-generation"),
    "kling-3.0": ("Kling AI", "video-generation"),
    "dreamina-seedance-2-0-260128": ("ByteDance", "video-generation"),
}
assert len(catalog["models"]) >= 79, "Expected four reviewed visual-generation models"
for model_id, (provider, capability) in visual_models.items():
    model = next(row for row in catalog["models"] if row["model_id"] == model_id)
    assert model["provider"] == provider and capability in model["capabilities"], f"{model_id}: provider or capability mismatch"
    assert not model["calculator_eligible"], f"{model_id}: media billing must not enter text arithmetic"
    assert model["page_template"] == "catalog-reference", f"{model_id}: missing page generation"
    assert (ROOT / model["sxf_url"].lstrip("/") / "index.html").is_file(), f"{model_id}: model page missing"
assert next(x for x in catalog["models"] if x["model_id"] == "kling-3.0")["pricing_status"] == "not-published", "Never convert Kling Credits into invented USD API prices"
assert next(x for x in catalog["models"] if x["model_id"] == "dreamina-seedance-2-0-260128")["pricing_basis"]["display_unit"].find("480p/720p") >= 0, "Seedance price must retain its billing caveat"
for slug in ("nano-banana-2-1-vs-nano-banana-pro", "kling-3-0-vs-seedance-2-0"):
    comparison_page = ROOT / "compare" / slug / "index.html"
    assert comparison_page.is_file(), f"{slug}: generated comparison page missing"
    assert f'https://sxf.si/compare/{slug}/' in comparison_page.read_text(encoding="utf-8"), f"{slug}: canonical comparison missing"
assert '<option value="video-generation">Video generation</option>' in (ROOT / "models/explorer.js").read_text(encoding="utf-8")

# Creative specialist continuation — verify unique routes, native meters and SEO.
creative_specialists = {
    "gpt-image-2.5-flare": ("OpenAI", "image-generation", "tokens"),
    "gemini-omni-1.1-flash": ("Google", "video-generation", "tokens"),
    "lyria-3.5": ("Google", "music-generation", "requests"),
    "flux-2-max": ("Black Forest Labs", "image-generation", "images"),
    "eleven_v4": ("ElevenLabs", "tts", "characters"),
    "eleven_v4_turbo": ("ElevenLabs", "tts", "characters"),
}
assert len(catalog["models"]) >= 85, "Expected 85 verified models after creative batch"
for mid, (provider,capability,meter) in creative_specialists.items():
    row = next(m for m in catalog["models"] if m["model_id"] == mid)
    assert row["provider"] == provider and capability in row["capabilities"], f"{mid}: provider or capability mismatch"
    assert row["pricing_basis"]["meter"] == meter, f"{mid}: native billing unit mismatch"
    assert not row["calculator_eligible"], f"{mid}: media model incorrectly in text calculator"
    assert row["page_template"] == "catalog-reference", f"{mid}: no dedicated page generator"
    route = ROOT / row["sxf_url"].lstrip("/") / "index.html"
    assert route.is_file(), f"{mid}: missing generated page"
    body = route.read_text(encoding="utf-8")
    assert f'https://sxf.si{row["sxf_url"]}' in body and "data-model-history" in body, f"{mid}: canonical/history mismatch"
for mid in ("eleven_v4", "eleven_v4_turbo"):
    assert next(m for m in catalog["models"] if m["model_id"] == mid)["pricing_status"] == "not-published", f"{mid}: invented USD API rate"
assert 'music-generation' in (ROOT / "models/explorer.js").read_text(encoding="utf-8")
for slug in ("gpt-image-2-5-sunburst-vs-flare", "eleven-v4-vs-eleven-v4-turbo", "gemini-omni-flash-vs-kling-3-0", "flux-2-max-vs-nano-banana-pro"):
    html = ROOT / "compare" / slug / "index.html"
    assert html.is_file(), f"{slug}: missing comparison page"
    text = html.read_text(encoding="utf-8")
    assert "SPECIALIST BUYER GUIDE" in text and f'https://sxf.si/compare/{slug}/' in text, f"{slug}: missing specialist metadata"

# 10 verified creator/voice models — canonical, SEO, and native-meter regression.
next_ten = {
    "gpt-image-2": ("OpenAI", "image-generation", "tokens"),
    "ideogram-v4": ("Ideogram", "image-generation", "images"),
    "ideogram-v3": ("Ideogram", "image-generation", "images"),
    "gen4.5": ("Runway", "video-generation", "minutes"),
    "nova-3": ("Deepgram", "transcription", "minutes"),
    "flux-general-en": ("Deepgram", "transcription", "minutes"),
    "scribe_v2": ("ElevenLabs", "transcription", "minutes"),
    "scribe_v2_realtime": ("ElevenLabs", "transcription", "minutes"),
    "flux-2-klein-9b": ("Black Forest Labs", "image-generation", "images"),
    "flux-2-pro": ("Black Forest Labs", "image-generation", "images"),
}
assert len(catalog["models"]) >= 95, "Expected at least 95 models after ten source-verified additions"
for mid, (provider,task,meter) in next_ten.items():
    row=next(m for m in catalog["models"] if m["model_id"] == mid)
    assert row["provider"] == provider and task in row["capabilities"], f"{mid}: provider/task mismatch"
    assert row["pricing_basis"]["meter"] == meter and row["calculator_eligible"] is False, f"{mid}: incompatible generic token calculator"
    reference = ROOT / row["sxf_url"].strip("/") / "index.html"
    assert reference.is_file(), f"{mid}: no generated model reference"
    text=reference.read_text(encoding="utf-8")
    assert f"https://sxf.si{row['sxf_url']}" in text and "data-model-history" in text and "data-model-comparisons" in text, f"{mid}: missing SEO/history/comparison link"
for slug in ("gpt-image-2-vs-gpt-image-2-5-flare", "ideogram-4-vs-ideogram-3", "runway-gen-4-5-vs-kling-3-0", "deepgram-nova-3-vs-elevenlabs-scribe-v2", "deepgram-flux-vs-scribe-realtime-v2", "flux-2-pro-vs-flux-2-klein-9b"):
    comparison_file=ROOT / "compare" / slug / "index.html"
    assert comparison_file.is_file(), f"{slug}: comparison missing"
    html=comparison_file.read_text(encoding="utf-8")
    specialist_present = ("SPECIALIST BUYER GUIDE" in html or (slug == "deepgram-nova-3-vs-elevenlabs-scribe-v2" and "Speech-to-text pricing:" in html and "Original SXF reproducibility lab" in html))
    assert specialist_present and f"https://sxf.si/compare/{slug}/" in html, f"{slug}: SEO or decision factors missing"

print(f"Catalog regression tests OK: {len(catalog['models'])} models")

# Verified 100-model release gates
assert len(catalog["models"]) == 100
for mid in ["claude-haiku-5-5","gemini-3.1-pro-preview","gemini-3.1-flash-image","gemini-3.8-live-extended-thinking","stable-image-ultra"]:
    row = next(x for x in catalog["models"] if x["model_id"] == mid)
    assert row["official_sources"] and row["calculator_eligible"] is False
    page=ROOT / row["sxf_url"].strip("/") / "index.html"
    assert page.is_file() and f"https://sxf.si{row['sxf_url']}" in page.read_text(encoding="utf-8")
for mid in ("claude-haiku-5-5", "gemini-3.1-pro-preview"):
    row=next(x for x in catalog["models"] if x["model_id"] == mid)
    assert row["pricing"].get("tiered") and not row["pricing"].get("standard")
for slug in ["claude-haiku-5-5-vs-claude-sonnet-5-5","gemini-3-1-pro-preview-vs-gemini-3-8-flash","nano-banana-2-vs-nano-banana-2-1","gemini-3-8-live-extended-thinking-vs-gemini-3-8-live","stable-image-ultra-vs-flux-2-pro"]:
    page=ROOT / "compare" / slug / "index.html"
    assert page.is_file() and f"https://sxf.si/compare/{slug}/" in page.read_text(encoding="utf-8")
