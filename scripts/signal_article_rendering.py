"""Render one SXF signal article, including the existing verified GitHub deep dive.

The HTML/SEO contract remains unchanged. All integration dependencies are
supplied by the caller; this module performs no network or filesystem I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Callable


@dataclass(frozen=True)
class SignalArticleContext:
    base_url: str
    compact_description: Callable
    seo_signal_eligible: Callable
    category_path: Callable
    item_topics: Callable
    extract_models: Callable
    slugify: Callable
    related_items: Callable
    signal_row: Callable
    editorial_units: Callable
    display_date: Callable
    page_head: Callable
    page_header: Callable
    page_footer: Callable


def signal_page_html(item, items, context: SignalArticleContext):
    BASE_URL = context.base_url
    compact_description = context.compact_description
    seo_signal_eligible = context.seo_signal_eligible
    category_path = context.category_path
    item_topics = context.item_topics
    extract_models = context.extract_models
    slugify = context.slugify
    related_items = context.related_items
    signal_row = context.signal_row
    editorial_units = context.editorial_units
    display_date = context.display_date
    page_head = context.page_head
    page_header = context.page_header
    page_footer = context.page_footer
    canonical = item["signal_url"]
    is_async_merge_deep_dive = canonical.endswith("/github-async-merge-api-generally-available-2bced9c/")
    page_title = item["title"] + " | SXF / AI"
    page_h1 = item["title"]
    description = compact_description(item)
    modified = item.get("modified_at") or item["published"]
    if is_async_merge_deep_dive:
        page_title = "GitHub Async Merge API: GA, Stacked PRs & Merge Queues | SXF / AI"
        page_h1 = "GitHub Async Merge API: GA, Stacked PRs & Merge Queues"
        description = "GitHub's async merge API is generally available. Learn how merge-async works, stacked pull request support, merge queues, permissions, status polling, errors and migration from synchronous merges."
        modified = "2026-10-05"
    indexable = bool(item.get("seo_eligible", seo_signal_eligible(item)))
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if indexable else "noindex,follow"
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": page_title,
                "description": description,
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "mainEntity": {"@id": canonical + "#article"},
                "publisher": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "publishingPrinciples": "https://sxf.si/about/#method",
                "inLanguage": "en",
            },
            {
                "@type": ["Article", "TechArticle"] if is_async_merge_deep_dive else "Article",
                "@id": canonical + "#article",
                "headline": page_h1,
                "description": description,
                "datePublished": item["published"],
                "dateModified": modified,
                "mainEntityOfPage": {"@id": canonical + "#webpage"},
                "url": canonical,
                "articleSection": item["category"],
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "author": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "creator": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "publisher": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "publishingPrinciples": "https://sxf.si/about/#method",
                "citation": [
                    item["url"],
                    "https://docs.github.com/en/rest/pulls/pulls?apiVersion=2026-03-10",
                ] if is_async_merge_deep_dive else item["url"],
                "keywords": [
                    "GitHub async merge API",
                    "GitHub merge API",
                    "stacked pull requests",
                    "GitHub merge queue",
                    "merge-async endpoint",
                    "GitHub REST API",
                ] if is_async_merge_deep_dive else None,
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Signals", "item": BASE_URL + "/signals/"},
                    {"@type": "ListItem", "position": 3, "name": item["category"], "item": BASE_URL + category_path(item["category"])},
                ],
            },
        ],
    }
    if is_async_merge_deep_dive:
        schema["@graph"].append({
            "@type": "FAQPage",
            "@id": canonical + "#faq",
            "mainEntityOfPage": {"@id": canonical + "#webpage"},
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "What is the GitHub async merge API?",
                    "acceptedAnswer": {"@type": "Answer", "text": "It is GitHub's REST API for requesting a pull request merge in the background or adding the pull request to a merge queue. New requests can return HTTP 202 with a UUID that is used to poll the merge result."},
                },
                {
                    "@type": "Question",
                    "name": "Does the async merge API support stacked pull requests?",
                    "acceptedAnswer": {"@type": "Answer", "text": "Yes. GitHub documents the async merge API as the required API for merging stacked pull requests, including open downstack pull requests."},
                },
                {
                    "@type": "Question",
                    "name": "What permission is required for an asynchronous merge?",
                    "acceptedAnswer": {"@type": "Answer", "text": "GitHub documents Contents repository permission with write access for fine-grained tokens used with the asynchronous merge endpoint."},
                },
                {
                    "@type": "Question",
                    "name": "How long can an async merge result be fetched?",
                    "acceptedAnswer": {"@type": "Answer", "text": "GitHub documents that an asynchronous merge result is retained for 24 hours after its most recent update; after that, fetching that UUID returns 404."},
                },
            ],
        })
        # Remove null-only optional properties from the special graph before serialization.
        for entity in schema["@graph"]:
            if entity.get("keywords") is None:
                entity.pop("keywords", None)

    topics = item_topics(item)
    models = extract_models(item["title"])
    topic_links = "".join(
        f'<a href="/topics/{escape(t["slug"], quote=True)}/">{escape(t["name"])}</a>' for t in topics[:4]
    )
    model_links = "".join(
        f'<a href="/models/{escape(slugify(name), quote=True)}/">{escape(name)}</a>' for name in models[:4]
    )
    deep_dive_html = ""
    if is_async_merge_deep_dive:
        deep_dive_html = f'''
        <section class="signal-deep-dive shell" aria-labelledby="async-merge-explained">
          <div class="intel-section-head"><div><p class="eyebrow">SXF TECHNICAL EXPLAINER</p><h2 id="async-merge-explained">How GitHub's async merge API works.</h2></div><span>Verified October 5, 2026</span></div>
          <div class="deep-dive-lead">
            <p>GitHub's asynchronous merge endpoint changes the integration pattern from “request a merge and wait for the final result” to “submit work, receive a request identifier, then check the result.” That matters most in busy repositories, merge-queue workflows and stacked pull-request systems where a merge can involve checks, rules, retries or multiple dependent pull requests.</p>
          </div>
          <div class="deep-dive-grid">
            <article><span>01 / SUBMIT</span><h3>Send the merge request.</h3><p>Use <code>PUT /repos/{{owner}}/{{repo}}/pulls/{{pull_number}}/merge-async</code>. For a new background request GitHub can return <code>202 Accepted</code> plus a UUID.</p></article>
            <article><span>02 / PROCESS</span><h3>GitHub handles the merge asynchronously.</h3><p>Background processing lets GitHub retry certain failures and reduces timeout risk for complex merges. The request can merge directly or use a merge queue.</p></article>
            <article><span>03 / POLL</span><h3>Fetch the result by UUID.</h3><p>Poll the result endpoint until the request reports <code>merged</code>, <code>enqueued</code> or <code>failed</code>. An <code>enqueued</code> result means the PR entered the queue; it does not mean the PR has merged yet.</p></article>
          </div>

          <div class="deep-dive-section">
            <p class="eyebrow">WHY THIS API IS DIFFERENT</p>
            <h2>Async merge vs the synchronous merge endpoint.</h2>
            <div class="deep-dive-table-wrap"><table class="deep-dive-table">
              <thead><tr><th>Area</th><th>Async merge API</th><th>Synchronous merge endpoint</th></tr></thead>
              <tbody>
                <tr><th>Execution model</th><td>Background request with status lookup</td><td>Merge result returned in the request flow</td></tr>
                <tr><th>New request status</th><td><code>202</code> + UUID when accepted</td><td><code>200</code> when merge succeeds</td></tr>
                <tr><th>Stacked PRs</th><td>Required API for stacked pull requests</td><td>Not the supported path for stacked PR merging</td></tr>
                <tr><th>Merge queues</th><td>Can enqueue explicitly or follow repository default</td><td>Does not provide the same async merge-queue workflow</td></tr>
                <tr><th>Complex merges</th><td>Designed to reduce timeout risk and allow certain retries</td><td>Caller waits on the merge request lifecycle</td></tr>
              </tbody>
            </table></div>
          </div>

          <div class="deep-dive-section">
            <p class="eyebrow">REQUEST CONTROLS</p>
            <h2>The parameters automation builders need to understand.</h2>
            <div class="deep-dive-facts">
              <div><strong>merge_action</strong><p><code>default</code>, <code>direct_merge</code>, or <code>merge_queue</code>. Default uses a merge queue when the target branch has one configured.</p></div>
              <div><strong>sha</strong><p>Locks the request to the expected PR head. If the PR changes between request and execution, GitHub cancels the merge rather than merging a different head.</p></div>
              <div><strong>merge_method</strong><p>For direct merges, the API supports <code>merge</code>, <code>squash</code>, or <code>rebase</code>.</p></div>
              <div><strong>bypass_rules</strong><p>Can request rule bypass only when the authenticated actor already has permission to bypass those repository rules.</p></div>
            </div>
          </div>

          <div class="deep-dive-section">
            <p class="eyebrow">STATUS & FAILURE MODEL</p>
            <h2>What each response means in production.</h2>
            <div class="deep-dive-status-grid">
              <article><strong>200</strong><p>The PR is already merged or already in a merge queue.</p></article>
              <article><strong>202</strong><p>The merge request was accepted for background processing; store the returned UUID.</p></article>
              <article><strong>400</strong><p>The pull request is not ready for merge, such as a closed or draft PR.</p></article>
              <article><strong>409</strong><p>Another async merge request is already pending; GitHub returns that request's UUID and options.</p></article>
            </div>
            <p class="deep-dive-note">Important operational detail: GitHub says branch protection and repository rules are not evaluated during the initial basic-state check. Also, async merge results are retained for 24 hours after their most recent update, so long-lived automation should persist the outcome it needs rather than treating the result endpoint as permanent storage.</p>
          </div>

          <div class="deep-dive-section">
            <p class="eyebrow">STACKED PULL REQUESTS</p>
            <h2>Why stacked PR support is the standout capability.</h2>
            <p>GitHub explicitly documents this as the required merge API for stacked pull requests. When the requested pull request is part of a stack, the operation includes open downstack pull requests. That makes the endpoint materially different for teams and developer tools that organize large changes as dependent, reviewable layers instead of one oversized pull request.</p>
            <p>For automation authors, that means “merge this PR” can represent a graph of dependent changes rather than a single isolated branch operation. Integrations should therefore treat stacked merges as stateful background work and surface the returned status clearly to users.</p>
          </div>

          <div class="deep-dive-section">
            <p class="eyebrow">MIGRATION CHECKLIST</p>
            <h2>When should an integration move to async merge?</h2>
            <ul class="deep-dive-checklist">
              <li><strong>Use it for new programmatic merge automation.</strong> GitHub now recommends the async API over the synchronous REST endpoint or GraphQL merge mutations.</li>
              <li><strong>Use it for stacked pull requests.</strong> This is the supported merge API for stacked PRs.</li>
              <li><strong>Model the workflow as a state machine.</strong> Persist the UUID, handle pending/merged/enqueued/failed states, and distinguish “queued” from “merged.”</li>
              <li><strong>Verify permissions.</strong> Fine-grained tokens need repository <code>Contents: write</code> for these endpoints.</li>
              <li><strong>Handle race conditions.</strong> Supply the expected head SHA when you need to prevent merging a PR that changed after the request was created.</li>
              <li><strong>Do not assume result URLs are permanent.</strong> The documented result retention window is 24 hours after the latest update.</li>
            </ul>
          </div>

          <div class="deep-dive-section deep-dive-faq">
            <p class="eyebrow">FAQ</p>
            <h2>GitHub async merge API questions.</h2>
            <details><summary>What is the GitHub async merge API?</summary><p>It is a REST API that requests a pull request merge in the background or adds the pull request to a merge queue. A newly accepted background request can return HTTP 202 and a UUID for result polling.</p></details>
            <details><summary>Does it support stacked pull requests?</summary><p>Yes. GitHub documents the async merge endpoint as the required API for stacked pull requests, and the operation can include open downstack pull requests.</p></details>
            <details><summary>What permissions does it need?</summary><p>For fine-grained tokens, GitHub documents <code>Contents</code> repository permission with write access.</p></details>
            <details><summary>How long is the result available?</summary><p>The result is retained for 24 hours after its most recent update. After that window, requesting the UUID returns 404.</p></details>
          </div>

          <div class="deep-dive-sources">
            <p class="eyebrow">PRIMARY SOURCES</p>
            <h2>Documentation used for this explainer.</h2>
            <a href="https://github.blog/changelog/2026-10-01-github-async-merge-api-generally-available/" target="_blank" rel="noopener noreferrer"><strong>GitHub Changelog</strong><span>General availability announcement ↗</span></a>
            <a href="https://docs.github.com/en/rest/pulls/pulls?apiVersion=2026-03-10#merge-a-pull-request-asynchronously" target="_blank" rel="noopener noreferrer"><strong>GitHub REST API Docs</strong><span>Endpoint, parameters, permissions and status model ↗</span></a>
          </div>
        </section>'''

    related = "".join(signal_row(x) for x in related_items(item, items))
    eligible_items = [row for row in items if row.get("seo_eligible", seo_signal_eligible(row))]
    archive_navigation = ""
    if indexable and item in eligible_items and len(eligible_items) > 1:
        archive_index = eligible_items.index(item)
        prev_item = eligible_items[archive_index - 1] if archive_index > 0 else None
        next_item = eligible_items[archive_index + 1] if archive_index + 1 < len(eligible_items) else None
        nav_links = []
        if prev_item:
            nav_links.append(
                f'<a rel="prev" href="/signals/{escape(prev_item["signal_slug"], quote=True)}/"><span>Previous signal</span><strong>{escape(prev_item["title"])}</strong></a>'
            )
        if next_item:
            nav_links.append(
                f'<a rel="next" href="/signals/{escape(next_item["signal_slug"], quote=True)}/"><span>Next signal</span><strong>{escape(next_item["title"])}</strong></a>'
            )
        archive_navigation = (
            '<nav class="signal-archive-navigation shell" aria-label="Signal archive navigation">'
            + "".join(nav_links)
            + "</nav>"
        )
    editorial = item.get("editorial") or editorial_units(item)
    summary_label = "Source summary" if item.get("summary") else "SXF signal note"
    return f'''<!doctype html><html lang="en">
    {page_head(page_title, description, canonical, schema, "article", robots)}
    <body class="intel-page signal-page">
      <a class="skip-link" href="#signal-main">Skip to signal</a>
      <div class="ambient ambient-one" aria-hidden="true"></div><div class="ambient ambient-two" aria-hidden="true"></div>
      {page_header()}
      <main id="signal-main">
        <section class="intel-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/signals/">Signals</a><span>/</span><a href="{escape(category_path(item["category"]), quote=True)}">{escape(item["category"])}</a></nav>
          <div class="intel-kicker"><span class="pulse-dot"></span> SIGNAL / {escape(item["category"].upper())}</div>
          <h1>{escape(page_h1)}</h1>
          <div class="signal-meta-strip">
            <div><span>SOURCE</span><strong>{escape(item["source"])}</strong></div>
            <div><span>PUBLISHED</span><strong>{escape(display_date(item["published"]))}</strong></div>
            <div><span>LAYER</span><strong>{escape(item["category"])}</strong></div>
            <div><span>SIGNAL SCORE</span><strong>{item.get("signal_score", 0):02d}/100</strong></div>
          </div>
        </section>
        <section class="signal-layout shell">
          <article class="signal-brief">
            <p class="eyebrow">{summary_label.upper()}</p>
            <p class="signal-summary">{escape(editorial["what_changed"])}</p>
            <div class="signal-context"><span>WHY IT MATTERS</span><p>{escape(editorial["why_it_matters"])}</p></div>
            <div class="signal-context"><span>WHAT TO VERIFY</span><p>{escape(editorial["what_to_verify"])}</p></div>
          </article>
          <aside class="source-card">
            <span class="source-card-label">SOURCE OF RECORD</span><strong>{escape(item["source"])}</strong>
            <p>Read the original publication for the complete context behind this signal.</p>
            <a href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">Open original source <b>↗</b></a>
          </aside>
        </section>
        {deep_dive_html}
        <section class="signal-taxonomy shell">
          <div><span>TOPICS</span>{topic_links or '<small>No topic tag yet</small>'}</div>
          <div><span>MODELS</span>{model_links or '<small>No named model detected</small>'}</div>
        </section>
        {archive_navigation}
        <section class="related-signals shell">
          <div class="intel-section-head"><div><p class="eyebrow">RELATED SIGNALS</p><h2>Keep the context connected.</h2></div><a href="/signals/">All signals ↗</a></div>
          <div class="signal-list">{related}</div>
        </section>
      </main>
      {page_footer()}
    </body></html>'''
