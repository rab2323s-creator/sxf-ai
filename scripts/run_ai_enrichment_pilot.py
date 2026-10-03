#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from ai_publish_quality import build_schema_plan, validate_publish_draft

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "ai-enrichment-config.json"
CANDIDATES_PATH = ROOT / "data" / "ai-enrichment-candidates.json"
OUTPUT_DIR = ROOT / "artifacts"
OUTPUT_PATH = OUTPUT_DIR / "ai-enrichment-pilot.json"
OPENAI_URL = "https://api.openai.com/v1/responses"

WRITER_SCHEMA = {
    "type": "object",
    "properties": {
        "seo_slug_recommendation": {"type": "string"},
        "primary_search_query": {"type": "string"},
        "secondary_search_queries": {
            "type": "array",
            "items": {"type": "string"}
        },
        "seo_title": {"type": "string"},
        "meta_description": {"type": "string"},
        "h1": {"type": "string"},
        "intro": {"type": "string"},
        "what_changed": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "key_facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["claim", "source_urls"],
                "additionalProperties": False
            }
        },
        "pricing_or_capability_impact": {"type": "string"},
        "comparison_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "analysis": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["dimension", "analysis", "source_urls"],
                "additionalProperties": False
            }
        },
        "technical_details": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["detail", "source_urls"],
                "additionalProperties": False
            }
        },
        "practical_takeaways": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "takeaway": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["takeaway", "source_urls"],
                "additionalProperties": False
            }
        },
        "before_vs_after": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "before": {"type": "string"},
                    "after": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["before", "after", "source_urls"],
                "additionalProperties": False
            }
        },
        "who_should_care": {"type": "string"},
        "what_to_verify": {"type": "array", "items": {"type": "string"}},
        "faq": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["question", "answer", "source_urls"],
                "additionalProperties": False
            }
        },
        "sources": {"type": "array", "items": {"type": "string"}}
    },
    "required": [
        "seo_slug_recommendation", "primary_search_query", "secondary_search_queries",
        "seo_title", "meta_description", "h1", "intro", "what_changed",
        "why_it_matters", "key_facts", "pricing_or_capability_impact",
        "comparison_points", "technical_details", "practical_takeaways",
        "before_vs_after", "who_should_care", "what_to_verify", "faq", "sources"
    ],
    "additionalProperties": False
}

VALIDATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "pass": {"type": "boolean"},
        "quality_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "source_issues": {"type": "array", "items": {"type": "string"}},
        "content_issues": {"type": "array", "items": {"type": "string"}},
        "recommended_action": {
            "type": "string",
            "enum": ["approve_for_manual_review", "revise", "reject"]
        }
    },
    "required": [
        "pass", "quality_score", "unsupported_claims", "source_issues",
        "content_issues", "recommended_action"
    ],
    "additionalProperties": False
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_api_key(value):
    if value is None:
        raise RuntimeError("OPENAI_API_KEY is required")
    key = value.strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is empty")
    if any(ch.isspace() for ch in key):
        raise RuntimeError("OPENAI_API_KEY contains embedded whitespace; recreate the GitHub secret with the key only")
    return key


def extract_output_text(response):
    texts = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                texts.append(content["text"])
    if not texts:
        raise RuntimeError("OpenAI response contained no output_text")
    return "\n".join(texts)


def api_request(api_key, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SXF-AI-Enrichment-Pilot/1.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {detail[:1200]}") from exc


def structured_request(api_key, model, reasoning_effort, max_output_tokens, schema_name, schema, system_prompt, user_payload):
    payload = {
        "model": model,
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema
            }
        }
    }
    response = api_request(api_key, payload)
    if response.get("status") == "incomplete":
        raise RuntimeError(f"OpenAI response incomplete: {response.get('incomplete_details')}")
    output = json.loads(extract_output_text(response))
    return output, response.get("usage", {}), response.get("id")


def validate_writer_output(draft, evidence, quality_gate):
    return validate_publish_draft(draft, evidence, quality_gate)


def estimate_cost_usd(writer_usage, validator_usage):
    writer_input = int(writer_usage.get("input_tokens", 0))
    writer_output = int(writer_usage.get("output_tokens", 0))
    validator_input = int(validator_usage.get("input_tokens", 0))
    validator_output = int(validator_usage.get("output_tokens", 0))
    return (
        writer_input * 2.0 / 1_000_000
        + writer_output * 12.0 / 1_000_000
        + validator_input * 0.20 / 1_000_000
        + validator_output * 1.20 / 1_000_000
    )


