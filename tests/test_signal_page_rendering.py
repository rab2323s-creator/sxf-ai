#!/usr/bin/env python3
"""Isolated HTML and SEO regression tests for the Signals index extraction."""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from html_shell import page_head, page_header, page_footer
from signal_page_rendering import SignalPageContext, signal_row, signals_index_html
import update_news


def sample(i, category="Models", *, eligible=True, title=None):
    slug = f"signal-{i}"
    return {
        "signal_slug": slug,
        "signal_url": f"https://sxf.si/signals/{slug}/",
        "url": f"https://primary.example/story/{i}?q=1&v=2",
        "title": title or f"Verified AI model release {i}",
        "source": "Primary & Source",
        "category": category,
        "summary": "Primary evidence",
        "published": f"2026-10-08T12:{i % 60:02d}:00Z",
        "modified_at": f"2026-10-09T10:{i % 60:02d}:00Z",
        "seo_eligible": eligible,
    }


def main():
    ctx = SignalPageContext(
        base_url="https://sxf.si",
        display_date=lambda value: "October 8, 2026",
        relative_time=lambda value: "2h ago",
        page_head=page_head,
        page_header=page_header,
        page_footer=page_footer,
    )
    row = sample(1, title='<New & "AI">')
    preserved_row = copy.deepcopy(row)
    expected = '''<a class="signal-row" href="/signals/signal-1/">
      <div class="signal-row-meta"><span>Primary &amp; Source</span><time datetime="2026-10-08T12:01:00Z">October 8, 2026</time></div>
      <h3>&lt;New &amp; &quot;AI&quot;&gt;</h3>
      <div class="signal-row-foot"><span>Models</span><b>Open signal ↗</b></div>
    </a>'''
    assert signal_row(row, ctx) == expected
    assert row == preserved_row

    rows = [sample(i, ["Models", "Tools", "Research", "Open Source"][i % 4]) for i in range(42)]
    rows[0] = sample(0, title='<New & "AI">')
    rows[40]["seo_eligible"] = False
    rows[41]["seo_eligible"] = True
    untouched = copy.deepcopy(rows)
    html = signals_index_html(rows, ctx)
    assert '<link rel="canonical" href="https://sxf.si/signals/" />' in html
    assert '<link rel="alternate" hreflang="en" href="https://sxf.si/signals/" />' in html
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
    assert '<meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
    assert html.count('class="signal-row"') == 40
    assert '<h3>&lt;New &amp; &quot;AI&quot;&gt;</h3>' in html
    assert '<strong id="signalsCount">42</strong>' in html
    assert 'href="https://sxf.si/signals/signal-41/"' in html
    assert 'href="https://sxf.si/signals/signal-40/"' not in html
    assert '1 indexed signals' in html
    assert 'Primary &amp; Source' in html
    assert '2h ago' in html
    assert '<script src="/signals.js" defer></script>' in html
    assert '<footer class="footer shell">' in html
    assert rows == untouched, "HTML rendering changed the snapshot input"
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert match, "Missing structured data"
    graph = json.loads(match.group(1))["@graph"]
    assert [entity["@type"] for entity in graph] == ["CollectionPage", "ItemList", "BreadcrumbList"]
    assert graph[0]["url"] == "https://sxf.si/signals/"
    assert graph[0]["dateModified"] == max(x["modified_at"] for x in rows)
    assert graph[1]["numberOfItems"] == 40
    assert len(graph[1]["itemListElement"]) == 40
    assert graph[1]["itemListElement"][0]["item"]["@id"] == rows[0]["signal_url"] + "#article"
    assert graph[2]["itemListElement"][1]["item"] == "https://sxf.si/signals/"

    empty = signals_index_html([], ctx)
    assert '<strong id="signalsCount">0</strong>' in empty
    empty_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', empty, re.S)
    assert empty_match
    empty_graph = json.loads(empty_match.group(1))["@graph"]
    assert "dateModified" not in empty_graph[0]
    assert empty_graph[1]["numberOfItems"] == 0
    assert 'class="signals-directory shell"' not in empty

    # Compatibility wrappers must continue to resolve the generator's live
    # dependencies rather than locking in a copy at module import time.
    original_display_date = update_news.display_date
    original_relative_time = update_news.relative_time
    try:
        update_news.display_date = ctx.display_date
        update_news.relative_time = ctx.relative_time
        assert update_news.signal_row(row) == expected
        assert update_news.signals_index_html(rows) == html
    finally:
        update_news.display_date = original_display_date
        update_news.relative_time = original_relative_time

    print("PASS: signal index canonical, JSON-LD, dateModified, 40-row limit, archive eligibility, escaping and wrappers")


if __name__ == "__main__":
    main()
