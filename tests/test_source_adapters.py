#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from source_adapters import (  # noqa: E402
    ADAPTER_CONTRACT_VERSION,
    AdapterDriftError,
    parse_anthropic_article,
    parse_anthropic_sitemap,
    run_source_adapter,
)


FIXTURES = ROOT / "tests" / "fixtures"


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def test_sitemap_discovery():
    body = (FIXTURES / "anthropic-sitemap.xml").read_bytes()
    urls, invalid = parse_anthropic_sitemap(
        body,
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
        discovery_days=45,
        max_urls=10,
    )
    expect(invalid == 0, "fixture sitemap should have no invalid candidate dates")
    expect(
        urls == [
            "https://www.anthropic.com/news/example-enterprise-update",
            "https://www.anthropic.com/claude-sonnet-5-5",
        ],
        f"unexpected Anthropic discovery set: {urls}",
    )


def test_model_discovery_reservation():
    body = b'''<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://www.anthropic.com/news/newest-news</loc><lastmod>2026-10-03T08:00:00Z</lastmod></url>
      <url><loc>https://www.anthropic.com/claude-opus-5-5</loc><lastmod>2026-09-22T08:00:00Z</lastmod></url>
    </urlset>'''
    urls, _invalid = parse_anthropic_sitemap(
        body,
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
        discovery_days=45,
        max_urls=1,
    )
    expect(
        urls == ["https://www.anthropic.com/claude-opus-5-5"],
        f"model announcement reservation failed: {urls}",
    )


def test_undated_model_discovery():
    body = b'''<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://www.anthropic.com/claude-opus-5-5</loc></url>
      <url><loc>https://www.anthropic.com/news/newest-news</loc><lastmod>2026-10-03T08:00:00Z</lastmod></url>
    </urlset>'''
    urls, invalid = parse_anthropic_sitemap(
        body,
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
        discovery_days=45,
        max_urls=2,
    )
    expect("https://www.anthropic.com/claude-opus-5-5" in urls, "undated model page must be discovered")
    expect(invalid == 0, f"undated model page should not count as invalid: {invalid}")


def test_article_parser():
    body = (FIXTURES / "anthropic-sonnet-article.html").read_bytes()
    item = parse_anthropic_article(body, "https://www.anthropic.com/claude-sonnet-5-5")
    expect(item["title"] == "Claude Sonnet 5.5", "article title parse drift")
    expect(item["published"] == "2026-09-28T12:00:00Z", "article published parse drift")
    expect(len(item["summary"]) >= 60, "article summary is unexpectedly thin")


def test_adapter_contract():
    sitemap = (FIXTURES / "anthropic-sitemap.xml").read_bytes()
    sonnet = (FIXTURES / "anthropic-sonnet-article.html").read_bytes()
    news = (FIXTURES / "anthropic-news-article.html").read_bytes()
    responses = {
        "https://www.anthropic.com/sitemap.xml": sitemap,
        "https://www.anthropic.com/claude-sonnet-5-5": sonnet,
        "https://www.anthropic.com/news/example-enterprise-update": news,
    }

    def fetcher(url):
        if url not in responses:
            raise AssertionError(f"unexpected fixture URL {url}")
        return responses[url]

    config = {
        "name": "Anthropic",
        "url": "https://www.anthropic.com/sitemap.xml",
        "adapter": "anthropic-sitemap",
        "status": "shadow",
        "max_current": 0,
        "discovery_days": 45,
        "max_discovery": 10,
    }
    items, diagnostics = run_source_adapter(
        config,
        user_agent="SXF-test",
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
        fetcher=fetcher,
    )
    expect(len(items) == 2, f"expected 2 adapter items, got {len(items)}")
    expect(diagnostics["parsed_count"] == 2, "adapter diagnostics parsed count drift")
    expect(diagnostics["invalid_count"] == 0, "adapter fixture should not have invalid items")
    for item in items:
        provenance = item["provenance"]
        expect(provenance["adapter_contract_version"] == ADAPTER_CONTRACT_VERSION, "contract version drift")
        expect(provenance["discovered_via"] == "official-sitemap", "provenance discovery method drift")


def test_zero_result_drift():
    stale = b'''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://www.anthropic.com/about</loc><lastmod>2026-10-02T00:00:00Z</lastmod></url>
    </urlset>'''
    try:
        parse_anthropic_sitemap(
            stale,
            now=datetime(2026, 10, 3, tzinfo=timezone.utc),
            discovery_days=45,
            max_urls=10,
        )
    except AdapterDriftError:
        return
    raise AssertionError("zero-result sitemap must raise AdapterDriftError")


if __name__ == "__main__":
    test_sitemap_discovery()
    test_model_discovery_reservation()
    test_undated_model_discovery()
    test_article_parser()
    test_adapter_contract()
    test_zero_result_drift()
    print("source adapter tests passed")
