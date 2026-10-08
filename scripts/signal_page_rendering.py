"""Pure HTML rendering for the Signals index and shared signal-list rows.

All clock formatting, SEO head markup and site-shell dependencies are injected.
Article body rendering remains in update_news.py until separately verified.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import Callable


@dataclass(frozen=True)
class SignalPageContext:
    base_url: str
    display_date: Callable[[str], str]
    relative_time: Callable[[str], str]
    page_head: Callable[..., str]
    page_header: Callable[..., str]
    page_footer: Callable[..., str]


def signal_row(item, context: SignalPageContext):
    display_date = context.display_date
    return f'''<a class="signal-row" href="/signals/{escape(item["signal_slug"], quote=True)}/">
      <div class="signal-row-meta"><span>{escape(item["source"])}</span><time datetime="{escape(item["published"], quote=True)}">{escape(display_date(item["published"]))}</time></div>
      <h3>{escape(item["title"])}</h3>
      <div class="signal-row-foot"><span>{escape(item["category"])}</span><b>Open signal ↗</b></div>
    </a>'''


def signals_index_html(items, context: SignalPageContext):
    BASE_URL = context.base_url
    display_date = context.display_date
    relative_time = context.relative_time
    page_head = context.page_head
    page_header = context.page_header
    page_footer = context.page_footer
    canonical = f"{BASE_URL}/signals/"
    description = "Track verified AI model releases, agent updates, research, benchmarks, tools and open-source changes from primary sources with the SXF AI signal index."
    page_modified = max((item.get("modified_at") or item.get("published") or "" for item in items), default="")
    agent_pattern = re.compile(r"\\bagent(?:s|ic)?\\b|\\bmcp\\b|computer use|tool calling|multi[- ]step|long[- ]running", re.I)

    def latest_matching(predicate):
        return next((item for item in items if predicate(item)), None)

    snapshot_items = [
        ("MODEL", latest_matching(lambda item: item["category"] == "Models")),
        ("AGENT", latest_matching(lambda item: bool(agent_pattern.search(" ".join([item.get("title", ""), item.get("summary", "")]))))),
        ("RESEARCH", latest_matching(lambda item: item["category"] == "Research")),
        ("TOOLS", latest_matching(lambda item: item["category"] == "Tools")),
    ]
    snapshot_cards = []
    for label, item in snapshot_items:
        if not item:
            continue
        snapshot_cards.append(f'''<a class="signals-snapshot-card" href="{escape(item.get("signal_url", item["url"]), quote=True)}">
          <div><span>{escape(label)}</span><small>{escape(item["source"])}</small></div>
          <h3>{escape(item["title"])}</h3>
          <p>{escape(relative_time(item["published"]))} · Primary source linked</p>
          <b>Open signal ↗</b>
        </a>''')

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#webpage",
                "name": "AI Signals — Latest Models, Agents & Research Updates | SXF / AI",
                "url": canonical,
                "description": description,
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "publisher": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "publishingPrinciples": "https://sxf.si/about/#method",
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
                "mainEntity": {"@id": canonical + "#signal-list"},
                **({"dateModified": page_modified} if page_modified else {}),
                "about": [
                    {"@type": "Thing", "name": "AI models"},
                    {"@type": "Thing", "name": "AI agents"},
                    {"@type": "Thing", "name": "Artificial intelligence research"},
                    {"@type": "Thing", "name": "AI developer tools"},
                    {"@type": "Thing", "name": "Open source artificial intelligence"},
                ],
                "inLanguage": "en",
            },
            {
                "@type": "ItemList",
                "@id": canonical + "#signal-list",
                "name": "Latest verified AI signals",
                "description": "Latest primary-source AI model, agent, research, tool and open-source updates tracked by SXF / AI.",
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "numberOfItems": min(len(items), 40),
                "mainEntityOfPage": {"@id": canonical + "#webpage"},
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "item": {
                            "@type": "Article",
                            "@id": item["signal_url"] + "#article",
                            "name": item["title"],
                            "url": item["signal_url"],
                            "mainEntityOfPage": {"@id": item["signal_url"] + "#webpage"},
                            "isPartOf": {"@id": "https://sxf.si/#website"},
                        },
                    }
                    for i, item in enumerate(items[:40])
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "AI Signals", "item": canonical},
                ],
            },
        ],
    }
    rows = "".join(signal_row(item, context) for item in items[:40])
    archive_items = [item for item in items[40:] if item.get("seo_eligible")]
    archive_links = "".join(
        f'<a href="{escape(item.get("signal_url", item["url"]), quote=True)}"><span>{escape(item["title"])}</span><small>{escape(item["source"])} · {escape(display_date(item["published"]))}</small></a>'
        for item in archive_items
    )
    archive_directory = (
        f'''<section class="signals-directory shell" aria-labelledby="signals-directory-title">
          <div class="intel-section-head"><div><p class="eyebrow">VERIFIED ARCHIVE</p><h2 id="signals-directory-title">More verified AI signals.</h2></div><span>{len(archive_items)} indexed signals</span></div>
          <div class="signals-directory-list">{archive_links}</div>
        </section>'''
        if archive_items else ""
    )
    return f'''<!doctype html><html lang="en">{page_head("AI Signals — Latest Models, Agents & Research Updates | SXF / AI", description, canonical, schema)}
    <body class="intel-page collection-page signals-page"><a class="skip-link" href="#signals-main">Skip to signals</a>
    {page_header()}<main id="signals-main">
      <section class="collection-hero signals-hero shell">
        <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><span>Signals</span></nav>
        <p class="eyebrow">SXF AI SIGNAL INDEX</p>
        <h1>AI Signals:<br><span>Models, Agents & Research Updates</span></h1>
        <p>Track verified AI model releases, agent developments, research, benchmarks, developer tools and open-source changes. Every signal keeps the primary source attached so you can move from what changed to the evidence behind it.</p>
        <div class="collection-stats"><div><strong id="signalsCount">{len(items)}</strong><span>tracked signals</span></div><div><strong>Models · Agents · Research</strong><span>core intelligence</span></div><div><strong>3h</strong><span>refresh cycle</span></div></div>
      </section>

      <section class="signals-snapshot shell" aria-labelledby="signals-snapshot-title">
        <div class="intel-section-head"><div><p class="eyebrow">INTELLIGENCE SNAPSHOT</p><h2 id="signals-snapshot-title">What matters right now.</h2></div><a href="/about/#method">How SXF verifies signals ↗</a></div>
        <div class="signals-snapshot-grid">{"".join(snapshot_cards)}</div>
      </section>

      <section class="signals-explorer shell" aria-labelledby="signals-stream-title">
        <div class="intel-section-head"><div><p class="eyebrow">LIVE INDEX</p><h2 id="signals-stream-title">Latest verified AI signals.</h2></div><a href="/brief/">Read SXF Brief ↗</a></div>
        <div class="signals-toolbar" role="group" aria-label="Filter AI signals">
          <div class="signals-filters">
            <button class="signals-filter active" type="button" data-signal-filter="All">All</button>
            <button class="signals-filter" type="button" data-signal-filter="Models">Models</button>
            <button class="signals-filter" type="button" data-signal-filter="Agents">Agents</button>
            <button class="signals-filter" type="button" data-signal-filter="Research">Research</button>
            <button class="signals-filter" type="button" data-signal-filter="Tools">Tools</button>
            <button class="signals-filter" type="button" data-signal-filter="Open Source">Open Source</button>
          </div>
          <label class="signals-search"><span class="sr-only">Search all AI signals</span><input id="signalsSearch" type="search" placeholder="Search all signals — GPT-6, agents, Copilot…" autocomplete="off"></label>
        </div>
        <p class="signals-result-meta" id="signalsResultMeta">Showing the latest 40 signals. Filters and search use the full current SXF feed.</p>
        <div class="signal-list" id="signalsFeed">{rows}</div>
        <div class="signals-empty" id="signalsEmpty" hidden>No signals match this filter yet.</div>
      </section>

      {archive_directory}

      <section class="signals-gateways shell" aria-labelledby="signals-gateways-title">
        <div class="intel-section-head"><div><p class="eyebrow">EXPLORE BY INTENT</p><h2 id="signals-gateways-title">Move from updates to deeper intelligence.</h2></div></div>
        <div class="signals-gateway-grid">
          <a href="/models/"><span>MODELS</span><strong>AI Model Intelligence</strong><p>Releases, capabilities, context, limits and model pages.</p><b>Explore models ↗</b></a>
          <a href="/topics/ai-agents/"><span>AGENTS</span><strong>AI Agent Intelligence</strong><p>Agent systems, memory, reliability, security and workflows.</p><b>Explore agents ↗</b></a>
          <a href="/research/"><span>RESEARCH</span><strong>AI Research</strong><p>Benchmarks, evaluations, safety and research context.</p><b>Explore research ↗</b></a>
          <a href="/compare/"><span>COMPARE</span><strong>Compare AI Models</strong><p>Pricing, context windows, specifications and workload fit.</p><b>Compare models ↗</b></a>
          <a href="/models/pricing/"><span>PRICING</span><strong>AI Model Pricing</strong><p>Normalized API pricing and model specifications from primary sources.</p><b>Compare pricing ↗</b></a>
          <a href="/topics/ai-security/"><span>SECURITY</span><strong>AI Security Signals</strong><p>Prompt injection, agent risk, permissions, MCP and defenses.</p><b>Explore security ↗</b></a>
        </div>
      </section>
    </main>{page_footer()}<script src="/signals.js" defer></script></body></html>'''
