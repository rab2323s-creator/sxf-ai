"""Render sitemap XML from prepared signals; no source fetching or global state."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class SitemapContext:
    base_url: str
    sitemap_path: Path
    model_pricing_catalog: dict
    model_evaluation_catalog: dict
    model_comparison_catalog: dict
    extract_models: Callable
    comparison_registry_rows: Callable
    seo_signal_eligible: Callable
    parse_date: Callable
    topic_groups: Callable
    topic_page_indexable: Callable
    provider_slug: Callable
    model_groups: Callable
    catalog_owns_model_route: Callable
    model_page_indexable: Callable
    slugify: Callable


def sitemap_entry(url, lastmod):
    return f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>"

def sitemap_image_entry(url, lastmod, *image_urls):
    image_nodes = "".join(
        f"<image:image><image:loc>{image_url}</image:loc></image:image>"
        for image_url in image_urls
    )
    return f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod>{image_nodes}</url>"

def content_lastmod(items, parse_date, fallback="2026-09-26"):
    dates = []
    for item in items:
        modified = parse_date(item.get("modified_at", "")) or parse_date(item.get("published", ""))
        if modified is not None:
            dates.append(modified)
    return max(dates).date().isoformat() if dates else fallback


def write_sitemap(items, context: SitemapContext):
    """Write the same sitemap as the legacy generator using explicit dependencies."""
    BASE_URL = context.base_url
    SITEMAP = context.sitemap_path
    MODEL_PRICING_CATALOG = context.model_pricing_catalog
    MODEL_EVALUATION_CATALOG = context.model_evaluation_catalog
    MODEL_COMPARISON_CATALOG = context.model_comparison_catalog
    extract_models = context.extract_models
    comparison_registry_rows = context.comparison_registry_rows
    seo_signal_eligible = context.seo_signal_eligible
    parse_date = context.parse_date
    topic_groups = context.topic_groups
    topic_page_indexable = context.topic_page_indexable
    provider_slug = context.provider_slug
    model_groups = context.model_groups
    catalog_owns_model_route = context.catalog_owns_model_route
    model_page_indexable = context.model_page_indexable
    slugify = context.slugify

    def lastmod(records, fallback="2026-09-26"):
        return content_lastmod(records, parse_date, fallback)

    generated_today = datetime.now(timezone.utc).date().isoformat()
    global_lastmod = lastmod(items)
    category_lastmod = {
        category: lastmod([item for item in items if item["category"] == category], global_lastmod)
        for category in ("Models", "Tools", "Research", "Open Source")
    }
    model_collection_items = [
        item for item in items
        if item["category"] == "Models" or extract_models(item["title"])
    ]
    guide_lastmod = max(lastmod(items[:6], "2026-09-26"), "2026-10-05")
    gpt6_compare_items = [
        item for item in items
        if {"GPT-6", "GPT-6 Astra", "GPT-6 Sol", "GPT-6 Luna"}.intersection(extract_models(item["title"]))
    ]
    sol_opus_items = [
        item for item in items
        if {"GPT-6 Sol", "Claude Opus 5.5"}.intersection(extract_models(item["title"]))
    ]

    rows = [
        sitemap_entry(f"{BASE_URL}/", global_lastmod),
        sitemap_entry(f"{BASE_URL}/models/", lastmod(model_collection_items, category_lastmod["Models"])),
        sitemap_entry(f"{BASE_URL}/models/pricing/", MODEL_PRICING_CATALOG["source_verified"]),
        sitemap_entry(f"{BASE_URL}/tools/", category_lastmod["Tools"]),
        sitemap_entry(f"{BASE_URL}/tools/ai-model-cost-calculator/", MODEL_PRICING_CATALOG["source_verified"]),
        sitemap_entry(f"{BASE_URL}/research/", category_lastmod["Research"]),
        sitemap_entry(f"{BASE_URL}/open-source/", category_lastmod["Open Source"]),
        sitemap_entry(f"{BASE_URL}/signals/", global_lastmod),
        sitemap_entry(f"{BASE_URL}/topics/", global_lastmod),
        sitemap_entry(f"{BASE_URL}/brief/", generated_today),
        sitemap_entry(f"{BASE_URL}/about/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/", guide_lastmod),
        sitemap_entry(f"{BASE_URL}/ai-agent-cost/", "2026-10-09"),
        sitemap_entry(f"{BASE_URL}/superintelligence/", "2026-10-01"),
        sitemap_entry(f"{BASE_URL}/compare/", generated_today),
        sitemap_entry(f"{BASE_URL}/evaluations/", MODEL_EVALUATION_CATALOG["source_verified"]),
        sitemap_entry(f"{BASE_URL}/evaluations/explorer/", MODEL_EVALUATION_CATALOG["source_verified"]),
    ] + [
        sitemap_entry(
            f'{BASE_URL}/evaluations/{benchmark["benchmark_id"]}/',
            MODEL_EVALUATION_CATALOG["source_verified"],
        )
        for benchmark in MODEL_EVALUATION_CATALOG["benchmarks"]
    ] + [
        sitemap_entry(f"{BASE_URL}/guides/best-ai-coding-tools/", "2026-09-25"),
        sitemap_entry(f"{BASE_URL}/guides/gpt-6-vs-claude/", "2026-09-25"),
        sitemap_entry(f"{BASE_URL}/guides/open-source-ai-models/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/best-ai-agents/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/ai-agent-security/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/github-copilot-alternatives/", "2026-09-26"),
        sitemap_image_entry(
            f"{BASE_URL}/guides/model-context-protocol-mcp/",
            "2026-10-05",
            f"{BASE_URL}/guides/model-context-protocol-mcp/images/mcp-architecture-map.svg"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/github-copilot-memory/",
            "2026-10-05",
            f"{BASE_URL}/guides/github-copilot-memory/images/github-copilot-memory-map.svg"
        ),
        sitemap_entry(f"{BASE_URL}/guides/prompt-injection/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/ai-super-agents/", "2026-09-26"),
        sitemap_entry(f"{BASE_URL}/guides/how-to-build-ai-super-agent/", "2026-09-28"),
        sitemap_image_entry(
            f"{BASE_URL}/guides/ai-agent-discovery/",
            "2026-10-03",
            f"{BASE_URL}/guides/ai-agent-discovery/images/ai-agent-discovery-routing-map.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/ai-agent-authorization/",
            "2026-10-03",
            f"{BASE_URL}/guides/ai-agent-authorization/images/ai-agent-authority-chain.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/ai-negotiation-agents/",
            "2026-10-02",
            f"{BASE_URL}/guides/ai-negotiation-agents/images/ai-negotiation-agents-autonomous-bargaining.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/ai-agent-collusion-secret-communication/",
            "2026-10-01",
            f"{BASE_URL}/guides/ai-agent-collusion-secret-communication/images/ai-agent-secret-collusion-steganography.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/can-ai-replicate-itself/",
            "2026-10-01",
            f"{BASE_URL}/guides/can-ai-replicate-itself/images/ai-self-replication-model-escape-map.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/ai-shutdown-resistance/",
            "2026-09-30",
            f"{BASE_URL}/guides/ai-shutdown-resistance/images/ai-shutdown-resistance-instrumental-convergence.webp"
        ),
        sitemap_entry(
            f"{BASE_URL}/guides/ai-deception-alignment-faking/",
            "2026-09-30"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/can-ai-become-conscious/",
            "2026-09-30",
            f"{BASE_URL}/guides/can-ai-become-conscious/images/ai-consciousness-evidence-ladder.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/what-is-agentic-ai/",
            "2026-09-30",
            f"{BASE_URL}/guides/what-is-agentic-ai/images/how-agentic-ai-works.webp",
            f"{BASE_URL}/guides/what-is-agentic-ai/images/agentic-ai-vs-chatbot-generative-ai.webp"
        ),
        sitemap_image_entry(
            f"{BASE_URL}/guides/will-ai-take-over-the-world/",
            "2026-09-29",
            f"{BASE_URL}/guides/will-ai-take-over-the-world/images/ai-takeover-capability-stack.webp",
            f"{BASE_URL}/guides/will-ai-take-over-the-world/images/digital-ai-takeover-vs-robots.webp",
            f"{BASE_URL}/guides/will-ai-take-over-the-world/images/current-ai-vs-takeover-requirements.webp",
            f"{BASE_URL}/guides/will-ai-take-over-the-world/images/ai-takeover-realistic-timeline.webp"
        ),
    ]

    for comparison in comparison_registry_rows():
        rows.append(sitemap_entry(
            f'{BASE_URL}/compare/{comparison["slug"]}/',
            MODEL_COMPARISON_CATALOG["source_verified"],
        ))

    for item in items:
        if not item.get("seo_eligible", seo_signal_eligible(item)):
            continue
        modified = parse_date(item.get("modified_at", "")) or parse_date(item["published"])
        rows.append(sitemap_entry(item["signal_url"], modified.date().isoformat()))

    for slug, (_topic, matched) in topic_groups(items).items():
        if topic_page_indexable(matched):
            rows.append(sitemap_entry(f"{BASE_URL}/topics/{slug}/", lastmod(matched)))

    rows.append(sitemap_entry(f"{BASE_URL}/providers/", MODEL_PRICING_CATALOG["source_verified"]))
    for provider in sorted({model["provider"] for model in MODEL_PRICING_CATALOG["models"]}):
        provider_models = [model for model in MODEL_PRICING_CATALOG["models"] if model["provider"] == provider]
        provider_verified = max(model["provenance"]["verified_at"] for model in provider_models)
        rows.append(sitemap_entry(
            f"{BASE_URL}/providers/{provider_slug(provider)}/",
            provider_verified,
        ))

    for model in MODEL_PRICING_CATALOG["models"]:
        if model.get("page_template") not in {"catalog-reference", "editorial-reference"}:
            continue
        rows.append(sitemap_entry(
            BASE_URL + model["sxf_url"],
            model["provenance"]["verified_at"],
        ))

    for name, matched in model_groups(items).items():
        if catalog_owns_model_route(name):
            continue
        if model_page_indexable(name, matched):
            rows.append(sitemap_entry(f"{BASE_URL}/models/{slugify(name)}/", lastmod(matched)))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "\n".join(rows) + "\n</urlset>\n"
    SITEMAP.write_text(xml, encoding="utf-8")
