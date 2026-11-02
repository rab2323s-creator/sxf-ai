#!/usr/bin/env python3
"""Regression tests for owner-controlled Signal indexing and sitemap entries."""
from __future__ import annotations

import re
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from editorial_approval import (
    DecisionLedger, EditorialConfigError, enforce_noindex_on_html,
    publication_decision, retire_unapproved_signal_routes,
)
from news_relevance import NewsDecision


def test_page_headers():
    markup = ('<head><meta name="robots" content="index,follow" />'
              '<meta name="googlebot" content="index,follow" /></head>')
    noindex = enforce_noindex_on_html(markup)
    assert noindex.count('content="noindex,follow"') == 2
    assert enforce_noindex_on_html(noindex) == noindex, "Noindex must be idempotent"
    without_googlebot = '<head><meta name="robots" content="index,follow" /></head>'
    repaired = enforce_noindex_on_html(without_googlebot)
    assert 'name="robots" content="noindex,follow"' in repaired
    assert 'name="googlebot" content="noindex,follow"' in repaired
    # Old pages can omit BOTH directives or use alternate meta syntax.
    missing_both = '<head><title>Legacy source</title></head>'
    repaired_both = enforce_noindex_on_html(missing_both)
    assert repaired_both.count('content="noindex,follow"') == 2
    assert enforce_noindex_on_html(repaired_both) == repaired_both
    single_quote = "<head><meta content='index,follow' name='robots'></head>"
    assert 'content="noindex,follow"' in enforce_noindex_on_html(single_quote)
    duplicate = '<head><meta name="robots" content="index" /><meta name="robots" content="follow" /></head>'
    try:
        enforce_noindex_on_html(duplicate)
    except EditorialConfigError:
        pass
    else:
        raise AssertionError("Duplicated crawler policies must fail closed")
    for bad in ('<head></head><head></head>', '<meta name="robots" content="index,follow" />'):
        try:
            enforce_noindex_on_html(bad)
        except EditorialConfigError:
            pass
        else:
            raise AssertionError("Missing crawler directive must fail closed")

    with TemporaryDirectory() as folder:
        root = Path(folder)
        approved = root / "approved" / "index.html"
        rejected = root / "rejected" / "index.html"
        approved.parent.mkdir()
        rejected.parent.mkdir()
        approved.write_text(markup)
        rejected.write_text(markup)
        assert retire_unapproved_signal_routes(root, {"approved"}) == 1
        assert approved.read_text() == markup
        assert rejected.read_text().count('noindex,follow') == 2
        assert retire_unapproved_signal_routes(root, {"approved"}) == 0


def test_publication():
    item = {"url": "https://example.org/story", "title": "Model release",
            "source": "Anthropic", "seo_eligible": True}
    assess = lambda *args: NewsDecision("accept", "automated_accept")
    assert publication_decision(item, DecisionLedger({}), set(), assess).status == "review"
    approved = DecisionLedger({item["url"]: {
        **item, "decision": "approved",
    }})
    assert publication_decision(item, approved, set(), assess).status == "accept"
    assert publication_decision({**item, "seo_eligible": False}, approved, set(), assess).status == "review"
    assert publication_decision(item, DecisionLedger({}), {item["url"]}, assess).status == "accept"
    assert publication_decision(item, DecisionLedger({}), set(), assess).status != "accept"


def test_historical_indexing_snapshot():
    """The 89 previously indexed source URLs must remain published."""
    from editorial_approval import read_legacy_indexable_urls, read_legacy_urls
    from update_news import (ARCHIVE_OUT, SITEMAP, EDITORIAL_BASELINE_PATH,
                             EDITORIAL_INDEX_BASELINE_PATH, is_approved_indexable_signal)
    archived = json.loads(ARCHIVE_OUT.read_text(encoding="utf-8"))["items"]
    frozen = read_legacy_indexable_urls(EDITORIAL_INDEX_BASELINE_PATH)
    published = read_legacy_urls(EDITORIAL_BASELINE_PATH)
    by_url = {row["url"]: row for row in archived}
    assert len(frozen) == 89 and frozen <= published
    assert frozen <= by_url.keys()
    sitemap = SITEMAP.read_text(encoding="utf-8")
    historic = json.loads((ROOT / "data" / "editorial-legacy-sitemap-urls.json").read_text())
    assert historic["version"] == "sxf-preapproval-non-signal-sitemap-v1"
    assert len(historic["urls"]) == 250
    present = set(re.findall(r"<loc>(https://sxf\\.si/[^<]+)</loc>", sitemap))
    missing = set(historic["urls"]) - present
    assert not missing, "Historical non-Signal sitemap pages dropped: " + repr(sorted(missing)[:12])
    for url in frozen:
        row = by_url[url]
        assert is_approved_indexable_signal(row), "Formerly indexed source was deindexed: " + url
        assert "<loc>" + row["signal_url"] + "</loc>" in sitemap, (
            "Formerly indexed signal removed from sitemap: " + url)


def test_generated_sitemap():
    from update_news import (
        ARCHIVE_OUT, SITEMAP, SIGNALS_DIR,
        is_approved_indexable_signal,
    )
    import json
    archive = json.loads(ARCHIVE_OUT.read_text(encoding="utf-8"))["items"]
    document = SITEMAP.read_text(encoding="utf-8")
    indexed = set(re.findall(r"<loc>(https://sxf\.si/signals/[^<]+)</loc>", document))
    indexed.discard("https://sxf.si/signals/")
    expected = {row["signal_url"] for row in archive
                if is_approved_indexable_signal(row)}
    assert indexed == expected, (
        f"Signal sitemap approval drift: missing={expected-indexed}, extra={indexed-expected}"
    )
    archived_slugs = {row["signal_slug"] for row in archive}
    for row in archive:
        path = SIGNALS_DIR / row["signal_slug"] / "index.html"
        contents = path.read_text(encoding="utf-8")
        if is_approved_indexable_signal(row):
            assert 'name="robots" content="index,follow' in contents
        else:
            assert 'name="robots" content="noindex,follow"' in contents
    for path in SIGNALS_DIR.glob("*/index.html"):
        if path.parent.name not in archived_slugs:
            assert 'name="robots" content="noindex,follow"' in path.read_text(encoding="utf-8")


if __name__ == "__main__":
    test_page_headers()
    test_publication()
    # --post-build is run only after source regeneration on CI.
    if "--post-build" in sys.argv:
        test_generated_sitemap()
        test_historical_indexing_snapshot()
    print("PASS: human-only signal indexability, sitemap and orphan noindex policies")
