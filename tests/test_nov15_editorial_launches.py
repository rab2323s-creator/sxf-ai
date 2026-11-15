#!/usr/bin/env python3
"""Five owner-approved November 15 editorial analyses must survive every feed rebuild."""
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
    "https://openai.com/index/introducing-chatgpt-wallet": "chatgpt-wallet-payment-approval-safety",
    "https://huggingface.co/blog/ggml-org/llama-cpp-v1": "llama-cpp-1-0-api-abi-stability-upgrade",
    "https://github.blog/changelog/2026-11-13-gemini-4-hydrogen-in-github-copilot": "gemini-4-hydrogen-github-copilot-availability",
    "https://github.blog/changelog/2026-11-13-manage-ai-scan-for-repositories-using-the-rest-api": "github-ai-scan-repository-rest-api-setup",
    "https://openai.com/index/children-first-declaration": "openai-child-safety-research-funding-2026",
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
        assert len(review["evidence"]) >= 9
        assert len(review["analysis"]) >= 4
        assert len(review["internal_links"]) >= 5
        assert len(review["reader_checklist"]) >= 5
        assert all(entry["source"] in review["sources"] for entry in review["evidence"])
        assert all(entry["source"] in review["sources"] for entry in review["analysis"])
        assert len(review["faq"]) >= 3
        assert review["hero_image"]["path"].startswith("/assets/signals/")
        assert review["hero_image"]["alt"] and review["hero_image"]["caption"]
        asset_path = ROOT / review["hero_image"]["path"].lstrip("/")
        assert asset_path.is_file(), "Missing original image: " + str(asset_path)
        image_svg = asset_path.read_text(encoding="utf-8")
        assert "<svg " in image_svg and "<title " in image_svg and "<desc " in image_svg
        assert review["sxf_feature"]["source"] in review["sources"]
        assert review["sxf_feature"]["type"] in {"matrix", "cards", "steps"}
        for section in review["analysis"]:
            assert len(section["paragraphs"]) >= 2
            for link in section.get("inline_links", []):
                assert any(link["text"] in p for p in section["paragraphs"])
                assert (ROOT / link["url"].lstrip("/") / "index.html").is_file(), link["url"]
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

        if slug == "chatgpt-wallet-payment-approval-safety":
            assert "launch" in review["seo_title"].lower()
            assert "rollout" in review["h1"].lower()
            assert review["brief_status_label"] == "ROLLOUT STATUS"
            assert review["featured_guide"]["url"] == "/guides/chatgpt-wallet/"
            assert "2026" in review["meta_description"]
            assert review["search_intent"].startswith("News and release-status")
        if slug == "openai-child-safety-research-funding-2026":
            assert review["seo_title"].startswith("OpenAI's $2M")
            assert "What It Means" in review["h1"]
            assert len(review["funding_comparison"]["rows"]) == 5
            assert len(review["funding_comparison"]["sources"]) == 2
            assert "https://openai.com/index/teen-development-research-grants/" in review["sources"]
        if slug == "github-ai-scan-repository-rest-api-setup":
            assert "422" in review["seo_title"]
            assert "repository_scan" in review["h1"]
            assert len(review["sources"]) >= 5
        html = unescape(update_news.signal_page_html(item, [item]))
        assert 'name="robots" content="index,follow' in html
        assert "<h1>" + review["h1"] + "</h1>" in html
        if slug == "chatgpt-wallet-payment-approval-safety":
            assert 'href="/guides/chatgpt-wallet/"' in html
            assert "<span>ROLLOUT STATUS</span>" in html
            assert "On November 13, 2026, OpenAI announced" in html
        if slug == "openai-child-safety-research-funding-2026":
            assert "signal-funding-comparison" in html
            assert "OpenAI's AI Child Safety Research Funding: $2M vs $5M" in html
            assert "separate announced commitments" in html
            assert html.index("signal-funding-comparison") < html.index("signal-editorial-analysis")
            assert 'href="https://openai.com/index/teen-development-research-grants/"' in html
        if slug == "github-ai-scan-repository-rest-api-setup":
            names = ("sxf-ai-scan-api-examples", "sxf-ai-scan-policy-hierarchy",
                     "sxf-ai-scan-errors", "sxf-ai-scan-tool-comparison",
                     "sxf-ai-scan-deployment-lab")
            assert all(html.count('id="' + name + '"') == 1 for name in names)
            assert "X-GitHub-Api-Version: 2026-03-10" in html
            assert "Documentation-derived, unexecuted examples." in html
        assert "signal-reader-tools" in html
        assert "signal-editorial-analysis" in html
        assert "signal-evidence" in html
        assert "signal-research-feature" in html
        assert "signal-reader-faq" in html
        assert review["hero_image"]["alt"] in html
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
        assert article["image"]["@id"] == item["signal_url"] + "#primaryimage"
        assert article["author"]["name"] == "SXF / AI Editorial"
        assert article["publisher"]["name"] == "SXF / AI"
        assert any(x.get("@type") == "ImageObject" and x.get("url") == "https://sxf.si" + review["hero_image"]["path"] for x in graph)
        assert len([x for x in graph if x.get("@type") == "BreadcrumbList"]) == 1
        assert article["headline"] == review["h1"] or review["h1"] in html
        assert len(article["citation"]) >= 1
        if post:
            assert "<loc>" + item["signal_url"] + "</loc>" in sitemap
            path = ROOT / "signals" / slug / "index.html"
            assert path.is_file(), "Missing published HTML: " + str(path)
            rendered = path.read_text(encoding="utf-8")
            assert 'name="robots" content="index,follow' in rendered
            assert 'rel="canonical" href="' + item["signal_url"] + '"' in rendered
            assert review["seo_title"] in unescape(rendered)
            if slug == "chatgpt-wallet-payment-approval-safety":
                assert 'href="/guides/chatgpt-wallet/"' in rendered
                assert "<span>ROLLOUT STATUS</span>" in rendered
                assert review["h1"] in unescape(rendered)
            if slug == "openai-child-safety-research-funding-2026":
                assert "signal-funding-comparison" in rendered
                assert "separate announced commitments" in rendered
                assert 'href="https://openai.com/index/teen-development-research-grants/"' in rendered
                assert review["h1"] in unescape(rendered)
            if slug == "github-ai-scan-repository-rest-api-setup":
                for name in ("sxf-ai-scan-api-examples", "sxf-ai-scan-policy-hierarchy",
                             "sxf-ai-scan-errors", "sxf-ai-scan-tool-comparison",
                             "sxf-ai-scan-deployment-lab"):
                    assert rendered.count('id="' + name + '"') == 1
                assert "X-GitHub-Api-Version: 2026-03-10" in rendered
            assert "signal-editorial-analysis" in rendered
            assert "signal-evidence" in rendered
            assert "signal-reader-tools" in rendered
            assert "signal-research-feature" in rendered and "signal-reader-faq" in rendered
            assert review["hero_image"]["path"] in rendered
    print("PASS: five owner-approved November 15 reports, original analysis, durable SEO, source evidence and internal graph" +
          (" post-build" if post else " pre-build"))

if __name__ == "__main__":
    main()
