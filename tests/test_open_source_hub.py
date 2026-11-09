#!/usr/bin/env python3
"""Open Source builder hub — navigation, SEO, data integrity and fallback regression."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "open-source" / "index.html"


class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.ids = set()
        self.links = []
        self.bad_links = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in ("h1", "h2"):
            self.headings.append(tag)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a":
            href = attrs.get("href", "")
            self.links.append(href)
            if href.startswith("/") and not href.startswith("//"):
                path = ROOT / href.lstrip("/") / "index.html"
                if (href.endswith("/") and not path.is_file()) and not href.startswith("/assets/"):
                    self.bad_links.append(href)


def main():
    html = PAGE.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(html)
    assert parser.headings.count("h1") == 1
    assert len(set(parser.ids)) == len(parser.ids)
    assert all(key in parser.ids for key in (
        "main-content", "explore-stack", "models", "inference",
        "frameworks", "resources", "latest", "sectionFeed",
        "sectionCount", "sectionEmpty", "sectionSearch",
    ))
    assert not parser.bad_links, parser.bad_links
    assert '<link rel="canonical" href="https://sxf.si/open-source/"' in html
    assert '<meta name="robots" content="index,follow' in html
    assert 'open-source and open-weight AI releases' in html
    assert 'Open-source AI' in html and 'model inference' in html
    assert '<link rel="stylesheet" href="../assets/open-source-hub.css">' in html
    assert (ROOT / "assets" / "open-source-hub.css").is_file()
    assert '<script src="../section.js" defer></script>' in html
    for link in (
        "/guides/open-source-ai-models/", "/guides/run-ai-models-locally/",
        "/guides/ai-model-licensing/", "/guides/llm-quantization-explained/",
        "/tools/local-llm-vram-finder/", "/guides/llm-gateway/",
        "/topics/open-source-ai/",
    ):
        assert link in parser.links, link

    scripts = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
    assert len(scripts) == 2
    graph = json.loads(scripts[0])["@graph"]
    page, crumbs, resources = graph
    assert [x["@type"] for x in graph] == ["CollectionPage", "BreadcrumbList", "ItemList"]
    assert page["url"] == "https://sxf.si/open-source/"
    assert page["breadcrumb"]["@id"] == crumbs["@id"]
    assert page["mainEntity"]["@id"] == resources["@id"]
    assert resources["numberOfItems"] == len(resources["itemListElement"]) == 6
    assert [r["position"] for r in resources["itemListElement"]] == list(range(1, 7))
    signal_schema = json.loads(scripts[1])
    assert signal_schema["@type"] == "ItemList"
    feed = json.loads((ROOT / "data" / "open-source.json").read_text(encoding="utf-8"))
    count = len(feed["items"])
    assert f'<strong id="sectionCount">{count}</strong>' in html
    assert signal_schema["numberOfItems"] == min(10, count)
    inside = html.split("<!-- SXF:SECTION_FEED_START -->", 1)[1].split(
        "<!-- SXF:SECTION_FEED_END -->", 1
    )[0]
    assert inside.count('class="intel-card"') == count
    marker = re.search(r'<div id="sectionEmpty" class="open-hub-empty"( hidden)?>', html)
    assert marker, "SSR fallback missing"
    assert bool(marker.group(1)) == bool(count), "Empty state visibility diverges from feed"
    assert re.search(r'<link rel="stylesheet" href="../assets/open-source-hub.css">', html)
    js = (ROOT / "section.js").read_text(encoding="utf-8")
    assert "openSourceResultsStatus" in js and "aria-pressed" in js
    assert "const source=isOpenSource?'../data/open-source.json'" in js
    assert "replace_block(page, \"<!-- SXF:SECTION_FEED_START -->\"" in (
        ROOT / "scripts" / "update_news.py"
    ).read_text(encoding="utf-8")
    print(f"PASS: Open Source hub SEO, intent, semantic layout, {count} verified signals, schema and empty fallback")


if __name__ == "__main__":
    main()
