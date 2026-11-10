#!/usr/bin/env python3
"""Source-owned Claude Haiku 5.5 / Sonnet 5.5 SEO and price integrity checks."""
from __future__ import annotations
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "claude-haiku-5-5-vs-claude-sonnet-5-5"
PAGE = ROOT / "compare" / SLUG / "index.html"
SOURCE = ROOT / "compare" / SLUG / "editorial.html"
CANONICAL = "https://sxf.si/compare/" + SLUG + "/"

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.ids = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.headings.append(a)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])

def main():
    source = SOURCE.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert source == page, "Generated comparison drifted from its specialist editorial source"
    assert "class=\"compare-v2-decisions shell>" not in page, "Malformed HTML from generic comparison"
    assert "What matters for visual creation" not in page
    assert page.count('rel="canonical" href="' + CANONICAL + '"') == 1
    assert '<meta name="robots" content="index,follow' in page
    parser = Reader()
    parser.feed(page)
    assert len(parser.headings) == 1
    assert len(parser.ids) == len(set(parser.ids)), "Duplicate element IDs"
    for anchor in ("main-content","hs-title","decision","specs","pricing","cost-lab","benchmarks","methodology","faq","sources","hs-requests","hs-input","hs-output","hs-cost-form","hs-haiku-total","hs-sonnet-total"):
        assert anchor in parser.ids, anchor
    for route in (
        "/models/claude-haiku-5-5/", "/models/claude-sonnet-5-5/",
        "/guides/anthropic-api-pricing/", "/compare/",
    ):
        assert route in parser.links, route
        assert (ROOT / route.lstrip("/") / "index.html").is_file(), route
    for asset in ("claude-haiku-sonnet-cost.js", "claude-haiku-sonnet-comparison.css"):
        assert (ROOT / "assets" / asset).is_file(), asset
        assert "/assets/" + asset in page, asset
    scripts = re.findall(r'<script type="application/ld\+json">([^<]+)</script>', page, re.S)
    assert len(scripts) == 1
    graph = json.loads(scripts[0])["@graph"]
    assert [x["@type"] for x in graph] == ["WebPage", "TechArticle", "BreadcrumbList"]
    web_page, article, crumbs = graph
    assert web_page["url"] == CANONICAL
    assert web_page["mainEntity"]["@id"] == article["@id"]
    assert web_page["breadcrumb"]["@id"] == crumbs["@id"]
    assert article["dateModified"] == "2026-11-10"
    assert len(article["citation"]) >= 4
    assert not any(x["@type"] == "FAQPage" for x in graph)
    assert page.count("39.2%") >= 1 and page.count("70.6%") >= 1
    assert "TERMINAL-BENCH 4.0" in page and "OSWORLD 2.1" in page
    assert "INDEPENDENT EVALUATIONS" in page
    assert "RELATED MATCHUPS" in page and "DECISION FACTORS" in page
    assert 'data-compare-contract' in page and 'data-what-changed' in page
    pricing = json.loads((ROOT/"data/model-pricing.json").read_text())
    records = {m["model_id"]:m for m in pricing["models"]}
    sonnet = records["claude-sonnet-5-5"]
    haiku = records["claude-haiku-5-5"]
    assert haiku["pricing"]["tiered"]["scopes"][0]["tiers"][0]["input"] == 0.1
    assert haiku["pricing"]["tiered"]["scopes"][0]["tiers"][1]["output"] == 2.5
    assert sonnet["pricing"]["standard"][-1]["cached_input"] == 0.1
    assert sonnet["pricing"]["standard"][-1]["start"] == "2026-10-07"
    provider = json.loads((ROOT / "data/model-catalog/providers/anthropic.json").read_text())
    anth = next(x for x in provider["models"] if x["model_id"] == "claude-sonnet-5-5")
    assert anth["pricing"] == sonnet["pricing"]
    assert '<th scope="col">Haiku &gt;100K prompt</th>' in page
    print("PASS: Claude Haiku 5.5 vs Sonnet 5.5 source-owned SEO, sources, canonical, published price tiers, schema, mobile CSS and visible evidence")

if __name__ == "__main__":
    main()