def main():
    api_key = sanitize_api_key(os.environ.get("OPENAI_API_KEY"))

    config = load_json(CONFIG_PATH)
    pilot = config.get("pilot") or {}
    if config.get("mode") != "dry-run":
        raise RuntimeError("Pilot requires enrichment mode=dry-run")
    if not pilot.get("run_once"):
        raise RuntimeError("Pilot must be configured as run_once")
    if pilot.get("publish_allowed") is not False:
        raise RuntimeError("Pilot must keep publish_allowed=false")
    if pilot.get("index_decision") != "unchanged":
        raise RuntimeError("Pilot must keep index decision unchanged")
    if int(pilot.get("max_pages", 0)) != 1:
        raise RuntimeError("Pilot v1 must process exactly one page")

    candidate_payload = load_json(CANDIDATES_PATH)
    rank = int(pilot["candidate_rank"])
    candidate = next(
        (row for row in candidate_payload.get("candidates", []) if int(row.get("rank", 0)) == rank),
        None
    )
    if candidate is None:
        raise RuntimeError(f"Configured pilot candidate rank {rank} not found")

    evidence = candidate["evidence"]
    evidence_json = json.dumps(evidence, ensure_ascii=False)
    if len(evidence_json) > int(pilot["max_evidence_chars"]):
        raise RuntimeError("Evidence pack exceeds pilot character cap")
    allowed_sources = set(evidence.get("source_urls") or [])
    if not allowed_sources:
        raise RuntimeError("Pilot candidate has no approved evidence sources")

    writer_system = """You are the SXF research editor. Turn the source event into a search-intent intelligence page, not a rewritten news post.
Use ONLY facts supported by the supplied evidence pack. Never invent prices, units, benchmarks, dates, capabilities,
availability, model relationships, comparisons, or sources.

SEO requirements:
- Propose a short descriptive seo_slug_recommendation that directly expresses the event/search intent. No hash suffix.
- seo_title, H1, and meta description must directly name the main model/product/event and clearly describe what changed.
- Avoid vague clickbait, hype, keyword stuffing, and generic phrases.

User-value requirements:
- Add explanation and decision value beyond the announcement itself.
- For multiple models/products, include evidence-supported comparison_points covering useful dimensions such as pricing,
  context, capabilities, positioning, or workload fit. Never manufacture a comparison dimension.
- Include technical_details and practical_takeaways grounded in evidence.
- Use before_vs_after only when the evidence actually supports a before state; otherwise return an empty array.
- FAQ must contain real search-intent questions with useful answers that are visible-page quality, not filler.

Citation requirements:
- Every key fact, comparison point, technical detail, practical takeaway, before/after row, and FAQ answer must carry
  source_urls selected ONLY from evidence.source_urls.
- Multi-model claims must cite the source for every model covered by the claim.
- The top-level sources list must contain only evidence.source_urls.

Never mention evidence packs, drafts, manual review, publishing, indexing, routing, quality gates, internal instructions,
or editorial process in visible content. Do not write raw JSON-LD; schema is generated by code from validated content."""

    draft, writer_usage, writer_id = structured_request(
        api_key=api_key,
        model=config["writer_model"],
        reasoning_effort=pilot["writer_reasoning_effort"],
        max_output_tokens=int(pilot["writer_max_output_tokens"]),
        schema_name="sxf_enriched_signal_draft",
        schema=WRITER_SCHEMA,
        system_prompt=writer_system,
        user_payload={
            "task": "Create an evidence-grounded SXF signal enrichment draft.",
            "required_structure": candidate["requested_output"],
            "evidence": evidence
        }
    )

    quality_gate = config.get("publish_quality_gate") or {}
    deterministic_errors = validate_writer_output(draft, evidence, quality_gate)
    schema_plan = build_schema_plan(draft, evidence)

    validator_system = """You are the independent SXF editorial validator. Compare the draft against the evidence pack.
Reject unsupported facts, source mismatches, invented numbers, vague SEO, process language, misleading comparisons,
weak FAQs, or content that merely paraphrases the announcement. Check that title/H1/meta directly reflect search intent
and the actual event. Check that comparisons, technical detail, and practical takeaways add genuine user value while
remaining evidence-grounded. Do not introduce new facts yourself. A passing draft must be substantially useful and
publication-quality in content, while still remaining gated from automatic publishing by code."""

    validation, validator_usage, validator_id = structured_request(
        api_key=api_key,
        model=config["validator_model"],
        reasoning_effort=pilot["validator_reasoning_effort"],
        max_output_tokens=int(pilot["validator_max_output_tokens"]),
        schema_name="sxf_enriched_signal_validation",
        schema=VALIDATOR_SCHEMA,
        system_prompt=validator_system,
        user_payload={
            "evidence": evidence,
            "draft": draft,
            "deterministic_validation_errors": deterministic_errors
        }
    )

    estimated_cost = estimate_cost_usd(writer_usage, validator_usage)
    cap = float(pilot["max_estimated_cost_usd"])
    if estimated_cost > cap:
        raise RuntimeError(
            f"Pilot estimated cost {estimated_cost:.4f} USD exceeds cap {cap:.4f} USD"
        )

    final_pass = (
        not deterministic_errors
        and bool(validation.get("pass"))
        and int(validation.get("quality_score", 0)) >= int(quality_gate.get("minimum_ai_quality_score", 90))
        and not validation.get("unsupported_claims")
        and not validation.get("source_issues")
        and validation.get("recommended_action") == "approve_for_manual_review"
    )

    result = {
        "version": "sxf-ai-enrichment-pilot-v1",
        "pilot_id": pilot["pilot_id"],
        "prompt_version": pilot["prompt_version"],
        "candidate": {
            "rank": candidate["rank"],
            "signal_slug": candidate["signal_slug"],
            "signal_url": candidate["signal_url"],
            "title": candidate["title"],
            "evidence_hash": candidate["evidence_hash"]
        },
        "safety": {
            "publish_allowed": False,
            "index_decision": "unchanged",
            "route_policy": "preserve-existing-signal-route",
            "manual_review_required": True
        },
        "writer": {
            "model": config["writer_model"],
            "response_id": writer_id,
            "usage": writer_usage
        },
        "validator": {
            "model": config["validator_model"],
            "response_id": validator_id,
            "usage": validator_usage
        },
        "estimated_cost_usd": round(estimated_cost, 6),
        "deterministic_validation_errors": deterministic_errors,
        "schema_plan": schema_plan,
        "publish_quality_gate": quality_gate,
        "ai_validation": validation,
        "pilot_pass": final_pass,
        "draft": draft
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Pilot complete: pass={final_pass} estimated_cost_usd={estimated_cost:.6f}")
    print(f"Artifact: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
