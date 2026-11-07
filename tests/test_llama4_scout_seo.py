#!/usr/bin/env python3
"""Llama 4 Scout: SEO, original evidence, memory math and reciprocal link integrity."""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import llama4_scout_model_page as editorial

URL = "https://sxf.si/models/llama-4-scout/"
PAGE = ROOT / "models/llama-4-scout/index.html"


def test_scout() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert page.count('rel="canonical" href="' + URL + '"') == 1
    assert page.count("<h1>") == 1
    assert page.count("data-sxf-scout-guide") == 1
    assert "<title>Llama 4 Scout: 10M Context, 109B Specs &amp; GPU VRAM | SXF</title>" in page
    assert 'src="/assets/llama4-scout-memory.js"' in page
    assert 'href="/assets/llama4-scout-guide.css"' in page
    assert "17 billion active parameters" in page
    assert "109 billion total parameters" in page
    assert "10-million-token maximum context window" in page
    assert "512 GPUs" in page
    assert "Llama 4 Community License" in page
    assert "EU-headquartered" in page
    assert "SXF ORIGINAL ENGINEERING MATH" in page
    assert "SXF ORIGINAL EVALUATION DESIGN" in page
    assert "not actual Llama 4 Scout outputs" in page
    assert "no universal direct Meta Standard token price" in page
    assert "id=\"scout-faq\"" in page
    assert len(re.findall(r"<h2\b", page)) >= 20
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in page
    for name in (
        "scout-overview", "scout-specs", "scout-vram", "scout-context",
        "scout-install", "scout-license", "scout-pricing", "scout-comparison",
        "scout-evaluation", "scout-faq", "scout-sources",
    ):
        assert page.count('id="' + name + '"') == 1, name
    for path in (
        "/models/llama-4-maverick/",
        "/compare/llama-4-scout-vs-llama-4-maverick/",
        "/compare/llama-4-maverick-vs-gemini-3-8-flash/",
        "/providers/meta/",
        "/models/pricing/",
        "/tools/local-llm-vram-finder/",
        "/guides/llm-quantization-explained/",
        "/guides/ai-agent-security/",
        "/evaluations/",
    ):
        assert 'href="' + path + '"' in page, path
        assert (ROOT / path.strip("/") / "index.html").exists(), path
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert m
    schema = json.loads(m.group(1))
    assert schema["@context"] == "https://schema.org"
    article = next(x for x in schema["@graph"] if x["@type"] == "TechArticle")
    faq = next(x for x in schema["@graph"] if x["@type"] == "FAQPage")
    assert article["mainEntityOfPage"]["@id"] == URL
    assert article["dateModified"] == "2026-11-07"
    assert len(article["citation"]) == 8
    assert len(faq["mainEntity"]) == 8


def test_generator_and_reciprocal() -> None:
    generator = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert "from llama4_scout_model_page import enrich_llama_4_scout_page" in generator
    assert 'if model_id == "llama-4-scout":' in generator
    assert "page = enrich_llama_4_scout_page(page)" in generator
    assert 'if model_id == "llama-4-maverick":' in generator
    assert "data-scout-reciprocal-link" in generator
    assert 'comparison["slug"] == "llama-4-scout-vs-llama-4-maverick"' in generator
    assert "data-scout-comparison-guide" in generator
    for route, marker in (
        ("models/llama-4-maverick/index.html", "data-scout-reciprocal-link"),
        ("compare/llama-4-scout-vs-llama-4-maverick/index.html", "data-scout-comparison-guide"),
    ):
        page = (ROOT / route).read_text(encoding="utf-8")
        assert marker in page
        assert page.count('href="/models/llama-4-scout/"') >= 1
        assert page.count("<h1>") == 1


def test_research_and_memory_math() -> None:
    # Theoretical weight-only payload, not physical VRAM measurement.
    assert 109_000_000_000 * 4 / 8 / 1e9 == 54.5
    assert 109_000_000_000 * 8 / 8 / 1e9 == 109
    assert 109_000_000_000 * 16 / 8 / 1e9 == 218
    assert round(109_000_000_000 * 4 / 8 / (1024 ** 3), 2) == 50.76
    assert round(10_000_000 * 32 * 1024 / 1e9, 2) == 327.68
    assert round(54.5 * 1.2 + 8192 * 32 * 1024 / 1e9, 2) == 65.67
    js = (ROOT / "assets/llama4-scout-memory.js").read_text(encoding="utf-8")
    assert "109000000000*bits/8/1000000000" in js
    assert "tokens*cacheKiB*1024/1000000000" in js
    assert "fetch(" not in js and "localStorage" not in js

    scorer = ROOT / "models/llama-4-scout/sxf-scout-eval.py"
    samples = ROOT / "models/llama-4-scout/sxf-scout-fixtures.jsonl"
    report = json.loads(subprocess.run(
        [sys.executable, str(scorer), str(samples)], check=True,
        capture_output=True, text=True, timeout=20,
    ).stdout)
    assert report["examples"] == 12
    assert report["correct"] == 11
    assert set(report["by_band_and_placement"]) == {
        band + "/" + location
        for band in ("8k","32k","128k","1m")
        for location in ("start","middle","end")
    }
    assert "synthetic" in report["disclaimer"].lower()
    assert "synthetic" in scorer.read_text(encoding="utf-8").lower()


if __name__ == "__main__":
    test_scout()
    test_generator_and_reciprocal()
    test_research_and_memory_math()
    print("PASS: Scout SEO, first-party facts, hardware assumptions, reciprocal links and research fixtures")
