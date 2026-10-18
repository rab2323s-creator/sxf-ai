#!/usr/bin/env python3
"""Keep the AI benchmarks hero aligned with the guide's actual subject."""
from __future__ import annotations

import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ai_model_benchmarks_guide import guide_html  # noqa: E402

PAGE = ROOT / "guides/ai-model-benchmarks-explained/index.html"
BENCHMARK_TERMS = (
    "AA-Briefcase v1.1",
    "AA-LCR v1.1",
    "GDPval-AA v2.1",
    "Intelligence Index",
)


def assert_benchmark_hero(html: str) -> None:
    match = re.search(r'<header class="guide-article-hero shell">(.*?)</header>', html, re.S)
    assert match, "Missing AI benchmarks guide hero"
    hero = unescape(match.group(1))
    assert "<span>AI Model Benchmarks Explained</span></nav>" in hero, (
        "Breadcrumb must describe the AI benchmarks guide"
    )
    assert "<h1>Artificial Analysis (AA) Benchmarks:<br><span>AA-Briefcase, AA-LCR &amp; AI Index</span></h1>" in match.group(1), (
        "Hero H1 must match the approved AA Benchmarks SEO target"
    )
    deck = re.search(r'<p class="guide-deck">(.*?)</p>', hero, re.S)
    assert deck, "Missing AI benchmarks guide introduction"
    assert "Artificial Analysis (AA) benchmarks" in deck.group(1), "The hero must define AA"
    assert all(term in deck.group(1) for term in BENCHMARK_TERMS), (
        "Hero introduction does not describe the benchmark methodologies"
    )
    for unrelated in ("RAG Embeddings", "Gemini Embedding 001", "Cohere Embed 5"):
        assert unrelated not in hero, f"Unrelated content leaked into hero: {unrelated}"



def assert_benchmark_body(html: str) -> None:
    assert html.count('id="aa-benchmark-definition"') == 1, "AA definition section missing or duplicated"
    assert 'href="#aa-benchmark-definition"' in html, "Definition must appear in the table of contents"
    assert '<summary>What is an AA benchmark?</summary>' in html, "Matching on-page FAQ missing"
    assert '/guides/how-to-choose-ai-model/' in html, "Contextual selection link must survive regeneration"


def assert_benchmark_meta(html: str) -> None:
    import json
    title = re.search(r'<title>(.*?)</title>', html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]+)"', html)
    schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert title and unescape(title.group(1)) == "AA Benchmarks Explained: AA-Briefcase, AA-LCR & AI Index | SXF"
    assert desc and unescape(desc.group(1)) == "What are Artificial Analysis (AA) benchmarks? Compare AA-Briefcase v1.1, AA-LCR v1.1 and the Intelligence Index, including scoring methods and limitations."
    assert schema, "Missing JSON-LD"
    nodes = json.loads(schema.group(1))["@graph"]
    page = next(x for x in nodes if x["@type"] == "WebPage")
    article = next(x for x in nodes if x["@type"] == "TechArticle")
    faq = next(x for x in nodes if x["@type"] == "FAQPage")
    assert page["name"] == unescape(title.group(1))
    assert article["headline"] == "Artificial Analysis (AA) Benchmarks: AA-Briefcase, AA-LCR & AI Index"
    assert page["description"] == article["description"] == unescape(desc.group(1))
    assert any(q["name"] == "What is an AA benchmark?" for q in faq["mainEntity"]), "FAQ schema out of sync"
    assert article["datePublished"] == "2026-10-15" and article["dateModified"] == "2026-10-18"


def main() -> None:
    # Check both the deployed HTML artifact and the source generator so a
    # future feed regeneration cannot silently bring back the copied hero.
    published = PAGE.read_text(encoding="utf-8")
    assert_benchmark_hero(published)
    assert_benchmark_body(published)
    assert_benchmark_meta(published)
    shell = {
        "page_head": lambda *args, **kwargs: "<head></head>",
        "page_header": lambda *args, **kwargs: "",
        "page_footer": lambda *args, **kwargs: "",
    }
    regenerated = guide_html(shell)
    assert_benchmark_hero(regenerated)
    assert_benchmark_body(regenerated)
    print("PASS: AI benchmarks guide breadcrumb and introduction match subject")


if __name__ == "__main__":
    main()
