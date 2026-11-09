#!/usr/bin/env python3
"""Regression checks for the source-owned SXF Mistral Medium 3.5 dossier."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "mistral-medium-3-5"
URL = "https://sxf.si/models/mistral-medium-3-5/"
SOURCE = ROOT / "scripts" / "mistral_medium35_dossier.html"
PAGE = ROOT / "models" / MODEL / "index.html"
STYLES = ROOT / "assets" / "mistral-medium35-guide.css"
CALC = ROOT / "assets" / "mistral-medium35-cost.js"
GENERATOR = ROOT / "scripts" / "update_news.py"


def test_dossier() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert source == page, "Published page drifted from durable editorial source."
    assert source.count("<h1") == 1
    assert source.count('rel="canonical" href="' + URL + '"') == 1
    assert "noindex" not in re.search(r"<head>.*?</head>", source, re.S).group()
    assert len(source) > 30000
    for anchor in (
        "mm35-overview", "mm35-verdict", "mm35-specifications",
        "mm35-features", "mm35-pricing", "mm35-benchmarks",
        "mm35-migration", "mm35-integration", "mm35-faq", "mm35-sources"
    ):
        assert source.count(f'id="{anchor}"') == 1, anchor
    for required in (
        'data-mm35-calculator', 'data-model-evaluations',
        'data-model-history', 'data-what-changed',
        '/assets/mistral-medium35-guide.css',
        '/assets/mistral-medium35-cost.js',
        "31 October 2026", "Mistral Large 4", "Modified MIT"
    ):
        assert required in source, required

    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)
    assert match
    obj = json.loads(match.group(1))
    graph = obj["@graph"]
    article = next(node for node in graph if node["@type"] == "TechArticle")
    faq = next(node for node in graph if node["@type"] == "FAQPage")
    assert article["mainEntityOfPage"]["@id"] == URL
    assert article["dateModified"] == "2026-11-09"
    assert len(article["citation"]) >= 6
    assert len(faq["mainEntity"]) == 8
    assert all(item["acceptedAnswer"]["text"] for item in faq["mainEntity"])
    assert source.count('data-mm35-input') >= 1
    assert source.count('data-mm35-cached') >= 1
    assert source.count('data-mm35-output') >= 1
    assert source.count('data-mm35-requests') >= 1
    assert "PRICE = Object.freeze({ input: 1.5, cached: 0.15, output: 7.5 })" in CALC.read_text()
    assert "mm35-snapshot" in STYLES.read_text()
    for path in (
        "models/mistral-large-4/index.html",
        "models/mistral-small-4/index.html",
        "evaluations/explorer/index.html",
        "guides/ai-model-benchmarks-explained/index.html",
    ):
        assert (ROOT / path).exists(), path
    generator = GENERATOR.read_text(encoding="utf-8")
    assert 'if model_id == "mistral-medium-3-5":' in generator
    assert 'source = ROOT / "scripts" / "mistral_medium35_dossier.html"' in generator


if __name__ == "__main__":
    test_dossier()
    print("Mistral Medium 3.5 authored dossier, schema, links and calculator: PASS")
