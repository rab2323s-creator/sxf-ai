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
    parse_meta_article,
    parse_meta_blog_index,
    parse_xai_article,
    parse_xai_news_index,
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



def test_meta_blog_discovery():
    body = b"""<html><body>
      <a href="/blog/introducing-muse-spark-meta-model-api/">Muse Spark</a>
      <a href="https://ai.meta.com/blog/introducing-muse-image-muse-video-msl?trk=test">Muse Image</a>
      <a href="/blog/">Blog home</a>
      <a href="https://example.com/blog/not-meta/">External</a>
      <a href="/blog/introducing-muse-spark-meta-model-api/#details">Duplicate</a>
    </body></html>"""
    urls = parse_meta_blog_index(
        body,
        discovery_url="https://ai.meta.com/blog/",
        max_urls=10,
    )
    expect(
        urls == [
            "https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/",
            "https://ai.meta.com/blog/introducing-muse-image-muse-video-msl",
        ],
        f"unexpected Meta discovery set: {urls}",
    )


def test_meta_article_parser():
    body = b"""<html><head>
      <meta property="og:title" content="Introducing Muse Spark 1.1 | AI at Meta">
      <meta name="description" content="Meta introduces Muse Spark 1.1, a multimodal reasoning model for agentic tasks, coding, tool use, and multimodal understanding.">
      <meta property="article:published_time" content="2026-07-09T12:00:00Z">
    </head><body><h1>Introducing Muse Spark 1.1</h1></body></html>"""
    item = parse_meta_article(
        body,
        "https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/",
    )
    expect(item["title"] == "Introducing Muse Spark 1.1", "Meta article title parse drift")
    expect(item["published"] == "2026-07-09T12:00:00Z", "Meta article published parse drift")
    expect(len(item["summary"]) >= 60, "Meta article summary is unexpectedly thin")


def test_meta_adapter_contract():
    index_one = b"""<html><body>
      <a href="/blog/introducing-muse-spark-meta-model-api/">Muse Spark</a>
    </body></html>"""
    index_two = b"""<html><body>
      <a href="/blog/introducing-muse-image-muse-video-msl/">Muse Image and Video</a>
    </body></html>"""
    article_one = b"""<html><head>
      <meta property="og:title" content="Introducing Muse Spark 1.1">
      <meta name="description" content="Meta introduces Muse Spark 1.1, a multimodal reasoning model for agentic tasks, coding, tool use, and multimodal understanding.">
      <meta property="article:published_time" content="2026-07-09T12:00:00Z">
    </head><body><h1>Introducing Muse Spark 1.1</h1></body></html>"""
    article_two = b"""<html><head>
      <meta property="og:title" content="Introducing Muse Image and Muse Video">
      <meta name="description" content="Meta introduces Muse Image and previews Muse Video, media generation models with image editing, composition, and native-audio video capabilities.">
      <meta property="article:published_time" content="2026-07-07T12:00:00Z">
    </head><body><h1>Introducing Muse Image and Muse Video</h1></body></html>"""

    responses = {
        "https://ai.meta.com/blog/": index_one,
        "https://ai.meta.com/blog/?page=2": index_two,
        "https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/": article_one,
        "https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/": article_two,
    }

    def fetcher(url):
        if url not in responses:
            raise AssertionError(f"unexpected Meta fixture URL {url}")
        return responses[url]

    config = {
        "name": "Meta",
        "url": "https://ai.meta.com/blog/",
        "adapter": "meta-blog",
        "status": "shadow",
        "max_current": 0,
        "discovery_pages": 2,
        "max_discovery": 10,
    }
    items, diagnostics = run_source_adapter(
        config,
        user_agent="SXF-test",
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
        fetcher=fetcher,
    )
    expect(len(items) == 2, f"expected 2 Meta adapter items, got {len(items)}")
    expect(diagnostics["discovered_count"] == 2, "Meta adapter discovered count drift")
    expect(diagnostics["parsed_count"] == 2, "Meta adapter parsed count drift")
    expect(diagnostics["invalid_count"] == 0, "Meta adapter fixture should not have invalid items")
    for item in items:
        provenance = item["provenance"]
        expect(provenance["adapter_contract_version"] == ADAPTER_CONTRACT_VERSION, "Meta contract version drift")
        expect(provenance["discovered_via"] == "official-blog-index", "Meta provenance discovery method drift")


