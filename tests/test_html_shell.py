#!/usr/bin/env python3
"""Regression contracts for shared HTML shell and SEO head extraction."""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from html_shell import page_header, page_footer, page_head
import update_news


def main():
    default_header = page_header()
    models_header = page_header("models")
    assert default_header.count('aria-current="page"') == 0
    assert models_header.count('aria-current="page"') == 1
    assert '<a href="/models/" aria-current="page">Models</a>' in models_header
    assert '<nav class="top-nav" aria-label="Primary navigation">' in models_header
    assert '<a class="brand" href="/" aria-label="SXF AI home">' in default_header
    assert update_news.page_header("models") == models_header

    footer = page_footer()
    year_script = '<script>document.getElementById("year").textContent=new Date().getFullYear();</script>'
    assert footer.count(year_script) == 1
    assert footer.count('mailto:info@sxf.si') == 2
    assert '<footer class="footer shell">' in footer
    assert update_news.page_footer() == footer

    canonical = "https://sxf.si/signals/test/?a=1&b=2"
    schema = {"@context": "https://schema.org", "@type": "Article", "name": "<New>", "headline": "Ö AI"}
    original_schema = dict(schema)
    title = '<New> & "Verified"'
    description = 'A & B "quoted"'
    article = page_head(title, description, canonical, schema, "article", "noindex,follow")
    assert '<title>&lt;New&gt; &amp; &quot;Verified&quot;</title>' in article
    assert '<meta name="description" content="A &amp; B &quot;quoted&quot;" />' in article
    escaped_url = 'https://sxf.si/signals/test/?a=1&amp;b=2'
    assert f'<link rel="canonical" href="{escaped_url}" />' in article
    assert f'<link rel="alternate" hreflang="en" href="{escaped_url}" />' in article
    assert f'<link rel="alternate" hreflang="x-default" href="{escaped_url}" />' in article
    assert '<meta name="robots" content="noindex,follow" />' in article
    assert '<meta name="googlebot" content="noindex,follow" />' in article
    assert '<meta property="og:type" content="article" />' in article
    assert '<meta name="twitter:card" content="summary" />' in article
    assert '<meta property="og:image" content=' not in article
    assert r'\u003cNew>' in article, "JSON-LD must escape literal < to avoid script injection"
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', article, re.S)
    assert match and json.loads(match.group(1)) == schema
    assert schema == original_schema
    assert update_news.page_head(title, description, canonical, schema, "article", "noindex,follow") == article

    site_schema = {"@type": "WebSite"}
    site = page_head("SXF", "A" * 200, "https://sxf.si/", site_schema)
    assert '<meta name="description" content="' + "A" * 180 + '" />' in site
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in site
    assert '<meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in site
    assert '<meta property="og:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />' in site
    assert '<meta name="twitter:card" content="summary_large_image" />' in site
    assert site.count('<link rel="canonical"') == 1
    assert site.count('<script type="application/ld+json">') == 1
    assert update_news.page_head("SXF", "A" * 200, "https://sxf.si/", site_schema) == site
    print("PASS: shared HTML shell, canonical/hreflang, robots, escaped JSON-LD and compatibility wrappers")


if __name__ == "__main__":
    main()
