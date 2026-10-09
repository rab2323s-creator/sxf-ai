#!/usr/bin/env python3
"""Build the lightweight SXF model index used by Explorer/search surfaces."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "model-pricing.json"
OUTPUT_PATH = ROOT / "data" / "model-index.json"

INDEX_MODEL_KEYS = {
    "model_id", "model", "provider", "family", "sxf_url",
    "context_window", "max_output", "capabilities", "access",
    "lifecycle", "pricing_status", "calculator_eligible",
    "pricing_basis", "verified_at", "standard_rate",
}


class IndexError(ValueError):
    pass


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise IndexError(f"Cannot load {path.relative_to(ROOT)}: {exc}") from exc


def active_standard_period(model: dict, verified: str):
    for period in model.get("pricing", {}).get("standard", []):
        if verified >= period["start"] and (not period.get("end") or verified <= period["end"]):
            return period
    return None


def compact_standard_rate(model: dict, verified: str):
    period = active_standard_period(model, verified)
    if not period or model.get("pricing_status") != "official-paid":
        return None

    basis = model["pricing_basis"]
    if basis["meter"] == "tokens":
        rate = {}
        for key in ("input", "cached_input", "output"):
            if key in period:
                rate[key] = period[key]
        return rate or None

    rates = period.get("rates", {})
    return {key: rates[key] for key in basis["dimensions"] if key in rates} or None


def build_index(catalog: dict) -> dict:
    # The compact index keeps source_verified as provenance but selects the
    # effective billing rates for the current UTC date.
    verified = catalog["source_verified"]
    effective_date = datetime.now(timezone.utc).date().isoformat()
    models = []
    for model in catalog["models"]:
        row = {
            "model_id": model["model_id"],
            "model": model["model"],
            "provider": model["provider"],
            "family": model["family"],
            "sxf_url": model["sxf_url"],
            "context_window": model.get("context_window"),
            "max_output": model.get("max_output"),
            "capabilities": model["capabilities"],
            "access": model["access"],
            "lifecycle": model["lifecycle"],
            "pricing_status": model["pricing_status"],
            "calculator_eligible": model["calculator_eligible"],
            "pricing_basis": {
                "meter": model["pricing_basis"]["meter"],
                "display_unit": model["pricing_basis"]["display_unit"],
            },
            "verified_at": model["provenance"]["verified_at"],
            "standard_rate": compact_standard_rate(model, effective_date),
        }
        if set(row) != INDEX_MODEL_KEYS:
            raise IndexError(f"{model['model_id']}: lightweight index contract drift")
        models.append(row)

    return {
        "schema_version": "1.0",
        "source_catalog_schema": catalog["schema_version"],
        "source_verified": verified,
        "model_count": len(models),
        "provider_count": len({model["provider"] for model in models}),
        "models": models,
    }


def rendered(index: dict) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        catalog = load_json(CATALOG_PATH)
        expected = rendered(build_index(catalog))
        if args.check:
            actual = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
            if actual != expected:
                raise IndexError("data/model-index.json is stale. Run: python scripts/build_model_index.py")
            print(f"Model index OK: {len(json.loads(expected)['models'])} models")
            return 0
        OUTPUT_PATH.write_text(expected, encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
        return 0
    except IndexError as exc:
        print(f"model index error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
