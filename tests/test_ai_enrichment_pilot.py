#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ai_publish_quality import build_schema_plan, validate_publish_draft
from run_ai_enrichment_pilot import estimate_cost_usd, sanitize_api_key


SOL = "https://developers.openai.com/api/docs/models/gpt-6-sol"
LUNA = "https://developers.openai.com/api/docs/models/gpt-6-luna"
PRICING = "https://developers.openai.com/api/docs/pricing"
ANNOUNCEMENT = "https://openai.com/index/introducing-gpt-6-sol-and-luna"


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def quality_gate():
    return {
        "minimum_ai_quality_score": 90,
        "seo_slug_max_chars": 72,
        "min_key_facts": 4,
        "min_comparison_points_when_multi_model": 3,
        "min_technical_details": 3,
        "min_practical_takeaways": 3,
        "faq_min": 3,
        "faq_max": 6,
        "required_schema_types": ["TechArticle", "BreadcrumbList", "FAQPage"],
        "require_item_list_for_comparison": True,
        "forbid_process_language": True,
        "require_direct_search_intent": True,
        "require_value_beyond_news": True,
    }


def evidence():
    return {
        "pricing_basis": {
            "currency": "USD",
            "unit": "per 1 million tokens",
            "scope": "Standard API token pricing unless a model-specific rule states otherwise",
        },
        "signal": {
            "title": "Introducing GPT-6 Sol and Luna",
            "url": ANNOUNCEMENT,
        },
        "models": [
            {"model": "GPT-6 Sol", "pricing_standard": {"input": 2}},
            {"model": "GPT-6 Luna", "pricing_standard": {"input": 0.1}},
        ],
        "source_urls": [SOL, LUNA, PRICING, ANNOUNCEMENT],
    }


def sample_draft():
    return {
        "seo_slug_recommendation": "gpt-6-sol-vs-luna-pricing-capabilities",
        "primary_search_query": "GPT-6 Sol vs Luna pricing and capabilities",
        "secondary_search_queries": [
            "GPT-6 Sol pricing",
            "GPT-6 Luna pricing",
            "GPT-6 Sol vs Luna",
        ],
        "seo_title": "GPT-6 Sol vs Luna: Pricing and Capabilities",
        "meta_description": "Compare GPT-6 Sol and GPT-6 Luna pricing, context limits, reasoning controls, and workload fit after OpenAI's new model release.",
        "h1": "GPT-6 Sol vs GPT-6 Luna: What Changed",
        "intro": "OpenAI introduced GPT-6 Sol and GPT-6 Luna as two GPT-6 options with different cost and workload positioning. The useful question is not only what launched, but how their documented pricing and capabilities change model selection for API teams.",
        "what_changed": "Both models list 1,050,000-token context windows and 128,000-token maximum output. Sol is positioned for complex coding and agentic work, while Luna is positioned for focused, high-volume, cost-sensitive workloads. Their standard token prices differ materially.",
        "why_it_matters": "Teams now have a documented tradeoff inside the same GPT-6 family: Sol targets more demanding workflows at higher unit cost, while Luna targets efficiency. The difference affects model routing, long-context budgeting, and which workloads merit the more expensive tier.",
        "key_facts": [
            {"claim": "GPT-6 Sol lists a 1,050,000-token context window.", "source_urls": [SOL]},
            {"claim": "GPT-6 Luna lists a 1,050,000-token context window.", "source_urls": [LUNA]},
            {"claim": "Both models support text and image input with text output.", "source_urls": [SOL, LUNA]},
            {"claim": "Standard prices are stated in USD per 1 million tokens.", "source_urls": [PRICING]},
        ],
        "pricing_or_capability_impact": "GPT-6 Sol lists higher standard token prices than GPT-6 Luna, while both models share the same documented context and maximum-output limits. This creates a direct cost-versus-workload-positioning decision for teams choosing between the two.",
        "comparison_points": [
            {"dimension": "Input price", "analysis": "Sol lists a higher standard input price than Luna per 1 million tokens.", "source_urls": [SOL, LUNA, PRICING]},
            {"dimension": "Context limits", "analysis": "Both models document the same 1,050,000-token context window and 128,000-token maximum output.", "source_urls": [SOL, LUNA]},
            {"dimension": "Workload positioning", "analysis": "Sol targets complex coding and agentic workflows, while Luna targets focused, high-volume and cost-sensitive workloads.", "source_urls": [ANNOUNCEMENT, SOL, LUNA]},
        ],
        "technical_details": [
            {"detail": "Both models document a 1,050,000-token context window.", "source_urls": [SOL, LUNA]},
            {"detail": "Both models document a 128,000-token maximum output.", "source_urls": [SOL, LUNA]},
            {"detail": "Long-context pricing rules apply above the documented threshold.", "source_urls": [PRICING]},
        ],
        "practical_takeaways": [
            {"takeaway": "Cost-sensitive high-volume workloads should compare Luna economics before choosing Sol.", "source_urls": [LUNA, PRICING]},
            {"takeaway": "Teams using complex coding or agentic workloads should evaluate Sol against the workload requirements.", "source_urls": [SOL, ANNOUNCEMENT]},
            {"takeaway": "Long-context workloads need separate cost checks because pricing multipliers can change request economics.", "source_urls": [PRICING]},
        ],
        "before_vs_after": [],
        "who_should_care": "API teams choosing between GPT-6 tiers, especially developers balancing complex agentic workloads against high-volume cost constraints.",
        "what_to_verify": [
            "Confirm the exact API model identifier before deployment.",
            "Benchmark workload quality at the intended reasoning level.",
            "Model long-context costs for requests near the documented threshold.",
        ],
        "faq": [
            {"question": "What is the difference between GPT-6 Sol and GPT-6 Luna?", "answer": "Sol is positioned for complex coding and agentic workflows, while Luna is positioned for focused, high-volume and cost-sensitive workloads.", "source_urls": [SOL, LUNA, ANNOUNCEMENT]},
            {"question": "How do GPT-6 Sol and Luna prices compare?", "answer": "The official pricing data lists materially higher standard token prices for Sol than Luna, with prices expressed in USD per 1 million tokens.", "source_urls": [SOL, LUNA, PRICING]},
            {"question": "Do GPT-6 Sol and Luna have the same context window?", "answer": "Yes. Both model pages document a 1,050,000-token context window and a 128,000-token maximum output.", "source_urls": [SOL, LUNA]},
        ],
        "sources": [SOL, LUNA, PRICING, ANNOUNCEMENT],
    }


