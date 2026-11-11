#!/usr/bin/env python3
"""Gemini Flash specialist comparison: SEO, facts, FAQ, internal links and owned generation."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gemini_flash_comparison import FAQ, TITLE, URL, DESCRIPTION

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.headings = set(), set(), []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            assert attrs["id"] not in self.ids, f"Duplicate id: {attrs['id']}"
            self.ids.add(attrs["id"])
        if attrs.get("href"):
            self.links.add(attrs["href"])
        if tag == "h1":
            self.headings.append("h1")

def check():
    path = ROOT / "compare/gemini-3-8-flash-vs-gemini-3-7-flash/index.html"
    html = path.read_text(encoding="utf-8")
    template = (ROOT / "data/comparison-page-content/gemini-38-vs-37.html").read_text(encoding="utf-8")
    generator = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert generator.count('if comparison["slug"] == "gemini-3-8-flash-vs-gemini-3-7-flash"') == 1
    assert 'render_gemini_flash_comparison(' in generator
    assert 'data-gemini-flash-upgrade="1"' in html
    assert "data-gemini-flash-upgrade" in template
    assert '<title>Gemini 3.8 Flash vs 3.7 Flash:' in html
    assert '<meta name="description" content="' in html and DESCRIPTION[:70] in html
    assert '<link rel="canonical" href="' + URL + '"' in html
    assert 'name="robots" content="index,follow' in html
    assert html.count("<h1>") == 1 and "Pricing, Benchmarks &amp; Which to Choose" in html
    assert html.count('type="application/ld+json"') == 1
    assert html.count('<main>') == html.count('</main>') == 1
    assert 'class="compare-v2-decisions shell>' not in html
    assert 'data-compare-contract' in html and 'data-model-ids="gemini-3.8-flash,gemini-3.7-flash"' in html
    assert "data-evaluation-comparability" in html
    assert "data-what-changed" in html
    assert "2027" in html and "2026" in html
    assert "data-gf-cost-lab" in html and "data-gf-total37" in html and "data-gf-total38" in html
    assert "/assets/gemini-flash-comparison.css" in html and "/assets/gemini-flash-comparison.js" in html
    assert "Gemini 3.8 Flash vs 3.7 Flash" in html
    assert html.count('id="gf-faq"') == 1
    assert "{{GF_FAQ}}" not in html and "SXF_GEMINI_FLASH_LIVE_FACTS" not in html
    assert "What is the main difference between Gemini 3.8 Flash and 3.7 Flash?" in html
    assert "The models have the" in html
    assert "/models/gemini/" in html
    graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))["@graph"]
    assert {"TechArticle", "WebPage", "BreadcrumbList", "FAQPage"} <= {row["@type"] for row in graph}
    faq = next(row for row in graph if row["@type"] == "FAQPage")["mainEntity"]
    assert len(faq) == len(FAQ) == 9
    for item in faq:
        assert item["name"] in html, f"Schema-only FAQ: {item['name']}"
    page = Page()
    page.feed(html)
    ids = {"gf-answer", "gf-differences", "gf-pricing", "gf-cost-lab", "gf-benchmarks",
           "gf-use-cases", "gf-migration", "gf-faq", "gf-sources"}
    assert ids <= page.ids, ids - page.ids
    for link in page.links:
        if link.startswith("#"):
            assert link[1:] in page.ids, f"Missing anchor {link}"
        if link.startswith("/") and not link.startswith("//"):
            dest = ROOT / link.split("#")[0].split("?")[0].lstrip("/")
            assert dest.is_file() or (dest / "index.html").is_file(), f"Missing local route {link}"
    for model in ("gemini-3-8-flash", "gemini-3-7-flash"):
        content = (ROOT / f"models/{model}/index.html").read_text(encoding="utf-8")
        assert '/compare/gemini-3-8-flash-vs-gemini-3-7-flash/' in content, model
    assert "data-gf-comparison-bridge" in (ROOT / "models/gemini-3-8-flash/index.html").read_text()
    css = (ROOT / "assets/gemini-flash-comparison.css").read_text()
    js = (ROOT / "assets/gemini-flash-comparison.js").read_text()
    assert "@media(max-width:760px)" in css
    assert "overflow:auto" in css and "gf-table-scroll" in css
    assert "addEventListener" in js and "fetch(" not in js and "XMLHttpRequest" not in js
    assert "2027" in js and "data-gf-total37" in js
    print("PASS: source-backed Gemini Flash comparison SEO, schema/FAQ parity, "
          "pricing, calculator, mobile CSS, internal links, source ownership and live evidence")

if __name__ == "__main__":
    check()
