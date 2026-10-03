#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_ai_enrichment import (  # noqa: E402
    build_evidence_pack,
    enrichment_priority,
    select_candidates,
)


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def sample_signal():
    return {
        "title": "Introducing GPT-6.1 Sol",
        "url": "https://example.com/gpt-6-1-sol",
        "signal_url": "https://sxf.si/signals/introducing-gpt-6-1-sol-test/",
        "signal_slug": "introducing-gpt-6-1-sol-test",
        "source": "OpenAI",
        "published": "2026-10-02T10:00:00Z",
        "category": "Models",
        "tags": ["OpenAI"],
        "summary": "GPT-6.1 Sol is a new production model with updated coding and agentic capabilities and lower API pricing.",
        "signal_score": 64,
        "seo_quality_score": 89,
        "seo_quality_factors": ["search-worthy-event", "named-model"],
        "seo_eligible": True,
    }


def sample_pricing():
    return {
        "models": [{
            "provider": "OpenAI",
            "family": "GPT-6.1",
            "model": "GPT-6.1 Sol",
            "model_id": "gpt-6.1-sol",
            "context_window": 1000000,
            "max_output": 128000,
            "knowledge_cutoff": "2026-06",
            "reasoning": {"type": "reasoning effort", "levels": ["low", "medium", "high"]},
            "modalities": {"input": ["text", "image"], "output": ["text"]},
            "positioning": "Production model for coding and agentic workflows.",
            "official_sources": [
                "https://developers.openai.com/api/docs/models/gpt-6-1-sol",
                "https://developers.openai.com/api/docs/pricing",
            ],
            "pricing": {
                "standard": [{
                    "start": "2026-09-29",
                    "end": None,
                    "input": 2,
                    "cached_input": 0.2,
                    "output": 10,
                }]
            },
            "provenance": {
                "verified_at": "2026-09-29",
                "evidence": {
                    "model_identity": "https://developers.openai.com/api/docs/models/gpt-6-1-sol",
                    "pricing": "https://developers.openai.com/api/docs/pricing",
                },
            },
        }]
    }


def sample_history():
    return {
        "events": [{
            "sequence": 1,
            "type": "baseline",
            "model_id": "gpt-6.1-sol",
            "verified_at": "2026-09-29",
            "snapshot": {"context_window": 1000000},
            "evidence": {
                "context_window": "https://developers.openai.com/api/docs/models/gpt-6-1-sol"
            },
        }]
    }


def test_selection_prefers_model_release():
    signal = sample_signal()
    weaker = dict(signal)
    weaker.update({
        "title": "A smaller tooling update",
        "url": "https://example.com/tooling",
        "signal_url": "https://sxf.si/signals/tooling/",
        "signal_slug": "tooling",
        "category": "Tools",
        "signal_score": 40,
        "seo_quality_score": 55,
    })
    config = {
        "candidate_max_age_days": 14,
        "candidate_limit": 1,
        "allowed_categories": ["Models", "Tools", "Research", "Open Source"],
        "min_seo_quality_score": 50,
        "min_signal_score": 38,
    }
    rows = select_candidates(
        [weaker, signal],
        config,
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
    )
    expect(len(rows) == 1, "candidate limit must be enforced")
    expect(rows[0]["title"] == "Introducing GPT-6.1 Sol", "model release should win enrichment priority")
    expect(enrichment_priority(signal) > enrichment_priority(weaker), "priority ordering drift")


def test_evidence_pack_matches_model_data():
    evidence = build_evidence_pack(sample_signal(), sample_pricing(), sample_history())
    expect(len(evidence["models"]) == 1, "known model must attach exactly one model evidence record")
    model = evidence["models"][0]
    expect(model["model_id"] == "gpt-6.1-sol", "model identity drift")
    expect(model["pricing_standard"]["input"] == 2, "active model price missing")
    expect(len(model["history"]) == 1, "model history evidence missing")
    expect(
        "https://developers.openai.com/api/docs/pricing" in evidence["source_urls"],
        "official pricing source missing from evidence URLs",
    )


