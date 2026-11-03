#!/usr/bin/env python3
"""SXF five owner-approved, source-verified November editorial launches.

Run before and after ingestion. Prevent SEO regressions, loss of approvals,
missing source evidence, broken internal routes and removal from the sitemap.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news
from editorial_approval import read_decisions, publication_decision
from signal_editorial_reviews import REVIEWS
from news_relevance import NewsDecision

SOURCES = {
    "https://openai.com/index/lifeval": "lifeval-ed4b582",
    "https://openai.com/index/grid-protectors-program": "introducing-the-grid-protectors-program-19244c7",
    "https://www.anthropic.com/news/ai-for-science-expands-foundations-research-institutions": "ai-for-science-expands-to-foundations-and-research-institutions-ad10900",
    "https://openai.com/index/scaling-git-at-openai": "scaling-git-at-openai-de4cf53",
    "https://huggingface.co/blog/transformers-mic": "transformers-model-integration-contracts-fec0e46",
}

def main():
    post = "--post-build" in sys.argv
    decisions = read_decisions(ROOT / "data" / "editorial-decisions.json")
    inbox = json.loads((ROOT / "data" / "editorial-inbox.json").read_text(encoding="utf-8"))["items"]
    archive = json.loads((ROOT / "data" / "archive.json").read_text(encoding="utf-8"))["items"]
    published = {r["url"]: r for r in archive}
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")

    for url, slug in SOURCES.items():
        record = decisions[url]
        assert record["decision"] == "approved", url
        source_row = next((r for r in inbox if r["url"] == url), None)
        if post:
            assert source_row is None, "Published item still in approval inbox: " + url
            assert url in published, "Published item missing from archive: " + url
            source_row = published[url]
        else:
            source_row = source_row or published.get(url)
        assert source_row, "Approved source not found: " + url
        assert (record["url"], record["title"], record["source"]) == (
            source_row["url"], source_row["title"], source_row["source"])

        review = REVIEWS[slug]
        assert review["primary_source"] == url
        assert len(review["evidence"]) >= 5
        assert len(review["analysis"]) >= 3
        assert len(review["internal_links"]) >= 3
        assert len(review["reader_checklist"]) >= 3
        assert 105 <= len(review["meta_description"]) <= 160
        assert 30 <= len(review["seo_title"]) <= 60
        assert review["schema_type"] == "NewsArticle"
        assert all(e["source"] in review["sources"] for e in review["evidence"])
        assert all(a["source"] in review["sources"] for a in review["analysis"])
        assert all(a["url"].startswith("/") and not a["url"].startswith("//")
                   and (ROOT / a["url"].lstrip("/") / "index.html").is_file()
                   for a in review["internal_links"])

        row = update_news.prepare_items([source_row])[0]
        assert row["signal_slug"] == slug
        assert row["seo_eligible"], "Reviewed article must pass SEO gate: " + url
        assert row["summary"] == review["summary"]
        assert publication_decision(
            row, decisions, set(), lambda *args: NewsDecision("review", "manual")
        ).status == "accept"
        assert publication_decision(
            {**row, "seo_eligible": False}, decisions, set(),
            lambda *args: NewsDecision("accept", "automatic")
        ).status == "review"
        assert update_news.is_approved_indexable_signal(row)

        html = unescape(update_news.signal_page_html(row, [row]))
        assert "name=\"robots\" content=\"index,follow" in html
        assert "<h1>" + review["h1"] + "</h1>" in html
        assert 'class="signal-reader-tools"' in html
        assert 'class="signal-editorial-analysis"' in html
        assert 'class="signal-evidence"' in html
        for link in review["internal_links"]:
            assert 'href="' + link["url"] + '"' in html, link["url"]
        for item in review["reader_checklist"]:
            assert item in html
        match = re.search(r'<script type="application/ld\\+json">(.*?)</script>', html, re.S)
        assert match, "Schema absent"
        graph = json.loads(match.group(1))["@graph"]
        article = next(x for x in graph if x.get("@id", "").endswith("#article"))
        assert article["@type"] == "NewsArticle"
        assert article["citation"] == review["sources"]
        assert article["keywords"] == review["keywords"]
        assert article["dateModified"] >= review["reviewed_at"]

        if post:
            assert "<loc>" + row["signal_url"] + "</loc>" in sitemap
            page = ROOT / "signals" / slug / "index.html"
            assert page.is_file(), str(page)
            page_text = page.read_text(encoding="utf-8")
            assert 'name="robots" content="index,follow' in page_text
            assert review["seo_title"] in unescape(page_text)
            assert "signal-reader-tools" in page_text
            assert "signal-editorial-analysis" in page_text
            assert "signal-evidence" in page_text

    print("PASS: five approved original SXF Signals, searchable schema, verified sources, internal links and durable sitemap" +
          (" (post-build)" if post else " (pre-build)"))

if __name__ == "__main__":
    main()
