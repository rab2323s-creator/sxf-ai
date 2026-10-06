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
    "identity_resolution": {
        "status": "new",
        "matched_model_id": None,
        "confidence": "high",
        "possible_duplicates": []
    },
    "proposed_record": {"model_id": "example-model"},
    "diff": {"model_id": {"before": None, "after": "example-model"}},
    "evidence": [{
        "url": "https://example.com/models/example-model",
        "source_type": "official_model_doc",
        "retrieved_at": "2026-10-06T12:00:00Z"
    }],
    "validation": {"status": "passed", "errors": [], "warnings": []},
    "review": {"status": "approved", "reviewed_by": "human-reviewer", "reviewed_at": "2026-10-06T12:05:00Z"}
}
module.validate_candidate(candidate, registry_ids)

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
    module.validate_candidate(bad, registry_ids)
except module.CandidateError:
    pass
else:
    raise AssertionError("Ambiguous identity must never be approvable")

bad = copy.deepcopy(candidate)
bad["validation"] = {"status": "failed", "errors": ["bad source"], "warnings": []}
try:
    module.validate_candidate(bad, registry_ids)
except module.CandidateError:
    pass
else:
    raise AssertionError("Failed validation must never be approvable")

queue = json.loads((ROOT / "data/model-candidates/queue.json").read_text(encoding="utf-8"))
assert module.validate_queue(queue, registry) == []

print("Candidate/review contract regression tests OK")
