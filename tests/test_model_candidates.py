#!/usr/bin/env python3
"""Regression tests for the candidate/review contract."""

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_model_candidates.py"
spec = importlib.util.spec_from_file_location("validate_model_candidates", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

registry = json.loads((ROOT / "data/model-identity/registry.json").read_text(encoding="utf-8"))
registry_ids = {row["canonical_model_id"] for row in registry["models"]}

candidate = {
    "candidate_id": "cand_test_new_model",
    "detected_at": "2026-10-06T12:00:00Z",
    "provider": "Example Provider",
    "canonical_model_id": None,
    "change_type": "new_model",
    "observed_identity": {"provider_native_id": "example-model", "display_name": "Example Model"},
    "identity_resolution": {
        "status": "new",
        "matched_model_id": None,
        "confidence": "high",
        "possible_duplicates": []
    },
    "proposed_record": {
        "provider": "Example Provider",
        "family": "Example",
        "model": "Example Model",
        "model_id": "example-model",
        "context_window": None,
        "max_output": None,
        "knowledge_cutoff": None,
        "reasoning": None,
        "modalities": {"input": ["audio"], "output": ["text"]},
        "positioning": "Example specialist model used for candidate validation tests.",
        "sxf_url": "/models/example-model/",
        "official_sources": ["https://example.com/models/example-model"],
        "pricing": {
            "standard": [
                {
                    "start": "2026-10-06",
                    "end": None,
                    "rates": {"minute": 0.01}
                }
            ]
        },
        "provenance": {
            "verified_at": "2026-10-06",
            "verification_method": "test fixture",
            "evidence": {
                "model_identity": "https://example.com/models/example-model",
                "context_window": "https://example.com/models/example-model",
                "max_output": "https://example.com/models/example-model",
                "knowledge_cutoff": "https://example.com/models/example-model",
                "reasoning": "https://example.com/models/example-model",
                "modalities": "https://example.com/models/example-model",
                "pricing": "https://example.com/models/example-model",
                "access": "https://example.com/models/example-model",
                "lifecycle": "https://example.com/models/example-model",
                "capabilities": "https://example.com/models/example-model"
            }
        },
        "pricing_status": "official-paid",
        "calculator_eligible": False,
        "page_template": "catalog-reference",
        "access": {"official_api": True, "open_weight": False, "self_hostable": False},
        "lifecycle": {"status": "current"},
        "capabilities": ["audio", "transcription"],
        "pricing_basis": {
            "meter": "minutes",
            "quantity": 1,
            "dimensions": ["minute"],
            "display_unit": "per minute"
        }
    },
    "diff": {"model_id": {"before": None, "after": "example-model"}},
    "evidence": [{
        "url": "https://example.com/models/example-model",
        "source_type": "official_model_doc",
        "retrieved_at": "2026-10-06T12:00:00Z"
    }],
    "validation": {"status": "passed", "errors": [], "warnings": []},
    "review": {"status": "approved", "reviewed_by": "human-reviewer", "reviewed_at": "2026-10-06T12:05:00Z"}
}
module.validate_candidate(candidate, registry_ids, registry)

assert module.classify_change("new", candidate["diff"]) == {"new_model"}
assert "price_change" in module.classify_change("exact", {"pricing": {"before": 1, "after": 2}})
assert "context_change" in module.classify_change("exact", {"context_window": {"before": 1, "after": 2}})
assert "identity_change" in module.classify_change("alias", {"aliases": {"before": [], "after": ["x"]}})

bad = copy.deepcopy(candidate)
bad["identity_resolution"]["status"] = "ambiguous"
bad["identity_resolution"]["confidence"] = "low"
bad["change_type"] = "metadata_correction"
bad["review"]["status"] = "approved"
try:
    module.validate_candidate(bad, registry_ids, registry)
except module.CandidateError:
    pass
else:
    raise AssertionError("Ambiguous identity must never be approvable")

bad = copy.deepcopy(candidate)
bad["validation"] = {"status": "failed", "errors": ["bad source"], "warnings": []}
try:
    module.validate_candidate(bad, registry_ids, registry)
except module.CandidateError:
    pass
else:
    raise AssertionError("Failed validation must never be approvable")

queue = json.loads((ROOT / "data/model-candidates/queue.json").read_text(encoding="utf-8"))
validated = module.validate_queue(queue, registry)
assert validated == queue["candidates"]
assert len({candidate["candidate_id"] for candidate in validated}) == len(validated)
assert all(candidate["review"]["status"] in module.REVIEW_STATUSES for candidate in validated)
assert all(candidate["validation"]["status"] in module.VALIDATION_STATUSES for candidate in validated)

print(f"Candidate/review contract regression tests OK: {len(validated)} queued candidates")