def test_xai_news_discovery():
    body = b"""<html><body>
      <a href="/news/grok-4-7">Grok 4.7</a>
      <a href="https://x.ai/news/team-bots?utm_source=test">Team Bots</a>
      <a href="/news">News home</a>
      <a href="https://example.com/news/not-xai">External</a>
      <a href="/news/grok-4-7#pricing">Duplicate</a>
    </body></html>"""
    urls = parse_xai_news_index(
        body,
        discovery_url="https://x.ai/news",
        max_urls=10,
    )
    expect(
        urls == [
            "https://x.ai/news/grok-4-7",
            "https://x.ai/news/team-bots",
        ],
        f"unexpected xAI discovery set: {urls}",
    )


def test_xai_article_parser():
    body = b"""<html><head>
      <title>Introducing Grok 4.7 | SpaceXAI</title>
      <meta name="description" content="SpaceXAI's most powerful model for coding and knowledge work, with stronger long-horizon reasoning and improved safeguards.">
    </head><body>
      <div>Sep 21, 2026</div>
      <h1>Introducing Grok 4.7</h1>
      <p>Grok 4.7 is our most capable model for coding and knowledge work, with improvements for difficult long-running tasks and verification.</p>
    </body></html>"""
    item = parse_xai_article(body, "https://x.ai/news/grok-4-7")
    expect(item["title"] == "Introducing Grok 4.7", "xAI article title parse drift")
    expect(item["published"] == "2026-09-21T00:00:00Z", "xAI article published parse drift")
    expect(len(item["summary"]) >= 60, "xAI article summary is unexpectedly thin")


def test_xai_article_requires_date():
    body = b"""<html><head>
      <title>Undated xAI update | SpaceXAI</title>
      <meta name="description" content="This fixture intentionally contains a substantial summary but no verifiable publication date anywhere in the page.">
    </head><body><h1>Undated xAI update</h1></body></html>"""
    try:
        parse_xai_article(body, "https://x.ai/news/undated-update")
    except AdapterDriftError as exc:
        expect("published" in str(exc), f"xAI missing-date rejection drift: {exc}")
        return
    raise AssertionError("xAI article without a verified publication date must be rejected")


def test_xai_adapter_contract():
    index = b"""<html><body>
      <a href="/news/grok-4-7">Grok 4.7</a>
      <a href="/news/team-bots">Team Bots</a>
    </body></html>"""
    grok = b"""<html><head>
      <meta property="og:title" content="Introducing Grok 4.7 | SpaceXAI">
      <meta name="description" content="SpaceXAI's most powerful model for coding and knowledge work, with stronger long-horizon reasoning and improved safeguards.">
    </head><body><div>Sep 21, 2026</div><h1>Introducing Grok 4.7</h1></body></html>"""
    bots = b"""<html><head>
      <meta property="og:title" content="Team Bots: shared AI teammates that learn as they work | SpaceXAI">
      <meta name="description" content="Give a Grok Bot the files, apps, and expertise it needs, then share it so your whole team can work from the same context.">
    </head><body><div>Sep 28, 2026</div><h1>Team Bots: shared AI teammates that learn as they work</h1></body></html>"""
    responses = {
        "https://x.ai/news": index,
        "https://x.ai/news/grok-4-7": grok,
        "https://x.ai/news/team-bots": bots,
    }

    def fetcher(url):
        if url not in responses:
            raise AssertionError(f"unexpected xAI fixture URL {url}")
        return responses[url]

    config = {
        "name": "xAI",
        "url": "https://x.ai/news",
        "adapter": "xai-news",
        "status": "shadow",
        "max_current": 0,
        "max_discovery": 10,
    }
    items, diagnostics = run_source_adapter(
        config,
        user_agent="SXF-test",
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
        fetcher=fetcher,
    )
    expect(len(items) == 2, f"expected 2 xAI adapter items, got {len(items)}")
    expect(diagnostics["discovered_count"] == 2, "xAI adapter discovered count drift")
    expect(diagnostics["parsed_count"] == 2, "xAI adapter parsed count drift")
    expect(diagnostics["invalid_count"] == 0, "xAI adapter fixture should not have invalid items")
    for item in items:
        provenance = item["provenance"]
        expect(provenance["adapter_contract_version"] == ADAPTER_CONTRACT_VERSION, "xAI contract version drift")
        expect(provenance["discovered_via"] == "official-news-index", "xAI provenance discovery method drift")

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
    test_meta_blog_discovery()
    test_meta_article_parser()
    test_meta_adapter_contract()
    test_xai_news_discovery()
    test_xai_article_parser()
    test_xai_article_requires_date()
    test_xai_adapter_contract()
    test_zero_result_drift()
    print("source adapter tests passed")