def test_publish_gate_accepts_research_page():
    errors = validate_publish_draft(sample_draft(), evidence(), quality_gate())
    expect(errors == [], f"unexpected publish gate errors: {errors}")


def test_publish_gate_rejects_process_language():
    draft = sample_draft()
    draft["intro"] += " This draft is ready for manual review."
    errors = validate_publish_draft(draft, evidence(), quality_gate())
    expect(any("process language" in error for error in errors), "process language must be rejected")


def test_publish_gate_requires_multi_model_sources():
    draft = sample_draft()
    draft["key_facts"][2]["source_urls"] = [SOL]
    errors = validate_publish_draft(draft, evidence(), quality_gate())
    expect(any("multi-model claim" in error for error in errors), "multi-model claim must cite both models")


def test_publish_gate_requires_comparison_value():
    draft = sample_draft()
    draft["comparison_points"] = []
    errors = validate_publish_draft(draft, evidence(), quality_gate())
    expect(any("comparison points" in error for error in errors), "multi-model page must compare models")


def test_publish_gate_rejects_unapproved_faq_source():
    draft = sample_draft()
    draft["faq"][0]["source_urls"] = ["https://example.com/not-evidence"]
    errors = validate_publish_draft(draft, evidence(), quality_gate())
    expect(any("faq[1] uses unapproved" in error for error in errors), "FAQ must stay evidence-only")


def test_schema_plan_contains_faq_and_comparison_schema():
    plan = build_schema_plan(sample_draft(), evidence())
    expect("TechArticle" in plan["types"], "TechArticle schema missing")
    expect("BreadcrumbList" in plan["types"], "BreadcrumbList schema missing")
    expect("FAQPage" in plan["types"], "FAQPage schema missing")
    expect("ItemList" in plan["types"], "ItemList schema missing for comparison")


def test_secret_sanitization():
    expect(sanitize_api_key("  sk-test-key\n") == "sk-test-key", "secret trim failed")
    try:
        sanitize_api_key("sk-test key")
    except RuntimeError as exc:
        expect("embedded whitespace" in str(exc), "embedded whitespace error drift")
    else:
        raise AssertionError("embedded whitespace must be rejected")


def test_cost_guard_math():
    cost = estimate_cost_usd(
        {"input_tokens": 7000, "output_tokens": 2200},
        {"input_tokens": 6000, "output_tokens": 800},
    )
    expect(0 < cost < 0.10, f"pilot cost estimate should stay below configured cap, got {cost}")


if __name__ == "__main__":
    test_publish_gate_accepts_research_page()
    test_publish_gate_rejects_process_language()
    test_publish_gate_requires_multi_model_sources()
    test_publish_gate_requires_comparison_value()
    test_publish_gate_rejects_unapproved_faq_source()
    test_schema_plan_contains_faq_and_comparison_schema()
    test_secret_sanitization()
    test_cost_guard_math()
    print("AI enrichment publish-quality tests passed")
