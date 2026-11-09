#!/usr/bin/env python3
"""Protect original SXF Scribe v2 speech-to-text editorial research from regressions."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://sxf.si/models/scribe-v2/"
SOURCE = ROOT / "scripts" / "scribe_v2_dossier.html"
PAGE = ROOT / "models" / "scribe-v2" / "index.html"
CSS = ROOT / "assets" / "scribe-v2-dossier.css"
JS = ROOT / "assets" / "scribe-v2-economics.js"


def run() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert source == page, "The generated Scribe v2 route drifted from its authored source"
    assert len(source) > 30000
    assert source.count("<h1") == 1
    assert source.count('rel="canonical" href="' + URL + '"') == 1
    assert '<meta name="robots" content="index,follow' in source
    assert 'name="description"' in source
    assert "noindex" not in source.split("</head>", 1)[0]
    for anchor in (
        "sv2-overview", "sv2-verdict", "sv2-specs", "sv2-features",
        "sv2-calculator", "sv2-api", "sv2-evaluation", "sv2-comparison",
        "sv2-privacy", "sv2-faq", "sv2-sources",
    ):
        assert source.count(f'id="{anchor}"') == 1, anchor
    for text in (
        'data-sv2-lab', 'data-sv2-minutes', 'data-sv2-recordings',
        'data-sv2-channels', 'data-sv2-keyterms', 'data-sv2-editing',
        'data-model-history', 'data-what-changed', 'data-model-comparisons',
        "No post-baseline factual changes recorded",
        'href="/assets/scribe-v2-dossier.css"',
        'src="/assets/scribe-v2-economics.js"',
        'href="/models/scribe-v2-realtime/"',
        'href="/compare/deepgram-nova-3-vs-elevenlabs-scribe-v2/"',
    ):
        assert text in source, text
    m = re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>', source)
    assert m, "missing linked structured data"
    root = json.loads(m.group(1))
    graph = root["@graph"]
    article = next(x for x in graph if x["@type"] == "TechArticle")
    faq = next(x for x in graph if x["@type"] == "FAQPage")
    crumbs = next(x for x in graph if x["@type"] == "BreadcrumbList")
    assert article["mainEntityOfPage"]["@id"] == URL
    assert article["dateModified"] == "2026-11-09"
    assert len(article["citation"]) >= 5
    assert len(faq["mainEntity"]) == 10
    assert len(crumbs["itemListElement"]) == 3
    assert all(x["acceptedAnswer"]["text"] for x in faq["mainEntity"])
    assert CSS.exists() and "sv2-facts" in CSS.read_text()
    assert JS.exists()
    js = JS.read_text(encoding="utf-8")
    assert "base: 0.22, keyterms: 0.05, editing: 0.07" in js
    assert "editing.disabled = n>1" in js
    for relative in (
        "models/scribe-v2-realtime/index.html",
        "compare/deepgram-nova-3-vs-elevenlabs-scribe-v2/index.html"
    ):
        assert (ROOT / relative).exists(), relative
    generator = (ROOT / "scripts" / "update_news.py").read_text()
    assert 'if model_id == "scribe_v2":' in generator
    assert 'source = ROOT / "scripts" / "scribe_v2_dossier.html"' in generator
    assert 'raise RuntimeError("Scribe v2 editorial dossier invalid' in generator


if __name__ == "__main__":
    run()
    print("Scribe v2 dossier, structured data, audio-hour pricing and source ownership: PASS")
