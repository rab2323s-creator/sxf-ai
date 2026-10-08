#!/usr/bin/env python3
"""Unit and SEO regression contracts for the extracted model provider directory."""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from html_shell import page_head, page_header, page_footer
from model_provider_index_rendering import ProviderIndexContext, provider_index_html
import update_news


def make_model(provider, model_id, date):
    return {
        "provider": provider,
        "model_id": model_id,
        "provenance": {"verified_at": date},
    }


def main():
    catalog = {
        "source_verified": "2026-10-08",
        "models": [
            make_model('Zeta "Labs"', "zeta-1", "2026-10-01"),
            make_model("A & Co", "a-1", "2026-10-06"),
            make_model("A & Co", "a-2", "2026-10-07"),
        ],
    }
    unchanged = copy.deepcopy(catalog)
    calls = []
    def paid(model):
        calls.append(model["model_id"])
        return model["model_id"] == "a-1"

    ctx = ProviderIndexContext(
        base_url="https://sxf.si",
        model_pricing_catalog=catalog,
        model_has_official_paid_pricing=paid,
        provider_slug=lambda provider: "a-and-co" if provider == "A & Co" else "zeta-labs",
        page_head=page_head,
        page_header=page_header,
        page_footer=page_footer,
    )

    html = provider_index_html([], ctx)
    assert html.startswith("<!doctype html><html lang=\"en\"><head>")
    assert '<link rel="canonical" href="https://sxf.si/providers/" />' in html
    assert '<link rel="alternate" hreflang="en" href="https://sxf.si/providers/" />' in html
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
    assert '<meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
    assert '<nav class="top-nav" aria-label="Primary navigation">' in html
    assert '<a href="/models/" aria-current="page">Models</a>' in html
    assert '<footer class="footer shell">' in html
    assert html.count('class="tracked-model"') == 2
    assert html.index('href="/providers/a-and-co/"') < html.index('href="/providers/zeta-labs/"')
    assert '<strong>A &amp; Co</strong>' in html
    assert '<strong>Zeta &quot;Labs&quot;</strong>' in html
    assert '2 tracked models · 1 calculator-priced · verified 2026-10-07' in html
    assert '1 tracked model · 0 calculator-priced · verified 2026-10-01' in html
    assert '<strong>3</strong><span>tracked models</span>' in html
    assert '<strong>2026-10-08</strong><span>catalog verified</span>' in html
    assert calls == ["a-1", "a-2", "zeta-1"], "Paid pricing callback order changed"
    assert catalog == unchanged, "Directory generation mutated catalog"

    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert schema_match, "Missing JSON-LD"
    graph = json.loads(schema_match.group(1))["@graph"]
    assert len(graph) == 2
    assert graph[0]["@type"] == "CollectionPage"
    assert graph[0]["url"] == "https://sxf.si/providers/"
    assert graph[1]["@type"] == "ItemList"
    assert graph[1]["numberOfItems"] == 2
    assert [row["name"] for row in graph[1]["itemListElement"]] == ["A & Co", 'Zeta "Labs"']
    assert [row["url"] for row in graph[1]["itemListElement"]] == [
        "https://sxf.si/providers/a-and-co/",
        "https://sxf.si/providers/zeta-labs/",
    ]

    # Keep the original call-site contract and verify identical HTML against
    # the new renderer with the real current catalogue dependencies.
    snapshot = copy.deepcopy(update_news.MODEL_PRICING_CATALOG)
    assert update_news.provider_index_html([]) == provider_index_html([], update_news.provider_index_context())
    assert update_news.MODEL_PRICING_CATALOG == snapshot

    print("PASS: provider directory HTML, canonical, robots, JSON-LD, sorting, catalog purity and legacy wrapper")


if __name__ == "__main__":
    main()
