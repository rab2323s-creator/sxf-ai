#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = "1.0"
TRACKED_FIELDS = (
    "provider",
    "family",
    "model",
    "aliases",
    "context_window",
    "max_output",
    "knowledge_cutoff",
    "reasoning",
    "modalities",
    "pricing",
    "availability",
    "status",
)
IDENTITY_FIELDS = {"provider", "family", "model", "aliases"}
OPTIONAL_FIELDS = {"aliases", "availability", "status"}
CHANGE_TYPES = {
    "pricing": "pricing_change",
    "context_window": "context_change",
    "max_output": "output_limit_change",
    "knowledge_cutoff": "knowledge_cutoff_change",
    "reasoning": "reasoning_change",
    "modalities": "modality_change",
    "availability": "availability_change",
    "status": "status_change",
    "provider": "identity_change",
    "family": "identity_change",
    "model": "identity_change",
    "aliases": "identity_change",
}


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def value_hash(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def tracked_snapshot(model):
    snapshot = {}
    for field in TRACKED_FIELDS:
        if field in model:
            snapshot[field] = copy.deepcopy(model[field])
    return snapshot


def evidence_for_field(model, field):
    evidence = model.get("provenance", {}).get("evidence", {})
    if field == "pricing":
        key = "pricing"
    elif field in IDENTITY_FIELDS:
        key = "model_identity"
    else:
        key = field

    url = evidence.get(key)
    if field in OPTIONAL_FIELDS and field not in model:
        return None
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError(
            f"{model.get('model_id')}: tracked field {field!r} has no official provenance evidence"
        )
    if url not in model.get("official_sources", []):
        raise RuntimeError(
            f"{model.get('model_id')}: provenance for {field!r} is not in official_sources"
        )
    return url


def snapshot_evidence(model, snapshot):
    return {field: evidence_for_field(model, field) for field in snapshot}


def event_hash(event_without_hash):
    return value_hash(event_without_hash)


def make_event(sequence, previous_event_hash, event_type, model_id, verified_at, *, snapshot=None, changes=None, evidence=None):
    event = {
        "sequence": sequence,
        "type": event_type,
        "model_id": model_id,
        "verified_at": verified_at,
        "previous_event_hash": previous_event_hash,
    }
    if snapshot is not None:
        event["snapshot"] = copy.deepcopy(snapshot)
    if changes is not None:
        event["changes"] = copy.deepcopy(changes)
    if evidence is not None:
        event["evidence"] = copy.deepcopy(evidence)

    digest = event_hash(event)
    event["event_id"] = "evt_" + digest[:20]
    event["event_hash"] = digest
    return event


def state_entry(snapshot, verified_at, event_id):
    return {
        "last_event_verified_at": verified_at,
        "last_event_id": event_id,
        "snapshot_hash": value_hash(snapshot),
        "snapshot": copy.deepcopy(snapshot),
    }


def build_initial_history(catalog):
    verified = catalog.get("source_verified")
    models = sorted(catalog.get("models", []), key=lambda model: model["model_id"])
    events = []
    state = {}
    previous_hash = None

    for model in models:
        model_id = model["model_id"]
        snapshot = tracked_snapshot(model)
        evidence = snapshot_evidence(model, snapshot)
        event = make_event(
            len(events) + 1,
            previous_hash,
            "baseline",
            model_id,
            model["provenance"]["verified_at"],
            snapshot=snapshot,
            evidence=evidence,
        )
        events.append(event)
        previous_hash = event["event_hash"]
        state[model_id] = state_entry(snapshot, event["verified_at"], event["event_id"])

    return {
        "schema_version": SCHEMA_VERSION,
        "name": "SXF AI Model Change Ledger",
        "description": (
            "Append-only, hash-chained history of source-backed changes to SXF model facts. "
            "Editorial positioning is intentionally excluded."
        ),
        "baseline_verified_at": verified,
        "tracked_fields": list(TRACKED_FIELDS),
        "immutability_policy": (
            "Existing ledger events are never rewritten by the sync engine. "
            "Models must remain in the catalog; retirement is represented as a sourced status change."
        ),
        "state": state,
        "events": events,
        "chain_head": previous_hash,
    }


def diff_snapshot(before, after, model):
    changes = []
    fields = sorted(set(before) | set(after))
    for field in fields:
        old = before.get(field)
        new = after.get(field)
        if old == new:
            continue
        changes.append({
            "field": field,
            "change_type": CHANGE_TYPES[field],
            "before": copy.deepcopy(old),
            "after": copy.deepcopy(new),
            "source_url": evidence_for_field(model, field),
        })
    return changes


def sync_history(catalog, history):
    validate_history_structure(history)
    result = copy.deepcopy(history)
    current_models = {model["model_id"]: model for model in catalog.get("models", [])}
    previous_state = result["state"]

    missing = sorted(set(previous_state) - set(current_models))
    if missing:
        raise RuntimeError(
            "Tracked models cannot be deleted from the canonical catalog; "
            f"keep the record and represent retirement/status instead: {missing}"
        )

    added_events = []
    previous_hash = result.get("chain_head")

    for model_id in sorted(current_models):
        model = current_models[model_id]
        snapshot = tracked_snapshot(model)
        verified_at = model["provenance"]["verified_at"]

        if model_id not in previous_state:
            event = make_event(
                len(result["events"]) + 1,
                previous_hash,
                "model_added",
                model_id,
                verified_at,
                snapshot=snapshot,
                evidence=snapshot_evidence(model, snapshot),
            )
            result["events"].append(event)
            result["state"][model_id] = state_entry(snapshot, verified_at, event["event_id"])
            previous_hash = event["event_hash"]
            added_events.append(event)
            continue

        prior = result["state"][model_id]
        changes = diff_snapshot(prior["snapshot"], snapshot, model)
        if not changes:
            continue

        if verified_at <= prior["last_event_verified_at"]:
            raise RuntimeError(
                f"{model_id}: factual changes require a newer provenance verified_at "
                f"than {prior['last_event_verified_at']}; got {verified_at}"
            )

        event = make_event(
            len(result["events"]) + 1,
            previous_hash,
            "model_changed",
            model_id,
            verified_at,
            changes=changes,
        )
        result["events"].append(event)
        result["state"][model_id] = state_entry(snapshot, verified_at, event["event_id"])
        previous_hash = event["event_hash"]
        added_events.append(event)

    result["chain_head"] = previous_hash
    return result, added_events


def validate_history_structure(history):
    if history.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError(f"model history schema drift: {history.get('schema_version')!r}")
    if history.get("tracked_fields") != list(TRACKED_FIELDS):
        raise RuntimeError("model history tracked_fields drift")
    if not isinstance(history.get("events"), list) or not history["events"]:
        raise RuntimeError("model history must contain baseline events")
    if not isinstance(history.get("state"), dict) or not history["state"]:
        raise RuntimeError("model history must contain current state")

    previous_hash = None
    replay = {}

    for expected_sequence, event in enumerate(history["events"], 1):
        if event.get("sequence") != expected_sequence:
            raise RuntimeError("model history event sequence is not contiguous")
        if event.get("previous_event_hash") != previous_hash:
            raise RuntimeError(f"model history hash chain broken at sequence {expected_sequence}")

        stored_hash = event.get("event_hash")
        stored_id = event.get("event_id")
        unsigned = {
            key: copy.deepcopy(value)
            for key, value in event.items()
            if key not in {"event_hash", "event_id"}
        }
        calculated = event_hash(unsigned)
        if stored_hash != calculated or stored_id != "evt_" + calculated[:20]:
            raise RuntimeError(f"model history event hash mismatch at sequence {expected_sequence}")

        model_id = event.get("model_id")
        event_type = event.get("type")
        verified_at = event.get("verified_at")
        if not isinstance(model_id, str) or not model_id:
            raise RuntimeError(f"model history event {expected_sequence} missing model_id")
        if not isinstance(verified_at, str) or not verified_at:
            raise RuntimeError(f"model history event {expected_sequence} missing verified_at")

        if event_type in {"baseline", "model_added"}:
            if model_id in replay:
                raise RuntimeError(f"duplicate initial history event for {model_id}")
            snapshot = event.get("snapshot")
            evidence = event.get("evidence")
            if not isinstance(snapshot, dict) or not isinstance(evidence, dict):
                raise RuntimeError(f"{event_type} event for {model_id} missing snapshot/evidence")
            if set(snapshot) != set(evidence):
                raise RuntimeError(f"{event_type} evidence coverage mismatch for {model_id}")
            replay[model_id] = state_entry(snapshot, verified_at, stored_id)
        elif event_type == "model_changed":
            if model_id not in replay:
                raise RuntimeError(f"change event appears before model baseline: {model_id}")
            changes = event.get("changes")
            if not isinstance(changes, list) or not changes:
                raise RuntimeError(f"model_changed event for {model_id} has no changes")
            snapshot = copy.deepcopy(replay[model_id]["snapshot"])
            seen_fields = set()
            for change in changes:
                field = change.get("field")
                if field in seen_fields or field not in TRACKED_FIELDS:
                    raise RuntimeError(f"invalid or duplicate changed field {field!r} for {model_id}")
                if change.get("change_type") != CHANGE_TYPES[field]:
                    raise RuntimeError(f"invalid change_type for {model_id}.{field}")
                seen_fields.add(field)
                if snapshot.get(field) != change.get("before"):
                    raise RuntimeError(f"history replay before-value mismatch for {model_id}.{field}")
                if not isinstance(change.get("source_url"), str) or not change["source_url"].startswith("https://"):
                    raise RuntimeError(f"history change missing official evidence for {model_id}.{field}")
                if change.get("after") is None:
                    snapshot.pop(field, None)
                else:
                    snapshot[field] = copy.deepcopy(change["after"])
            replay[model_id] = state_entry(snapshot, verified_at, stored_id)
        else:
            raise RuntimeError(f"unsupported model history event type: {event_type!r}")

        previous_hash = stored_hash

    if history.get("chain_head") != previous_hash:
        raise RuntimeError("model history chain_head does not match final event hash")

    if replay != history["state"]:
        raise RuntimeError("model history state does not match replayed event ledger")


def validate_history_against_catalog(catalog, history):
    validate_history_structure(history)
    current_models = {model["model_id"]: model for model in catalog.get("models", [])}

    if set(current_models) != set(history["state"]):
        missing = sorted(set(current_models) - set(history["state"]))
        extra = sorted(set(history["state"]) - set(current_models))
        raise RuntimeError(f"model history/catalog membership mismatch: missing={missing}, extra={extra}")

    for model_id, model in current_models.items():
        snapshot = tracked_snapshot(model)
        entry = history["state"][model_id]
        if snapshot != entry["snapshot"]:
            raise RuntimeError(f"model history state is stale for {model_id}")
        if value_hash(snapshot) != entry["snapshot_hash"]:
            raise RuntimeError(f"model history snapshot hash mismatch for {model_id}")


def sync_model_history_file(catalog_path, history_path):
    catalog_path = Path(catalog_path)
    history_path = Path(history_path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
        updated, events = sync_history(catalog, history)
    else:
        updated = build_initial_history(catalog)
        events = updated["events"]

    validate_history_against_catalog(catalog, updated)

    rendered = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
    existing = history_path.read_text(encoding="utf-8") if history_path.exists() else None
    if existing != rendered:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(rendered, encoding="utf-8")

    return {
        "models": len(updated["state"]),
        "events": len(updated["events"]),
        "events_added": len(events),
        "chain_head": updated["chain_head"],
    }
