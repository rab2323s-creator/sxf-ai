#!/usr/bin/env python3
"""Source-cited updates must be present after every full and snapshot rebuild."""
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from model_editorial_updates import apply_update, load_register

def main():
    register = load_register(ROOT)
    stamp = register["date"]
    assert stamp >= "2026-11-24"
    assert len(register["updates"]) >= 60
    assert {"llama-4-scout", "llama-4-maverick", "gpt-oss-120b", "nova-3", "flux-general-en", "ideogram-v4", "ideogram-v3", "flux-2-max", "flux-2-pro", "flux-2-klein-9b"} <= register["updates"].keys()
    assert {"mistral-small-4","mistral-ocr-4-1","ministral-14b-2512","ministral-8b-2512","ministral-3b-2512","mistral-embed","shieldstral-1-0","gemini-3-1-pro-preview","gemini-3-1-flash-image","gemini-3-pro-image"} <= register["updates"].keys()
    assert {"embed-v4-0","embed-v5-0-pro","embed-v5-0-fast","rerank-4-pro","rerank-4-fast","parse-v5-0","north-mini-code-1-0","command-a-reasoning","codestral","codestral-embed"} <= register["updates"].keys()
    assert {"gpt-image-2", "gemini-omni-1-1-flash", "gemini-3-8-live", "gemini-3-8-live-extended-thinking", "gemini-3-8-flash-tts", "gemini-3-8-flash-lite-tts", "gpt-realtime-2-1-mini", "gpt-transcribe", "gpt-live-transcribe", "gpt-realtime-translate"} <= register["updates"].keys()
    assert all(row.get("date", stamp) >= "2026-11-24" for row in register["updates"].values())
    for slug, row in register["updates"].items():
        stamp = row.get("date", register["date"])
        path = ROOT / "models" / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        marker = f'data-verified-model-update="{slug}"'
        assert page.count(marker) == 1, slug
        assert stamp in page and row["title"] in page, slug
        assert all(url in page for url, _label in row["sources"]), slug
        for old, new in row.get("replacements", []):
            if old not in new:
                assert old not in page, (slug, old)
        normalized = apply_update(page, slug, row, stamp)
        assert apply_update(normalized, slug, row, stamp) == normalized, slug
        schemas = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page, re.S)
        assert schemas, slug
        found = False
        for schema in schemas:
            obj = json.loads(schema)
            nodes = obj if isinstance(obj, list) else obj.get("@graph", [obj])
            for node in nodes:
                if node.get("@type") in {"WebPage", "CollectionPage", "TechArticle", "Article"}:
                    assert node["dateModified"][:10] >= stamp, slug
                    assert all(url in node.get("citation", []) for url, _label in row["sources"]), slug
                    found = True
        assert found, slug
        stripped = re.sub(r'<section\b[^>]*' + re.escape(marker) + r'[^>]*>.*?</section>', '', page, count=1, flags=re.S)
        rebuilt = apply_update(stripped, slug, row, stamp)
        assert rebuilt.count(marker) == 1, slug
    # Partial catalog rebuilds run before the guarded full site build.
    for slug, expected in (
        ("gemini-3-8-flash-tts", "Editorial source check: November 24, 2026."),
        ("gemini-3-8-flash-lite-tts", "Editorial pricing and lifecycle verification: November 24, 2026."),
    ):
        template = (ROOT / "data/model-page-content" / f"{slug}.html").read_text(encoding="utf-8")
        assert expected in template, slug
    pricing = json.loads((ROOT / "data/model-pricing.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "data/model-index.json").read_text(encoding="utf-8"))
    for data in (pricing, index):
        models = {m["model_id"]: m for m in data["models"]}
        for model_id in ("gemini-3.7-flash", "voxtral-mini-2602", "voxtral-mini-transcribe-realtime-2602", "mistral-large-2512", "mistral-medium-3-5"):
            assert models[model_id]["lifecycle"]["status"] == "deprecated", model_id
    by_id = {m["model_id"]: m for m in pricing["models"]}
    omni = by_id["gemini-omni-1.1-flash"]
    assert (omni["context_window"], omni["max_output"]) == (131072, 65536)
    for model_id in ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"):
        assert all("cached_input" not in rate for rate in by_id[model_id]["pricing"]["standard"]), model_id
    large = next(m for m in pricing["models"] if m["model_id"] == "mistral-large-4")
    assert large["lifecycle"]["status"] == "current"
    assert large["reasoning"]["levels"] == ["low", "medium", "high"]
    assert large["access"]["open_weight"] and large["access"]["self_hostable"]
    rate = large["pricing"]["standard"][-1]
    assert (rate["input"], rate["cached_input"], rate["output"]) == (0.7, 0.07, 2.1)
    print("PASS: all registered model update sections, official sources, dates, lifecycle and idempotent rendering")

if __name__ == "__main__":
    main()
