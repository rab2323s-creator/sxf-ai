#!/usr/bin/env python3
"""Five owner-approved November 6 editorial analyses must survive every feed rebuild."""
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
    "https://openai.com/index/introducing-gpt-6-cyber": "gpt-6-cyber-security-benchmarks-access",
    "https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemini-omni-1-2-flash/": "gemini-omni-1-2-flash-video-pricing",
    "https://huggingface.co/blog/nvidia/cosmos-interactive-world-simulation": "nvidia-cosmos-3-world-models-simulation",
    "https://research.google/blog/detecting-signs-of-hypertension-using-wearable-sensors/": "google-smartwatch-hypertension-ai-study",
    "https://openai.com/index/setting-new-standard-responsible-ai-infrastructure": "openai-data-center-community-compact",
}
SLUGS = set(SOURCES.values())

def main():
    post = "--post-build" in sys.argv
    decisions = read_decisions(ROOT / "data" / "editorial-decisions.json")
    inbox = json.loads((ROOT / "data" / "editorial-inbox.json").read_text(encoding="utf-8"))["items"]
    archive = json.loads((ROOT / "data" / "archive.json").read_text(encoding="utf-8"))["items"]
    published = {row["url"]: row for row in archive}
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    aliases = json.loads((ROOT / "data" / "slug_aliases.json").read_text(encoding="utf-8"))
    for url, slug in SOURCES.items():
        assert aliases[url] == slug, "Stable canonical slug alias missing: " + url
        assert decisions[url]["decision"] == "approved", "Owner approval missing"
        row = next((r for r in inbox if r["url"] == url), None)
        if post:
            assert row is None, "Published article remains in pending review queue"
            assert url in published, "Approved article absent from permanent archive"
            row = published[url]
        else:
            row = row or published.get(url)
        assert row is not None, "Approved article lost before ingestion: " + url
        assert decisions[url]["title"] == row["title"]
        assert decisions[url]["source"] == row["source"]
        review = REVIEWS[slug]
        assert review["primary_source"] == url
        assert 30 <= len(review["seo_title"]) <= 60
        assert 105 <= len(review["meta_description"]) <= 160
        assert len(review["summary"]) >= 120
        assert len(review["evidence"]) >= 5
        assert len(review["analysis"]) >= 3
        assert len(review["internal_links"]) >= 3
        assert len(review["reader_checklist"]) >= 3
        assert all(entry["source"] in review["sources"] for entry in review["evidence"])
        assert all(entry["source"] in review["sources"] for entry in review["analysis"])
        for link in review["internal_links"]:
            target = link["url"]
            assert target.startswith("/") and not target.startswith("//")
            destination = ROOT / target.lstrip("/") / "index.html"
            if post or target not in {"/signals/" + s + "/" for s in SLUGS}:
                assert destination.is_file(), "Broken internal link: " + target

        item = update_news.prepare_items([row])[0]
        assert item["signal_slug"] == slug
        assert item["seo_eligible"], "SEO quality gate failed: " + slug
        assert item["summary"] == review["summary"]
        assert publication_decision(
            item, decisions, set(), lambda *args: NewsDecision("review", "blocked")
        ).status == "accept"
        assert publication_decision(
            {**item, "seo_eligible": False}, decisions, set(),
            lambda *args: NewsDecision("accept", "bypass")
        ).status == "review", "Must never bypass quality gate"
        assert update_news.is_approved_indexable_signal(item)

        html = unescape(update_news.signal_page_html(item, [item]))
        assert 'name="robots" content="index,follow' in html
        assert "<h1>" + review["h1"] + "</h1>" in html
        assert "signal-reader-tools" in html
        assert "signal-editorial-analysis" in html
        assert "signal-evidence" in html
        for link in review["internal_links"]:
            assert 'href="' + link["url"] + '"' in html
        schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        assert schema
        graph = json.loads(schema.group(1))["@graph"]
        article = next(x for x in graph if x.get("@id", "").endswith("#article"))
        assert article["@type"] == "NewsArticle"
        assert article["citation"] == review["sources"]
        assert article["keywords"] == review["keywords"]
        assert article["dateModified"] >= review["reviewed_at"]
        if post:
            assert "<loc>" + item["signal_url"] + "</loc>" in sitemap
            path = ROOT / "signals" / slug / "index.html"
            assert path.is_file(), "Missing published HTML: " + str(path)
            rendered = path.read_text(encoding="utf-8")
            assert 'name="robots" content="index,follow' in rendered
            assert 'rel="canonical" href="' + item["signal_url"] + '"' in rendered
            assert review["seo_title"] in unescape(rendered)
            assert "signal-editorial-analysis" in rendered
            assert "signal-evidence" in rendered
            assert "signal-reader-tools" in rendered
    print("PASS: five owner-approved November 6 reports, original analysis, durable SEO, source evidence and internal graph" +
          (" post-build" if post else " pre-build"))

if __name__ == "__main__":
    main()
