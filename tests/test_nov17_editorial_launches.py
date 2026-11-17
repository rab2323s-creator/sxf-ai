#!/usr/bin/env python3
"""Five owner-approved November 17 editorial analyses must survive every feed rebuild."""
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
    "https://openai.com/index/strengthening-nato-allied-cyber-defences-ai": "openai-daybreak-nato-cyber-defense-2026",
    "https://github.blog/changelog/2026-11-16-github-copilot-models-deprecated-on-november-16-2026": "github-copilot-models-retired-november-2026",
    "https://github.blog/changelog/2026-11-16-vs-code-retires-the-local-harness-in-february-2027": "vs-code-local-harness-retirement-february-2027",
    "https://huggingface.co/blog/openrouter": "hugging-face-openrouter-inference-routing-guide",
    "https://openai.com/index/expanding-chatgpt-for-academic-researchers": "chatgpt-academic-researchers-grants-2026",
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
        assert len(review["evidence"]) >= 8
        assert len(review["analysis"]) >= 4
        assert len(review["internal_links"]) >= 5
        assert len(review["reader_checklist"]) >= 5
        assert all(entry["source"] in review["sources"] for entry in review["evidence"])
        assert all(entry["source"] in review["sources"] for entry in review["analysis"])
        assert review["sxf_feature"]["type"] == "matrix"
        assert review["sxf_feature"]["mobile_stacked"] is True
        feature = review["sxf_feature"]
        assert 2 <= len(feature["columns"]) <= 4
        assert len(feature["rows"]) >= 3
        assert all(len(row_cells) == len(feature["columns"]) for row_cells in feature["rows"])
        assert feature["source"] in review["sources"]
        assert len(review["faq"]) >= 3
        assert len(review["longtail_keywords"]) >= 4
        assert len(review["search_questions"]) >= 4
        assert review["search_intent"]
        assert review["hero_image"]["path"].startswith("/assets/signals/")
        assert len(review["hero_image"]["alt"]) >= 70
        asset = ROOT / review["hero_image"]["path"].lstrip("/")
        assert asset.is_file(), "Missing source-grounded SVG: " + str(asset)
        illustration = asset.read_text(encoding="utf-8")
        assert "<svg " in illustration and "<title " in illustration and "<desc " in illustration
        for section in review["analysis"]:
            for link in section.get("inline_links", []):
                assert any(link["text"] in p for p in section["paragraphs"])
                assert link["url"].startswith("/") and not link["url"].startswith("//")
                destination = ROOT / link["url"].lstrip("/") / "index.html"
                if post or link["url"] not in {"/signals/" + s + "/" for s in SLUGS}:
                    assert destination.is_file(), "Broken inline link: " + link["url"]
        assert len({link["url"] for link in review["internal_links"]}) == len(review["internal_links"]), "Duplicate internal link"
        assert all(p["heading"] and len(p["paragraphs"]) >= 2 for p in review["analysis"])
        assert all(len(p) >= 150 for section in review["analysis"] for p in section["paragraphs"])
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
        assert "signal-research-feature" in html
        assert "signal-reader-faq" in html
        assert "sxf-compare-responsive" in html
        assert html.count("data-label=") >= len(review["sxf_feature"]["rows"]) * (len(feature["columns"]))
        assert review["hero_image"]["alt"] in html
        assert 'name="twitter:card" content="summary_large_image"' in html
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
        assert article["headline"] == review["h1"] or review["h1"] in html
        assert len(article["citation"]) >= 1
        assert article["mainEntityOfPage"]["@id"] == item["signal_url"] + "#webpage"
        assert article["url"] == item["signal_url"]
        assert article["author"]["name"] == "SXF / AI Editorial"
        assert article["publisher"]["name"] == "SXF / AI"
        assert article["datePublished"] == item["published"]
        assert article["image"]["@id"] == item["signal_url"] + "#primaryimage"
        assert len([node for node in graph if node.get("@type") == "BreadcrumbList"]) == 1
        assert any(node.get("@type") == "ImageObject" and
                   node.get("url") == "https://sxf.si" + review["hero_image"]["path"] for node in graph)
        assert all(node.get("@type") != "FAQPage" for node in graph), "Only visible FAQ; no unearned rich results"
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
            assert 'sxf-compare-responsive' in rendered
            assert 'signal-reader-faq' in rendered
            assert review["hero_image"]["path"] in rendered
            assert 'name="twitter:card" content="summary_large_image"' in rendered
            assert len(re.findall('data-label=', rendered)) >= len(feature["rows"]) * len(feature["columns"])
    print("PASS: five owner-approved November 17 reports, original analysis, durable SEO, source evidence and internal graph" +
          (" post-build" if post else " pre-build"))

if __name__ == "__main__":
    main()
