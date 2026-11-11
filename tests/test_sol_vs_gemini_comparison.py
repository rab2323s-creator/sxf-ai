#!/usr/bin/env python3
"""Regression contract for the SXF GPT-6 Sol vs Gemini 3.8 Flash guide."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sol_vs_gemini_comparison import enrich_sol_vs_gemini, TITLE, DESCRIPTION, URL

class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), set()
        self.h1 = 0
    def handle_starttag(self, name, attrs):
        attrs = dict(attrs)
        if name == "h1":
            self.h1 += 1
        if attrs.get("id"):
            assert attrs["id"] not in self.ids, "Duplicate id: " + attrs["id"]
            self.ids.add(attrs["id"])
        if attrs.get("href"):
            self.links.add(attrs["href"])

def check():
    path = ROOT / "compare/gpt-6-sol-vs-gemini-3-8-flash/index.html"
    page = path.read_text(encoding="utf-8")
    content = (ROOT / "data/comparison-page-content/gpt6-sol-vs-gemini-38.html").read_text(encoding="utf-8")
    assert page.count('data-sxf-sol-gemini-guide="1"') == 1
    assert content.count("<!-- SXF_SLOT_TOP -->") == 1
    assert "<title>GPT-6 Sol vs Gemini 3.8 Flash:" in page
    assert DESCRIPTION in page
    assert 'rel="canonical" href="' + URL + '"' in page
    assert 'name="robots" content="index,follow' in page
    assert "API Pricing, Coding &amp; Which to Choose" in page
    assert "data-compare-contract" in page
    assert 'data-model-ids="gpt-6-sol,gemini-3.8-flash"' in page
    assert "data-evaluation-comparability" in page and "data-what-changed" in page
    assert page.count('id="quick-answer"') == 1
    for item in ("sg-evidence", "sg-lab", "sg-method", "sg-sources", "specs"):
        assert 'id="' + item + '"' in page, item
    assert "42</strong>" in page and "41</strong>" in page
    assert "artificial-analysis-v4.3.2" in page
    assert "2026-10-04" in page
    assert "per-token price" in page
    assert "272,000" in page and "January 1, 2027" in page
    assert "Cost-per-Success Lab" in page
    assert 'data-sg-sol-total' in page and 'data-sg-gem-total' in page
    assert "gemini-3.8-flash" in page and "gpt-6-sol" in page
    assert "No synthetic winner score" in page
    assert "TechArticle" in page and "BreadcrumbList" in page and "FAQPage" in page
    schema = json.loads(re.search(
        r'<script type="application/ld\+json">(.*?)</script>', page, re.S
    ).group(1))
    graph = schema["@graph"]
    assert {"WebPage", "TechArticle", "BreadcrumbList", "FAQPage"} <= {
        item["@type"] for item in graph
    }
    assert next(x for x in graph if x["@type"] == "WebPage")["mainEntity"]["@id"] == URL + "#article"
    faq = next(x for x in graph if x["@type"] == "FAQPage")
    assert len(faq["mainEntity"]) == 9
    for item in faq["mainEntity"]:
        assert item["name"] in page
    parser = Scan()
    parser.feed(page)
    assert parser.h1 == 1
    for link in parser.links:
        if link.startswith("#"):
            assert link[1:] in parser.ids, "Missing page anchor: " + link
        elif link.startswith("/") and not link.startswith("//"):
            p = ROOT / link.split("?", 1)[0].split("#", 1)[0].lstrip("/")
            assert p.is_file() or (p / "index.html").is_file(), "Missing internal route: " + link
    assert enrich_sol_vs_gemini(page) == page, "Enrichment must be idempotent"
    css = (ROOT / "assets/sol-vs-gemini.css").read_text(encoding="utf-8")
    js = (ROOT / "assets/sol-vs-gemini.js").read_text(encoding="utf-8")
    assert "@media(max-width:680px)" in css and "overflow:auto" in css
    assert "272000" in js and "2027" in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    assert "data-sg-period" in content and "data-sg-sol-success" in content
    print("PASS: direct-intent SEO, owned regeneration, original calculator, provenance, "
          "canonical, JSON-LD FAQ, internal links and mobile contract")

if __name__ == "__main__":
    check()
