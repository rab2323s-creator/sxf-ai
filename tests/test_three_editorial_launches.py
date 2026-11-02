#!/usr/bin/env python3
"""Safely verify 3 owner-delegated, source-backed AI news launches."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news
from editorial_approval import read_decisions, publication_decision
from signal_editorial_reviews import REVIEWS
from news_relevance import NewsDecision

SOURCES = {
"https://blogs.microsoft.com/blog/2026/10/28/introducing-the-microsoft-copilot-harness-unlocking-the-potential-of-truly-multi-model-agentic-work/": "introducing-the-microsoft-copilot-harness-unlocking-the-potential-of-t-2ce02f1",
"https://github.blog/changelog/2026-10-28-github-intelligence-puts-your-code-context-and-history-to-work": "github-intelligence-puts-your-code-context-and-history-to-work-3a09379",
"https://www.anthropic.com/news/expanding-partnership-gsa": "expanding-our-partnership-with-gsa-to-bring-claude-to-all-levels-of-go-16faca1",
}
def main():
    decisions = read_decisions(ROOT / "data" / "editorial-decisions.json")
    inbox = json.loads((ROOT / "data" / "editorial-inbox.json").read_text())["items"]
    assert len(decisions) == 3 and not decisions.rejected_fingerprints
    archive = json.loads((ROOT / "data" / "archive.json").read_text())["items"]
    live = {row["url"]: row for row in archive}
    sitemap = (ROOT / "sitemap.xml").read_text()
    post = "--post-build" in sys.argv
    for url, slug in SOURCES.items():
        source_row = next((x for x in inbox if x["url"] == url), None)
        if post:
            # Accepted stories are intentionally removed from the review inbox.
            assert source_row is None, "Published story must leave review inbox"
            source_row = live[url]
        else:
            # An already-published, approved story no longer appears in inbox.
            # Pre-build CI must accept the persisted published archive identity.
            source_row = source_row or live.get(url)
            assert source_row is not None, "Approved story absent from inbox and archive"
        assert decisions[url]["decision"] == "approved"
        assert all(decisions[url][x] == source_row[x] for x in ("url", "title", "source"))
        review = REVIEWS[slug]
        assert len(review["evidence"]) >= 5 and len(review["analysis"]) >= 3
        row = update_news.prepare_items([source_row])[0]
        assert row["signal_slug"] == slug, (row["signal_slug"], slug)
        assert row["seo_eligible"] and row["summary"] == review["summary"]
        assert publication_decision(row, decisions, set(), lambda *a: NewsDecision("review", "default")).status == "accept"
        # Approval never bypasses SEO eligibility.
        assert publication_decision({**row, "seo_eligible": False}, decisions, set(), lambda *a: NewsDecision("accept", "auto")).status == "review"
        assert update_news.is_approved_indexable_signal(row)
        rendered = update_news.signal_page_html(row, [row])
        assert 'name="robots" content="index,follow' in rendered
        assert review["seo_title"] in rendered
        assert "signal-editorial-analysis" in rendered
        assert "signal-evidence" in rendered
        if post:
            assert url in live, "Approved story missing from published archive: " + url
            assert live[url]["seo_eligible"], "Approved story was saved without SEO eligibility"
            assert "<loc>" + row["signal_url"] + "</loc>" in sitemap
            path = ROOT / "signals" / slug / "index.html"
            assert path.is_file()
            html = path.read_text()
            assert 'name="robots" content="index,follow' in html
            assert review["seo_title"] in html
            assert "signal-editorial-analysis" in html and "signal-evidence" in html
    print("PASS: 3 reviewed source-cited AI launches, approval identity, SEO and archive" + (" post-build" if post else ""))

if __name__ == "__main__":
    main()
