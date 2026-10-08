"""Render curated comparison pages from verified catalog data.

Kept markup exactly consistent with the original generator, while injecting
pricing, evaluation and shared-HTML dependencies. No file or network I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Callable


@dataclass(frozen=True)
class ComparisonRenderingContext:
    base_url: str
    model_comparison_catalog: dict
    model_pricing_catalog: dict
    model_catalog_entry: Callable
    compare_decision_items: Callable
    comparison_registry_rows: Callable
    comparison_price_text: Callable
    compare_live_facts_html: Callable
    comparison_evidence_html: Callable
    compare_change_watch_html: Callable
    compare_pair_fact_line: Callable
    provider_slug: Callable
    page_head: Callable
    page_header: Callable
    page_footer: Callable


def generic_comparison_page_html(comparison, context: ComparisonRenderingContext):
    BASE_URL = context.base_url
    MODEL_COMPARISON_CATALOG = context.model_comparison_catalog
    model_catalog_entry = context.model_catalog_entry
    compare_decision_items = context.compare_decision_items
    comparison_registry_rows = context.comparison_registry_rows
    comparison_price_text = context.comparison_price_text
    compare_live_facts_html = context.compare_live_facts_html
    comparison_evidence_html = context.comparison_evidence_html
    compare_change_watch_html = context.compare_change_watch_html
    page_head = context.page_head
    page_header = context.page_header
    page_footer = context.page_footer
    model_ids = comparison["model_ids"]
    if len(model_ids) != 2:
        raise RuntimeError(f'{comparison["slug"]}: generic comparison requires exactly two models')
    left, right = [model_catalog_entry(model_id) for model_id in model_ids]
    canonical = f'{BASE_URL}/compare/{comparison["slug"]}/'
    verified = max(left["provenance"]["verified_at"], right["provenance"]["verified_at"], MODEL_COMPARISON_CATALOG["source_verified"])
    decision_items = compare_decision_items(model_ids)
    decisions_html = "".join(
        f'<article><span>{index:02d}</span><h3>{escape(label)}</h3><p>{escape(text)}</p></article>'
        for index, (label, text) in enumerate(decision_items, 1)
    )
    source_links = "".join(
        f'<a href="{escape(model["provenance"]["evidence"]["model_identity"], quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(model["model"])} official specs</span><b>↗</b></a>'
        for model in (left, right)
    )
    related = []
    for candidate in comparison_registry_rows():
        if candidate["slug"] == comparison["slug"]:
            continue
        overlap = len(set(candidate["model_ids"]).intersection(model_ids))
        if overlap:
            related.append((overlap, candidate))
    related.sort(key=lambda row: (-row[0], row[1]["title"]))
    related_html = "".join(
        f'<a href="/compare/{escape(candidate["slug"], quote=True)}/"><span>{escape(candidate["kicker"])}</span><strong>{escape(candidate["title"])}</strong><b>↗</b></a>'
        for _, candidate in related[:4]
    )

    faq = [
        (f'Which has the larger context window: {left["model"]} or {right["model"]}?', compare_decision_items(model_ids)[0][1] if decision_items else "See the verified facts table."),
        (f'Which is cheaper: {left["model"]} or {right["model"]}?', next((text for label, text in decision_items if label == "Direct token cost"), "A directly comparable paid token rate is not available for both models.")),
        ("Does SXF declare an overall winner?", "No. This page compares source-backed specifications and economics. Quality, latency and task success require workload-specific evaluation evidence."),
    ]
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "TechArticle",
                "headline": comparison["title"],
                "description": comparison["summary"],
                "url": canonical,
                "dateModified": verified,
                "about": [{"@type": "Thing", "name": left["model"]}, {"@type": "Thing", "name": right["model"]}],
                "citation": list(dict.fromkeys(left["official_sources"] + right["official_sources"])),
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Compare", "item": BASE_URL + "/compare/"},
                    {"@type": "ListItem", "position": 3, "name": comparison["title"], "item": canonical},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in faq
                ],
            },
        ],
    }
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in faq)

    return f'''<!doctype html><html lang="en">{page_head(
        comparison["title"] + " — Specs, Pricing & Differences | SXF / AI",
        comparison["summary"],
        canonical,
        schema,
    )}
    <body class="intel-page comparison-page compare-v2-page">{page_header("compare")}<main>
      <section class="comparison-hero shell">
        <nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/compare/">Compare</a><span>/</span><span>{escape(comparison["title"])}</span></nav>
        <p class="eyebrow">{escape(comparison["kicker"].upper())} / VERIFIED {escape(verified)}</p>
        <h1>{escape(left["model"])}<br><span>vs {escape(right["model"])}</span></h1>
        <p>{escape(comparison["summary"])}</p>
        <div class="comparison-meta">
          <div><span>PROVIDERS</span><strong>{escape(left["provider"])} · {escape(right["provider"])}</strong></div>
          <div><span>CONTEXT</span><strong>{left["context_window"]:,} · {right["context_window"]:,}</strong></div>
          <div><span>PRICING</span><strong>{escape(comparison_price_text(left["model_id"]))} · {escape(comparison_price_text(right["model_id"]))}</strong></div>
        </div>
      </section>
      {compare_live_facts_html(model_ids)}

      <section class="compare-v2-decisions shell">
        <div class="intel-section-head"><div><p class="eyebrow">DECISION FACTORS</p><h2>What materially changes the choice.</h2></div><span>No synthetic winner score</span></div>
        <div class="compare-v2-decision-grid">{decisions_html}</div>
      </section>

      <section class="compare-v2-workload shell">
        <div class="compare-method-head"><p class="eyebrow">HOW TO DECIDE</p><h2>Specifications narrow the field. Your workload decides.</h2><p>Context, modalities and direct token economics are comparable from official sources. Coding quality, latency, reliability and agent success should be measured on your own acceptance tests before production routing.</p></div>
        <div class="compare-method-grid">
          <article><span>01</span><h3>Replay real tasks</h3><p>Use representative prompts, files, tools and expected outputs from the workload you plan to ship.</p></article>
          <article><span>02</span><h3>Measure task cost</h3><p>Include retries, cached tokens, long-context rules and tool charges—not only headline input price.</p></article>
          <article><span>03</span><h3>Track failures</h3><p>Record hallucinations, tool errors, timeout behavior and human corrections alongside pass rate.</p></article>
          <article><span>04</span><h3>Route by task</h3><p>A portfolio can outperform a one-model policy when different task classes have different cost and capability needs.</p></article>
        </div>
      </section>

      {comparison_evidence_html(model_ids)}
      {compare_change_watch_html(model_ids)}
      <section class="model-reference-lower shell">
        <div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{source_links}</div>
        <div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq_html}</div>
      </section>
      <section class="compare-v2-related shell">
        <div class="intel-section-head"><div><p class="eyebrow">RELATED MATCHUPS</p><h2>Continue the decision tree.</h2></div><a href="/compare/">All comparisons ↗</a></div>
        <div class="model-related-links">{related_html}</div>
      </section>
    </main>{page_footer()}</body></html>'''


def compare_index_html(items, context: ComparisonRenderingContext):
    BASE_URL = context.base_url
    MODEL_COMPARISON_CATALOG = context.model_comparison_catalog
    MODEL_PRICING_CATALOG = context.model_pricing_catalog
    comparison_registry_rows = context.comparison_registry_rows
    model_catalog_entry = context.model_catalog_entry
    compare_pair_fact_line = context.compare_pair_fact_line
    provider_slug = context.provider_slug
    page_head = context.page_head
    page_header = context.page_header
    page_footer = context.page_footer
    canonical = f"{BASE_URL}/compare/"
    verified = MODEL_COMPARISON_CATALOG["source_verified"]
    comparisons = comparison_registry_rows()
    providers = sorted({model["provider"] for model in MODEL_PRICING_CATALOG["models"]})
    title = "Compare AI Models — Pricing, Context & Specs (2026) | SXF / AI"
    description = "Compare AI models across verified pricing, context windows, output limits, modalities and reasoning controls. Build any matchup across the SXF model database or open a curated decision page."

    rows = []
    for comparison in comparisons:
        models = [model_catalog_entry(model_id) for model_id in comparison["model_ids"]]
        row = {
            **comparison,
            "url": f'/compare/{comparison["slug"]}/',
            "providers": " · ".join(dict.fromkeys(model["provider"] for model in models)),
            "facts": compare_pair_fact_line(comparison["model_ids"]),
            "tags_text": " ".join(comparison.get("tags", [])),
        }
        rows.append(row)

    featured = rows[:3]
    featured_html = "".join(
        f'''<a class="compare-feature-card" href="{escape(c["url"], quote=True)}">
          <div class="compare-feature-meta"><span>{escape(c["kicker"])}</span><small>{escape(c["providers"])}</small></div>
          <h2>{escape(c["title"])}</h2><p>{escape(c["summary"])}</p>
          <div class="compare-feature-foot"><span>{escape(c["facts"])}</span><b>Open comparison ↗</b></div>
        </a>''' for c in featured
    )
    cards_html = "".join(
        f'''<article class="compare-library-card" data-compare-card data-tags="{escape(c["tags_text"], quote=True)}" data-search="{escape((c["title"]+" "+c["providers"]+" "+c["summary"]+" "+c["facts"]).lower(), quote=True)}">
          <a href="{escape(c["url"], quote=True)}"><div class="compare-card-meta"><span>{escape(c["kicker"])}</span><small>{escape(c["providers"])}</small></div>
          <h3>{escape(c["title"])}</h3><p>{escape(c["summary"])}</p>
          <div class="compare-card-foot"><small>{escape(c["facts"])}</small><b>Compare models ↗</b></div></a>
        </article>''' for c in rows
    )

    options = "".join(
        f'<option value="{escape(model["model_id"], quote=True)}">{escape(model["provider"])} — {escape(model["model"])}</option>'
        for model in MODEL_PRICING_CATALOG["models"]
    )
    provider_filters = "".join(
        f'<button class="compare-filter" type="button" data-compare-filter="{escape(provider_slug(provider), quote=True)}">{escape(provider)}</button>'
        for provider in providers
    )

    faq_items = [
        ("Can I compare any two models?", "Yes. The interactive builder works across every model in the canonical SXF database. Curated indexable pages are limited to high-intent matchups so the site does not create thin SEO pages."),
        ("What facts come from official sources?", "Context windows, output policies, modalities, reasoning controls, pricing availability and provider-published Standard token rates come from the model catalog and its official-source provenance."),
        ("Does SXF rank models by intelligence?", "No synthetic intelligence score is generated from specifications. Benchmark or quality claims require explicit evaluation evidence; the comparison engine focuses on auditable facts and deployment economics."),
        ("How are missing prices handled?", "If a provider does not publish a directly comparable Standard paid token rate, SXF shows the pricing state as unavailable and excludes that model from direct token-cost arithmetic rather than substituting partner pricing."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq_items)
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage", "@id": canonical+"#webpage", "url": canonical,
                "name": "Compare AI Models", "description": description,
                "isPartOf": {"@id": BASE_URL+"/#website"}, "inLanguage": "en",
                "hasPart": [{"@type": "WebPage", "name": c["title"], "url": BASE_URL+c["url"]} for c in rows],
            },
            {
                "@type": "ItemList", "name": "SXF curated AI model comparisons", "numberOfItems": len(rows),
                "itemListElement": [{"@type": "ListItem", "position": i+1, "name": c["title"], "url": BASE_URL+c["url"]} for i,c in enumerate(rows)],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q,a in faq_items],
            },
        ],
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema)}
    <body class="intel-page compare-hub-page">{page_header("compare")}<main>
      <section class="compare-hub-hero shell">
        <nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><span>Compare</span></nav>
        <div class="compare-hub-hero-grid"><div><p class="eyebrow">COMPARE ENGINE V2</p><h1>Compare AI Models: Pricing, Context, Specs &amp; Capabilities</h1></div>
        <div class="compare-hub-intro"><p>Compare AI models across verified pricing, context windows, output limits, reasoning controls, modalities and capabilities. Build side-by-side comparisons across OpenAI, Anthropic, Google, xAI and Meta, then explore curated deep comparisons backed by source-linked model data.</p><p>No synthetic winner score. Missing prices stay missing. Every factual field is tied to a verified source.</p></div></div>
        <div class="compare-hub-stats"><div><strong>{len(rows)}</strong><span>curated comparisons</span></div><div><strong>{len(MODEL_PRICING_CATALOG["models"])}</strong><span>models in builder</span></div><div><strong>{len(providers)}</strong><span>providers</span></div><div><strong>{escape(verified)}</strong><span>registry verified</span></div></div>
      </section>

      <section class="compare-builder shell" data-compare-builder data-registry="/data/model-comparisons.json" data-catalog="/data/model-pricing.json">
        <div class="compare-builder-head"><div><p class="eyebrow">INTERACTIVE BUILDER</p><h2>Put any two models side by side.</h2><p>Choose models and workload assumptions. The browser calculates from the same public catalog used to render SXF pricing pages.</p></div><span>Client-side · no thin URLs</span></div>
        <div class="compare-builder-controls">
          <label><span>Model A</span><select id="compareModelA">{options}</select></label>
          <div class="compare-builder-vs">VS</div>
          <label><span>Model B</span><select id="compareModelB">{options}</select></label>
        </div>
        <div class="compare-builder-workload">
          <label><span>Uncached input</span><input id="compareInputTokens" type="number" min="0" step="1000" value="100000"></label>
          <label><span>Cached input</span><input id="compareCachedTokens" type="number" min="0" step="1000" value="0"></label>
          <label><span>Output</span><input id="compareOutputTokens" type="number" min="0" step="1000" value="10000"></label>
        </div>
        <div id="compareBuilderResults" class="compare-builder-results" aria-live="polite"></div>
        <div id="compareCuratedLink" class="compare-curated-link" hidden></div>
      </section>

      <section class="compare-featured shell"><div class="intel-section-head"><div><p class="eyebrow">START HERE</p><h2>High-value decisions.</h2></div><span>Curated · indexable · source-backed</span></div><div class="compare-feature-grid">{featured_html}</div></section>

      <section class="compare-library shell" id="comparison-library">
        <div class="compare-library-heading"><div><p class="eyebrow">COMPARISON LIBRARY</p><h2>{len(rows)} decisions worth a dedicated page.</h2><p>These URLs are intentionally curated. The builder above handles the long tail without flooding search engines with near-duplicate pages.</p></div><div class="compare-library-count"><strong>{len(rows)}</strong><span>published matchups</span></div></div>
        <div class="compare-library-tools"><label class="compare-search"><span class="sr-only">Search comparisons</span><input id="compare-search" type="search" placeholder="Search models, providers, pricing, coding…"></label><div class="compare-filters"><button class="compare-filter is-active" type="button" data-compare-filter="all">All</button>{provider_filters}<button class="compare-filter" type="button" data-compare-filter="pricing">Pricing</button><button class="compare-filter" type="button" data-compare-filter="coding">Coding</button><button class="compare-filter" type="button" data-compare-filter="multimodal">Multimodal</button><button class="compare-filter" type="button" data-compare-filter="open-source">Open weights</button></div></div>
        <div class="compare-library-grid">{cards_html}</div><div id="compare-empty" class="compare-empty" hidden>No comparison matches that filter.</div>
      </section>

      <section class="compare-method shell"><div class="compare-method-head"><p class="eyebrow">WHY THIS ENGINE IS DIFFERENT</p><h2>Specifications, economics and history share one source of truth.</h2><p>Many model directories stop at a leaderboard or a price table. SXF connects current provider facts to dated pricing rules and an append-only change ledger, so a comparison can explain what is known, what changed and what remains unverified.</p></div>
        <div class="compare-method-grid"><article><span>01</span><h3>Primary-source facts</h3><p>Core model fields come from official provider documentation stored with provenance.</p></article><article><span>02</span><h3>Dated economics</h3><p>Scheduled price changes and long-context multipliers are applied from the catalog, not hand-entered into each page.</p></article><article><span>03</span><h3>Explicit unknowns</h3><p>Missing output caps or direct paid prices remain unpublished rather than becoming synthetic zeros.</p></article><article><span>04</span><h3>Change-aware</h3><p>Dedicated comparison pages include the same model change ledger used by reference pages.</p></article></div>
      </section>

      <section class="model-reference-lower shell compare-hub-faq"><div class="model-sources"><p class="eyebrow">DATA LAYER</p><a href="/data/model-pricing.json"><span>Canonical model database</span><b>↗</b></a><a href="/data/model-comparisons.json"><span>Curated comparison registry</span><b>↗</b></a><a href="/data/model-history.json"><span>Append-only model history</span><b>↗</b></a><a href="/models/pricing/"><span>Pricing database & calculator</span><b>↗</b></a></div><div class="model-faq"><p class="eyebrow">COMPARE FAQ</p>{faq_html}</div></section>
    </main>{page_footer()}<script src="/compare/compare.js" defer></script></body></html>'''
