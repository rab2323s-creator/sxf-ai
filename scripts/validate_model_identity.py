#!/usr/bin/env python3
"""Validate the SXF model identity registry against the canonical catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "model-identity" / "registry.json"
CATALOG_PATH = ROOT / "data" / "model-pricing.json"

ALLOWED_LIFECYCLE = {"current", "preview", "legacy", "deprecated"}


class IdentityError(ValueError):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise IdentityError(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise IdentityError(f"Cannot load {path.relative_to(ROOT)}: {exc}") from exc


def valid_https(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_registry(registry: dict, catalog: dict) -> dict:
    require(registry.get("schema_version") == "1.0", "identity registry schema_version must be 1.0")
    entries = registry.get("models")
    require(isinstance(entries, list), "identity registry models must be an array")

    catalog_models = catalog.get("models") or []
    catalog_by_id = {model["model_id"]: model for model in catalog_models}
    require(len(catalog_by_id) == len(catalog_models), "canonical catalog contains duplicate model IDs")

    by_id = {}
    provider_tokens: dict[str, dict[str, str]] = {}

    for entry in entries:
        require(isinstance(entry, dict), "identity registry entries must be objects")
        cid = entry.get("canonical_model_id")
        provider = entry.get("provider")
        require(isinstance(cid, str) and cid.strip(), "canonical_model_id must be non-empty")
        require(cid not in by_id, f"duplicate canonical_model_id: {cid}")
        require(isinstance(provider, str) and provider.strip(), f"{cid}: provider must be non-empty")
        require(entry.get("lifecycle_status") in ALLOWED_LIFECYCLE, f"{cid}: invalid lifecycle_status")

        for field in ("provider_native_ids", "aliases", "renamed_from", "identity_sources"):
            values = entry.get(field)
            require(isinstance(values, list), f"{cid}.{field} must be an array")
            require(len(values) == len(set(values)), f"{cid}.{field} contains duplicates")
            require(all(isinstance(value, str) and value.strip() for value in values), f"{cid}.{field} contains invalid values")
        require(entry["provider_native_ids"], f"{cid}.provider_native_ids must not be empty")
        require(entry["identity_sources"], f"{cid}.identity_sources must not be empty")
        require(all(valid_https(url) for url in entry["identity_sources"]), f"{cid}: identity_sources must be https URLs")
        require(isinstance(entry.get("family"), str) and entry["family"].strip(), f"{cid}.family must be non-empty")
        require(entry.get("version") is None or (isinstance(entry["version"], str) and entry["version"].strip()), f"{cid}.version must be null or non-empty")
        require(isinstance(entry.get("display_name"), str) and entry["display_name"].strip(), f"{cid}.display_name must be non-empty")

        own_tokens = entry["provider_native_ids"] + entry["aliases"] + entry["renamed_from"]
        require(len(own_tokens) == len(set(own_tokens)), f"{cid}: native IDs, aliases, and renamed_from overlap")
        tokens = provider_tokens.setdefault(provider, {})
        for token in own_tokens:
            require(token not in tokens, f"{provider}: identity token {token!r} collides between {tokens.get(token)} and {cid}")
            tokens[token] = cid

        for relation in ("predecessor", "successor"):
            value = entry.get(relation)
            require(value is None or (isinstance(value, str) and value.strip()), f"{cid}.{relation} must be null or a canonical ID")
            require(value != cid, f"{cid}.{relation} cannot point to itself")

        by_id[cid] = entry

    require(set(by_id) == set(catalog_by_id),
            "identity registry must cover exactly the canonical catalog; missing="
            + ",".join(sorted(set(catalog_by_id) - set(by_id)))
            + " extras=" + ",".join(sorted(set(by_id) - set(catalog_by_id))))

    for cid, entry in by_id.items():
        model = catalog_by_id[cid]
        require(entry["provider"] == model["provider"], f"{cid}: provider drift between registry and catalog")
        require(entry["family"] == model["family"], f"{cid}: family drift between registry and catalog")
        require(entry["display_name"] == model["model"], f"{cid}: display_name drift between registry and catalog")
        require(entry["lifecycle_status"] == model["lifecycle"]["status"], f"{cid}: lifecycle drift between registry and catalog")
        require(set(entry["aliases"]) == set(model.get("aliases", [])), f"{cid}: alias drift between registry and catalog")
        require(cid in entry["provider_native_ids"], f"{cid}: bootstrap registry must retain current catalog model_id as a native ID")
        identity_source = model["provenance"]["evidence"]["model_identity"]
        require(identity_source in entry["identity_sources"], f"{cid}: catalog identity evidence missing from registry")

        for relation in ("predecessor", "successor"):
            target = entry.get(relation)
            if target is not None:
                require(target in by_id, f"{cid}.{relation} references unknown canonical ID {target}")
                require(by_id[target]["provider"] == entry["provider"], f"{cid}.{relation} crosses provider boundary")

    # Relations are directional and must be reciprocal when declared.
    for cid, entry in by_id.items():
        predecessor = entry.get("predecessor")
        successor = entry.get("successor")
        if predecessor is not None:
            require(by_id[predecessor].get("successor") == cid,
                    f"{cid}.predecessor={predecessor} is not reciprocal")
        if successor is not None:
            require(by_id[successor].get("predecessor") == cid,
                    f"{cid}.successor={successor} is not reciprocal")

    # Successor graph must be acyclic.
    for start in by_id:
        seen = set()
        cursor = start
        while cursor is not None:
            require(cursor not in seen, f"successor cycle detected from {start}")
            seen.add(cursor)
            cursor = by_id[cursor].get("successor")

    return by_id


def main() -> int:
    try:
        registry = load_json(REGISTRY_PATH)
        catalog = load_json(CATALOG_PATH)
        entries = validate_registry(registry, catalog)
        providers = {entry["provider"] for entry in entries.values()}
        print(f"Model identity registry OK: {len(entries)} models / {len(providers)} providers")
        return 0
    except IdentityError as exc:
        print(f"identity error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
