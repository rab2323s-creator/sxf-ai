#!/usr/bin/env python3
"""North Small Translate: verify source-backed published page and generator ownership."""
from __future__ import annotations
import ast
import json
from html.parser import HTMLParser
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
ROUTE = "models/north-small-translate-1-0/"
CANONICAL = "https://sxf.si/" + ROUTE
SOURCE = ROOT / ROUTE / "editorial.html"
INDEX = ROOT / ROUTE / "index.html"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.h1 = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "link":
            self.links.append(a)

def assert_page(page: str, *, published: bool):
    parsed = PageParser()
    parsed.feed(page)
    assert parsed.h1 == 1, "Exactly one H1 required"
    assert len(parsed.ids) == len(set(parsed.ids)), "Duplicate HTML ids"
    assert sum(x.get("rel") == "canonical" and x.get("href") == CANONICAL for x in parsed.links) == 1
    assert "<title>North Small Translate 1.0:" in page
    assert 'name="robots" content="index,follow' in page
    for anchor in ("north-overview", "north-specs", "north-languages",
                   "north-benchmarks", "north-api", "north-deployment",
                   "north-license", "north-lab", "north-faq", "north-sources"):
        assert anchor in parsed.ids, anchor
    for expected in ("north-small-translate-1.0", "218B", "25B", "16K",
                     "CC BY-NC 4.0", "WMT26", "83.60", "84.36",
                     "GPT-5.6-Sol", "Cohere Chat V2", "data-north-lab",
                     "data-north-guide", "data-north-copy"):
        assert expected in page, expected
    for asset in ("north-small-translate-guide.css", "north-small-translate-guide.js"):
        assert asset in page
        assert (ROOT / "assets" / asset).is_file(), asset
    schema_raw = re.search(r'<script type="application/ld\+json">([^<]+)</script>', page)
    assert schema_raw, "Missing JSON-LD"
    schema = json.loads(schema_raw.group(1))
    graph = schema["@graph"]
    types = {node["@type"] for node in graph}
    assert {"TechArticle", "FAQPage", "BreadcrumbList", "WebPage"} <= types
    faq = next(node for node in graph if node["@type"] == "FAQPage")
    assert len(faq["mainEntity"]) >= 8
    for q in faq["mainEntity"]:
        assert q["name"] in page and q["acceptedAnswer"]["text"] in page
    if published:
        assert "data-model-history" in page
        assert "data-what-changed" in page

def verify_generator_route():
    text = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    module = ast.parse(text)
    func = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                and n.name == "render_catalog_model_page")
    # Exercise the real generator's branch in isolation, without importing the
    # full news pipeline or reaching a live external endpoint.
    namespace = {
        "ROOT": ROOT,
        "model_change_watch_html": lambda ids, heading: '<section data-what-changed></section>',
        "model_history_html": lambda ids, heading: '<section data-model-history></section>',
        "model_comparison_links_html": lambda mid: "",
        "evaluation_model_block_html": lambda mid: "",
        "inject_before_main_end": lambda page, section: page.replace("</main>", section + "</main>", 1),
    }
    isolated = ast.Module(body=[func], type_ignores=[])
    exec(compile(ast.fix_missing_locations(isolated), "generator-branch", "exec"), namespace)
    page = namespace["render_catalog_model_page"]("north-small-translate-1-0", [])
    assert_page(page, published=True)
    assert page.count("data-what-changed") == 1
    assert page.count("data-model-history") == 1
    assert page.index('id="north-benchmarks"') < page.index("data-model-history")
    assert page.replace('<section data-what-changed></section>', '').replace(
        '<section data-model-history></section>', ''
    ).strip() == SOURCE.read_text(encoding="utf-8").strip()
    return page

def main():
    editorial = SOURCE.read_text(encoding="utf-8")
    published = INDEX.read_text(encoding="utf-8")
    assert_page(editorial, published=False)
    assert_page(published, published=True)
    assert 'data-north-guide' in verify_generator_route()
    # The generator must not change the authored source on disk.
    assert SOURCE.read_text(encoding="utf-8") == editorial
    print("PASS: North Small Translate canonical SEO, FAQs, assets and regeneration ownership")

if __name__ == "__main__":
    main()
