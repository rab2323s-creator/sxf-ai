#!/usr/bin/env python3
"""Gemini 3.8 Live SEO regression: generated page, source, costs and schema."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gemini_38_live_model_page as editorial

URL = "https://sxf.si/models/gemini-3-8-live/"
PAGE = ROOT / "models/gemini-3-8-live/index.html"


def test_page() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert page.count('rel="canonical" href="' + URL + '"') == 1
    assert page.count('<h1>') == 1
    assert page.count('data-g38-live-guide') == 1
    assert '<title>Gemini 3.8 Live API: Voice Agents, Pricing &amp; Python | SXF</title>' in page
    assert "131,072" in page and "65,536" in page
    assert "gemini-3.8-live" in page
    assert 'data-g38-calculator' in page
    assert 'href="/assets/gemini-38-live-guide.css"' in page
    assert 'src="/assets/gemini-38-live-calculator.js"' in page
    assert "SXF ORIGINAL TEST DESIGN" in page
    assert "not a claim that SXF has executed measured voice calls" in page
    assert "thinking_level" in page
    assert "Non-blocking by default" in page
    assert "id=\"g38-live-faq\"" in page
    for path in (
        "/models/gemini-3-8-live-extended-thinking/",
        "/compare/gemini-3-8-live-extended-thinking-vs-gemini-3-8-live/",
        "/models/gemini-3-8-flash-tts/",
        "/guides/ai-agent-security/",
        "/guides/ai-agent-observability/",
        "/guides/ai-receptionist/",
    ):
        assert f'href="{path}"' in page
        assert (ROOT / path.lstrip("/") / "index.html").exists(), path

    for anchor in (
        "g38-live-overview", "g38-live-features", "g38-live-pricing",
        "g38-live-api", "g38-live-migration", "g38-live-comparison",
        "g38-live-lab", "g38-live-faq", "g38-live-sources",
    ):
        assert page.count(f'id="{anchor}"') == 1

    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert schema_match
    doc = json.loads(schema_match.group(1))
    article = next(n for n in doc["@graph"] if n["@type"] == "TechArticle")
    faq = next(n for n in doc["@graph"] if n["@type"] == "FAQPage")
    assert article["dateModified"] == "2026-11-07"
    assert article["mainEntityOfPage"]["@id"] == URL
    assert len(article["citation"]) >= 5
    assert len(faq["mainEntity"]) == 6

    # The source HTML is preserved by the generator on rebuild, not manually pasted once.
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in page
    generator = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert "from gemini_38_live_model_page import enrich_gemini_38_live_page" in generator
    assert 'if model_id == "gemini-3.8-live":' in generator
    assert "page = enrich_gemini_38_live_page(page)" in generator

    # Google approximates voice-minute charges. Text/modality metering is separate.
    assert round(5 * 0.005 + 3 * 0.018, 4) == 0.079
    js = (ROOT / "assets/gemini-38-live-calculator.js").read_text(encoding="utf-8")
    assert "input * 0.005 + output * 0.018 + video * 0.002" in js
    assert "fetch(" not in js and "localStorage" not in js
    assert (ROOT / "assets/gemini-38-live-guide.css").exists()


if __name__ == "__main__":
    test_page()
    print("PASS: Gemini 3.8 Live SEO, calculator, links and regeneration safety")
