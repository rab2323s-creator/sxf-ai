#!/usr/bin/env python3
"""Article rendering parity contracts for ordinary Signals and the GitHub special case."""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from html_shell import page_head, page_header, page_footer
from signal_article_rendering import SignalArticleContext, signal_page_html
import update_news

SPECIAL_SLUG = "github-async-merge-api-generally-available-2bced9c"


def sample(slug, *, eligible, title="AI <Model> & Update", changed="2026-10-09T09:00:00Z"):
    return {
        "signal_slug": slug,
        "signal_url": f"https://sxf.si/signals/{slug}/",
        "url": f"https://primary.example/{slug}?a=1&b=2",
        "title": title,
        "summary": "Verified source summary",
        "source": "Primary & Source",
        "category": "Models",
        "signal_score": 84,
        "published": "2026-10-08T12:00:00Z",
        "modified_at": changed,
        "seo_eligible": eligible,
        "editorial": {
            "what_changed": "<Evidence> published & verified.",
            "why_it_matters": "Model capabilities matter.",
            "what_to_verify": "Check the source link.",
        },
    }


def schema_from(html):
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert match, "JSON-LD missing"
    return json.loads(match.group(1))


def graph_by_type(schema, value):
    return next(e for e in schema["@graph"] if e["@type"] == value)


def main():
    calls = []
    def eligibility(row):
        calls.append(row["signal_slug"])
        return row.get("seo_eligible", False)

    ctx = SignalArticleContext(
        base_url="https://sxf.si",
        compact_description=lambda row: row["editorial"]["what_changed"],
        seo_signal_eligible=eligibility,
        category_path=lambda cat: "/models/" if cat == "Models" else "/signals/",
        item_topics=lambda row: [{"slug": "model-updates", "name": "Model Updates"}],
        extract_models=lambda title: ["GPT 6"],
        slugify=lambda name: "gpt-6",
        related_items=lambda row, rows: [x for x in rows if x["url"] != row["url"]][:1],
        signal_row=lambda row: f'<a class="signal-row" href="/signals/{row["signal_slug"]}/">Related</a>',
        editorial_units=lambda row: row["editorial"],
        display_date=lambda value: "October 8, 2026",
        page_head=page_head,
        page_header=page_header,
        page_footer=page_footer,
    )
    normal = sample("ordinary-ai-update", eligible=True)
    previous = sample("older-signal", eligible=True)
    hidden = sample("private-signal", eligible=False)
    following = sample("newer-signal", eligible=True)
    items = [previous, normal, hidden, following]
    untouched = copy.deepcopy(items)

    html = signal_page_html(normal, items, ctx)
    assert '<link rel="canonical" href="https://sxf.si/signals/ordinary-ai-update/" />' in html
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
    assert '<meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in html
    assert "<h1>AI &lt;Model&gt; &amp; Update</h1>" in html
    assert "https://primary.example/ordinary-ai-update?a=1&amp;b=2" in html
    assert '<a href="/models/gpt-6/">GPT 6</a>' in html
    assert '<a href="/topics/model-updates/">Model Updates</a>' in html
    assert '<a rel="prev" href="/signals/older-signal/">' in html
    assert '<a rel="next" href="/signals/newer-signal/">' in html
    assert '/signals/private-signal/' not in html
    assert '<a class="signal-row" href="/signals/older-signal/">Related</a>' in html
    assert '<meta property="og:type" content="article" />' in html

    graph = schema_from(html)["@graph"]
    assert len(graph) == 3
    page, article, crumbs = graph
    assert page["@type"] == "WebPage"
    assert page["@id"] == normal["signal_url"] + "#webpage"
    assert article["@type"] == "Article"
    assert article["datePublished"] == normal["published"]
    assert article["dateModified"] == normal["modified_at"]
    assert article["citation"] == normal["url"]
    assert article["keywords"] is None, "Preserve existing JSON-LD, including null field"
    assert crumbs["@type"] == "BreadcrumbList"
    assert crumbs["itemListElement"][2]["item"] == "https://sxf.si/models/"
    assert items == untouched, "Rendering mutated input archive records"

    noindex = signal_page_html(hidden, items, ctx)
    assert '<meta name="robots" content="noindex,follow" />' in noindex
    assert '<meta name="googlebot" content="noindex,follow" />' in noindex
    assert '<nav class="signal-archive-navigation' not in noindex
    assert schema_from(noindex)["@graph"][1]["dateModified"] == hidden["modified_at"]

    special = sample(SPECIAL_SLUG, eligible=True, title="Original GitHub title")
    deep = signal_page_html(special, [special], ctx)
    assert '<link rel="canonical" href="https://sxf.si/signals/' + SPECIAL_SLUG + '/" />' in deep
    assert "GitHub Async Merge API: GA, Stacked PRs &amp; Merge Queues" in deep
    assert '<section class="signal-deep-dive shell"' in deep
    assert "PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async" in deep
    assert "Verified October 5, 2026" in deep
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in deep
    special_schema = schema_from(deep)["@graph"]
    assert len(special_schema) == 4
    assert special_schema[1]["@type"] == ["Article", "TechArticle"]
    assert special_schema[1]["dateModified"] == "2026-10-05"
    assert special_schema[1]["citation"] == [
        special["url"],
        "https://docs.github.com/en/rest/pulls/pulls?apiVersion=2026-03-10",
    ]
    assert len(special_schema[1]["keywords"]) == 6
    faq = graph_by_type({"@graph": special_schema}, "FAQPage")
    assert len(faq["mainEntity"]) == 4
    assert all(q["@type"] == "Question" for q in faq["mainEntity"])
    assert '\"<Evidence>\"' not in deep, "Escaped editorial text should never be raw HTML"

    special_hidden = dict(special, seo_eligible=False)
    special_noindex = signal_page_html(special_hidden, [special_hidden], ctx)
    assert '<meta name="robots" content="noindex,follow" />' in special_noindex
    assert len(schema_from(special_noindex)["@graph"]) == 4
    assert items == untouched
    assert calls, "SEO eligibility callback must be resolved as before"

    # Compatibility wrapper preserves the original function signature.
    wrapper_html = update_news.signal_page_html(normal, items)
    wrapper_schema = schema_from(wrapper_html)["@graph"]
    assert wrapper_schema[1]["datePublished"] == normal["published"]
    assert wrapper_schema[1]["dateModified"] == normal["modified_at"]
    assert '<link rel="canonical" href="' + normal["signal_url"] + '" />' in wrapper_html
    assert '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' in wrapper_html
    assert len(schema_from(update_news.signal_page_html(special, [special]))["@graph"]) == 4

    print("PASS: signal articles canonical, robots/noindex, dates, schema, archive links, source escaping and GitHub deep dive")


if __name__ == "__main__":
    main()
