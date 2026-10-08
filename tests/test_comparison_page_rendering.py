#!/usr/bin/env python3
"""SEO and output contracts for the indexed comparison hub and generic matchups."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_news
from comparison_page_rendering import compare_index_html, generic_comparison_page_html


def graph(html):
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert match, "Missing JSON-LD"
    return json.loads(match.group(1))["@graph"]


def main():
    ctx = update_news.comparison_rendering_context()
    registry = update_news.comparison_registry_rows()
    assert registry and any(row.get("template") == "generic" for row in registry)
    index = compare_index_html([], ctx)
    assert update_news.compare_index_html([]) == index
    assert '<link rel="canonical" href="https://sxf.si/compare/" />' in index
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in index
    assert '<a href="/compare/" aria-current="page">Compare</a>' in index
    assert '<script src="/compare/compare.js" defer></script>' in index
    assert 'data-compare-builder' in index
    schema = graph(index)
    assert [row["@type"] for row in schema] == ["CollectionPage", "ItemList", "FAQPage"]
    assert schema[0]["url"] == "https://sxf.si/compare/"
    assert schema[1]["numberOfItems"] == len(registry)
    assert len(schema[1]["itemListElement"]) == len(registry)
    assert len(schema[2]["mainEntity"]) == 4
    assert index.count('class="compare-library-card"') == len(registry)
    assert index.count('class="compare-feature-card"') == min(3, len(registry))
    assert '<footer class="footer shell">' in index

    checked = 0
    for comparison in registry:
        if comparison.get("template") != "generic":
            continue
        html = generic_comparison_page_html(comparison, ctx)
        assert html == update_news.generic_comparison_page_html(comparison)
        canonical = "https://sxf.si/compare/" + comparison["slug"] + "/"
        assert f'<link rel="canonical" href="{canonical}" />' in html
        assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
        assert '<a href="/compare/" aria-current="page">Compare</a>' in html
        assert 'data-compare-contract' in html
        assert '<footer class="footer shell">' in html
        parts = graph(html)
        assert [x["@type"] for x in parts] == ["TechArticle", "BreadcrumbList", "FAQPage"]
        assert parts[0]["url"] == canonical
        assert parts[0]["headline"] == comparison["title"]
        assert parts[0]["dateModified"]
        assert parts[0]["citation"]
        assert len(parts[1]["itemListElement"]) == 3
        assert len(parts[2]["mainEntity"]) == 3
        checked += 1
    assert checked > 0

    invalid = dict(registry[0], model_ids=["one"])
    try:
        generic_comparison_page_html(invalid, ctx)
    except RuntimeError as exc:
        assert "exactly two models" in str(exc)
    else:
        raise AssertionError("Invalid comparison passed")

    print(f"PASS: comparison index SEO, JSON-LD, {checked} generic matchups and compatibility")


if __name__ == "__main__":
    main()
