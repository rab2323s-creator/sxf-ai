#!/usr/bin/env python3
"""Validate SXF model discovery candidates and review-state invariants."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "model-candidates" / "queue.json"
REGISTRY_PATH = ROOT / "data" / "model-identity" / "registry.json"

CHANGE_TYPES = {
    "new_model", "identity_change", "price_change", "context_change",
    "capability_change", "lifecycle_change", "access_change",
    "source_issue", "metadata_correction",
}
IDENTITY_STATUSES = {"exact", "alias", "renamed", "successor", "new", "possible_duplicate", "ambiguous"}
CONFIDENCE = {"high", "medium", "low"}
VALIDATION_STATUSES = {"pending", "passed", "failed"}
REVIEW_STATUSES = {"pending", "approved", "rejected", "needs_changes"}
SOURCE_TYPES = {
    "official_model_doc", "official_pricing", "official_api_reference",
    "official_changelog", "official_model_card", "official_repository",
    "partner_pricing", "other_official",
}


class CandidateError(ValueError):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise CandidateError(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise CandidateError(f"Cannot load {path.relative_to(ROOT)}: {exc}") from exc


def valid_datetime(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def valid_https(value) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def classify_change(identity_status: str, diff: dict) -> set[str]:
    if identity_status == "new":
        return {"new_model"}

    keys = set(diff)
    classes = set()
    if keys & {"model_id", "provider_native_ids", "aliases", "family", "version", "display_name", "renamed_from", "predecessor", "successor"}:
        classes.add("identity_change")
    if "pricing" in keys or "pricing_basis" in keys or "pricing_status" in keys:
        classes.add("price_change")
    if "context_window" in keys or "max_output" in keys:
        classes.add("context_change")
    if keys & {"capabilities", "modalities", "reasoning"}:
        classes.add("capability_change")
    if "lifecycle" in keys or "lifecycle_status" in keys:
        classes.add("lifecycle_change")
    if "access" in keys or "calculator_eligible" in keys:
        classes.add("access_change")
    if keys & {"official_sources", "provenance", "source_issue"}:
        classes.add("source_issue")
    if not classes and keys:
        classes.add("metadata_correction")
    return classes


def validate_candidate(candidate: dict, registry_ids: set[str]):
    require(isinstance(candidate, dict), "candidate must be an object")
    cid = candidate.get("candidate_id")
    require(isinstance(cid, str) and cid.startswith("cand_") and len(cid) > 5, "candidate_id must start with cand_")
    require(valid_datetime(candidate.get("detected_at")), f"{cid}: detected_at must be ISO date-time")
    require(isinstance(candidate.get("provider"), str) and candidate["provider"].strip(), f"{cid}: provider required")
    require(candidate.get("change_type") in CHANGE_TYPES, f"{cid}: invalid change_type")

    identity = candidate.get("identity_resolution")
    require(isinstance(identity, dict), f"{cid}: identity_resolution required")
    require(identity.get("status") in IDENTITY_STATUSES, f"{cid}: invalid identity resolution status")
    require(identity.get("confidence") in CONFIDENCE, f"{cid}: invalid identity confidence")
    matched = identity.get("matched_model_id")
    duplicates = identity.get("possible_duplicates")
    require(matched is None or matched in registry_ids, f"{cid}: matched_model_id is not in registry")
    require(isinstance(duplicates, list) and len(duplicates) == len(set(duplicates)), f"{cid}: possible_duplicates must be unique array")
    require(all(item in registry_ids for item in duplicates), f"{cid}: possible_duplicates references unknown registry ID")

    if identity["status"] in {"exact", "alias", "renamed", "successor"}:
        require(matched is not None, f"{cid}: resolved identity requires matched_model_id")
    if identity["status"] == "new":
        require(matched is None, f"{cid}: new identity cannot have matched_model_id")
    if identity["status"] == "possible_duplicate":
        require(bool(duplicates), f"{cid}: possible_duplicate requires candidates")
    if identity["status"] == "ambiguous":
        require(identity["confidence"] != "high", f"{cid}: ambiguous identity cannot be high confidence")

    canonical_id = candidate.get("canonical_model_id")
    require(canonical_id is None or isinstance(canonical_id, str), f"{cid}: canonical_model_id must be string or null")
    if matched is not None:
        require(canonical_id in {None, matched}, f"{cid}: canonical_model_id conflicts with matched identity")

    diff = candidate.get("diff", {})
    require(isinstance(diff, dict), f"{cid}: diff must be an object")
    allowed_classes = classify_change(identity["status"], diff)
    require(candidate["change_type"] in allowed_classes or
            (candidate["change_type"] == "source_issue" and "source_issue" in diff),
            f"{cid}: change_type {candidate['change_type']} does not match identity/diff classification {sorted(allowed_classes)}")

    evidence = candidate.get("evidence")
    require(isinstance(evidence, list) and evidence, f"{cid}: evidence must be non-empty")
    for index, row in enumerate(evidence):
        require(isinstance(row, dict), f"{cid}: evidence[{index}] must be object")
        require(valid_https(row.get("url")), f"{cid}: evidence[{index}].url must be https")
        require(row.get("source_type") in SOURCE_TYPES, f"{cid}: invalid evidence source_type")
        require(valid_datetime(row.get("retrieved_at")), f"{cid}: evidence[{index}].retrieved_at must be ISO date-time")

    validation = candidate.get("validation")
    require(isinstance(validation, dict), f"{cid}: validation required")
    require(validation.get("status") in VALIDATION_STATUSES, f"{cid}: invalid validation status")
    require(isinstance(validation.get("errors"), list), f"{cid}: validation.errors must be array")
    require(isinstance(validation.get("warnings"), list), f"{cid}: validation.warnings must be array")
    if validation["status"] == "passed":
        require(not validation["errors"], f"{cid}: passed validation cannot contain errors")
    if validation["status"] == "failed":
        require(bool(validation["errors"]), f"{cid}: failed validation requires errors")

    review = candidate.get("review")
    require(isinstance(review, dict), f"{cid}: review required")
    require(review.get("status") in REVIEW_STATUSES, f"{cid}: invalid review status")
    reviewed_by = review.get("reviewed_by")
    reviewed_at = review.get("reviewed_at")
    if review["status"] == "pending":
        require(reviewed_by is None and reviewed_at is None, f"{cid}: pending review cannot have reviewer metadata")
    else:
        require(isinstance(reviewed_by, str) and reviewed_by.strip(), f"{cid}: reviewed candidate requires reviewed_by")
        require(valid_datetime(reviewed_at), f"{cid}: reviewed candidate requires reviewed_at")

    if review["status"] == "approved":
        require(validation["status"] == "passed", f"{cid}: approval requires passed validation")
        require(identity["status"] not in {"ambiguous", "possible_duplicate"}, f"{cid}: unresolved identity cannot be approved")
        if candidate["change_type"] != "source_issue":
            require(isinstance(candidate.get("proposed_record"), dict), f"{cid}: approved change requires proposed_record")


def validate_queue(queue: dict, registry: dict):
    require(queue.get("schema_version") == "1.0", "candidate queue schema_version must be 1.0")
    candidates = queue.get("candidates")
    require(isinstance(candidates, list), "candidate queue candidates must be an array")
    registry_ids = {entry["canonical_model_id"] for entry in registry.get("models", [])}
    seen = set()
    for candidate in candidates:
        validate_candidate(candidate, registry_ids)
        cid = candidate["candidate_id"]
        require(cid not in seen, f"duplicate candidate_id: {cid}")
        seen.add(cid)
    return candidates


def main() -> int:
    try:
        queue = load_json(QUEUE_PATH)
        registry = load_json(REGISTRY_PATH)
        candidates = validate_queue(queue, registry)
        counts = {}
        for candidate in candidates:
            counts[candidate["review"]["status"]] = counts.get(candidate["review"]["status"], 0) + 1
        print(f"Model candidate queue OK: {len(candidates)} candidates / review={counts}")
        return 0
    except CandidateError as exc:
        print(f"candidate error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
