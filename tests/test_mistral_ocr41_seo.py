#!/usr/bin/env python3
"""Mistral OCR 4.1 SEO, source, math, original research and reciprocal links."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mistral_ocr41_model_page as editorial

URL = "https://sxf.si/models/mistral-ocr-4-1/"
PAGE = ROOT / "models/mistral-ocr-4-1/index.html"


def test_seo_and_schema() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert page.count('rel="canonical" href="' + URL + '"') == 1
    assert page.count("<h1>") == 1
    assert page.count("data-mocr41-guide") == 1
    assert "<title>Mistral OCR 4.1: API, Pricing, PDF &amp; Tables | SXF</title>" in page
    assert 'href="/assets/mistral-ocr41-guide.css"' in page
    assert 'src="/assets/mistral-ocr41-cost.js"' in page
    assert "mistral-ocr-4-1" in page
    assert "$0.004" in page and "$0.005" in page
    assert "include_blocks=True" in page
    assert "confidence_scores_granularity" in page
    assert 'data-mocr41-calculator' in page
    assert "SXF ORIGINAL REPRODUCIBLE RESEARCH DESIGN" in page
    assert "are not Mistral API outputs or independent performance measurements" in page
    assert len(re.findall(r"<h2\b", page)) >= 17

    for anchor in (
        "mocr41-overview", "mocr41-features", "mocr41-pricing",
        "mocr41-api", "mocr41-blocks", "mocr41-annotations",
        "mocr41-migration", "mocr41-rag", "mocr41-research",
        "mocr41-faq", "mocr41-sources",
    ):
        assert page.count('id="' + anchor + '"') == 1, anchor

    for route in (
        "/providers/mistral-ai/", "/models/pricing/",
        "/guides/vector-database-for-rag/",
        "/guides/rag-vs-fine-tuning-vs-long-context/",
        "/guides/ai-model-benchmarks-explained/",
        "/guides/ai-agent-cost/", "/guides/prompt-injection/",
        "/guides/ai-agent-security/", "/evaluations/",
    ):
        assert 'href="' + route + '"' in page, route
        assert (ROOT / route.lstrip("/") / "index.html").exists(), route

    schema_match = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', page, re.S,
    )
    assert schema_match, "missing TechArticle/FAQ schema"
    schema = json.loads(schema_match.group(1))
    assert schema["@context"] == "https://schema.org"
    article = next(x for x in schema["@graph"] if x["@type"] == "TechArticle")
    faq = next(x for x in schema["@graph"] if x["@type"] == "FAQPage")
    assert article["mainEntityOfPage"]["@id"] == URL
    assert article["dateModified"] == "2026-11-07"
    assert len(article["citation"]) >= 6
    assert len(faq["mainEntity"]) == 8

    # A content update must persist through scheduled regeneration.
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in page
    generator = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert "from mistral_ocr41_model_page import enrich_mistral_ocr_41_page" in generator
    assert 'if model_id == "mistral-ocr-4-1":' in generator
    assert "page = enrich_mistral_ocr_41_page(page)" in generator


def test_inbound_links() -> None:
    for route, marker in (
        ("guides/vector-database-for-rag/index.html", 'data-ocr41-inbound="vector-rag"'),
        ("guides/rag-vs-fine-tuning-vs-long-context/index.html", 'data-ocr41-inbound="rag-architecture"'),
    ):
        page = (ROOT / route).read_text(encoding="utf-8")
        assert marker in page
        assert 'href="/models/mistral-ocr-4-1/"' in page
        assert page.count("<h1>") == 1


def test_cost_and_research_fixtures() -> None:
    for pages, standard, annotated in (
        (25, 0.10, 0.125),
        (250, 1.0, 1.25),
        (1000, 4.0, 5.0),
        (10000, 40.0, 50.0),
        (100000, 400.0, 500.0),
    ):
        assert round(pages * 0.004, 5) == standard
        assert round(pages * 0.005, 5) == annotated

    # 1,000 pages, 5% reprocessing, 10% QA, 2 min/page, $30/hr.
    assert round(1000 * 1.05 * 0.004, 2) == 4.20
    assert round(1000 * 0.10 * 2 / 60 * 30, 2) == 100.0
    assert round(4.20 + 100.0, 2) == 104.20

    script = ROOT / "assets/mistral-ocr41-cost.js"
    source = script.read_text(encoding="utf-8")
    assert "count*(1+retry)*rate" in source
    assert "reviewedPages*minutes/60*reviewerRate" in source
    assert "fetch(" not in source and "localStorage" not in source

    base = ROOT / "models/mistral-ocr-4-1"
    scorer = base / "sxf-ocr-eval.py"
    fixture = base / "sxf-ocr-synthetic.jsonl"
    result = subprocess.run(
        [sys.executable, str(scorer), str(fixture)],
        capture_output=True, text=True, check=True, timeout=25,
    )
    report = json.loads(result.stdout)
    assert report["total"]["documents"] == 12
    assert set(report["by_group"]) == {
        "invoice", "research-table", "multilingual-form", "noisy-scan"
    }
    assert report["total"]["cer"] > 0
    assert report["total"]["critical_field_exact_match"] < 1.0
    assert "Synthetic" in report["disclosure"]
    assert "synthetic" in scorer.read_text(encoding="utf-8").lower()


if __name__ == "__main__":
    test_seo_and_schema()
    test_inbound_links()
    test_cost_and_research_fixtures()
    print("PASS: OCR 4.1 SEO, original research, pricing and inbound RAG links")
