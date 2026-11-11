#!/usr/bin/env python3
"""Gemini family source, SEO, responsive behavior, schema and regeneration contract."""
from __future__ import annotations

from html.parser import HTMLParser
from html import escape
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gemini_family_page import enrich_gemini_family_page, add_gemini_discovery_links, FAQ, TITLE

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = set()
        self.ids = set()
        self.h1 = 0
    def handle_starttag(self, name, attrs):
        attr = dict(attrs)
        if attr.get("href"):
            self.hrefs.add(attr["href"])
        if attr.get("id"):
            self.ids.add(attr["id"])
        if name == "h1":
            self.h1 += 1

def check():
    path = ROOT / "models/gemini/index.html"
    page = path.read_text(encoding="utf-8")
    assert 'data-sxf-gemini-guide' in page, "Gemini authored content missing from built output"
    assert '<title>' + escape(TITLE) + '</title>' in page
    assert 'name="robots" content="index,follow' in page
    assert '<link rel="canonical" href="https://sxf.si/models/gemini/"' in page
    assert 'href="/assets/gemini-family.css"' in page
    assert 'src="/assets/gemini-family.js"' in page
    assert 'class="signal-list"' in page, "Existing Gemini release signals removed"
    assert "data-what-changed" in page, "Model history guard missing"
    assert "id=\"gemini-search-answers\"" in page
    assert "id=\"gemini-checklist\"" in page
    assert "Gemini 3.8 Flash vs 3.7 Flash: what changed?" in page
    assert "Gemini Embedding 001 vs Embedding 2" in page
    assert "Gemini 3.8 Flash TTS API" in page
    assert "Google Gemini Models<br><span>Versions, Pricing, Features &amp; API</span>" in page
    assert "compared for 2026." not in page
    assert "data-gemini-cost-lab" in page
    assert "Gemini 4 Carbon" in page and "Gemini 3.8 Flash" in page
    assert "November 11, 2026" in page
    assert "2027" in page
    assert page.count("<h1>") == 1
    assert page.count("<title>") == 1
    assert "{{GEMINI_FAQ}}" not in page

    marker = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert marker, "JSON-LD missing"
    schema = json.loads(marker.group(1))
    graph = schema["@graph"]
    assert {"CollectionPage", "BreadcrumbList", "ItemList", "FAQPage"} <= {node["@type"] for node in graph}
    faq = next(node for node in graph if node["@type"] == "FAQPage")
    assert len(faq["mainEntity"]) == len(FAQ)
    for row in faq["mainEntity"]:
        assert row["name"] in page, f"FAQ schema text has no visible question: {row['name']}"

    links = Links()
    links.feed(page)
    needed_ids = {"gemini-search-answers", "gemini-checklist", "gemini-models", "gemini-comparison", "gemini-pricing", "gemini-cost-lab",
                  "gemini-api", "gemini-capabilities", "gemini-compare-links",
                  "gemini-faq", "gemini-sources", "gemini-news"}
    assert needed_ids <= links.ids, sorted(needed_ids - links.ids)
    for href in links.hrefs:
        if href.startswith("#"):
            assert href[1:] in links.ids, "Broken in-page anchor: " + href
        elif href.startswith("/") and not href.startswith("//"):
            local = ROOT / href.split("#", 1)[0].split("?", 1)[0].lstrip("/")
            assert local.is_file() or (local / "index.html").is_file(), "Broken local link: " + href

    for file in ("assets/gemini-family.css", "assets/gemini-family.js"):
        assert (ROOT / file).is_file()
    css = (ROOT / "assets/gemini-family.css").read_text()
    js = (ROOT / "assets/gemini-family.js").read_text()
    assert "@media(max-width:720px)" in css
    assert "overflow:auto" in css or "overflow-x:auto" in css
    assert 'addEventListener("input", refresh)' in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js

    # Generator idempotence: adding a second copy is prohibited.
    assert enrich_gemini_family_page(page) == page
    for rel in ("models/index.html", "providers/google/index.html",
                "models/gemini-3-8-flash/index.html", "models/gemini-4/index.html",
                "models/gemini-embedding-001/index.html",
                "models/gemini-3-8-flash-tts/index.html"):
        body = (ROOT / rel).read_text(encoding="utf-8")
        assert body.count('data-gemini-hub-link') == 1, "Missing or duplicated Gemini hub link: " + rel
        assert 'href="/models/gemini/"' in body

    print("PASS: Gemini hub SEO, source content, schema, pricing tool, responsive CSS, "
          "local links, reciprocal discovery and rerun idempotence")

if __name__ == "__main__":
    check()
