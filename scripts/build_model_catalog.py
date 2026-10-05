#!/usr/bin/env python3
"""Build and validate the SXF canonical AI model catalog.

Source of truth:
  data/model-catalog/manifest.json
  data/model-catalog/providers/*.json

Generated compatibility artifact:
  data/model-pricing.json

The generator intentionally uses only Python's standard library so the catalog
can be validated in CI without introducing a package-manager dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "data" / "model-catalog"
MANIFEST_PATH = CATALOG_DIR / "manifest.json"
OUTPUT_PATH = ROOT / "data" / "model-pricing.json"

ALLOWED_PRICING_STATUSES = {
    "official-paid",
    "free-preview",
    "partner-priced",
    "not-published",
    "self-hosted",
}
REQUIRED_EVIDENCE = {
    "model_identity",
    "context_window",
    "max_output",
    "knowledge_cutoff",
    "reasoning",
    "modalities",
    "pricing",
}


class CatalogError(ValueError):
    pass


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogError(f"Missing required catalog file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def require(condition: bool, message: str):
    if not condition:
        raise CatalogError(message)


def valid_https(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_iso_date(value, label: str, allow_null: bool = False):
    if value is None and allow_null:
        return
    require(isinstance(value, str), f"{label} must be an ISO date string")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CatalogError(f"{label} must be YYYY-MM-DD: {value!r}") from exc


def validate_pricing(model: dict, label: str):
    pricing = model.get("pricing")
    require(isinstance(pricing, dict), f"{label}.pricing must be an object")
    schedules = pricing.get("standard", [])
    require(isinstance(schedules, list), f"{label}.pricing.standard must be an array")

    previous_end = None
    for index, period in enumerate(schedules):
        p = f"{label}.pricing.standard[{index}]"
        require(isinstance(period, dict), f"{p} must be an object")
        validate_iso_date(period.get("start"), f"{p}.start")
        validate_iso_date(period.get("end"), f"{p}.end", allow_null=True)
        start = period["start"]
        end = period.get("end")
        if end is not None:
            require(start <= end, f"{p} ends before it starts")
        if previous_end is not None:
            require(start > previous_end, f"{label} has overlapping Standard pricing periods")
        previous_end = end
        for key in ("input", "output"):
            require(isinstance(period.get(key), (int, float)) and period[key] >= 0, f"{p}.{key} must be a non-negative number")
        for key in ("cached_input", "cache_write", "cache_write_5m", "cache_write_1h"):
            if key in period:
                require(isinstance(period[key], (int, float)) and period[key] >= 0, f"{p}.{key} must be a non-negative number")

    long_context = pricing.get("long_context")
    if long_context is not None:
        require(isinstance(long_context, dict), f"{label}.pricing.long_context must be an object")
        require(isinstance(long_context.get("threshold_input_tokens"), int) and long_context["threshold_input_tokens"] > 0,
                f"{label}.pricing.long_context.threshold_input_tokens must be a positive integer")
        multipliers = long_context.get("multipliers")
        require(isinstance(multipliers, dict) and multipliers, f"{label}.pricing.long_context.multipliers must be a non-empty object")
        for key, value in multipliers.items():
            require(isinstance(value, (int, float)) and value > 0, f"{label}.pricing.long_context.multipliers.{key} must be positive")

    if model.get("calculator_eligible") is True:
        require(model.get("pricing_status") == "official-paid",
                f"{label}: calculator_eligible=true requires pricing_status=official-paid")
        require(bool(schedules), f"{label}: calculator_eligible=true requires Standard pricing")


def validate_model(model: dict, provider: str, seen_ids: set[str], seen_aliases: set[str]):
    require(isinstance(model, dict), f"{provider}: each model must be an object")
    model_id = model.get("model_id")
    label = f"{provider}/{model_id or '<missing-id>'}"

    for key in ("family", "model", "model_id", "positioning", "sxf_url", "pricing_status"):
        require(isinstance(model.get(key), str) and model[key].strip(), f"{label}.{key} must be a non-empty string")

    require(model_id not in seen_ids, f"Duplicate model_id: {model_id}")
    require(model_id not in seen_aliases, f"model_id conflicts with an alias: {model_id}")
    seen_ids.add(model_id)

    aliases = model.get("aliases", [])
    require(isinstance(aliases, list), f"{label}.aliases must be an array")
    for alias in aliases:
        require(isinstance(alias, str) and alias.strip(), f"{label}.aliases contains an invalid value")
        require(alias not in seen_ids and alias not in seen_aliases, f"Duplicate/conflicting alias: {alias}")
        seen_aliases.add(alias)

    require(isinstance(model.get("context_window"), int) and model["context_window"] > 0,
            f"{label}.context_window must be a positive integer")
    max_output = model.get("max_output")
    require(max_output is None or max_output == "unlimited" or (isinstance(max_output, int) and max_output > 0),
            f"{label}.max_output must be positive, null, or 'unlimited'")

    modalities = model.get("modalities")
    require(isinstance(modalities, dict), f"{label}.modalities must be an object")
    for direction in ("input", "output"):
        values = modalities.get(direction)
        require(isinstance(values, list) and values and all(isinstance(x, str) and x for x in values),
                f"{label}.modalities.{direction} must be a non-empty string array")

    sources = model.get("official_sources")
    require(isinstance(sources, list) and sources, f"{label}.official_sources must be non-empty")
    for source in sources:
        require(isinstance(source, str) and valid_https(source), f"{label} has invalid official source URL: {source!r}")

    status = model.get("pricing_status")
    require(status in ALLOWED_PRICING_STATUSES, f"{label}.pricing_status is unsupported: {status!r}")
    require(isinstance(model.get("calculator_eligible"), bool), f"{label}.calculator_eligible must be boolean")

    provenance = model.get("provenance")
    require(isinstance(provenance, dict), f"{label}.provenance must be an object")
    validate_iso_date(provenance.get("verified_at"), f"{label}.provenance.verified_at")
    require(isinstance(provenance.get("verification_method"), str) and provenance["verification_method"],
            f"{label}.provenance.verification_method must be a non-empty string")
    evidence = provenance.get("evidence")
    require(isinstance(evidence, dict), f"{label}.provenance.evidence must be an object")
    missing = REQUIRED_EVIDENCE - set(evidence)
    require(not missing, f"{label}.provenance.evidence missing: {', '.join(sorted(missing))}")
    for key, source in evidence.items():
        require(isinstance(source, str) and valid_https(source), f"{label}.provenance.evidence.{key} must be an https URL")

    validate_pricing(model, label)


def build_catalog() -> dict:
    manifest = load_json(MANIFEST_PATH)
    sources = manifest.get("catalog_sources")
    require(isinstance(sources, dict), "manifest.catalog_sources must be an object")

    provider_paths = sources.get("providers")
    model_order = sources.get("model_order")
    require(isinstance(provider_paths, list) and provider_paths, "manifest.catalog_sources.providers must be non-empty")
    require(isinstance(model_order, list) and model_order, "manifest.catalog_sources.model_order must be non-empty")
    require(len(model_order) == len(set(model_order)), "manifest.catalog_sources.model_order contains duplicate ids")

    seen_ids: set[str] = set()
    seen_aliases: set[str] = set()
    indexed = {}

    for relative in provider_paths:
        require(isinstance(relative, str) and relative.startswith("providers/"),
                f"Invalid provider source path: {relative!r}")
        payload = load_json(CATALOG_DIR / relative)
        provider = payload.get("provider")
        models = payload.get("models")
        require(isinstance(provider, str) and provider.strip(), f"{relative}: provider must be non-empty")
        require(isinstance(models, list), f"{relative}: models must be an array")
        for source_model in models:
            require("provider" not in source_model, f"{relative}: model entries must inherit provider from the provider file")
            model = {"provider": provider, **source_model}
            validate_model(model, provider, seen_ids, seen_aliases)
            indexed[model["model_id"]] = model

    missing = [model_id for model_id in model_order if model_id not in indexed]
    extras = sorted(set(indexed) - set(model_order))
    require(not missing, f"manifest model_order references missing models: {', '.join(missing)}")
    require(not extras, f"Provider files contain models absent from manifest model_order: {', '.join(extras)}")

    output = {}
    for key, value in manifest.items():
        if key == "catalog_sources":
            output["models"] = [indexed[model_id] for model_id in model_order]
        else:
            output[key] = value

    require(output.get("pricing_statuses") == [
        "official-paid", "free-preview", "partner-priced", "not-published", "self-hosted"
    ], "manifest.pricing_statuses must preserve the public catalog contract")

    return output


def rendered(catalog: dict) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate sources and fail if generated output is stale")
    args = parser.parse_args()

    try:
        catalog = build_catalog()
        expected = rendered(catalog)
        if args.check:
            actual = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
            if actual != expected:
                raise CatalogError(
                    "data/model-pricing.json is stale. Run: python scripts/build_model_catalog.py"
                )
            print(f"Model catalog OK: {len(catalog['models'])} models")
            return 0

        OUTPUT_PATH.write_text(expected, encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} with {len(catalog['models'])} models")
        return 0
    except CatalogError as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
