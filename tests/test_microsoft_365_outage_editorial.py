#!/usr/bin/env python3
"""Editorial safety checks for the Nov 2026 Microsoft 365 outage report."""
from __future__ import annotations
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "microsoft-365-outage-outlook-teams-copilot-2026"
CANONICAL = f"https://sxf.si/signals/{SLUG}/"
PAGE = ROOT / "signals" / SLUG / "index.html"
IMAGE = ROOT / "assets" / "signals" / "microsoft-365-outage-2026.svg"
html = PAGE.read_text(encoding="utf-8")
assert IMAGE.is_file() and IMAGE.read_text(encoding="utf-8").startswith("<svg ")
assert html.count("<h1>") == 1
assert f'<link rel="canonical" href="{CANONICAL}">' in html
assert 'content="index,follow,max-image-preview:large' in html
assert '<meta name="viewport" content="width=device-width,initial-scale=1">' in html
assert "@media(max-width:590px)" in html and "@media(max-width:930px)" in html
assert html.count("<main ") == 1 and html.count("</main>") == 1
assert html.endswith("</body></html>")
assert "74 countries" in html and "MO1550821" in html and "EX1550543" in html
visible_text = re.sub(r"<[^>]+>", "", html)
assert "09:57 UTC" in visible_text and "not a continuously updating live status" in visible_text
assert "no evidence of malicious activity" in html
assert "Reuters" in html and "Associated Press" in html
assert "/research/ai-coding-agent-architecture/" in html
assert "/guides/deploy-ai-agents-production/" in html

schema = json.loads(html.split('<script type="application/ld+json">', 1)[1].split('</script>', 1)[0])
graph = {entry["@type"]: entry for entry in schema["@graph"]}
assert {"WebPage", "NewsArticle", "ImageObject", "BreadcrumbList", "FAQPage"} <= graph.keys()
assert graph["NewsArticle"]["articleSection"] == "Tools"
assert graph["WebPage"]["url"] == CANONICAL
assert len(graph["FAQPage"]["mainEntity"]) == 6
assert graph["NewsArticle"]["datePublished"].startswith("2026-11-13")
assert graph["NewsArticle"]["image"]["@id"] == CANONICAL + "#primaryimage"
assert len(graph["NewsArticle"]["citation"]) >= 5

sitemap = ET.parse(ROOT / "sitemap.xml")
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
locs = [node.text for node in sitemap.findall(".//s:loc", ns)]
assert locs.count(CANONICAL) == 1

for p in ("signals/index.html", "tools/index.html",
          "signals/microsoft-idc-ai-roi-frontier-firms-2026/index.html"):
    assert f"/signals/{SLUG}/" in (ROOT / p).read_text(encoding="utf-8"), p

generator = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
assert 'outage_slug = "' + SLUG + '"' in generator
assert '| {"' + SLUG + '"}' in generator
assert SLUG in (ROOT / "scripts/sitemap_generation.py").read_text(encoding="utf-8")
print("PASS: Microsoft 365 outage content, SEO, links and regeneration safeguards")
