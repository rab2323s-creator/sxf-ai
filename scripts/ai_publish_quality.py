#!/usr/bin/env python3
from __future__ import annotations

import re

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){2,9}$")
HASH_SUFFIX_RE = re.compile(r"-[0-9a-f]{7,}$", re.I)
PROCESS_LANGUAGE = re.compile(
    r"\b(evidence pack|manual review|publish(?:ing)?|indexing|signal route|route policy|"
    r"this draft|the draft|internal process|quality gate)\b",
    re.I,
)
HYPE_LANGUAGE = re.compile(
    r"\b(revolutionary|game[- ]changing|ultimate|unmatched|unbeatable|best ever|"
    r"world[- ]changing|groundbreaking)\b",
    re.I,
)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "into", "is",
    "it", "new", "now", "of", "on", "or", "the", "to", "with", "introducing",
}


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def meaningful_tokens(value):
    return {
        token for token in normalized(value).split()
        if token not in STOPWORDS and len(token) >= 2
    }


def _collect_visible_text(draft):
    values = []
    for key in (
        "seo_title", "meta_description", "h1", "intro", "what_changed",
        "why_it_matters", "pricing_or_capability_impact", "who_should_care",
        "primary_search_query",
    ):
        value = draft.get(key)
        if isinstance(value, str):
            values.append(value)
    for key, text_key in (
        ("key_facts", "claim"),
        ("comparison_points", "analysis"),
        ("technical_details", "detail"),
        ("practical_takeaways", "takeaway"),
        ("faq", "answer"),
    ):
        for row in draft.get(key, []) or []:
            if isinstance(row, dict) and isinstance(row.get(text_key), str):
                values.append(row[text_key])
    return "\n".join(values)


def _row_source_urls(row):
    urls = row.get("source_urls") if isinstance(row, dict) else None
    return urls if isinstance(urls, list) else []


def _validate_source_rows(errors, rows, text_key, allowed_sources, label, min_sources=1):
    for index, row in enumerate(rows or [], start=1):
        if not isinstance(row, dict) or not isinstance(row.get(text_key), str) or not row[text_key].strip():
            errors.append(f"{label}[{index}] missing {text_key}")
            continue
        urls = _row_source_urls(row)
        if len(urls) < min_sources:
            errors.append(f"{label}[{index}] requires at least {min_sources} source URL(s)")
        invalid = sorted(url for url in urls if url not in allowed_sources)
        if invalid:
            errors.append(f"{label}[{index}] uses unapproved source(s): " + ", ".join(invalid))


def required_schema_types(draft, evidence):
    required = ["TechArticle", "BreadcrumbList", "FAQPage"]
    if len(evidence.get("models") or []) >= 2 or len(draft.get("comparison_points") or []) >= 2:
        required.append("ItemList")
    return required


def build_schema_plan(draft, evidence):
    return {
        "generated_by": "code",
        "types": required_schema_types(draft, evidence),
        "faq_visible_on_page": True,
        "faq_count": len(draft.get("faq") or []),
        "comparison_item_count": len(draft.get("comparison_points") or []),
        "policy": "schema is generated from validated visible content; AI does not write raw JSON-LD",
    }


