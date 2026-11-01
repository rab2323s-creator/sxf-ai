#!/usr/bin/env python3
"""Regression checks for source-backed GPT-6 Intelligent UI Signal."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news
import gpt6_intelligent_ui_signal_page as release
from signal_article_rendering import signal_page_html as render_article
from html.parser import HTMLParser

def main():
    archive = json.loads((ROOT / "data/archive.json").read_text(encoding="utf-8"))["items"]
    item = next(i for i in archive if i.get("signal_slug") == release.SLUG.split("/")[-2])
    html = update_news.signal_page_html(item, [item])
    destination = ROOT / "signals" / item["signal_slug"] / "index.html"
    saved = destination.read_text(encoding="utf-8")
    assert "data-sxf-bill-splitter" in saved and "gpt6-ui-availability" in saved, "Committed Signal missing the authored analysis"
    assert f'<link rel="canonical" href="{item["signal_url"]}"' in html
    assert '<meta name="robots" content="index,follow' in html
    assert "<title>" + release.TITLE.replace("&", "&amp;") + "</title>" in html
    assert "<h1>" + release.H1 + "</h1>" in html
    assert 'data-sxf-bill-splitter' in html
    assert 'aria-live="polite"' in html
    for anchor in ["gpt6-ui-examples", "gpt6-ui-architecture", "gpt6-ui-availability", "gpt6-ui-speed", "gpt6-ui-demo", "gpt6-ui-faq"]:
        assert f'id="{anchor}"' in html
    for url in ["/models/gpt-6/", "/models/gpt-6-sol/", "/models/gpt-6-luna/", "/models/gpt-6-astra/", "/guides/how-to-choose-ai-model/"]:
        assert 'href="' + url + '"' in html
        assert (ROOT / url.strip("/") / "index.html").is_file(), url
    raw = html.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
    graph = json.loads(raw)["@graph"]
    assert len(graph) == 4
    assert graph[1]["@type"] == ["Article", "TechArticle"]
    assert graph[1]["datePublished"] == "2026-10-07T00:00:00Z"
    assert graph[1]["citation"] == release.SOURCES
    assert graph[3]["@type"] == "FAQPage"
    assert len(graph[3]["mainEntity"]) == len(release.FAQ)
    assert "does not support Intelligent UI" in html
    assert 'GPT-6 Instant' in html
    print("PASS: Intelligent UI launch page, canonical, metadata, sources, demo, FAQ and cross-links")

if __name__ == "__main__":
    main()
