#!/usr/bin/env python3
"""Guard homepage decision-first layout, accessibility, SEO and destination links."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ("/compare/", "/models/pricing/", "/evaluations/", "/research/")


class HomepageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.section_ids = []
        self.paths = []
        self.ctas = {}
        self.anchors = []
        self.section_stack = []
        self.current_section = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            self.section_ids.append((attrs.get("id") or attrs.get("class") or ""))
            self.section_stack.append(self.current_section)
            self.current_section = attrs.get("id") or attrs.get("class") or ""
        if tag == "h1":
            self.headings.append("h1")
        if tag == "a":
            href = attrs.get("href", "")
            cls = attrs.get("class", "")
            self.anchors.append(href)
            if "decision-pathway-card" in cls.split():
                assert self.current_section == "decision-pathways", "Cards outside decision section"
                self.paths.append(href)
            if "primary-cta" in cls.split() or "secondary-cta" in cls.split():
                self.ctas[cls] = href

    def handle_endtag(self, tag):
        if tag == "section" and self.section_stack:
            self.current_section = self.section_stack.pop()


def main():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    parser = HomepageParser()
    parser.feed(html)
    assert len(parser.headings) == 1, "Homepage needs exactly one H1"
    assert parser.ctas.get("primary-cta") == "/compare/", parser.ctas
    assert parser.ctas.get("secondary-cta") == "/models/pricing/", parser.ctas
    assert parser.paths == list(EXPECTED), parser.paths
    assert parser.section_ids.index("decision-pathways") < parser.section_ids.index("what-changed shell")
    assert parser.section_ids.index("decision-pathways") < parser.section_ids.index("latest")
    assert '#latest' in parser.anchors, "The radar must remain easy to reach"
    assert 'aria-labelledby="decision-pathways-title"' in html
    assert 'id="decision-pathways-title"' in html
    for path in EXPECTED:
        assert (ROOT / path.lstrip("/") / "index.html").is_file(), f"Missing pathway target: {path}"
    schema_start = '<script type="application/ld+json">'
    assert schema_start in html, "Homepage structured data missing"
    data = json.loads(html.split(schema_start, 1)[1].split("</script>", 1)[0])
    nodes = data["@graph"]
    page = next(node for node in nodes if node.get("@type") == "CollectionPage")
    item = next(node for node in nodes if node.get("@id") == "https://sxf.si/#decision-pathways")
    assert page["mainEntity"]["@id"] == item["@id"]
    assert [node["item"]["url"] for node in item["itemListElement"]] == ["https://sxf.si" + path for path in EXPECTED]
    assert len(item["itemListElement"]) == 4
    assert ".decision-pathways-grid" in css and "@media(max-width:530px)" in css
    assert ".decision-pathway-card:focus-visible" in css
    assert "@media(prefers-reduced-motion:reduce)" in css
    print("PASS: homepage decision pathways, links, schema and responsive styles")


if __name__ == "__main__":
    main()
