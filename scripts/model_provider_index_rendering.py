"""Model provider directory HTML, using explicit dependencies only.

This module generates markup without altering the model catalog, routing,
canonical URLs, JSON-LD, or the shared page shell.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Callable


@dataclass(frozen=True)
class ProviderIndexContext:
    base_url: str
    model_pricing_catalog: dict
    model_has_official_paid_pricing: Callable
    provider_slug: Callable
    page_head: Callable
    page_header: Callable
    page_footer: Callable


def provider_index_html(items, context: ProviderIndexContext):
    """Generate the existing canonical provider directory without file writes."""
    BASE_URL = context.base_url
    MODEL_PRICING_CATALOG = context.model_pricing_catalog
    model_has_official_paid_pricing = context.model_has_official_paid_pricing
    provider_slug = context.provider_slug
    page_head = context.page_head
    page_header = context.page_header
    page_footer = context.page_footer
    providers = sorted({model["provider"] for model in MODEL_PRICING_CATALOG["models"]})
    cards = []
    for provider in providers:
        models = [model for model in MODEL_PRICING_CATALOG["models"] if model["provider"] == provider]
        paid = sum(1 for model in models if model_has_official_paid_pricing(model))
        verified = max(model["provenance"]["verified_at"] for model in models)
        cards.append(
            f'''<a class="tracked-model" href="/providers/{escape(provider_slug(provider), quote=True)}/">
              <span>{len(models):02d}</span><strong>{escape(provider)}</strong>
              <small>{len(models)} tracked model{"s" if len(models) != 1 else ""} · {paid} calculator-priced · verified {escape(verified)}</small><b>↗</b>
            </a>'''
        )

    canonical = BASE_URL + "/providers/"
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": "AI Model Providers | SXF / AI",
                "url": canonical,
                "description": "Verified model portfolios, pricing availability, specifications and source-backed change history by AI provider.",
                "isPartOf": {"@id": BASE_URL + "/#website"},
                "inLanguage": "en",
            },
            {
                "@type": "ItemList",
                "name": "Tracked AI model providers",
                "numberOfItems": len(providers),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index + 1,
                        "name": provider,
                        "url": f'{BASE_URL}/providers/{provider_slug(provider)}/',
                    }
                    for index, provider in enumerate(providers)
                ],
            },
        ],
    }
    return f'''<!doctype html><html lang="en">{page_head(
        "AI Model Providers — OpenAI, Anthropic, Google, xAI & Meta | SXF / AI",
        "Browse verified AI model portfolios by provider, including pricing availability, model specs, official sources and change history.",
        canonical,
        schema,
    )}
    <body class="intel-page model-page">{page_header("models")}<main>
      <section class="collection-hero shell">
        <nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>Providers</span></nav>
        <p class="eyebrow">MODEL INTELLIGENCE / PROVIDERS</p>
        <h1>AI model providers.<br><span>One verified data layer.</span></h1>
        <p>Browse provider portfolios without mixing direct API pricing, partner pricing and self-hosted economics. Every model record points back to official evidence.</p>
        <div class="collection-stats">
          <div><strong>{len(providers)}</strong><span>providers</span></div>
          <div><strong>{len(MODEL_PRICING_CATALOG["models"])}</strong><span>tracked models</span></div>
          <div><strong>{escape(MODEL_PRICING_CATALOG["source_verified"])}</strong><span>catalog verified</span></div>
        </div>
      </section>
      <section class="shell">
        <div class="intel-section-head"><div><p class="eyebrow">PROVIDER DIRECTORY</p><h2>Choose a model ecosystem.</h2></div><a href="/models/pricing/">Pricing explorer ↗</a></div>
        <div class="tracked-models">{"".join(cards)}</div>
      </section>
    </main>{page_footer()}</body></html>'''