def validate_publish_draft(draft, evidence, quality_gate):
    errors = []
    allowed_sources = set(evidence.get("source_urls") or [])
    models = evidence.get("models") or []
    signal = evidence.get("signal") or {}

    slug = draft.get("seo_slug_recommendation", "")
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug) or len(slug) > int(quality_gate["seo_slug_max_chars"]):
        errors.append("seo_slug_recommendation must be 3..10 lowercase hyphenated tokens within length limit")
    if HASH_SUFFIX_RE.search(slug):
        errors.append("seo_slug_recommendation must not contain a hash suffix")

    title = draft.get("seo_title", "")
    meta = draft.get("meta_description", "")
    h1 = draft.get("h1", "")
    if not (30 <= len(title) <= 60):
        errors.append("seo_title length must be 30..60")
    if not (105 <= len(meta) <= 160):
        errors.append("meta_description length must be 105..160")
    if not (25 <= len(h1) <= 90):
        errors.append("h1 length must be 25..90")

    source_terms = meaningful_tokens(signal.get("title", ""))
    for label, value in (("seo_title", title), ("h1", h1)):
        if source_terms and len(source_terms.intersection(meaningful_tokens(value))) < min(2, len(source_terms)):
            errors.append(f"{label} does not directly reflect the source event/entities")

    if len(models) <= 2 and models:
        title_h1 = normalized(title + " " + h1)
        for model in models:
            model_name = normalized(model.get("model", ""))
            if model_name and model_name not in title_h1:
                errors.append(f"seo title/H1 must directly name {model.get('model')}")

    primary_query = draft.get("primary_search_query", "")
    secondary_queries = draft.get("secondary_search_queries") or []
    if not isinstance(primary_query, str) or len(primary_query.strip()) < 8:
        errors.append("primary_search_query is missing or too weak")
    if not isinstance(secondary_queries, list) or not (2 <= len(secondary_queries) <= 5):
        errors.append("secondary_search_queries must contain 2..5 queries")

    if len(draft.get("intro", "")) < 140:
        errors.append("intro is too short")
    if len(draft.get("what_changed", "")) < 180:
        errors.append("what_changed is too short")
    if len(draft.get("why_it_matters", "")) < 180:
        errors.append("why_it_matters is too short")

    key_facts = draft.get("key_facts") or []
    if len(key_facts) < int(quality_gate["min_key_facts"]):
        errors.append("not enough key facts")
    _validate_source_rows(errors, key_facts, "claim", allowed_sources, "key_facts")

    if len(models) >= 2:
        for index, row in enumerate(key_facts, start=1):
            claim = normalized(row.get("claim", "")) if isinstance(row, dict) else ""
            if "both models" in claim and len(_row_source_urls(row)) < 2:
                errors.append(f"key_facts[{index}] makes a multi-model claim but cites fewer than 2 sources")

    comparison = draft.get("comparison_points") or []
    if len(models) >= 2 and len(comparison) < int(quality_gate["min_comparison_points_when_multi_model"]):
        errors.append("multi-model pages require comparison points")
    _validate_source_rows(
        errors,
        comparison,
        "analysis",
        allowed_sources,
        "comparison_points",
        min_sources=2 if len(models) >= 2 else 1,
    )
    for index, row in enumerate(comparison, start=1):
        if not isinstance(row, dict) or len((row.get("dimension") or "").strip()) < 3:
            errors.append(f"comparison_points[{index}] missing dimension")

    technical = draft.get("technical_details") or []
    if len(technical) < int(quality_gate["min_technical_details"]):
        errors.append("not enough technical details")
    _validate_source_rows(errors, technical, "detail", allowed_sources, "technical_details")

    takeaways = draft.get("practical_takeaways") or []
    if len(takeaways) < int(quality_gate["min_practical_takeaways"]):
        errors.append("not enough practical takeaways")
    _validate_source_rows(errors, takeaways, "takeaway", allowed_sources, "practical_takeaways")

    before_after = draft.get("before_vs_after") or []
    for index, row in enumerate(before_after, start=1):
        if not isinstance(row, dict) or not row.get("before") or not row.get("after"):
            errors.append(f"before_vs_after[{index}] is incomplete")
            continue
        urls = _row_source_urls(row)
        if not urls:
            errors.append(f"before_vs_after[{index}] requires source_urls")
        invalid = sorted(url for url in urls if url not in allowed_sources)
        if invalid:
            errors.append(f"before_vs_after[{index}] uses unapproved source(s): " + ", ".join(invalid))

    faq = draft.get("faq") or []
    faq_min = int(quality_gate["faq_min"])
    faq_max = int(quality_gate["faq_max"])
    if not (faq_min <= len(faq) <= faq_max):
        errors.append(f"FAQ count must be {faq_min}..{faq_max}")
    _validate_source_rows(errors, faq, "answer", allowed_sources, "faq")
    for index, row in enumerate(faq, start=1):
        if not isinstance(row, dict) or len((row.get("question") or "").strip()) < 10:
            errors.append(f"faq[{index}] question is too weak")
        if isinstance(row, dict) and len((row.get("answer") or "").strip()) < 50:
            errors.append(f"faq[{index}] answer is too short")

    cited = set(draft.get("sources") or [])
    invalid_sources = sorted(url for url in cited if url not in allowed_sources)
    if invalid_sources:
        errors.append("sources list contains unapproved URL(s): " + ", ".join(invalid_sources))

    visible = _collect_visible_text(draft)
    if quality_gate.get("forbid_process_language") and PROCESS_LANGUAGE.search(visible):
        errors.append("visible content contains internal editorial/process language")
    if HYPE_LANGUAGE.search(visible):
        errors.append("visible content contains hype language")

    schema_types = required_schema_types(draft, evidence)
    required = list(quality_gate.get("required_schema_types") or [])
    for schema_type in required:
        if schema_type not in schema_types:
            errors.append(f"required schema type missing: {schema_type}")
    if quality_gate.get("require_item_list_for_comparison") and comparison and "ItemList" not in schema_types:
        errors.append("comparison content requires ItemList schema")

    pricing_basis = evidence.get("pricing_basis") or {}
    if models and any(model.get("pricing_standard") for model in models):
        if not pricing_basis.get("currency") or not pricing_basis.get("unit"):
            errors.append("pricing evidence must include currency and pricing unit")

    return errors