def test_exact_model_match_beats_family_fallback():
    pricing = {
        "models": [
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Astra",
                "model_id": "gpt-6-astra",
                "official_sources": ["https://example.com/astra"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 10, "cached_input": 1, "output": 50}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/astra"}},
            },
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Sol",
                "model_id": "gpt-6-sol",
                "official_sources": ["https://example.com/sol"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 2, "cached_input": 0.2, "output": 10}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/sol"}},
            },
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Luna",
                "model_id": "gpt-6-luna",
                "official_sources": ["https://example.com/luna"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 0.1, "cached_input": 0.01, "output": 0.5}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/luna"}},
            },
        ]
    }
    signal = sample_signal()
    signal["title"] = "Better prompt caching for GPT-6 Sol"
    signal["summary"] = "OpenAI updated prompt caching behavior for GPT-6 Sol."
    evidence = build_evidence_pack(signal, pricing, {"events": []})
    expect([m["model"] for m in evidence["models"]] == ["GPT-6 Sol"], "exact model must beat family fallback")


def test_grouped_model_variants_attach_each_named_model():
    pricing = {
        "models": [
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Sol",
                "model_id": "gpt-6-sol",
                "official_sources": ["https://example.com/sol"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 2, "cached_input": 0.2, "output": 10}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/sol"}},
            },
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Luna",
                "model_id": "gpt-6-luna",
                "official_sources": ["https://example.com/luna"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 0.1, "cached_input": 0.01, "output": 0.5}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/luna"}},
            },
        ]
    }
    signal = sample_signal()
    signal["title"] = "Introducing GPT-6 Sol and Luna"
    signal["summary"] = "OpenAI introduced GPT-6 Sol and Luna for production workloads."
    evidence = build_evidence_pack(signal, pricing, {"events": []})
    expect(
        [m["model"] for m in evidence["models"]] == ["GPT-6 Sol", "GPT-6 Luna"],
        f"grouped variants drift: {[m['model'] for m in evidence['models']]}",
    )


def test_unknown_variant_does_not_attach_family_models():
    pricing = {
        "models": [
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Astra",
                "model_id": "gpt-6-astra",
                "official_sources": ["https://example.com/astra"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 10, "cached_input": 1, "output": 50}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/astra"}},
            },
            {
                "provider": "OpenAI",
                "family": "GPT-6",
                "model": "GPT-6 Sol",
                "model_id": "gpt-6-sol",
                "official_sources": ["https://example.com/sol"],
                "pricing": {"standard": [{"start": "2026-09-01", "end": None, "input": 2, "cached_input": 0.2, "output": 10}]},
                "provenance": {"verified_at": "2026-09-01", "evidence": {"model_identity": "https://example.com/sol"}},
            },
        ]
    }
    signal = sample_signal()
    signal["title"] = "Introducing GPT-6.1 Sol"
    signal["summary"] = "OpenAI introduced GPT-6.1 Sol."
    evidence = build_evidence_pack(signal, pricing, {"events": []})
    expect(evidence["models"] == [], "unknown specific variant must not inherit family model facts")

def test_non_model_signal_does_not_invent_model_data():
    signal = sample_signal()
    signal.update({
        "title": "Repository security advisory comments API in public preview",
        "summary": "GitHub added API support for security advisory comments.",
        "category": "Tools",
        "source": "GitHub",
    })
    evidence = build_evidence_pack(signal, sample_pricing(), sample_history())
    expect(evidence["models"] == [], "non-model signal must not receive unrelated model evidence")


if __name__ == "__main__":
    test_selection_prefers_model_release()
    test_evidence_pack_matches_model_data()
    test_exact_model_match_beats_family_fallback()
    test_grouped_model_variants_attach_each_named_model()
    test_unknown_variant_does_not_attach_family_models()
    test_non_model_signal_does_not_invent_model_data()
    print("AI enrichment dry-run tests passed")
