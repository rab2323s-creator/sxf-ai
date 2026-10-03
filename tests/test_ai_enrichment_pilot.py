#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_ai_enrichment_pilot import estimate_cost_usd, sanitize_api_key, validate_writer_output


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def sample_draft():
    source = "https://example.com/source"
    return {
        "seo_title": "GPT-6 Sol and Luna: What Changed",
        "meta_description": "A source-grounded look at GPT-6 Sol and Luna, including pricing, capabilities, and what the release changes for API users.",
        "h1": "GPT-6 Sol and Luna: what changed",
        "intro": "This release introduces two GPT-6 variants with different price and workload tradeoffs. The evidence pack provides verified model data and the original release source, allowing the draft to separate what is documented from what still needs verification before deployment.",
        "what_changed": "The release adds GPT-6 Sol and GPT-6 Luna as distinct models in the GPT-6 family. The evidence pack supplies verified pricing and model metadata for both variants, while the source announcement establishes the release context without requiring unsupported assumptions.",
        "why_it_matters": "The practical significance is model selection: teams can compare the two variants on documented economics and model characteristics instead of treating the announcement as a single undifferentiated upgrade. Any production decision should still verify availability and workload-specific behavior.",
        "key_facts": [
            {"claim": "Fact one from evidence.", "source_url": source},
            {"claim": "Fact two from evidence.", "source_url": source},
            {"claim": "Fact three from evidence.", "source_url": source}
        ],
        "pricing_or_capability_impact": "Use only verified pricing and capability fields from the evidence pack.",
        "before_vs_after": [],
        "who_should_care": "API teams comparing model economics and workload fit.",
        "what_to_verify": ["Availability", "Exact API model identifiers"],
        "faq": [
            {"question": "What changed?", "answer": "Two model variants are covered by the release."},
            {"question": "Should teams migrate immediately?", "answer": "Verify workload fit before changing production deployments."}
        ],
        "sources": [source]
    }


def test_writer_validation_accepts_evidence_only_sources():
    draft = sample_draft()
    errors = validate_writer_output(draft, {"https://example.com/source"})
    expect(errors == [], f"unexpected deterministic errors: {errors}")


def test_writer_validation_rejects_unapproved_source():
    draft = sample_draft()
    draft["key_facts"][0]["source_url"] = "https://invented.example/fact"
    errors = validate_writer_output(draft, {"https://example.com/source"})
    expect(any("unapproved sources" in error for error in errors), "unapproved source must be rejected")


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
        {"input_tokens": 6000, "output_tokens": 1500},
        {"input_tokens": 5000, "output_tokens": 500}
    )
    expect(0 < cost < 0.10, f"pilot cost estimate should stay below configured cap, got {cost}")


if __name__ == "__main__":
    test_writer_validation_accepts_evidence_only_sources()
    test_writer_validation_rejects_unapproved_source()
    test_secret_sanitization()
    test_cost_guard_math()
    print("AI enrichment pilot tests passed")
