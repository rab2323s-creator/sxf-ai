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
    "Artificial Analysis Intelligence Index",
)


def assert_benchmark_hero(html: str) -> None:
    match = re.search(r'<header class="guide-article-hero shell">(.*?)</header>', html, re.S)
    assert match, "Missing AI benchmarks guide hero"
    hero = unescape(match.group(1))
    assert "<span>AI Model Benchmarks Explained</span></nav>" in hero, (
        "Breadcrumb must describe the AI benchmarks guide"
    )
    assert "AI Model Benchmarks Explained (2026)" in hero
    deck = re.search(r'<p class="guide-deck">(.*?)</p>', hero, re.S)
    assert deck, "Missing AI benchmarks guide introduction"
    assert all(term in deck.group(1) for term in BENCHMARK_TERMS), (
        "Hero introduction does not describe the benchmark methodologies"
    )
    for unrelated in ("RAG Embeddings", "Gemini Embedding 001", "Cohere Embed 5"):
        assert unrelated not in hero, f"Unrelated content leaked into hero: {unrelated}"


def main() -> None:
    # Check both the deployed HTML artifact and the source generator so a
    # future feed regeneration cannot silently bring back the copied hero.
    assert_benchmark_hero(PAGE.read_text(encoding="utf-8"))
    shell = {
        "page_head": lambda *args, **kwargs: "<head></head>",
        "page_header": lambda *args, **kwargs: "",
        "page_footer": lambda *args, **kwargs: "",
    }
    assert_benchmark_hero(guide_html(shell))
    print("PASS: AI benchmarks guide breadcrumb and introduction match subject")


if __name__ == "__main__":
    main()
