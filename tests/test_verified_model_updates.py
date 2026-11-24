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
    assert len(register["updates"]) == 10
    for slug, row in register["updates"].items():
        path = ROOT / "models" / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        marker = f'data-verified-model-update="{slug}"'
        assert page.count(marker) == 1, slug
        assert stamp in page and row["title"] in page, slug
        assert all(url in page for url, _label in row["sources"]), slug
        for old, new in row.get("replacements", []):
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
    pricing = json.loads((ROOT / "data/model-pricing.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "data/model-index.json").read_text(encoding="utf-8"))
    for data in (pricing, index):
        models = {m["model_id"]: m for m in data["models"]}
        for model_id in ("gemini-3.7-flash", "voxtral-mini-2602", "voxtral-mini-transcribe-realtime-2602"):
            assert models[model_id]["lifecycle"]["status"] == "deprecated", model_id
    print("PASS: ten model update sections, official sources, dates, lifecycle and idempotent rendering")

if __name__ == "__main__":
    main()
