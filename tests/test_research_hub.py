"""Guard the Research hub's indexing, accessibility and generated feed contracts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "research" / "index.html"
CSS = ROOT / "section.css"
JS = ROOT / "section.js"

class ResearchParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.h1 = 0
        self.images = []
        self.headers = []
    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "a":
            self.links.append(attr.get("href", ""))
        if tag == "img":
            self.images.append(attr)
        if tag in ("h1", "h2", "h3"):
            self.headers.append(tag)


def main():
    source = HTML.read_text(encoding="utf-8")
    p = ResearchParser()
    p.feed(source)
    assert p.h1 == 1, "Research must have one clear H1"
    assert len(p.ids) == len(set(p.ids)), "Duplicate HTML id"
    assert source.count('<link rel="canonical" href="https://sxf.si/research/">') == 1
    assert '<meta name="robots" content="index,follow' in source
    assert 'id="research-main"' in source and 'href="#research-main"' in source
    assert source.count('<!-- SXF:SECTION_FEED_START -->') == 1
    assert source.count('<!-- SXF:SECTION_FEED_END -->') == 1
    assert source.count('<!-- SXF:SECTION_SCHEMA_START -->') == 1
    assert source.count('<!-- SXF:SECTION_SCHEMA_END -->') == 1
    assert re.search(r'<strong id="sectionCount">\d+</strong>', source)
    assert source.index('id="featured-research-title"') < source.index('id="signals"')
    assert source.index('id="benchmark-evidence"') < source.index('id="signals"')
    for required in (
        "/research/ai-agent-memory/",
        "/research/ai-agent-reliability/",
        "/research/ai-coding-agent-architecture/",
        "/evaluations/",
        "/evaluations/explorer/",
        "/guides/ai-agent-evaluation-checklist/",
        "/guides/ai-agent-security/",
        "/guides/ai-agent-authorization/",
        "/about/",
    ):
        assert required in p.links, f"Missing important research destination: {required}"
        if required.endswith("/") and required.startswith("/"):
            assert (ROOT / required.strip("/") / "index.html").exists(), f"Broken internal destination: {required}"
    for img in p.images:
        assert img.get("alt"), "Image alt text required"
        assert img.get("width") and img.get("height"), "Dimensions required to avoid layout shift"
        assert (ROOT / img["src"].lstrip("/")).exists(), "Research image missing: " + img["src"]
    scripts = re.findall(r'<script type="application/ld\+json"(?:[^>]*)>(.*?)</script>', source, re.S)
    assert len(scripts) == 2
    schemas = [json.loads(x) for x in scripts]
    collection = next(x for x in schemas[0]["@graph"] if x.get("@type") == "CollectionPage")
    assert collection["url"] == "https://sxf.si/research/"
    assert any(x.get("@id", "").endswith("#featured-research") for x in schemas[0]["@graph"])
    assert schemas[1]["@type"] == "ItemList"
    assert "section-signals-schema" in source
    assert ".mode-research .research-hero-grid" in CSS.read_text(encoding="utf-8")
    assert "@media(max-width:680px)" in CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "if(!feedReady)return;" in js, "Never erase server-rendered research links while loading"
    assert "x.setAttribute('aria-pressed'" in js
    print("PASS: research hub SEO, internal links, JSON-LD, image/accessibility and generator contracts")


if __name__ == "__main__":
    main()
